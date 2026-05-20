"""
Platform 1.0 Schema Models (Pydantic v2)
=========================================
PR #16 event-message-schema.md 기준 Pydantic 모델 정의.
이 모듈은 스키마 검증의 Single Source of Truth 역할을 한다.

주의: 이 파일은 스키마 문서를 구현한 것이며, 스키마를 변경하지 않는다.
"""

import json
import re
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator


# ──────────────────────────────────────────────────────────────────────
# Enum Definitions (from interface-schema.md Section 3)
# ──────────────────────────────────────────────────────────────────────

VALID_EVENT_TYPES = {
    "FALL_DETECTED",
    "COLLAPSE_DETECTED",
    "ZONE_INTRUSION",
    "STILLNESS_DETECTED",
    "HAZARDOUS_ACTION",
    "FIRE_DETECTED",
    "HEARTRATE_ABNORMAL",
    "TEMPERATURE_ABNORMAL",
    "BAND_FALL_DETECTED",
    "BAND_DISCONNECTED",
    "ENV_THRESHOLD_EXCEEDED",
    "DEVICE_OFFLINE",
    "DEVICE_ONLINE",
    "NORMAL_RESTORED",
    "SYSTEM_ALERT",
}

VALID_RISK_LEVELS = {"CRITICAL", "WARNING", "NORMAL"}

VALID_EVENT_STATES = {"ACTIVE", "ACKNOWLEDGED", "ARCHIVED"}

VALID_DEVICE_TYPES = {
    "IP_CAMERA",
    "SMART_BAND",
    "ENV_SENSOR",
    "FIRE_CONTACT",
    "ALARM_DEVICE",
    "NVR",
}

VALID_DEVICE_STATUSES = {"CONNECTED", "DISCONNECTED", "ERROR", "RECONNECTING"}

# Vision AI event types that require confidence and model_version
VISION_AI_EVENT_TYPES = {
    "FALL_DETECTED",
    "COLLAPSE_DETECTED",
    "ZONE_INTRUSION",
    "STILLNESS_DETECTED",
    "HAZARDOUS_ACTION",
}

# Smart Band event types that require worker_id
BAND_EVENT_TYPES = {
    "HEARTRATE_ABNORMAL",
    "TEMPERATURE_ABNORMAL",
    "BAND_FALL_DETECTED",
    "BAND_DISCONNECTED",
}

# Event types that MUST have CRITICAL risk_level (C-001)
CRITICAL_EVENT_TYPES = {"FALL_DETECTED", "COLLAPSE_DETECTED", "FIRE_DETECTED"}

# Priority mapping for cloud queue (C-004)
RISK_TO_PRIORITY = {
    "CRITICAL": "HIGH",
    "WARNING": "NORMAL",
    "NORMAL": "LOW",
}

# ──────────────────────────────────────────────────────────────────────
# Regex Patterns (from interface-schema.md Section 2)
# ──────────────────────────────────────────────────────────────────────

PATTERN_EVENT_ID = r"^EVT-\d{14}-\d{3}$"
PATTERN_SITE_ID = r"^SITE-\d{3}$"
PATTERN_DEVICE_ID = r"^(CAM|BAND|ENV|FIRE|NVR|ALARM)-\d{3}$"
PATTERN_WORKER_ID = r"^WKR-\d{4}$"
PATTERN_CAMERA_ID = r"^CAM-\d{3}$"
PATTERN_BAND_ID = r"^BAND-\d{3}$"
PATTERN_SENSOR_ID = r"^ENV-\d{3}$"
PATTERN_MODEL_VERSION = r"^v\d+\.\d+\.\d+-(tao|pretrained|custom)-(ds|cloud)$"
PATTERN_TIMESTAMP = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$"


# ──────────────────────────────────────────────────────────────────────
# Sub-Models (EventContext)
# ──────────────────────────────────────────────────────────────────────


class VideoClipContext(BaseModel):
    clip_path: str
    clip_s3_key: Optional[str] = None
    duration_sec: int
    pre_event_sec: int
    post_event_sec: int
    thumbnail_path: Optional[str] = None


class SensorSnapshot(BaseModel):
    data_type: str
    value: float
    unit: str
    threshold: float
    duration_above_threshold_sec: Optional[int] = None


