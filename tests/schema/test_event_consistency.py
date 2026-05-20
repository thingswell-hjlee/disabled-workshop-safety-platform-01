"""
Event Consistency Validation Tests
====================================
필드 간 논리적 정합성 검증 (C-001 ~ C-009).
Reference: docs/schema-validation-test.md Section 4
"""

import pytest

from tests.schema.models import (
    CRITICAL_EVENT_TYPES,
    RISK_TO_PRIORITY,
    VALID_EVENT_TYPES,
    CloudQueueMessage,
    SafetyEvent,
)


# ──────────────────────────────────────────────────────────────────────
# Consistency Rule Validators (Business Logic)
# ──────────────────────────────────────────────────────────────────────


def check_c001_risk_matches_event(event: SafetyEvent) -> bool:
    """C-001: FALL_DETECTED, COLLAPSE_DETECTED, FIRE_DETECTED → must be CRITICAL"""
    if event.event_type in CRITICAL_EVENT_TYPES:
        return event.risk_level == "CRITICAL"
    return True


def check_c002_device_prefix_matches_type(event: SafetyEvent) -> bool:
    """C-002: device_id prefix must match implied device_type"""
    prefix = event.device_id.split("-")[0]
    # BAND events should come from BAND devices
    band_events = {"HEARTRATE_ABNORMAL", "TEMPERATURE_ABNORMAL", "BAND_FALL_DETECTED", "BAND_DISCONNECTED"}
    if event.event_type in band_events:
        return prefix == "BAND"
    # ENV events from ENV devices
    if event.event_type == "ENV_THRESHOLD_EXCEEDED":
        return prefix == "ENV"
    # FIRE from FIRE or CAM
    if event.event_type == "FIRE_DETECTED":
        return prefix in {"FIRE", "CAM"}
    return True


def check_c003_idempotency_key(site_id: str, event_id: str, idempotency_key: str) -> bool:
    """C-003: idempotency_key must equal {site_id}:{event_id}"""
    return idempotency_key == f"{site_id}:{event_id}"


def check_c004_priority_matches_risk(risk_level: str, priority: str) -> bool:
    """C-004: Priority must match risk_level mapping"""
    expected = RISK_TO_PRIORITY.get(risk_level)
    return priority == expected


def check_c005_initial_event_state(event: SafetyEvent) -> bool:
    """C-005: New events must start as ACTIVE"""
    return event.event_state == "ACTIVE"


def check_c006_confidence_range(event: SafetyEvent) -> bool:
    """C-006: confidence must be 0.0 <= confidence <= 1.0"""
    if event.confidence is not None:
        return 0.0 <= event.confidence <= 1.0
    return True


# ──────────────────────────────────────────────────────────────────────
# Test Class: C-001 risk_level matches event_type
# ──────────────────────────────────────────────────────────────────────


class TestConsistencyC001:
    """C-001: FALL_DETECTED, COLLAPSE_DETECTED, FIRE_DETECTED → CRITICAL"""

    @pytest.mark.consistency
    @pytest.mark.parametrize(
        "event_type",
        ["FALL_DETECTED", "COLLAPSE_DETECTED", "FIRE_DETECTED"],
    )
    def test_critical_events_have_critical_risk(self, event_type):
        """Critical event types must have CRITICAL risk_level"""
        event = SafetyEvent(
            event_id="EVT-20250519120000-001",
            site_id="SITE-001",
            device_id="CAM-001" if event_type != "FIRE_DETECTED" else "FIRE-001",
            event_type=event_type,
            risk_level="CRITICAL",
            timestamp="2025-05-19T12:00:00.123Z",
            event_state="ACTIVE",
            confidence=0.9 if event_type != "FIRE_DETECTED" else None,
            model_version="v1.0.0-tao-ds" if event_type != "FIRE_DETECTED" else None,
        )
        assert check_c001_risk_matches_event(event) is True

    @pytest.mark.consistency
    def test_fall_detected_with_normal_risk_fails_c001(self, invalid_events):
        """ERR-11: FALL_DETECTED with NORMAL risk_level violates C-001"""
        event_data = invalid_events[10]  # FALL_DETECTED with risk_level=NORMAL
        # Pydantic accepts it (both are valid enums individually)
        event = SafetyEvent(**event_data)
        # But C-001 consistency check fails
        assert check_c001_risk_matches_event(event) is False


# ──────────────────────────────────────────────────────────────────────
# Test Class: C-002 device_id prefix matches device_type
# ──────────────────────────────────────────────────────────────────────


class TestConsistencyC002:
    """C-002: device_id prefix must match event source type"""

    @pytest.mark.consistency
    def test_band_event_from_band_device(self):
        """Band events should come from BAND-xxx devices"""
        event = SafetyEvent(
            event_id="EVT-20250519120000-001",
            site_id="SITE-001",
            device_id="BAND-003",
            event_type="HEARTRATE_ABNORMAL",
            risk_level="WARNING",
            timestamp="2025-05-19T12:00:00.123Z",
            event_state="ACTIVE",
            worker_id="WKR-0001",
        )
        assert check_c002_device_prefix_matches_type(event) is True

    @pytest.mark.consistency
    def test_band_event_from_cam_device_fails_c002(self):
        """Band event from CAM device violates C-002"""
        event = SafetyEvent(
            event_id="EVT-20250519120000-001",
            site_id="SITE-001",
            device_id="CAM-001",
            event_type="HEARTRATE_ABNORMAL",
            risk_level="WARNING",
            timestamp="2025-05-19T12:00:00.123Z",
            event_state="ACTIVE",
            worker_id="WKR-0001",
        )
        assert check_c002_device_prefix_matches_type(event) is False

    @pytest.mark.consistency
    def test_env_event_from_env_device(self):
        """ENV_THRESHOLD_EXCEEDED should come from ENV-xxx device"""
        event = SafetyEvent(
            event_id="EVT-20250519120000-001",
            site_id="SITE-001",
            device_id="ENV-002",
            event_type="ENV_THRESHOLD_EXCEEDED",
            risk_level="WARNING",
            timestamp="2025-05-19T12:00:00.123Z",
            event_state="ACTIVE",
        )
        assert check_c002_device_prefix_matches_type(event) is True

    @pytest.mark.consistency
    def test_valid_events_pass_c002(self, valid_events):
        """All valid event fixtures pass C-002"""
        for i, event_data in enumerate(valid_events):
            event = SafetyEvent(**event_data)
            assert check_c002_device_prefix_matches_type(event) is True, (
                f"Event {i} ({event.event_type}) failed C-002"
            )


