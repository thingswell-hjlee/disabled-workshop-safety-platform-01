"""Dashboard Backend - CRUD Operations

PostgreSQL CRUD 작업. Raw SQL 기반으로 data-model.md 스키마 직접 매핑.
"""

import logging
from datetime import datetime, timezone
from typing import Optional, List, Tuple

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .schemas import IoTEventPayload, IoTStatusPayload

logger = logging.getLogger(__name__)


# --- Event CRUD ---

async def insert_event(session: AsyncSession, payload: IoTEventPayload) -> dict:
    """Insert a new event from IoT payload."""
    query = text("""
        INSERT INTO events (
            event_id, site_id, device_id, worker_id,
            event_type, risk_level, confidence, model_version,
            timestamp, state, context_summary,
            clip_s3_key, idempotency_key, synced_to_cloud
        ) VALUES (
            :event_id, :site_id, :device_id, :worker_id,
            :event_type, :risk_level, :confidence, :model_version,
            :timestamp, 'ACTIVE', :context_summary,
            :clip_s3_key, :idempotency_key, TRUE
        )
        ON CONFLICT (idempotency_key) DO NOTHING
        RETURNING event_id, created_at
    """)

    result = await session.execute(query, {
        "event_id": payload.event_id,
        "site_id": payload.site_id,
        "device_id": payload.device_id,
        "worker_id": payload.worker_id,
        "event_type": payload.event_type.value,
        "risk_level": payload.risk_level.value,
        "confidence": payload.confidence,
        "model_version": payload.model_version,
        "timestamp": payload.timestamp,
        "context_summary": payload.context_summary,
        "clip_s3_key": payload.clip_s3_key,
        "idempotency_key": payload.idempotency_key,
    })

    row = result.fetchone()
    if row:
        return {"event_id": row[0], "created_at": str(row[1]), "status": "created"}
    else:
        return {"event_id": payload.event_id, "status": "duplicate_skipped"}


