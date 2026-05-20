"""
End-to-End Flow Simulator Tests
=================================
전체 Platform 1.0 이벤트 파이프라인을 시뮬레이션한다.

흐름:
  Edge Producer → stream:ds-events/sensors → Event Engine →
  stream:alarms + stream:dashboard + stream:cloud-queue + stream:clip-trigger →
  AWS Receiver → MQTT Transform → DB Storage

이 테스트는 fakeredis를 사용하여 외부 의존성 없이 실행 가능하다.
"""

import json
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from tests.integration.mock_aws_receiver import MockAwsReceiver
from tests.integration.mock_edge_producer import EdgeEventProducer, MockEventEngine
from tests.schema.models import (
    AlarmsMessage,
    CloudQueueMessage,
    DsEventsMessage,
    MqttEventPayload,
    SafetyEvent,
    CRITICAL_EVENT_TYPES,
    RISK_TO_PRIORITY,
)


# ──────────────────────────────────────────────────────────────────────
# E2E Scenario 1: FALL_DETECTED Full Pipeline
# ──────────────────────────────────────────────────────────────────────


class TestE2EFallDetected:
    """E2E: FALL_DETECTED 이벤트의 전체 파이프라인 검증"""

    @pytest.mark.e2e
    def test_full_pipeline_fall_detected(self, fakeredis_client):
        """
        FALL_DETECTED: Edge → Redis → EventEngine → Alarms + Dashboard +
        CloudQueue + ClipTrigger → AWS Receiver → MQTT → (DB)
        """
        # === Step 1: Edge produces DeepStream event ===
        producer = EdgeEventProducer(fakeredis_client)
        ds_msg = producer.produce_ds_event(
            event_type="FALL_DETECTED",
            device_id="CAM-001",
            confidence=0.92,
            class_label="fall",
            class_id=2,
            model_version="v1.0.0-tao-ds",
        )

        # === Step 2: Validate produced message schema ===
        ds_msg_for_validation = dict(ds_msg)
        ds_msg_for_validation["inference"] = json.loads(ds_msg["inference"])
        validated = DsEventsMessage(**ds_msg_for_validation)
        assert validated.event_type == "FALL_DETECTED"

        # === Step 3: Verify in Redis stream ===
        stream_len = fakeredis_client.xlen("stream:ds-events")
        assert stream_len == 1

        # === Step 4: Event Engine processes ===
        engine = MockEventEngine(fakeredis_client)
        result = engine.process_ds_event(ds_msg)
        assert result["alarm"] is True
        assert result["dashboard"] is True
        assert result["cloud_queue"] is True
        assert result["clip_trigger"] is True

        # === Step 5: Verify alarm stream ===
        alarms = fakeredis_client.xrange("stream:alarms", "-", "+")
        assert len(alarms) == 1
        _, alarm_data = alarms[0]
        assert alarm_data["risk_level"] == "CRITICAL"
        assert alarm_data["action"] == "ALL_ON"
        assert alarm_data["source_event_type"] == "FALL_DETECTED"

        # === Step 6: Verify dashboard stream ===
        dashboard_msgs = fakeredis_client.xrange("stream:dashboard", "-", "+")
        assert len(dashboard_msgs) == 1
        _, dash_data = dashboard_msgs[0]
        assert dash_data["event_type"] == "FALL_DETECTED"
        assert dash_data["event_state"] == "ACTIVE"
        context = json.loads(dash_data["context"])
        assert "summary" in context
        assert context["clip_available"] is True

        # === Step 7: Verify cloud queue ===
        cloud_msgs = fakeredis_client.xrange("stream:cloud-queue", "-", "+")
        assert len(cloud_msgs) == 1
        _, cloud_data = cloud_msgs[0]
        assert cloud_data["priority"] == "HIGH"
        assert cloud_data["idempotency_key"] == f"SITE-001:{ds_msg['event_id']}"

        # === Step 8: Verify clip trigger ===
        clip_msgs = fakeredis_client.xrange("stream:clip-trigger", "-", "+")
        assert len(clip_msgs) == 1
        _, clip_data = clip_msgs[0]
        assert clip_data["device_id"] == "CAM-001"
        assert clip_data["pre_sec"] == "30"
        assert clip_data["post_sec"] == "30"

        # === Step 9: AWS Receiver consumes and transforms ===
        receiver = MockAwsReceiver(fakeredis_client)
        messages = receiver.consume_all_pending()
        assert len(messages) == 1

        mqtt_payload = receiver.transform_to_mqtt(messages[0]["data"])
        assert mqtt_payload["event_type"] == "FALL_DETECTED"
        assert mqtt_payload["risk_level"] == "CRITICAL"
        assert mqtt_payload["idempotency_key"] == f"SITE-001:{ds_msg['event_id']}"
        assert mqtt_payload["confidence"] == 0.92

        # === Step 10: Store event ===
        success = receiver.store_event(mqtt_payload)
        assert success is True


