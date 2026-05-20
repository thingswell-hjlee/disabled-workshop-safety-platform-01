"""
Event API Integration Tests

Dashboard Backend의 Event 관련 API를 테스트합니다.
실행: pytest apps/dashboard-backend/tests/test_event_api.py -v

NOTE: 이 테스트는 validation endpoint만 테스트합니다 (DB 불필요).
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch, MagicMock
import sys
import os

# Add src to path for proper import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    session = AsyncMock()
    return session


@pytest.fixture
def client(mock_db_session):
    """Create test client with mocked dependencies."""
    # Mock database module before importing app
    with patch.dict(os.environ, {
        "AWS_MODE": "mock",
        "CLOUD_DB_HOST": "localhost",
        "CLOUD_DB_PORT": "5432",
        "CLOUD_DB_NAME": "safety_platform",
        "CLOUD_DB_USER": "safety_admin",
        "CLOUD_DB_PASSWORD": "safety_password",
    }):
        from src.api import app
        from httpx import AsyncClient, ASGITransport
        transport = ASGITransport(app=app)
        return AsyncClient(transport=transport, base_url="http://test")


def _make_valid_event() -> dict:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    return {
        "event_id": "EVT-20250519120000-001",
        "site_id": "SITE-001",
        "device_id": "CAM-001",
        "worker_id": None,
        "event_type": "FALL_DETECTED",
        "risk_level": "CRITICAL",
        "confidence": 0.92,
        "model_version": "v1.0.0-tao-ds",
        "timestamp": now,
        "context_summary": "작업장 A구역 낙상 감지",
        "clip_s3_key": None,
        "idempotency_key": "SITE-001:EVT-20250519120000-001",
    }


class TestEventValidationEndpoint:
    """
    Test /api/v1/validate/event endpoint.
    This endpoint does NOT require database (validation only).
    """

    @pytest.mark.asyncio
    async def test_validate_valid_event(self, client):
        """Valid event should return valid=True."""
        async with client as ac:
            response = await ac.post(
                "/api/v1/validate/event",
                json=_make_valid_event(),
            )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True

    @pytest.mark.asyncio
    async def test_validate_invalid_event_type(self, client):
        """Invalid event_type should return valid=False with errors."""
        payload = _make_valid_event()
        payload["event_type"] = "INVALID_TYPE"
        async with client as ac:
            response = await ac.post("/api/v1/validate/event", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert len(data["errors"]) > 0

    @pytest.mark.asyncio
    async def test_validate_missing_required_field(self, client):
        """Missing event_id should return valid=False."""
        payload = _make_valid_event()
        del payload["event_id"]
        async with client as ac:
            response = await ac.post("/api/v1/validate/event", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False

    @pytest.mark.asyncio
    async def test_validate_wrong_risk_for_critical_event(self, client):
        """FALL_DETECTED with WARNING should fail."""
        payload = _make_valid_event()
        payload["risk_level"] = "WARNING"
        async with client as ac:
            response = await ac.post("/api/v1/validate/event", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False

    @pytest.mark.asyncio
    async def test_validate_fire_from_contact(self, client):
        """FIRE_DETECTED from FIRE-001 without confidence should be valid."""
        payload = _make_valid_event()
        payload["device_id"] = "FIRE-001"
        payload["event_type"] = "FIRE_DETECTED"
        payload["risk_level"] = "CRITICAL"
        payload["confidence"] = None
        payload["model_version"] = None
        async with client as ac:
            response = await ac.post("/api/v1/validate/event", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True


class TestHealthEndpoint:
    """Test /health endpoint."""

    @pytest.mark.asyncio
    async def test_health_endpoint(self, client):
        """Health endpoint should respond."""
        with patch("src.database.check_db_health", new_callable=AsyncMock,
                   return_value={"status": "healthy", "message": "ok"}):
            async with client as ac:
                response = await ac.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["service"] == "dashboard-backend"
            assert data["aws_mode"] == "mock"
