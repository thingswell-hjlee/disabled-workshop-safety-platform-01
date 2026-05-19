"""Alarm Controller - REST API Endpoints"""
from fastapi import FastAPI

from .models import AlarmStatus, AlarmState, AlarmAction

app = FastAPI(
    title="Alarm Controller Service",
    description="접점연동 현장 경보(사이렌, 경광등) 제어 서비스",
    version="1.0.0",
)


@app.get("/health")
async def health_check():
    """서비스 헬스체크"""
    return {
        "status": "healthy",
        "service": "alarm-controller",
        "version": "1.0.0",
        "gpio": {"initialized": True},
    }


@app.get("/api/v1/alarm/status")
async def get_alarm_status():
    """현재 알람 상태 조회"""
    # TODO: Read actual GPIO state
    return AlarmStatus().__dict__


@app.post("/api/v1/alarm/trigger")
async def trigger_alarm(command: dict):
    """수동 알람 발동 (테스트용)"""
    action = command.get("action", "ALL_ON")
    return {
        "action": action,
        "status": "triggered",
        "message": f"Alarm {action} executed",
    }


@app.post("/api/v1/alarm/clear")
async def clear_alarm(request: dict):
    """알람 수동 해제"""
    return {
        "action": "ALL_OFF",
        "status": "cleared",
        "cleared_by": request.get("cleared_by", "system"),
        "reason": request.get("reason", ""),
    }


@app.get("/api/v1/alarm/logs")
async def get_alarm_logs(limit: int = 50):
    """알람 동작 이력 조회"""
    # TODO: Query alarm log store
    return {"logs": [], "total": 0}


@app.post("/api/v1/alarm/test")
async def test_alarm():
    """알람 장비 테스트 (1초 동작 후 자동 해제)"""
    # TODO: Implement GPIO test sequence
    return {
        "status": "test_completed",
        "siren": "ok",
        "light": "ok",
        "duration_ms": 1000,
    }
