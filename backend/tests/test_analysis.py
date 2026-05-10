import pytest
from unittest.mock import patch, MagicMock
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_analysis_api_health():
    """Test analysis endpoint health check"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/analysis/health")
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_start_analysis_unauthorized():
    """Test starting analysis without auth returns 401"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/analysis/some-task-id/start")
        assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_get_analysis_result_unauthorized():
    """Test getting analysis result without auth returns 401"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/analysis/some-task-id/result")
        assert response.status_code in [401, 403]