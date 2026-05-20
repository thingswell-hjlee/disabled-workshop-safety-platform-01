"""Training Pipeline - API Tests"""
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
        assert data["service"] == "training-pipeline"
        assert data["gpu"]["available"] is True


class TestPipelineStatus:
    def test_get_status(self, client):
        response = client.get("/api/v1/pipeline/status")
        assert response.status_code == 200
        data = response.json()
        assert data["state"] == "IDLE"
        assert data["active_model_version"] == "v1.0.0-edge"


class TestDataCollection:
    def test_list_datasets_empty(self, client):
        response = client.get("/api/v1/data/datasets")
        assert response.status_code == 200
        assert response.json()["datasets"] == []

    def test_trigger_collection(self, client):
        response = client.post("/api/v1/data/collect")
        assert response.status_code == 200
        assert response.json()["status"] == "collection_started"

    def test_get_data_stats(self, client):
        response = client.get("/api/v1/data/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total_samples"] == 0
        assert "train_split" in data


class TestTrainingJobs:
    def test_list_jobs_empty(self, client):
        response = client.get("/api/v1/training/jobs")
        assert response.status_code == 200
        assert response.json()["jobs"] == []

    def test_create_job(self, client):
        config = {"epochs": 30, "batch_size": 8, "dataset_id": "DS-001"}
        response = client.post("/api/v1/training/jobs", json=config)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "queued"
        assert data["job_id"].startswith("TRN-")

    def test_cancel_job(self, client):
        response = client.post("/api/v1/training/jobs/TRN-20250519-001/cancel")
        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"


class TestModels:
    def test_list_models_empty(self, client):
        response = client.get("/api/v1/models")
        assert response.status_code == 200
        assert response.json()["models"] == []

    def test_optimize_model(self, client):
        response = client.post("/api/v1/models/v1.1.0/optimize")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "optimization_started"
        assert data["target"] == "TensorRT_INT8"


class TestDeployment:
    def test_deploy_model(self, client):
        response = client.post("/api/v1/deploy/v1.1.0-edge")
        assert response.status_code == 200
        assert response.json()["status"] == "deployment_started"

    def test_deployment_status(self, client):
        response = client.get("/api/v1/deploy/status")
        assert response.status_code == 200
        data = response.json()
        assert data["current_model"] == "v1.0.0-edge"
        assert data["health_check_passed"] is True

    def test_rollback(self, client):
        response = client.post("/api/v1/deploy/rollback")
        assert response.status_code == 200
        assert response.json()["status"] == "rollback_started"
