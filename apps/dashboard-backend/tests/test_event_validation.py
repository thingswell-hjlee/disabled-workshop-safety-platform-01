"""
Event Message Schema Validation Tests

PR #16 확정 스키마(event-message-schema.md, aws-iot-message-schema.md) 기준으로
payload 검증 로직을 테스트합니다.

실행: pytest apps/dashboard-backend/tests/test_event_validation.py -v
"""

import pytest
from datetime import datetime, timezone, timedelta
from pydantic import ValidationError

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from schemas import IoTEventPayload, IoTStatusPayload


class TestEventPayloadValidation:
    """IoT Event Payload validation tests."""

    def _make_valid_event(self, **overrides) -> dict:
        """Create a valid event payload for testing."""
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        base = {
            "event_id": "EVT-20250519120000-001",
            "site_id": "SITE-001",
            "device_id": "CAM-001",
            "worker_id": None,
            "event_type": "FALL_DETECTED",
            "risk_level": "CRITICAL",
            "confidence": 0.92,
            "model_version": "v1.0.0-tao-ds",
            "timestamp": now,
            "context_summary": "작업장 A구역 낙상 감지 (신뢰도 92%)",
            "clip_s3_key": "events/SITE-001/2025/05/19/EVT-20250519120000-001.mp4",
            "idempotency_key": "SITE-001:EVT-20250519120000-001",
        }
        base.update(overrides)
        return base

    def test_valid_fall_detected_event(self):
        """Valid FALL_DETECTED event should pass validation."""
        data = self._make_valid_event()
        event = IoTEventPayload(**data)
        assert event.event_id == "EVT-20250519120000-001"
        assert event.event_type.value == "FALL_DETECTED"
        assert event.risk_level.value == "CRITICAL"

    def test_valid_fire_detected_contact(self):
        """FIRE_DETECTED from contact sensor (no confidence/model_version needed if from FIRE device)."""
        # FIRE_DETECTED from FIRE-001 (contact) does NOT require confidence/model_version
        # BUT our schema requires it for FIRE_DETECTED only from camera (VISION_AI check)
        # Actually, looking at the schema: FIRE_DETECTED is NOT in VISION_AI_EVENTS
        # So confidence is optional for fire
        data = self._make_valid_event(
            device_id="FIRE-001",
            event_type="FIRE_DETECTED",
            risk_level="CRITICAL",
            confidence=None,
            model_version=None,
            idempotency_key="SITE-001:EVT-20250519120000-001",
        )
        event = IoTEventPayload(**data)
        assert event.event_type.value == "FIRE_DETECTED"
        assert event.confidence is None

    def test_valid_env_threshold_exceeded(self):
        """ENV_THRESHOLD_EXCEEDED event should pass."""
        data = self._make_valid_event(
            device_id="ENV-001",
            event_type="ENV_THRESHOLD_EXCEEDED",
            risk_level="WARNING",
            confidence=None,
            model_version=None,
        )
        event = IoTEventPayload(**data)
        assert event.event_type.value == "ENV_THRESHOLD_EXCEEDED"

    def test_valid_band_fall_detected(self):
        """BAND_FALL_DETECTED with worker_id should pass."""
        data = self._make_valid_event(
            device_id="BAND-001",
            event_type="BAND_FALL_DETECTED",
            risk_level="WARNING",
            worker_id="WKR-0001",
            confidence=None,
            model_version=None,
        )
        event = IoTEventPayload(**data)
        assert event.worker_id == "WKR-0001"

    # --- Invalid Cases ---

    def test_invalid_event_id_format(self):
        """event_id not matching pattern should fail."""
        data = self._make_valid_event(event_id="INVALID-ID")
        with pytest.raises(ValidationError) as exc_info:
            IoTEventPayload(**data)
        assert "event_id" in str(exc_info.value)

    def test_invalid_site_id_format(self):
        """site_id not matching SITE-NNN should fail."""
        data = self._make_valid_event(site_id="WRONG-01")
        with pytest.raises(ValidationError) as exc_info:
            IoTEventPayload(**data)
        assert "site_id" in str(exc_info.value)

    def test_invalid_device_id_format(self):
        """device_id with wrong prefix should fail."""
        data = self._make_valid_event(device_id="SENSOR-001")
        with pytest.raises(ValidationError) as exc_info:
            IoTEventPayload(**data)
        assert "device_id" in str(exc_info.value)

    def test_invalid_event_type(self):
        """Non-existent event_type should fail."""
        data = self._make_valid_event(event_type="EXPLOSION_DETECTED")
        with pytest.raises(ValidationError) as exc_info:
            IoTEventPayload(**data)
        assert "event_type" in str(exc_info.value).lower() or "input" in str(exc_info.value).lower()

    def test_invalid_risk_level(self):
        """Invalid risk_level should fail."""
        data = self._make_valid_event(risk_level="HIGH")
        with pytest.raises(ValidationError) as exc_info:
            IoTEventPayload(**data)
        assert "risk_level" in str(exc_info.value).lower() or "input" in str(exc_info.value).lower()

    def test_critical_event_with_wrong_risk_level(self):
        """FALL_DETECTED must have risk_level=CRITICAL."""
        data = self._make_valid_event(
            event_type="FALL_DETECTED",
            risk_level="WARNING",
        )
        with pytest.raises(ValidationError) as exc_info:
            IoTEventPayload(**data)
        assert "CRITICAL" in str(exc_info.value)

    def test_collapse_must_be_critical(self):
        """COLLAPSE_DETECTED must have risk_level=CRITICAL."""
        data = self._make_valid_event(
            event_type="COLLAPSE_DETECTED",
            risk_level="NORMAL",
        )
        with pytest.raises(ValidationError) as exc_info:
            IoTEventPayload(**data)
        assert "CRITICAL" in str(exc_info.value)

    def test_worker_required_event_without_worker(self):
        """HEARTRATE_ABNORMAL without worker_id should fail."""
        data = self._make_valid_event(
            device_id="BAND-001",
            event_type="HEARTRATE_ABNORMAL",
            risk_level="WARNING",
            worker_id=None,
            confidence=None,
            model_version=None,
        )
        with pytest.raises(ValidationError) as exc_info:
            IoTEventPayload(**data)
        assert "worker_id" in str(exc_info.value)

    def test_band_disconnected_without_worker(self):
        """BAND_DISCONNECTED without worker_id should fail."""
        data = self._make_valid_event(
            device_id="BAND-002",
            event_type="BAND_DISCONNECTED",
            risk_level="WARNING",
            worker_id=None,
            confidence=None,
            model_version=None,
        )
        with pytest.raises(ValidationError) as exc_info:
            IoTEventPayload(**data)
        assert "worker_id" in str(exc_info.value)

    def test_vision_ai_event_without_confidence(self):
        """FALL_DETECTED (Vision AI) without confidence should fail."""
        data = self._make_valid_event(confidence=None)
        with pytest.raises(ValidationError) as exc_info:
            IoTEventPayload(**data)
        assert "confidence" in str(exc_info.value)

    def test_vision_ai_event_without_model_version(self):
        """ZONE_INTRUSION without model_version should fail."""
        data = self._make_valid_event(
            event_type="ZONE_INTRUSION",
            risk_level="WARNING",
            confidence=0.85,
            model_version=None,
        )
        with pytest.raises(ValidationError) as exc_info:
            IoTEventPayload(**data)
        assert "model_version" in str(exc_info.value)

    def test_confidence_out_of_range(self):
        """confidence > 1.0 should fail."""
        data = self._make_valid_event(confidence=1.5)
        with pytest.raises(ValidationError) as exc_info:
            IoTEventPayload(**data)
        assert "confidence" in str(exc_info.value).lower() or "less than" in str(exc_info.value).lower()

    def test_confidence_negative(self):
        """confidence < 0.0 should fail."""
        data = self._make_valid_event(confidence=-0.1)
        with pytest.raises(ValidationError) as exc_info:
            IoTEventPayload(**data)

    def test_invalid_model_version_format(self):
        """model_version not matching pattern should fail."""
        data = self._make_valid_event(model_version="1.0.0")
        with pytest.raises(ValidationError) as exc_info:
            IoTEventPayload(**data)
        assert "model_version" in str(exc_info.value)

    def test_invalid_worker_id_format(self):
        """worker_id not matching WKR-NNNN should fail."""
        data = self._make_valid_event(
            device_id="BAND-001",
            event_type="BAND_FALL_DETECTED",
            risk_level="WARNING",
            worker_id="WORKER-1",
            confidence=None,
            model_version=None,
        )
        with pytest.raises(ValidationError) as exc_info:
            IoTEventPayload(**data)
        assert "worker_id" in str(exc_info.value)

    def test_wrong_idempotency_key(self):
        """idempotency_key must be {site_id}:{event_id}."""
        data = self._make_valid_event(idempotency_key="WRONG-KEY")
        with pytest.raises(ValidationError) as exc_info:
            IoTEventPayload(**data)
        assert "idempotency_key" in str(exc_info.value)

    def test_future_timestamp_rejected(self):
        """Timestamp more than 5 seconds in the future should fail."""
        future = (datetime.now(timezone.utc) + timedelta(minutes=10)).strftime(
            "%Y-%m-%dT%H:%M:%S.%f"
        )[:-3] + "Z"
        data = self._make_valid_event(timestamp=future)
        with pytest.raises(ValidationError) as exc_info:
            IoTEventPayload(**data)
        assert "future" in str(exc_info.value)

    def test_invalid_timestamp_format(self):
        """Non-ISO8601 timestamp should fail."""
        data = self._make_valid_event(timestamp="2025/05/19 12:00:00")
        with pytest.raises(ValidationError) as exc_info:
            IoTEventPayload(**data)
        assert "timestamp" in str(exc_info.value)


