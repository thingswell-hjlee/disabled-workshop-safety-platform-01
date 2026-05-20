"""
Event Format Validation Tests
==============================
ID 형식, 타임스탬프 형식, enum 값 검증 테스트.
Reference: docs/schema-validation-test.md Section 2
"""

import pytest
from pydantic import ValidationError

from tests.schema.models import (
    PATTERN_DEVICE_ID,
    PATTERN_EVENT_ID,
    PATTERN_MODEL_VERSION,
    PATTERN_SITE_ID,
    PATTERN_TIMESTAMP,
    PATTERN_WORKER_ID,
    SafetyEvent,
)


# ──────────────────────────────────────────────────────────────────────
# event_id Format Tests (Section 5.1)
# ──────────────────────────────────────────────────────────────────────


class TestEventIdFormat:
    """event_id format validation: ^EVT-\\d{14}-\\d{3}$"""

    @pytest.mark.format
    def test_valid_event_id(self, valid_events):
        """TC-01: Valid event_id passes validation"""
        event = valid_events[0]
        result = SafetyEvent(**event)
        assert result.event_id == "EVT-20250519120000-001"

    @pytest.mark.format
    @pytest.mark.parametrize(
        "invalid_id,description",
        [
            ("20250519120000-001", "Missing EVT- prefix"),
            ("EVT_20250519120000_001", "Wrong separator (underscore)"),
            ("EVT-2025051912-001", "Short timestamp (10 digits)"),
            ("EVT-20250519120000-01", "Short sequence (2 digits)"),
            ("EVT-20250519120000-0001", "Long sequence (4 digits)"),
            ("EVT-2025051912000A-001", "Non-numeric in timestamp"),
            ("", "Empty string"),
            ("EVT-20250519120000", "Missing sequence"),
        ],
    )
    def test_invalid_event_id(self, invalid_id, description):
        """Boundary: Invalid event_id formats are rejected"""
        with pytest.raises(ValidationError) as exc_info:
            SafetyEvent(
                event_id=invalid_id,
                site_id="SITE-001",
                device_id="CAM-001",
                event_type="DEVICE_OFFLINE",
                risk_level="NORMAL",
                timestamp="2025-05-19T12:00:00.123Z",
                event_state="ACTIVE",
            )
        assert "event_id" in str(exc_info.value)


# ──────────────────────────────────────────────────────────────────────
# device_id Format Tests (Section 5.2)
# ──────────────────────────────────────────────────────────────────────


class TestDeviceIdFormat:
    """device_id format validation: ^(CAM|BAND|ENV|FIRE|NVR|ALARM)-\\d{3}$"""

    @pytest.mark.format
    @pytest.mark.parametrize(
        "valid_id",
        ["CAM-001", "BAND-012", "ENV-003", "FIRE-001", "NVR-001", "ALARM-001"],
    )
    def test_valid_device_ids(self, valid_id):
        """Valid device_id with all supported prefixes"""
        result = SafetyEvent(
            event_id="EVT-20250519120000-001",
            site_id="SITE-001",
            device_id=valid_id,
            event_type="DEVICE_ONLINE",
            risk_level="NORMAL",
            timestamp="2025-05-19T12:00:00.123Z",
            event_state="ACTIVE",
        )
        assert result.device_id == valid_id

    @pytest.mark.format
    @pytest.mark.parametrize(
        "invalid_id,description",
        [
            ("CAMERA-001", "Invalid prefix CAMERA"),
            ("CAM-01", "Short number (2 digits)"),
            ("CAM-0001", "Long number (4 digits)"),
            ("cam-001", "Lowercase prefix"),
            ("001", "No prefix"),
            ("CAM--001", "Extra dash"),
            ("SENSOR-001", "Invalid prefix SENSOR"),
        ],
    )
    def test_invalid_device_ids(self, invalid_id, description):
        """Boundary: Invalid device_id formats are rejected"""
        with pytest.raises(ValidationError) as exc_info:
            SafetyEvent(
                event_id="EVT-20250519120000-001",
                site_id="SITE-001",
                device_id=invalid_id,
                event_type="DEVICE_OFFLINE",
                risk_level="NORMAL",
                timestamp="2025-05-19T12:00:00.123Z",
                event_state="ACTIVE",
            )
        assert "device_id" in str(exc_info.value)


