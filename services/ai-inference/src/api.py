"""AI Inference Engine - REST API Endpoints"""
from fastapi import FastAPI, HTTPException
from typing import List

from .models import ModelInfo, InferenceStats, ZoneConfig

app = FastAPI(
    title="AI Inference Engine Service",
    description="Edge AI 실시간 위험 감지·판단 서비스",
    version="1.0.0",
)


@app.get("/health")
async def health_check():
    """서비스 헬스체크 (GPU 상태 포함)"""
    return {
        "status": "healthy",
        "service": "ai-inference",
        "version": "1.0.0",
        "gpu": {
            "available": True,
            "device": "cuda:0",
            "utilization_percent": 0.0,
            "memory_used_mb": 0.0,
        },
    }


@app.get("/api/v1/models", response_model=List[dict])
async def get_models():
    """현재 로드된 모델 목록"""
    # TODO: Implement model registry lookup
    return [
        {
            "model_id": "yolov8-safety",
            "model_type": "object_detection",
            "model_version": "v1.0.0-edge",
            "framework": "tensorrt",
            "status": "loaded",
        }
    ]


@app.get("/api/v1/models/{model_id}/info")
async def get_model_info(model_id: str):
    """모델 상세 정보"""
    # TODO: Implement model info lookup
    raise HTTPException(status_code=501, detail="Not implemented")


@app.post("/api/v1/models/{model_id}/reload")
async def reload_model(model_id: str):
    """모델 핫스왑 요청"""
    # TODO: Implement hot-swap logic
    return {
        "model_id": model_id,
        "action": "reload",
        "status": "accepted",
        "message": "Model reload request queued",
    }


@app.get("/api/v1/inference/stats")
async def get_inference_stats():
    """추론 통계"""
    # TODO: Implement real stats collection
    return InferenceStats().__dict__


@app.get("/api/v1/zones")
async def get_zones():
    """전체 위험구역 설정 조회"""
    # TODO: Implement zone config lookup
    return {"zones": []}


@app.put("/api/v1/zones/{camera_id}")
async def set_zone(camera_id: str, zone: dict):
    """카메라별 위험구역 polygon 설정"""
    # TODO: Implement zone config update
    return {
        "camera_id": camera_id,
        "action": "zone_updated",
        "zone": zone,
    }
