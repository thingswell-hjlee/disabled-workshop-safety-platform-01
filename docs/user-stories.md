# Platform 1.0 User Stories

> **Status:** Active
> **Last Updated:** 2025-05-20
> **Purpose:** Platform 1.0 기능을 유저스토리 단위로 정의하고 세션별 구현 범위를 명확히 한다.
> **Reference:** PR #16 동결 스키마, PR #21 Integration Test

---

## 1. User Story Format

```
As a [역할],
I want [기능],
so that [목적].
```

## 2. 역할 정의

| 역할 | 설명 |
|------|------|
| **시설 관리자** | 장애인직업재활시설의 안전 관리 담당자 |
| **시스템 운영자** | Platform 인프라 운영 담당자 |
| **AI 엔지니어** | AI 모델 학습/배포 담당자 |
| **QA 엔지니어** | 통합시험 및 품질 검증 담당자 |

---

## 3. Edge Device SW (S1) User Stories

### US-EDGE-001: RTSP 카메라 수집

**As a** 시설 관리자,
**I want** 8대의 IP 카메라 RTSP 스트림을 Edge AI 서버에서 실시간 수집할 수 있도록,
**so that** 영상 기반 안전 이벤트를 실시간으로 감지할 수 있다.

| 항목 | 내용 |
|------|------|
| **ID** | US-EDGE-001 |
| **세션** | S1 (Edge Device) |
| **Priority** | P0 |
| **관련 PR** | PR #19 |
| **관련 Requirements** | FR-EDGE-001, FR-EDGE-002 |
| **검증 방법** | DeepStream 파이프라인 FPS > 25 확인 |

---

### US-EDGE-002: 낙상/쓰러짐 이벤트 생성

**As a** 시설 관리자,
**I want** 카메라 영상에서 낙상(FALL_DETECTED) 또는 쓰러짐(COLLAPSE_DETECTED) 상황이 감지되면 즉시 안전 이벤트가 생성되도록,
**so that** CRITICAL 등급 알람이 즉각 발동되어 신속한 대응이 가능하다.

| 항목 | 내용 |
|------|------|
| **ID** | US-EDGE-002 |
| **세션** | S1 (Edge Device) |
| **Priority** | P0 |
| **관련 PR** | PR #19 |
| **관련 Requirements** | FR-EDGE-003, FR-EDGE-004 |
| **검증 방법** | stream:ds-events에 FALL_DETECTED 메시지 발행 확인 |
| **event_type** | FALL_DETECTED, COLLAPSE_DETECTED |
| **risk_level** | CRITICAL (C-001 규칙) |

---

### US-EDGE-003: Redis Streams 이벤트 발행

**As a** 시스템 운영자,
**I want** Edge에서 감지된 모든 이벤트가 PR #16 동결 스키마에 맞춰 Redis Streams에 발행되도록,
**so that** 후속 시스템(Alarm Controller, Dashboard, AWS Sync)이 일관된 메시지를 소비할 수 있다.

| 항목 | 내용 |
|------|------|
| **ID** | US-EDGE-003 |
| **세션** | S1 (Edge Device) |
| **Priority** | P0 |
| **관련 PR** | PR #19 |
| **관련 Requirements** | FR-EDGE-005, FR-EDGE-006 |
| **검증 방법** | 6개 Redis stream 메시지 스키마 검증 통과 |
| **관련 Streams** | stream:ds-events, stream:sensors, stream:alarms, stream:dashboard, stream:cloud-queue, stream:clip-trigger |

---

### US-EDGE-004: 카메라 연결 끊김/재연결

**As a** 시설 관리자,
**I want** 카메라 연결이 끊기면 DEVICE_OFFLINE 이벤트가 생성되고, 재연결 시 DEVICE_ONLINE 이벤트가 생성되도록,
**so that** 장비 상태를 실시간으로 모니터링하고 장애에 대응할 수 있다.

| 항목 | 내용 |
|------|------|
| **ID** | US-EDGE-004 |
| **세션** | S1 (Edge Device) |
| **Priority** | P1 |
| **관련 PR** | PR #19 |
| **관련 Requirements** | FR-EDGE-007 |
| **검증 방법** | DEVICE_OFFLINE/DEVICE_ONLINE 이벤트 정상 생성 확인 |
| **event_type** | DEVICE_OFFLINE, DEVICE_ONLINE |
| **risk_level** | NORMAL |

---

## 4. AWS Cloud SW (S2) User Stories

### US-AWS-001: Edge 이벤트 수신

