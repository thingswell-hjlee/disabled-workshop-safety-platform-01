"""Dashboard Backend - Event Message Schema Validation

PR #16 확정 스키마 기준 (docs/event-message-schema.md, docs/aws-iot-message-schema.md).
event_type, risk_level, ID 형식 등을 Pydantic v2로 엄격 검증합니다.
"""

import re
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, Field, field_validator, model_validator


# --- Enums (from docs/interface-schema.md) ---

class EventType(str, Enum):
    FALL_DETECTED = "FALL_DETECTED"
    COLLAPSE_DETECTED = "COLLAPSE_DETECTED"
    ZONE_INTRUSION = "ZONE_INTRUSION"
    STILLNESS_DETECTED = "STILLNESS_DETECTED"
    HAZARDOUS_ACTION = "HAZARDOUS_ACTION"
    FIRE_DETECTED = "FIRE_DETECTED"
    HEARTRATE_ABNORMAL = "HEARTRATE_ABNORMAL"
    TEMPERATURE_ABNORMAL = "TEMPERATURE_ABNORMAL"
    BAND_FALL_DETECTED = "BAND_FALL_DETECTED"
    BAND_DISCONNECTED = "BAND_DISCONNECTED"
    ENV_THRESHOLD_EXCEEDED = "ENV_THRESHOLD_EXCEEDED"
    DEVICE_OFFLINE = "DEVICE_OFFLINE"
    DEVICE_ONLINE = "DEVICE_ONLINE"
    NORMAL_RESTORED = "NORMAL_RESTORED"
    SYSTEM_ALERT = "SYSTEM_ALERT"


class RiskLevel(str, Enum):
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    NORMAL = "NORMAL"


class EventState(str, Enum):
    ACTIVE = "ACTIVE"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    ARCHIVED = "ARCHIVED"


class DeviceType(str, Enum):
    IP_CAMERA = "IP_CAMERA"
    SMART_BAND = "SMART_BAND"
    ENV_SENSOR = "ENV_SENSOR"
    FIRE_CONTACT = "FIRE_CONTACT"
    ALARM_DEVICE = "ALARM_DEVICE"
    NVR = "NVR"


class DeviceStatus(str, Enum):
    CONNECTED = "CONNECTED"
    DISCONNECTED = "DISCONNECTED"
    ERROR = "ERROR"
    RECONNECTING = "RECONNECTING"


