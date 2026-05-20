"""
MQTT Payload Schema Validation Tests
======================================
AWS IoT Core MQTT 토픽별 페이로드 스키마 검증.
Reference: docs/aws-iot-message-schema.md
"""

import pytest
from pydantic import ValidationError

from tests.schema.models import (
    MqttEventPayload,
    MqttModelDeployCommand,
    MqttModelStatusReport,
    MqttStatusPayload,
)


# ──────────────────────────────────────────────────────────────────────
# safety/{site_id}/events Tests
# ──────────────────────────────────────────────────────────────────────


class TestMqttEventPayload:
    """MQTT safety/{site_id}/events payload validation"""

    @pytest.mark.mqtt
    @pytest.mark.schema
    def test_valid_event_payload(self, mqtt_payloads):
        """Valid MQTT event payload passes validation"""
        payloads = mqtt_payloads["safety/{site_id}/events"]
        result = MqttEventPayload(**payloads[0])
        assert result.event_id == "EVT-20250519120000-001"
        assert result.context_summary == "작업장 A구역 낙상 감지 (신뢰도 92%)"
        assert result.idempotency_key == "SITE-001:EVT-20250519120000-001"

    @pytest.mark.mqtt
    @pytest.mark.schema
    def test_fire_event_payload(self, mqtt_payloads):
        """FIRE_DETECTED payload with null confidence/model_version"""
        payloads = mqtt_payloads["safety/{site_id}/events"]
        result = MqttEventPayload(**payloads[1])
        assert result.event_type == "FIRE_DETECTED"
        assert result.confidence is None
        assert result.model_version is None

    @pytest.mark.mqtt
    @pytest.mark.schema
    def test_event_payload_requires_context_summary(self):
        """MQTT event payload must have context_summary"""
        with pytest.raises(ValidationError):
            MqttEventPayload(
                event_id="EVT-20250519120000-001",
                site_id="SITE-001",
                device_id="CAM-001",
                event_type="FALL_DETECTED",
                risk_level="CRITICAL",
                timestamp="2025-05-19T12:00:00.123Z",
                # Missing context_summary
                idempotency_key="SITE-001:EVT-20250519120000-001",
            )

    @pytest.mark.mqtt
    @pytest.mark.schema
    def test_event_payload_requires_idempotency_key(self):
        """MQTT event payload must have idempotency_key"""
        with pytest.raises(ValidationError):
            MqttEventPayload(
                event_id="EVT-20250519120000-001",
                site_id="SITE-001",
                device_id="CAM-001",
                event_type="FALL_DETECTED",
                risk_level="CRITICAL",
                timestamp="2025-05-19T12:00:00.123Z",
                context_summary="낙상 감지",
                # Missing idempotency_key
            )


# ──────────────────────────────────────────────────────────────────────
# safety/{site_id}/status Tests
# ──────────────────────────────────────────────────────────────────────