# ──────────────────────────────────────────────────────────────────────
# E2E Scenario 2: FIRE_DETECTED from Contact Sensor
# ──────────────────────────────────────────────────────────────────────


class TestE2EFireDetected:
    """E2E: FIRE_DETECTED 화재접점 이벤트의 전체 파이프라인"""

    @pytest.mark.e2e
    def test_full_pipeline_fire_contact(self, fakeredis_client):
        """
        FIRE_DETECTED (접점): Edge Sensor → stream:sensors →
        EventEngine → CRITICAL alarm → cloud queue HIGH priority
        """
        # Step 1: Fire contact event from Device Gateway
        producer = EdgeEventProducer(fakeredis_client)
        sensor_msg = producer.produce_fire_event()

        # Step 2: Verify in sensors stream
        sensor_len = fakeredis_client.xlen("stream:sensors")
        assert sensor_len == 1

        # Step 3: Event Engine processes (simulate as DS event for pipeline)
        engine = MockEventEngine(fakeredis_client)
        # Convert sensor message format for engine processing
        engine_input = {
            "event_id": sensor_msg["event_id"],
            "site_id": sensor_msg["site_id"],
            "device_id": sensor_msg["device_id"],
            "event_type": "FIRE_DETECTED",
            "timestamp": sensor_msg["timestamp"],
            "model_version": "",
            "inference": json.dumps({"pgie": None, "tracker": None}),
        }
        result = engine.process_ds_event(engine_input)

        # Step 4: Alarm must be CRITICAL with ALL_ON
        alarms = fakeredis_client.xrange("stream:alarms", "-", "+")
        assert len(alarms) == 1
        _, alarm_data = alarms[0]
        assert alarm_data["risk_level"] == "CRITICAL"
        assert alarm_data["action"] == "ALL_ON"

        # Step 5: Cloud queue must have HIGH priority
        cloud_msgs = fakeredis_client.xrange("stream:cloud-queue", "-", "+")
        _, cloud_data = cloud_msgs[0]
        assert cloud_data["priority"] == "HIGH"


# ──────────────────────────────────────────────────────────────────────
# E2E Scenario 3: Smart Band HEARTRATE_ABNORMAL
# ──────────────────────────────────────────────────────────────────────


class TestE2EHeartRateAbnormal:
    """E2E: HEARTRATE_ABNORMAL 스마트밴드 이벤트 파이프라인"""

    @pytest.mark.e2e
    def test_full_pipeline_heartrate(self, fakeredis_client):
        """
        HEARTRATE_ABNORMAL: Band → stream:sensors →
        EventEngine → WARNING alarm → cloud queue NORMAL priority
        """
        # Step 1: Band sensor event
        producer = EdgeEventProducer(fakeredis_client)
        sensor_msg = producer.produce_sensor_event(
            event_type="HEARTRATE_ABNORMAL",
            device_id="BAND-003",
            worker_id="WKR-0012",
            data_type="HEARTRATE",
            value=142.0,
            source="SMART_BAND",
        )

        # Step 2: Verify worker_id is present
        assert sensor_msg["worker_id"] == "WKR-0012"

        # Step 3: Event Engine processes
        engine = MockEventEngine(fakeredis_client)
        engine_input = {
            "event_id": sensor_msg["event_id"],
            "site_id": sensor_msg["site_id"],
            "device_id": sensor_msg["device_id"],
            "event_type": "HEARTRATE_ABNORMAL",
            "timestamp": sensor_msg["timestamp"],
            "model_version": "",
            "inference": json.dumps({"pgie": None, "tracker": None}),
        }
        result = engine.process_ds_event(engine_input)

        # Step 4: Alarm should be WARNING with LIGHT_ON
        alarms = fakeredis_client.xrange("stream:alarms", "-", "+")
        _, alarm_data = alarms[0]
        assert alarm_data["risk_level"] == "WARNING"
        assert alarm_data["action"] == "LIGHT_ON"

        # Step 5: Cloud queue with NORMAL priority
        cloud_msgs = fakeredis_client.xrange("stream:cloud-queue", "-", "+")
        _, cloud_data = cloud_msgs[0]
        assert cloud_data["priority"] == "NORMAL"


