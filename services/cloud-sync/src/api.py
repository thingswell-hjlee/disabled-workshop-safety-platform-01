"""Cloud Sync - REST API Endpoints"""
from fastapi import FastAPI

from .models import SyncStatus, SyncState, SyncStats, CloudConnection

app = FastAPI(
    title="Cloud Sync Service",
    description="Edge → AWS 클라우드 이벤트 동기화 서비스",
    version="1.0.0",
)


@app.get("/health")
async def health_check():
    """서비스 헬스체크"""
    return {
        "status": "healthy",
        "service": "cloud-sync",
        "version": "1.0.0",
        "cloud_connected": True,
    }


@app.get("/api/v1/sync/status")
async def get_sync_status():
    """현재 동기화 상태 조회"""
    return SyncStatus().__dict__


@app.get("/api/v1/sync/queue")
async def get_queue_status():
    """대기 큐 상태 조회"""
    # TODO: Query Redis queue depth
    return {
        "pending": 0,
        "high_priority": 0,
        "normal_priority": 0,
        "low_priority": 0,
        "oldest_queued_at": None,
    }


@app.post("/api/v1/sync/flush")
async def flush_queue():
    """큐잉된 이벤트 즉시 전송 시도"""
    # TODO: Trigger immediate sync
    return {"status": "flush_initiated", "pending_count": 0}


@app.post("/api/v1/sync/pause")
async def pause_sync():
    """동기화 일시 중지"""
    # TODO: Pause sync worker
    return {"status": "paused"}


@app.post("/api/v1/sync/resume")
async def resume_sync():
    """동기화 재개"""
    # TODO: Resume sync worker
    return {"status": "resumed"}


@app.get("/api/v1/sync/stats")
async def get_sync_stats():
    """동기화 통계"""
    return SyncStats().__dict__


@app.get("/api/v1/sync/connection")
async def get_connection_info():
    """AWS IoT Core 연결 정보"""
    return CloudConnection().__dict__


@app.post("/api/v1/sync/reconnect")
async def reconnect():
    """클라우드 연결 재시도"""
    # TODO: Implement reconnection
    return {"status": "reconnect_initiated"}
