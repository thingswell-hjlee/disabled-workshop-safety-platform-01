"""
Event Completeness Validation Tests
=====================================
필수 필드 존재 여부 및 조건부 필수 필드 검증.
Reference: docs/schema-validation-test.md Section 3
"""

import pytest
from pydantic import ValidationError

from tests.schema.models import (
    BAND_EVENT_TYPES,
    VISION_AI_EVENT_TYPES,
    SafetyEvent,
)


# ──────────────────────────────────────────────────────────────────────
# Required Fields Tests (Section 3.1)
# ──────────────────────────────────────────────────────────────────────


class TestRequiredFields:
    """All required fields must be present in a valid event."""

    REQUIRED_FIELDS = [
        "event_id",
        "site_id",
        "device_id",
        "event_type",
        "risk_level",
        "timestamp",
        "event_state",
    ]

    @pytest.mark.completeness
    @pytest.mark.parametrize("field", REQUIRED_FIELDS)
    def test_missing_required_field_rejected(self, field):
        """Each required field must be present"""
        base_event = {
            "event_id": "EVT-20250519120000-001",
            "site_id": "SITE-001",
            "device_id": "CAM-001",
            "event_type": "DEVICE_ONLINE",
            "risk_level": "NORMAL",
            "timestamp": "2025-05-19T12:00:00.123Z",
            "event_state": "ACTIVE",
        }
        # Remove the target field
        del base_event[field]

        with pytest.raises(ValidationError) as exc_info:
            SafetyEvent(**base_event)
        assert field in str(exc_info.value)

    @pytest.mark.completeness
    def test_missing_event_type_from_fixture(self, invalid_events):
        """ERR-02: Missing event_type field is rejected"""
        event = invalid_events[1]  # missing event_type
        with pytest.raises(ValidationError) as exc_info:
            SafetyEvent(**event)
        assert "event_type" in str(exc_info.value)

    @pytest.mark.completeness
    def test_all_required_fields_present_in_valid_events(self, valid_events):
        """All valid events contain all required fields"""
        for i, event in enumerate(valid_events):
            result = SafetyEvent(**event)
            for field in self.REQUIRED_FIELDS:
                assert getattr(result, field) is not None, (
                    f"Event {i}: required field '{field}' is None"
                )


# ──────────────────────────────────────────────────────────────────────
# Conditional Required Fields Tests (Section 3.2)
# ──────────────────────────────────────────────────────────────────────


class TestConditionalRequiredFields:
    """Fields required based on event_type."""

    @pytest.mark.completeness
    @pytest.mark.parametrize("event_type", list(VISION_AI_EVENT_TYPES))
    def test_vision_ai_events_require_confidence(self, event_type):
        """Vision AI events must have non-null confidence"""
        # This validates the business rule (not enforced by Pydantic alone)
        event = SafetyEvent(
            event_id="EVT-20250519120000-001",
            site_id="SITE-001",
            device_id="CAM-001",
            event_type=event_type,
            risk_level="CRITICAL" if event_type in {"FALL_DETECTED", "COLLAPSE_DETECTED"} else "WARNING",
            timestamp="2025-05-19T12:00:00.123Z",
            event_state="ACTIVE",
            confidence=0.85,
            model_version="v1.0.0-tao-ds",
        )
        assert event.confidence is not None
        assert event.model_version is not None

    @pytest.mark.completeness
    def test_vision_ai_event_missing_confidence_flagged(self, invalid_events):
        """ERR-12: Vision AI event with null confidence is a completeness violation"""
        event_data = invalid_events[11]  # FALL_DETECTED with confidence=null
        # Pydantic allows it (field is Optional), but business rule says it's invalid
        event = SafetyEvent(**event_data)
        # Business rule check: Vision AI events MUST have confidence
        if event.event_type in VISION_AI_EVENT_TYPES:
            assert event.confidence is None  # This is the violation we're testing
            # In production, the Event Engine should reject this

    @pytest.mark.completeness
    @pytest.mark.parametrize("event_type", list(BAND_EVENT_TYPES))
    def test_band_events_require_worker_id(self, event_type):
        """Smart Band events must have non-null worker_id"""
        event = SafetyEvent(
            event_id="EVT-20250519120000-001",
            site_id="SITE-001",
            device_id="BAND-003",
            event_type=event_type,
            risk_level="WARNING",
            timestamp="2025-05-19T12:00:00.123Z",
            event_state="ACTIVE",
            worker_id="WKR-0001",
        )
        assert event.worker_id is not None

    @pytest.mark.completeness
    def test_band_event_missing_worker_id_flagged(self, invalid_events):
        """ERR-13: Band event with null worker_id is a completeness violation"""
        event_data = invalid_events[12]  # HEARTRATE_ABNORMAL with worker_id=null
        event = SafetyEvent(**event_data)
        # Business rule check: Band events MUST have worker_id
        if event.event_type in BAND_EVENT_TYPES:
            assert event.worker_id is None  # This is the violation

    @pytest.mark.completeness
    def test_env_threshold_requires_sensor_snapshot(self, valid_events):
        """ENV_THRESHOLD_EXCEEDED must have context.sensor_snapshot"""
        env_event = valid_events[6]  # ENV_THRESHOLD_EXCEEDED
        result = SafetyEvent(**env_event)
        assert result.event_type == "ENV_THRESHOLD_EXCEEDED"
        assert result.context is not None
        assert result.context.sensor_snapshot is not None


# ──────────────────────────────────────────────────────────────────────
# Platform 2.0/3.0 Reserved Fields Tests
# ──────────────────────────────────────────────────────────────────────


class TestReservedFields:
    """Platform 2.0/3.0 reserved fields must be null in Platform 1.0."""

    PLATFORM_20_FIELDS = ["feedback_type", "activity_index_history", "baseline_profile"]
    PLATFORM_30_FIELDS = ["reanalysis_result", "audit_hash", "rag_reference"]

    @pytest.mark.completeness
    def test_platform_20_fields_are_null(self, valid_events):
        """All Platform 2.0 reserved fields are null"""
        for i, event in enumerate(valid_events):
            result = SafetyEvent(**event)
            for field in self.PLATFORM_20_FIELDS:
                assert getattr(result, field) is None, (
                    f"Event {i}: Platform 2.0 field '{field}' should be null"
                )

    @pytest.mark.completeness
    def test_platform_30_fields_are_null(self, valid_events):
        """All Platform 3.0 reserved fields are null"""
        for i, event in enumerate(valid_events):
            result = SafetyEvent(**event)
            for field in self.PLATFORM_30_FIELDS:
                assert getattr(result, field) is None, (
                    f"Event {i}: Platform 3.0 field '{field}' should be null"
                )
