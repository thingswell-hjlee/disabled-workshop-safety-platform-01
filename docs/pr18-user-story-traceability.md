# PR #18 User Story Traceability

> **PR:** feature/aws-cloud-iot-s3-rds → develop
> **세션:** S2 (AWS Cloud SW)
> **기준:** PR #21 Integration Test (docs/integration-session-impact-review.md)
> **테스트 결과:** 94/94 ALL PASSED

---

## 담당 유저스토리 매핑

| User Story | 제목 | PR #21 조치항목 | 상태 |
|-----------|------|----------------|------|
| US-AWS-001 | Edge 이벤트 수신 | 4.1 MQTT payload 명시적 모델 구현 | ✅ PASS |
| US-AWS-002 | 이벤트 DB 저장 | 4.4 PostgreSQL DDL | ✅ PASS |
| US-AWS-003 | 이벤트 목록/상세 API | 4.5 event_state/event_type 검증 | ✅ PASS |
| US-AWS-004 | 장비 상태 저장 | — (Device API) | ✅ PASS |
| US-AWS-005 | MQTT Payload 검증 | 4.1 + 4.2 idempotency_key | ✅ PASS |

---

## US-AWS-001: Edge 이벤트 수신

### Acceptance Criteria

| AC | 내용 | 결과 |
|----|------|------|
| AC-1 | IoTEventPayload 모델에 context_summary 필드 포함 | ✅ PASS |
| AC-2 | IoTEventPayload 모델에 clip_s3_key 필드 포함 | ✅ PASS |
| AC-3 | IoTEventPayload 모델에 idempotency_key 필드 포함 (필수) | ✅ PASS |
| AC-4 | IoTStatusPayload 모델 구현 (safety/{site_id}/status) | ✅ PASS |
| AC-5 | POST /api/v1/events/ingest 엔드포인트 존재 | ✅ PASS |
| AC-6 | 잘못된 payload 수신 시 422 반환 | ✅ PASS |

### 구현 파일

| 파일 | 역할 |
|------|------|
| `apps/dashboard-backend/src/schemas.py` | IoTEventPayload, IoTStatusPayload Pydantic v2 모델 |
| `apps/dashboard-backend/src/api.py` | POST /api/v1/events/ingest, POST /api/v1/edge/status |
| `infra/aws/iot/mock-receiver.py` | Mosquitto 기반 Mock IoT receiver |

### 테스트 명령

```bash
python3 -m pytest apps/dashboard-backend/tests/test_user_stories.py::TestUSAWS001_EdgeEventReceive -v
```

---

## US-AWS-002: 이벤트 DB 저장

### Acceptance Criteria

| AC | 내용 | 결과 |
|----|------|------|
| AC-1 | PostgreSQL DDL 파일 존재 (infra/aws/rds/init-schema.sql) | ✅ PASS |
| AC-2 | events 테이블 정의 (event_id PK) | ✅ PASS |
| AC-3 | idempotency_key UNIQUE 제약 | ✅ PASS |
| AC-4 | site_id, device_id, event_type, risk_level NOT NULL 제약 | ✅ PASS |
| AC-5 | event_type CHECK 제약 (15종) | ✅ PASS |
| AC-6 | risk_level CHECK 제약 (CRITICAL/WARNING/NORMAL) | ✅ PASS |
| AC-7 | CRUD insert에 ON CONFLICT DO NOTHING (중복 방지) | ✅ PASS |
| AC-8 | 중복 이벤트 시 duplicate_skipped 반환 | ✅ PASS |

### 구현 파일

| 파일 | 역할 |
|------|------|
| `infra/aws/rds/init-schema.sql` | PostgreSQL DDL (9개 테이블) |
| `infra/aws/rds/seed-data.sql` | 초기 데이터 (site, devices, workers, models) |
| `apps/dashboard-backend/src/crud.py` | insert_event() — ON CONFLICT DO NOTHING |
| `apps/dashboard-backend/src/database.py` | asyncpg 연결 관리 |

### 테스트 명령

```bash
python3 -m pytest apps/dashboard-backend/tests/test_user_stories.py::TestUSAWS002_EventDBStorage -v
```

---

## US-AWS-003: 이벤트 목록/상세 API

### Acceptance Criteria

| AC | 내용 | 결과 |
|----|------|------|
| AC-1 | GET /api/v1/events (필터, 페이지네이션) | ✅ PASS |
| AC-2 | GET /api/v1/events/{event_id} (상세) | ✅ PASS |
| AC-3 | POST /api/v1/events/{event_id}/acknowledge | ✅ PASS |
| AC-4 | POST /api/v1/events/{event_id}/archive | ✅ PASS |
| AC-5 | POST /api/v1/validate/event (스키마 검증 전용) | ✅ PASS |
| AC-6 | event_type enum 검증 (15종만 허용) | ✅ PASS |
| AC-7 | risk_level enum 검증 (3종만 허용) | ✅ PASS |

### 구현 파일

| 파일 | 역할 |
|------|------|
| `apps/dashboard-backend/src/api.py` | 전체 REST API 엔드포인트 |
| `apps/dashboard-backend/src/crud.py` | get_events(), get_event_by_id(), acknowledge_event(), archive_event() |
| `apps/dashboard-backend/src/schemas.py` | EventResponse, EventListResponse 등 |

### 테스트 명령

```bash
python3 -m pytest apps/dashboard-backend/tests/test_user_stories.py::TestUSAWS003_EventListDetailAPI -v
```

---

## US-AWS-004: 장비 상태 저장

