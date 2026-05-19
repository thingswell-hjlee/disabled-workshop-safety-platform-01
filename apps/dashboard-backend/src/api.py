"""Dashboard Backend - REST API & WebSocket Endpoints"""
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends
from typing import Optional

from .models import (
    DashboardSummary, SystemMetrics, WorkerStatus, TokenResponse,
)

app = FastAPI(
    title="Dashboard Backend API",
    description="관리자 대시보드 REST API + WebSocket 서비스",
    version="1.0.0",
)


# --- Health ---
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "dashboard-backend",
        "version": "1.0.0",
    }


# --- Auth ---
@app.post("/api/v1/auth/login")
async def login(credentials: dict):
    """관리자 로그인 → JWT 발급"""
    username = credentials.get("username", "")
    password = credentials.get("password", "")
    # TODO: Implement real authentication
    if not username or not password:
        raise HTTPException(status_code=400, detail="Username and password required")
    return {
        "access_token": "mock_access_token",
        "refresh_token": "mock_refresh_token",
        "token_type": "bearer",
        "expires_in": 1800,
    }


@app.post("/api/v1/auth/refresh")
async def refresh_token(body: dict):
    """토큰 갱신"""
    # TODO: Implement token refresh
    return {
        "access_token": "new_mock_access_token",
        "token_type": "bearer",
        "expires_in": 1800,
    }


@app.get("/api/v1/auth/me")
async def get_current_user():
    """현재 인증된 사용자 정보"""
    # TODO: Extract from JWT
    return {
        "user_id": "USR-001",
        "username": "admin",
        "role": "admin",
        "display_name": "관리자",
    }


# --- Dashboard ---
@app.get("/api/v1/dashboard/summary")
async def get_dashboard_summary():
    """전체 현황 요약"""
    return DashboardSummary().__dict__


@app.get("/api/v1/dashboard/devices")
async def get_devices_status():
    """전 장비 상태 목록"""
    # TODO: Aggregate from device-gateway
    return {"devices": [], "total": 0}


@app.get("/api/v1/dashboard/workers")
async def get_workers_status():
    """작업자 상태 목록"""
    # TODO: Aggregate from bio stream
    return {"workers": [], "total": 0}


# --- Events ---
@app.get("/api/v1/events")
async def get_events(
    risk_level: Optional[str] = None,
    event_type: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    """이벤트 목록 조회 (필터링)"""
    # TODO: Query event store
    return {"events": [], "total": 0, "limit": limit, "offset": offset}


@app.get("/api/v1/events/{event_id}")
async def get_event_detail(event_id: str):
    """이벤트 상세 조회"""
    raise HTTPException(status_code=404, detail="Event not found")


@app.post("/api/v1/events/{event_id}/acknowledge")
async def acknowledge_event(event_id: str, body: dict):
    """이벤트 알람 해제"""
    return {
        "event_id": event_id,
        "status": "acknowledged",
        "acknowledged_by": body.get("acknowledged_by"),
    }


# --- System ---
@app.get("/api/v1/system/health")
async def get_system_health():
    """전 서비스 상태 집합"""
    return {
        "services": {
            "device-gateway": "healthy",
            "ai-inference": "healthy",
            "event-processor": "healthy",
            "alarm-controller": "healthy",
            "cloud-sync": "healthy",
        },
        "overall": "healthy",
    }


@app.get("/api/v1/system/metrics")
async def get_system_metrics():
    """시스템 메트릭"""
    return SystemMetrics().__dict__


# --- WebSocket ---
@app.websocket("/ws/dashboard")
async def websocket_dashboard(websocket: WebSocket):
    """실시간 대시보드 데이터 스트림"""
    await websocket.accept()
    try:
        while True:
            # TODO: Subscribe to Redis streams and forward to client
            data = await websocket.receive_text()
            await websocket.send_json({"type": "pong", "data": data})
    except WebSocketDisconnect:
        pass
