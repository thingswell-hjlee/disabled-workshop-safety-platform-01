"""SDK Common - ID Generation Tests"""
import pytest
from src.ids import (
    generate_event_id, generate_maint_id,
    validate_device_id, validate_site_id,
    validate_worker_id, validate_event_id,
)


class TestGenerateEventId:
    def test_format(self):
        event_id = generate_event_id()
        assert event_id.startswith("EVT-")
        assert len(event_id) == 22  # EVT-YYYYMMDDHHmmss-NNN

    def test_uniqueness(self):
        ids = {generate_event_id() for _ in range(100)}
        assert len(ids) == 100

    def test_validates_own_output(self):
        event_id = generate_event_id()
        assert validate_event_id(event_id)


class TestGenerateMaintId:
    def test_format(self):
        maint_id = generate_maint_id()
        assert maint_id.startswith("MAINT-")
        parts = maint_id.split("-")
        assert len(parts) == 3


class TestValidateDeviceId:
    @pytest.mark.parametrize("device_id,expected", [
        ("CAM-001", True),
        ("BAND-008", True),
        ("ENV-002", True),
        ("FIRE-001", True),
        ("NVR-001", True),
        ("ALARM-001", True),
        ("CAM-1", False),
        ("INVALID-001", False),
        ("CAM001", False),
        ("", False),
    ])
    def test_validation(self, device_id, expected):
        assert validate_device_id(device_id) == expected


class TestValidateSiteId:
    @pytest.mark.parametrize("site_id,expected", [
        ("SITE-001", True),
        ("SITE-999", True),
        ("SITE-1", False),
        ("site-001", False),
        ("", False),
    ])
    def test_validation(self, site_id, expected):
        assert validate_site_id(site_id) == expected


class TestValidateWorkerId:
    @pytest.mark.parametrize("worker_id,expected", [
        ("WKR-0001", True),
        ("WKR-9999", True),
        ("WKR-001", False),
        ("WRK-0001", False),
        ("", False),
    ])
    def test_validation(self, worker_id, expected):
        assert validate_worker_id(worker_id) == expected
