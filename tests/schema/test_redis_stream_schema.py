"""
Redis Streams Schema Validation Tests
=======================================
6개 Redis Stream의 메시지 스키마 검증.
Reference: docs/redis-streams-schema.md
"""

import pytest
from pydantic import ValidationError

from tests.schema.models import (
    AlarmsMessage,
    ClipTriggerMessage,
    CloudQueueMessage,
    DashboardMessage,
    DsEventsMessage,
    SensorsMessage,
)


# ──────────────────────────────────────────────────────────────────────
# stream:ds-events Tests
# ──────────────────────────────────────────────────────────────────────


class TestDsEventsStream:
    """stream:ds-events message validation"""

    @pytest.mark.redis
    @pytest.mark.schema
    def test_valid_ds_event_message(self, redis_stream_messages):
        """Valid DeepStream event message passes validation"""
        msg = redis_stream_messages["stream:ds-events"][0]
        result = DsEventsMessage(**msg)
        assert result.event_id == "EVT-20250519120000-001"
        assert result.source_id == "pipeline-0"
        assert result.model_version == "v1.0.0-tao-ds"

    @pytest.mark.redis
    @pytest.mark.schema
    def test_ds_event_requires_source_id(self, redis_stream_messages):
        """stream:ds-events requires source_id field"""
        msg = dict(redis_stream_messages["stream:ds-events"][0])
        del msg["source_id"]
        with pytest.raises(ValidationError) as exc_info:
            DsEventsMessage(**msg)
        assert "source_id" in str(exc_info.value)

    @pytest.mark.redis
    @pytest.mark.schema
    def test_ds_event_requires_inference_pgie(self):
        """stream:ds-events inference must contain pgie"""
        with pytest.raises(ValidationError):
            DsEventsMessage(
                event_id="EVT-20250519120000-001",
                site_id="SITE-001",
                source_id="pipeline-0",
                device_id="CAM-001",
                event_type="FALL_DETECTED",
                timestamp="2025-05-19T12:00:00.123Z",
                model_version="v1.0.0-tao-ds",
                inference={"sgie": None},  # Missing pgie and tracker
            )

    @pytest.mark.redis
    @pytest.mark.schema
    def test_ds_event_device_must_be_camera(self):
        """stream:ds-events device_id must be CAM-xxx"""
        with pytest.raises(ValidationError):
            DsEventsMessage(
                event_id="EVT-20250519120000-001",
                site_id="SITE-001",
                source_id="pipeline-0",
                device_id="BAND-001",  # Should be CAM
                event_type="FALL_DETECTED",
                timestamp="2025-05-19T12:00:00.123Z",
                model_version="v1.0.0-tao-ds",
                inference={
                    "pgie": {"class_id": 2, "confidence": 0.9, "label": "fall", "bbox": {"x": 0.1, "y": 0.2, "w": 0.3, "h": 0.4}},
                    "tracker": {"object_id": 1, "age_frames": 5},
                },
            )


# ──────────────────────────────────────────────────────────────────────
# stream:sensors Tests
# ──────────────────────────────────────────────────────────────────────


class TestSensorsStream:
    """stream:sensors message validation"""

    @pytest.mark.redis
    @pytest.mark.schema
    def test_valid_sensor_message(self, redis_stream_messages):
        """Valid sensor message passes validation"""
        msgs = redis_stream_messages["stream:sensors"]
        # Heartrate
        result = SensorsMessage(**msgs[0])
        assert result.data_type == "HEARTRATE"
        assert result.source == "SMART_BAND"
        assert result.worker_id == "WKR-0012"
        # ENV
        result = SensorsMessage(**msgs[1])
        assert result.data_type == "GAS"
        assert result.source == "ENV_SENSOR"

    @pytest.mark.redis
    @pytest.mark.schema
    def test_sensor_invalid_data_type(self):
        """Invalid data_type rejected"""
        with pytest.raises(ValidationError):
            SensorsMessage(
                event_id="EVT-20250519120000-001",
                site_id="SITE-001",
                device_id="BAND-001",
                worker_id="WKR-0001",
                event_type="HEARTRATE_ABNORMAL",
                timestamp="2025-05-19T12:00:00.123Z",
                data_type="BLOOD_PRESSURE",  # Invalid
                value=120.0,
                source="SMART_BAND",
            )

    @pytest.mark.redis
    @pytest.mark.schema
    def test_sensor_invalid_source(self):
        """Invalid source rejected"""
        with pytest.raises(ValidationError):
            SensorsMessage(
                event_id="EVT-20250519120000-001",
                site_id="SITE-001",
                device_id="BAND-001",
                worker_id="WKR-0001",
                event_type="HEARTRATE_ABNORMAL",
                timestamp="2025-05-19T12:00:00.123Z",
                data_type="HEARTRATE",
                value=120.0,
                source="WEARABLE",  # Invalid
            )


