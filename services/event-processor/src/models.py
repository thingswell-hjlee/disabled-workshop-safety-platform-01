"""Event Processor - Data Models & Type Definitions"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class EventState(str, Enum):
    ACTIVE = "ACTIVE"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    ARCHIVED = "ARCHIVED"


class AlarmAction(str, Enum):
    SIREN_ON = "SIREN_ON"
    LIGHT_ON = "LIGHT_ON"
    SIREN_OFF = "SIREN_OFF"
    LIGHT_OFF = "LIGHT_OFF"
    ALL_OFF = "ALL_OFF"


class RouteTarget(str, Enum):
    ALARM = "alarm"
    DASHBOARD = "dashboard"
    CLOUD = "cloud"
    NVR_CLIP = "nvr_clip"
    LOG = "log"


@dataclass
class RiskClassification:
    """Risk level classification rule"""
    event_type: str
    risk_level: str  # CRITICAL | WARNING | NORMAL
    alarm_actions: list = field(default_factory=list)
    routes: list = field(default_factory=list)


@dataclass
class ProcessedEvent:
    """Event after risk classification and enrichment"""
    event_id: str
    site_id: str
    device_id: str
    worker_id: Optional[str]
    event_type: str
    risk_level: str
    confidence: Optional[float]
    model_version: Optional[str]
    timestamp: str
    state: EventState = EventState.ACTIVE
    payload: dict = field(default_factory=dict)
    routed_to: list = field(default_factory=list)


@dataclass
class AlarmCommand:
    """Command sent to alarm-controller service"""
    event_id: str
    risk_level: str
    action: AlarmAction
    timestamp: str
    source_event_type: str


@dataclass
class AcknowledgeRequest:
    """Alarm acknowledge request from dashboard"""
    event_id: str
    acknowledged_by: str
    reason: str
    timestamp: str


@dataclass
class EventStats:
    """Event processing statistics"""
    total_events_processed: int = 0
    critical_count: int = 0
    warning_count: int = 0
    normal_count: int = 0
    events_per_minute: float = 0.0
    avg_processing_ms: float = 0.0
    duplicate_suppressed: int = 0
