import asyncio

import httpx

from app.main import app


async def fetch_json(path: str):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get(path)
    return response


def test_ping():
    response = asyncio.run(fetch_json("/api/health/ping"))
    assert response.status_code == 200
    assert response.json() == {"ping": "pong"}


def test_ready():
    response = asyncio.run(fetch_json("/ready"))
    assert response.status_code == 200
    assert response.json().get("status") == "ready"