# ──────────────────────────────────────────────────────────────────────
# site_id Format Tests
# ──────────────────────────────────────────────────────────────────────


class TestSiteIdFormat:
    """site_id format validation: ^SITE-\\d{3}$"""

    @pytest.mark.format
    def test_valid_site_id(self):
        """Valid site_id"""
        result = SafetyEvent(
            event_id="EVT-20250519120000-001",
            site_id="SITE-001",
            device_id="CAM-001",
            event_type="DEVICE_ONLINE",
            risk_level="NORMAL",
            timestamp="2025-05-19T12:00:00.123Z",
            event_state="ACTIVE",
        )
        assert result.site_id == "SITE-001"

    @pytest.mark.format
    @pytest.mark.parametrize(
        "invalid_id",
        ["SITE-01", "SITE-1000", "site-001", "LOCATION-001", ""],
    )
    def test_invalid_site_ids(self, invalid_id):
        """Boundary: Invalid site_id formats are rejected"""
        with pytest.raises(ValidationError):
            SafetyEvent(
                event_id="EVT-20250519120000-001",
                site_id=invalid_id,
                device_id="CAM-001",
                event_type="DEVICE_ONLINE",
                risk_level="NORMAL",
                timestamp="2025-05-19T12:00:00.123Z",
                event_state="ACTIVE",
            )


# ──────────────────────────────────────────────────────────────────────
# Timestamp Format Tests (Section 5.4)
# ──────────────────────────────────────────────────────────────────────


class TestTimestampFormat:
    """Timestamp validation: ISO 8601 UTC with milliseconds"""

    @pytest.mark.format
    def test_valid_timestamp(self):
        """Valid UTC timestamp with milliseconds"""
        result = SafetyEvent(
            event_id="EVT-20250519120000-001",
            site_id="SITE-001",
            device_id="CAM-001",
            event_type="DEVICE_ONLINE",
            risk_level="NORMAL",
            timestamp="2025-05-19T12:00:00.123Z",
            event_state="ACTIVE",
        )
        assert result.timestamp == "2025-05-19T12:00:00.123Z"

    @pytest.mark.format
    @pytest.mark.parametrize(
        "invalid_ts,description",
        [
            ("2025-05-19T12:00:00Z", "No milliseconds"),
            ("2025-05-19T12:00:00.123+09:00", "Non-UTC timezone"),
            ("2025-13-45T99:99:99.999Z", "Invalid date values"),
            ("", "Empty string"),
            ("2025-05-19 12:00:00.123", "Missing T and Z"),
            ("not-a-timestamp", "Random string"),
        ],
    )
    def test_invalid_timestamps(self, invalid_ts, description):
        """Boundary: Invalid timestamp formats are rejected"""
        with pytest.raises(ValidationError):
            SafetyEvent(
                event_id="EVT-20250519120000-001",
                site_id="SITE-001",
                device_id="CAM-001",
                event_type="DEVICE_ONLINE",
                risk_level="NORMAL",
                timestamp=invalid_ts,
                event_state="ACTIVE",
            )


# ──────────────────────────────────────────────────────────────────────
# model_version Format Tests
# ──────────────────────────────────────────────────────────────────────


