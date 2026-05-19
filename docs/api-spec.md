# Platform 1.0 API 명세 (API Specification)

> **참조:** docs/design.md | docs/software-architecture.md | docs/data-model.md
> **기준:** REST API, JSON 응답, API 버전 `/api/v1/`
> **인증:** JWT Bearer Token (대시보드 API), X.509 인증서 (AWS IoT)

---

## 공통 규칙

### 요청/응답 형식
- Content-Type: `application/json`
- 날짜: ISO 8601 UTC (`2025-05-19T12:00:00.000Z`)
- 에러 응답: `{"error": {"code": "...", "message": "..."}}`

### 인증
- 대시보드 API: `Authorization: Bearer {access_token}`
- 시스템 내부 API: 인증 없음 (내부 네트워크, Docker network)
- AWS 전송: X.509 인증서 (MQTT over TLS)

### 페이지네이션
```
GET /api/v1/events?limit=50&offset=0&sort=timestamp:desc
```

### 공통 응답 코드

| Code | 의미 |
|------|------|
| 200 | 성공 |
| 201 | 생성 성공 |
| 400 | 잘못된 요청 |
| 401 | 인증 필요 |
| 403 | 권한 없음 |
| 404 | 리소스 없음 |
| 500 | 서버 에러 |

---

## 1. Edge AI 서버 → AWS 이벤트 전송 API

### 1.1 개요

| 항목 | 내용 |
|------|------|
| 방향 | Edge AI → AWS IoT Core |
| 프로토콜 | MQTT over TLS (port 8883) |
| 인증 | X.509 디바이스 인증서 |
| 토픽 | `safety/{site_id}/events` |
| QoS | 1 (At least once) |
| 모듈 | aws-sync-agent |

### 1.2 이벤트 메시지 (Publish)

**Topic:** `safety/SITE-001/events`

```json
{
  "event_id": "EVT-20250519120000-001",
  "site_id": "SITE-001",
  "device_id": "CAM-001",
  "worker_id": "WKR-0002",
  "event_type": "FALL_DETECTED",
  "risk_level": "CRITICAL",
  "confidence": 0.88,
  "model_version": "v1.0.0-tao-ds",
  "timestamp": "2025-05-19T12:00:00.123Z",
  "context_summary": {
    "tracking_id": 42,
    "zone": "DangerZone-A",
    "activity_index": 0.15,
    "active_cameras": 8,
    "dwell_time_sec": 0.0
  },
  "clip_s3_key": "events/SITE-001/2025/05/19/EVT-20250519120000-001.mp4",
  "idempotency_key": "EVT-20250519120000-001"
}
```

### 1.3 상태 보고 메시지

**Topic:** `safety/SITE-001/status`

```json
{
  "site_id": "SITE-001",
  "timestamp": "2025-05-19T12:00:00.000Z",
  "edge_status": "ONLINE",
  "deepstream_fps": [15.2, 15.1, 14.9, 15.0, 15.3, 14.8, 15.1, 15.0],
  "gpu_utilization": 62.5,
  "active_cameras": 8,
  "active_bands": 8,
  "pending_cloud_events": 0
}
```

### 1.4 영상 클립 업로드

| 항목 | 내용 |
|------|------|
| 방향 | Edge AI → AWS S3 |
| 프로토콜 | HTTPS (Multipart Upload) |
| 인증 | IAM STS 임시 자격 증명 |
| 버킷 | `safety-platform-events-{account_id}` |
| 키 패턴 | `events/{site_id}/{YYYY}/{MM}/{DD}/{event_id}.mp4` |

---

## 2. Edge AI 서버 → 대시보드 이벤트 조회 API

### 2.1 이벤트 목록 조회

```
GET /api/v1/events
```

**Query Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| risk_level | string | ❌ | CRITICAL, WARNING, NORMAL |
| event_type | string | ❌ | FALL_DETECTED 등 |
| device_id | string | ❌ | 장비 필터 |
| state | string | ❌ | ACTIVE, ACKNOWLEDGED, ARCHIVED |
| date_from | string | ❌ | 시작 날짜 (ISO 8601) |
| date_to | string | ❌ | 종료 날짜 |
| limit | int | ❌ | 페이지 크기 (기본 50) |
| offset | int | ❌ | 오프셋 |

**Response 200:**

