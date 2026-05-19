"""Platform 공통 상수 및 Enum 정의 - 전 서비스 공유"""
from enum import Enum


# --- Risk Level ---
class RiskLevel(str, Enum):
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    NORMAL = "NORMAL"


# --- Event Types ---
class EventType(str, Enum):
    # CRITICAL events
    FALL_DETECTED = "FALL_DETECTED"
    ZONE_INTRUSION = "ZONE_INTRUSION"
    FIRE_DETECTED = "FIRE_DETECTED"
    HEARTRATE_ABNORMAL = "HEARTRATE_ABNORMAL"
    BAND_FALL_DETECTED = "BAND_FALL_DETECTED"
    # WARNING events
    ABNORMAL_BEHAVIOR = "ABNORMAL_BEHAVIOR"
    ENV_THRESHOLD_EXCEEDED = "ENV_THRESHOLD_EXCEEDED"
    TEMPERATURE_ABNORMAL = "TEMPERATURE_ABNORMAL"
    BAND_DISCONNECTED = "BAND_DISCONNECTED"
    # NORMAL events
    NORMAL_RESTORED = "NORMAL_RESTORED"
    DEVICE_ONLINE = "DEVICE_ONLINE"
    # System events
    DEVICE_OFFLINE = "DEVICE_OFFLINE"
    SYSTEM_ALERT = "SYSTEM_ALERT"


# --- Device Types ---
class DeviceType(str, Enum):
    IP_CAMERA = "IP_CAMERA"
    SMART_BAND = "SMART_BAND"
    ENV_SENSOR = "ENV_SENSOR"
    FIRE_CONTACT = "FIRE_CONTACT"
    NVR = "NVR"
    ALARM = "ALARM"


# --- Device Status ---
class DeviceStatus(str, Enum):
    CONNECTED = "CONNECTED"
    DISCONNECTED = "DISCONNECTED"
    ERROR = "ERROR"
    RECONNECTING = "RECONNECTING"


# --- Risk Classification Mapping ---
RISK_CLASSIFICATION = {
    RiskLevel.CRITICAL: [
        EventType.FALL_DETECTED,
        EventType.ZONE_INTRUSION,
        EventType.FIRE_DETECTED,
        EventType.HEARTRATE_ABNORMAL,
        EventType.BAND_FALL_DETECTED,
    ],
    RiskLevel.WARNING: [
        EventType.ABNORMAL_BEHAVIOR,
        EventType.ENV_THRESHOLD_EXCEEDED,
        EventType.TEMPERATURE_ABNORMAL,
        EventType.BAND_DISCONNECTED,
    ],
    RiskLevel.NORMAL: [
        EventType.NORMAL_RESTORED,
        EventType.DEVICE_ONLINE,
    ],
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


# --- Redis Streams ---
REDIS_STREAMS = {
    "frames_prefix": "stream:frames",
    "bio": "stream:bio",
    "sensors": "stream:sensors",
    "events": "stream:events",
    "alarms": "stream:alarms",
    "dashboard": "stream:dashboard",
    "cloud_queue": "stream:cloud_queue",
}