class InferenceDetail(BaseModel):
    model_version: str
    class_id: int
    class_label: str
    confidence: float = Field(ge=0.0, le=1.0)
    bbox: dict
    tracker_id: Optional[int] = None
    frame_number: Optional[int] = None

    @field_validator("bbox")
    @classmethod
    def validate_bbox(cls, v: dict) -> dict:
        required_keys = {"x", "y", "w", "h"}
        if not required_keys.issubset(v.keys()):
            raise ValueError(f"bbox must contain keys: {required_keys}")
        for key in required_keys:
            val = v[key]
            if not isinstance(val, (int, float)) or val < 0.0 or val > 1.0:
                raise ValueError(f"bbox.{key} must be between 0.0 and 1.0")
        return v


class SystemState(BaseModel):
    gpu_utilization: float = Field(ge=0.0, le=1.0)
    active_pipelines: int
    pending_events: int
    uptime_sec: int


class EventContext(BaseModel):
    video_clip: Optional[VideoClipContext] = None
    sensor_snapshot: Optional[SensorSnapshot] = None
    inference_detail: Optional[InferenceDetail] = None
    system_state: Optional[SystemState] = None


# ──────────────────────────────────────────────────────────────────────
# Main Model: SafetyEvent (Canonical Event Message)
# ──────────────────────────────────────────────────────────────────────


class SafetyEvent(BaseModel):
    """
    Platform 1.0 Canonical Safety Event.
    Reference: docs/event-message-schema.md
    """

    # Platform 1.0 Required Fields
    event_id: str = Field(..., pattern=PATTERN_EVENT_ID)
    site_id: str = Field(..., pattern=PATTERN_SITE_ID)
    device_id: str = Field(..., pattern=PATTERN_DEVICE_ID)
    event_type: str
    risk_level: str
    timestamp: str
    event_state: str

    # Platform 1.0 Optional Fields
    worker_id: Optional[str] = Field(None, pattern=PATTERN_WORKER_ID)
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    model_version: Optional[str] = Field(None, pattern=PATTERN_MODEL_VERSION)
    context: Optional[EventContext] = None

    # Platform 2.0 Reserved (always null in 1.0)
    feedback_type: Optional[str] = None
    activity_index_history: Optional[list] = None
    baseline_profile: Optional[dict] = None

    # Platform 3.0 Reserved (always null in 1.0)
    reanalysis_result: Optional[dict] = None
    audit_hash: Optional[str] = None
    rag_reference: Optional[dict] = None

    @field_validator("event_type")
    @classmethod
    def validate_event_type(cls, v: str) -> str:
        if v not in VALID_EVENT_TYPES:
            raise ValueError(
                f"Invalid event_type: '{v}'. Must be one of: {sorted(VALID_EVENT_TYPES)}"
            )
        return v

    @field_validator("risk_level")
    @classmethod
    def validate_risk_level(cls, v: str) -> str:
        if v not in VALID_RISK_LEVELS:
            raise ValueError(
                f"Invalid risk_level: '{v}'. Must be one of: {sorted(VALID_RISK_LEVELS)}"
            )
        return v

    @field_validator("event_state")
    @classmethod
    def validate_event_state(cls, v: str) -> str:
        if v not in VALID_EVENT_STATES:
            raise ValueError(
                f"Invalid event_state: '{v}'. Must be one of: {sorted(VALID_EVENT_STATES)}"
            )
        return v

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v: str) -> str:
        if not re.match(PATTERN_TIMESTAMP, v):
            raise ValueError(
                "Timestamp must be ISO 8601 UTC with milliseconds: YYYY-MM-DDTHH:mm:ss.mmmZ"
            )
        # Validate it's a real date
        try:
            dt = datetime.strptime(v, "%Y-%m-%dT%H:%M:%S.%fZ")
            dt = dt.replace(tzinfo=timezone.utc)
            # Allow max +5 seconds tolerance for future timestamps
            now = datetime.now(timezone.utc)
            from datetime import timedelta

            if dt > now + timedelta(seconds=5):
                raise ValueError("Timestamp must not be in the future (max +5s tolerance)")
        except ValueError as e:
            if "Timestamp must not be" in str(e):
                raise
            raise ValueError(f"Invalid timestamp value: {v}")
        return v


# ──────────────────────────────────────────────────────────────────────
# Redis Stream Models
# ──────────────────────────────────────────────────────────────────────


