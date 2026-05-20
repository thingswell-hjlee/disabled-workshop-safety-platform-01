# Platform 1.0 User Story Map

> **Status:** Active
> **Last Updated:** 2025-05-20
> **Purpose:** 유저스토리를 세션별·우선순위별로 시각화하고 의존 관계를 정의한다.
> **Reference:** docs/user-stories.md, PR #16 동결 스키마

---

## 1. Story Map Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         Platform 1.0 User Story Map                             │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
│  │  S1: Edge   │  │  S2: AWS    │  │  S3: AI     │  │  S4: Test   │           │
│  │  Device SW  │  │  Cloud SW   │  │  Training   │  │  Integration│           │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘           │
│         │                 │                 │                 │                  │
│  P0 ────┼─────────────────┼─────────────────┼─────────────────┼──── Critical   │
│         │                 │                 │                 │                  │
│   ┌─────┴─────┐   ┌──────┴─────┐   ┌──────┴─────┐   ┌──────┴─────┐           │
│   │US-EDGE-001│   │US-AWS-001  │   │US-AI-001   │   │US-INT-001  │           │
│   │RTSP 수집  │   │이벤트 수신 │   │모델 패키지 │   │Schema 검증 │           │
│   ├───────────┤   ├────────────┤   ├────────────┤   ├────────────┤           │
│   │US-EDGE-002│   │US-AWS-002  │   │US-AI-002   │   │US-INT-002  │           │
│   │낙상 감지  │   │DB 저장     │   │버전 검증   │   │E2E 흐름    │           │
│   ├───────────┤   └────────────┘   └────────────┘   ├────────────┤           │
│   │US-EDGE-003│                                      │US-INT-003  │           │
│   │Redis 발행 │                                      │Model 검증  │           │
│   └───────────┘                                      └────────────┘           │
│         │                 │                 │                                   │
│  P1 ────┼─────────────────┼─────────────────┼──────────────────────── High     │
│         │                 │                 │                                   │
│   ┌─────┴─────┐   ┌──────┴─────┐   ┌──────┴─────┐                            │
│   │US-EDGE-004│   │US-AWS-003  │   │US-AI-003   │                             │
│   │연결 관리  │   │조회 API    │   │데이터셋    │                             │
│   └───────────┘   ├────────────┤   └────────────┘                             │
│                    │US-AWS-004  │                                               │
│                    │장비 상태   │                                               │
│                    └────────────┘                                               │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. 세션별 유저스토리 분류

### 2.1 S1: Edge Device SW (PR #19)

| ID | 제목 | Priority | 의존성 | 출력 인터페이스 |
|----|------|----------|--------|----------------|
| US-EDGE-001 | RTSP 카메라 수집 | P0 | 없음 (독립) | DeepStream Pipeline 내부 |
| US-EDGE-002 | 낙상/쓰러짐 이벤트 생성 | P0 | US-EDGE-001 | stream:ds-events |
| US-EDGE-003 | Redis Streams 이벤트 발행 | P0 | US-EDGE-002 | 6개 Redis streams |
| US-EDGE-004 | 카메라 연결 끊김/재연결 | P1 | US-EDGE-001 | stream:sensors, stream:dashboard |

**핵심 출력물:**
- stream:ds-events → Event Engine
- stream:sensors → Event Engine
- stream:alarms → Alarm Controller
- stream:dashboard → Dashboard Backend
- stream:cloud-queue → AWS Sync Service
- stream:clip-trigger → Rolling Buffer

---

### 2.2 S2: AWS Cloud SW (PR #18)

| ID | 제목 | Priority | 의존성 | 입력 인터페이스 |
|----|------|----------|--------|----------------|
| US-AWS-001 | Edge 이벤트 수신 | P0 | US-EDGE-003 | MQTT safety/{site_id}/events |
| US-AWS-002 | 이벤트 DB 저장 | P0 | US-AWS-001 | DynamoDB / PostgreSQL |
| US-AWS-003 | 이벤트 조회 API | P1 | US-AWS-002 | REST API |
| US-AWS-004 | 장비 상태 저장 | P1 | US-EDGE-003 | MQTT safety/{site_id}/status |

**핵심 입력물:**
- stream:cloud-queue (Edge → AWS Sync → MQTT)
- MQTT safety/{site_id}/events
- MQTT safety/{site_id}/status

---

### 2.3 S3: AI Training SW (PR #20)

| ID | 제목 | Priority | 의존성 | 출력 인터페이스 |
|----|------|----------|--------|----------------|
| US-AI-001 | 모델 패키지 생성 | P0 | 없음 (독립) | /models/ 디렉토리 구조 |
| US-AI-002 | 모델 버전 검증 | P0 | US-AI-001 | registry.json |
| US-AI-003 | 학습 데이터셋 구조 | P1 | 없음 (독립) | metadata.json |

**핵심 출력물:**
- /models/registry.json
- /models/staged/{version}/metadata.json
- MQTT safety/{site_id}/models (배포 상태 보고)

---

### 2.4 S4: Integration Test (PR #21)

| ID | 제목 | Priority | 의존성 | 검증 대상 |
|----|------|----------|--------|-----------|
| US-INT-001 | Schema Validation | P0 | PR #16 스키마 | 모든 세션 메시지 |
| US-INT-002 | Edge→Redis→AWS E2E | P0 | US-EDGE-003, US-AWS-001 | 전체 파이프라인 |
| US-INT-003 | Model Package Validation | P0 | US-AI-001, US-AI-002 | 모델 패키지 |