class TestModelVersionFormat:
    """model_version format: ^v\\d+\\.\\d+\\.\\d+-(tao|pretrained|custom)-(ds|cloud)$"""

    @pytest.mark.format
    @pytest.mark.parametrize(
        "valid_version",
        [
            "v1.0.0-tao-ds",
            "v1.0.0-pretrained-ds",
            "v2.1.0-custom-cloud",
            "v10.20.30-tao-cloud",
        ],
    )
    def test_valid_model_versions(self, valid_version):
        """Valid model_version formats"""
        result = SafetyEvent(
            event_id="EVT-20250519120000-001",
            site_id="SITE-001",
            device_id="CAM-001",
            event_type="FALL_DETECTED",
            risk_level="CRITICAL",
            timestamp="2025-05-19T12:00:00.123Z",
            event_state="ACTIVE",
            confidence=0.9,
            model_version=valid_version,
        )
        assert result.model_version == valid_version

    @pytest.mark.format
    @pytest.mark.parametrize(
        "invalid_version,description",
        [
            ("1.0.0-tao-ds", "Missing v prefix"),
            ("v1.0-tao-ds", "Missing patch version"),
            ("v1.0.0-pytorch-ds", "Invalid tool name"),
            ("v1.0.0-tao-edge", "Invalid target name"),
            ("v1.0.0-tao", "Missing target"),
            ("", "Empty string"),
        ],
    )
    def test_invalid_model_versions(self, invalid_version, description):
        """Boundary: Invalid model_version formats are rejected"""
        with pytest.raises(ValidationError):
            SafetyEvent(
                event_id="EVT-20250519120000-001",
                site_id="SITE-001",
                device_id="CAM-001",
                event_type="FALL_DETECTED",
                risk_level="CRITICAL",
                timestamp="2025-05-19T12:00:00.123Z",
                event_state="ACTIVE",
                confidence=0.9,
                model_version=invalid_version,
            )


# ──────────────────────────────────────────────────────────────────────
# worker_id Format Tests
# ──────────────────────────────────────────────────────────────────────


class TestWorkerIdFormat:
    """worker_id format: ^WKR-\\d{4}$"""

    @pytest.mark.format
    def test_valid_worker_id(self):
        """Valid worker_id"""
        result = SafetyEvent(
            event_id="EVT-20250519120000-001",
            site_id="SITE-001",
            device_id="BAND-003",
            event_type="HEARTRATE_ABNORMAL",
            risk_level="WARNING",
            timestamp="2025-05-19T12:00:00.123Z",
            event_state="ACTIVE",
            worker_id="WKR-0012",
        )
        assert result.worker_id == "WKR-0012"

    @pytest.mark.format
    @pytest.mark.parametrize(
        "invalid_id",
        ["WKR-001", "WKR-00001", "WORKER-0001", "wkr-0001", ""],
    )
    def test_invalid_worker_ids(self, invalid_id):
        """Boundary: Invalid worker_id formats are rejected"""
        with pytest.raises(ValidationError):
            SafetyEvent(
                event_id="EVT-20250519120000-001",
                site_id="SITE-001",
                device_id="BAND-003",
                event_type="HEARTRATE_ABNORMAL",
                risk_level="WARNING",
                timestamp="2025-05-19T12:00:00.123Z",
                event_state="ACTIVE",
                worker_id=invalid_id,
            )


# ──────────────────────────────────────────────────────────────────────
# Enum Validation Tests (Section 2.3)
# ──────────────────────────────────────────────────────────────────────


class TestEnumValidation:
    """Enum value validation for event_type, risk_level, event_state"""

    @pytest.mark.format
    def test_invalid_event_type(self, invalid_events):
        """ERR-01: Invalid event_type is rejected"""
        event = invalid_events[0]  # UNKNOWN_EVENT
        with pytest.raises(ValidationError) as exc_info:
            SafetyEvent(**event)
        assert "event_type" in str(exc_info.value)

    @pytest.mark.format
    def test_invalid_risk_level(self, invalid_events):
        """ERR-03: Invalid risk_level is rejected"""
        event = invalid_events[2]  # risk_level: HIGH
        with pytest.raises(ValidationError) as exc_info:
            SafetyEvent(**event)
        assert "risk_level" in str(exc_info.value)

    @pytest.mark.format
    def test_invalid_event_state(self):
        """Invalid event_state is rejected"""
        with pytest.raises(ValidationError):
            SafetyEvent(
                event_id="EVT-20250519120000-001",
                site_id="SITE-001",
                device_id="CAM-001",
                event_type="DEVICE_ONLINE",
                risk_level="NORMAL",
                timestamp="2025-05-19T12:00:00.123Z",
                event_state="PENDING",
            )

    @pytest.mark.format
    def test_all_valid_event_types_accepted(self, valid_events):
        """All 10 valid event fixtures pass validation"""
        for i, event in enumerate(valid_events):
            result = SafetyEvent(**event)
            assert result.event_id is not None, f"Event {i} failed validation"