class EdgeStatus(str, Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    ERROR = "ERROR"


class ModelStatus(str, Enum):
    STAGED = "STAGED"
    ACTIVE = "ACTIVE"
    ROLLBACK = "ROLLBACK"
    ARCHIVED = "ARCHIVED"


class ModelType(str, Enum):
    PGIE_DETECTION = "PGIE_DETECTION"
    SGIE_ACTION = "SGIE_ACTION"
    CUSTOM = "CUSTOM"


class ModelFramework(str, Enum):
    TENSORRT = "TENSORRT"
    ONNX = "ONNX"
    TAO = "TAO"


class ModelPrecision(str, Enum):
    FP16 = "FP16"
    INT8 = "INT8"
    FP32 = "FP32"


# --- Pattern Constants ---
EVENT_ID_PATTERN = re.compile(r"^EVT-\d{14}-\d{3}$")
SITE_ID_PATTERN = re.compile(r"^SITE-\d{3}$")
DEVICE_ID_PATTERN = re.compile(r"^(CAM|BAND|ENV|FIRE|NVR|ALARM)-\d{3}$")
WORKER_ID_PATTERN = re.compile(r"^WKR-\d{4}$")
MODEL_VERSION_PATTERN = re.compile(r"^v\d+\.\d+\.\d+-(tao|pretrained|custom)-(ds|cloud)$")

# Events that MUST have risk_level=CRITICAL
CRITICAL_ONLY_EVENTS = {
    EventType.FALL_DETECTED,
    EventType.COLLAPSE_DETECTED,
    EventType.FIRE_DETECTED,
}

# Events that require worker_id
WORKER_REQUIRED_EVENTS = {
    EventType.HEARTRATE_ABNORMAL,
    EventType.TEMPERATURE_ABNORMAL,
    EventType.BAND_FALL_DETECTED,
    EventType.BAND_DISCONNECTED,
}

# Vision AI events that require confidence + model_version
VISION_AI_EVENTS = {
    EventType.FALL_DETECTED,
    EventType.COLLAPSE_DETECTED,
    EventType.ZONE_INTRUSION,
    EventType.STILLNESS_DETECTED,
    EventType.HAZARDOUS_ACTION,
}


# --- IoT Event Payload (MQTT safety/{site_id}/events) ---

class IoTEventPayload(BaseModel):
    """
    AWS IoT Core event payload schema.
    Matches docs/aws-iot-message-schema.md Section 2.1.
    """
    event_id: str
    site_id: str
    device_id: str
    worker_id: Optional[str] = None
    event_type: EventType
    risk_level: RiskLevel
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    model_version: Optional[str] = None
    timestamp: str
    context_summary: str
    clip_s3_key: Optional[str] = None
    idempotency_key: str

    @field_validator("event_id")
    @classmethod
    def validate_event_id(cls, v: str) -> str:
        if not EVENT_ID_PATTERN.match(v):
            raise ValueError(f"event_id must match EVT-YYYYMMDDHHmmss-SEQ, got: {v}")
        return v

    @field_validator("site_id")
    @classmethod
    def validate_site_id(cls, v: str) -> str:
        if not SITE_ID_PATTERN.match(v):
            raise ValueError(f"site_id must match SITE-NNN, got: {v}")
        return v

    @field_validator("device_id")
    @classmethod
    def validate_device_id(cls, v: str) -> str:
        if not DEVICE_ID_PATTERN.match(v):
            raise ValueError(f"device_id must match (CAM|BAND|ENV|FIRE|NVR|ALARM)-NNN, got: {v}")
        return v

    @field_validator("worker_id")
    @classmethod
    def validate_worker_id(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not WORKER_ID_PATTERN.match(v):
            raise ValueError(f"worker_id must match WKR-NNNN, got: {v}")
        return v

    @field_validator("model_version")
    @classmethod
    def validate_model_version(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not MODEL_VERSION_PATTERN.match(v):
            raise ValueError(
                f"model_version must match v{{major}}.{{minor}}.{{patch}}-{{tool}}-{{target}}, got: {v}"
            )
        return v

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v: str) -> str:
        try:
            dt = datetime.fromisoformat(v.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            if dt > now + timedelta(seconds=5):
                raise ValueError("timestamp is in the future (max +5s tolerance)")
        except (ValueError, TypeError) as e:
            if "timestamp is in the future" in str(e):
                raise
            raise ValueError(f"timestamp must be valid ISO 8601 UTC, got: {v}")
        return v

    @model_validator(mode="after")
    def validate_business_rules(self):
        """Cross-field business rule validation."""
        # CRITICAL events must have risk_level=CRITICAL
        if self.event_type in CRITICAL_ONLY_EVENTS and self.risk_level != RiskLevel.CRITICAL:
            raise ValueError(
                f"{self.event_type.value} must have risk_level=CRITICAL"
            )

        # Worker-required events must have worker_id
        if self.event_type in WORKER_REQUIRED_EVENTS and self.worker_id is None:
            raise ValueError(
                f"{self.event_type.value} requires worker_id"
            )

        # Vision AI events must have confidence and model_version
        if self.event_type in VISION_AI_EVENTS:
            if self.confidence is None:
                raise ValueError(
                    f"{self.event_type.value} requires confidence"
                )
            if self.model_version is None:
                raise ValueError(
                    f"{self.event_type.value} requires model_version"
                )

        # Idempotency key format check
        expected = f"{self.site_id}:{self.event_id}"
        if self.idempotency_key != expected:
            raise ValueError(
                f"idempotency_key must be '{expected}', got: '{self.idempotency_key}'"
            )

        return self


# --- IoT Status Payload (MQTT safety/{site_id}/status) ---

class IoTStatusPayload(BaseModel):
    """Edge status report payload. Matches docs/aws-iot-message-schema.md Section 2.2."""
    site_id: str
    timestamp: str
    edge_status: EdgeStatus
    deepstream_fps: List[float]
    gpu_utilization: float = Field(ge=0.0, le=1.0)
    active_cameras: int = Field(ge=0)
    active_bands: int = Field(ge=0)
    pending_cloud_events: int = Field(ge=0)

    @field_validator("site_id")
    @classmethod
    def validate_site_id(cls, v: str) -> str:
        if not SITE_ID_PATTERN.match(v):
            raise ValueError(f"site_id must match SITE-NNN, got: {v}")
        return v


# --- API Response Models ---

class EventResponse(BaseModel):
    """Event list item response."""
    event_id: str
    site_id: str
    device_id: str
    worker_id: Optional[str] = None
    event_type: str
    risk_level: str
    confidence: Optional[float] = None
    model_version: Optional[str] = None
    timestamp: str
    state: str
    clip_path: Optional[str] = None
    clip_s3_key: Optional[str] = None


class EventDetailResponse(EventResponse):
    """Event detail response with context."""
    context_summary: Optional[str] = None
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[str] = None
    ack_reason: Optional[str] = None
    idempotency_key: Optional[str] = None
    synced_to_cloud: bool = False
    created_at: Optional[str] = None


class EventListResponse(BaseModel):
    """Paginated event list response."""
    events: List[EventResponse]
    total: int
    limit: int
    offset: int


class DeviceResponse(BaseModel):
    """Device list item response."""
    device_id: str
    device_type: str
    name: str
    status: str
    site_id: str
    zone_id: Optional[str] = None
    last_heartbeat: Optional[str] = None
    metrics: Optional[dict] = None


class DeviceDetailResponse(DeviceResponse):
    """Device detail response."""
    ip_address: Optional[str] = None
    firmware_version: Optional[str] = None
    metadata: Optional[dict] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class DeviceListResponse(BaseModel):
    """Device list response."""
    devices: List[DeviceResponse]
    total: int
    summary: Optional[dict] = None


class ModelVersionResponse(BaseModel):
    """Model version list item."""
    model_version: str
    model_type: str
    model_name: str
    precision: str
    status: str
    deployed_at: Optional[str] = None
    metrics: Optional[dict] = None


class ModelDetailResponse(ModelVersionResponse):
    """Model version detail."""
    framework: Optional[str] = None
    engine_path: Optional[str] = None
    file_size_mb: Optional[float] = None
    trained_at: Optional[str] = None
    s3_key: Optional[str] = None
    site_id: Optional[str] = None
    created_at: Optional[str] = None


class ModelListResponse(BaseModel):
    """Model version list."""
    models: List[ModelVersionResponse]
    total: int


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: dict = Field(default_factory=lambda: {"code": "UNKNOWN", "message": ""})
