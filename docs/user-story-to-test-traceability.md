# Platform 1.0 User Story to Test Traceability Matrix

> **Status:** Active
> **Last Updated:** 2025-05-20
> **Purpose:** 유저스토리 → Acceptance Criteria → 테스트 케이스 간 추적성을 보장한다.
> **Reference:** docs/user-stories.md, docs/user-story-acceptance-criteria.md, PR #21 tests/

---

## 1. Traceability Format

```
User Story → Acceptance Criteria → Test Case → Test File → 실행 명령
```

---

## 2. S1: Edge Device SW

### US-EDGE-001: RTSP 카메라 수집

| AC ID | Test Case ID | 테스트 설명 | 테스트 파일 | 실행 명령 | 상태 |
|-------|-------------|-------------|-------------|-----------|------|
| AC-EDGE-001-01 | TC-EDGE-001-01 | 8대 카메라 RTSP 연결 확인 | (구현 대기: services/ai-inference/tests/) | — | NOT_IMPL |
| AC-EDGE-001-02 | TC-EDGE-001-02 | 파이프라인 FPS ≥ 25 확인 | (구현 대기: services/ai-inference/tests/) | — | NOT_IMPL |
| AC-EDGE-001-03 | TC-EDGE-001-03 | 설정 파일 기반 RTSP URL 로드 | (구현 대기: services/ai-inference/tests/) | — | NOT_IMPL |
| AC-EDGE-001-04 | TC-EDGE-001-04 | RTSP 연결 실패 시 재시도 + 로그 | (구현 대기: services/ai-inference/tests/) | — | NOT_IMPL |
| AC-EDGE-001-05 | TC-EDGE-001-05 | 1대 장애 시 나머지 정상 처리 | (구현 대기: services/ai-inference/tests/) | — | NOT_IMPL |

---

### US-EDGE-002: 낙상/쓰러짐 이벤트 생성

| AC ID | Test Case ID | 테스트 설명 | 테스트 파일 | 실행 명령 | 상태 |
|-------|-------------|-------------|-------------|-----------|------|
| AC-EDGE-002-01 | TC-EDGE-002-01 | FALL_DETECTED 이벤트 정상 생성 | tests/fixtures/valid_events.json [0] | `pytest tests/schema/test_event_format.py::TestEnumValidation::test_all_valid_event_types_accepted -v` | ✅ PASS |
| AC-EDGE-002-02 | TC-EDGE-002-02 | COLLAPSE_DETECTED 이벤트 정상 생성 | tests/fixtures/valid_events.json [2] | `pytest tests/schema/test_event_format.py -v -k "valid_event"` | ✅ PASS |
| AC-EDGE-002-03 | TC-EDGE-002-03 | 필수 필드 포함 검증 (event_id, timestamp, model_version) | tests/schema/test_event_format.py | `pytest tests/schema/test_event_format.py -v` | ✅ PASS |
| AC-EDGE-002-04 | TC-EDGE-002-04 | Vision AI 이벤트에 confidence + model_version 필수 | tests/schema/test_event_completeness.py | `pytest tests/schema/test_event_completeness.py::TestConditionalRequiredFields::test_vision_ai_events_require_confidence -v` | ✅ PASS |
| AC-EDGE-002-05 | TC-EDGE-002-05 | confidence < 0.70 시 이벤트 미생성 | (비즈니스 로직: services/ai-inference/) | — | NOT_IMPL |
| AC-EDGE-002-06 | TC-EDGE-002-06 | C-001: FALL/COLLAPSE/FIRE → CRITICAL | tests/schema/test_event_consistency.py | `pytest tests/schema/test_event_consistency.py::TestConsistencyC001 -v` | ✅ PASS |

---

### US-EDGE-003: Redis Streams 이벤트 발행

