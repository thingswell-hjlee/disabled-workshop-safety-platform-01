# Platform 1.0 User Story Acceptance Criteria

> **Status:** Active
> **Last Updated:** 2025-05-20
> **Format:** EARS (Easy Approach to Requirements Syntax)
> **Reference:** docs/user-stories.md, PR #16 동결 스키마

---

## EARS Format

```
WHEN [조건/트리거],
THE SYSTEM SHALL [기대 동작].
```

변형:
- **Ubiquitous:** THE SYSTEM SHALL [항상 충족해야 하는 조건].
- **Event-driven:** WHEN [이벤트 발생], THE SYSTEM SHALL [반응].
- **State-driven:** WHILE [상태], THE SYSTEM SHALL [동작].
- **Unwanted behavior:** IF [비정상 조건], THEN THE SYSTEM SHALL [대응].

---

## 1. Edge Device SW (S1)

### AC-EDGE-001: RTSP 카메라 수집

| AC ID | 조건 | 기대 동작 |
|-------|------|-----------|
| AC-EDGE-001-01 | WHEN DeepStream 파이프라인이 시작되면, | THE SYSTEM SHALL 설정된 8대 카메라의 RTSP 스트림에 연결한다. |
| AC-EDGE-001-02 | WHILE 카메라가 정상 연결 상태이면, | THE SYSTEM SHALL 각 파이프라인에서 25 FPS 이상의 프레임을 처리한다. |
| AC-EDGE-001-03 | THE SYSTEM SHALL | RTSP 연결 정보를 환경설정 파일에서 읽어온다 (하드코딩 금지). |
| AC-EDGE-001-04 | IF RTSP 연결이 실패하면, | THEN THE SYSTEM SHALL 5초 간격으로 재연결을 시도하고 로그를 남긴다. |
| AC-EDGE-001-05 | WHEN 카메라 1대가 장애 상태여도, | THE SYSTEM SHALL 나머지 카메라의 처리를 중단하지 않는다. |

---

### AC-EDGE-002: 낙상/쓰러짐 이벤트 생성

| AC ID | 조건 | 기대 동작 |
|-------|------|-----------|
| AC-EDGE-002-01 | WHEN AI 모델이 낙상(fall)을 감지하고 confidence ≥ 0.70이면, | THE SYSTEM SHALL event_type=FALL_DETECTED, risk_level=CRITICAL 이벤트를 생성한다. |
| AC-EDGE-002-02 | WHEN AI 모델이 쓰러짐(collapse)을 감지하고 confidence ≥ 0.70이면, | THE SYSTEM SHALL event_type=COLLAPSE_DETECTED, risk_level=CRITICAL 이벤트를 생성한다. |
| AC-EDGE-002-03 | THE SYSTEM SHALL | 생성된 이벤트에 event_id(`^EVT-\d{14}-\d{3}$`), site_id, device_id, timestamp(ISO 8601 UTC ms), model_version(`^v\d+\.\d+\.\d+-(tao|pretrained|custom)-(ds|cloud)$`) 필드를 포함한다. |
| AC-EDGE-002-04 | THE SYSTEM SHALL | FALL_DETECTED, COLLAPSE_DETECTED 이벤트에 confidence(0.0~1.0)와 model_version을 반드시 포함한다. |
| AC-EDGE-002-05 | WHEN confidence < 0.70이면, | THE SYSTEM SHALL 이벤트를 생성하지 않는다. |
| AC-EDGE-002-06 | THE SYSTEM SHALL | FALL_DETECTED, COLLAPSE_DETECTED, FIRE_DETECTED에 대해 반드시 risk_level=CRITICAL을 할당한다 (C-001 규칙). |

---

### AC-EDGE-003: Redis Streams 이벤트 발행

| AC ID | 조건 | 기대 동작 |
|-------|------|-----------|
| AC-EDGE-003-01 | WHEN 이벤트가 생성되면, | THE SYSTEM SHALL stream:ds-events에 DsEventsMessage 스키마에 맞는 메시지를 발행한다. |
| AC-EDGE-003-02 | WHEN Event Engine이 이벤트를 처리하면, | THE SYSTEM SHALL stream:alarms, stream:dashboard, stream:cloud-queue, stream:clip-trigger에 각각의 스키마에 맞는 메시지를 발행한다. |
| AC-EDGE-003-03 | THE SYSTEM SHALL | stream:cloud-queue 메시지에 idempotency_key를 `{site_id}:{event_id}` 형식으로 포함한다 (C-003). |
| AC-EDGE-003-04 | THE SYSTEM SHALL | stream:cloud-queue의 priority를 risk_level에 따라 매핑한다: CRITICAL→HIGH, WARNING→NORMAL, NORMAL→LOW (C-004). |
| AC-EDGE-003-05 | THE SYSTEM SHALL | stream:alarms 메시지의 action을 CRITICAL→ALL_ON, WARNING→LIGHT_ON, NORMAL→ALL_OFF로 설정한다. |
| AC-EDGE-003-06 | THE SYSTEM SHALL | 모든 새 이벤트의 event_state를 ACTIVE로 초기화한다 (C-005). |
| AC-EDGE-003-07 | THE SYSTEM SHALL | Redis stream name에 hyphen 구분자를 사용한다: stream:ds-events, stream:cloud-queue, stream:clip-trigger. |