class DsEventsMessage(BaseModel):
    """stream:ds-events message schema (from redis-streams-schema.md)"""

    event_id: str = Field(..., pattern=PATTERN_EVENT_ID)
    site_id: str = Field(..., pattern=PATTERN_SITE_ID)
    source_id: str
    device_id: str = Field(..., pattern=r"^CAM-\d{3}$")
    event_type: str
    timestamp: str
    model_version: str = Field(..., pattern=PATTERN_MODEL_VERSION)
    inference: dict

    @field_validator("event_type")
    @classmethod
    def validate_event_type(cls, v: str) -> str:
        if v not in VALID_EVENT_TYPES:
            raise ValueError(f"Invalid event_type: '{v}'")
        return v

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v: str) -> str:
        if not re.match(PATTERN_TIMESTAMP, v):
            raise ValueError("Timestamp must be ISO 8601 UTC with milliseconds")
        return v

    @field_validator("inference")
    @classmethod
    def validate_inference(cls, v: dict) -> dict:
        if "pgie" not in v:
            raise ValueError("inference must contain 'pgie'")
        if "tracker" not in v:
            raise ValueError("inference must contain 'tracker'")
        pgie = v["pgie"]
        if pgie is not None:
            for key in ("class_id", "confidence", "label", "bbox"):
                if key not in pgie:
                    raise ValueError(f"inference.pgie must contain '{key}'")
        tracker = v["tracker"]
        if tracker is not None:
            for key in ("object_id", "age_frames"):
                if key not in tracker:
                    raise ValueError(f"inference.tracker must contain '{key}'")
        return v


class SensorsMessage(BaseModel):
    """stream:sensors message schema"""

    event_id: str = Field(..., pattern=PATTERN_EVENT_ID)
    site_id: str = Field(..., pattern=PATTERN_SITE_ID)
    device_id: str = Field(..., pattern=PATTERN_DEVICE_ID)
    worker_id: Optional[str] = Field(None, pattern=PATTERN_WORKER_ID)
    event_type: str
    timestamp: str
    data_type: str
    value: float
    source: str

    @field_validator("event_type")
    @classmethod
    def validate_event_type(cls, v: str) -> str:
        if v not in VALID_EVENT_TYPES:
            raise ValueError(f"Invalid event_type: '{v}'")
        return v

    @field_validator("data_type")
    @classmethod
    def validate_data_type(cls, v: str) -> str:
        valid = {"HEARTRATE", "TEMPERATURE", "FALL", "GAS", "HUMIDITY", "DUST", "DISCONNECT"}
        if v not in valid:
            raise ValueError(f"Invalid data_type: '{v}'. Must be one of: {sorted(valid)}")
        return v

    @field_validator("source")
    @classmethod
    def validate_source(cls, v: str) -> str:
        valid = {"SMART_BAND", "ENV_SENSOR", "FIRE_CONTACT"}
        if v not in valid:
            raise ValueError(f"Invalid source: '{v}'. Must be one of: {sorted(valid)}")
        return v


class AlarmsMessage(BaseModel):
    """stream:alarms message schema"""

    event_id: str = Field(..., pattern=PATTERN_EVENT_ID)
    site_id: str = Field(..., pattern=PATTERN_SITE_ID)
    risk_level: str
    action: str
    timestamp: str
    source_event_type: str

    @field_validator("risk_level")
    @classmethod
    def validate_risk_level(cls, v: str) -> str:
        if v not in VALID_RISK_LEVELS:
            raise ValueError(f"Invalid risk_level: '{v}'")
        return v

    @field_validator("action")
    @classmethod
    def validate_action(cls, v: str) -> str:
        valid = {"SIREN_ON", "LIGHT_ON", "ALL_ON", "ALL_OFF"}
        if v not in valid:
            raise ValueError(f"Invalid action: '{v}'. Must be one of: {sorted(valid)}")
        return v

    @field_validator("source_event_type")
    @classmethod
    def validate_source_event_type(cls, v: str) -> str:
        if v not in VALID_EVENT_TYPES:
            raise ValueError(f"Invalid source_event_type: '{v}'")
        return v


