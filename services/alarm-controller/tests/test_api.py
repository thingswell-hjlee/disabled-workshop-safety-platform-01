"""Alarm Controller - API Tests"""
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
        assert data["service"] == "alarm-controller"
        assert data["gpio"]["initialized"] is True


class TestAlarmStatus:
    def test_get_status_idle(self, client):
        response = client.get("/api/v1/alarm/status")
        assert response.status_code == 200
        data = response.json()
        assert data["state"] == "IDLE"
        assert data["siren_active"] is False
        assert data["light_active"] is False


class TestAlarmTrigger:
    def test_trigger_all_on(self, client):
        response = client.post(
            "/api/v1/alarm/trigger",
            json={"action": "ALL_ON"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "triggered"

    def test_clear_alarm(self, client):
        response = client.post(
            "/api/v1/alarm/clear",
            json={"cleared_by": "admin", "reason": "상황 종료"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "cleared"


class TestAlarmLogs:
    def test_get_logs_empty(self, client):
        response = client.get("/api/v1/alarm/logs")
        assert response.status_code == 200
        assert response.json()["logs"] == []


class TestAlarmTest:
    def test_run_test(self, client):
        response = client.post("/api/v1/alarm/test")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "test_completed"
        assert data["siren"] == "ok"