---

### AC-EDGE-004: 카메라 연결 끊김/재연결

| AC ID | 조건 | 기대 동작 |
|-------|------|-----------|
| AC-EDGE-004-01 | WHEN 카메라 연결이 끊기면, | THE SYSTEM SHALL event_type=DEVICE_OFFLINE, risk_level=NORMAL 이벤트를 생성한다. |
| AC-EDGE-004-02 | WHEN 카메라가 재연결되면, | THE SYSTEM SHALL event_type=DEVICE_ONLINE, risk_level=NORMAL 이벤트를 생성한다. |
| AC-EDGE-004-03 | THE SYSTEM SHALL | DEVICE_OFFLINE/ONLINE 이벤트의 device_id를 해당 카메라 ID(CAM-NNN)로 설정한다. |
| AC-EDGE-004-04 | IF 30초 이상 재연결 실패하면, | THEN THE SYSTEM SHALL stream:dashboard에 장비 상태 경고를 발행한다. |

---

## 2. AWS Cloud SW (S2)

### AC-AWS-001: Edge 이벤트 수신

| AC ID | 조건 | 기대 동작 |
|-------|------|-----------|
| AC-AWS-001-01 | WHEN MQTT safety/{site_id}/events 토픽에 메시지가 도착하면, | THE SYSTEM SHALL MqttEventPayload 스키마로 검증한다. |
| AC-AWS-001-02 | THE SYSTEM SHALL | 수신된 페이로드에서 event_id, site_id, device_id, event_type, risk_level, timestamp, context_summary, idempotency_key 필드를 추출한다. |
| AC-AWS-001-03 | IF 페이로드가 스키마 검증을 통과하지 못하면, | THEN THE SYSTEM SHALL 해당 메시지를 dead-letter queue에 저장하고 오류 로그를 남긴다. |
| AC-AWS-001-04 | THE SYSTEM SHALL | MQTT QoS 1(At least once)로 수신하고, 처리 완료 후 ACK한다. |
| AC-AWS-001-05 | THE SYSTEM SHALL | idempotency_key(`{site_id}:{event_id}`)로 중복 수신을 감지한다. |

---

### AC-AWS-002: 이벤트 DB 저장

| AC ID | 조건 | 기대 동작 |
|-------|------|-----------|
| AC-AWS-002-01 | WHEN 검증된 이벤트가 수신되면, | THE SYSTEM SHALL event_id를 PRIMARY KEY 또는 UNIQUE 제약으로 저장한다. |
| AC-AWS-002-02 | THE SYSTEM SHALL | event_id, site_id, device_id, event_type, risk_level, timestamp, event_state 필드를 NOT NULL로 저장한다. |
| AC-AWS-002-03 | IF 동일 event_id로 중복 저장 시도 시, | THEN THE SYSTEM SHALL 기존 레코드를 유지하고 중복 삽입을 무시한다 (ON CONFLICT DO NOTHING). |
| AC-AWS-002-04 | THE SYSTEM SHALL | 저장 시 event_state를 ACTIVE로 초기화한다 (C-005). |
| AC-AWS-002-05 | THE SYSTEM SHALL | timestamp 컬럼에 인덱스를 생성하여 시간 범위 조회를 지원한다. |

---

### AC-AWS-003: 이벤트 조회 API

| AC ID | 조건 | 기대 동작 |
|-------|------|-----------|
| AC-AWS-003-01 | WHEN GET /api/events 요청이 오면, | THE SYSTEM SHALL 저장된 이벤트 목록을 반환한다. |
| AC-AWS-003-02 | WHEN event_type 필터가 지정되면, | THE SYSTEM SHALL 해당 유형의 이벤트만 반환한다 (15종 유효 enum 검증). |
| AC-AWS-003-03 | WHEN risk_level 필터가 지정되면, | THE SYSTEM SHALL 해당 등급의 이벤트만 반환한다 (CRITICAL/WARNING/NORMAL). |
| AC-AWS-003-04 | WHEN timestamp_from/timestamp_to가 지정되면, | THE SYSTEM SHALL 해당 시간 범위의 이벤트만 반환한다. |
| AC-AWS-003-05 | THE SYSTEM SHALL | 응답 JSON이 SafetyEvent 스키마의 Platform 1.0 Required/Optional 필드를 포함한다. |