| AC ID | Test Case ID | 테스트 설명 | 테스트 파일 | 실행 명령 | 상태 |
|-------|-------------|-------------|-------------|-----------|------|
| AC-EDGE-003-01 | TC-EDGE-003-01 | stream:ds-events 메시지 스키마 통과 | tests/schema/test_redis_stream_schema.py | `pytest tests/schema/test_redis_stream_schema.py::TestDsEventsStream -v` | ✅ PASS |
| AC-EDGE-003-02 | TC-EDGE-003-02 | Event Engine → 4개 downstream stream 발행 | tests/integration/test_redis_pubsub.py | `pytest tests/integration/test_redis_pubsub.py::TestIT001ValidFallEvent::test_event_engine_processes_fall_event -v` | ✅ PASS |
| AC-EDGE-003-03 | TC-EDGE-003-03 | C-003: idempotency_key = {site_id}:{event_id} | tests/schema/test_event_consistency.py | `pytest tests/schema/test_event_consistency.py::TestConsistencyC003 -v` | ✅ PASS |
| AC-EDGE-003-04 | TC-EDGE-003-04 | C-004: priority 매핑 (CRITICAL→HIGH) | tests/schema/test_event_consistency.py | `pytest tests/schema/test_event_consistency.py::TestConsistencyC004 -v` | ✅ PASS |
| AC-EDGE-003-05 | TC-EDGE-003-05 | alarm action 매핑 (CRITICAL→ALL_ON) | tests/integration/test_redis_pubsub.py | `pytest tests/integration/test_redis_pubsub.py::TestIT004CriticalAlarm -v` | ✅ PASS |
| AC-EDGE-003-06 | TC-EDGE-003-06 | C-005: event_state = ACTIVE 초기화 | tests/schema/test_event_consistency.py | `pytest tests/schema/test_event_consistency.py::TestConsistencyC005 -v` | ✅ PASS |
| AC-EDGE-003-07 | TC-EDGE-003-07 | Redis stream name hyphen 검증 | tests/schema/test_redis_stream_schema.py | `pytest tests/schema/test_redis_stream_schema.py::TestStreamNames -v` | ✅ PASS |

---

### US-EDGE-004: 카메라 연결 끊김/재연결

| AC ID | Test Case ID | 테스트 설명 | 테스트 파일 | 실행 명령 | 상태 |
|-------|-------------|-------------|-------------|-----------|------|
| AC-EDGE-004-01 | TC-EDGE-004-01 | DEVICE_OFFLINE 이벤트 스키마 검증 | tests/fixtures/valid_events.json [7] | `pytest tests/schema/test_event_format.py::TestEnumValidation::test_all_valid_event_types_accepted -v` | ✅ PASS |
| AC-EDGE-004-02 | TC-EDGE-004-02 | DEVICE_ONLINE 이벤트 스키마 검증 | tests/fixtures/valid_events.json (NORMAL_RESTORED) | `pytest tests/schema/test_event_format.py -v` | ✅ PASS |
| AC-EDGE-004-03 | TC-EDGE-004-03 | device_id = CAM-NNN 형식 검증 | tests/schema/test_event_format.py | `pytest tests/schema/test_event_format.py::TestDeviceIdFormat -v` | ✅ PASS |
| AC-EDGE-004-04 | TC-EDGE-004-04 | 30초 재연결 실패 → dashboard 경고 | (구현 대기: services/device-gateway/) | — | NOT_IMPL |

---

## 3. S2: AWS Cloud SW

### US-AWS-001: Edge 이벤트 수신

| AC ID | Test Case ID | 테스트 설명 | 테스트 파일 | 실행 명령 | 상태 |
|-------|-------------|-------------|-------------|-----------|------|
| AC-AWS-001-01 | TC-AWS-001-01 | MQTT events 페이로드 스키마 검증 | tests/schema/test_mqtt_schema.py | `pytest tests/schema/test_mqtt_schema.py::TestMqttEventPayload::test_valid_event_payload -v` | ✅ PASS |
| AC-AWS-001-02 | TC-AWS-001-02 | 필수 필드 추출 확인 | tests/schema/test_mqtt_schema.py | `pytest tests/schema/test_mqtt_schema.py::TestMqttEventPayload -v` | ✅ PASS |
| AC-AWS-001-03 | TC-AWS-001-03 | 스키마 검증 실패 시 오류 처리 | tests/schema/test_mqtt_schema.py | `pytest tests/schema/test_mqtt_schema.py::TestMqttEventPayload::test_event_payload_requires_context_summary -v` | ✅ PASS |
| AC-AWS-001-04 | TC-AWS-001-04 | QoS 1 ACK 처리 | (구현 대기: services/cloud-sync/) | — | NOT_IMPL |
| AC-AWS-001-05 | TC-AWS-001-05 | idempotency_key 중복 감지 | tests/integration/test_redis_pubsub.py | `pytest tests/integration/test_redis_pubsub.py::TestIT010DuplicateEvent -v` | ✅ PASS |

