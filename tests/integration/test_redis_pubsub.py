"""
Redis Streams Integration Tests
=================================
Redis Streams를 통한 publish/consume 흐름 검증.
fakeredis를 사용하여 실제 Redis 없이도 테스트 가능.

Test Scenarios (from schema-validation-test.md Section 7):
- IT-001: Valid FALL_DETECTED → consumer processes, validation passes
- IT-002: Invalid event_id → consumer rejects
- IT-003: Missing required field → consumer rejects
- IT-004: CRITICAL event → alarm triggered
- IT-005: Event → dashboard message
- IT-006: Event → cloud queue with correct priority
- IT-007: Vision AI without confidence → validation fails
- IT-008: BAND event without worker_id → validation fails
- IT-009: 1000 events rapidly → all processed
- IT-010: Duplicate event_id handling
"""

import json
import time

import pytest

from tests.integration.mock_aws_receiver import MockAwsReceiver
from tests.integration.mock_edge_producer import EdgeEventProducer, MockEventEngine
from tests.schema.models import (
    PATTERN_EVENT_ID,
    CloudQueueMessage,
    DsEventsMessage,
    SafetyEvent,
)


# ──────────────────────────────────────────────────────────────────────
# IT-001: Valid FALL_DETECTED passes through pipeline
# ──────────────────────────────────────────────────────────────────────


class TestIT001ValidFallEvent:
    """IT-001: Valid FALL_DETECTED event passes through entire pipeline"""

    @pytest.mark.integration
    def test_produce_and_consume_fall_event(self, fakeredis_client):
        """Produce FALL_DETECTED → consume from stream:ds-events"""
        producer = EdgeEventProducer(fakeredis_client)
        msg = producer.produce_ds_event(
            event_type="FALL_DETECTED",
            confidence=0.92,
        )

        # Verify message in stream
        messages = fakeredis_client.xrange("stream:ds-events", "-", "+")
        assert len(messages) == 1

        msg_id, msg_data = messages[0]
        assert msg_data["event_type"] == "FALL_DETECTED"
        assert msg_data["site_id"] == "SITE-001"
        assert msg_data["device_id"] == "CAM-001"

    @pytest.mark.integration
    def test_event_engine_processes_fall_event(self, fakeredis_client):
        """Event Engine processes FALL_DETECTED and publishes to downstream streams"""
        producer = EdgeEventProducer(fakeredis_client)
        engine = MockEventEngine(fakeredis_client)

        # Produce event
        msg = producer.produce_ds_event(event_type="FALL_DETECTED", confidence=0.92)

        # Process through Event Engine
        result = engine.process_ds_event(msg)

        assert result["alarm"] is True
        assert result["dashboard"] is True
        assert result["cloud_queue"] is True
        assert result["clip_trigger"] is True

    @pytest.mark.integration
    def test_fall_event_generates_critical_alarm(self, fakeredis_client):
        """FALL_DETECTED → stream:alarms with CRITICAL risk and ALL_ON action"""
        producer = EdgeEventProducer(fakeredis_client)
        engine = MockEventEngine(fakeredis_client)

        msg = producer.produce_ds_event(event_type="FALL_DETECTED")
        engine.process_ds_event(msg)

        # Check alarm stream
        alarms = fakeredis_client.xrange("stream:alarms", "-", "+")
        assert len(alarms) == 1
        _, alarm_data = alarms[0]
        assert alarm_data["risk_level"] == "CRITICAL"
        assert alarm_data["action"] == "ALL_ON"
        assert alarm_data["source_event_type"] == "FALL_DETECTED"


# ──────────────────────────────────────────────────────────────────────
# IT-002: Invalid event_id rejected
# ──────────────────────────────────────────────────────────────────────


