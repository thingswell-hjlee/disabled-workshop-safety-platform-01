"""Alarm Controller - Model Tests"""
import pytest
from src.models import AlarmState, AlarmAction, AlarmCommand, AlarmStatus, AlarmLog


class TestAlarmStatus:
    def test_default_idle(self):
        status = AlarmStatus()
        assert status.state == AlarmState.IDLE
        assert status.siren_active is False
        assert status.light_active is False

    def test_both_active(self):
        status = AlarmStatus(
            state=AlarmState.BOTH_ACTIVE,
            siren_active=True,
            light_active=True,
            last_event_id="EVT-20250519120000-001",
        )
        assert status.state == AlarmState.BOTH_ACTIVE


class TestAlarmCommand:
    def test_critical_command(self):
        cmd = AlarmCommand(
            event_id="EVT-20250519120000-001",
            risk_level="CRITICAL",
            action=AlarmAction.ALL_ON,
            timestamp="2025-05-19T12:00:00.000Z",
            source_event_type="FALL_DETECTED",
        )
        assert cmd.action == AlarmAction.ALL_ON
        assert cmd.duration_seconds is None  # manual off

    def test_warning_command(self):
        cmd = AlarmCommand(
            event_id="EVT-20250519120000-002",
            risk_level="WARNING",
            action=AlarmAction.LIGHT_ON,
            timestamp="2025-05-19T12:00:00.000Z",
            source_event_type="ENV_THRESHOLD_EXCEEDED",
            duration_seconds=300,
        )
        assert cmd.duration_seconds == 300


class TestAlarmLog:
    def test_create_log(self):
        log = AlarmLog(
            event_id="EVT-20250519120000-001",
            action=AlarmAction.ALL_ON,
            risk_level="CRITICAL",
            source_event_type="FALL_DETECTED",
            triggered_at="2025-05-19T12:00:00.000Z",
        )
        assert log.cleared_at is None
        assert log.cleared_by is None