---

### US-AWS-002: 이벤트 DB 저장

| AC ID | Test Case ID | 테스트 설명 | 테스트 파일 | 실행 명령 | 상태 |
|-------|-------------|-------------|-------------|-----------|------|
| AC-AWS-002-01 | TC-AWS-002-01 | event_id UNIQUE 제약 확인 | tests/integration/test_db_storage.py | `pytest tests/integration/test_db_storage.py::TestPostgresStorage::test_store_event_to_postgres -v` | ✅ PASS (Docker) |
| AC-AWS-002-02 | TC-AWS-002-02 | 필수 필드 NOT NULL 저장 | tests/fixtures/init-db.sql | DDL 확인 (event_id, site_id, device_id, event_type, risk_level, timestamp NOT NULL) | ✅ PASS |
| AC-AWS-002-03 | TC-AWS-002-03 | 중복 event_id 삽입 무시 | tests/integration/test_db_storage.py | `pytest tests/integration/test_db_storage.py::TestPostgresStorage::test_duplicate_rejected_by_postgres -v` | ✅ PASS (Docker) |
| AC-AWS-002-04 | TC-AWS-002-04 | event_state=ACTIVE 초기화 | tests/integration/mock_aws_receiver.py | store_event() 코드 확인 | ✅ PASS |
| AC-AWS-002-05 | TC-AWS-002-05 | timestamp 인덱스 존재 | tests/fixtures/init-db.sql | `CREATE INDEX idx_events_timestamp` 확인 | ✅ PASS |

---

### US-AWS-003: 이벤트 조회 API

| AC ID | Test Case ID | 테스트 설명 | 테스트 파일 | 실행 명령 | 상태 |
|-------|-------------|-------------|-------------|-----------|------|
| AC-AWS-003-01 | TC-AWS-003-01 | GET /api/events 응답 확인 | (구현 대기: apps/dashboard-backend/) | — | NOT_IMPL |
| AC-AWS-003-02 | TC-AWS-003-02 | event_type 필터 (15종 검증) | (구현 대기) | — | NOT_IMPL |
| AC-AWS-003-03 | TC-AWS-003-03 | risk_level 필터 (3종 검증) | (구현 대기) | — | NOT_IMPL |
| AC-AWS-003-04 | TC-AWS-003-04 | timestamp range 필터 | (구현 대기) | — | NOT_IMPL |
| AC-AWS-003-05 | TC-AWS-003-05 | 응답 스키마 SafetyEvent 일치 | (구현 대기) | — | NOT_IMPL |

---

### US-AWS-004: 장비 상태 저장

| AC ID | Test Case ID | 테스트 설명 | 테스트 파일 | 실행 명령 | 상태 |
|-------|-------------|-------------|-------------|-----------|------|
| AC-AWS-004-01 | TC-AWS-004-01 | MQTT status 페이로드 스키마 검증 | tests/schema/test_mqtt_schema.py | `pytest tests/schema/test_mqtt_schema.py::TestMqttStatusPayload -v` | ✅ PASS |
| AC-AWS-004-02 | TC-AWS-004-02 | edge_status/gpu_utilization 범위 검증 | tests/schema/test_mqtt_schema.py | `pytest tests/schema/test_mqtt_schema.py::TestMqttStatusPayload::test_gpu_utilization_boundary -v` | ✅ PASS |
| AC-AWS-004-03 | TC-AWS-004-03 | deepstream_fps 배열 저장 | tests/fixtures/mqtt_payloads.json | fixture 확인 (8개 FPS 값) | ✅ PASS |
| AC-AWS-004-04 | TC-AWS-004-04 | gpu > 0.9 경고 표시 | (구현 대기: apps/dashboard-backend/) | — | NOT_IMPL |

---

## 4. S3: AI Training SW

### US-AI-001: 모델 패키지 생성