### Acceptance Criteria

| AC | 내용 | 결과 |
|----|------|------|
| AC-1 | GET /api/v1/devices 엔드포인트 | ✅ PASS |
| AC-2 | GET /api/v1/devices/{device_id} 엔드포인트 | ✅ PASS |
| AC-3 | PATCH /api/v1/devices/{device_id}/status 엔드포인트 | ✅ PASS |
| AC-4 | DeviceType enum 6종 (PR #16 기준) | ✅ PASS |
| AC-5 | DeviceStatus enum 4종 | ✅ PASS |
| AC-6 | DDL에 devices 테이블 정의 | ✅ PASS |
| AC-7 | device_type CHECK 제약 | ✅ PASS |

### 구현 파일

| 파일 | 역할 |
|------|------|
| `apps/dashboard-backend/src/api.py` | Device API 엔드포인트 |
| `apps/dashboard-backend/src/crud.py` | get_devices(), get_device_by_id(), update_device_status() |
| `apps/dashboard-backend/src/schemas.py` | DeviceType, DeviceStatus enum |
| `infra/aws/rds/init-schema.sql` | devices 테이블 DDL |

### 테스트 명령

```bash
python3 -m pytest apps/dashboard-backend/tests/test_user_stories.py::TestUSAWS004_DeviceStatus -v
```

---

## US-AWS-005: MQTT Payload 검증

### Acceptance Criteria

| AC | 내용 | 결과 |
|----|------|------|
| AC-1 | 15종 event_type enum 정의 | ✅ PASS |
| AC-2 | 3종 risk_level enum 정의 | ✅ PASS |
| AC-3 | C-001: FALL/COLLAPSE/FIRE → CRITICAL 강제 | ✅ PASS |
| AC-4 | C-003: idempotency_key = {site_id}:{event_id} 강제 | ✅ PASS |
| AC-5 | confidence 범위 0.0~1.0 검증 | ✅ PASS |
| AC-6 | timestamp 미래 시간 거부 (+5초 초과) | ✅ PASS |
| AC-7 | model_version 형식 v{M}.{m}.{p}-{tool}-{target} 검증 | ✅ PASS |
| AC-8 | 유효하지 않은 event_type 거부 | ✅ PASS |
| AC-9 | 유효하지 않은 risk_level 거부 | ✅ PASS |
| AC-10 | event_id 형식 EVT-YYYYMMDDHHmmss-SEQ 검증 | ✅ PASS |
| AC-11 | site_id 형식 SITE-NNN 검증 | ✅ PASS |
| AC-12 | device_id 형식 (CAM|BAND|ENV|FIRE|NVR|ALARM)-NNN 검증 | ✅ PASS |

### 구현 파일

| 파일 | 역할 |
|------|------|
| `apps/dashboard-backend/src/schemas.py` | Pydantic v2 validators (field_validator, model_validator) |
| `infra/aws/iot/mock-receiver.py` | MQTT 수신 시 동일 검증 로직 |

### 테스트 명령

```bash
python3 -m pytest apps/dashboard-backend/tests/test_user_stories.py::TestUSAWS005_MQTTPayloadValidation -v
python3 -m pytest apps/dashboard-backend/tests/test_event_validation.py -v
```

---

## PR #21 조치항목 대응 현황

| PR #21 항목 | 내용 | PR #18 대응 | 상태 |
|------------|------|------------|------|
| 4.1 | MQTT payload 명시적 모델 (context_summary, clip_s3_key, idempotency_key) | `src/schemas.py` IoTEventPayload | ✅ 해결 |
| 4.2 | idempotency_key = {site_id}:{event_id} 형식 | model_validator 구현 | ✅ 해결 |
| 4.3 | cloud-queue priority mapping | Edge 측 책임 (N/A) | — |
| 4.4 | PostgreSQL DDL 작성 | `infra/aws/rds/init-schema.sql` | ✅ 해결 |
| 4.5 | event_type/event_state enum 입력 검증 | Pydantic strict enum 사용 | ✅ 해결 |
| 4.6 | Redis Stream name 참조 | config 기반 (TODO: sdk-common 연동) | ⚠️ TODO |

---

## 전체 테스트 실행 결과

```
$ python3 -m pytest apps/dashboard-backend/tests/ -v
========================== 94 passed in 0.53s ==========================

테스트 구성:
- test_api.py: 4 tests (health, auth, system)
- test_event_api.py: 6 tests (validation endpoint)
- test_event_validation.py: 42 tests (schema validation)
- test_models.py: 6 tests (data models)
- test_user_stories.py: 36 tests (US-AWS-001~005 AC 검증)
```

### 실행 명령 (전체)

```bash
python3 -m pytest apps/dashboard-backend/tests/ -v --tb=short
```

### 실행 명령 (유저스토리별)

```bash
# US-AWS-001
python3 -m pytest apps/dashboard-backend/tests/test_user_stories.py::TestUSAWS001_EdgeEventReceive -v

# US-AWS-002
python3 -m pytest apps/dashboard-backend/tests/test_user_stories.py::TestUSAWS002_EventDBStorage -v

# US-AWS-003
python3 -m pytest apps/dashboard-backend/tests/test_user_stories.py::TestUSAWS003_EventListDetailAPI -v

# US-AWS-004
python3 -m pytest apps/dashboard-backend/tests/test_user_stories.py::TestUSAWS004_DeviceStatus -v

# US-AWS-005
python3 -m pytest apps/dashboard-backend/tests/test_user_stories.py::TestUSAWS005_MQTTPayloadValidation -v
```
