"""Dashboard Backend - REST API & WebSocket Endpoints

Platform 1.0 구현:
- Event ingest (IoT Core mock receiver용)
- Event list/detail/acknowledge/archive
- Device list/detail/status update
- Model version list/detail
- Edge status ingest/query
- System health

Reference: docs/api-spec.md
"""

import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings
from .database import get_db_session, check_db_health, init_db, close_db
from .schemas import (
    IoTEventPayload,
    IoTStatusPayload,
    EventListResponse,
    EventDetailResponse,
    DeviceListResponse,
    DeviceDetailResponse,
    ModelListResponse,
    ModelDetailResponse,
    ErrorResponse,
)
from . import crud

logger = logging.getLogger(__name__)


# --- Lifespan ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup/shutdown lifecycle."""
    logger.info(f"Starting {settings.service_name} v{settings.service_version}")
    logger.info(f"AWS Mode: {settings.aws_mode.value}")
    logger.info(f"Database: {settings.db_host}:{settings.db_port}/{settings.db_name}")
    await init_db()
    yield
    await close_db()
    logger.info("Shutdown complete")


app = FastAPI(
    title="Safety Platform Dashboard Backend API",
    description="AI기반 장애인직업재활시설 스마트안전시스템 - 대시보드 REST API",
    version="1.0.0",
    lifespan=lifespan,
)

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://dashboard.safety-platform.io"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Health
# ============================================================

@app.get("/health")
async def health_check():
    """Service health check."""
    db_health = await check_db_health()
    return {
        "status": "healthy" if db_health["status"] == "healthy" else "degraded",
        "service": settings.service_name,
        "version": settings.service_version,
        "aws_mode": settings.aws_mode.value,
        "database": db_health,
    }


# ============================================================
# Event Ingest (IoT Core Rule → Lambda → this API, or mock direct call)
# ============================================================

@app.post("/api/v1/events/ingest", status_code=201)
async def ingest_event(
    payload: IoTEventPayload,
    session: AsyncSession = Depends(get_db_session),
):
    """
    Ingest event from IoT Core (via Lambda) or direct mock call.
    Validates payload against event-message-schema and inserts to PostgreSQL.
    """
    try:
        result = await crud.insert_event(session, payload)
        return {
            "status": "accepted",
            "event_id": result["event_id"],
            "detail": result["status"],
        }
    except Exception as e:
        logger.error(f"Event ingest failed: {e}")
        raise HTTPException(status_code=500, detail=f"Event ingest failed: {str(e)}")


# ============================================================
# Event Queries (docs/api-spec.md Section 2)
# ============================================================

@app.get("/api/v1/events")
async def get_events(
    risk_level: Optional[str] = Query(None, description="CRITICAL, WARNING, NORMAL"),
    event_type: Optional[str] = Query(None, description="Event type filter"),
    device_id: Optional[str] = Query(None, description="Device ID filter"),
    state: Optional[str] = Query(None, description="ACTIVE, ACKNOWLEDGED, ARCHIVED"),
    date_from: Optional[str] = Query(None, description="Start date (ISO 8601)"),
    date_to: Optional[str] = Query(None, description="End date (ISO 8601)"),
    limit: int = Query(50, ge=1, le=200, description="Page size"),
    offset: int = Query(0, ge=0, description="Offset"),
    session: AsyncSession = Depends(get_db_session),
):
    """이벤트 목록 조회 (필터링 + 페이지네이션)."""
    events, total = await crud.get_events(
        session,
        site_id=settings.site_id,
        risk_level=risk_level,
        event_type=event_type,
        device_id=device_id,
        state=state,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset,
    )
    return {"events": events, "total": total, "limit": limit, "offset": offset}


