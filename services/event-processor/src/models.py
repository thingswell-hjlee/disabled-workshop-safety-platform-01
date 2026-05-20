"""Event Processor - Data Models & Type Definitions

PR #16 동결 스키마 기준으로 정의.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class EventState(str, Enum):
    """PR #16 동결: event_state enum"""
    ACTIVE = "ACTIVE"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    ARCHIVED = "ARCHIVED"


class AlarmAction(str, Enum):
    """PR #16 동결: stream:alarms action enum"""
    SIREN_ON = "SIREN_ON"
    LIGHT_ON = "LIGHT_ON"
    ALL_ON = "ALL_ON"
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
    model_version: Optional[str]  # Format: v{M}.{m}.{p}-{tool}-{target}
    timestamp: str
    event_state: EventState = EventState.ACTIVE
    context: dict = field(default_factory=dict)
    routed_to: list = field(default_factory=list)


@dataclass
class AlarmCommand:
    """Command sent to alarm-controller service via stream:alarms"""
    event_id: str
    site_id: str
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