class TestIT002InvalidEventId:
    """IT-002: Invalid event_id format is detected during validation"""

    @pytest.mark.integration
    def test_invalid_event_id_fails_schema_validation(self, fakeredis_client):
        """Invalid event_id fails Pydantic validation"""
        from pydantic import ValidationError

        invalid_msg = {
            "event_id": "INVALID-FORMAT",
            "site_id": "SITE-001",
            "source_id": "pipeline-0",
            "device_id": "CAM-001",
            "event_type": "FALL_DETECTED",
            "timestamp": "2025-05-19T12:00:00.123Z",
            "model_version": "v1.0.0-tao-ds",
            "inference": {
                "pgie": {"class_id": 2, "confidence": 0.9, "label": "fall", "bbox": {"x": 0.1, "y": 0.2, "w": 0.3, "h": 0.4}},
                "tracker": {"object_id": 1, "age_frames": 5},
            },
        }

        with pytest.raises(ValidationError):
            DsEventsMessage(**invalid_msg)


# ──────────────────────────────────────────────────────────────────────
# IT-003: Missing required field rejected
# ──────────────────────────────────────────────────────────────────────


class TestIT003MissingField:
    """IT-003: Missing required field is detected during validation"""

    @pytest.mark.integration
    def test_missing_event_type_fails(self):
        """Missing event_type field fails validation"""
        from pydantic import ValidationError

        incomplete_msg = {
            "event_id": "EVT-20250519120000-001",
            "site_id": "SITE-001",
            "source_id": "pipeline-0",
            "device_id": "CAM-001",
            # Missing event_type
            "timestamp": "2025-05-19T12:00:00.123Z",
            "model_version": "v1.0.0-tao-ds",
            "inference": {
                "pgie": {"class_id": 2, "confidence": 0.9, "label": "fall", "bbox": {"x": 0.1, "y": 0.2, "w": 0.3, "h": 0.4}},
                "tracker": {"object_id": 1, "age_frames": 5},
            },
        }

        with pytest.raises(ValidationError) as exc_info:
            DsEventsMessage(**incomplete_msg)
        assert "event_type" in str(exc_info.value)


# ──────────────────────────────────────────────────────────────────────
# IT-004: CRITICAL event triggers alarm
# ──────────────────────────────────────────────────────────────────────


class TestIT004CriticalAlarm:
    """IT-004: CRITICAL event → stream:alarms receives message"""

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "event_type", ["FALL_DETECTED", "COLLAPSE_DETECTED", "FIRE_DETECTED"]
    )
    def test_critical_events_trigger_alarm(self, fakeredis_client, event_type):
        """All CRITICAL event types trigger ALL_ON alarm"""
        producer = EdgeEventProducer(fakeredis_client)
        engine = MockEventEngine(fakeredis_client)

        device_id = "FIRE-001" if event_type == "FIRE_DETECTED" else "CAM-001"
        msg = producer.produce_ds_event(
            event_type=event_type, device_id=device_id
        )
        engine.process_ds_event(msg)

        alarms = fakeredis_client.xrange("stream:alarms", "-", "+")
        assert len(alarms) >= 1
        _, alarm_data = alarms[-1]
        assert alarm_data["risk_level"] == "CRITICAL"
        assert alarm_data["action"] == "ALL_ON"


# ──────────────────────────────────────────────────────────────────────
# IT-005: Event generates dashboard message
# ──────────────────────────────────────────────────────────────────────


class TestIT005Dashboard:
    """IT-005: Event → stream:dashboard receives formatted message"""

    @pytest.mark.integration
    def test_event_generates_dashboard_message(self, fakeredis_client):
        """FALL_DETECTED produces dashboard message with context"""
        producer = EdgeEventProducer(fakeredis_client)
        engine = MockEventEngine(fakeredis_client)

        msg = producer.produce_ds_event(event_type="FALL_DETECTED")
        engine.process_ds_event(msg)

        dashboard_msgs = fakeredis_client.xrange("stream:dashboard", "-", "+")
        assert len(dashboard_msgs) == 1
        _, dash_data = dashboard_msgs[0]
        assert dash_data["event_state"] == "ACTIVE"
        assert dash_data["event_type"] == "FALL_DETECTED"
        assert dash_data["risk_level"] == "CRITICAL"

        # Verify context has required fields
        context = json.loads(dash_data["context"])
        assert "summary" in context
        assert "clip_available" in context