class DashboardMessage(BaseModel):
    """stream:dashboard message schema"""

    event_id: str = Field(..., pattern=PATTERN_EVENT_ID)
    site_id: str = Field(..., pattern=PATTERN_SITE_ID)
    device_id: str = Field(..., pattern=PATTERN_DEVICE_ID)
    worker_id: Optional[str] = Field(None, pattern=PATTERN_WORKER_ID)
    event_type: str
    risk_level: str
    timestamp: str
    event_state: str
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    model_version: Optional[str] = Field(None, pattern=PATTERN_MODEL_VERSION)
    context: dict

    @field_validator("worker_id", mode="before")
    @classmethod
    def empty_string_to_none_worker(cls, v):
        """Redis stores null as empty string; normalize to None"""
        if v == "" or v is None:
            return None
        return v

    @field_validator("model_version", mode="before")
    @classmethod
    def empty_string_to_none_model(cls, v):
        """Redis stores null as empty string; normalize to None"""
        if v == "" or v is None:
            return None
        return v

    @field_validator("confidence", mode="before")
    @classmethod
    def empty_string_to_none_confidence(cls, v):
        """Redis stores null as empty string; normalize to None"""
        if v == "" or v is None:
            return None
        return float(v) if isinstance(v, str) else v

    @field_validator("context", mode="before")
    @classmethod
    def parse_context_json(cls, v):
        """Parse JSON string context from Redis"""
        if isinstance(v, str):
            return json.loads(v)
        return v

    @field_validator("event_type")
    @classmethod
    def validate_event_type(cls, v: str) -> str:
        if v not in VALID_EVENT_TYPES:
            raise ValueError(f"Invalid event_type: '{v}'")
        return v

    @field_validator("context")
    @classmethod
    def validate_context(cls, v: dict) -> dict:
        if "summary" not in v:
            raise ValueError("context must contain 'summary'")
        if "clip_available" not in v:
            raise ValueError("context must contain 'clip_available'")
        return v


class CloudQueueMessage(BaseModel):
    """stream:cloud-queue message schema"""

    event_id: str = Field(..., pattern=PATTERN_EVENT_ID)
    site_id: str = Field(..., pattern=PATTERN_SITE_ID)
    device_id: str = Field(..., pattern=PATTERN_DEVICE_ID)
    worker_id: Optional[str] = Field(None, pattern=PATTERN_WORKER_ID)
    event_type: str
    risk_level: str
    timestamp: str
    idempotency_key: str
    priority: str
    clip_path: Optional[str] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    model_version: Optional[str] = Field(None, pattern=PATTERN_MODEL_VERSION)

    @field_validator("worker_id", mode="before")
    @classmethod
    def empty_string_to_none_worker(cls, v):
        """Redis stores null as empty string; normalize to None"""
        if v == "" or v is None:
            return None
        return v

    @field_validator("model_version", mode="before")
    @classmethod
    def empty_string_to_none_model(cls, v):
        """Redis stores null as empty string; normalize to None"""
        if v == "" or v is None:
            return None
        return v

    @field_validator("confidence", mode="before")
    @classmethod
    def empty_string_to_none_confidence(cls, v):
        """Redis stores null as empty string; normalize to None"""
        if v == "" or v is None:
            return None
        return float(v) if isinstance(v, str) else v

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: str) -> str:
        valid = {"HIGH", "NORMAL", "LOW"}
        if v not in valid:
            raise ValueError(f"Invalid priority: '{v}'. Must be one of: {sorted(valid)}")
        return v

    @field_validator("idempotency_key")
    @classmethod
    def validate_idempotency_key(cls, v: str) -> str:
        # Must be {site_id}:{event_id}
        if ":" not in v:
            raise ValueError("idempotency_key must be in format '{site_id}:{event_id}'")
        return v


class ClipTriggerMessage(BaseModel):
    """stream:clip-trigger message schema"""

    event_id: str = Field(..., pattern=PATTERN_EVENT_ID)
    site_id: str = Field(..., pattern=PATTERN_SITE_ID)
    device_id: str = Field(..., pattern=r"^CAM-\d{3}$")
    trigger_ts: str
    pre_sec: int = Field(gt=0)
    post_sec: int = Field(gt=0)

    @field_validator("trigger_ts")
    @classmethod
    def validate_trigger_ts(cls, v: str) -> str:
        if not re.match(PATTERN_TIMESTAMP, v):
            raise ValueError("trigger_ts must be ISO 8601 UTC with milliseconds")
        return v


# ──────────────────────────────────────────────────────────────────────
# MQTT Models
# ──────────────────────────────────────────────────────────────────────


class MqttEventPayload(BaseModel):
    """MQTT safety/{site_id}/events payload"""

    event_id: str = Field(..., pattern=PATTERN_EVENT_ID)
    site_id: str = Field(..., pattern=PATTERN_SITE_ID)
    device_id: str = Field(..., pattern=PATTERN_DEVICE_ID)
    worker_id: Optional[str] = Field(None, pattern=PATTERN_WORKER_ID)
    event_type: str
    risk_level: str
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    model_version: Optional[str] = Field(None, pattern=PATTERN_MODEL_VERSION)
    timestamp: str
    context_summary: str
    clip_s3_key: Optional[str] = None
    idempotency_key: str

    @field_validator("event_type")
    @classmethod
    def validate_event_type(cls, v: str) -> str:
        if v not in VALID_EVENT_TYPES:
            raise ValueError(f"Invalid event_type: '{v}'")
        return v

    @field_validator("risk_level")
    @classmethod
    def validate_risk_level(cls, v: str) -> str:
        if v not in VALID_RISK_LEVELS:
            raise ValueError(f"Invalid risk_level: '{v}'")
        return v


