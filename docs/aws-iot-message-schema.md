# AWS IoT Core Message Schema

> **Status:** FROZEN (Platform 1.0)
> **Last Updated:** 2025-05-19
> **Purpose:** AWS IoT Core MQTT 토픽 구조, 메시지 페이로드, S3 업로드 경로 정의

## Overview

엣지 서버에서 AWS 클라우드로의 통신은 AWS IoT Core MQTT를 통해 수행됩니다.

```
┌──────────────┐                    ┌──────────────┐                ┌──────────────┐
│  Edge Server │ ── MQTT/TLS ──▶    │ AWS IoT Core │ ──── Rules ──▶ │  DynamoDB /  │
│  (Thing)     │                    │              │                │  Lambda / S3 │
└──────────────┘                    └──────────────┘                └──────────────┘
```

---

## 1. Connection & Authentication

| Property | Value |
|----------|-------|
| **Protocol** | MQTT over TLS 1.2 |
| **Port** | 8883 |
| **QoS** | 1 (At least once) |
| **Authentication** | X.509 device certificate |
| **Keep Alive** | 300 seconds |
| **Client ID** | `{site_id}-edge-{instance}` |

### Certificate Structure

```
/certs/
├── root-CA.crt          # Amazon Root CA
├── device.cert.pem      # Device certificate
└── device.private.key   # Private key
```


---

## 2. MQTT Topics

### 2.1 safety/{site_id}/events — Event Payload

**Direction:** Edge → Cloud
**Purpose:** 안전 이벤트 전송 (CRITICAL/WARNING 우선)

#### Message Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `event_id` | string | Yes | `EVT-YYYYMMDDHHmmss-SEQ` |
| `site_id` | string | Yes | `SITE-NNN` |
| `device_id` | string | Yes | Source device ID |
| `worker_id` | string | No | Associated worker (null if N/A) |
| `event_type` | string | Yes | event_type enum |
| `risk_level` | string | Yes | `CRITICAL`, `WARNING`, `NORMAL` |
| `confidence` | float | No | 0.0 ~ 1.0 (AI inference confidence) |
| `model_version` | string | No | Model version string |
| `timestamp` | string | Yes | ISO 8601 UTC |
| `context_summary` | string | Yes | Human-readable event summary |
| `clip_s3_key` | string | No | S3 key for video clip (null if not yet uploaded) |
| `idempotency_key` | string | Yes | `{site_id}:{event_id}` for deduplication |

#### Example Payload

```json
{
  "event_id": "EVT-20250519120000-001",
  "site_id": "SITE-001",
  "device_id": "CAM-001",
  "worker_id": null,
  "event_type": "FALL_DETECTED",
  "risk_level": "CRITICAL",
  "confidence": 0.92,
  "model_version": "v1.0.0-tao-ds",
  "timestamp": "2025-05-19T12:00:00.123Z",
  "context_summary": "작업장 A구역 낙상 감지 (신뢰도 92%)",
  "clip_s3_key": "events/SITE-001/2025/05/19/EVT-20250519120000-001.mp4",
  "idempotency_key": "SITE-001:EVT-20250519120000-001"
}
```


---

### 2.2 safety/{site_id}/status — Edge Status

**Direction:** Edge → Cloud
**Purpose:** 엣지 서버 상태 주기적 보고 (60초 간격)

#### Message Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `site_id` | string | Yes | `SITE-NNN` |
| `timestamp` | string | Yes | ISO 8601 UTC |
| `edge_status` | string | Yes | `HEALTHY`, `DEGRADED`, `ERROR` |
| `deepstream_fps` | array[float] | Yes | FPS per pipeline |
| `gpu_utilization` | float | Yes | 0.0 ~ 1.0 (GPU usage ratio) |
| `active_cameras` | integer | Yes | Number of connected cameras |
| `active_bands` | integer | Yes | Number of connected smart bands |
| `pending_cloud_events` | integer | Yes | Events waiting for cloud sync |

#### Example Payload

```json
{
  "site_id": "SITE-001",
  "timestamp": "2025-05-19T12:00:00.000Z",
  "edge_status": "HEALTHY",
  "deepstream_fps": [29.8, 30.1, 28.5, 30.0],
  "gpu_utilization": 0.65,
  "active_cameras": 4,
  "active_bands": 12,
  "pending_cloud_events": 3
}
```


---

### 2.3 safety/{site_id}/models — Model Deployment Status

**Direction:** Bidirectional (Cloud ↔ Edge)
**Purpose:** 모델 배포 명령 및 상태 보고