# ──────────────────────────────────────────────────────────────────────
# E2E Scenario 4: ENV_THRESHOLD_EXCEEDED
# ──────────────────────────────────────────────────────────────────────


class TestE2EEnvThreshold:
    """E2E: ENV_THRESHOLD_EXCEEDED 환경센서 이벤트 파이프라인"""

    @pytest.mark.e2e
    def test_full_pipeline_env_sensor(self, fakeredis_client):
        """
        ENV_THRESHOLD_EXCEEDED: ENV Sensor → stream:sensors →
        EventEngine → WARNING → cloud queue
        """
        producer = EdgeEventProducer(fakeredis_client)
        sensor_msg = producer.produce_env_event(
            device_id="ENV-002", data_type="GAS", value=28.5
        )

        # Verify in stream
        assert fakeredis_client.xlen("stream:sensors") == 1

        # Event Engine
        engine = MockEventEngine(fakeredis_client)
        engine_input = {
            "event_id": sensor_msg["event_id"],
            "site_id": sensor_msg["site_id"],
            "device_id": sensor_msg["device_id"],
            "event_type": "ENV_THRESHOLD_EXCEEDED",
            "timestamp": sensor_msg["timestamp"],
            "model_version": "",
            "inference": json.dumps({"pgie": None, "tracker": None}),
        }
        engine.process_ds_event(engine_input)

        # Verify WARNING alarm
        alarms = fakeredis_client.xrange("stream:alarms", "-", "+")
        _, alarm_data = alarms[0]
        assert alarm_data["risk_level"] == "WARNING"


# ──────────────────────────────────────────────────────────────────────
# E2E Scenario 5: Multiple Event Types in Sequence
# ──────────────────────────────────────────────────────────────────────


class TestE2EMultipleEvents:
    """E2E: 다양한 이벤트 타입이 순차적으로 처리됨"""

    @pytest.mark.e2e
    def test_mixed_events_pipeline(self, fakeredis_client):
        """
        Multiple event types processed correctly with proper
        risk_level and priority assignment
        """
        producer = EdgeEventProducer(fakeredis_client)
        engine = MockEventEngine(fakeredis_client)
        receiver = MockAwsReceiver(fakeredis_client)

        # Scenario: FALL → STILLNESS → DEVICE_OFFLINE → FIRE
        scenarios = [
            ("FALL_DETECTED", "CRITICAL", "HIGH", "ALL_ON"),
            ("STILLNESS_DETECTED", "WARNING", "NORMAL", "LIGHT_ON"),
            ("DEVICE_OFFLINE", "NORMAL", "LOW", "ALL_OFF"),
            ("FIRE_DETECTED", "CRITICAL", "HIGH", "ALL_ON"),
        ]

        for event_type, expected_risk, expected_priority, expected_action in scenarios:
            device_id = "FIRE-001" if event_type == "FIRE_DETECTED" else "CAM-001"
            msg = producer.produce_ds_event(
                event_type=event_type, device_id=device_id
            )
            engine.process_ds_event(msg)

        # Verify all 4 events in each downstream stream
        assert fakeredis_client.xlen("stream:ds-events") == 4
        assert fakeredis_client.xlen("stream:alarms") == 4
        assert fakeredis_client.xlen("stream:dashboard") == 4
        assert fakeredis_client.xlen("stream:cloud-queue") == 4

        # Verify priority ordering in cloud queue
        cloud_msgs = fakeredis_client.xrange("stream:cloud-queue", "-", "+")
        priorities = [m[1]["priority"] for m in cloud_msgs]
        assert priorities == ["HIGH", "NORMAL", "LOW", "HIGH"]

        # AWS Receiver processes all
        messages = receiver.consume_all_pending()
        assert len(messages) == 4

        # Transform all to MQTT
        for msg in messages:
            mqtt = receiver.transform_to_mqtt(msg["data"])
            assert mqtt["idempotency_key"] is not None

        assert len(receiver.mqtt_payloads) == 4