# ──────────────────────────────────────────────────────────────────────
# Test Class: C-003 idempotency_key format
# ──────────────────────────────────────────────────────────────────────


class TestConsistencyC003:
    """C-003: idempotency_key must equal {site_id}:{event_id}"""

    @pytest.mark.consistency
    def test_valid_idempotency_key(self):
        """Correct idempotency_key format"""
        assert check_c003_idempotency_key(
            "SITE-001", "EVT-20250519120000-001", "SITE-001:EVT-20250519120000-001"
        ) is True

    @pytest.mark.consistency
    def test_invalid_idempotency_key(self):
        """Wrong idempotency_key format"""
        assert check_c003_idempotency_key(
            "SITE-001", "EVT-20250519120000-001", "EVT-20250519120000-001"
        ) is False

    @pytest.mark.consistency
    def test_cloud_queue_fixture_has_valid_idempotency(self, redis_stream_messages):
        """Cloud queue fixture has correct idempotency_key"""
        msg = redis_stream_messages["stream:cloud-queue"][0]
        assert check_c003_idempotency_key(
            msg["site_id"], msg["event_id"], msg["idempotency_key"]
        ) is True


# ──────────────────────────────────────────────────────────────────────
# Test Class: C-004 priority matches risk_level
# ──────────────────────────────────────────────────────────────────────


class TestConsistencyC004:
    """C-004: priority must match risk_level (CRITICAL→HIGH, WARNING→NORMAL, NORMAL→LOW)"""

    @pytest.mark.consistency
    @pytest.mark.parametrize(
        "risk_level,expected_priority",
        [("CRITICAL", "HIGH"), ("WARNING", "NORMAL"), ("NORMAL", "LOW")],
    )
    def test_priority_mapping(self, risk_level, expected_priority):
        """Priority correctly maps from risk_level"""
        assert check_c004_priority_matches_risk(risk_level, expected_priority) is True

    @pytest.mark.consistency
    def test_critical_with_low_priority_fails(self):
        """CRITICAL risk with LOW priority violates C-004"""
        assert check_c004_priority_matches_risk("CRITICAL", "LOW") is False

    @pytest.mark.consistency
    def test_cloud_queue_fixture_priority(self, redis_stream_messages):
        """Cloud queue fixture has correct priority mapping"""
        msg = redis_stream_messages["stream:cloud-queue"][0]
        assert check_c004_priority_matches_risk(
            msg["risk_level"], msg["priority"]
        ) is True


# ──────────────────────────────────────────────────────────────────────
# Test Class: C-005 event_state initial value
# ──────────────────────────────────────────────────────────────────────


class TestConsistencyC005:
    """C-005: New events must start as ACTIVE"""

    @pytest.mark.consistency
    def test_all_valid_events_start_active(self, valid_events):
        """All fixture events have event_state=ACTIVE"""
        for i, event_data in enumerate(valid_events):
            event = SafetyEvent(**event_data)
            assert check_c005_initial_event_state(event) is True, (
                f"Event {i} does not start as ACTIVE"
            )


# ──────────────────────────────────────────────────────────────────────
# Test Class: C-006 confidence range
# ──────────────────────────────────────────────────────────────────────


class TestConsistencyC006:
    """C-006: 0.0 ≤ confidence ≤ 1.0"""

    @pytest.mark.consistency
    @pytest.mark.boundary
    @pytest.mark.parametrize(
        "confidence",
        [0.0, 0.5, 1.0, 0.001, 0.999],
    )
    def test_valid_confidence_values(self, confidence):
        """Valid confidence values pass"""
        event = SafetyEvent(
            event_id="EVT-20250519120000-001",
            site_id="SITE-001",
            device_id="CAM-001",
            event_type="FALL_DETECTED",
            risk_level="CRITICAL",
            timestamp="2025-05-19T12:00:00.123Z",
            event_state="ACTIVE",
            confidence=confidence,
            model_version="v1.0.0-tao-ds",
        )
        assert check_c006_confidence_range(event) is True

    @pytest.mark.consistency
    @pytest.mark.boundary
    def test_confidence_above_1_rejected(self, invalid_events):
        """ERR-09: Confidence > 1.0 is rejected by Pydantic"""
        from pydantic import ValidationError

        event_data = invalid_events[8]  # confidence: 1.5
        with pytest.raises(ValidationError):
            SafetyEvent(**event_data)

    @pytest.mark.consistency
    @pytest.mark.boundary
    def test_confidence_below_0_rejected(self):
        """Confidence < 0.0 is rejected"""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            SafetyEvent(
                event_id="EVT-20250519120000-001",
                site_id="SITE-001",
                device_id="CAM-001",
                event_type="FALL_DETECTED",
                risk_level="CRITICAL",
                timestamp="2025-05-19T12:00:00.123Z",
                event_state="ACTIVE",
                confidence=-0.01,
                model_version="v1.0.0-tao-ds",
            )
