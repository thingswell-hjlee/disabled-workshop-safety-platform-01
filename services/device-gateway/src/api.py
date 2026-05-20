"""Device Gateway - REST API Endpoints"""
from fastapi import FastAPI, HTTPException
from typing import List

from .models import DeviceHealthResponse, DeviceStatus, DeviceType

app = FastAPI(
    title="Device Gateway Service",
    description="현장 장비 데이터 수집 및 정규화 서비스",
    version="1.0.0",
)


@app.get("/health")
async def health_check():
    """서비스 헬스체크"""
    return {
        "status": "healthy",
        "service": "device-gateway",
        "version": "1.0.0",
    }


@app.get("/api/v1/devices", response_model=List[DeviceHealthResponse])
async def get_all_devices():
    """전체 장비 상태 조회"""
    # TODO: Implement device registry lookup
    raise HTTPException(status_code=501, detail="Not implemented")


@app.get("/api/v1/devices/{device_id}", response_model=DeviceHealthResponse)
async def get_device(device_id: str):
    """개별 장비 상태 조회"""
    # TODO: Implement device lookup
    raise HTTPException(status_code=501, detail="Not implemented")


@app.post("/api/v1/devices/{device_id}/reconnect")
async def reconnect_device(device_id: str):
    """장비 수동 재연결 요청"""
    # TODO: Implement reconnection logic
    return {
        "device_id": device_id,
        "action": "reconnect",
        "status": "requested",
    }


@app.get("/api/v1/streams/status")
async def get_stream_status():
    """Redis Stream 발행 상태 조회"""
    # TODO: Implement stream status check
    return {
        "streams": {
            "frames": {"active_channels": 0, "messages_per_second": 0},
            "bio": {"active_bands": 0, "messages_per_second": 0},
            "sensors": {"active_sensors": 0, "messages_per_second": 0},
        }
    }