```json
{
  "events": [
    {
      "event_id": "EVT-20250519120000-001",
      "site_id": "SITE-001",
      "device_id": "CAM-001",
      "worker_id": "WKR-0002",
      "event_type": "FALL_DETECTED",
      "risk_level": "CRITICAL",
      "confidence": 0.88,
      "timestamp": "2025-05-19T12:00:00.123Z",
      "state": "ACTIVE",
      "clip_path": "/clips/2025/05/19/EVT-20250519120000-001.mp4"
    }
  ],
  "total": 142,
  "limit": 50,
  "offset": 0
}
```

### 2.2 이벤트 상세 조회

```
GET /api/v1/events/{event_id}
```

**Response 200:**

```json
{
  "event_id": "EVT-20250519120000-001",
  "site_id": "SITE-001",
  "device_id": "CAM-001",
  "worker_id": "WKR-0002",
  "event_type": "FALL_DETECTED",
  "risk_level": "CRITICAL",
  "confidence": 0.88,
  "model_version": "v1.0.0-tao-ds",
  "timestamp": "2025-05-19T12:00:00.123Z",
  "state": "ACTIVE",
  "clip_path": "/clips/2025/05/19/EVT-20250519120000-001.mp4",
  "context": {
    "video_clip": {
      "path": "/clips/2025/05/19/EVT-20250519120000-001.mp4",
      "start_ts": "2025-05-19T11:59:30.000Z",
      "end_ts": "2025-05-19T12:00:30.000Z",
      "duration_sec": 60
    },
    "inference_detail": {
      "pgie_conf": 0.95,
      "sgie_conf": 0.88,
      "tracking_id": 42,
      "dwell_time_sec": 0.0,
      "roi_name": "DangerZone-A"
    },
    "sensor_snapshot": {
      "band_data": {"bpm": 72, "temp": 36.5},
      "env_data": {"temperature": 25.3, "co_ppm": 2.1}
    },
    "activity_index": 0.15
  },
  "acknowledged_by": null,
  "acknowledged_at": null,
  "ack_reason": null
}
```

### 2.3 실시간 이벤트 스트림 (WebSocket)

```
WS /ws/dashboard
```

**서버 → 클라이언트 Push 메시지:**

```json
{
  "type": "event",
  "timestamp": "2025-05-19T12:00:00.123Z",
  "data": {
    "event_id": "EVT-20250519120000-001",
    "event_type": "FALL_DETECTED",
    "risk_level": "CRITICAL",
    "device_id": "CAM-001",
    "confidence": 0.88
  }
}
```

**메시지 타입:**

| type | 설명 | 갱신 주기 |
|------|------|-----------|
| event | 새 이벤트 발생 | 즉시 |
| device_status | 장비 상태 변경 | 즉시 |
| system_metrics | GPU, FPS, 메모리 | 5초 |
| alarm_state | 알람 동작/해제 | 즉시 |

---

## 3. 장비 상태 조회 API

### 3.1 전체 장비 목록

```
GET /api/v1/devices
```

**Query Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| device_type | string | ❌ | IP_CAMERA, SMART_BAND 등 |
| status | string | ❌ | CONNECTED, DISCONNECTED 등 |

**Response 200:**

```json
{
  "devices": [
    {
      "device_id": "CAM-001",
      "device_type": "IP_CAMERA",
      "name": "작업장A 북측",
      "status": "CONNECTED",
      "zone_id": "ZONE-A",
      "last_heartbeat": "2025-05-19T12:00:00.000Z",
      "metrics": {"fps": 15.2, "resolution": "1920x1080"}
    },
    {
      "device_id": "BAND-001",
      "device_type": "SMART_BAND",
      "name": "밴드 #1",
      "status": "CONNECTED",
      "worker_id": "WKR-0001",
      "last_heartbeat": "2025-05-19T11:59:55.000Z",
      "metrics": {"battery": 85, "heartrate": 72}
    }
  ],
  "total": 20,
  "summary": {
    "connected": 18,
    "disconnected": 1,
    "error": 1
  }
}
```

### 3.2 개별 장비 상세

```
GET /api/v1/devices/{device_id}
```

**Response 200:**