@app.get("/api/v1/events/{event_id}")
async def get_event_detail(
    event_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """이벤트 상세 조회."""
    event = await crud.get_event_by_id(session, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@app.post("/api/v1/events/{event_id}/acknowledge")
async def acknowledge_event(
    event_id: str,
    body: dict,
    session: AsyncSession = Depends(get_db_session),
):
    """이벤트 Acknowledge (알람 해제)."""
    acknowledged_by = body.get("acknowledged_by")
    reason = body.get("reason")

    if not acknowledged_by:
        raise HTTPException(status_code=400, detail="acknowledged_by is required")

    result = await crud.acknowledge_event(session, event_id, acknowledged_by, reason)
    if not result:
        raise HTTPException(
            status_code=404,
            detail="Event not found or not in ACTIVE state"
        )
    return result


@app.post("/api/v1/events/{event_id}/archive")
async def archive_event(
    event_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """이벤트 Archive (보관 처리)."""
    result = await crud.archive_event(session, event_id)
    if not result:
        raise HTTPException(
            status_code=404,
            detail="Event not found or already archived"
        )
    return result


# ============================================================
# Device APIs (docs/api-spec.md Section 3)
# ============================================================

@app.get("/api/v1/devices")
async def get_devices(
    device_type: Optional[str] = Query(None, description="Device type filter"),
    status: Optional[str] = Query(None, description="Status filter"),
    session: AsyncSession = Depends(get_db_session),
):
    """전체 장비 목록 조회."""
    devices, total, summary = await crud.get_devices(
        session,
        site_id=settings.site_id,
        device_type=device_type,
        status=status,
    )
    return {"devices": devices, "total": total, "summary": summary}


@app.get("/api/v1/devices/{device_id}")
async def get_device_detail(
    device_id: str,
    session: AsyncSession = Depends(get_db_session),
):
    """개별 장비 상세 조회."""
    device = await crud.get_device_by_id(session, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@app.patch("/api/v1/devices/{device_id}/status")
async def update_device_status(
    device_id: str,
    body: dict,
    session: AsyncSession = Depends(get_db_session),
):
    """장비 상태 업데이트 (내부 API)."""
    new_status = body.get("status")
    if not new_status:
        raise HTTPException(status_code=400, detail="status field is required")

    valid_statuses = ["CONNECTED", "DISCONNECTED", "ERROR", "MAINTENANCE"]
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"status must be one of {valid_statuses}"
        )

    result = await crud.update_device_status(
        session, device_id, new_status,
        last_heartbeat=body.get("last_heartbeat"),
    )
    if not result:
        raise HTTPException(status_code=404, detail="Device not found")
    return result


# ============================================================
# Model Version APIs (docs/api-spec.md Section 6)
# ============================================================

@app.get("/api/v1/models")
async def get_models(
    session: AsyncSession = Depends(get_db_session),
):
    """모델 버전 목록 조회."""
    models = await crud.get_model_versions(session, site_id=settings.site_id)
    return {"models": models, "total": len(models)}


@app.get("/api/v1/models/{model_version}")
async def get_model_detail(
    model_version: str,
    session: AsyncSession = Depends(get_db_session),
):
    """모델 버전 상세 조회."""
    model = await crud.get_model_version_by_id(session, model_version)
    if not model:
        raise HTTPException(status_code=404, detail="Model version not found")
    return model


# ============================================================
# Edge Status APIs
# ============================================================

@app.post("/api/v1/edge/status", status_code=201)
async def ingest_edge_status(
    payload: IoTStatusPayload,
    session: AsyncSession = Depends(get_db_session),
):
    """Edge 서버 상태 보고 수신 (safety/{site_id}/status mock)."""
    result = await crud.insert_edge_status(session, payload)
    return {"status": "accepted", "detail": result}


@app.get("/api/v1/edge/status/latest")
async def get_latest_edge_status(
    session: AsyncSession = Depends(get_db_session),
):
    """최신 Edge 서버 상태 조회."""
    status = await crud.get_latest_edge_status(session, site_id=settings.site_id)
    if not status:
        return {"message": "No edge status reported yet"}
    return status


# ============================================================
# System Health (docs/api-spec.md Section 9)
# ============================================================

@app.get("/api/v1/system/health")
async def get_system_health(
    session: AsyncSession = Depends(get_db_session),
):
    """전체 시스템 헬스 체크."""
    db_health = await check_db_health()
    edge_status = await crud.get_latest_edge_status(session, site_id=settings.site_id)

    return {
        "overall": "healthy" if db_health["status"] == "healthy" else "degraded",
        "timestamp": None,
        "services": {
            "dashboard-backend": {"status": "healthy", "version": settings.service_version},
            "database": db_health,
            "aws-mode": settings.aws_mode.value,
        },
        "edge": edge_status,
    }


# ============================================================
# Schema Validation Endpoint (for testing)
# ============================================================

@app.post("/api/v1/validate/event")
async def validate_event_schema(payload: dict):
    """
    Event payload schema validation (테스트 전용).
    실제 DB 저장 없이 payload 검증만 수행.
    """
    try:
        validated = IoTEventPayload(**payload)
        return {"valid": True, "parsed": validated.model_dump()}
    except ValidationError as e:
        return {
            "valid": False,
            "errors": e.errors(),
        }


# ============================================================
# WebSocket (실시간 이벤트 스트림)
# ============================================================

@app.websocket("/ws/dashboard")
async def websocket_dashboard(websocket: WebSocket):
    """실시간 대시보드 데이터 스트림."""
    await websocket.accept()
    try:
        while True:
            # TODO: Subscribe to Redis streams and forward to client
            data = await websocket.receive_text()
            await websocket.send_json({"type": "pong", "data": data})
    except WebSocketDisconnect:
        pass


# ============================================================
# Auth (Placeholder - 기존 유지)
# ============================================================

@app.post("/api/v1/auth/login")
async def login(credentials: dict):
    """관리자 로그인 → JWT 발급."""
    username = credentials.get("username", "")
    password = credentials.get("password", "")
    if not username or not password:
        raise HTTPException(status_code=400, detail="Username and password required")
    # TODO: Implement real authentication
    return {
        "access_token": "mock_access_token",
        "refresh_token": "mock_refresh_token",
        "token_type": "bearer",
        "expires_in": settings.jwt_expire_minutes * 60,
    }