**As a** 시스템 운영자,
**I want** Edge 서버에서 발생한 이벤트를 AWS IoT Core MQTT를 통해 클라우드에서 수신할 수 있도록,
**so that** 원격에서 시설 안전 상황을 실시간 모니터링할 수 있다.

| 항목 | 내용 |
|------|------|
| **ID** | US-AWS-001 |
| **세션** | S2 (AWS Cloud) |
| **Priority** | P0 |
| **관련 PR** | PR #18 |
| **관련 Requirements** | FR-AWS-001, FR-AWS-002 |
| **검증 방법** | MQTT safety/{site_id}/events 토픽 수신 + 스키마 검증 |
| **MQTT Topic** | safety/{site_id}/events |
| **Payload 검증** | MqttEventPayload 모델 통과 |

---

### US-AWS-002: 이벤트 DB 저장

**As a** 시스템 운영자,
**I want** 수신된 이벤트가 PostgreSQL(또는 DynamoDB)에 저장되어 이력 관리가 가능하도록,
**so that** 과거 이벤트를 조회하고 통계 분석에 활용할 수 있다.

| 항목 | 내용 |
|------|------|
| **ID** | US-AWS-002 |
| **세션** | S2 (AWS Cloud) |
| **Priority** | P0 |
| **관련 PR** | PR #18 |
| **관련 Requirements** | FR-AWS-003 |
| **검증 방법** | event_id UNIQUE 제약, 필수 필드 NOT NULL 저장 확인 |
| **중복 처리** | idempotency_key 기반 ON CONFLICT DO NOTHING |

---

### US-AWS-003: 이벤트 조회 API

**As a** 시설 관리자,
**I want** 대시보드에서 이벤트 이력을 날짜/유형/위험등급으로 필터링하여 조회할 수 있도록,
**so that** 과거 안전 이벤트를 분석하고 보고서를 작성할 수 있다.

| 항목 | 내용 |
|------|------|
| **ID** | US-AWS-003 |
| **세션** | S2 (AWS Cloud) |
| **Priority** | P1 |
| **관련 PR** | PR #18 |
| **관련 Requirements** | FR-AWS-004 |
| **검증 방법** | API 응답이 SafetyEvent 스키마와 일치 확인 |
| **필터 필드** | event_type, risk_level, timestamp range, site_id |

---

### US-AWS-004: 장비 상태 저장

**As a** 시스템 운영자,
**I want** Edge 서버의 상태(GPU 사용률, 활성 카메라 수, 미전송 이벤트 수)가 주기적으로 클라우드에 저장되도록,
**so that** 시설 장비의 건강 상태를 원격으로 확인하고 장애를 예방할 수 있다.

| 항목 | 내용 |
|------|------|
| **ID** | US-AWS-004 |
| **세션** | S2 (AWS Cloud) |
| **Priority** | P1 |
| **관련 PR** | PR #18 |
| **관련 Requirements** | FR-AWS-005 |
| **검증 방법** | MQTT safety/{site_id}/status 수신 + MqttStatusPayload 검증 |
| **주기** | 60초 간격 |

---

## 5. AI Training SW (S3) User Stories

### US-AI-001: 모델 패키지 생성

**As a** AI 엔지니어,
**I want** TAO Toolkit으로 학습된 모델을 표준 패키지 구조로 생성할 수 있도록,
**so that** Edge 서버에 일관된 방식으로 모델을 배포할 수 있다.

| 항목 | 내용 |
|------|------|
| **ID** | US-AI-001 |
| **세션** | S3 (AI Training) |
| **Priority** | P0 |
| **관련 PR** | PR #20 |
| **관련 Requirements** | FR-AI-001, FR-AI-002 |
| **검증 방법** | ModelEntry 스키마 검증 통과 |
| **폴더 구조** | /models/active/, /models/staged/, /models/rollback/ |

---

### US-AI-002: 모델 버전 검증

**As a** AI 엔지니어,
**I want** 모델 버전이 `v{M}.{m}.{p}-{tool}-{target}` 형식을 반드시 따르도록 검증 가능하게,
**so that** 모델 이력 관리와 롤백이 안전하게 수행된다.

| 항목 | 내용 |
|------|------|
| **ID** | US-AI-002 |
| **세션** | S3 (AI Training) |
| **Priority** | P0 |
| **관련 PR** | PR #20 |
| **관련 Requirements** | FR-AI-003 |
| **검증 방법** | model_version pattern regex 검증 |
| **Pattern** | `^v\d+\.\d+\.\d+-(tao\|pretrained\|custom)-(ds\|cloud)$` |
| **예시** | v1.0.0-tao-ds, v1.1.0-custom-cloud |

---