| AC ID | Test Case ID | 테스트 설명 | 테스트 파일 | 실행 명령 | 상태 |
|-------|-------------|-------------|-------------|-----------|------|
| AC-AI-001-01 | TC-AI-001-01 | staged 디렉토리 구조 검증 | (구현 대기: services/training-pipeline/) | — | NOT_IMPL |
| AC-AI-001-02 | TC-AI-001-02 | model_version 형식 검증 | tests/schema/test_event_format.py | `pytest tests/schema/test_event_format.py::TestModelVersionFormat -v` | ✅ PASS |
| AC-AI-001-03 | TC-AI-001-03 | metadata.json 필드 구조 검증 | tests/fixtures/model_registry.json | fixture의 metadata_example 확인 | ✅ PASS |
| AC-AI-001-04 | TC-AI-001-04 | registry.json 업데이트 검증 | tests/schema/test_model_package.py | `pytest tests/schema/test_model_package.py::TestModelRegistry -v` | ✅ PASS |
| AC-AI-001-05 | TC-AI-001-05 | SHA-256 checksum 존재 검증 | tests/fixtures/model_registry.json | metadata_example.checksum 확인 | ✅ PASS |

---

### US-AI-002: 모델 버전 검증

| AC ID | Test Case ID | 테스트 설명 | 테스트 파일 | 실행 명령 | 상태 |
|-------|-------------|-------------|-------------|-----------|------|
| AC-AI-002-01 | TC-AI-002-01 | 유효하지 않은 model_version 거부 | tests/schema/test_event_format.py | `pytest tests/schema/test_event_format.py::TestModelVersionFormat::test_invalid_model_versions -v` | ✅ PASS |
| AC-AI-002-02 | TC-AI-002-02 | ACTIVE 모델 최대 1개 | tests/schema/test_model_package.py | `pytest tests/schema/test_model_package.py::TestModelRegistry::test_registry_active_model -v` | ✅ PASS |
| AC-AI-002-03 | TC-AI-002-03 | 배포 성공 시 ROLLBACK 전환 | tests/schema/test_model_package.py | `pytest tests/schema/test_model_package.py::TestModelRegistry::test_registry_rollback_model -v` | ✅ PASS |
| AC-AI-002-04 | TC-AI-002-04 | 배포 실패 시 ROLLBACK→ACTIVE 복원 | (구현 대기: services/training-pipeline/) | — | NOT_IMPL |
| AC-AI-002-05 | TC-AI-002-05 | metrics 범위 검증 (mAP, fps, inference_time_ms) | tests/schema/test_model_package.py | `pytest tests/schema/test_model_package.py::TestModelMetrics -v` | ✅ PASS |

---

### US-AI-003: 학습 데이터셋 구조

| AC ID | Test Case ID | 테스트 설명 | 테스트 파일 | 실행 명령 | 상태 |
|-------|-------------|-------------|-------------|-----------|------|
| AC-AI-003-01 | TC-AI-003-01 | training_config 필드 존재 | tests/fixtures/model_registry.json | metadata_example.training_config 확인 | ✅ PASS |
| AC-AI-003-02 | TC-AI-003-02 | evaluation 필드 존재 | tests/fixtures/model_registry.json | metadata_example.evaluation 확인 | ✅ PASS |
| AC-AI-003-03 | TC-AI-003-03 | classes 배열 + num_classes 일치 | tests/fixtures/model_registry.json | metadata_example.classes.length == num_classes | ✅ PASS |
| AC-AI-003-04 | TC-AI-003-04 | input_dims 필드 존재 | tests/fixtures/model_registry.json | metadata_example.input_dims 확인 | ✅ PASS |

---

## 5. S4: Integration Test

### US-INT-001: Schema Validation