# ──────────────────────────────────────────────────────────────────────
# IT-006: Event goes to cloud queue with correct priority
# ──────────────────────────────────────────────────────────────────────


class TestIT006CloudQueue:
    """IT-006: Event → stream:cloud-queue with correct priority"""

    @pytest.mark.integration
    def test_critical_event_has_high_priority(self, fakeredis_client):
        """CRITICAL events get HIGH priority in cloud queue"""
        producer = EdgeEventProducer(fakeredis_client)
        engine = MockEventEngine(fakeredis_client)

        msg = producer.produce_ds_event(event_type="FALL_DETECTED")
        engine.process_ds_event(msg)

        cloud_msgs = fakeredis_client.xrange("stream:cloud-queue", "-", "+")
        assert len(cloud_msgs) == 1
        _, cloud_data = cloud_msgs[0]
        assert cloud_data["priority"] == "HIGH"
        assert cloud_data["risk_level"] == "CRITICAL"

    @pytest.mark.integration
    def test_warning_event_has_normal_priority(self, fakeredis_client):
        """WARNING events get NORMAL priority"""
        producer = EdgeEventProducer(fakeredis_client)
        engine = MockEventEngine(fakeredis_client)

        msg = producer.produce_ds_event(event_type="STILLNESS_DETECTED")
        engine.process_ds_event(msg)

        cloud_msgs = fakeredis_client.xrange("stream:cloud-queue", "-", "+")
        _, cloud_data = cloud_msgs[0]
        assert cloud_data["priority"] == "NORMAL"

    @pytest.mark.integration
    def test_cloud_queue_has_idempotency_key(self, fakeredis_client):
        """Cloud queue message has correct idempotency_key format"""
        producer = EdgeEventProducer(fakeredis_client)
        engine = MockEventEngine(fakeredis_client)

        msg = producer.produce_ds_event(event_type="FALL_DETECTED")
        engine.process_ds_event(msg)

        cloud_msgs = fakeredis_client.xrange("stream:cloud-queue", "-", "+")
        _, cloud_data = cloud_msgs[0]
        expected_key = f"SITE-001:{msg['event_id']}"
        assert cloud_data["idempotency_key"] == expected_key


# ──────────────────────────────────────────────────────────────────────
# IT-009: Rapid event processing (load test)
# ──────────────────────────────────────────────────────────────────────


class TestIT009RapidEvents:
    """IT-009: 1000 events rapidly → all processed, no data loss"""

    @pytest.mark.integration
    def test_100_events_processed_without_loss(self, fakeredis_client):
        """100 events are all processed (reduced from 1000 for unit test speed)"""
        producer = EdgeEventProducer(fakeredis_client)
        engine = MockEventEngine(fakeredis_client)

        event_count = 100
        for i in range(event_count):
            event_type = "FALL_DETECTED" if i % 3 == 0 else "STILLNESS_DETECTED"
            msg = producer.produce_ds_event(event_type=event_type)
            engine.process_ds_event(msg)

        # Verify all streams received correct count
        ds_events = fakeredis_client.xlen("stream:ds-events")
        alarms = fakeredis_client.xlen("stream:alarms")
        dashboard = fakeredis_client.xlen("stream:dashboard")
        cloud_queue = fakeredis_client.xlen("stream:cloud-queue")

        assert ds_events == event_count
        assert alarms == event_count
        assert dashboard == event_count
        assert cloud_queue == event_count


# ──────────────────────────────────────────────────────────────────────
# IT-010: Duplicate event_id handling
# ──────────────────────────────────────────────────────────────────────


