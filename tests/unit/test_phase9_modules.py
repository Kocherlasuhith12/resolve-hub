import pytest
from httpx import ASGITransport, AsyncClient

from resolvehub.app.main import app


@pytest.mark.asyncio
async def test_system_health_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/health/live")
        assert res.status_code == 200
        assert res.json() == {"status": "ok"}