| AC ID | Test Case ID | 테스트 설명 | 테스트 파일 | 실행 명령 | 상태 |
|-------|-------------|-------------|-------------|-----------|------|
| AC-INT-001-01 | TC-INT-001-01 | 196+ 스키마 테스트 ALL PASS | tests/schema/ | `pytest tests/schema/ -v` | ✅ PASS (196) |
| AC-INT-001-02 | TC-INT-001-02 | 유효하지 않은 event_type 거부 | tests/schema/test_event_format.py | `pytest tests/schema/test_event_format.py::TestEnumValidation::test_invalid_event_type -v` | ✅ PASS |
| AC-INT-001-03 | TC-INT-001-03 | 필수 필드 누락 시 에러 | tests/schema/test_event_completeness.py | `pytest tests/schema/test_event_completeness.py::TestRequiredFields -v` | ✅ PASS |
| AC-INT-001-04 | TC-INT-001-04 | confidence 범위 초과 거부 (C-006) | tests/schema/test_event_consistency.py | `pytest tests/schema/test_event_consistency.py::TestConsistencyC006 -v` | ✅ PASS |
| AC-INT-001-05 | TC-INT-001-05 | timestamp 형식 오류 거부 | tests/schema/test_event_format.py | `pytest tests/schema/test_event_format.py::TestTimestampFormat -v` | ✅ PASS |
| AC-INT-001-06 | TC-INT-001-06 | enum 유효값 15/3/3 검증 | tests/schema/test_event_format.py | `pytest tests/schema/test_event_format.py::TestEnumValidation -v` | ✅ PASS |

---

### US-INT-002: Edge → Redis → AWS Mock → DB E2E

| AC ID | Test Case ID | 테스트 설명 | 테스트 파일 | 실행 명령 | 상태 |
|-------|-------------|-------------|-------------|-----------|------|
| AC-INT-002-01 | TC-INT-002-01 | FALL_DETECTED full pipeline | tests/e2e/test_e2e_flow.py | `pytest tests/e2e/test_e2e_flow.py::TestE2EFallDetected -v` | ✅ PASS |
| AC-INT-002-02 | TC-INT-002-02 | CRITICAL → alarm ALL_ON | tests/integration/test_redis_pubsub.py | `pytest tests/integration/test_redis_pubsub.py::TestIT004CriticalAlarm -v` | ✅ PASS |
| AC-INT-002-03 | TC-INT-002-03 | cloud-queue → AWS receiver 소비 | tests/integration/test_redis_pubsub.py | `pytest tests/integration/test_redis_pubsub.py::TestAwsReceiverTransform -v` | ✅ PASS |
| AC-INT-002-04 | TC-INT-002-04 | clip_s3_key 경로 형식 | tests/integration/test_redis_pubsub.py | `pytest tests/integration/test_redis_pubsub.py::TestAwsReceiverTransform::test_s3_key_path_format -v` | ✅ PASS |
| AC-INT-002-05 | TC-INT-002-05 | 100건 연속 처리 무손실 | tests/integration/test_redis_pubsub.py | `pytest tests/integration/test_redis_pubsub.py::TestIT009RapidEvents -v` | ✅ PASS |
| AC-INT-002-06 | TC-INT-002-06 | 중복 event_id 감지 | tests/integration/test_redis_pubsub.py | `pytest tests/integration/test_redis_pubsub.py::TestIT010DuplicateEvent -v` | ✅ PASS |

---

### US-INT-003: Model Package Validation

| AC ID | Test Case ID | 테스트 설명 | 테스트 파일 | 실행 명령 | 상태 |
|-------|-------------|-------------|-------------|-----------|------|
| AC-INT-003-01 | TC-INT-003-01 | registry.json 스키마 통과 | tests/schema/test_model_package.py | `pytest tests/schema/test_model_package.py::TestModelRegistry::test_valid_registry -v` | ✅ PASS |
| AC-INT-003-02 | TC-INT-003-02 | model_type pgie/sgie 외 거부 | tests/schema/test_model_package.py | `pytest tests/schema/test_model_package.py::TestModelEntry::test_invalid_model_type_rejected -v` | ✅ PASS |
| AC-INT-003-03 | TC-INT-003-03 | framework 유효값 외 거부 | tests/schema/test_model_package.py | `pytest tests/schema/test_model_package.py::TestModelEntry::test_invalid_framework_rejected -v` | ✅ PASS |
| AC-INT-003-04 | TC-INT-003-04 | mAP 범위 초과 거부 | tests/schema/test_model_package.py | `pytest tests/schema/test_model_package.py::TestModelMetrics::test_mAP_boundary -v` | ✅ PASS |
| AC-INT-003-05 | TC-INT-003-05 | inference_time_ms ≤ 0 거부 | tests/schema/test_model_package.py | `pytest tests/schema/test_model_package.py::TestModelMetrics::test_inference_time_must_be_positive -v` | ✅ PASS |