# ──────────────────────────────────────────────────────────────────────
# E2E Scenario 6: Schema Validation at Every Pipeline Stage
# ──────────────────────────────────────────────────────────────────────


class TestE2ESchemaValidationPipeline:
    """E2E: 파이프라인 각 단계에서 스키마 검증이 통과하는지 확인"""

    @pytest.mark.e2e
    def test_schema_valid_at_every_stage(self, fakeredis_client):
        """
        Each pipeline stage produces schema-valid messages:
        1. DsEventsMessage at stream:ds-events
        2. AlarmsMessage at stream:alarms
        3. CloudQueueMessage at stream:cloud-queue
        4. MqttEventPayload at AWS receiver output
        """
        producer = EdgeEventProducer(fakeredis_client)
        engine = MockEventEngine(fakeredis_client)
        receiver = MockAwsReceiver(fakeredis_client)

        # Produce and process
        msg = producer.produce_ds_event(
            event_type="COLLAPSE_DETECTED", confidence=0.88
        )
        engine.process_ds_event(msg)

        # Stage 1: Validate ds-events message
        ds_messages = fakeredis_client.xrange("stream:ds-events", "-", "+")
        _, ds_data = ds_messages[0]
        ds_data_parsed = dict(ds_data)
        ds_data_parsed["inference"] = json.loads(ds_data_parsed["inference"])
        ds_validated = DsEventsMessage(**ds_data_parsed)
        assert ds_validated.event_type == "COLLAPSE_DETECTED"

        # Stage 2: Validate alarm message
        alarm_messages = fakeredis_client.xrange("stream:alarms", "-", "+")
        _, alarm_data = alarm_messages[0]
        alarm_validated = AlarmsMessage(**alarm_data)
        assert alarm_validated.risk_level == "CRITICAL"

        # Stage 3: Validate cloud-queue message
        cloud_messages = fakeredis_client.xrange("stream:cloud-queue", "-", "+")
        _, cloud_data = cloud_messages[0]
        cloud_validated = CloudQueueMessage(**cloud_data)
        assert cloud_validated.priority == "HIGH"
        assert cloud_validated.idempotency_key == f"SITE-001:{msg['event_id']}"

        # Stage 4: AWS receiver output → MQTT payload validation
        messages = receiver.consume_all_pending()
        mqtt_payload = receiver.transform_to_mqtt(messages[0]["data"])
        mqtt_validated = MqttEventPayload(**mqtt_payload)
        assert mqtt_validated.event_type == "COLLAPSE_DETECTED"
        assert mqtt_validated.risk_level == "CRITICAL"


# ──────────────────────────────────────────────────────────────────────
# E2E Scenario 7: Error Propagation (Invalid Event Handling)
# ──────────────────────────────────────────────────────────────────────