```json
{
  "device_id": "CAM-001",
  "device_type": "IP_CAMERA",
  "name": "작업장A 북측",
  "site_id": "SITE-001",
  "zone_id": "ZONE-A",
  "status": "CONNECTED",
  "ip_address": "192.168.10.101",
  "firmware_version": "2.1.0",
  "last_heartbeat": "2025-05-19T12:00:00.000Z",
  "camera_detail": {
    "rtsp_url": "rtsp://192.168.10.101:554/stream1",
    "resolution": "1920x1080",
    "fps": 15,
    "source_id": 0,
    "recording_enabled": true
  },
  "health_history": [
    {"timestamp": "2025-05-19T11:55:00Z", "status": "CONNECTED", "fps": 15.1},
    {"timestamp": "2025-05-19T11:50:00Z", "status": "CONNECTED", "fps": 15.0}
  ]
}
```

---

## 4. 알람 제어 API

### 4.1 현재 알람 상태

```
GET /api/v1/alarm/status
```

**Response 200:**

```json
{
  "state": "BOTH_ON",
  "siren_active": true,
  "light_active": true,
  "triggered_at": "2025-05-19T12:00:00.123Z",
  "triggered_by_event": "EVT-20250519120000-001",
  "risk_level": "CRITICAL",
  "duration_sec": 45
}
```

### 4.2 알람 수동 해제 (Acknowledge)

```
POST /api/v1/alarm/clear
```

**Request Body:**

```json
{
  "cleared_by": "admin",
  "reason": "작업자 확인 완료 - 정상 활동",
  "event_id": "EVT-20250519120000-001"
}
```

**Response 200:**

```json
{
  "status": "cleared",
  "cleared_at": "2025-05-19T12:00:45.000Z",
  "cleared_by": "admin",
  "previous_state": "BOTH_ON"
}
```

### 4.3 알람 테스트

```
POST /api/v1/alarm/test
```

**Response 200:**

```json
{
  "status": "test_completed",
  "siren": "ok",
  "light": "ok",
  "duration_ms": 1000
}
```

---

## 5. 이벤트 조치 상태 변경 API

### 5.1 이벤트 Acknowledge

```
POST /api/v1/events/{event_id}/acknowledge
```

**Request Body:**

```json
{
  "acknowledged_by": "admin",
  "reason": "오탐 확인 - 작업자 정상 착석 동작"
}
```

**Response 200:**

```json
{
  "event_id": "EVT-20250519120000-001",
  "state": "ACKNOWLEDGED",
  "acknowledged_by": "admin",
  "acknowledged_at": "2025-05-19T12:05:00.000Z",
  "ack_reason": "오탐 확인 - 작업자 정상 착석 동작",
  "alarm_cleared": true
}
```

### 5.2 이벤트 아카이브

```
POST /api/v1/events/{event_id}/archive
```

**Response 200:**

```json
{
  "event_id": "EVT-20250519120000-001",
  "state": "ARCHIVED",
  "archived_at": "2025-05-19T13:00:00.000Z"
}
```

---

## 6. 모델 버전 조회 API

### 6.1 모델 목록

```
GET /api/v1/models
```

**Response 200:**

```json
{
  "models": [
    {
      "model_version": "v1.0.0-tao-ds",
      "model_type": "PGIE_DETECTION",
      "model_name": "PeopleNet",
      "precision": "FP16",
      "status": "ACTIVE",
      "deployed_at": "2025-05-19T10:00:00.000Z",
      "metrics": {
        "mAP": 0.91,
        "precision": 0.93,
        "recall": 0.89,
        "f1": 0.91,
        "inference_ms": 12.5
      }
    },
    {
      "model_version": "v1.0.0-tao-ds",
      "model_type": "SGIE_ACTION",
      "model_name": "ActionRecognitionNet",
      "precision": "FP16",
      "status": "ACTIVE",
      "deployed_at": "2025-05-19T10:00:00.000Z",
      "metrics": {
        "mAP": 0.84,
        "precision": 0.86,
        "recall": 0.82,
        "f1": 0.84,
        "inference_ms": 4.2
      }
    }
  ],
  "total": 2
}
```

### 6.2 모델 상세

```
GET /api/v1/models/{model_version}
```

**Response 200:**

```json
{
  "model_version": "v1.0.0-tao-ds",
  "model_type": "PGIE_DETECTION",
  "model_name": "PeopleNet",
  "framework": "TENSORRT",
  "precision": "FP16",
  "engine_path": "/models/active/pgie/peoplenet_v1.0.0_fp16.engine",
  "file_size_mb": 45.2,
  "trained_at": "2025-05-15T14:00:00.000Z",
  "deployed_at": "2025-05-19T10:00:00.000Z",
  "status": "ACTIVE",
  "metrics": {
    "mAP": 0.91,
    "precision": 0.93,
    "recall": 0.89,
    "f1": 0.91,
    "inference_ms": 12.5
  },
  "training_config": {
    "base_model": "peoplenet_vunpruned_v2.6.2",
    "epochs": 80,
    "dataset_size": 5000
  }
}
```