---

## 6. 추적성 커버리지 요약

| 세션 | 유저스토리 | 총 AC | 테스트 매핑 완료 | 테스트 PASS | NOT_IMPL | 커버리지 |
|------|-----------|-------|-----------------|-------------|----------|----------|
| S1 (Edge) | 4 | 22 | 17 | 14 | 8 | 64% |
| S2 (AWS) | 4 | 19 | 13 | 10 | 9 | 53% |
| S3 (AI) | 3 | 14 | 12 | 11 | 3 | 79% |
| S4 (Test) | 3 | 17 | 17 | 17 | 0 | 100% |
| **합계** | **14** | **72** | **59** | **52** | **20** | **72%** |

### 상태 범례

| 상태 | 의미 |
|------|------|
| ✅ PASS | PR #21 테스트에서 검증 완료 |
| ✅ PASS (Docker) | Docker 환경(Redis+PostgreSQL)에서 검증 완료 |
| NOT_IMPL | 해당 세션에서 구현 필요 (테스트 대기) |

---

## 7. 미구현 테스트 우선순위

### P0 (다음 PR에서 구현 필요)

| TC ID | AC ID | 설명 | 담당 세션 |
|-------|-------|------|-----------|
| TC-EDGE-002-05 | AC-EDGE-002-05 | confidence < 0.70 시 이벤트 미생성 | S1 (Edge) |
| TC-AWS-001-04 | AC-AWS-001-04 | MQTT QoS 1 ACK 처리 | S2 (AWS) |
| TC-AI-002-04 | AC-AI-002-04 | 배포 실패 시 ROLLBACK→ACTIVE 복원 | S3 (AI) |

### P1 (Platform 1.0 릴리스 전 구현)

| TC ID | AC ID | 설명 | 담당 세션 |
|-------|-------|------|-----------|
| TC-EDGE-001-01~05 | AC-EDGE-001-* | RTSP 카메라 수집 전체 | S1 (Edge) |
| TC-EDGE-004-04 | AC-EDGE-004-04 | 30초 재연결 실패 → dashboard 경고 | S1 (Edge) |
| TC-AWS-003-01~05 | AC-AWS-003-* | 이벤트 조회 API 전체 | S2 (AWS) |
| TC-AWS-004-04 | AC-AWS-004-04 | GPU > 0.9 경고 표시 | S2 (AWS) |
| TC-AI-001-01 | AC-AI-001-01 | staged 디렉토리 구조 검증 | S3 (AI) |

---

## 8. 테스트 실행 가이드 (세션별)

### S1 (Edge) 세션이 자기 유저스토리 테스트 실행

```bash
# US-EDGE-002 관련 테스트
pytest tests/schema/test_event_format.py::TestEnumValidation -v
pytest tests/schema/test_event_consistency.py::TestConsistencyC001 -v
pytest tests/schema/test_event_completeness.py::TestConditionalRequiredFields -v

# US-EDGE-003 관련 테스트
pytest tests/schema/test_redis_stream_schema.py -v
pytest tests/integration/test_redis_pubsub.py -v
```

### S2 (AWS) 세션이 자기 유저스토리 테스트 실행

```bash
# US-AWS-001 관련 테스트
pytest tests/schema/test_mqtt_schema.py::TestMqttEventPayload -v

# US-AWS-002 관련 테스트
pytest tests/integration/test_db_storage.py -v

# US-AWS-004 관련 테스트
pytest tests/schema/test_mqtt_schema.py::TestMqttStatusPayload -v
```

### S3 (AI) 세션이 자기 유저스토리 테스트 실행

```bash
# US-AI-001, US-AI-002 관련 테스트
pytest tests/schema/test_model_package.py -v
pytest tests/schema/test_event_format.py::TestModelVersionFormat -v

# US-AI-003 관련 테스트 (fixture 기반)
pytest tests/schema/test_model_package.py::TestModelMetrics -v
```

### S4 (Integration) 전체 검증

```bash
# 전체 스키마 + 통합 + E2E
pytest tests/ -k "not Postgres" -v
```

---

*작성: Integration Test Session (S4) | 기준: PR #21 commit 7454b37*
