"""CALLSIGN acceptance through real routes, mocking only QRZ HTTP transport."""
from datetime import datetime, timedelta, timezone

import pytest
import requests

from app.config import settings
from app.models.callsign_cache import CallsignCache


NOW = datetime(2026, 6, 15, 12, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def callsign_clock_and_network(api_app, monkeypatch):
    from app.services import callsign_service

    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 6, 15, 12, tzinfo=timezone.utc) if tz else cls(2026, 6, 15, 12)

    monkeypatch.setattr(callsign_service, "datetime", Clock)
    monkeypatch.setattr(settings, "QRZ_USERNAME", "contract-user")
    monkeypatch.setattr(settings, "QRZ_PASSWORD", "contract-password")

    def forbidden(*args, **kwargs):
        pytest.fail("Unexpected external QRZ request")

    monkeypatch.setattr("app.utils.qrz_client.requests.get", forbidden)


def cache(db, callsign="JA1ABC", *, days=29, name="Cached Operator", country="Japan"):
    row = CallsignCache(call_sign=callsign, full_name=name, country=country,
                        grid_square="PM95AA", cached_at=(NOW - timedelta(days=days)).replace(tzinfo=None))
    db.add(row)
    db.commit()
    return row


def lookup(client, operator, callsign="JA1ABC"):
    response = client.get(f"/api/v1/callsigns/{callsign}", headers=operator.headers)
    assert response.status_code == 200, response.text
    return response.json()


def qrz_transport(monkeypatch, *, failure=False):
    calls = []

    def get(url, *, params, timeout):
        assert url == "https://xmldata.qrz.com/xml/current/"
        calls.append(dict(params))
        if failure:
            raise requests.ConnectionError("contract QRZ outage")
        response = requests.Response()
        response.status_code = 200
        if "username" in params:
            xml = "<QRZDatabase><Session><Key>contract-session</Key></Session></QRZDatabase>"
        else:
            assert params["s"] == "contract-session"
            assert params["callsign"] == "JA1ABC"
            xml = """<QRZDatabase><Callsign><call>JA1ABC</call><fname>Online</fname>
            <name>Operator</name><country>Japan</country><grid>PM95AA</grid>
            <lat>35.5</lat><lon>139.0</lon><class>First</class>
            <efdate>2020-01-02</efdate><expdate>2030-01-02</expdate></Callsign></QRZDatabase>"""
        response._content = xml.encode()
        return response

    monkeypatch.setattr("app.utils.qrz_client.requests.get", get)
    return calls


def test_fresh_cache_wins_and_is_shared(api_client, db, owner, other):
    row = cache(db)
    for operator in (owner, other):
        result = lookup(api_client, operator, "ja1abc")
        assert result["call_sign"] == "JA1ABC"
        assert result["full_name"] == "Cached Operator"
        assert result["country"] == "Japan"
        assert result["cached"] is True
        assert result["offline"] is False
        assert datetime.fromisoformat(result["cached_at"]) == row.cached_at
    assert db.query(CallsignCache).count() == 1


@pytest.mark.parametrize("existing", [False, True])
def test_online_result_persisted_and_reused_across_users(api_client, db, owner, other, monkeypatch, existing):
    if existing:
        cache(db, days=31, name="Old Identity")
    calls = qrz_transport(monkeypatch)
    result = lookup(api_client, owner)
    assert result["full_name"] == "Online Operator"
    assert result["country"] == "Japan"
    assert result["grid_square"] == "PM95AA"
    assert (result["latitude"], result["longitude"]) == (35.5, 139.0)
    assert result["license_date"] == "2020-01-02"
    assert result["license_exp"] == "2030-01-02"
    assert result["cached"] is False
    assert result["offline"] is False
    assert len(calls) == 2
    db.expire_all()
    rows = db.query(CallsignCache).all()
    assert len(rows) == 1
    assert rows[0].call_sign == "JA1ABC"
    assert rows[0].full_name == "Online Operator"
    assert rows[0].cached_at == NOW.replace(tzinfo=None)
    second = lookup(api_client, other)
    assert second["cached"] is True
    assert second["full_name"] == "Online Operator"
    assert len(calls) == 2


@pytest.mark.parametrize("configured", [True, False])
def test_stale_cache_survives_qrz_failure_or_no_credentials(api_client, db, owner, monkeypatch, configured):
    row = cache(db, days=31)
    timestamp = row.cached_at
    calls = qrz_transport(monkeypatch, failure=True)
    if not configured:
        monkeypatch.setattr(settings, "QRZ_USERNAME", "")
        monkeypatch.setattr(settings, "QRZ_PASSWORD", "")
    result = lookup(api_client, owner)
    assert result["full_name"] == "Cached Operator"
    assert result["cached"] is True
    assert result["offline"] is False
    assert datetime.fromisoformat(result["cached_at"]) == timestamp
    assert len(calls) == (1 if configured else 0)
    db.expire_all()
    assert db.query(CallsignCache).one().cached_at == timestamp


@pytest.mark.parametrize("configured", [True, False])
def test_offline_inference_is_not_registered_identity_or_persisted(api_client, db, owner, monkeypatch, configured):
    calls = qrz_transport(monkeypatch, failure=True)
    if not configured:
        monkeypatch.setattr(settings, "QRZ_USERNAME", "")
        monkeypatch.setattr(settings, "QRZ_PASSWORD", "")
    result = lookup(api_client, owner)
    assert result["call_sign"] == "JA1ABC"
    assert result["country"] == "Japan"
    assert result["offline"] is True
    assert result["cached"] is False
    assert result["cached_at"] is None
    for field in ("first_name", "last_name", "full_name", "class_type", "license_date", "license_exp", "grid_square", "latitude", "longitude"):
        assert result[field] is None
    assert db.query(CallsignCache).count() == 0
    assert len(calls) == (1 if configured else 0)


def test_search_country_and_twenty_result_bound(api_client, db, owner, other):
    for index in range(25):
        cache(db, f"JA1T{index:02d}", country="Japan")
    cache(db, "JA1FOREIGN", country="Canada")
    cache(db, "K1OTHER", country="Japan")
    response = api_client.get("/api/v1/callsigns/search/ja1", headers=other.headers, params={"country": "jap"})
    assert response.status_code == 200, response.text
    results = response.json()["results"]
    assert len(results) == 20
    assert len({r["call_sign"] for r in results}) == 20
    assert all(r["call_sign"] in {f"JA1T{i:02d}" for i in range(25)} and r["country"] == "Japan" for r in results)
    response = api_client.get("/api/v1/callsigns/search/JA1", headers=owner.headers, params={"country": "Canada"})
    assert response.status_code == 200, response.text
    assert [r["call_sign"] for r in response.json()["results"]] == ["JA1FOREIGN"]


@pytest.mark.parametrize("size", [50, 51])
def test_batch_processes_first_fifty_only(api_client, db, owner, size):
    names = [f"JA1T{i:02d}" for i in range(size)]
    for name in names:
        cache(db, name)
    response = api_client.post("/api/v1/callsigns/batch-query", headers=owner.headers, json={"call_signs": names})
    assert response.status_code == 200, response.text
    data = response.json()
    assert [r["call_sign"] for r in data["results"]] == names[:50]
    assert data["found"] == 50
    assert all(r["cached"] is True for r in data["results"])


def test_shared_cache_delete_hit_and_miss(api_client, db, owner, other):
    cache(db)
    for operator in (other, owner):
        response = api_client.delete("/api/v1/callsigns/cache/ja1abc", headers=operator.headers)
        assert response.status_code == 204, response.text
        assert response.content == b""
        assert db.query(CallsignCache).count() == 0