async def get_events(
    session: AsyncSession,
    site_id: str = "SITE-001",
    risk_level: Optional[str] = None,
    event_type: Optional[str] = None,
    device_id: Optional[str] = None,
    state: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> Tuple[List[dict], int]:
    """Get paginated event list with filters."""
    conditions = ["site_id = :site_id"]
    params = {"site_id": site_id, "limit": limit, "offset": offset}

    if risk_level:
        conditions.append("risk_level = :risk_level")
        params["risk_level"] = risk_level

    if event_type:
        conditions.append("event_type = :event_type")
        params["event_type"] = event_type

    if device_id:
        conditions.append("device_id = :device_id")
        params["device_id"] = device_id

    if state:
        conditions.append("state = :state")
        params["state"] = state

    if date_from:
        conditions.append("timestamp >= :date_from")
        params["date_from"] = date_from

    if date_to:
        conditions.append("timestamp <= :date_to")
        params["date_to"] = date_to

    where_clause = " AND ".join(conditions)

    # Count total
    count_query = text(f"SELECT COUNT(*) FROM events WHERE {where_clause}")
    count_result = await session.execute(count_query, params)
    total = count_result.scalar()

    # Fetch events
    data_query = text(f"""
        SELECT event_id, site_id, device_id, worker_id,
               event_type, risk_level, confidence, model_version,
               timestamp, state, clip_path, clip_s3_key
        FROM events
        WHERE {where_clause}
        ORDER BY timestamp DESC
        LIMIT :limit OFFSET :offset
    """)
    result = await session.execute(data_query, params)
    rows = result.fetchall()

    events = []
    for row in rows:
        events.append({
            "event_id": row[0],
            "site_id": row[1],
            "device_id": row[2],
            "worker_id": row[3],
            "event_type": row[4],
            "risk_level": row[5],
            "confidence": row[6],
            "model_version": row[7],
            "timestamp": row[8].isoformat() if row[8] else None,
            "state": row[9],
            "clip_path": row[10],
            "clip_s3_key": row[11],
        })

    return events, total


async def get_event_by_id(session: AsyncSession, event_id: str) -> Optional[dict]:
    """Get event detail by event_id."""
    query = text("""
        SELECT event_id, site_id, device_id, worker_id,
               event_type, risk_level, confidence, model_version,
               timestamp, state, context_summary,
               acknowledged_by, acknowledged_at, ack_reason,
               clip_path, clip_s3_key, idempotency_key,
               synced_to_cloud, created_at
        FROM events
        WHERE event_id = :event_id
    """)
    result = await session.execute(query, {"event_id": event_id})
    row = result.fetchone()

    if not row:
        return None

    return {
        "event_id": row[0],
        "site_id": row[1],
        "device_id": row[2],
        "worker_id": row[3],
        "event_type": row[4],
        "risk_level": row[5],
        "confidence": row[6],
        "model_version": row[7],
        "timestamp": row[8].isoformat() if row[8] else None,
        "state": row[9],
        "context_summary": row[10],
        "acknowledged_by": row[11],
        "acknowledged_at": row[12].isoformat() if row[12] else None,
        "ack_reason": row[13],
        "clip_path": row[14],
        "clip_s3_key": row[15],
        "idempotency_key": row[16],
        "synced_to_cloud": row[17],
        "created_at": row[18].isoformat() if row[18] else None,
    }


async def acknowledge_event(
    session: AsyncSession,
    event_id: str,
    acknowledged_by: str,
    reason: Optional[str] = None,
) -> Optional[dict]:
    """Acknowledge an event."""
    now = datetime.now(timezone.utc)
    query = text("""
        UPDATE events
        SET state = 'ACKNOWLEDGED',
            acknowledged_by = :acknowledged_by,
            acknowledged_at = :acknowledged_at,
            ack_reason = :reason
        WHERE event_id = :event_id AND state = 'ACTIVE'
        RETURNING event_id, state, acknowledged_by, acknowledged_at
    """)
    result = await session.execute(query, {
        "event_id": event_id,
        "acknowledged_by": acknowledged_by,
        "acknowledged_at": now,
        "reason": reason,
    })
    row = result.fetchone()
    if not row:
        return None
    return {
        "event_id": row[0],
        "state": row[1],
        "acknowledged_by": row[2],
        "acknowledged_at": row[3].isoformat() if row[3] else None,
        "ack_reason": reason,
    }


async def archive_event(session: AsyncSession, event_id: str) -> Optional[dict]:
    """Archive an event."""
    query = text("""
        UPDATE events
        SET state = 'ARCHIVED'
        WHERE event_id = :event_id AND state IN ('ACTIVE', 'ACKNOWLEDGED')
        RETURNING event_id, state
    """)
    result = await session.execute(query, {"event_id": event_id})
    row = result.fetchone()
    if not row:
        return None
    return {
        "event_id": row[0],
        "state": row[1],
        "archived_at": datetime.now(timezone.utc).isoformat(),
    }


# --- Device CRUD ---

async def get_devices(
    session: AsyncSession,
    site_id: str = "SITE-001",
    device_type: Optional[str] = None,
    status: Optional[str] = None,
) -> Tuple[List[dict], int, dict]:
    """Get all devices with optional filters."""
    conditions = ["site_id = :site_id"]
    params = {"site_id": site_id}

    if device_type:
        conditions.append("device_type = :device_type")
        params["device_type"] = device_type

    if status:
        conditions.append("status = :status")
        params["status"] = status

    where_clause = " AND ".join(conditions)

    # Fetch devices
    query = text(f"""
        SELECT device_id, device_type, name, status, site_id,
               zone_id, last_heartbeat, metadata
        FROM devices
        WHERE {where_clause}
        ORDER BY device_id
    """)
    result = await session.execute(query, params)
    rows = result.fetchall()

    devices = []
    summary = {"connected": 0, "disconnected": 0, "error": 0}
    for row in rows:
        device = {
            "device_id": row[0],
            "device_type": row[1],
            "name": row[2],
            "status": row[3],
            "site_id": row[4],
            "zone_id": row[5],
            "last_heartbeat": row[6].isoformat() if row[6] else None,
            "metrics": row[7],
        }
        devices.append(device)

        if row[3] == "CONNECTED":
            summary["connected"] += 1
        elif row[3] == "DISCONNECTED":
            summary["disconnected"] += 1
        elif row[3] == "ERROR":
            summary["error"] += 1

    return devices, len(devices), summary


async def get_device_by_id(session: AsyncSession, device_id: str) -> Optional[dict]:
    """Get device detail by device_id."""
    query = text("""
        SELECT device_id, device_type, name, status, site_id,
               zone_id, ip_address, firmware_version,
               last_heartbeat, metadata, created_at, updated_at
        FROM devices
        WHERE device_id = :device_id
    """)
    result = await session.execute(query, {"device_id": device_id})
    row = result.fetchone()

    if not row:
        return None

    return {
        "device_id": row[0],
        "device_type": row[1],
        "name": row[2],
        "status": row[3],
        "site_id": row[4],
        "zone_id": row[5],
        "ip_address": row[6],
        "firmware_version": row[7],
        "last_heartbeat": row[8].isoformat() if row[8] else None,
        "metadata": row[9],
        "created_at": row[10].isoformat() if row[10] else None,
        "updated_at": row[11].isoformat() if row[11] else None,
    }


async def update_device_status(
    session: AsyncSession,
    device_id: str,
    status: str,
    last_heartbeat: Optional[str] = None,
) -> Optional[dict]:
    """Update device status."""
    now = datetime.now(timezone.utc)
    query = text("""
        UPDATE devices
        SET status = :status,
            last_heartbeat = COALESCE(:last_heartbeat, last_heartbeat),
            updated_at = :updated_at
        WHERE device_id = :device_id
        RETURNING device_id, status, last_heartbeat
    """)
    result = await session.execute(query, {
        "device_id": device_id,
        "status": status,
        "last_heartbeat": last_heartbeat,
        "updated_at": now,
    })
    row = result.fetchone()
    if not row:
        return None
    return {
        "device_id": row[0],
        "status": row[1],
        "last_heartbeat": row[2].isoformat() if row[2] else None,
    }


# --- Edge Status CRUD ---

async def insert_edge_status(session: AsyncSession, payload: IoTStatusPayload) -> dict:
    """Insert edge status report."""
    import json
    query = text("""
        INSERT INTO edge_status (
            site_id, timestamp, edge_status,
            deepstream_fps, gpu_utilization,
            active_cameras, active_bands, pending_cloud_events
        ) VALUES (
            :site_id, :timestamp, :edge_status,
            :deepstream_fps, :gpu_utilization,
            :active_cameras, :active_bands, :pending_cloud_events
        )
        RETURNING id
    """)
    result = await session.execute(query, {
        "site_id": payload.site_id,
        "timestamp": payload.timestamp,
        "edge_status": payload.edge_status.value,
        "deepstream_fps": json.dumps(payload.deepstream_fps),
        "gpu_utilization": payload.gpu_utilization,
        "active_cameras": payload.active_cameras,
        "active_bands": payload.active_bands,
        "pending_cloud_events": payload.pending_cloud_events,
    })
    row = result.fetchone()
    return {"id": row[0], "status": "created"}


async def get_latest_edge_status(session: AsyncSession, site_id: str = "SITE-001") -> Optional[dict]:
    """Get latest edge status for a site."""
    query = text("""
        SELECT site_id, timestamp, edge_status,
               deepstream_fps, gpu_utilization,
               active_cameras, active_bands, pending_cloud_events
        FROM edge_status
        WHERE site_id = :site_id
        ORDER BY timestamp DESC
        LIMIT 1
    """)
    result = await session.execute(query, {"site_id": site_id})
    row = result.fetchone()
    if not row:
        return None
    return {
        "site_id": row[0],
        "timestamp": row[1].isoformat() if row[1] else None,
        "edge_status": row[2],
        "deepstream_fps": row[3],
        "gpu_utilization": row[4],
        "active_cameras": row[5],
        "active_bands": row[6],
        "pending_cloud_events": row[7],
    }


# --- Model Version CRUD ---

async def get_model_versions(
    session: AsyncSession,
    site_id: str = "SITE-001",
) -> List[dict]:
    """Get all model versions for a site."""
    query = text("""
        SELECT model_version, model_type, model_name, precision,
               status, deployed_at, metrics
        FROM model_versions
        WHERE site_id = :site_id
        ORDER BY deployed_at DESC NULLS LAST
    """)
    result = await session.execute(query, {"site_id": site_id})
    rows = result.fetchall()

    models = []
    for row in rows:
        models.append({
            "model_version": row[0],
            "model_type": row[1],
            "model_name": row[2],
            "precision": row[3],
            "status": row[4],
            "deployed_at": row[5].isoformat() if row[5] else None,
            "metrics": row[6],
        })
    return models


async def get_model_version_by_id(
    session: AsyncSession,
    model_version: str,
) -> Optional[dict]:
    """Get model version detail."""
    query = text("""
        SELECT model_version, site_id, model_type, model_name,
               framework, precision, engine_path, file_size_mb,
               trained_at, metrics, status, deployed_at, s3_key,
               created_at
        FROM model_versions
        WHERE model_version = :model_version
    """)
    result = await session.execute(query, {"model_version": model_version})
    row = result.fetchone()
    if not row:
        return None
    return {
        "model_version": row[0],
        "site_id": row[1],
        "model_type": row[2],
        "model_name": row[3],
        "framework": row[4],
        "precision": row[5],
        "engine_path": row[6],
        "file_size_mb": row[7],
        "trained_at": row[8].isoformat() if row[8] else None,
        "metrics": row[9],
        "status": row[10],
        "deployed_at": row[11].isoformat() if row[11] else None,
        "s3_key": row[12],
        "created_at": row[13].isoformat() if row[13] else None,
    }