---

## 7. 모델 배포 상태 API

### 7.1 현재 배포 상태

```
GET /api/v1/deploy/status
```

**Response 200:**

```json
{
  "current_pgie": {
    "model_version": "v1.0.0-tao-ds",
    "status": "ACTIVE",
    "deployed_at": "2025-05-19T10:00:00.000Z"
  },
  "current_sgie": {
    "model_version": "v1.0.0-tao-ds",
    "status": "ACTIVE",
    "deployed_at": "2025-05-19T10:00:00.000Z"
  },
  "staged": null,
  "rollback_available": {
    "model_version": "v0.9.0-pretrained-ds",
    "engine_path": "/models/rollback/pgie/peoplenet_v0.9.0_fp16.engine"
  },
  "last_deploy": {
    "timestamp": "2025-05-19T10:00:00.000Z",
    "result": "SUCCESS",
    "duration_sec": 8
  }
}
```

### 7.2 모델 배포 요청

```
POST /api/v1/deploy
```

**Request Body:**

```json
{
  "model_version": "v1.1.0-tao-ds",
  "target": "PGIE",
  "engine_path": "/models/staged/pgie/peoplenet_v1.1.0_fp16.engine"
}
```

**Response 202 (Accepted):**

```json
{
  "deploy_id": "DEP-20250519150000-001",
  "model_version": "v1.1.0-tao-ds",
  "status": "DEPLOYING",
  "message": "Deployment initiated. Hot-swap in progress."
}
```

### 7.3 배포 롤백

```
POST /api/v1/deploy/rollback
```

**Response 200:**

```json
{
  "status": "ROLLED_BACK",
  "previous_version": "v1.1.0-tao-ds",
  "restored_version": "v1.0.0-tao-ds",
  "rolled_back_at": "2025-05-19T15:01:00.000Z"
}
```

---

## 8. 로컬 이벤트 재전송 API

### 8.1 클라우드 동기화 상태

```
GET /api/v1/sync/status
```

**Response 200:**

```json
{
  "state": "ONLINE",
  "pending_events": 0,
  "last_sync_at": "2025-05-19T12:00:00.000Z",
  "events_synced_today": 23,
  "bytes_transferred_today": 145600000,
  "avg_latency_ms": 120.5,
  "network_outages_today": 0
}
```

### 8.2 큐 상태

```
GET /api/v1/sync/queue
```

**Response 200:**

```json
{
  "pending": 0,
  "by_priority": {
    "HIGH": 0,
    "NORMAL": 0,
    "LOW": 0
  },
  "oldest_queued_at": null,
  "queue_capacity": 10000,
  "disk_backup_enabled": true
}
```

### 8.3 즉시 재전송 (Flush)

```
POST /api/v1/sync/flush
```

**Response 200:**

```json
{
  "status": "flush_initiated",
  "pending_count": 5,
  "estimated_duration_sec": 10
}
```

### 8.4 동기화 일시 중지/재개

```
POST /api/v1/sync/pause
POST /api/v1/sync/resume
```

**Response 200:**

```json
{
  "status": "paused",
  "paused_at": "2025-05-19T12:00:00.000Z"
}
```

---

## 9. 시스템 상태 API

### 9.1 전체 시스템 헬스

```
GET /api/v1/system/health
```

**Response 200:**

```json
{
  "overall": "healthy",
  "timestamp": "2025-05-19T12:00:00.000Z",
  "services": {
    "deepstream-pipeline": {"status": "healthy", "fps_avg": 15.1, "uptime_sec": 259200},
    "event-engine": {"status": "healthy", "events_processed": 1523, "queue_depth": 0},
    "alarm-controller": {"status": "healthy", "gpio_initialized": true, "current_state": "IDLE"},
    "device-gateway": {"status": "healthy", "connected_devices": 18},
    "aws-sync": {"status": "healthy", "cloud_connected": true, "pending": 0},
    "dashboard-backend": {"status": "healthy", "active_sessions": 2},
    "redis": {"status": "healthy", "memory_used_mb": 128},
    "mosquitto": {"status": "healthy", "connected_clients": 12}
  },
  "network": {
    "internet": "connected",
    "aws_iot": "connected",
    "local_lan": "connected"
  }
}
```