### US-AI-003: 학습 데이터셋 구조

**As a** AI 엔지니어,
**I want** 학습에 사용되는 데이터셋의 메타데이터(버전, 크기, 클래스 분포)가 표준 형식으로 관리되도록,
**so that** 모델 재학습 시 데이터 계보를 추적할 수 있다.

| 항목 | 내용 |
|------|------|
| **ID** | US-AI-003 |
| **세션** | S3 (AI Training) |
| **Priority** | P1 |
| **관련 PR** | PR #20 |
| **관련 Requirements** | FR-AI-004 |
| **검증 방법** | metadata.json 구조 검증 |
| **필수 필드** | model_version, classes, num_classes, checksum, training_config |

---

## 6. Integration Test (S4) User Stories

### US-INT-001: Schema Validation

**As a** QA 엔지니어,
**I want** 모든 인터페이스 메시지가 PR #16 동결 스키마를 통과하는지 자동 검증할 수 있도록,
**so that** 세션 간 인터페이스 불일치를 조기에 발견할 수 있다.

| 항목 | 내용 |
|------|------|
| **ID** | US-INT-001 |
| **세션** | S4 (Integration Test) |
| **Priority** | P0 |
| **관련 PR** | PR #21 |
| **관련 Requirements** | FR-INT-001 |
| **검증 방법** | pytest tests/schema/ -v → 196 tests ALL PASSED |
| **카테고리** | format, completeness, consistency, boundary |

---

### US-INT-002: Edge → Redis → AWS Mock → DB E2E

**As a** QA 엔지니어,
**I want** Edge에서 생성된 이벤트가 Redis Streams를 거쳐 AWS Mock Receiver를 통해 DB에 저장되는 전체 파이프라인을 시뮬레이션할 수 있도록,
**so that** 실제 인프라 없이도 통합 흐름의 정합성을 검증할 수 있다.

| 항목 | 내용 |
|------|------|
| **ID** | US-INT-002 |
| **세션** | S4 (Integration Test) |
| **Priority** | P0 |
| **관련 PR** | PR #21 |
| **관련 Requirements** | FR-INT-002 |
| **검증 방법** | pytest tests/e2e/ -v → 11 tests ALL PASSED |
| **흐름** | Edge Mock → stream:ds-events → EventEngine → stream:alarms + stream:dashboard + stream:cloud-queue → AWS Receiver → MQTT Transform → DB Storage |

---

### US-INT-003: Model Package Validation

**As a** QA 엔지니어,
**I want** AI 모델 패키지(registry.json, metadata.json)가 PR #16 스키마를 통과하는지 자동 검증할 수 있도록,
**so that** 잘못된 모델 패키지가 배포되는 것을 방지할 수 있다.

| 항목 | 내용 |
|------|------|
| **ID** | US-INT-003 |
| **세션** | S4 (Integration Test) |
| **Priority** | P0 |
| **관련 PR** | PR #21 |
| **관련 Requirements** | FR-INT-003 |
| **검증 방법** | pytest tests/schema/test_model_package.py -v → ALL PASSED |
| **검증 대상** | ModelRegistry, ModelEntry, ModelMetrics |

---

## 7. User Story Summary

| ID | 제목 | 세션 | Priority | PR |
|----|------|------|----------|-----|
| US-EDGE-001 | RTSP 카메라 수집 | S1 | P0 | #19 |
| US-EDGE-002 | 낙상/쓰러짐 이벤트 생성 | S1 | P0 | #19 |
| US-EDGE-003 | Redis Streams 이벤트 발행 | S1 | P0 | #19 |
| US-EDGE-004 | 카메라 연결 끊김/재연결 | S1 | P1 | #19 |
| US-AWS-001 | Edge 이벤트 수신 | S2 | P0 | #18 |
| US-AWS-002 | 이벤트 DB 저장 | S2 | P0 | #18 |
| US-AWS-003 | 이벤트 조회 API | S2 | P1 | #18 |
| US-AWS-004 | 장비 상태 저장 | S2 | P1 | #18 |
| US-AI-001 | 모델 패키지 생성 | S3 | P0 | #20 |
| US-AI-002 | 모델 버전 검증 | S3 | P0 | #20 |
| US-AI-003 | 학습 데이터셋 구조 | S3 | P1 | #20 |
| US-INT-001 | Schema Validation | S4 | P0 | #21 |
| US-INT-002 | Edge→Redis→AWS E2E | S4 | P0 | #21 |
| US-INT-003 | Model Package Validation | S4 | P0 | #21 |

---

*작성: Integration Test Session (S4) | 기준: PR #21, PR #16 동결 스키마*