#### Cloud → Edge (Deploy Command)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `action` | string | Yes | `DEPLOY`, `ROLLBACK`, `STATUS_REQUEST` |
| `model_version` | string | Yes | Target model version |
| `model_type` | string | Yes | `pgie`, `sgie` |
| `s3_uri` | string | Yes | S3 URI for model package |
| `timestamp` | string | Yes | ISO 8601 UTC |

#### Edge → Cloud (Status Report)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `site_id` | string | Yes | `SITE-NNN` |
| `action` | string | Yes | `DEPLOY_STATUS` |
| `model_version` | string | Yes | Model version |
| `status` | string | Yes | `DOWNLOADING`, `STAGED`, `DEPLOYING`, `ACTIVE`, `FAILED`, `ROLLBACK` |
| `progress` | float | No | 0.0 ~ 1.0 (download/deploy progress) |
| `error_message` | string | No | Error details if FAILED |
| `timestamp` | string | Yes | ISO 8601 UTC |

#### Example Payloads

**Deploy Command:**
```json
{
  "action": "DEPLOY",
  "model_version": "v1.1.0-tao-ds",
  "model_type": "pgie",
  "s3_uri": "s3://safety-models/SITE-001/pgie/v1.1.0-tao-ds/model.zip",
  "timestamp": "2025-05-19T12:00:00.000Z"
}
```

**Status Report:**
```json
{
  "site_id": "SITE-001",
  "action": "DEPLOY_STATUS",
  "model_version": "v1.1.0-tao-ds",
  "status": "ACTIVE",
  "progress": 1.0,
  "error_message": null,
  "timestamp": "2025-05-19T12:05:30.000Z"
}
```


---

## 3. S3 Upload Path Pattern

### Event Video Clips

```
events/{site_id}/{YYYY}/{MM}/{DD}/{event_id}.mp4
```

**Example:**
```
events/SITE-001/2025/05/19/EVT-20250519120000-001.mp4
```

### Model Packages

```
models/{site_id}/{model_type}/{model_version}/model.zip
```

**Example:**
```
models/SITE-001/pgie/v1.1.0-tao-ds/model.zip
```

### Edge Logs (reserved Platform 2.0+)

```
logs/{site_id}/{YYYY}/{MM}/{DD}/{component}-{HH}.log.gz
```

---

## 4. Offline Queue Behavior

엣지 서버가 인터넷 연결이 끊긴 경우의 오프라인 큐 동작을 정의합니다.

| Property | Value |
|----------|-------|
| **Max Queue Size** | 10,000 events |
| **Queue Storage** | Local disk (`/data/offline-queue/`) |
| **Priority Order** | CRITICAL → WARNING → NORMAL |
| **Retry Strategy** | Exponential backoff |
| **Initial Retry Interval** | 5 seconds |
| **Max Retry Interval** | 5 minutes |
| **Backoff Multiplier** | 2x |
| **Connection Check** | Every 10 seconds |

### Queue Overflow Policy

1. Queue가 10,000 이벤트를 초과하면 **NORMAL** priority 이벤트부터 drop
2. **CRITICAL** 이벤트는 절대 drop하지 않음 (디스크 공간 허용 시)
3. Drop된 이벤트 수를 `pending_cloud_events` 메트릭에 반영

### Reconnection Behavior

```
[Disconnected] → 5s → retry → 10s → retry → 20s → retry → 40s → ... → 300s (max)
                  ↓ (connected)
[Connected] → Flush queue in priority order (CRITICAL first)
            → Resume normal operation
```

---

## 5. IoT Core Rules

| Rule Name | Topic Filter | Action |
|-----------|-------------|--------|
| `safety-events-to-dynamodb` | `safety/+/events` | DynamoDB put (events table) |
| `safety-events-critical-lambda` | `safety/+/events` (filter: risk_level=CRITICAL) | Lambda (notification) |
| `safety-status-to-timestream` | `safety/+/status` | Timestream write |
| `safety-models-to-lambda` | `safety/+/models` | Lambda (deploy orchestration) |

---

## 6. Security Requirements

| Requirement | Implementation |
|-------------|----------------|
| Transport encryption | TLS 1.2 mandatory |
| Device authentication | X.509 certificate per edge device |
| Topic authorization | IoT Policy restricts to own `site_id` |
| Message validation | IoT Rules SQL filter + Lambda validation |
| Certificate rotation | 365-day validity, auto-rotation (Platform 2.0+) |
| Audit logging | CloudTrail for IoT actions |
