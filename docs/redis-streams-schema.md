# Redis Streams Message Schema

> **Status:** FROZEN (Platform 1.0)
> **Last Updated:** 2025-05-19
> **Purpose:** 엣지 서버 내부 컴포넌트 간 Redis Streams 메시지 구조 정의

## Overview

Platform 1.0에서는 6개의 Redis Stream을 사용하여 컴포넌트 간 비동기 메시지를 전달합니다.

```
┌──────────────┐     stream:ds-events     ┌──────────────┐
│  DeepStream  │ ──────────────────────▶   │              │
└──────────────┘                           │              │     stream:alarms      ┌────────────────┐
                                           │              │ ──────────────────────▶ │ Alarm Controller│
┌──────────────┐     stream:sensors        │ Event Engine │                        └────────────────┘
│Device Gateway│ ──────────────────────▶   │              │     stream:dashboard   ┌────────────────┐
└──────────────┘                           │              │ ──────────────────────▶ │Dashboard Backend│
                                           │              │                        └────────────────┘
                                           │              │     stream:cloud-queue  ┌────────────────┐
                                           │              │ ──────────────────────▶ │  AWS Sync Svc  │
                                           │              │                        └────────────────┘
                                           │              │     stream:clip-trigger ┌────────────────┐
                                           │              │ ──────────────────────▶ │ Rolling Buffer │
                                           └──────────────┘                        └────────────────┘
```

---

## 1. stream:ds-events

### Metadata

| Property | Value |
|----------|-------|
| **Stream Name** | `stream:ds-events` |
| **Publisher** | DeepStream Pipeline |
| **Subscriber** | Event Engine |
| **Consumer Group** | `cg-event-engine` |
| **Max Length** | 10,000 entries |
| **TTL** | 1 hour |

### Message Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `event_id` | string | Yes | `EVT-YYYYMMDDHHmmss-SEQ` |
| `site_id` | string | Yes | `SITE-NNN` |
| `source_id` | string | Yes | Source pipeline identifier |
| `device_id` | string | Yes | `CAM-NNN` |
| `event_type` | string | Yes | event_type enum |
| `timestamp` | string | Yes | ISO 8601 UTC |
| `model_version` | string | Yes | `v{M}.{m}.{p}-{tool}-{target}` |
| `inference.pgie` | object | Yes | Primary GIE inference result |
| `inference.pgie.class_id` | integer | Yes | Detected class ID |
| `inference.pgie.confidence` | float | Yes | 0.0 ~ 1.0 |
| `inference.pgie.label` | string | Yes | Class label |
| `inference.pgie.bbox` | object | Yes | `{x, y, w, h}` normalized 0~1 |
| `inference.sgie` | object | No | Secondary GIE result (Platform 1.0: optional) |
| `inference.tracker` | object | Yes | Object tracker state |
| `inference.tracker.object_id` | integer | Yes | Tracker assigned ID |
| `inference.tracker.age_frames` | integer | Yes | Frames since first seen |
| `analytics` | object | No | Analytics metadata (reserved Platform 2.0+) |

### Example JSON

```json
{
  "event_id": "EVT-20250519120000-001",
  "site_id": "SITE-001",
  "source_id": "pipeline-0",
  "device_id": "CAM-001",
  "event_type": "FALL_DETECTED",
  "timestamp": "2025-05-19T12:00:00.123Z",
  "model_version": "v1.0.0-tao-ds",
  "inference": {
    "pgie": {
      "class_id": 2,
      "confidence": 0.92,
      "label": "fall",
      "bbox": { "x": 0.35, "y": 0.45, "w": 0.15, "h": 0.20 }
    },
    "sgie": null,
    "tracker": {
      "object_id": 42,
      "age_frames": 15
    }
  },
  "analytics": null
}
```

---

## 2. stream:sensors

### Metadata

| Property | Value |
|----------|-------|
| **Stream Name** | `stream:sensors` |
| **Publisher** | Device Gateway |
| **Subscriber** | Event Engine |
| **Consumer Group** | `cg-event-engine` |
| **Max Length** | 50,000 entries |
| **TTL** | 30 minutes |

