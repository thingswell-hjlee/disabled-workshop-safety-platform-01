# Canonical Event Message Schema

> **Status:** FROZEN (Platform 1.0)
> **Last Updated:** 2025-05-19
> **Purpose:** 정규 이벤트 메시지의 단일 진실 원천 (Single Source of Truth)

## Overview

모든 컴포넌트는 이 정규 이벤트 메시지 구조를 기준으로 이벤트를 생성/소비합니다. Platform 1.0 필수 필드, Platform 2.0/3.0 reserved 필드를 명확히 구분합니다.

---

## 1. Platform 1.0 Required Fields (Non-null)

모든 이벤트 메시지에 반드시 포함되어야 하는 필드입니다.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `event_id` | string | 이벤트 고유 ID | `^EVT-\d{14}-\d{3}$` |
| `site_id` | string | 사이트 ID | `^SITE-\d{3}$` |
| `device_id` | string | 소스 디바이스 ID | `^(CAM\|BAND\|ENV\|FIRE\|NVR\|ALARM)-\d{3}$` |
| `event_type` | string | 이벤트 유형 | event_type enum |
| `risk_level` | string | 위험 수준 | `CRITICAL\|WARNING\|NORMAL` |
| `timestamp` | string | 이벤트 발생 시간 | ISO 8601 UTC |
| `event_state` | string | 이벤트 처리 상태 | `ACTIVE\|ACKNOWLEDGED\|ARCHIVED` |


---

## 2. Platform 1.0 Optional Fields (Nullable)

이벤트 유형에 따라 포함 여부가 결정되는 필드입니다.

| Field | Type | Description | Condition |
|-------|------|-------------|-----------|
| `worker_id` | string \| null | 관련 작업자 ID | SMART_BAND 이벤트 시 필수 |
| `confidence` | float \| null | AI 추론 신뢰도 (0.0~1.0) | Vision AI 이벤트 시 필수 |
| `model_version` | string \| null | 모델 버전 | Vision AI 이벤트 시 필수 |
| `context` | EventContext \| null | 이벤트 컨텍스트 | 가능한 경우 포함 |

---

## 3. Platform 2.0 Reserved Fields (Nullable)

Platform 2.0에서 활성화될 예정인 필드입니다. Platform 1.0에서는 항상 `null`입니다.

| Field | Type | Description | Platform |
|-------|------|-------------|----------|
| `feedback_type` | string \| null | 관리자 피드백 유형 (`TRUE_POSITIVE`, `FALSE_POSITIVE`, `MISSED`) | 2.0 |
| `activity_index_history` | array \| null | 작업자 활동 지수 이력 (최근 N분) | 2.0 |
| `baseline_profile` | object \| null | 작업자 기준선 프로파일 참조 | 2.0 |

---

## 4. Platform 3.0 Reserved Fields (Nullable)

Platform 3.0에서 활성화될 예정인 필드입니다. Platform 1.0/2.0에서는 항상 `null`입니다.

| Field | Type | Description | Platform |
|-------|------|-------------|----------|
| `reanalysis_result` | object \| null | AI 재분석 결과 (오탐 재검토) | 3.0 |
| `audit_hash` | string \| null | 이벤트 무결성 해시 (블록체인/해시체인) | 3.0 |
| `rag_reference` | object \| null | RAG 기반 유사 사례 참조 | 3.0 |


---

## 5. EventContext Structure

이벤트에 대한 추가 컨텍스트를 제공하는 중첩 구조입니다.

### 5.1 EventContext

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `video_clip` | VideoClipContext \| null | No | 영상 클립 정보 |
| `sensor_snapshot` | SensorSnapshot \| null | No | 센서 스냅샷 |
| `inference_detail` | InferenceDetail \| null | No | AI 추론 상세 |
| `system_state` | SystemState \| null | No | 시스템 상태 스냅샷 |

### 5.2 VideoClipContext

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `clip_path` | string | Yes | 로컬 클립 파일 경로 |
| `clip_s3_key` | string \| null | No | S3 업로드 키 (업로드 후 채움) |
| `duration_sec` | integer | Yes | 클립 길이 (초) |
| `pre_event_sec` | integer | Yes | 이벤트 전 녹화 시간 |
| `post_event_sec` | integer | Yes | 이벤트 후 녹화 시간 |
| `thumbnail_path` | string \| null | No | 썸네일 이미지 경로 |

### 5.3 SensorSnapshot

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `data_type` | string | Yes | 센서 데이터 유형 |
| `value` | float | Yes | 측정값 |
| `unit` | string | Yes | 단위 (bpm, °C, ppm 등) |
| `threshold` | float | Yes | 초과 기준값 |
| `duration_above_threshold_sec` | integer \| null | No | 기준 초과 지속 시간 |

### 5.4 InferenceDetail

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `model_version` | string | Yes | 모델 버전 |
| `class_id` | integer | Yes | 감지된 클래스 ID |
| `class_label` | string | Yes | 클래스 라벨 |
| `confidence` | float | Yes | 신뢰도 (0.0~1.0) |
| `bbox` | object | Yes | `{x, y, w, h}` 정규화 좌표 |
| `tracker_id` | integer \| null | No | 트래커 객체 ID |
| `frame_number` | integer \| null | No | 감지 프레임 번호 |

### 5.5 SystemState

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `gpu_utilization` | float | Yes | GPU 사용률 (0.0~1.0) |
| `active_pipelines` | integer | Yes | 활성 파이프라인 수 |
| `pending_events` | integer | Yes | 미처리 이벤트 수 |
| `uptime_sec` | integer | Yes | 시스템 가동 시간 (초) |


---

## 6. Validation Rules

### 6.1 Field Constraints

