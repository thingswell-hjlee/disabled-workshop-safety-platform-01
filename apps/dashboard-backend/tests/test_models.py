"""Dashboard Backend - Model Tests"""
import pytest
from src.models import (
    User, UserRole, WorkerStatus, WorkerInfo,
    DashboardSummary, SystemMetrics, WebSocketMessage,
)


class TestUser:
    def test_create_admin(self):
        user = User(
            user_id="USR-001",
            username="admin",
            role=UserRole.ADMIN,
            display_name="관리자",
        )
        assert user.role == UserRole.ADMIN
        assert user.is_active is True
        assert user.failed_login_attempts == 0

    def test_locked_user(self):
        user = User(
            user_id="USR-002",
            username="operator1",
            role=UserRole.OPERATOR,
            display_name="운영자1",
            failed_login_attempts=5,
            locked_until="2025-05-19T12:15:00.000Z",
        )
        assert user.failed_login_attempts == 5


class TestWorkerInfo:
    def test_normal_worker(self):
        worker = WorkerInfo(
            worker_id="WKR-0001",
            name="작업자1",
            status=WorkerStatus.NORMAL,
            device_id="BAND-001",
            heartrate=72,
            body_temperature=36.5,
            zone="작업장A",
        )
        assert worker.status == WorkerStatus.NORMAL
        assert worker.heartrate == 72

    def test_offline_worker(self):
        worker = WorkerInfo(
            worker_id="WKR-0003",
            name="작업자3",
            status=WorkerStatus.OFFLINE,
            device_id="BAND-003",
        )
        assert worker.heartrate is None


class TestDashboardSummary:
    def test_default_summary(self):
        summary = DashboardSummary()
        assert summary.total_cameras == 8
        assert summary.total_bands == 8
        assert summary.network_status == "connected"


class TestWebSocketMessage:
    def test_event_message(self):
        msg = WebSocketMessage(
            type="event",
            timestamp="2025-05-19T12:00:00.000Z",
            data={"event_type": "FALL_DETECTED", "risk_level": "CRITICAL"},
        )
        assert msg.type == "event"
        assert msg.data["risk_level"] == "CRITICAL"
