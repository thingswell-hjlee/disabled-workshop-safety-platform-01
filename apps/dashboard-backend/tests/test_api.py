"""Dashboard Backend - API Tests"""
import pytest
from fastapi.testclient import TestClient
from src.api import app


@pytest.fixture
def client():
    return TestClient(app)


class TestHealthCheck:
    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["service"] == "dashboard-backend"


class TestAuth:
    def test_login_success(self, client):
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "admin", "password": "test123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 1800

    def test_login_missing_credentials(self, client):
        response = client.post(
            "/api/v1/auth/login",
            json={"username": "", "password": ""},
        )
        assert response.status_code == 400

    def test_get_current_user(self, client):
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 200
        assert response.json()["role"] == "admin"


class TestDashboard:
    def test_get_summary(self, client):
        response = client.get("/api/v1/dashboard/summary")
        assert response.status_code == 200
        data = response.json()
        assert "critical_count" in data
        assert "warning_count" in data
        assert data["total_cameras"] == 8
        assert data["total_bands"] == 8

    def test_get_devices(self, client):
        response = client.get("/api/v1/dashboard/devices")
        assert response.status_code == 200
        assert "devices" in response.json()

    def test_get_workers(self, client):
        response = client.get("/api/v1/dashboard/workers")
        assert response.status_code == 200
        assert "workers" in response.json()


class TestEvents:
    def test_get_events_empty(self, client):
        response = client.get("/api/v1/events")
        assert response.status_code == 200
        data = response.json()
        assert data["events"] == []
        assert data["total"] == 0

    def test_get_events_with_filter(self, client):
        response = client.get("/api/v1/events?risk_level=CRITICAL&limit=10")
        assert response.status_code == 200
        assert response.json()["limit"] == 10

    def test_get_event_not_found(self, client):
        response = client.get("/api/v1/events/EVT-NOTEXIST")
        assert response.status_code == 404

    def test_acknowledge_event(self, client):
        response = client.post(
            "/api/v1/events/EVT-20250519120000-001/acknowledge",
            json={"acknowledged_by": "admin", "reason": "오탐 확인"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "acknowledged"


class TestSystem:
    def test_get_system_health(self, client):
        response = client.get("/api/v1/system/health")
        assert response.status_code == 200
        data = response.json()
        assert data["overall"] == "healthy"
        assert "device-gateway" in data["services"]

    def test_get_system_metrics(self, client):
        response = client.get("/api/v1/system/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "edge_cpu_percent" in data
        assert "edge_gpu_percent" in data
