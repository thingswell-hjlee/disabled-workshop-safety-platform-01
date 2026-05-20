"""AI Inference - Data Models & Type Definitions

PR #16 동결 스키마 기준으로 정의.
event_type, risk_level은 packages/sdk-common/src/constants.py에서 import하여 사용.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class EventType(str, Enum):
    """PR #16 동결 event_type enum (15종)"""
    # Vision AI events
    FALL_DETECTED = "FALL_DETECTED"
    COLLAPSE_DETECTED = "COLLAPSE_DETECTED"
    ZONE_INTRUSION = "ZONE_INTRUSION"
    STILLNESS_DETECTED = "STILLNESS_DETECTED"
    HAZARDOUS_ACTION = "HAZARDOUS_ACTION"
    FIRE_DETECTED = "FIRE_DETECTED"
    # Smart Band events
    HEARTRATE_ABNORMAL = "HEARTRATE_ABNORMAL"
    TEMPERATURE_ABNORMAL = "TEMPERATURE_ABNORMAL"
    BAND_FALL_DETECTED = "BAND_FALL_DETECTED"
    BAND_DISCONNECTED = "BAND_DISCONNECTED"
    # Environmental Sensor events
    ENV_THRESHOLD_EXCEEDED = "ENV_THRESHOLD_EXCEEDED"
    # Device status events
    DEVICE_OFFLINE = "DEVICE_OFFLINE"
    DEVICE_ONLINE = "DEVICE_ONLINE"
    # System events
    NORMAL_RESTORED = "NORMAL_RESTORED"
    SYSTEM_ALERT = "SYSTEM_ALERT"


class RiskLevel(str, Enum):
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    NORMAL = "NORMAL"


class ModelType(str, Enum):
    OBJECT_DETECTION = "object_detection"
    FALL_DETECTION = "fall_detection"
    BEHAVIOR_ANALYSIS = "behavior_analysis"
    ZONE_MONITOR = "zone_monitor"


@dataclass
class BoundingBox:
    """Normalized bounding box (0.0~1.0) per PR #16 inference_detail.bbox"""
    x: float
    y: float
    w: float
    h: float


@dataclass
class DetectionResult:
    """Single detection result from AI model"""
    event_type: EventType
    confidence: float
    bbox: Optional[BoundingBox] = None
    zone: Optional[str] = None
    model_version: str = ""  # Format: v{M}.{m}.{p}-{tool}-{target}


@dataclass
class InferenceEvent:
    """Event produced by inference engine → stream:ds-events"""
    event_id: str
    site_id: str
    device_id: str
    worker_id: Optional[str]
    event_type: EventType
    risk_level: RiskLevel
    confidence: float
    model_version: str  # Format: v{M}.{m}.{p}-{tool}-{target} (e.g. v1.0.0-tao-ds)
    timestamp: str
    source_id: str = "pipeline-0"
    payload: dict = field(default_factory=dict)


@dataclass
class ModelInfo:
    """Loaded model information"""
    model_id: str
    model_type: ModelType
    model_version: str  # Format: v{M}.{m}.{p}-{tool}-{target}
    framework: str  # "TAO" | "PyTorch" | "TensorFlow" | "ONNX"
    precision: str = "FP16"  # "FP16" | "FP32" | "INT8"
    input_shape: List[int] = field(default_factory=lambda: [1, 3, 544, 960])
    device: str = "cuda:0"
    status: str = "ACTIVE"  # ACTIVE | STAGED | ROLLBACK | ARCHIVED


@dataclass
class ZoneConfig:
    """Danger zone polygon configuration per camera"""
    camera_id: str
    zone_name: str
    polygon: List[List[float]] = field(default_factory=list)  # [[x,y], ...]
    enabled: bool = True


@dataclass
class InferenceStats:
    """Runtime inference statistics"""
    total_frames_processed: int = 0
    avg_inference_ms: float = 0.0
    fps: float = 0.0
    gpu_utilization_percent: float = 0.0
    gpu_memory_used_mb: float = 0.0
    active_channels: int = 0
    events_generated: int = 0


@dataclass
class ThresholdConfig:
    """Sensor threshold configuration"""
    temperature_max: float = 40.0
    humidity_max: float = 85.0
    co_ppm_max: float = 50.0
    voc_ppb_max: float = 500.0
    heartrate_min: int = 40
    heartrate_max: int = 150
    body_temp_min: float = 35.0
    body_temp_max: float = 38.5
    band_timeout_seconds: int = 30
