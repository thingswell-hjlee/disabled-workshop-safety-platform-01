"""
Event Schema Validation Tests.

PR #16 event-message-schema 기준 스키마 검증.
- Format validation (ID patterns, timestamp, enums)
- Completeness (required fields)
- Consistency (risk_level ↔ event_type)
- Boundary tests (confidence range, bbox range)
"""

import json
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.event_schema import (
    CRITICAL_EVENT_TYPES,
    DEVICE_ID_PATTERN,
    EVENT_ID_PATTERN,
    MODEL_VERSION_PATTERN,
    SITE_ID_PATTERN,
    VALID_EVENT_TYPES,
    VALID_RISK_LEVELS,
    VISION_AI_EVENT_TYPES,
    BBox,
    DSEvent,
    DeviceStatusEvent,
    InferenceResult,
    PGIEResult,
    TrackerResult,
    generate_event_id,
    generate_timestamp,
    validate_ds_event,
)


# ─── Format Validation Tests ────────────────────────────────────────────────


class TestEventIdFormat:
    """event_id format: EVT-YYYYMMDDHHmmss-SEQ"""

    def test_valid_event_id(self):
        event_id = generate_event_id()
        assert EVENT_ID_PATTERN.match(event_id), f"Invalid event_id: {event_id}"

    def test_event_id_sequential(self):
        id1 = generate_event_id()
        id2 = generate_event_id()
        # Both should be valid
        assert EVENT_ID_PATTERN.match(id1)
        assert EVENT_ID_PATTERN.match(id2)
        # They should differ (at least in sequence)
        assert id1 != id2

    def test_event_id_pattern_valid_examples(self):
        valid = ["EVT-20250519120000-001", "EVT-20251231235959-999"]
        for eid in valid:
            assert EVENT_ID_PATTERN.match(eid), f"Should be valid: {eid}"

    def test_event_id_pattern_invalid_examples(self):
        invalid = [
            "EVT-2025051912-001",       # short timestamp
            "EVT-20250519120000-01",     # short sequence
            "EVT-20250519120000-0001",   # long sequence
            "EVT_20250519120000_001",    # wrong separator
            "20250519120000-001",        # missing prefix
            "",                          # empty
            "INVALID",                   # garbage
        ]
        for eid in invalid:
            assert not EVENT_ID_PATTERN.match(eid), f"Should be invalid: {eid}"


class TestSiteIdFormat:
    """site_id format: SITE-NNN"""

    def test_valid_site_ids(self):
        valid = ["SITE-001", "SITE-099", "SITE-999"]
        for sid in valid:
            assert SITE_ID_PATTERN.match(sid), f"Should be valid: {sid}"

    def test_invalid_site_ids(self):
        invalid = ["SITE-01", "SITE-1000", "site-001", "SITE001", ""]
        for sid in invalid:
            assert not SITE_ID_PATTERN.match(sid), f"Should be invalid: {sid}"


class TestDeviceIdFormat:
    """device_id format: {TYPE}-NNN"""

    def test_valid_device_ids(self):
        valid = [
            "CAM-001", "CAM-008",
            "BAND-001", "BAND-012",
            "ENV-001", "ENV-003",
            "FIRE-001",
            "NVR-001",
            "ALARM-001",
        ]
        for did in valid:
            assert DEVICE_ID_PATTERN.match(did), f"Should be valid: {did}"

    def test_invalid_device_ids(self):
        invalid = [
            "CAMERA-001",   # invalid prefix
            "CAM-01",       # short number
            "CAM-0001",     # long number
            "cam-001",      # lowercase
            "CAM--001",     # double dash
            "001",          # no prefix
            "",             # empty
        ]
        for did in invalid:
            assert not DEVICE_ID_PATTERN.match(did), f"Should be invalid: {did}"