class TestStatusPayloadValidation:
    """IoT Status Payload validation tests."""

    def _make_valid_status(self, **overrides) -> dict:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        base = {
            "site_id": "SITE-001",
            "timestamp": now,
            "edge_status": "HEALTHY",
            "deepstream_fps": [29.8, 30.1, 28.5, 30.0],
            "gpu_utilization": 0.65,
            "active_cameras": 4,
            "active_bands": 8,
            "pending_cloud_events": 0,
        }
        base.update(overrides)
        return base

    def test_valid_status(self):
        """Valid status payload should pass."""
        data = self._make_valid_status()
        status = IoTStatusPayload(**data)
        assert status.edge_status.value == "HEALTHY"
        assert status.active_cameras == 4

    def test_invalid_edge_status(self):
        """Invalid edge_status should fail."""
        data = self._make_valid_status(edge_status="OFFLINE")
        with pytest.raises(ValidationError):
            IoTStatusPayload(**data)

    def test_gpu_utilization_out_of_range(self):
        """gpu_utilization > 1.0 should fail."""
        data = self._make_valid_status(gpu_utilization=1.5)
        with pytest.raises(ValidationError):
            IoTStatusPayload(**data)

    def test_invalid_site_id(self):
        """Invalid site_id should fail."""
        data = self._make_valid_status(site_id="INVALID")
        with pytest.raises(ValidationError):
            IoTStatusPayload(**data)

    def test_negative_cameras(self):
        """Negative active_cameras should fail."""
        data = self._make_valid_status(active_cameras=-1)
        with pytest.raises(ValidationError):
            IoTStatusPayload(**data)


