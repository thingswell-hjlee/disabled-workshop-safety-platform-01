"""
Event Boundary Value Tests
===========================
경계값, 범위 초과, 엣지 케이스 검증.
Reference: docs/schema-validation-test.md Section 5
"""

import pytest
from pydantic import ValidationError

from tests.schema.models import SafetyEvent


# ──────────────────────────────────────────────────────────────────────
# Confidence Boundary Tests (Section 5.3)
# ──────────────────────────────────────────────────────────────────────


class TestConfidenceBoundary:
    """Confidence value boundary tests (0.0~1.0)"""

    BASE_EVENT = {
        "event_id": "EVT-20250519120000-001",
        "site_id": "SITE-001",
        "device_id": "CAM-001",
        "event_type": "FALL_DETECTED",
        "risk_level": "CRITICAL",
        "timestamp": "2025-05-19T12:00:00.123Z",
        "event_state": "ACTIVE",
        "model_version": "v1.0.0-tao-ds",
    }

    @pytest.mark.boundary
    @pytest.mark.parametrize(
        "value,description",
        [
            (0.0, "Minimum valid"),
            (1.0, "Maximum valid"),
            (0.5, "Mid-range"),
            (0.001, "Near-zero"),
            (0.999, "Near-one"),
            (0.999999, "High precision"),
        ],
    )
    def test_valid_confidence_boundary(self, value, description):
        """Valid confidence boundary values pass"""
        event = SafetyEvent(**{**self.BASE_EVENT, "confidence": value})
        assert event.confidence == value

    @pytest.mark.boundary
    @pytest.mark.parametrize(
        "value,description",
        [
            (-0.01, "Below minimum"),
            (1.01, "Above maximum"),
            (-1.0, "Negative"),
            (2.0, "Double maximum"),
            (100.0, "Way above maximum"),
        ],
    )
    def test_invalid_confidence_boundary(self, value, description):
        """Invalid confidence boundary values are rejected"""
        with pytest.raises(ValidationError):
            SafetyEvent(**{**self.BASE_EVENT, "confidence": value})


# ──────────────────────────────────────────────────────────────────────
# Null vs Missing Field Tests
# ──────────────────────────────────────────────────────────────────────


class TestNullHandling:
    """Null value handling for optional fields"""

    BASE_EVENT = {
        "event_id": "EVT-20250519120000-001",
        "site_id": "SITE-001",
        "device_id": "CAM-001",
        "event_type": "DEVICE_ONLINE",
        "risk_level": "NORMAL",
        "timestamp": "2025-05-19T12:00:00.123Z",
        "event_state": "ACTIVE",
    }

    @pytest.mark.boundary
    def test_null_optional_fields_accepted(self):
        """Null values for optional fields are accepted"""
        event = SafetyEvent(
            **self.BASE_EVENT,
            worker_id=None,
            confidence=None,
            model_version=None,
            context=None,
        )
        assert event.worker_id is None
        assert event.confidence is None
        assert event.model_version is None
        assert event.context is None

    @pytest.mark.boundary
    def test_missing_optional_fields_default_to_none(self):
        """Missing optional fields default to None"""
        event = SafetyEvent(**self.BASE_EVENT)
        assert event.worker_id is None
        assert event.confidence is None
        assert event.model_version is None

    @pytest.mark.boundary
    def test_null_required_field_rejected(self):
        """Null value for required field is rejected"""
        with pytest.raises(ValidationError):
            SafetyEvent(
                event_id=None,
                site_id="SITE-001",
                device_id="CAM-001",
                event_type="DEVICE_ONLINE",
                risk_level="NORMAL",
                timestamp="2025-05-19T12:00:00.123Z",
                event_state="ACTIVE",
            )


# ──────────────────────────────────────────────────────────────────────
# Event ID Sequence Boundary
# ──────────────────────────────────────────────────────────────────────