class MqttStatusPayload(BaseModel):
    """MQTT safety/{site_id}/status payload"""

    site_id: str = Field(..., pattern=PATTERN_SITE_ID)
    timestamp: str
    edge_status: str
    deepstream_fps: list
    gpu_utilization: float = Field(ge=0.0, le=1.0)
    active_cameras: int = Field(ge=0)
    active_bands: int = Field(ge=0)
    pending_cloud_events: int = Field(ge=0)

    @field_validator("edge_status")
    @classmethod
    def validate_edge_status(cls, v: str) -> str:
        valid = {"HEALTHY", "DEGRADED", "ERROR"}
        if v not in valid:
            raise ValueError(f"Invalid edge_status: '{v}'. Must be one of: {sorted(valid)}")
        return v


class MqttModelDeployCommand(BaseModel):
    """MQTT safety/{site_id}/models - Cloud to Edge"""

    action: str
    model_version: str = Field(..., pattern=PATTERN_MODEL_VERSION)
    model_type: str
    s3_uri: str
    timestamp: str

    @field_validator("action")
    @classmethod
    def validate_action(cls, v: str) -> str:
        valid = {"DEPLOY", "ROLLBACK", "STATUS_REQUEST"}
        if v not in valid:
            raise ValueError(f"Invalid action: '{v}'")
        return v

    @field_validator("model_type")
    @classmethod
    def validate_model_type(cls, v: str) -> str:
        valid = {"pgie", "sgie"}
        if v not in valid:
            raise ValueError(f"Invalid model_type: '{v}'")
        return v


class MqttModelStatusReport(BaseModel):
    """MQTT safety/{site_id}/models - Edge to Cloud"""

    site_id: str = Field(..., pattern=PATTERN_SITE_ID)
    action: str
    model_version: str = Field(..., pattern=PATTERN_MODEL_VERSION)
    status: str
    progress: Optional[float] = Field(None, ge=0.0, le=1.0)
    error_message: Optional[str] = None
    timestamp: str

    @field_validator("action")
    @classmethod
    def validate_action(cls, v: str) -> str:
        if v != "DEPLOY_STATUS":
            raise ValueError(f"Status report action must be 'DEPLOY_STATUS', got '{v}'")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        valid = {"DOWNLOADING", "STAGED", "DEPLOYING", "ACTIVE", "FAILED", "ROLLBACK"}
        if v not in valid:
            raise ValueError(f"Invalid status: '{v}'")
        return v


# ──────────────────────────────────────────────────────────────────────
# Model Package Models
# ──────────────────────────────────────────────────────────────────────


class ModelMetrics(BaseModel):
    mAP: float = Field(ge=0.0, le=1.0)
    inference_time_ms: float = Field(gt=0)
    fps: float = Field(gt=0)
    classes: int = Field(gt=0)


class ModelEntry(BaseModel):
    model_version: str = Field(..., pattern=PATTERN_MODEL_VERSION)
    model_type: str
    model_name: str
    framework: str
    precision: str
    engine_path: str
    labels_path: str
    status: str
    deployed_at: str
    metrics: ModelMetrics

    @field_validator("model_type")
    @classmethod
    def validate_model_type(cls, v: str) -> str:
        valid = {"pgie", "sgie"}
        if v not in valid:
            raise ValueError(f"Invalid model_type: '{v}'")
        return v

    @field_validator("framework")
    @classmethod
    def validate_framework(cls, v: str) -> str:
        valid = {"TAO", "PyTorch", "TensorFlow", "ONNX"}
        if v not in valid:
            raise ValueError(f"Invalid framework: '{v}'")
        return v

    @field_validator("precision")
    @classmethod
    def validate_precision(cls, v: str) -> str:
        valid = {"FP16", "FP32", "INT8"}
        if v not in valid:
            raise ValueError(f"Invalid precision: '{v}'")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        valid = {"ACTIVE", "STAGED", "ROLLBACK", "ARCHIVED"}
        if v not in valid:
            raise ValueError(f"Invalid status: '{v}'")
        return v


class ModelRegistry(BaseModel):
    schema_version: str
    site_id: str = Field(..., pattern=PATTERN_SITE_ID)
    last_updated: str
    models: list[ModelEntry]
