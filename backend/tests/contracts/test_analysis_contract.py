"""Frozen ANALYSIS/MAP acceptance: literal oracles, real authenticated HTTP."""
from datetime import date, datetime, time, timezone

import pytest

from app.models.location import Location
from app.models.qso_log import QSOLog


@pytest.fixture
def analysis_data(db, owner, other, station_factory, location_factory):
    a = station_factory(owner, "BA1AAA")
    b = station_factory(owner, "BA1BBB")
    foreign = station_factory(other, "JA1ZZZ")
    location_factory(owner, a, grid="OM89AA")
    location_factory(owner, b, grid="PM95AA")
    location_factory(other, foreign, grid="OM89AA")
    # paper only, LoTW only, eQSL only, both, unconfirmed, unconfirmed.
    # Deliberately seed statuses directly: POST creation has QSL linkage.
    rows = [
        (owner, a, "20m", "FT8", "Japan", "PM95AA", "OM89AA", "Y", "N", "N"),
        (owner, a, "20m", "FT8", "Japan", "PM95XX", "OM89XX", "N", "Y", "N"),
        (owner, a, "40m", "CW", "Germany", "JO62AA", "OM89AA", "N", "N", "Y"),
        (owner, b, "40m", "CW", "Germany", "JO62XX", "PM95AA", "Y", "Y", "N"),
        (owner, b, "20m", "SSB", "Japan", "PM95AA", "PM95XX", "N", "N", "N"),
        (owner, b, "10m", "FT8", "Canada", "FN31AA", "PM95AA", "N", "N", "N"),
        (other, foreign, "80m", "AM", "Foreign", "AA00AA", "OM89AA", "Y", "Y", "Y"),
    ]
    for index, (user, station, band, mode, entity, grid, own, paper, lotw, eqsl) in enumerate(rows):
        db.add(QSOLog(user_id=user.id, station_id=station["id"], call_sign=f"JA1T{index}",
                      qso_date=date(2026, 1, 2), time_on=time(12), band=band, mode=mode,
                      dxcc=entity, grid_square=grid, my_gridsquare=own,
                      qsl_rcvd=paper, lotw_rcvd=lotw, eqsl_rcvd=eqsl))
    db.add(QSOLog(user_id=owner.id, station_id=a["id"], call_sign="DELETED",
                  qso_date=date(2026, 1, 2), band="80m", mode="AM", dxcc="Deleted",
                  grid_square="AA00AA", my_gridsquare="OM89AA", qsl_rcvd="Y",
                  lotw_rcvd="Y", is_deleted=True))
    db.commit()
    return a, b, foreign


def get_data(client, user, path, **params):
    response = client.get(f"/api/v1/stats/{path}", headers=user.headers, params=params)
    assert response.status_code == 200, response.text
    return response.json()["data"]


def test_overview_scope_and_confirmation(api_client, owner, analysis_data, monkeypatch):
    from app.services import log_service

    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 1, 15, tzinfo=timezone.utc)

    monkeypatch.setattr(log_service, "datetime", Clock)
    a, b, foreign = analysis_data
    for station, total, confirmed, entities, confirmed_entities in [
        (None, 6, 3, 3, 2), (a["id"], 3, 2, 2, 1),
        (b["id"], 3, 1, 3, 1), (foreign["id"], 0, 0, 0, 0),
    ]:
        data = get_data(api_client, owner, "overview", **({"station_id": station} if station else {}))
        assert {key: data[key] for key in ("total_qso", "confirmed_qso", "total_dxcc", "confirmed_dxcc")} == {
            "total_qso": total, "confirmed_qso": confirmed,
            "total_dxcc": entities, "confirmed_dxcc": confirmed_entities,
        }
        assert data["monthly_qso"] == total
        assert data["yearly_qso"] == total
        assert data["station_count"] == 2


