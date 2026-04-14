from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_ping():
    r = client.get('/api/health/ping')
    assert r.status_code == 200
    assert r.json() == {"ping": "pong"}


def test_ready():
    r = client.get('/ready')
    assert r.status_code == 200
    assert r.json().get('status') == 'ready'
