"""AI Inference Engine - API Tests"""
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
        assert data["service"] == "ai-inference"
        assert "gpu" in data
        assert data["gpu"]["available"] is True


class TestModelsAPI:
    def test_get_models_list(self, client):
        response = client.get("/api/v1/models")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["model_id"] == "yolov8-safety"

    def test_reload_model(self, client):
        response = client.post("/api/v1/models/yolov8-safety/reload")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "accepted"


class TestInferenceStats:
    def test_get_stats(self, client):
        response = client.get("/api/v1/inference/stats")
        assert response.status_code == 200
        data = response.json()
        assert "fps" in data
        assert "gpu_utilization_percent" in data
        assert "active_channels" in data


class TestZonesAPI:
    def test_get_zones_empty(self, client):
        response = client.get("/api/v1/zones")
        assert response.status_code == 200
        data = response.json()
        assert "zones" in data

    def test_set_zone(self, client):
        zone_data = {
            "zone_name": "위험구역A",
            "polygon": [[0, 0], [100, 0], [100, 100], [0, 100]],
            "enabled": True,
        }
        response = client.put("/api/v1/zones/CAM-001", json=zone_data)
        assert response.status_code == 200
        data = response.json()
        assert data["camera_id"] == "CAM-001"
        assert data["action"] == "zone_updated"