class TestModelVersionFormat:
    """model_version format: v{M}.{m}.{p}-{tool}-{target}"""

    def test_valid_versions(self):
        valid = [
            "v1.0.0-tao-ds",
            "v1.0.0-pretrained-ds",
            "v2.1.0-custom-cloud",
            "v0.1.0-tao-ds",
            "v10.20.30-custom-ds",
        ]
        for v in valid:
            assert MODEL_VERSION_PATTERN.match(v), f"Should be valid: {v}"

    def test_invalid_versions(self):
        invalid = [
            "1.0.0-tao-ds",        # missing 'v'
            "v1.0-tao-ds",         # missing patch
            "v1.0.0-unknown-ds",   # invalid tool
            "v1.0.0-tao-edge",     # invalid target
            "v1.0.0-tao",          # missing target
            "",                    # empty
        ]
        for v in invalid:
            assert not MODEL_VERSION_PATTERN.match(v), f"Should be invalid: {v}"


class TestTimestampFormat:
    """timestamp: ISO 8601 UTC with millisecond precision"""

    def test_generated_timestamp_format(self):
        ts = generate_timestamp()
        pattern = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$")
        assert pattern.match(ts), f"Invalid timestamp: {ts}"

    def test_timestamp_ends_with_z(self):
        ts = generate_timestamp()
        assert ts.endswith("Z")

    def test_timestamp_has_milliseconds(self):
        ts = generate_timestamp()
        # Should have exactly 3 digits after the dot
        parts = ts.split(".")
        assert len(parts) == 2
        assert len(parts[1]) == 4  # "mmmZ"


# ─── Completeness Tests ─────────────────────────────────────────────────────


class TestDSEventCompleteness:
    """Required fields for stream:ds-events messages."""

    def test_valid_fall_event_passes_validation(self, sample_fall_event):
        event_dict = sample_fall_event.to_redis_dict()
        errors = validate_ds_event(event_dict)
        assert errors == [], f"Validation errors: {errors}"

    def test_valid_collapse_event_passes_validation(self, sample_collapse_event):
        event_dict = sample_collapse_event.to_redis_dict()
        errors = validate_ds_event(event_dict)
        assert errors == [], f"Validation errors: {errors}"

    def test_missing_event_id_fails(self, sample_fall_event):
        event_dict = sample_fall_event.to_redis_dict()
        del event_dict["event_id"]
        errors = validate_ds_event(event_dict)
        assert any("event_id" in e for e in errors)

    def test_missing_site_id_fails(self, sample_fall_event):
        event_dict = sample_fall_event.to_redis_dict()
        del event_dict["site_id"]
        errors = validate_ds_event(event_dict)
        assert any("site_id" in e for e in errors)

    def test_missing_device_id_fails(self, sample_fall_event):
        event_dict = sample_fall_event.to_redis_dict()
        del event_dict["device_id"]
        errors = validate_ds_event(event_dict)
        assert any("device_id" in e for e in errors)

    def test_missing_inference_fails(self, sample_fall_event):
        event_dict = sample_fall_event.to_redis_dict()
        del event_dict["inference"]
        errors = validate_ds_event(event_dict)
        assert any("inference" in e for e in errors)

    def test_missing_model_version_fails(self, sample_fall_event):
        event_dict = sample_fall_event.to_redis_dict()
        del event_dict["model_version"]
        errors = validate_ds_event(event_dict)
        assert any("model_version" in e for e in errors)

    def test_all_required_fields_present(self, sample_fall_event):
        event_dict = sample_fall_event.to_redis_dict()
        required = [
            "event_id", "site_id", "source_id", "device_id",
            "event_type", "timestamp", "model_version", "inference"
        ]
        for field in required:
            assert field in event_dict, f"Missing required field: {field}"


# ─── Consistency Tests ───────────────────────────────────────────────────────