**핵심 역할:**
- 다른 세션의 출력물이 PR #16 스키마를 준수하는지 검증
- Mock 기반 E2E 시뮬레이션으로 통합 흐름 사전 검증

---

## 3. 의존 관계 그래프

```
US-EDGE-001 ──→ US-EDGE-002 ──→ US-EDGE-003 ──→ US-AWS-001 ──→ US-AWS-002 ──→ US-AWS-003
     │                                │               │
     └──→ US-EDGE-004                 │               └──→ US-AWS-004
                                      │
                                      └──→ US-INT-002 (E2E 검증)

US-AI-001 ──→ US-AI-002 ──→ US-INT-003 (Model 검증)
     │
     └──→ US-AI-003

PR #16 Schema ──→ US-INT-001 (모든 메시지 검증)
```

---

## 4. 우선순위별 구현 순서

### Phase 1: P0 (필수 — Platform 1.0 최소 동작)

```
┌─────────────────────────────────────────────────────────────────────┐
│ 1. US-EDGE-001 → 2. US-EDGE-002 → 3. US-EDGE-003                  │
│        ↓                                    ↓                       │
│ 4. US-AI-001 → 5. US-AI-002          6. US-AWS-001 → 7. US-AWS-002│
│                                                                     │
│ ────── 검증 ──────                                                  │
│ 8. US-INT-001  9. US-INT-002  10. US-INT-003                       │
└─────────────────────────────────────────────────────────────────────┘
```

### Phase 2: P1 (고 — Platform 1.0 운영 기능)

```
┌─────────────────────────────────────────────────────────────────────┐
│ 11. US-EDGE-004  12. US-AWS-003  13. US-AWS-004  14. US-AI-003     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 5. 세션 간 인터페이스 매핑

| 소스 (Publisher) | 인터페이스 | 대상 (Subscriber) | 유저스토리 |
|-----------------|-----------|-------------------|-----------|
| S1 Edge | stream:ds-events | S1 Event Engine | US-EDGE-002 → US-EDGE-003 |
| S1 Edge | stream:sensors | S1 Event Engine | US-EDGE-004 → US-EDGE-003 |
| S1 Edge | stream:alarms | S1 Alarm Controller | US-EDGE-003 |
| S1 Edge | stream:dashboard | S2 Dashboard Backend | US-EDGE-003 → US-AWS-003 |
| S1 Edge | stream:cloud-queue | S2 AWS Sync | US-EDGE-003 → US-AWS-001 |
| S1 Edge | stream:clip-trigger | S1 Rolling Buffer | US-EDGE-003 |
| S2 AWS | MQTT events | S2 IoT Core | US-AWS-001 |
| S2 AWS | MQTT status | S2 IoT Core | US-AWS-004 |
| S3 AI | MQTT models | S1 Edge Deployer | US-AI-001 → US-AI-002 |
| S3 AI | registry.json | S1 DeepStream Loader | US-AI-002 |
| S4 Test | 검증 결과 | 모든 세션 | US-INT-001, 002, 003 |

---

## 6. 세션별 작업 독립성

각 세션은 자기 유저스토리만 보고 독립적으로 작업할 수 있습니다.

| 세션 | 독립 작업 가능 유저스토리 | 의존 유저스토리 |
|------|------------------------|----------------|
| S1 (Edge) | US-EDGE-001, 002, 003, 004 | 없음 (최상위) |
| S2 (AWS) | US-AWS-002, 003, 004 | US-AWS-001 ← US-EDGE-003 |
| S3 (AI) | US-AI-001, 002, 003 | 없음 (독립) |
| S4 (Test) | US-INT-001, 003 | US-INT-002 ← US-EDGE-003 + US-AWS-001 |

**핵심 규칙:**
- S1과 S3은 완전 독립 작업 가능
- S2는 S1의 메시지 형식을 참조하지만 mock 기반으로 독립 개발 가능
- S4는 모든 세션의 출력을 검증하지만 fixture 기반으로 독립 실행 가능

---

## 7. 스키마 기준 문서 참조

| 유저스토리 | 참조 스키마 문서 |
|-----------|----------------|
| US-EDGE-001 | — (내부 파이프라인) |
| US-EDGE-002 | docs/event-message-schema.md, docs/redis-streams-schema.md |
| US-EDGE-003 | docs/redis-streams-schema.md (6개 stream 전체) |
| US-EDGE-004 | docs/event-message-schema.md (DEVICE_OFFLINE/ONLINE) |
| US-AWS-001 | docs/aws-iot-message-schema.md (events topic) |
| US-AWS-002 | docs/event-message-schema.md (필수 필드) |
| US-AWS-003 | docs/event-message-schema.md (조회 응답) |
| US-AWS-004 | docs/aws-iot-message-schema.md (status topic) |
| US-AI-001 | docs/model-package-schema.md (폴더 구조) |
| US-AI-002 | docs/model-package-schema.md (registry.json) |
| US-AI-003 | docs/model-package-schema.md (metadata.json) |
| US-INT-001 | docs/schema-validation-test.md (전체) |
| US-INT-002 | docs/redis-streams-schema.md + docs/aws-iot-message-schema.md |
| US-INT-003 | docs/model-package-schema.md |

---

*작성: Integration Test Session (S4) | 기준: PR #21, PR #16 동결 스키마*
