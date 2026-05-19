"""Training Pipeline - Data Models & Type Definitions"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict


class PipelineState(str, Enum):
    IDLE = "IDLE"
    COLLECTING = "COLLECTING"
    TRAINING = "TRAINING"
    OPTIMIZING = "OPTIMIZING"
    DEPLOYING = "DEPLOYING"
    ERROR = "ERROR"


class JobState(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class OptimizationType(str, Enum):
    TENSORRT_FP16 = "TensorRT_FP16"
    TENSORRT_INT8 = "TensorRT_INT8"
    ONNX = "ONNX"


@dataclass
class PipelineStatus:
    """Overall training pipeline status"""
    state: PipelineState = PipelineState.IDLE
    current_job_id: Optional[str] = None
    active_model_version: str = "v1.0.0-edge"
    total_datasets: int = 0
    total_trained_models: int = 0
    gpu_available: bool = True
    disk_usage_percent: float = 0.0


@dataclass
class DatasetInfo:
    """Dataset metadata"""
    dataset_id: str
    name: str
    created_at: str
    site_id: str
    total_samples: int = 0
    train_samples: int = 0
    val_samples: int = 0
    test_samples: int = 0
    event_types: List[str] = field(default_factory=list)
    source_devices: List[str] = field(default_factory=list)


@dataclass
class TrainingConfig:
    """Training hyperparameters"""
    base_model: str = "yolov8n.pt"
    epochs: int = 50
    batch_size: int = 16
    learning_rate: float = 0.001
    image_size: int = 640
    augmentation: bool = True
    early_stopping_patience: int = 10
    dataset_id: str = ""


@dataclass
class TrainingJob:
    """Training job information"""
    job_id: str
    state: JobState = JobState.QUEUED
    config: TrainingConfig = field(default_factory=TrainingConfig)
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    current_epoch: int = 0
    total_epochs: int = 50
    best_loss: Optional[float] = None
    metrics: Dict[str, float] = field(default_factory=dict)
    error_message: Optional[str] = None


@dataclass
class TrainingMetrics:
    """Model performance metrics after training"""
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    mAP50: float = 0.0
    mAP50_95: float = 0.0
    inference_ms: float = 0.0


@dataclass
class ModelArtifact:
    """Trained model artifact"""
    model_version: str
    model_type: str  # "object_detection", "fall_detection"
    trained_at: str
    dataset_id: str
    metrics: TrainingMetrics = field(default_factory=TrainingMetrics)
    optimized: bool = False
    optimization_type: Optional[OptimizationType] = None
    optimized_metrics: Optional[TrainingMetrics] = None
    file_path: str = ""
    file_size_mb: float = 0.0


@dataclass
class DeploymentStatus:
    """Edge deployment status"""
    current_model: str = "v1.0.0-edge"
    previous_model: Optional[str] = None
    deployed_at: Optional[str] = None
    state: str = "active"  # active | deploying | rolling_back | failed
    health_check_passed: bool = True
    accuracy_check_passed: bool = True
    accuracy_degradation_percent: float = 0.0
