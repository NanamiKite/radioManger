import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker
from starlette.websockets import WebSocketDisconnect

from app.database.session import get_db
from app.main import app
from app.services.session_service import SessionService
from app.utils.security import SecurityUtils


@pytest.fixture
def client(db, monkeypatch):
    import app.dependencies as auth
    import app.api.v1.udp as udp
    factory = sessionmaker(bind=db.get_bind(), autoflush=False)
    monkeypatch.setattr(auth, 'SessionLocal', factory)
    monkeypatch.setattr(udp, 'SessionLocal', factory)
    def request_session():
        with factory() as session:
            yield session
    app.middleware_stack = None  # Fresh rate-limit state per isolated client.
    app.dependency_overrides[get_db] = request_session
    with TestClient(app, client=('127.0.0.1', 45555)) as client:
        yield client
    app.dependency_overrides.clear()


def register_login(client, name):
    response = client.post('/api/v1/auth/register', json={
        'username': name, 'email': f'{name}@example.com',
        'password': 'flow-regression-password', 'confirm_password': 'flow-regression-password',
    })
    assert response.status_code == 201, response.text
    response = client.post('/api/v1/auth/login', json={'username': name, 'password': 'flow-regression-password'})
    assert response.status_code == 200, response.text
    body = response.json()
    assert 'refresh_token' not in body
    return body['access_token'], {'Authorization': f"Bearer {body['access_token']}"}


def test_http_ownership_and_logout(client):
    token_a, a = register_login(client, 'operator_a')
    _, b = register_login(client, 'operator_b')
    station = client.post('/api/v1/stations', headers=a, json={'callsign': 'BA1OWN'}).json()
    denied = client.post('/api/v1/locations', headers=b, json={'station_id': station['id'], 'grid_square': 'OM89AA'})
    assert denied.status_code == 404, denied.text
    denied = client.post('/api/v1/logs', headers=b, json={'station_id': station['id'], 'call_sign': 'JA1ABC'})
    assert denied.status_code == 404
    created = client.post('/api/v1/locations', headers=a, json={'station_id': station['id'], 'grid_square': 'OM89AA'})
    assert created.status_code == 201, created.text
    log = client.post('/api/v1/logs', headers=a, json={'call_sign': 'JA1ABC', 'freq': 14.074, 'band': '20m', 'mode': 'FT8'})
    assert log.status_code == 201, log.text
    assert client.get('/api/v1/logs', headers=b).json()['total'] == 0
    assert client.get('/api/v1/logs', headers=a).json()['items'][0]['station_callsign'] == 'BA1OWN'
    assert client.post('/api/v1/auth/logout', headers=a).status_code == 200
    assert client.get('/api/v1/auth/me', headers=a).status_code == 401
    with client.websocket_connect('/api/v1/udp/ws') as websocket:
        websocket.send_json({'token': token_a})
        with pytest.raises(WebSocketDisconnect) as closed:
            websocket.receive_json()
        assert closed.value.code == 4401


def test_websocket_save_rechecks_revocation(client, db):
    token, headers = register_login(client, 'operator_ws')
    client.post('/api/v1/stations', headers=headers, json={'callsign': 'BA1OWN'})
    station = client.get('/api/v1/stations', headers=headers).json()[0]
    client.post('/api/v1/locations', headers=headers, json={'station_id': station['id'], 'grid_square': 'OM89AA'})
    with client.websocket_connect('/api/v1/udp/ws') as websocket:
        websocket.send_json({'token': token})
        websocket.send_json({'action': 'save', 'data': {'call_sign': 'JA1ABC'}})
        assert websocket.receive_json()['type'] == 'qso_saved'
        SessionService.remove_session(db, SecurityUtils.decode_token(token)['jti'])
        db.commit()
        websocket.send_json({'action': 'save', 'data': {'call_sign': 'JA2ABC'}})
        with pytest.raises(WebSocketDisconnect) as closed:
            websocket.receive_json()
        assert closed.value.code == 4401
    from app.models.qso_log import QSOLog
    assert db.query(QSOLog).count() == 1


@pytest.mark.parametrize('path', ['/api/v1/dxcluster/ws', '/api/v1/udp/ws'])
def test_websocket_no_query_auth_and_clean_disconnect(client, path):
    token, _ = register_login(client, 'operator_invalid')
    with client.websocket_connect(f'{path}?token={token}') as websocket:
        websocket.send_json({'token': 'invalid'})
        with pytest.raises(WebSocketDisconnect) as closed:
            websocket.receive_json()
        assert closed.value.code == 4401
    with client.websocket_connect(path) as websocket:
        websocket.send_json({'token': token})
    from app.services.udp_listener_service import udp_listener
    from app.services.dxcluster_manager import dxcluster_manager
    assert udp_listener._subscribers == {}
    assert dxcluster_manager.subscriber_count == 0