class TestAllEventTypes:
    """Test all valid event_types can be created."""

    def _make_event_for_type(self, event_type: str) -> dict:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

        # Map event types to appropriate settings
        vision_ai = ["FALL_DETECTED", "COLLAPSE_DETECTED", "ZONE_INTRUSION",
                     "STILLNESS_DETECTED", "HAZARDOUS_ACTION"]
        worker_required = ["HEARTRATE_ABNORMAL", "TEMPERATURE_ABNORMAL",
                           "BAND_FALL_DETECTED", "BAND_DISCONNECTED"]
        critical_only = ["FALL_DETECTED", "COLLAPSE_DETECTED", "FIRE_DETECTED"]

        risk = "CRITICAL" if event_type in critical_only else "WARNING"
        confidence = 0.88 if event_type in vision_ai else None
        model_version = "v1.0.0-tao-ds" if event_type in vision_ai else None
        worker_id = "WKR-0001" if event_type in worker_required else None

        if event_type.startswith("BAND") or event_type in ["HEARTRATE_ABNORMAL", "TEMPERATURE_ABNORMAL"]:
            device_id = "BAND-001"
        elif event_type == "ENV_THRESHOLD_EXCEEDED":
            device_id = "ENV-001"
        elif event_type == "FIRE_DETECTED":
            device_id = "FIRE-001"
        elif event_type in ["DEVICE_OFFLINE", "DEVICE_ONLINE"]:
            device_id = "CAM-001"
        elif event_type in ["NORMAL_RESTORED", "SYSTEM_ALERT"]:
            device_id = "NVR-001"
        else:
            device_id = "CAM-001"

        return {
            "event_id": "EVT-20250519120000-001",
            "site_id": "SITE-001",
            "device_id": device_id,
            "worker_id": worker_id,
            "event_type": event_type,
            "risk_level": risk,
            "confidence": confidence,
            "model_version": model_version,
            "timestamp": now,
            "context_summary": f"Test event: {event_type}",
            "clip_s3_key": None,
            "idempotency_key": "SITE-001:EVT-20250519120000-001",
        }

    @pytest.mark.parametrize("event_type", [
        "FALL_DETECTED", "COLLAPSE_DETECTED", "ZONE_INTRUSION",
        "STILLNESS_DETECTED", "HAZARDOUS_ACTION", "FIRE_DETECTED",
        "HEARTRATE_ABNORMAL", "TEMPERATURE_ABNORMAL",
        "BAND_FALL_DETECTED", "BAND_DISCONNECTED",
        "ENV_THRESHOLD_EXCEEDED", "DEVICE_OFFLINE", "DEVICE_ONLINE",
        "NORMAL_RESTORED", "SYSTEM_ALERT",
    ])
    def test_all_event_types_valid(self, event_type):
        """Each Platform 1.0 event_type should create a valid payload."""
        data = self._make_event_for_type(event_type)
        event = IoTEventPayload(**data)
        assert event.event_type.value == event_type