### 9.2 시스템 메트릭

```
GET /api/v1/system/metrics
```

**Response 200:**

```json
{
  "timestamp": "2025-05-19T12:00:00.000Z",
  "edge_server": {
    "cpu_percent": 42.5,
    "memory_percent": 58.3,
    "disk_percent": 35.2,
    "uptime_hours": 72
  },
  "gpu": {
    "utilization_percent": 62.5,
    "memory_used_mb": 4200,
    "memory_total_mb": 12288,
    "temperature_celsius": 65
  },
  "deepstream": {
    "pipeline_state": "PLAYING",
    "fps_per_channel": [15.2, 15.1, 14.9, 15.0, 15.3, 14.8, 15.1, 15.0],
    "avg_inference_ms": 12.5,
    "frames_processed_total": 8542300
  },
  "events": {
    "total_today": 23,
    "critical_today": 2,
    "warning_today": 8,
    "avg_processing_ms": 18.3
  },
  "storage": {
    "clips_size_gb": 12.5,
    "events_db_size_mb": 45,
    "nvr_usage_percent": 42
  }
}
```

### 9.3 DeepStream 파이프라인 상태

```
GET /api/v1/system/deepstream
```

**Response 200:**

```json
{
  "pipeline_state": "PLAYING",
  "uptime_sec": 259200,
  "sources": [
    {"source_id": 0, "device_id": "CAM-001", "status": "STREAMING", "fps": 15.2},
    {"source_id": 1, "device_id": "CAM-002", "status": "STREAMING", "fps": 15.1},
    {"source_id": 2, "device_id": "CAM-003", "status": "STREAMING", "fps": 14.9},
    {"source_id": 3, "device_id": "CAM-004", "status": "STREAMING", "fps": 15.0},
    {"source_id": 4, "device_id": "CAM-005", "status": "STREAMING", "fps": 15.3},
    {"source_id": 5, "device_id": "CAM-006", "status": "STREAMING", "fps": 14.8},
    {"source_id": 6, "device_id": "CAM-007", "status": "STREAMING", "fps": 15.1},
    {"source_id": 7, "device_id": "CAM-008", "status": "STREAMING", "fps": 15.0}
  ],
  "models": {
    "pgie": {"version": "v1.0.0-tao-ds", "status": "LOADED", "inference_ms": 12.5},
    "sgie": {"version": "v1.0.0-tao-ds", "status": "LOADED", "inference_ms": 4.2}
  },
  "tracker": {
    "algorithm": "NvDCF",
    "active_tracks": 12,
    "max_tracks_per_source": 50
  },
  "analytics": {
    "roi_zones_configured": 8,
    "events_generated_total": 1523
  }
}
```

---

## API 요약 매트릭스

| # | API | Method | Path | 모듈 | 인증 | 관련 요구사항 |
|---|-----|--------|------|------|------|--------------|
| 1 | AWS 이벤트 전송 | MQTT Pub | safety/{site}/events | aws-sync-agent | X.509 | FR-CLD-001,002 |
| 2 | 이벤트 조회 | GET | /api/v1/events | dashboard-backend | JWT | FR-DSH-005,006 |
| 3 | 장비 상태 | GET | /api/v1/devices | dashboard-backend | JWT | FR-DSH-007, FR-DEV-* |
| 4 | 알람 제어 | GET/POST | /api/v1/alarm/* | alarm-control | JWT | FR-EVT-008~012 |
| 5 | 이벤트 조치 | POST | /api/v1/events/{id}/acknowledge | event-engine | JWT | FR-EVT-010,011 |
| 6 | 모델 버전 | GET | /api/v1/models | model-management | JWT | FR-CLD-005 |
| 7 | 모델 배포 | GET/POST | /api/v1/deploy/* | model-management | Internal | FR-TAO-009,010 |
| 8 | 재전송 | GET/POST | /api/v1/sync/* | aws-sync-agent | JWT | FR-CLD-002 |
| 9 | 시스템 상태 | GET | /api/v1/system/* | dashboard-backend | JWT | FR-DSH-007, NFR-017,018 |

---

## 변경 이력

| 버전 | 일자 | 내용 |
|------|------|------|
| 1.0 | 2025-05-19 | Platform 1.0 API 명세 초안 (9개 API 그룹) |