---

### AC-AWS-004: 장비 상태 저장

| AC ID | 조건 | 기대 동작 |
|-------|------|-----------|
| AC-AWS-004-01 | WHEN MQTT safety/{site_id}/status 토픽에 메시지가 도착하면, | THE SYSTEM SHALL MqttStatusPayload 스키마로 검증한다. |
| AC-AWS-004-02 | THE SYSTEM SHALL | edge_status(HEALTHY/DEGRADED/ERROR), gpu_utilization(0.0~1.0), active_cameras, active_bands, pending_cloud_events를 저장한다. |
| AC-AWS-004-03 | THE SYSTEM SHALL | deepstream_fps 배열을 파이프라인별 FPS로 저장한다. |
| AC-AWS-004-04 | IF gpu_utilization > 0.9이고 edge_status != ERROR이면, | THEN THE SYSTEM SHALL 대시보드에 경고를 표시한다. |

---

## 3. AI Training SW (S3)

### AC-AI-001: 모델 패키지 생성

| AC ID | 조건 | 기대 동작 |
|-------|------|-----------|
| AC-AI-001-01 | WHEN 모델 학습이 완료되면, | THE SYSTEM SHALL /models/staged/{model_version}/ 디렉토리에 model.engine, labels.txt, config.txt, metadata.json을 생성한다. |
| AC-AI-001-02 | THE SYSTEM SHALL | model_version을 `v{M}.{m}.{p}-{tool}-{target}` 형식으로 명명한다 (tool: tao/pretrained/custom, target: ds/cloud). |
| AC-AI-001-03 | THE SYSTEM SHALL | metadata.json에 model_version, model_name, model_type(pgie/sgie), framework(TAO/PyTorch/TensorFlow/ONNX), precision(FP16/FP32/INT8), classes, checksum을 포함한다. |
| AC-AI-001-04 | THE SYSTEM SHALL | /models/registry.json을 업데이트하여 새 모델 엔트리를 추가한다 (status=STAGED). |
| AC-AI-001-05 | THE SYSTEM SHALL | 모델 패키지의 무결성을 SHA-256 checksum으로 검증 가능하게 한다. |

---

### AC-AI-002: 모델 버전 검증

| AC ID | 조건 | 기대 동작 |
|-------|------|-----------|
| AC-AI-002-01 | THE SYSTEM SHALL | model_version이 regex `^v\d+\.\d+\.\d+-(tao|pretrained|custom)-(ds|cloud)$`와 일치하지 않으면 배포를 거부한다. |
| AC-AI-002-02 | THE SYSTEM SHALL | registry.json의 models 배열에서 status=ACTIVE인 모델이 최대 1개임을 보장한다. |
| AC-AI-002-03 | WHEN 모델 배포가 성공하면, | THE SYSTEM SHALL 이전 ACTIVE 모델을 status=ROLLBACK으로 변경한다. |
| AC-AI-002-04 | WHEN 모델 배포가 실패하면, | THE SYSTEM SHALL status=ROLLBACK인 모델을 ACTIVE로 복원한다. |
| AC-AI-002-05 | THE SYSTEM SHALL | registry.json의 metrics에 mAP(0.0~1.0), inference_time_ms(>0), fps(>0), classes(>0)를 포함한다. |

---

### AC-AI-003: 학습 데이터셋 구조

| AC ID | 조건 | 기대 동작 |
|-------|------|-----------|
| AC-AI-003-01 | THE SYSTEM SHALL | metadata.json의 training_config에 epochs, batch_size, learning_rate, dataset_version을 포함한다. |
| AC-AI-003-02 | THE SYSTEM SHALL | metadata.json의 evaluation에 mAP, mAP_50, inference_time_ms, test_dataset_size를 포함한다. |
| AC-AI-003-03 | THE SYSTEM SHALL | classes 배열에 감지 대상 클래스 목록을 포함하고 num_classes와 일치시킨다. |
| AC-AI-003-04 | THE SYSTEM SHALL | input_dims에 channels, height, width를 명시한다. |

---

## 4. Integration Test (S4)

### AC-INT-001: Schema Validation

