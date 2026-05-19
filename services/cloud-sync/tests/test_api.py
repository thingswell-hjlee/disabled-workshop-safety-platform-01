"""Cloud Sync - API Tests"""
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
        assert data["service"] == "cloud-sync"
        assert data["cloud_connected"] is True


class TestSyncStatus:
    def test_get_status(self, client):
        response = client.get("/api/v1/sync/status")
        assert response.status_code == 200
        data = response.json()
        assert data["state"] == "ONLINE"
        assert data["pending_events"] == 0


class TestSyncQueue:
    def test_get_queue(self, client):
        response = client.get("/api/v1/sync/queue")
        assert response.status_code == 200
        data = response.json()
        assert data["pending"] == 0
        assert "high_priority" in data

    def test_flush_queue(self, client):
        response = client.post("/api/v1/sync/flush")
        assert response.status_code == 200
        assert response.json()["status"] == "flush_initiated"


class TestSyncControl:
    def test_pause(self, client):
        response = client.post("/api/v1/sync/pause")
        assert response.status_code == 200
        assert response.json()["status"] == "paused"

    def test_resume(self, client):
        response = client.post("/api/v1/sync/resume")
        assert response.status_code == 200
        assert response.json()["status"] == "resumed"


class TestSyncStats:
    def test_get_stats(self, client):
        response = client.get("/api/v1/sync/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_synced" in data
        assert "queue_depth" in data


class TestConnection:
    def test_get_connection(self, client):
        response = client.get("/api/v1/sync/connection")
        assert response.status_code == 200
        data = response.json()
        assert data["protocol"] == "mqtt"
        assert data["tls_version"] == "TLSv1.2"

    def test_reconnect(self, client):
        response = client.post("/api/v1/sync/reconnect")
        assert response.status_code == 200
        assert response.json()["status"] == "reconnect_initiated"