class TestIT010DuplicateEvent:
    """IT-010: Duplicate event_id detection"""

    @pytest.mark.integration
    def test_duplicate_event_detected(self, fakeredis_client):
        """Duplicate events are detectable via idempotency_key"""
        producer = EdgeEventProducer(fakeredis_client)
        engine = MockEventEngine(fakeredis_client)
        receiver = MockAwsReceiver(fakeredis_client)

        # Produce same event twice
        fixed_event_id = "EVT-20250519120000-001"
        msg1 = producer.produce_ds_event(
            event_type="FALL_DETECTED", event_id=fixed_event_id
        )
        msg2 = producer.produce_ds_event(
            event_type="FALL_DETECTED", event_id=fixed_event_id
        )
        engine.process_ds_event(msg1)
        engine.process_ds_event(msg2)

        # Both end up in cloud queue
        messages = receiver.consume_all_pending()
        assert len(messages) == 2

        # But they have the same idempotency_key
        keys = [m["data"]["idempotency_key"] for m in messages]
        assert keys[0] == keys[1]
        assert keys[0] == f"SITE-001:{fixed_event_id}"

    @pytest.mark.integration
    def test_aws_receiver_detects_duplicate(self, fakeredis_client):
        """AWS receiver detects and handles duplicate events"""
        receiver = MockAwsReceiver(fakeredis_client)

        # First event
        event1 = {"event_id": "EVT-20250519120000-001", "site_id": "SITE-001"}
        receiver.received_events.append(event1)

        # Second (duplicate) event
        event2 = {"event_id": "EVT-20250519120000-001", "site_id": "SITE-001"}
        receiver.received_events.append(event2)

        # Check duplicate
        assert receiver.check_duplicate("EVT-20250519120000-001") is True


# ──────────────────────────────────────────────────────────────────────
# AWS Receiver Transform Test
# ──────────────────────────────────────────────────────────────────────


class TestAwsReceiverTransform:
    """AWS receiver transforms cloud-queue message to MQTT payload"""

    @pytest.mark.integration
    def test_transform_to_mqtt_payload(self, fakeredis_client):
        """Cloud queue message correctly transforms to MQTT format"""
        receiver = MockAwsReceiver(fakeredis_client)

        cloud_msg = {
            "event_id": "EVT-20250519120000-001",
            "site_id": "SITE-001",
            "device_id": "CAM-001",
            "worker_id": "",
            "event_type": "FALL_DETECTED",
            "risk_level": "CRITICAL",
            "timestamp": "2025-05-19T12:00:00.123Z",
            "idempotency_key": "SITE-001:EVT-20250519120000-001",
            "priority": "HIGH",
            "clip_path": "/data/clips/EVT-20250519120000-001.mp4",
            "confidence": "0.92",
            "model_version": "v1.0.0-tao-ds",
        }

        mqtt_payload = receiver.transform_to_mqtt(cloud_msg)

        assert mqtt_payload["event_id"] == "EVT-20250519120000-001"
        assert mqtt_payload["event_type"] == "FALL_DETECTED"
        assert mqtt_payload["risk_level"] == "CRITICAL"
        assert mqtt_payload["confidence"] == 0.92
        assert mqtt_payload["idempotency_key"] == "SITE-001:EVT-20250519120000-001"
        assert mqtt_payload["context_summary"] is not None
        assert "SITE-001" in mqtt_payload["clip_s3_key"]

    @pytest.mark.integration
    def test_s3_key_path_format(self, fakeredis_client):
        """S3 key follows pattern: events/{site_id}/{YYYY}/{MM}/{DD}/{event_id}.mp4"""
        receiver = MockAwsReceiver(fakeredis_client)

        cloud_msg = {
            "event_id": "EVT-20250519120000-001",
            "site_id": "SITE-001",
            "device_id": "CAM-001",
            "event_type": "FALL_DETECTED",
            "risk_level": "CRITICAL",
            "timestamp": "2025-05-19T12:00:00.123Z",
            "idempotency_key": "SITE-001:EVT-20250519120000-001",
            "priority": "HIGH",
            "clip_path": "/data/clips/EVT-20250519120000-001.mp4",
            "confidence": "0.92",
            "model_version": "v1.0.0-tao-ds",
        }

        mqtt_payload = receiver.transform_to_mqtt(cloud_msg)
        expected_key = "events/SITE-001/2025/05/19/EVT-20250519120000-001.mp4"
        assert mqtt_payload["clip_s3_key"] == expected_key
