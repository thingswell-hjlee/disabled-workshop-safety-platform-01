"""SDK Common - Constants Tests (PR #16 동결 스키마 기준)"""
import pytest
from src.constants import (
    RiskLevel, EventType, DeviceType, DeviceStatus, EventState, AlarmAction,
    CloudPriority, RISK_CLASSIFICATION, RISK_TO_PRIORITY,
    DEFAULT_THRESHOLDS, SERVICE_PORTS, REDIS_STREAMS, CONSUMER_GROUPS,
)


class TestEventTypeEnum:
    """PR #16 동결: 15종 event_type"""

    def test_event_type_count(self):
        assert len(EventType) == 15

    def test_vision_ai_events_present(self):
        assert EventType.FALL_DETECTED.value == "FALL_DETECTED"
        assert EventType.COLLAPSE_DETECTED.value == "COLLAPSE_DETECTED"
        assert EventType.ZONE_INTRUSION.value == "ZONE_INTRUSION"
        assert EventType.STILLNESS_DETECTED.value == "STILLNESS_DETECTED"
        assert EventType.HAZARDOUS_ACTION.value == "HAZARDOUS_ACTION"
        assert EventType.FIRE_DETECTED.value == "FIRE_DETECTED"

    def test_band_events_present(self):
        assert EventType.HEARTRATE_ABNORMAL.value == "HEARTRATE_ABNORMAL"
        assert EventType.TEMPERATURE_ABNORMAL.value == "TEMPERATURE_ABNORMAL"
        assert EventType.BAND_FALL_DETECTED.value == "BAND_FALL_DETECTED"
        assert EventType.BAND_DISCONNECTED.value == "BAND_DISCONNECTED"

    def test_no_abnormal_behavior(self):
        """ABNORMAL_BEHAVIOR is NOT in PR #16 spec"""
        values = [e.value for e in EventType]
        assert "ABNORMAL_BEHAVIOR" not in values


class TestRiskClassification:
    """PR #16 C-001: FALL/COLLAPSE/FIRE → must be CRITICAL"""

    def test_critical_events_count(self):
        assert len(RISK_CLASSIFICATION[RiskLevel.CRITICAL]) == 3

    def test_warning_events_count(self):
        assert len(RISK_CLASSIFICATION[RiskLevel.WARNING]) == 8

    def test_normal_events_count(self):
        assert len(RISK_CLASSIFICATION[RiskLevel.NORMAL]) == 4

    def test_fall_is_critical(self):
        assert EventType.FALL_DETECTED in RISK_CLASSIFICATION[RiskLevel.CRITICAL]

    def test_collapse_is_critical(self):
        assert EventType.COLLAPSE_DETECTED in RISK_CLASSIFICATION[RiskLevel.CRITICAL]

    def test_fire_is_critical(self):
        assert EventType.FIRE_DETECTED in RISK_CLASSIFICATION[RiskLevel.CRITICAL]

    def test_env_threshold_is_warning(self):
        assert EventType.ENV_THRESHOLD_EXCEEDED in RISK_CLASSIFICATION[RiskLevel.WARNING]

    def test_stillness_is_warning(self):
        assert EventType.STILLNESS_DETECTED in RISK_CLASSIFICATION[RiskLevel.WARNING]

    def test_hazardous_is_warning(self):
        assert EventType.HAZARDOUS_ACTION in RISK_CLASSIFICATION[RiskLevel.WARNING]


class TestPriorityMapping:
    """PR #16 C-004: CRITICAL→HIGH, WARNING→NORMAL, NORMAL→LOW"""

    def test_critical_to_high(self):
        assert RISK_TO_PRIORITY[RiskLevel.CRITICAL] == CloudPriority.HIGH

    def test_warning_to_normal(self):
        assert RISK_TO_PRIORITY[RiskLevel.WARNING] == CloudPriority.NORMAL

    def test_normal_to_low(self):
        assert RISK_TO_PRIORITY[RiskLevel.NORMAL] == CloudPriority.LOW


class TestAlarmAction:
    """PR #16 동결: stream:alarms action enum"""

    def test_valid_actions(self):
        assert AlarmAction.SIREN_ON.value == "SIREN_ON"
        assert AlarmAction.LIGHT_ON.value == "LIGHT_ON"
        assert AlarmAction.ALL_ON.value == "ALL_ON"
        assert AlarmAction.ALL_OFF.value == "ALL_OFF"

    def test_action_count(self):
        assert len(AlarmAction) == 4


class TestDeviceType:
    """PR #16 동결: device_type enum"""

    def test_alarm_device(self):
        assert DeviceType.ALARM_DEVICE.value == "ALARM_DEVICE"

    def test_all_types(self):
        expected = {"IP_CAMERA", "SMART_BAND", "ENV_SENSOR", "FIRE_CONTACT", "ALARM_DEVICE", "NVR"}
        actual = {d.value for d in DeviceType}
        assert actual == expected


class TestDefaultThresholds:
    def test_temperature_max(self):
        assert DEFAULT_THRESHOLDS["temperature_max"] == 40.0

    def test_heartrate_range(self):
        assert DEFAULT_THRESHOLDS["heartrate_min"] == 40
        assert DEFAULT_THRESHOLDS["heartrate_max"] == 150

    def test_band_timeout(self):
        assert DEFAULT_THRESHOLDS["band_timeout_seconds"] == 30


class TestServicePorts:
    def test_all_services_defined(self):
        expected_services = [
            "device-gateway", "ai-inference", "event-processor",
            "alarm-controller", "cloud-sync", "training-pipeline",
            "dashboard-backend",
        ]
        for svc in expected_services:
            assert svc in SERVICE_PORTS

    def test_no_port_conflicts(self):
        ports = list(SERVICE_PORTS.values())
        assert len(ports) == len(set(ports))


class TestRedisStreams:
    """PR #16 동결: Redis Streams 이름"""

    def test_all_streams_defined(self):
        assert "ds_events" in REDIS_STREAMS
        assert "sensors" in REDIS_STREAMS
        assert "alarms" in REDIS_STREAMS
        assert "dashboard" in REDIS_STREAMS
        assert "cloud_queue" in REDIS_STREAMS
        assert "clip_trigger" in REDIS_STREAMS

    def test_stream_name_format(self):
        """All stream values use 'stream:' prefix with hyphen separator"""
        for key, value in REDIS_STREAMS.items():
            assert value.startswith("stream:"), f"{key}: '{value}' must start with 'stream:'"

    def test_exact_stream_names(self):
        assert REDIS_STREAMS["ds_events"] == "stream:ds-events"
        assert REDIS_STREAMS["sensors"] == "stream:sensors"
        assert REDIS_STREAMS["alarms"] == "stream:alarms"
        assert REDIS_STREAMS["dashboard"] == "stream:dashboard"
        assert REDIS_STREAMS["cloud_queue"] == "stream:cloud-queue"
        assert REDIS_STREAMS["clip_trigger"] == "stream:clip-trigger"