### Message Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `event_id` | string | Yes | `EVT-YYYYMMDDHHmmss-SEQ` |
| `site_id` | string | Yes | `SITE-NNN` |
| `device_id` | string | Yes | `BAND-NNN` or `ENV-NNN` |
| `worker_id` | string | Conditional | `WKR-NNNN` (required for SMART_BAND) |
| `event_type` | string | Yes | event_type enum |
| `timestamp` | string | Yes | ISO 8601 UTC |
| `data_type` | string | Yes | `HEARTRATE`, `TEMPERATURE`, `FALL`, `GAS`, `HUMIDITY`, `DUST`, `DISCONNECT` |
| `value` | float/string | Yes | Measured value or state |
| `source` | string | Yes | `SMART_BAND`, `ENV_SENSOR`, `FIRE_CONTACT` |

### Example JSON

```json
{
  "event_id": "EVT-20250519120100-005",
  "site_id": "SITE-001",
  "device_id": "BAND-003",
  "worker_id": "WKR-0012",
  "event_type": "HEARTRATE_ABNORMAL",
  "timestamp": "2025-05-19T12:01:00.456Z",
  "data_type": "HEARTRATE",
  "value": 142,
  "source": "SMART_BAND"
}
```

---

## 3. stream:alarms

### Metadata

| Property | Value |
|----------|-------|
| **Stream Name** | `stream:alarms` |
| **Publisher** | Event Engine |
| **Subscriber** | Alarm Controller |
| **Consumer Group** | `cg-alarm-ctrl` |
| **Max Length** | 1,000 entries |
| **TTL** | 10 minutes |

### Message Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `event_id` | string | Yes | Source event ID |
| `site_id` | string | Yes | `SITE-NNN` |
| `risk_level` | string | Yes | `CRITICAL`, `WARNING`, `NORMAL` |
| `action` | string | Yes | `SIREN_ON`, `LIGHT_ON`, `ALL_ON`, `ALL_OFF` |
| `timestamp` | string | Yes | ISO 8601 UTC |
| `source_event_type` | string | Yes | Original event_type that triggered alarm |

### Example JSON

```json
{
  "event_id": "EVT-20250519120000-001",
  "site_id": "SITE-001",
  "risk_level": "CRITICAL",
  "action": "ALL_ON",
  "timestamp": "2025-05-19T12:00:00.200Z",
  "source_event_type": "FALL_DETECTED"
}
```

---

## 4. stream:dashboard

### Metadata

| Property | Value |
|----------|-------|
| **Stream Name** | `stream:dashboard` |
| **Publisher** | Event Engine |
| **Subscriber** | Dashboard Backend |
| **Consumer Group** | `cg-dashboard` |
| **Max Length** | 5,000 entries |
| **TTL** | 30 minutes |

### Message Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `event_id` | string | Yes | `EVT-YYYYMMDDHHmmss-SEQ` |
| `site_id` | string | Yes | `SITE-NNN` |
| `device_id` | string | Yes | Source device |
| `worker_id` | string | No | Associated worker (if applicable) |
| `event_type` | string | Yes | event_type enum |
| `risk_level` | string | Yes | risk_level enum |
| `timestamp` | string | Yes | ISO 8601 UTC |
| `event_state` | string | Yes | `ACTIVE` (initial) |
| `confidence` | float | No | 0.0 ~ 1.0 (for AI events) |
| `model_version` | string | No | Model version (for AI events) |
| `context` | object | Yes | Event context for dashboard display |
| `context.summary` | string | Yes | Human-readable summary |
| `context.location` | string | No | Device/zone location label |
| `context.clip_available` | boolean | Yes | Whether video clip is available |

### Example JSON

```json
{
  "event_id": "EVT-20250519120000-001",
  "site_id": "SITE-001",
  "device_id": "CAM-001",
  "worker_id": null,
  "event_type": "FALL_DETECTED",
  "risk_level": "CRITICAL",
  "timestamp": "2025-05-19T12:00:00.123Z",
  "event_state": "ACTIVE",
  "confidence": 0.92,
  "model_version": "v1.0.0-tao-ds",
  "context": {
    "summary": "작업장 A구역 낙상 감지 (신뢰도 92%)",
    "location": "A구역 프레스실",
    "clip_available": true
  }
}
```

---

## 5. stream:cloud-queue

### Metadata

