"""SDK Common - Constants Tests"""
import pytest
from src.constants import (
    RiskLevel, EventType, DeviceType, DeviceStatus,
    RISK_CLASSIFICATION, DEFAULT_THRESHOLDS, SERVICE_PORTS, REDIS_STREAMS,
)


class TestRiskClassification:
    def test_critical_events_count(self):
        assert len(RISK_CLASSIFICATION[RiskLevel.CRITICAL]) == 5

    def test_warning_events_count(self):
        assert len(RISK_CLASSIFICATION[RiskLevel.WARNING]) == 4

    def test_normal_events_count(self):
        assert len(RISK_CLASSIFICATION[RiskLevel.NORMAL]) == 2

    def test_fall_is_critical(self):
        assert EventType.FALL_DETECTED in RISK_CLASSIFICATION[RiskLevel.CRITICAL]

    def test_env_threshold_is_warning(self):
        assert EventType.ENV_THRESHOLD_EXCEEDED in RISK_CLASSIFICATION[RiskLevel.WARNING]


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
        assert len(ports) == len(set(ports))  # no duplicates


class TestRedisStreams:
    def test_all_streams_defined(self):
        assert "events" in REDIS_STREAMS
        assert "alarms" in REDIS_STREAMS
        assert "cloud_queue" in REDIS_STREAMS
        assert "dashboard" in REDIS_STREAMS