# ──────────────────────────────────────────────────────────────────────
# stream:alarms Tests
# ──────────────────────────────────────────────────────────────────────


class TestAlarmsStream:
    """stream:alarms message validation"""

    @pytest.mark.redis
    @pytest.mark.schema
    def test_valid_alarm_message(self, redis_stream_messages):
        """Valid alarm message passes validation"""
        msg = redis_stream_messages["stream:alarms"][0]
        result = AlarmsMessage(**msg)
        assert result.action == "ALL_ON"
        assert result.risk_level == "CRITICAL"
        assert result.source_event_type == "FALL_DETECTED"

    @pytest.mark.redis
    @pytest.mark.schema
    @pytest.mark.parametrize(
        "action", ["SIREN_ON", "LIGHT_ON", "ALL_ON", "ALL_OFF"]
    )
    def test_valid_alarm_actions(self, action):
        """All valid alarm actions accepted"""
        result = AlarmsMessage(
            event_id="EVT-20250519120000-001",
            site_id="SITE-001",
            risk_level="CRITICAL",
            action=action,
            timestamp="2025-05-19T12:00:00.123Z",
            source_event_type="FALL_DETECTED",
        )
        assert result.action == action

    @pytest.mark.redis
    @pytest.mark.schema
    def test_invalid_alarm_action(self):
        """Invalid alarm action rejected"""
        with pytest.raises(ValidationError):
            AlarmsMessage(
                event_id="EVT-20250519120000-001",
                site_id="SITE-001",
                risk_level="CRITICAL",
                action="BUZZER_ON",  # Invalid
                timestamp="2025-05-19T12:00:00.123Z",
                source_event_type="FALL_DETECTED",
            )


# ──────────────────────────────────────────────────────────────────────
# stream:dashboard Tests
# ──────────────────────────────────────────────────────────────────────


class TestDashboardStream:
    """stream:dashboard message validation"""

    @pytest.mark.redis
    @pytest.mark.schema
    def test_valid_dashboard_message(self, redis_stream_messages):
        """Valid dashboard message passes validation"""
        msg = redis_stream_messages["stream:dashboard"][0]
        result = DashboardMessage(**msg)
        assert result.event_state == "ACTIVE"
        assert result.context["summary"] == "작업장 A구역 낙상 감지 (신뢰도 92%)"
        assert result.context["clip_available"] is True

    @pytest.mark.redis
    @pytest.mark.schema
    def test_dashboard_requires_context_summary(self):
        """Dashboard message context must contain summary"""
        with pytest.raises(ValidationError):
            DashboardMessage(
                event_id="EVT-20250519120000-001",
                site_id="SITE-001",
                device_id="CAM-001",
                event_type="FALL_DETECTED",
                risk_level="CRITICAL",
                timestamp="2025-05-19T12:00:00.123Z",
                event_state="ACTIVE",
                context={"location": "A구역"},  # Missing summary and clip_available
            )


# ──────────────────────────────────────────────────────────────────────
# stream:cloud-queue Tests
# ──────────────────────────────────────────────────────────────────────