| Rule | Constraint |
|------|-----------|
| `confidence` range | 0.0 ≤ confidence ≤ 1.0 |
| `risk_level` for CRITICAL events | FALL_DETECTED, COLLAPSE_DETECTED, FIRE_DETECTED → must be CRITICAL |
| `worker_id` requirement | HEARTRATE_ABNORMAL, TEMPERATURE_ABNORMAL, BAND_FALL_DETECTED, BAND_DISCONNECTED → worker_id must not be null |
| `model_version` requirement | Vision AI events (FALL, COLLAPSE, ZONE, STILLNESS, HAZARDOUS, FIRE from camera) → must not be null |
| `timestamp` | Must be valid ISO 8601 UTC, not in future (max +5sec tolerance) |

### 6.2 Required Combinations

| event_type | Required Non-null Fields |
|-----------|--------------------------|
| `FALL_DETECTED` | confidence, model_version, context.inference_detail |
| `COLLAPSE_DETECTED` | confidence, model_version, context.inference_detail |
| `ZONE_INTRUSION` | confidence, model_version, context.inference_detail |
| `STILLNESS_DETECTED` | confidence, model_version, context.inference_detail |
| `HAZARDOUS_ACTION` | confidence, model_version, context.inference_detail |
| `FIRE_DETECTED` | confidence (camera) or sensor_snapshot (contact) |
| `HEARTRATE_ABNORMAL` | worker_id, context.sensor_snapshot |
| `TEMPERATURE_ABNORMAL` | worker_id, context.sensor_snapshot |
| `BAND_FALL_DETECTED` | worker_id |
| `BAND_DISCONNECTED` | worker_id |
| `ENV_THRESHOLD_EXCEEDED` | context.sensor_snapshot |
| `DEVICE_OFFLINE` | — |
| `DEVICE_ONLINE` | — |
| `NORMAL_RESTORED` | — |
| `SYSTEM_ALERT` | — |


---

## 7. Examples

### 7.1 FALL_DETECTED Event

```json
{
  "event_id": "EVT-20250519120000-001",
  "site_id": "SITE-001",
  "device_id": "CAM-001",
  "event_type": "FALL_DETECTED",
  "risk_level": "CRITICAL",
  "timestamp": "2025-05-19T12:00:00.123Z",
  "event_state": "ACTIVE",
  "worker_id": null,
  "confidence": 0.92,
  "model_version": "v1.0.0-tao-ds",
  "context": {
    "video_clip": {
      "clip_path": "/data/clips/EVT-20250519120000-001.mp4",
      "clip_s3_key": null,
      "duration_sec": 60,
      "pre_event_sec": 30,
      "post_event_sec": 30,
      "thumbnail_path": "/data/clips/EVT-20250519120000-001.jpg"
    },
    "sensor_snapshot": null,
    "inference_detail": {
      "model_version": "v1.0.0-tao-ds",
      "class_id": 2,
      "class_label": "fall",
      "confidence": 0.92,
      "bbox": { "x": 0.35, "y": 0.45, "w": 0.15, "h": 0.20 },
      "tracker_id": 42,
      "frame_number": 1800
    },
    "system_state": null
  },
  "feedback_type": null,
  "activity_index_history": null,
  "baseline_profile": null,
  "reanalysis_result": null,
  "audit_hash": null,
  "rag_reference": null
}
```

### 7.2 FIRE_DETECTED Event

```json
{
  "event_id": "EVT-20250519121500-003",
  "site_id": "SITE-001",
  "device_id": "FIRE-001",
  "event_type": "FIRE_DETECTED",
  "risk_level": "CRITICAL",
  "timestamp": "2025-05-19T12:15:00.789Z",
  "event_state": "ACTIVE",
  "worker_id": null,
  "confidence": null,
  "model_version": null,
  "context": {
    "video_clip": null,
    "sensor_snapshot": {
      "data_type": "FIRE_CONTACT",
      "value": 1.0,
      "unit": "boolean",
      "threshold": 1.0,
      "duration_above_threshold_sec": null
    },
    "inference_detail": null,
    "system_state": null
  },
  "feedback_type": null,
  "activity_index_history": null,
  "baseline_profile": null,
  "reanalysis_result": null,
  "audit_hash": null,
  "rag_reference": null
}
```

### 7.3 ENV_THRESHOLD_EXCEEDED Event

```json
{
  "event_id": "EVT-20250519123000-007",
  "site_id": "SITE-001",
  "device_id": "ENV-002",
  "event_type": "ENV_THRESHOLD_EXCEEDED",
  "risk_level": "WARNING",
  "timestamp": "2025-05-19T12:30:00.456Z",
  "event_state": "ACTIVE",
  "worker_id": null,
  "confidence": null,
  "model_version": null,
  "context": {
    "video_clip": null,
    "sensor_snapshot": {
      "data_type": "GAS",
      "value": 28.5,
      "unit": "ppm",
      "threshold": 25.0,
      "duration_above_threshold_sec": 120
    },
    "inference_detail": null,
    "system_state": null
  },
  "feedback_type": null,
  "activity_index_history": null,
  "baseline_profile": null,
  "reanalysis_result": null,
  "audit_hash": null,
  "rag_reference": null
}
```

---

## 8. Schema Evolution Rules

| Rule | Description |
|------|-------------|
| **Additive only** | 새 필드 추가만 허용 (기존 필드 제거/변경 금지) |
| **Nullable default** | 새 필드는 항상 nullable, 기존 consumer 영향 없음 |
| **Version marker** | Platform 2.0/3.0 활성화 시 별도 마이그레이션 문서 작성 |
| **Backward compatible** | Platform 1.0 consumer는 Platform 2.0 메시지를 무시 가능 |