| AC ID | 조건 | 기대 동작 |
|-------|------|-----------|
| AC-INT-001-01 | WHEN pytest tests/schema/ 실행 시, | THE SYSTEM SHALL PR #16 동결 스키마 기준 196개 이상의 테스트를 PASS한다. |
| AC-INT-001-02 | WHEN 유효하지 않은 event_type이 포함된 메시지가 검증되면, | THE SYSTEM SHALL ValidationError를 발생시킨다. |
| AC-INT-001-03 | WHEN 필수 필드가 누락된 메시지가 검증되면, | THE SYSTEM SHALL 누락된 필드명을 포함한 ValidationError를 발생시킨다. |
| AC-INT-001-04 | WHEN confidence가 0.0~1.0 범위를 벗어나면, | THE SYSTEM SHALL ValidationError를 발생시킨다 (C-006). |
| AC-INT-001-05 | WHEN timestamp에 밀리초가 없거나 Z 접미사가 없으면, | THE SYSTEM SHALL ValidationError를 발생시킨다. |
| AC-INT-001-06 | THE SYSTEM SHALL | 15종 event_type, 3종 risk_level, 3종 event_state만 유효값으로 허용한다. |

---

### AC-INT-002: Edge → Redis → AWS Mock → DB E2E

| AC ID | 조건 | 기대 동작 |
|-------|------|-----------|
| AC-INT-002-01 | WHEN Edge Mock Producer가 FALL_DETECTED 이벤트를 발행하면, | THE SYSTEM SHALL stream:ds-events, stream:alarms, stream:dashboard, stream:cloud-queue, stream:clip-trigger에 메시지가 도착함을 확인한다. |
| AC-INT-002-02 | WHEN CRITICAL 이벤트가 발생하면, | THE SYSTEM SHALL stream:alarms에 action=ALL_ON 메시지가 발행된다. |
| AC-INT-002-03 | WHEN stream:cloud-queue에 메시지가 도착하면, | THE SYSTEM SHALL AWS Mock Receiver가 이를 소비하고 MQTT 페이로드로 변환한다. |
| AC-INT-002-04 | WHEN MQTT 페이로드가 생성되면, | THE SYSTEM SHALL clip_s3_key 경로가 `events/{site_id}/{YYYY}/{MM}/{DD}/{event_id}.mp4` 형식을 따른다. |
| AC-INT-002-05 | WHEN 100건의 이벤트를 연속 발행하면, | THE SYSTEM SHALL 데이터 손실 없이 모두 처리된다 (IT-009). |
| AC-INT-002-06 | WHEN 동일 event_id로 중복 발행하면, | THE SYSTEM SHALL idempotency_key로 중복을 감지한다 (IT-010). |

---

### AC-INT-003: Model Package Validation

| AC ID | 조건 | 기대 동작 |
|-------|------|-----------|
| AC-INT-003-01 | WHEN registry.json이 제공되면, | THE SYSTEM SHALL ModelRegistry 스키마 검증을 통과한다 (schema_version, site_id, models). |
| AC-INT-003-02 | WHEN model_type이 pgie/sgie가 아니면, | THE SYSTEM SHALL ValidationError를 발생시킨다. |
| AC-INT-003-03 | WHEN framework이 TAO/PyTorch/TensorFlow/ONNX가 아니면, | THE SYSTEM SHALL ValidationError를 발생시킨다. |
| AC-INT-003-04 | WHEN mAP이 0.0~1.0 범위를 벗어나면, | THE SYSTEM SHALL ValidationError를 발생시킨다. |
| AC-INT-003-05 | WHEN inference_time_ms가 0 이하이면, | THE SYSTEM SHALL ValidationError를 발생시킨다. |

---

## 5. Acceptance Criteria 요약 매트릭스

| User Story | AC 수 | CRITICAL AC | 비고 |
|------------|--------|-------------|------|
| US-EDGE-001 | 5 | AC-EDGE-001-02 (FPS ≥ 25) | 성능 기준 |
| US-EDGE-002 | 6 | AC-EDGE-002-01, 02, 06 (C-001) | 스키마 준수 |
| US-EDGE-003 | 7 | AC-EDGE-003-03, 04 (C-003, C-004) | 일관성 규칙 |
| US-EDGE-004 | 4 | AC-EDGE-004-01, 02 | 장비 관리 |
| US-AWS-001 | 5 | AC-AWS-001-01, 05 | 스키마 검증 |
| US-AWS-002 | 5 | AC-AWS-002-01, 03 | 데이터 무결성 |
| US-AWS-003 | 5 | AC-AWS-003-05 | 응답 스키마 |
| US-AWS-004 | 4 | AC-AWS-004-01 | 상태 모니터링 |
| US-AI-001 | 5 | AC-AI-001-02, 04 | 패키지 구조 |
| US-AI-002 | 5 | AC-AI-002-01 | 버전 형식 |
| US-AI-003 | 4 | AC-AI-003-01 | 메타데이터 |
| US-INT-001 | 6 | AC-INT-001-01, 06 | 전체 스키마 |
| US-INT-002 | 6 | AC-INT-002-01, 05 | E2E 흐름 |
| US-INT-003 | 5 | AC-INT-003-01 | 모델 검증 |
| **합계** | **72** | | |

---

*작성: Integration Test Session (S4) | 기준: PR #21, PR #16 동결 스키마*
