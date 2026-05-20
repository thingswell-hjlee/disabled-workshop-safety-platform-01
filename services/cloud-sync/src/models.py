"""Cloud Sync - Data Models & Type Definitions"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List


class SyncState(str, Enum):
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    SYNCING = "SYNCING"
    ERROR = "ERROR"


class QueuePriority(str, Enum):
    HIGH = "HIGH"       # CRITICAL events
    NORMAL = "NORMAL"   # WARNING events
    LOW = "LOW"         # NORMAL / status updates


@dataclass
class SyncStatus:
    """Current cloud sync status"""
    state: SyncState = SyncState.ONLINE
    pending_events: int = 0
    last_sync_at: Optional[str] = None
    last_error: Optional[str] = None
    events_synced_today: int = 0
    bytes_transferred_today: int = 0
    avg_latency_ms: float = 0.0


@dataclass
class QueuedEvent:
    """Event queued for cloud transmission"""
    event_id: str
    site_id: str
    priority: QueuePriority
    payload: dict = field(default_factory=dict)
    queued_at: str = ""
    retry_count: int = 0
    max_retries: int = 5
    idempotency_key: str = ""


@dataclass
class SyncResult:
    """Result of a sync operation"""
    event_id: str
    success: bool
    status_code: Optional[int] = None
    error_message: Optional[str] = None
    synced_at: Optional[str] = None
    latency_ms: Optional[float] = None


@dataclass
class CloudConnection:
    """AWS IoT Core connection info"""
    endpoint: str = ""
    connected: bool = False
    protocol: str = "mqtt"
    tls_version: str = "TLSv1.2"
    cert_expiry: Optional[str] = None
    last_ping_ms: Optional[float] = None


@dataclass
class SyncStats:
    """Sync service statistics"""
    total_synced: int = 0
    total_failed: int = 0
    total_retried: int = 0
    queue_depth: int = 0
    avg_sync_latency_ms: float = 0.0
    uptime_seconds: int = 0
    network_outages_today: int = 0
    last_outage_duration_seconds: Optional[int] = None
