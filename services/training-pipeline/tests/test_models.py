"""Training Pipeline - Model Tests"""
import pytest
from src.models import (
    PipelineState, JobState, OptimizationType,
    PipelineStatus, DatasetInfo, TrainingConfig, TrainingJob,
    TrainingMetrics, ModelArtifact, DeploymentStatus,
)


class TestPipelineStatus:
    def test_default_idle(self):
        status = PipelineStatus()
        assert status.state == PipelineState.IDLE
        assert status.active_model_version == "v1.0.0-edge"
        assert status.gpu_available is True


class TestTrainingConfig:
    def test_default_config(self):
        config = TrainingConfig()
        assert config.epochs == 50
        assert config.batch_size == 16
        assert config.image_size == 640
        assert config.augmentation is True

    def test_custom_config(self):
        config = TrainingConfig(epochs=30, batch_size=8, learning_rate=0.0005)
        assert config.epochs == 30
        assert config.learning_rate == 0.0005


class TestTrainingJob:
    def test_create_job(self):
        job = TrainingJob(job_id="TRN-20250519-001")
        assert job.state == JobState.QUEUED
        assert job.current_epoch == 0
        assert job.total_epochs == 50

    def test_running_job(self):
        job = TrainingJob(
            job_id="TRN-20250519-001",
            state=JobState.RUNNING,
            current_epoch=25,
            best_loss=0.045,
            metrics={"mAP50": 0.82},
        )
        assert job.current_epoch == 25
        assert job.metrics["mAP50"] == 0.82


class TestTrainingMetrics:
    def test_good_metrics(self):
        metrics = TrainingMetrics(
            accuracy=0.87,
            precision=0.85,
            recall=0.82,
            f1_score=0.83,
            mAP50=0.88,
            mAP50_95=0.65,
            inference_ms=12.5,
        )
        assert metrics.f1_score == 0.83
        assert metrics.inference_ms == 12.5


class TestModelArtifact:
    def test_unoptimized_model(self):
        model = ModelArtifact(
            model_version="v1.1.0",
            model_type="object_detection",
            trained_at="2025-05-19T10:00:00.000Z",
            dataset_id="DS-001",
        )
        assert model.optimized is False
        assert model.optimization_type is None

    def test_optimized_model(self):
        model = ModelArtifact(
            model_version="v1.1.0-edge",
            model_type="object_detection",
            trained_at="2025-05-19T10:00:00.000Z",
            dataset_id="DS-001",
            optimized=True,
            optimization_type=OptimizationType.TENSORRT_INT8,
            file_size_mb=15.2,
        )
        assert model.optimized is True
        assert model.optimization_type == OptimizationType.TENSORRT_INT8


class TestDeploymentStatus:
    def test_default_active(self):
        status = DeploymentStatus()
        assert status.state == "active"
        assert status.health_check_passed is True
        assert status.accuracy_degradation_percent == 0.0
