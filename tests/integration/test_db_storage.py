"""
PostgreSQL Storage Integration Tests
======================================
이벤트의 PostgreSQL 저장 및 조회 검증.
실제 PostgreSQL 없이도 mock으로 테스트 가능.

Reference: docs/event-message-schema.md
"""

import pytest

from tests.integration.mock_aws_receiver import MockAwsReceiver


# ──────────────────────────────────────────────────────────────────────
# In-Memory Storage Tests (PostgreSQL 없이 실행 가능)
# ──────────────────────────────────────────────────────────────────────


class TestInMemoryStorage:
    """In-memory event storage (no PostgreSQL required)"""

    @pytest.mark.integration
    def test_store_event_in_memory(self, fakeredis_client):
        """Event can be stored in-memory"""
        receiver = MockAwsReceiver(fakeredis_client, pg_connection=None)

        mqtt_payload = {
            "event_id": "EVT-20250519120000-001",
            "site_id": "SITE-001",
            "device_id": "CAM-001",
            "worker_id": None,
            "event_type": "FALL_DETECTED",
            "risk_level": "CRITICAL",
            "confidence": 0.92,
            "model_version": "v1.0.0-tao-ds",
            "timestamp": "2025-05-19T12:00:00.123Z",
            "context_summary": "낙상 감지",
            "clip_s3_key": None,
            "idempotency_key": "SITE-001:EVT-20250519120000-001",
        }

        success = receiver.store_event(mqtt_payload)
        assert success is True

    @pytest.mark.integration
    def test_count_stored_events(self, fakeredis_client):
        """Event count tracking works"""
        receiver = MockAwsReceiver(fakeredis_client, pg_connection=None)
        receiver.received_events.append({"event_id": "EVT-20250519120000-001"})
        receiver.received_events.append({"event_id": "EVT-20250519120000-002"})

        assert receiver.get_stored_events_count() == 2

    @pytest.mark.integration
    def test_duplicate_detection_in_memory(self, fakeredis_client):
        """Duplicate event detection works in-memory"""
        receiver = MockAwsReceiver(fakeredis_client, pg_connection=None)

        # First event
        receiver.received_events.append({"event_id": "EVT-20250519120000-001"})

        # Second (new) event
        receiver.received_events.append({"event_id": "EVT-20250519120000-002"})

        # Check: first event already received before the second
        assert receiver.check_duplicate("EVT-20250519120000-001") is True


# ──────────────────────────────────────────────────────────────────────
# PostgreSQL Storage Tests (requires docker-compose)
# ──────────────────────────────────────────────────────────────────────


class TestPostgresStorage:
    """PostgreSQL event storage (requires running PostgreSQL)"""

    @pytest.mark.integration
    def test_store_event_to_postgres(self, fakeredis_client, pg_connection):
        """Event is stored to PostgreSQL"""
        receiver = MockAwsReceiver(fakeredis_client, pg_connection=pg_connection)

        mqtt_payload = {
            "event_id": "EVT-20250519120000-001",
            "site_id": "SITE-001",
            "device_id": "CAM-001",
            "worker_id": None,
            "event_type": "FALL_DETECTED",
            "risk_level": "CRITICAL",
            "confidence": 0.92,
            "model_version": "v1.0.0-tao-ds",
            "timestamp": "2025-05-19T12:00:00.123Z",
            "context_summary": "낙상 감지",
            "clip_s3_key": None,
            "idempotency_key": "SITE-001:EVT-20250519120000-001",
        }

        success = receiver.store_event(mqtt_payload)
        assert success is True

        # Verify count
        count = receiver.get_stored_events_count()
        assert count == 1

    @pytest.mark.integration
    def test_duplicate_rejected_by_postgres(self, fakeredis_client, pg_connection):
        """Duplicate event_id is rejected by unique constraint"""
        receiver = MockAwsReceiver(fakeredis_client, pg_connection=pg_connection)

        mqtt_payload = {
            "event_id": "EVT-20250519120000-001",
            "site_id": "SITE-001",
            "device_id": "CAM-001",
            "worker_id": None,
            "event_type": "FALL_DETECTED",
            "risk_level": "CRITICAL",
            "confidence": 0.92,
            "model_version": "v1.0.0-tao-ds",
            "timestamp": "2025-05-19T12:00:00.123Z",
            "context_summary": "낙상 감지",
            "clip_s3_key": None,
            "idempotency_key": "SITE-001:EVT-20250519120000-001",
        }

        # First insert
        success1 = receiver.store_event(mqtt_payload)
        assert success1 is True

        # Duplicate insert (ON CONFLICT DO NOTHING → returns None)
        success2 = receiver.store_event(mqtt_payload)
        assert success2 is False

        # Still only 1 event
        count = receiver.get_stored_events_count()
        assert count == 1

    @pytest.mark.integration
    def test_multiple_events_stored(self, fakeredis_client, pg_connection):
        """Multiple different events are all stored"""
        receiver = MockAwsReceiver(fakeredis_client, pg_connection=pg_connection)

        event_types = [
            ("EVT-20250519120000-001", "FALL_DETECTED", "CRITICAL"),
            ("EVT-20250519120100-002", "STILLNESS_DETECTED", "WARNING"),
            ("EVT-20250519120200-003", "DEVICE_OFFLINE", "NORMAL"),
        ]

        for event_id, event_type, risk_level in event_types:
            payload = {
                "event_id": event_id,
                "site_id": "SITE-001",
                "device_id": "CAM-001",
                "worker_id": None,
                "event_type": event_type,
                "risk_level": risk_level,
                "confidence": None,
                "model_version": None,
                "timestamp": "2025-05-19T12:00:00.123Z",
                "context_summary": f"{event_type} event",
                "clip_s3_key": None,
                "idempotency_key": f"SITE-001:{event_id}",
            }
            receiver.store_event(payload)

        count = receiver.get_stored_events_count()
        assert count == 3
