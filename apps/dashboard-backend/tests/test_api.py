"""Dashboard Backend - API Tests (Updated for AWS Cloud Integration)

NOTE: 이 테스트 중 DB 의존 테스트(events, devices 등)는 PostgreSQL이 필요합니다.
DB 없이 실행 가능한 테스트는 test_event_validation.py, test_event_api.py 참조.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.api import app


@pytest.fixture
def client():
    from httpx import AsyncClient, ASGITransport
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


class TestHealthCheck:
    @pytest.mark.asyncio
    async def test_health_returns_200(self, client):
        with patch("src.database.check_db_health", new_callable=AsyncMock,
                   return_value={"status": "healthy", "message": "ok"}):
            async with client as ac:
                response = await ac.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["service"] == "dashboard-backend"
            assert data["aws_mode"] == "mock"


class TestAuth:
    @pytest.mark.asyncio
    async def test_login_success(self, client):
        async with client as ac:
            response = await ac.post(
                "/api/v1/auth/login",
                json={"username": "admin", "password": "test123"},
            )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_login_missing_credentials(self, client):
        async with client as ac:
            response = await ac.post(
                "/api/v1/auth/login",
                json={"username": "", "password": ""},
            )
        assert response.status_code == 400


class TestSystemHealth:
    @pytest.mark.asyncio
    async def test_get_system_health(self, client):
        with patch("src.api.check_db_health", new_callable=AsyncMock,
                   return_value={"status": "healthy", "message": "ok"}):
            with patch("src.api.crud.get_latest_edge_status", new_callable=AsyncMock,
                       return_value=None):
                async with client as ac:
                    response = await ac.get("/api/v1/system/health")
                assert response.status_code == 200
                data = response.json()
                assert data["overall"] == "healthy"
                assert "services" in data