def test_distributions_matrix_and_dxcc(api_client, owner, analysis_data):
    data = get_data(api_client, owner, "band-mode")
    # Percentages derive from six owned, live QSOs; allow half a tenth of a
    # percentage point for display rounding, without fixing undocumented precision.
    for items, key, counts in (
        (data["bands"], "band", {"20m": 3, "40m": 2, "10m": 1}),
        (data["modes"], "mode", {"FT8": 3, "CW": 2, "SSB": 1}),
    ):
        assert {r[key]: r["qso_count"] for r in items} == counts
        for row in items:
            assert row["percentage"] == pytest.approx(100 * counts[row[key]] / 6, abs=0.05)
    matrix = get_data(api_client, owner, "band-mode-matrix")
    assert {(r["band"], r["mode"]): r["count"] for r in matrix} == {
        ("20m", "FT8"): 2, ("40m", "CW"): 2, ("20m", "SSB"): 1, ("10m", "FT8"): 1}
    ranks = get_data(api_client, owner, "dxcc")
    assert ranks["total_dxcc"] == 3
    assert {r["entity"]: r["count"] for r in ranks["dxcc_list"]} == {"Japan": 3, "Germany": 2, "Canada": 1}
    chart = get_data(api_client, owner, "dxcc-chart")
    assert chart["total_entities"] == 3
    assert set(chart["bands"]) == {"10m", "20m", "40m"}
    assert chart["band_confirmed"] == {"10m": 0, "20m": 1, "40m": 1}
    assert {r["entity"]: r["bands"] for r in chart["entities"]} == {
        "Japan": {"10m": None, "20m": {"count": 3, "confirmed": True}, "40m": None},
        "Germany": {"10m": None, "20m": None, "40m": {"count": 2, "confirmed": True}},
        "Canada": {"10m": {"count": 1, "confirmed": False}, "20m": None, "40m": None}}


def test_paper_and_eqsl_do_not_confirm_dxcc_chart(api_client, db, owner, analysis_data):
    # Remove the two LoTW confirmations; paper/eQSL remain real, distinct signals.
    db.query(QSOLog).filter(QSOLog.user_id == owner.id).update({QSOLog.lotw_rcvd: "N"})
    db.commit()
    chart = get_data(api_client, owner, "dxcc-chart")
    assert chart["band_confirmed"] == {"10m": 0, "20m": 0, "40m": 0}
    assert get_data(api_client, owner, "overview")["confirmed_qso"] == 2


@pytest.mark.parametrize("scope", ["active", "explicit", "all"])
def test_map_grid_prefix_coordinates_and_qsl(api_client, db, owner, analysis_data, scope):
    params = {}
    if scope == "explicit":
        params = {"my_grid": "pm95ZZ"}
    elif scope == "all":
        db.query(Location).filter(Location.user_id == owner.id).update({Location.is_active: False})
        db.commit()
    response = api_client.get("/api/v1/map/grids", headers=owner.headers, params=params)
    assert response.status_code == 200, response.text
    data = response.json()
    # Maidenhead 4-character cell centers: 2 degrees longitude, 1 latitude.
    expected = {
        "active": [("PM95", 1, 1, 35.5, 139.0), ("PM95", 1, 1, 35.5, 139.0), ("JO62", 1, 0, 52.5, 13.0)],
        "explicit": [("JO62", 1, 1, 52.5, 13.0), ("PM95", 1, 0, 35.5, 139.0), ("FN31", 1, 0, 41.5, -73.0)],
        "all": [("PM95", 2, 1, 35.5, 139.0), ("PM95", 1, 1, 35.5, 139.0), ("JO62", 1, 0, 52.5, 13.0), ("JO62", 1, 1, 52.5, 13.0), ("FN31", 1, 0, 41.5, -73.0)],
    }
    assert sorted((r["grid"], r["count"], r["confirmed"], r["lat"], r["lon"]) for r in data["grids"]) == sorted(expected[scope])
    if scope == "all":
        assert (data["my_grid"], data["my_lat"], data["my_lon"]) == (None, None, None)
    else:
        assert (data["my_grid"], data["my_lat"], data["my_lon"]) == ("OM89", 39.5, 117.0)


def test_empty_analysis_and_map(api_client, owner):
    overview = get_data(api_client, owner, "overview")
    for key in ("total_qso", "total_dxcc", "confirmed_qso", "confirmed_dxcc", "monthly_qso", "yearly_qso", "station_count"):
        assert overview[key] == 0
    assert get_data(api_client, owner, "band-mode") == {"bands": [], "modes": []}
    assert get_data(api_client, owner, "band-mode-matrix") == []
    assert get_data(api_client, owner, "dxcc") == {"total_dxcc": 0, "dxcc_list": []}
    assert get_data(api_client, owner, "dxcc-chart") == {
        "bands": [], "entities": [], "band_confirmed": {}, "band_worked": {}, "total_entities": 0}
    response = api_client.get("/api/v1/map/grids", headers=owner.headers)
    assert response.status_code == 200, response.text
    assert response.json() == {"my_grid": None, "my_lat": None, "my_lon": None, "grids": []}
