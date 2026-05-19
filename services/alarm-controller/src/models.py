"""Alarm Controller - Data Models & Type Definitions"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class AlarmState(str, Enum):
    IDLE = "IDLE"
    SIREN_ACTIVE = "SIREN_ACTIVE"
    LIGHT_ACTIVE = "LIGHT_ACTIVE"
    BOTH_ACTIVE = "BOTH_ACTIVE"


class AlarmAction(str, Enum):
    SIREN_ON = "SIREN_ON"
    SIREN_OFF = "SIREN_OFF"
    LIGHT_ON = "LIGHT_ON"
    LIGHT_OFF = "LIGHT_OFF"
    ALL_ON = "ALL_ON"
    ALL_OFF = "ALL_OFF"


class GpioDirection(str, Enum):
    OUTPUT = "OUTPUT"
    INPUT = "INPUT"


@dataclass
class GpioPin:
    """GPIO pin configuration"""
    pin_number: int
    direction: GpioDirection
    label: str
    active_high: bool = True
    current_state: bool = False


@dataclass
class AlarmCommand:
    """Incoming alarm command from event-processor"""
    event_id: str
    risk_level: str
    action: AlarmAction
    timestamp: str
    source_event_type: str
    duration_seconds: Optional[int] = None  # None = until manual off


@dataclass
class AlarmStatus:
    """Current alarm system status"""
    state: AlarmState = AlarmState.IDLE
    siren_active: bool = False
    light_active: bool = False
    last_triggered_at: Optional[str] = None
    last_event_id: Optional[str] = None
    triggered_count_today: int = 0


@dataclass
class AlarmLog:
    """Alarm activation log entry"""
    event_id: str
    action: AlarmAction
    risk_level: str
    source_event_type: str
    triggered_at: str
    cleared_at: Optional[str] = None
    cleared_by: Optional[str] = None
    clear_reason: Optional[str] = None