class TestEventConsistency:
    """Consistency rules between fields."""

    def test_all_event_types_are_valid(self):
        """Verify our enum set matches schema."""
        expected = {
            "FALL_DETECTED", "COLLAPSE_DETECTED", "ZONE_INTRUSION",
            "STILLNESS_DETECTED", "HAZARDOUS_ACTION", "FIRE_DETECTED",
            "HEARTRATE_ABNORMAL", "TEMPERATURE_ABNORMAL", "BAND_FALL_DETECTED",
            "BAND_DISCONNECTED", "ENV_THRESHOLD_EXCEEDED", "DEVICE_OFFLINE",
            "DEVICE_ONLINE", "NORMAL_RESTORED", "SYSTEM_ALERT"
        }
        assert VALID_EVENT_TYPES == expected

    def test_critical_events_are_correct(self):
        """FALL, COLLAPSE, FIRE must be CRITICAL."""
        assert "FALL_DETECTED" in CRITICAL_EVENT_TYPES
        assert "COLLAPSE_DETECTED" in CRITICAL_EVENT_TYPES
        assert "FIRE_DETECTED" in CRITICAL_EVENT_TYPES

    def test_vision_ai_events_require_model_version(self):
        """Vision AI events must include model_version."""
        for event_type in VISION_AI_EVENT_TYPES:
            event = DSEvent(
                event_id=generate_event_id(),
                site_id="SITE-001",
                source_id="pipeline-0",
                device_id="CAM-001",
                event_type=event_type,
                timestamp=generate_timestamp(),
                model_version="v1.0.0-tao-ds",
                inference=InferenceResult(
                    pgie=PGIEResult(
                        class_id=1, confidence=0.8,
                        label="test", bbox=BBox(0.1, 0.1, 0.2, 0.2)
                    ),
                    tracker=TrackerResult(object_id=1, age_frames=1),
                ),
            )
            event_dict = event.to_redis_dict()
            errors = validate_ds_event(event_dict)
            assert errors == [], f"{event_type} validation failed: {errors}"

    def test_invalid_event_type_fails(self):
        event_dict = {
            "event_id": generate_event_id(),
            "site_id": "SITE-001",
            "source_id": "pipeline-0",
            "device_id": "CAM-001",
            "event_type": "INVALID_TYPE",
            "timestamp": generate_timestamp(),
            "model_version": "v1.0.0-tao-ds",
            "inference": json.dumps({
                "pgie": {"class_id": 1, "confidence": 0.8, "label": "test",
                         "bbox": {"x": 0.1, "y": 0.1, "w": 0.2, "h": 0.2}},
                "tracker": {"object_id": 1, "age_frames": 1},
            }),
        }
        errors = validate_ds_event(event_dict)
        assert any("event_type" in e for e in errors)


# ─── Boundary Tests ──────────────────────────────────────────────────────────