| Property | Value |
|----------|-------|
| **Stream Name** | `stream:cloud-queue` |
| **Publisher** | Event Engine |
| **Subscriber** | AWS Sync Service |
| **Consumer Group** | `cg-aws-sync` |
| **Max Length** | 10,000 entries |
| **TTL** | 24 hours |

### Message Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `event_id` | string | Yes | `EVT-YYYYMMDDHHmmss-SEQ` |
| `site_id` | string | Yes | `SITE-NNN` |
| `device_id` | string | Yes | Source device |
| `worker_id` | string | No | Associated worker |
| `event_type` | string | Yes | event_type enum |
| `risk_level` | string | Yes | risk_level enum |
| `timestamp` | string | Yes | ISO 8601 UTC |
| `idempotency_key` | string | Yes | `{site_id}:{event_id}` for deduplication |
| `priority` | string | Yes | `HIGH`, `NORMAL`, `LOW` |
| `clip_path` | string | No | Local file path to video clip |
| `confidence` | float | No | 0.0 ~ 1.0 |
| `model_version` | string | No | Model version |

### Priority Rules

| Priority | Condition |
|----------|-----------|
| `HIGH` | risk_level = CRITICAL |
| `NORMAL` | risk_level = WARNING |
| `LOW` | risk_level = NORMAL, DEVICE_ONLINE/OFFLINE |

### Example JSON

```json
{
  "event_id": "EVT-20250519120000-001",
  "site_id": "SITE-001",
  "device_id": "CAM-001",
  "worker_id": null,
  "event_type": "FALL_DETECTED",
  "risk_level": "CRITICAL",
  "timestamp": "2025-05-19T12:00:00.123Z",
  "idempotency_key": "SITE-001:EVT-20250519120000-001",
  "priority": "HIGH",
  "clip_path": "/data/clips/EVT-20250519120000-001.mp4",
  "confidence": 0.92,
  "model_version": "v1.0.0-tao-ds"
}
```

---

## 6. stream:clip-trigger

### Metadata

| Property | Value |
|----------|-------|
| **Stream Name** | `stream:clip-trigger` |
| **Publisher** | Event Engine |
| **Subscriber** | Rolling Buffer Service |
| **Consumer Group** | `cg-rolling-buffer` |
| **Max Length** | 1,000 entries |
| **TTL** | 5 minutes |

### Message Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `event_id` | string | Yes | Triggering event ID |
| `site_id` | string | Yes | `SITE-NNN` |
| `device_id` | string | Yes | `CAM-NNN` (camera source) |
| `trigger_ts` | string | Yes | ISO 8601 UTC - moment of event |
| `pre_sec` | integer | Yes | Seconds before event (default: 30) |
| `post_sec` | integer | Yes | Seconds after event (default: 30) |

### Example JSON

```json
{
  "event_id": "EVT-20250519120000-001",
  "site_id": "SITE-001",
  "device_id": "CAM-001",
  "trigger_ts": "2025-05-19T12:00:00.123Z",
  "pre_sec": 30,
  "post_sec": 30
}
```

---

## Consumer Group Configuration

| Stream | Consumer Group | Consumers | Acknowledgement |
|--------|---------------|-----------|-----------------|
| `stream:ds-events` | `cg-event-engine` | 1 (Event Engine) | Per-message ACK |
| `stream:sensors` | `cg-event-engine` | 1 (Event Engine) | Per-message ACK |
| `stream:alarms` | `cg-alarm-ctrl` | 1 (Alarm Controller) | Per-message ACK |
| `stream:dashboard` | `cg-dashboard` | 1 (Dashboard Backend) | Per-message ACK |
| `stream:cloud-queue` | `cg-aws-sync` | 1 (AWS Sync Service) | Per-message ACK after cloud confirm |
| `stream:clip-trigger` | `cg-rolling-buffer` | 1 (Rolling Buffer) | Per-message ACK after clip saved |

---

## Error Handling

- **Pending messages:** Consumer가 ACK하지 않은 메시지는 `XPENDING`으로 모니터링
- **Claim timeout:** 60초 내 ACK 없으면 다른 consumer가 claim 가능
- **Dead letter:** 3회 재시도 실패 시 `stream:dead-letter`로 이동
- **Max length exceeded:** MAXLEN으로 자동 trim (가장 오래된 메시지 제거)
