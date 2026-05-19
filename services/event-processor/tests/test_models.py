"""Event Processor - Model Tests"""
import pytest
from src.models import (
    EventState, AlarmAction, ProcessedEvent,
    AlarmCommand, AcknowledgeRequest, EventStats,
)


class TestProcessedEvent:
    def test_create_active_event(self):
        event = ProcessedEvent(
            event_id="EVT-20250519120000-001",
            site_id="SITE-001",
            device_id="CAM-003",
            worker_id="WKR-0002",
            event_type="FALL_DETECTED",
            risk_level="CRITICAL",
            confidence=0.92,
            model_version="v1.0.0-edge",
            timestamp="2025-05-19T12:00:00.123Z",
            routed_to=["alarm", "dashboard", "cloud"],
        )
        assert event.state == EventState.ACTIVE
        assert "alarm" in event.routed_to

    def test_event_state_transition(self):
        event = ProcessedEvent(
            event_id="EVT-20250519120000-001",
            site_id="SITE-001",
            device_id="CAM-003",
            worker_id=None,
            event_type="FIRE_DETECTED",
            risk_level="CRITICAL",
            confidence=None,
            model_version=None,
            timestamp="2025-05-19T12:00:00.000Z",
        )
        event.state = EventState.ACKNOWLEDGED
        assert event.state == EventState.ACKNOWLEDGED


class TestAlarmCommand:
    def test_create_siren_command(self):
        cmd = AlarmCommand(
            event_id="EVT-20250519120000-001",
            risk_level="CRITICAL",
            action=AlarmAction.SIREN_ON,
            timestamp="2025-05-19T12:00:00.000Z",
            source_event_type="FALL_DETECTED",
        )
        assert cmd.action == AlarmAction.SIREN_ON

    def test_create_light_only_command(self):
        cmd = AlarmCommand(
            event_id="EVT-20250519120000-002",
            risk_level="WARNING",
            action=AlarmAction.LIGHT_ON,
            timestamp="2025-05-19T12:00:00.000Z",
            source_event_type="ENV_THRESHOLD_EXCEEDED",
        )
        assert cmd.action == AlarmAction.LIGHT_ON


class TestAcknowledgeRequest:
    def test_create_acknowledge(self):
        req = AcknowledgeRequest(
            event_id="EVT-20250519120000-001",
            acknowledged_by="admin",
            reason="오탐 확인 - 작업자 정상 활동",
            timestamp="2025-05-19T12:05:00.000Z",
        )
        assert req.acknowledged_by == "admin"
        assert "오탐" in req.reason