class TestE2EErrorHandling:
    """E2E: 유효하지 않은 이벤트가 파이프라인에서 적절히 처리됨"""

    @pytest.mark.e2e
    def test_invalid_event_detected_before_processing(self):
        """Invalid events are caught by schema validation before pipeline entry"""
        invalid_event = {
            "event_id": "INVALID-ID",
            "site_id": "SITE-001",
            "source_id": "pipeline-0",
            "device_id": "CAM-001",
            "event_type": "FALL_DETECTED",
            "timestamp": "2025-05-19T12:00:00.123Z",
            "model_version": "v1.0.0-tao-ds",
            "inference": {
                "pgie": {"class_id": 2, "confidence": 0.9, "label": "fall",
                         "bbox": {"x": 0.1, "y": 0.2, "w": 0.3, "h": 0.4}},
                "tracker": {"object_id": 1, "age_frames": 5},
            },
        }

        with pytest.raises(ValidationError):
            DsEventsMessage(**invalid_event)

    @pytest.mark.e2e
    def test_valid_events_do_not_raise(self, fakeredis_client):
        """All valid fixture events can pass through full pipeline without errors"""
        producer = EdgeEventProducer(fakeredis_client)
        engine = MockEventEngine(fakeredis_client)

        event_types = [
            "FALL_DETECTED",
            "COLLAPSE_DETECTED",
            "STILLNESS_DETECTED",
            "ZONE_INTRUSION",
            "HAZARDOUS_ACTION",
        ]

        for et in event_types:
            msg = producer.produce_ds_event(event_type=et)
            result = engine.process_ds_event(msg)
            assert result["alarm"] is True
            assert result["cloud_queue"] is True


# ──────────────────────────────────────────────────────────────────────
# E2E Scenario 8: Consistency Rules Through Pipeline
# ──────────────────────────────────────────────────────────────────────


class TestE2EConsistencyRules:
    """E2E: 일관성 규칙이 파이프라인 전체에 걸쳐 유지됨"""

    @pytest.mark.e2e
    def test_c001_risk_level_consistency_through_pipeline(self, fakeredis_client):
        """C-001: CRITICAL events maintain CRITICAL risk through all streams"""
        producer = EdgeEventProducer(fakeredis_client)
        engine = MockEventEngine(fakeredis_client)

        msg = producer.produce_ds_event(event_type="FALL_DETECTED")
        engine.process_ds_event(msg)

        # All downstream streams should have CRITICAL
        alarms = fakeredis_client.xrange("stream:alarms", "-", "+")
        assert alarms[0][1]["risk_level"] == "CRITICAL"

        dashboard = fakeredis_client.xrange("stream:dashboard", "-", "+")
        assert dashboard[0][1]["risk_level"] == "CRITICAL"

        cloud = fakeredis_client.xrange("stream:cloud-queue", "-", "+")
        assert cloud[0][1]["risk_level"] == "CRITICAL"

    @pytest.mark.e2e
    def test_c003_idempotency_key_consistency(self, fakeredis_client):
        """C-003: idempotency_key is consistent across pipeline"""
        producer = EdgeEventProducer(fakeredis_client)
        engine = MockEventEngine(fakeredis_client)
        receiver = MockAwsReceiver(fakeredis_client)

        msg = producer.produce_ds_event(event_type="FALL_DETECTED")
        engine.process_ds_event(msg)

        expected_key = f"SITE-001:{msg['event_id']}"

        # Cloud queue
        cloud = fakeredis_client.xrange("stream:cloud-queue", "-", "+")
        assert cloud[0][1]["idempotency_key"] == expected_key

        # MQTT payload
        messages = receiver.consume_all_pending()
        mqtt = receiver.transform_to_mqtt(messages[0]["data"])
        assert mqtt["idempotency_key"] == expected_key

    @pytest.mark.e2e
    def test_c004_priority_risk_mapping_through_pipeline(self, fakeredis_client):
        """C-004: Priority correctly maps from risk_level through pipeline"""
        producer = EdgeEventProducer(fakeredis_client)
        engine = MockEventEngine(fakeredis_client)

        test_cases = [
            ("FALL_DETECTED", "CRITICAL", "HIGH"),
            ("STILLNESS_DETECTED", "WARNING", "NORMAL"),
            ("DEVICE_OFFLINE", "NORMAL", "LOW"),
        ]

        for event_type, expected_risk, expected_priority in test_cases:
            # Clear streams
            for stream in ["stream:ds-events", "stream:alarms", "stream:dashboard",
                           "stream:cloud-queue", "stream:clip-trigger"]:
                fakeredis_client.delete(stream)

            device_id = "CAM-001"
            msg = producer.produce_ds_event(event_type=event_type, device_id=device_id)
            engine.process_ds_event(msg)

            cloud = fakeredis_client.xrange("stream:cloud-queue", "-", "+")
            assert cloud[0][1]["priority"] == expected_priority, (
                f"{event_type}: expected priority {expected_priority}"
            )
