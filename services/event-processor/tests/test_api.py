"""Event Processor - API Tests"""
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
        assert data["service"] == "event-processor"


class TestEventsAPI:
    def test_get_events_empty(self, client):
        response = client.get("/api/v1/events")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_event_not_found(self, client):
        response = client.get("/api/v1/events/EVT-20250519120000-999")
        assert response.status_code == 404

    def test_acknowledge_event(self, client):
        response = client.post(
            "/api/v1/events/EVT-20250519120000-001/acknowledge",
            json={"acknowledged_by": "admin", "reason": "오탐 확인"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["state"] == "ACKNOWLEDGED"


class TestRulesAPI:
    def test_get_rules(self, client):
        response = client.get("/api/v1/rules")
        assert response.status_code == 200
        rules = response.json()["rules"]
        assert "FALL_DETECTED" in rules["CRITICAL"]
        assert "ENV_THRESHOLD_EXCEEDED" in rules["WARNING"]

    def test_update_rules(self, client):
        new_rules = {"CRITICAL": ["FALL_DETECTED", "FIRE_DETECTED"]}
        response = client.put("/api/v1/rules", json=new_rules)
        assert response.status_code == 200