class TestBoundaryValues:
    """Boundary value tests for numeric fields."""

    def test_confidence_minimum_valid(self):
        """Confidence 0.0 is valid."""
        event = DSEvent(
            event_id=generate_event_id(),
            site_id="SITE-001",
            source_id="pipeline-0",
            device_id="CAM-001",
            event_type="FALL_DETECTED",
            timestamp=generate_timestamp(),
            model_version="v1.0.0-tao-ds",
            inference=InferenceResult(
                pgie=PGIEResult(
                    class_id=1, confidence=0.0,
                    label="fall", bbox=BBox(0.1, 0.1, 0.2, 0.2)
                ),
                tracker=TrackerResult(object_id=1, age_frames=1),
            ),
        )
        errors = validate_ds_event(event.to_redis_dict())
        assert errors == []

    def test_confidence_maximum_valid(self):
        """Confidence 1.0 is valid."""
        event = DSEvent(
            event_id=generate_event_id(),
            site_id="SITE-001",
            source_id="pipeline-0",
            device_id="CAM-001",
            event_type="FALL_DETECTED",
            timestamp=generate_timestamp(),
            model_version="v1.0.0-tao-ds",
            inference=InferenceResult(
                pgie=PGIEResult(
                    class_id=1, confidence=1.0,
                    label="fall", bbox=BBox(0.1, 0.1, 0.2, 0.2)
                ),
                tracker=TrackerResult(object_id=1, age_frames=1),
            ),
        )
        errors = validate_ds_event(event.to_redis_dict())
        assert errors == []

    def test_confidence_below_minimum_fails(self):
        """Confidence -0.01 is invalid."""
        event_dict = {
            "event_id": generate_event_id(),
            "site_id": "SITE-001",
            "source_id": "pipeline-0",
            "device_id": "CAM-001",
            "event_type": "FALL_DETECTED",
            "timestamp": generate_timestamp(),
            "model_version": "v1.0.0-tao-ds",
            "inference": json.dumps({
                "pgie": {"class_id": 1, "confidence": -0.01, "label": "fall",
                         "bbox": {"x": 0.1, "y": 0.1, "w": 0.2, "h": 0.2}},
                "tracker": {"object_id": 1, "age_frames": 1},
            }),
        }
        errors = validate_ds_event(event_dict)
        assert any("confidence" in e for e in errors)

    def test_confidence_above_maximum_fails(self):
        """Confidence 1.01 is invalid."""
        event_dict = {
            "event_id": generate_event_id(),
            "site_id": "SITE-001",
            "source_id": "pipeline-0",
            "device_id": "CAM-001",
            "event_type": "FALL_DETECTED",
            "timestamp": generate_timestamp(),
            "model_version": "v1.0.0-tao-ds",
            "inference": json.dumps({
                "pgie": {"class_id": 1, "confidence": 1.01, "label": "fall",
                         "bbox": {"x": 0.1, "y": 0.1, "w": 0.2, "h": 0.2}},
                "tracker": {"object_id": 1, "age_frames": 1},
            }),
        }
        errors = validate_ds_event(event_dict)
        assert any("confidence" in e for e in errors)

    def test_bbox_all_zeros_valid_for_device_status(self):
        """Bbox (0,0,0,0) is valid for device status events."""
        event = DeviceStatusEvent(
            event_id=generate_event_id(),
            site_id="SITE-001",
            source_id="pipeline-0",
            device_id="CAM-001",
            event_type="DEVICE_OFFLINE",
            timestamp=generate_timestamp(),
            model_version="v1.0.0-tao-ds",
        )
        event_dict = event.to_redis_dict()
        errors = validate_ds_event(event_dict)
        assert errors == [], f"Device status event should be valid: {errors}"


# ─── Serialization Tests ─────────────────────────────────────────────────────


class TestSerialization:
    """Test Redis serialization/deserialization roundtrip."""

    def test_ds_event_to_redis_dict(self, sample_fall_event):
        """DSEvent serializes to flat dict correctly."""
        d = sample_fall_event.to_redis_dict()
        assert isinstance(d, dict)
        assert d["event_id"] == sample_fall_event.event_id
        assert d["site_id"] == "SITE-001"
        assert d["device_id"] == "CAM-001"
        assert d["event_type"] == "FALL_DETECTED"
        # inference is JSON string
        inference = json.loads(d["inference"])
        assert inference["pgie"]["class_id"] == 1
        assert inference["pgie"]["confidence"] == 0.92

    def test_ds_event_roundtrip(self, sample_fall_event):
        """DSEvent survives Redis serialization roundtrip."""
        redis_dict = sample_fall_event.to_redis_dict()
        restored = DSEvent.from_redis_dict(redis_dict)
        assert restored.event_id == sample_fall_event.event_id
        assert restored.site_id == sample_fall_event.site_id
        assert restored.device_id == sample_fall_event.device_id
        assert restored.event_type == sample_fall_event.event_type
        assert restored.inference.pgie.confidence == 0.92
        assert restored.inference.pgie.bbox.x == 0.35
        assert restored.inference.tracker.object_id == 42

    def test_device_status_event_to_redis_dict(self, sample_device_offline_event):
        """DeviceStatusEvent serializes correctly."""
        d = sample_device_offline_event.to_redis_dict()
        assert d["event_type"] == "DEVICE_OFFLINE"
        assert d["device_id"] == "CAM-002"
        inference = json.loads(d["inference"])
        assert inference["pgie"]["class_id"] == -1
        assert inference["pgie"]["label"] == "device_status"
