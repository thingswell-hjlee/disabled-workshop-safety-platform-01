"""Device Gateway - Data Models & Type Definitions"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class DeviceType(str, Enum):
    IP_CAMERA = "IP_CAMERA"
    SMART_BAND = "SMART_BAND"
    ENV_SENSOR = "ENV_SENSOR"
    FIRE_CONTACT = "FIRE_CONTACT"
    NVR = "NVR"
    ALARM = "ALARM"


class DeviceStatus(str, Enum):
    CONNECTED = "CONNECTED"
    DISCONNECTED = "DISCONNECTED"
    ERROR = "ERROR"
    RECONNECTING = "RECONNECTING"


class StreamDataType(str, Enum):
    FRAME = "frame"
    HEARTRATE = "heartrate"
    TEMPERATURE = "temperature"
    ACCELERATION = "acceleration"
    LOCATION = "location"
    ENVIRONMENT = "environment"
    FIRE_CONTACT = "fire_contact"


@dataclass
class DeviceInfo:
    device_id: str
    site_id: str
    device_type: DeviceType
    status: DeviceStatus
    last_heartbeat: Optional[datetime] = None
    metadata: dict = field(default_factory=dict)


@dataclass
class FrameMessage:
    """Redis Stream message for video frames"""
    device_id: str
    site_id: str
    timestamp: str
    frame_seq: int
    resolution: str
    encoding: str = "raw_bgr"
    frame_ref: str = ""  # Redis key for frame binary


@dataclass
class BioMessage:
    """Redis Stream message for smart band biometric data"""
    device_id: str
    worker_id: str
    site_id: str
    timestamp: str
    data_type: StreamDataType
    value: dict = field(default_factory=dict)
    battery_level: Optional[int] = None


@dataclass
class SensorMessage:
    """Redis Stream message for environment sensors"""
    device_id: str
    site_id: str
    zone: str
    timestamp: str
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    co_ppm: Optional[float] = None
    voc_ppb: Optional[float] = None


@dataclass
class FireContactMessage:
    """Redis Stream message for fire detection contact"""
    device_id: str
    site_id: str
    timestamp: str
    sensor_type: str = "fire_contact"
    status: str = "NORMAL"  # NORMAL | DETECTED | FAULT
    raw_signal: int = 0


@dataclass
class DeviceHealthResponse:
    """API response for device health"""
    device_id: str
    device_type: DeviceType
    status: DeviceStatus
    last_heartbeat: Optional[str] = None
    uptime_seconds: Optional[int] = None
    error_message: Optional[str] = None