class TestMqttStatusPayload:
    """MQTT safety/{site_id}/status payload validation"""

    @pytest.mark.mqtt
    @pytest.mark.schema
    def test_valid_status_payload(self, mqtt_payloads):
        """Valid MQTT status payload passes validation"""
        payloads = mqtt_payloads["safety/{site_id}/status"]
        result = MqttStatusPayload(**payloads[0])
        assert result.edge_status == "HEALTHY"
        assert result.gpu_utilization == 0.65
        assert result.active_cameras == 8
        assert result.active_bands == 8
        assert len(result.deepstream_fps) == 8

    @pytest.mark.mqtt
    @pytest.mark.schema
    @pytest.mark.parametrize("status", ["HEALTHY", "DEGRADED", "ERROR"])
    def test_valid_edge_statuses(self, status):
        """All valid edge_status values accepted"""
        result = MqttStatusPayload(
            site_id="SITE-001",
            timestamp="2025-05-19T12:00:00.000Z",
            edge_status=status,
            deepstream_fps=[30.0],
            gpu_utilization=0.5,
            active_cameras=4,
            active_bands=8,
            pending_cloud_events=0,
        )
        assert result.edge_status == status

    @pytest.mark.mqtt
    @pytest.mark.schema
    def test_invalid_edge_status(self):
        """Invalid edge_status rejected"""
        with pytest.raises(ValidationError):
            MqttStatusPayload(
                site_id="SITE-001",
                timestamp="2025-05-19T12:00:00.000Z",
                edge_status="OFFLINE",  # Invalid
                deepstream_fps=[30.0],
                gpu_utilization=0.5,
                active_cameras=4,
                active_bands=8,
                pending_cloud_events=0,
            )

    @pytest.mark.mqtt
    @pytest.mark.schema
    def test_gpu_utilization_boundary(self):
        """gpu_utilization must be 0.0~1.0 (C-007)"""
        with pytest.raises(ValidationError):
            MqttStatusPayload(
                site_id="SITE-001",
                timestamp="2025-05-19T12:00:00.000Z",
                edge_status="HEALTHY",
                deepstream_fps=[30.0],
                gpu_utilization=1.5,  # Over 1.0
                active_cameras=4,
                active_bands=8,
                pending_cloud_events=0,
            )


# ──────────────────────────────────────────────────────────────────────
# safety/{site_id}/models Tests
# ──────────────────────────────────────────────────────────────────────


class TestMqttModelPayload:
    """MQTT safety/{site_id}/models payload validation"""

    @pytest.mark.mqtt
    @pytest.mark.schema
    def test_valid_deploy_command(self, mqtt_payloads):
        """Valid model deploy command passes validation"""
        payloads = mqtt_payloads["safety/{site_id}/models"]
        result = MqttModelDeployCommand(**payloads[0])
        assert result.action == "DEPLOY"
        assert result.model_version == "v1.1.0-tao-ds"
        assert result.model_type == "pgie"

    @pytest.mark.mqtt
    @pytest.mark.schema
    def test_valid_status_report(self, mqtt_payloads):
        """Valid model status report passes validation"""
        payloads = mqtt_payloads["safety/{site_id}/models"]
        result = MqttModelStatusReport(**payloads[1])
        assert result.action == "DEPLOY_STATUS"
        assert result.status == "ACTIVE"
        assert result.progress == 1.0

    @pytest.mark.mqtt
    @pytest.mark.schema
    @pytest.mark.parametrize("action", ["DEPLOY", "ROLLBACK", "STATUS_REQUEST"])
    def test_valid_deploy_actions(self, action):
        """All valid deploy actions accepted"""
        result = MqttModelDeployCommand(
            action=action,
            model_version="v1.0.0-tao-ds",
            model_type="pgie",
            s3_uri="s3://bucket/model.zip",
            timestamp="2025-05-19T12:00:00.000Z",
        )
        assert result.action == action

    @pytest.mark.mqtt
    @pytest.mark.schema
    @pytest.mark.parametrize(
        "status",
        ["DOWNLOADING", "STAGED", "DEPLOYING", "ACTIVE", "FAILED", "ROLLBACK"],
    )
    def test_valid_model_statuses(self, status):
        """All valid model statuses accepted"""
        result = MqttModelStatusReport(
            site_id="SITE-001",
            action="DEPLOY_STATUS",
            model_version="v1.0.0-tao-ds",
            status=status,
            progress=0.5 if status == "DOWNLOADING" else None,
            timestamp="2025-05-19T12:00:00.000Z",
        )
        assert result.status == status

    @pytest.mark.mqtt
    @pytest.mark.schema
    def test_invalid_model_type(self):
        """Invalid model_type rejected"""
        with pytest.raises(ValidationError):
            MqttModelDeployCommand(
                action="DEPLOY",
                model_version="v1.0.0-tao-ds",
                model_type="tgie",  # Invalid
                s3_uri="s3://bucket/model.zip",
                timestamp="2025-05-19T12:00:00.000Z",
            )
