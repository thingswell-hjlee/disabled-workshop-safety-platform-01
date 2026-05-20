"""Platform 공통 상수 및 Enum 정의 - 전 서비스 공유

PR #16 동결 스키마 기준 (docs/interface-schema.md, docs/event-message-schema.md)
"""
from enum import Enum


# --- Risk Level ---
class RiskLevel(str, Enum):
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    NORMAL = "NORMAL"


# --- Event Types (PR #16 동결: 15종) ---
class EventType(str, Enum):
    # Vision AI events (CRITICAL or WARNING)
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


# --- Device Types (PR #16 동결) ---
class DeviceType(str, Enum):
    IP_CAMERA = "IP_CAMERA"
    SMART_BAND = "SMART_BAND"
    ENV_SENSOR = "ENV_SENSOR"
    FIRE_CONTACT = "FIRE_CONTACT"
    ALARM_DEVICE = "ALARM_DEVICE"
    NVR = "NVR"


# --- Device Status ---
class DeviceStatus(str, Enum):
    CONNECTED = "CONNECTED"
    DISCONNECTED = "DISCONNECTED"
    ERROR = "ERROR"
    RECONNECTING = "RECONNECTING"


# --- Event State ---
class EventState(str, Enum):
    ACTIVE = "ACTIVE"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    ARCHIVED = "ARCHIVED"


# --- Alarm Action (PR #16 동결: stream:alarms schema) ---
class AlarmAction(str, Enum):
    SIREN_ON = "SIREN_ON"
    LIGHT_ON = "LIGHT_ON"
    ALL_ON = "ALL_ON"
    ALL_OFF = "ALL_OFF"


# --- Cloud Queue Priority (PR #16 동결) ---
class CloudPriority(str, Enum):
    HIGH = "HIGH"
    NORMAL = "NORMAL"
    LOW = "LOW"


# --- Risk Classification Mapping (PR #16: C-001 규칙) ---
# FALL_DETECTED, COLLAPSE_DETECTED, FIRE_DETECTED → must be CRITICAL
RISK_CLASSIFICATION = {
    RiskLevel.CRITICAL: [
        EventType.FALL_DETECTED,
        EventType.COLLAPSE_DETECTED,
        EventType.FIRE_DETECTED,
    ],
    RiskLevel.WARNING: [
        EventType.ZONE_INTRUSION,
        EventType.STILLNESS_DETECTED,
        EventType.HAZARDOUS_ACTION,
        EventType.HEARTRATE_ABNORMAL,
        EventType.TEMPERATURE_ABNORMAL,
        EventType.BAND_FALL_DETECTED,
        EventType.BAND_DISCONNECTED,
        EventType.ENV_THRESHOLD_EXCEEDED,
    ],
    RiskLevel.NORMAL: [
        EventType.NORMAL_RESTORED,
        EventType.DEVICE_ONLINE,
        EventType.DEVICE_OFFLINE,
        EventType.SYSTEM_ALERT,
    ],
}

# --- Priority Mapping (PR #16: C-004 규칙) ---
RISK_TO_PRIORITY = {
    RiskLevel.CRITICAL: CloudPriority.HIGH,
    RiskLevel.WARNING: CloudPriority.NORMAL,
    RiskLevel.NORMAL: CloudPriority.LOW,
}


# --- Default Thresholds ---
DEFAULT_THRESHOLDS = {
    "temperature_max": 40.0,
    "humidity_max": 85.0,
    "co_ppm_max": 50.0,
    "voc_ppb_max": 500.0,
    "heartrate_min": 40,
    "heartrate_max": 150,
    "body_temp_min": 35.0,
    "body_temp_max": 38.5,
    "band_timeout_seconds": 30,
}


# --- Service Ports ---
SERVICE_PORTS = {
    "device-gateway": 8001,
    "ai-inference": 8002,
    "event-processor": 8003,
    "alarm-controller": 8004,
    "cloud-sync": 8005,
    "training-pipeline": 8006,
    "dashboard-backend": 8080,
}


# --- Redis Streams (PR #16 동결: redis-streams-schema.md) ---
REDIS_STREAMS = {
    "ds_events": "stream:ds-events",
    "sensors": "stream:sensors",
    "alarms": "stream:alarms",
    "dashboard": "stream:dashboard",
    "cloud_queue": "stream:cloud-queue",
    "clip_trigger": "stream:clip-trigger",
}

# --- Consumer Groups (PR #16 동결) ---
CONSUMER_GROUPS = {
    "stream:ds-events": "cg-event-engine",
    "stream:sensors": "cg-event-engine",
    "stream:alarms": "cg-alarm-ctrl",
    "stream:dashboard": "cg-dashboard",
    "stream:cloud-queue": "cg-aws-sync",
    "stream:clip-trigger": "cg-rolling-buffer",
}
