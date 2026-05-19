"""Device Gateway - API Tests"""
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
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "device-gateway"
        assert data["version"] == "1.0.0"


class TestDevicesAPI:
    def test_get_all_devices_not_implemented(self, client):
        response = client.get("/api/v1/devices")
        assert response.status_code == 501

    def test_get_device_not_implemented(self, client):
        response = client.get("/api/v1/devices/CAM-001")
        assert response.status_code == 501

    def test_reconnect_device(self, client):
        response = client.post("/api/v1/devices/CAM-001/reconnect")
        assert response.status_code == 200
        data = response.json()
        assert data["device_id"] == "CAM-001"
        assert data["action"] == "reconnect"


class TestStreamsAPI:
    def test_get_stream_status(self, client):
        response = client.get("/api/v1/streams/status")
        assert response.status_code == 200
        data = response.json()
        assert "streams" in data
        assert "frames" in data["streams"]
        assert "bio" in data["streams"]
        assert "sensors" in data["streams"]
