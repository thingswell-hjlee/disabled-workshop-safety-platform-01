"""Cloud Sync - Model Tests"""
import pytest
from src.models import (
    SyncState, QueuePriority, SyncStatus,
    QueuedEvent, SyncResult, CloudConnection, SyncStats,
)


class TestSyncStatus:
    def test_default_online(self):
        status = SyncStatus()
        assert status.state == SyncState.ONLINE
        assert status.pending_events == 0

    def test_offline_with_pending(self):
        status = SyncStatus(
            state=SyncState.OFFLINE,
            pending_events=42,
            last_error="Connection timeout",
        )
        assert status.state == SyncState.OFFLINE
        assert status.pending_events == 42


class TestQueuedEvent:
    def test_critical_event(self):
        event = QueuedEvent(
            event_id="EVT-20250519120000-001",
            site_id="SITE-001",
            priority=QueuePriority.HIGH,
            payload={"event_type": "FALL_DETECTED"},
            queued_at="2025-05-19T12:00:00.000Z",
            idempotency_key="EVT-20250519120000-001",
        )
        assert event.priority == QueuePriority.HIGH
        assert event.retry_count == 0
        assert event.max_retries == 5

    def test_retry_increment(self):
        event = QueuedEvent(
            event_id="EVT-20250519120000-002",
            site_id="SITE-001",
            priority=QueuePriority.NORMAL,
            retry_count=3,
        )
        assert event.retry_count == 3


class TestSyncResult:
    def test_success(self):
        result = SyncResult(
            event_id="EVT-20250519120000-001",
            success=True,
            status_code=200,
            synced_at="2025-05-19T12:00:01.000Z",
            latency_ms=120.5,
        )
        assert result.success is True
        assert result.latency_ms == 120.5

    def test_failure(self):
        result = SyncResult(
            event_id="EVT-20250519120000-002",
            success=False,
            error_message="Connection refused",
        )
        assert result.success is False


class TestCloudConnection:
    def test_default(self):
        conn = CloudConnection()
        assert conn.protocol == "mqtt"
        assert conn.tls_version == "TLSv1.2"
        assert conn.connected is False
