# Integration Session Impact Review

> **검토일:** 2025-05-20
> **기준:** PR #21 Integration Test (feature/integration-schema-validation)
> **참조 스키마:** PR #16 동결 (docs/interface-schema.md, event-message-schema.md, redis-streams-schema.md, aws-iot-message-schema.md, model-package-schema.md)

---

## 1. 통합시험 결과 요약

| 테스트 카테고리 | 테스트 수 | 결과 |
|----------------|-----------|------|
| Schema Validation (format/completeness/consistency/boundary) | 196 | ✅ ALL PASSED |
| Integration (Redis pub/sub, DB storage) | 20 | ✅ ALL PASSED |
| E2E Simulator (full pipeline) | 11 | ✅ ALL PASSED |
| **합계** | **227** | **✅ ALL PASSED** |

PR #21 자체 테스트는 모두 통과합니다.
그러나 **다른 세션(PR #18/19/20)의 구현 코드가 이 테스트를 통과할 수 있는지** 점검한 결과,
아래와 같은 불일치가 확인되었습니다.

---

## 2. 세션별 PASS / FIX_REQUIRED / TEST_GAP 판정 종합

| 점검 항목 | PR #19 Edge | PR #18 AWS | PR #20 Training |
|-----------|:-----------:|:----------:|:---------------:|
| event_type enum 호환 | ⚠️ FIX_REQUIRED | ⚠️ TEST_GAP | N/A |
| risk_level 매핑 (C-001) | ⚠️ FIX_REQUIRED | ⚠️ TEST_GAP | N/A |
| model_version 형식 | ⚠️ FIX_REQUIRED | N/A | ⚠️ FIX_REQUIRED |
| Redis stream name | ⚠️ FIX_REQUIRED | ⚠️ TEST_GAP | N/A |
| Redis message 필드 | ⚠️ FIX_REQUIRED | N/A | N/A |
| DeviceType enum | ⚠️ FIX_REQUIRED | N/A | N/A |
| AlarmAction enum | ⚠️ FIX_REQUIRED | N/A | N/A |
| MQTT payload 모델 | N/A | ⚠️ FIX_REQUIRED | ⚠️ TEST_GAP |
| idempotency_key 형식 | N/A | ⚠️ FIX_REQUIRED | N/A |
| PostgreSQL DDL | N/A | ⚠️ FIX_REQUIRED | N/A |
| registry.json 구조 | N/A | N/A | ⚠️ FIX_REQUIRED |
| model status enum | N/A | N/A | ⚠️ FIX_REQUIRED |
| E2E pipeline adapter | ⚠️ FIX_REQUIRED | ⚠️ BLOCKED | ⚠️ BLOCKED |

---

## 3. PR #19 Edge Device SW — 조치 필요사항

### 3.1 FIX_REQUIRED: event_type enum (services/ai-inference/src/models.py)

**현재 상태:** `ABNORMAL_BEHAVIOR` 포함, `COLLAPSE_DETECTED`/`STILLNESS_DETECTED`/`HAZARDOUS_ACTION` 누락 (13종)
**PR #16 기준:** 15종 (ABNORMAL_BEHAVIOR 제거, 3종 추가)

```python
# 수정 필요 — 이미 PR #21에서 수정 완료된 버전 참고:
# packages/sdk-common/src/constants.py의 EventType enum 사용
```

**검증 명령:** `pytest tests/schema/test_event_format.py::TestEnumValidation -v`

### 3.2 FIX_REQUIRED: risk_level 매핑 (RISK_CLASSIFICATION)

**현재 상태:** CRITICAL = [FALL, ZONE_INTRUSION, FIRE, HEARTRATE_ABNORMAL, BAND_FALL_DETECTED] (5종)
**PR #16 C-001:** CRITICAL = [FALL_DETECTED, COLLAPSE_DETECTED, FIRE_DETECTED] (3종만)

| event_type | 현재 | PR #16 기준 |
|------------|------|------------|
| ZONE_INTRUSION | CRITICAL ❌ | WARNING |
| HEARTRATE_ABNORMAL | CRITICAL ❌ | WARNING |
| BAND_FALL_DETECTED | CRITICAL ❌ | WARNING |
| COLLAPSE_DETECTED | 없음 ❌ | CRITICAL |
| STILLNESS_DETECTED | 없음 ❌ | WARNING |
| HAZARDOUS_ACTION | 없음 ❌ | WARNING |

**검증 명령:** `pytest tests/schema/test_event_consistency.py::TestConsistencyC001 -v`

### 3.3 FIX_REQUIRED: model_version 형식 (services/ai-inference/src/api.py)

**현재 상태:** `"v1.0.0-edge"` (2-segment suffix)
**PR #16 기준:** `"v1.0.0-tao-ds"` — pattern: `^v\d+\.\d+\.\d+-(tao|pretrained|custom)-(ds|cloud)$`

**수정 대상:**
- `services/ai-inference/src/api.py` line: `"model_version": "v1.0.0-edge"`
- `services/training-pipeline` 전체 (아래 S3 참조)

**검증 명령:** `pytest tests/schema/test_event_format.py::TestModelVersionFormat -v`

### 3.4 FIX_REQUIRED: Redis Stream names (services/device-gateway)

**현재 상태:** `stream:frames`, `stream:bio`, `stream:events`, `stream:cloud_queue` (underscore)
**PR #16 기준:** `stream:ds-events`, `stream:sensors`, `stream:cloud-queue` (hyphen)

| 현재 | PR #16 |
|------|--------|
| `stream:frames` | ❌ 없음 (frames는 DeepStream 내부 처리) |
| `stream:bio` | ❌ → `stream:sensors` |
| `stream:events` | ❌ → `stream:ds-events` |
| `stream:cloud_queue` | ❌ → `stream:cloud-queue` |

**수정 대상:** `packages/sdk-common/src/constants.py` REDIS_STREAMS (이미 PR #21에서 수정됨)

**검증 명령:** `pytest tests/schema/test_redis_stream_schema.py::TestStreamNames -v`

### 3.5 FIX_REQUIRED: Redis message 필드 구조 (FrameMessage, BioMessage, SensorMessage)

**현재 상태:** `services/device-gateway/src/models.py`의 메시지 모델에 `event_id`, `event_type` 필드 없음
**PR #16 기준:** `stream:sensors` 메시지에 `event_id`, `site_id`, `device_id`, `worker_id`, `event_type`, `timestamp`, `data_type`, `value`, `source` 필수

**수정 대상:** `services/device-gateway/src/models.py`
- `SensorMessage` → PR #16 `stream:sensors` 스키마 적용
- `BioMessage` → PR #16 `stream:sensors` 스키마로 통합
- `FireContactMessage` → PR #16 `stream:sensors` source=FIRE_CONTACT로 통합

**검증 명령:** `pytest tests/schema/test_redis_stream_schema.py::TestSensorsStream -v`

### 3.6 FIX_REQUIRED: DeviceType.ALARM → ALARM_DEVICE

**현재 상태:** `services/device-gateway/src/models.py` — `DeviceType.ALARM = "ALARM"`
**PR #16 기준:** `ALARM_DEVICE`

**검증 명령:** `from tests.schema.models import VALID_DEVICE_TYPES; assert "ALARM_DEVICE" in ...`

### 3.7 FIX_REQUIRED: AlarmAction enum (services/alarm-controller/src/models.py)

**현재 상태:** 6종 (SIREN_ON, SIREN_OFF, LIGHT_ON, LIGHT_OFF, ALL_ON, ALL_OFF)
**PR #16 기준:** 4종 (SIREN_ON, LIGHT_ON, ALL_ON, ALL_OFF) — `SIREN_OFF`/`LIGHT_OFF` 없음

**검증 명령:** `pytest tests/schema/test_redis_stream_schema.py::TestAlarmsStream -v`

---

## 4. PR #18 AWS Cloud SW — 조치 필요사항

### 4.1 FIX_REQUIRED: MQTT payload 명시적 모델 구현

**현재 상태:** `services/cloud-sync/src/models.py`에 MQTT 페이로드용 모델 클래스 없음
**PR #16 기준:** `safety/{site_id}/events` payload에 `context_summary`, `clip_s3_key`, `idempotency_key` 필수

**구현 필요:**
```python
# 참고: tests/schema/models.py → MqttEventPayload, MqttStatusPayload, MqttModelDeployCommand
```

**검증 명령:** `pytest tests/schema/test_mqtt_schema.py -v`

### 4.2 FIX_REQUIRED: idempotency_key 형식

**현재 상태:** `QueuedEvent.idempotency_key = ""` (빈 문자열 기본값)
**PR #16 C-003:** 반드시 `{site_id}:{event_id}` 형식 (예: `SITE-001:EVT-20250519120000-001`)

**수정 대상:** `services/cloud-sync/src/models.py` — `QueuedEvent`
**검증 명령:** `pytest tests/schema/test_event_consistency.py::TestConsistencyC003 -v`

### 4.3 FIX_REQUIRED: QueuedEvent 필드 구조

**현재 상태:** `event_type`, `risk_level`, `timestamp` 필드가 `payload` dict 내부에 매립됨
**PR #16 기준:** `stream:cloud-queue` 메시지에 `event_type`, `risk_level`, `timestamp` top-level 필수

**검증 명령:** `pytest tests/schema/test_redis_stream_schema.py::TestCloudQueueStream -v`

### 4.4 FIX_REQUIRED: PostgreSQL DDL (database/)

**현재 상태:** `database/` 폴더에 README만 존재, 실제 DDL 없음
**PR #16 기준:** `event_id` UNIQUE 제약, 필수 필드 (site_id, device_id, event_type, risk_level, timestamp, event_state) NOT NULL

**참고:** `tests/fixtures/init-db.sql`에 최소 DDL 존재 → 이를 `database/migrations/001-create-events.sql`로 이관 필요

**검증 명령:** `pytest tests/integration/test_db_storage.py::TestPostgresStorage -v`

### 4.5 TEST_GAP: dashboard-backend event_state/event_type 검증 로직

**현재 상태:** API endpoint에서 event_type/risk_level enum 검증 없음 (아무 문자열이나 허용)
**PR #16 기준:** 15종 event_type, 3종 risk_level, 3종 event_state만 유효

**권장:** Pydantic response model 또는 입력 검증에 `tests/schema/models.py`의 enum 세트 활용

### 4.6 TEST_GAP: Redis Stream name 참조

**현재 상태:** `services/cloud-sync/src/api.py`에서 Redis stream 이름 하드코딩 없음 (아직 구현 전)
**리스크:** 구현 시 `stream:cloud_queue` (underscore) 사용 가능성

**예방:** `packages/sdk-common/src/constants.py`의 `REDIS_STREAMS` dict import 사용 권장

---

## 5. PR #20 AI Training SW — 조치 필요사항

### 5.1 FIX_REQUIRED: model_version 형식

**현재 상태:**
- `PipelineStatus.active_model_version = "v1.0.0-edge"`
- `ModelArtifact.model_version` 예시: `"v1.1.0"`, `"v1.1.0-edge"`
- `DeploymentStatus.current_model = "v1.0.0-edge"`

**PR #16 기준:** `^v\d+\.\d+\.\d+-(tao|pretrained|custom)-(ds|cloud)$`
- tool: `tao` | `pretrained` | `custom`
- target: `ds` | `cloud`

| 현재 | PR #16 올바른 형식 |
|------|-------------------|
| `v1.0.0-edge` | `v1.0.0-tao-ds` |
| `v1.1.0` | `v1.1.0-tao-ds` |
| `v0.9.0-edge` | `v0.9.0-pretrained-ds` |

**수정 대상:**
- `services/training-pipeline/src/models.py` — PipelineStatus, ModelArtifact, DeploymentStatus
- `services/training-pipeline/src/api.py` — API 응답의 model_version
- `services/training-pipeline/tests/` — 테스트 fixture

**검증 명령:** `pytest tests/schema/test_event_format.py::TestModelVersionFormat -v`

### 5.2 FIX_REQUIRED: model_type enum

**현재 상태:** `"object_detection"`, `"fall_detection"`, `"behavior_analysis"`, `"zone_monitor"`
**PR #16 기준:** `"pgie"` | `"sgie"` (2종만)

**수정 대상:** `services/training-pipeline/src/models.py` — `ModelType` enum, `ModelArtifact.model_type`
**검증 명령:** `pytest tests/schema/test_model_package.py::TestModelEntry -v`

### 5.3 FIX_REQUIRED: registry.json 구현

**현재 상태:** `/models/registry.json` 파일 미존재
**PR #16 기준:** `model-package-schema.md`에 정의된 registry.json 구조 필수

```json
{
  "schema_version": "1.0",
  "site_id": "SITE-001",
  "last_updated": "...",
  "models": [{ "model_version": "v1.0.0-tao-ds", "model_type": "pgie", ... }]
}
```

**참고 fixture:** `tests/fixtures/model_registry.json`
**검증 명령:** `pytest tests/schema/test_model_package.py::TestModelRegistry -v`

### 5.4 FIX_REQUIRED: DeploymentStatus.state enum (대문자)

**현재 상태:** `"active"` | `"deploying"` | `"rolling_back"` | `"failed"` (소문자)
**PR #16 기준:** `"ACTIVE"` | `"STAGED"` | `"DEPLOYING"` | `"FAILED"` | `"ROLLBACK"` (대문자)

**수정 대상:** `services/training-pipeline/src/models.py` — DeploymentStatus.state
**검증 명령:** `pytest tests/schema/test_model_package.py::TestModelEntry::test_valid_model_statuses -v`

### 5.5 FIX_REQUIRED: precision/framework enum 분리

**현재 상태:** `OptimizationType` enum에 framework와 precision이 혼합 (`TensorRT_FP16`, `TensorRT_INT8`, `ONNX`)
**PR #16 기준:**
- `precision`: `"FP16"` | `"FP32"` | `"INT8"` (별도)
- `framework`: `"TAO"` | `"PyTorch"` | `"TensorFlow"` | `"ONNX"` (별도)

**수정 대상:** `services/training-pipeline/src/models.py` — OptimizationType → Precision + Framework 분리

### 5.6 TEST_GAP: MQTT models 토픽 구현

**현재 상태:** MQTT `safety/{site_id}/models` 토픽의 DEPLOY/ROLLBACK/STATUS_REQUEST 구현 없음
**PR #16 기준:** Cloud→Edge 배포 명령, Edge→Cloud 상태 보고 구현 필요

**참고 모델:** `tests/schema/models.py` → `MqttModelDeployCommand`, `MqttModelStatusReport`
**검증 명령:** `pytest tests/schema/test_mqtt_schema.py::TestMqttModelPayload -v`

---

## 6. Integration Test 세션(S4) 자체 보강 필요사항

| 항목 | 상태 | 설명 |
|------|------|------|
| Edge → Event Engine adapter 테스트 | TEST_GAP | stream:ds-events 실제 소비 후 SafetyEvent 변환 테스트 부재 |
| Cloud Sync consumer 테스트 | TEST_GAP | stream:cloud-queue 소비 → MQTT 발행 adapter 미구현 |
| Model deploy pipeline 테스트 | TEST_GAP | MQTT models → edge model swap 흐름 미검증 |
| Load test (1000건+) | TEST_GAP | 현재 100건으로 축소, nightly job 별도 필요 |
| Network failure simulation | TEST_GAP | 오프라인 큐 동작 검증 미구현 |
| Timestamp ordering (C-009) | TEST_GAP | 이벤트 시간 ≤ alarm/dashboard/cloud 시간 미검증 |

---

## 7. 우선순위

### P0 (병합 전 필수 — 다른 세션이 PR #21 테스트를 통과하려면)

| 순위 | 세션 | 수정 항목 | 영향도 |
|------|------|-----------|--------|
| 1 | S1 (Edge) | event_type enum 15종 정렬 + RISK_CLASSIFICATION C-001 | 전체 파이프라인 |
| 2 | S1 (Edge) | Redis stream name 일치 (hyphen) | 메시지 라우팅 |
| 3 | S3 (Training) | model_version 형식 `v{M}.{m}.{p}-{tool}-{target}` | 모델 배포 |
| 4 | S2 (AWS) | idempotency_key `{site_id}:{event_id}` 형식 | 중복 제거 |

### P1 (릴리스 전 필수)

| 순위 | 세션 | 수정 항목 |
|------|------|-----------|
| 5 | S1 (Edge) | stream:sensors 메시지 필드 구조 정렬 |
| 6 | S1 (Edge) | AlarmAction 4종 정렬 (SIREN_OFF/LIGHT_OFF 제거) |
| 7 | S2 (AWS) | MQTT payload 모델 구현 (context_summary, clip_s3_key) |
| 8 | S2 (AWS) | PostgreSQL DDL 작성 (database/migrations/) |
| 9 | S3 (Training) | registry.json 구현 + model_type pgie/sgie |
| 10 | S3 (Training) | DeploymentStatus.state 대문자 enum |

### P2 (Platform 1.0 완성)

| 순위 | 세션 | 수정 항목 |
|------|------|-----------|
| 11 | S1 (Edge) | DeviceType.ALARM → ALARM_DEVICE |
| 12 | S3 (Training) | MQTT models 토픽 adapter 구현 |
| 13 | S2 (AWS) | dashboard event_type/event_state 입력 검증 |
| 14 | S4 (Test) | C-009 timestamp ordering 테스트 |
| 15 | S4 (Test) | Network failure simulation 테스트 |

---

## 8. 다음 PR 제안

| PR | 세션 | 제목 | 내용 |
|----|------|------|------|
| PR #22 | S1 (Edge) | `fix: PR #16 스키마 정렬 — event_type, Redis streams, AlarmAction` | P0 #1,2 + P1 #5,6,11 |
| PR #23 | S3 (Training) | `fix: PR #16 스키마 정렬 — model_version, registry.json, deploy state` | P0 #3 + P1 #9,10 + P2 #12 |
| PR #24 | S2 (AWS) | `fix: PR #16 스키마 정렬 — idempotency_key, MQTT payload, DB DDL` | P0 #4 + P1 #7,8 + P2 #13 |
| PR #25 | S4 (Test) | `feat: 통합시험 보강 — adapter test, load test, C-009` | P2 #14,15 + 자체 보강 |

### 권장 병합 순서

```
PR #21 (Integration Test) → PR #22 (Edge fix) → PR #23 (Training fix) → PR #24 (AWS fix) → PR #25 (Test 보강)
```

---

## 부록: 검증 명령 모음

```bash
# 전체 스키마 검증 (외부 의존성 없음)
pytest tests/schema/ -v

# 특정 규칙 검증
pytest tests/schema/test_event_consistency.py::TestConsistencyC001 -v  # CRITICAL 매핑
pytest tests/schema/test_event_consistency.py::TestConsistencyC003 -v  # idempotency_key
pytest tests/schema/test_event_consistency.py::TestConsistencyC004 -v  # priority 매핑

# Redis stream 스키마
pytest tests/schema/test_redis_stream_schema.py -v

# MQTT 페이로드
pytest tests/schema/test_mqtt_schema.py -v

# 모델 패키지
pytest tests/schema/test_model_package.py -v

# 전체 E2E (mock 기반)
pytest tests/e2e/ -v
```

---

*작성: Integration Test Session (S4) | 기준: PR #21 commit 7454b37*
