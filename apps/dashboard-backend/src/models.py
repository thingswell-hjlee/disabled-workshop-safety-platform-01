"""Dashboard Backend - Data Models & Type Definitions"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List


class UserRole(str, Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"


class WorkerStatus(str, Enum):
    NORMAL = "NORMAL"
    ABNORMAL = "ABNORMAL"
    OFFLINE = "OFFLINE"


@dataclass
class User:
    """System user (dashboard admin)"""
    user_id: str
    username: str
    role: UserRole
    display_name: str
    is_active: bool = True
    failed_login_attempts: int = 0
    locked_until: Optional[str] = None


@dataclass
class LoginRequest:
    username: str
    password: str


@dataclass
class TokenResponse:
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 1800  # 30 minutes


@dataclass
class DashboardSummary:
    """Main dashboard summary data"""
    critical_count: int = 0
    warning_count: int = 0
    total_events_today: int = 0
    active_cameras: int = 0
    total_cameras: int = 8
    active_bands: int = 0
    total_bands: int = 8
    active_sensors: int = 0
    total_sensors: int = 2
    network_status: str = "connected"  # connected | disconnected
    edge_ai_status: str = "healthy"  # healthy | degraded | down
    last_update: Optional[str] = None


@dataclass
class WorkerInfo:
    """Worker status for dashboard display"""
    worker_id: str
    name: str
    status: WorkerStatus
    device_id: str  # associated band
    heartrate: Optional[int] = None
    body_temperature: Optional[float] = None
    zone: Optional[str] = None
    last_update: Optional[str] = None


@dataclass
class SystemMetrics:
    """System-level metrics for monitoring"""
    edge_cpu_percent: float = 0.0
    edge_gpu_percent: float = 0.0
    edge_memory_percent: float = 0.0
    redis_memory_mb: float = 0.0
    cloud_sync_pending: int = 0
    uptime_seconds: int = 0


@dataclass
class WebSocketMessage:
    """WebSocket message format"""
    type: str  # "event" | "status" | "metric" | "alarm"
    timestamp: str
    data: dict = field(default_factory=dict)