class TestCloudQueueStream:
    """stream:cloud-queue message validation"""

    @pytest.mark.redis
    @pytest.mark.schema
    def test_valid_cloud_queue_message(self, redis_stream_messages):
        """Valid cloud queue message passes validation"""
        msg = redis_stream_messages["stream:cloud-queue"][0]
        result = CloudQueueMessage(**msg)
        assert result.idempotency_key == "SITE-001:EVT-20250519120000-001"
        assert result.priority == "HIGH"

    @pytest.mark.redis
    @pytest.mark.schema
    @pytest.mark.parametrize("priority", ["HIGH", "NORMAL", "LOW"])
    def test_valid_priorities(self, priority):
        """All valid priorities accepted"""
        result = CloudQueueMessage(
            event_id="EVT-20250519120000-001",
            site_id="SITE-001",
            device_id="CAM-001",
            event_type="FALL_DETECTED",
            risk_level="CRITICAL",
            timestamp="2025-05-19T12:00:00.123Z",
            idempotency_key="SITE-001:EVT-20250519120000-001",
            priority=priority,
        )
        assert result.priority == priority

    @pytest.mark.redis
    @pytest.mark.schema
    def test_invalid_priority(self):
        """Invalid priority rejected"""
        with pytest.raises(ValidationError):
            CloudQueueMessage(
                event_id="EVT-20250519120000-001",
                site_id="SITE-001",
                device_id="CAM-001",
                event_type="FALL_DETECTED",
                risk_level="CRITICAL",
                timestamp="2025-05-19T12:00:00.123Z",
                idempotency_key="SITE-001:EVT-20250519120000-001",
                priority="URGENT",  # Invalid
            )


# ──────────────────────────────────────────────────────────────────────
# stream:clip-trigger Tests
# ──────────────────────────────────────────────────────────────────────


class TestClipTriggerStream:
    """stream:clip-trigger message validation"""

    @pytest.mark.redis
    @pytest.mark.schema
    def test_valid_clip_trigger_message(self, redis_stream_messages):
        """Valid clip trigger message passes validation"""
        msg = redis_stream_messages["stream:clip-trigger"][0]
        result = ClipTriggerMessage(**msg)
        assert result.pre_sec == 30
        assert result.post_sec == 30

    @pytest.mark.redis
    @pytest.mark.schema
    def test_clip_trigger_pre_sec_must_be_positive(self):
        """pre_sec must be positive"""
        with pytest.raises(ValidationError):
            ClipTriggerMessage(
                event_id="EVT-20250519120000-001",
                site_id="SITE-001",
                device_id="CAM-001",
                trigger_ts="2025-05-19T12:00:00.123Z",
                pre_sec=0,  # Must be > 0
                post_sec=30,
            )

    @pytest.mark.redis
    @pytest.mark.schema
    def test_clip_trigger_device_must_be_camera(self):
        """clip-trigger device_id must be CAM-xxx"""
        with pytest.raises(ValidationError):
            ClipTriggerMessage(
                event_id="EVT-20250519120000-001",
                site_id="SITE-001",
                device_id="BAND-001",  # Should be CAM
                trigger_ts="2025-05-19T12:00:00.123Z",
                pre_sec=30,
                post_sec=30,
            )


# ──────────────────────────────────────────────────────────────────────
# Stream Name Validation
# ──────────────────────────────────────────────────────────────────────


class TestStreamNames:
    """Redis stream name format validation"""

    VALID_STREAM_NAMES = [
        "stream:ds-events",
        "stream:sensors",
        "stream:alarms",
        "stream:dashboard",
        "stream:cloud-queue",
        "stream:clip-trigger",
    ]

    @pytest.mark.redis
    @pytest.mark.schema
    def test_all_stream_names_follow_convention(self):
        """All stream names use 'stream:' prefix"""
        for name in self.VALID_STREAM_NAMES:
            assert name.startswith("stream:"), f"Stream '{name}' must start with 'stream:'"

    @pytest.mark.redis
    @pytest.mark.schema
    def test_fixture_contains_all_streams(self, redis_stream_messages):
        """Fixture file has messages for all 6 streams"""
        for stream in self.VALID_STREAM_NAMES:
            assert stream in redis_stream_messages, f"Missing fixture for '{stream}'"
            assert len(redis_stream_messages[stream]) > 0, f"Empty fixture for '{stream}'"