class TestEventIdSequenceBoundary:
    """event_id sequence number boundary tests"""

    @pytest.mark.boundary
    @pytest.mark.parametrize(
        "seq,expected_valid",
        [
            ("001", True),
            ("999", True),
            ("000", True),
            ("01", False),
            ("0001", False),
            ("1", False),
        ],
    )
    def test_sequence_number_boundary(self, seq, expected_valid):
        """Sequence number must be exactly 3 digits"""
        event_id = f"EVT-20250519120000-{seq}"
        if expected_valid:
            event = SafetyEvent(
                event_id=event_id,
                site_id="SITE-001",
                device_id="CAM-001",
                event_type="DEVICE_ONLINE",
                risk_level="NORMAL",
                timestamp="2025-05-19T12:00:00.123Z",
                event_state="ACTIVE",
            )
            assert event.event_id == event_id
        else:
            with pytest.raises(ValidationError):
                SafetyEvent(
                    event_id=event_id,
                    site_id="SITE-001",
                    device_id="CAM-001",
                    event_type="DEVICE_ONLINE",
                    risk_level="NORMAL",
                    timestamp="2025-05-19T12:00:00.123Z",
                    event_state="ACTIVE",
                )


# ──────────────────────────────────────────────────────────────────────
# Type Coercion Tests
# ──────────────────────────────────────────────────────────────────────


class TestTypeCoercion:
    """Ensure strict type checking (no silent coercion)"""

    @pytest.mark.boundary
    def test_integer_confidence_coerced(self):
        """Integer 1 is coerced to float 1.0 for confidence"""
        event = SafetyEvent(
            event_id="EVT-20250519120000-001",
            site_id="SITE-001",
            device_id="CAM-001",
            event_type="FALL_DETECTED",
            risk_level="CRITICAL",
            timestamp="2025-05-19T12:00:00.123Z",
            event_state="ACTIVE",
            confidence=1,
            model_version="v1.0.0-tao-ds",
        )
        assert event.confidence == 1.0

    @pytest.mark.boundary
    def test_string_confidence_rejected(self):
        """String value for confidence is rejected"""
        with pytest.raises(ValidationError):
            SafetyEvent(
                event_id="EVT-20250519120000-001",
                site_id="SITE-001",
                device_id="CAM-001",
                event_type="FALL_DETECTED",
                risk_level="CRITICAL",
                timestamp="2025-05-19T12:00:00.123Z",
                event_state="ACTIVE",
                confidence="high",
                model_version="v1.0.0-tao-ds",
            )


# ──────────────────────────────────────────────────────────────────────
# Maximum Field Length Tests
# ──────────────────────────────────────────────────────────────────────


class TestFieldLengthBoundary:
    """Edge cases for field length and content"""

    @pytest.mark.boundary
    def test_event_id_exact_length(self):
        """event_id must be exactly 24 characters (EVT-YYYYMMDDHHmmss-NNN)"""
        valid_id = "EVT-20250519120000-001"
        assert len(valid_id) == 22  # EVT- (4) + 14 digits + - (1) + 3 digits = 22
        event = SafetyEvent(
            event_id=valid_id,
            site_id="SITE-001",
            device_id="CAM-001",
            event_type="DEVICE_ONLINE",
            risk_level="NORMAL",
            timestamp="2025-05-19T12:00:00.123Z",
            event_state="ACTIVE",
        )
        assert len(event.event_id) == 22

    @pytest.mark.boundary
    def test_site_id_exact_length(self):
        """site_id must be exactly 8 characters (SITE-NNN)"""
        valid_id = "SITE-001"
        assert len(valid_id) == 8
        event = SafetyEvent(
            event_id="EVT-20250519120000-001",
            site_id=valid_id,
            device_id="CAM-001",
            event_type="DEVICE_ONLINE",
            risk_level="NORMAL",
            timestamp="2025-05-19T12:00:00.123Z",
            event_state="ACTIVE",
        )
        assert len(event.site_id) == 8
