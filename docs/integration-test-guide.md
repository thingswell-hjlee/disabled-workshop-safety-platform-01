# Integration Test Guide

> **Version:** Platform 1.0
> **Last Updated:** 2025-05-20
> **Owner:** Integration Test Session (S4)
> **Branch:** `feature/integration-schema-validation`

## Overview

PR #16에서 동결된 인터페이스 스키마를 기준으로, Edge Device SW, AWS Cloud SW, AI Training SW가
서로 충돌 없이 통합될 수 있도록 자동 검증하는 테스트 스위트입니다.

---

## Quick Start

### 1. 외부 의존성 없이 즉시 실행 (스키마 + 통합 + E2E)

```bash
# 의존성 설치
pip install -r requirements-test.txt

# 스키마 검증 테스트 (196 tests, ~0.2s)
./scripts/run-schema-tests.sh

# 통합 + E2E 테스트 (31 tests, ~0.4s)
./scripts/run-integration-tests.sh
```

### 2. Docker 환경 포함 전체 테스트

```bash
# 테스트 환경 시작 (Redis + PostgreSQL)
./scripts/start-local-test-env.sh up

# 전체 테스트 실행 (PostgreSQL 포함)
./scripts/run-integration-tests.sh --all

# 환경 종료
./scripts/start-local-test-env.sh down
```

---

## Test Structure

```
tests/
├── conftest.py                      # 공통 설정, fixtures, markers
├── __init__.py
├── fixtures/
│   ├── valid_events.json            # 정상 이벤트 10종
│   ├── invalid_events.json          # 오류 이벤트 13종
│   ├── redis_stream_messages.json   # 6개 Redis stream 샘플
│   ├── mqtt_payloads.json           # 3개 MQTT 토픽 페이로드
│   ├── model_registry.json          # 모델 레지스트리 샘플
│   └── init-db.sql                  # PostgreSQL 초기화 DDL
├── schema/                          # 스키마 검증 (외부 의존성 없음)
│   ├── models.py                    # Pydantic v2 스키마 모델
│   ├── test_event_format.py         # ID/timestamp/enum 형식 검증
│   ├── test_event_completeness.py   # 필수 필드 존재 여부
│   ├── test_event_consistency.py    # 필드간 논리 정합성 (C-001~C-009)
│   ├── test_event_boundary.py       # 경계값 테스트
│   ├── test_redis_stream_schema.py  # 6개 Redis stream 메시지 스키마
│   ├── test_mqtt_schema.py          # MQTT 페이로드 스키마
│   └── test_model_package.py        # 모델 패키지 스키마
├── integration/                     # 통합 테스트 (fakeredis 기반)
│   ├── mock_edge_producer.py        # Edge 이벤트 생성 mock
│   ├── mock_aws_receiver.py         # AWS 수신 mock
│   ├── test_redis_pubsub.py         # Redis pub/sub 흐름 (IT-001~IT-010)
│   └── test_db_storage.py           # DB 저장 테스트
└── e2e/                             # E2E 시뮬레이터
    └── test_e2e_flow.py             # 전체 파이프라인 시뮬레이션
```

---

## Test Categories & Markers

| Marker | Purpose | 파일 | 외부 의존성 |
|--------|---------|------|-------------|
| `format` | ID 형식, timestamp, enum 검증 | test_event_format.py | 없음 |
| `completeness` | 필수 필드 존재 여부 | test_event_completeness.py | 없음 |
| `consistency` | 필드간 논리 정합성 | test_event_consistency.py | 없음 |
| `boundary` | 경계값, 엣지 케이스 | test_event_boundary.py | 없음 |
| `redis` | Redis stream 메시지 스키마 | test_redis_stream_schema.py | 없음 |
| `mqtt` | MQTT 페이로드 스키마 | test_mqtt_schema.py | 없음 |
| `model` | 모델 패키지 스키마 | test_model_package.py | 없음 |
| `integration` | Redis pub/sub 통합 흐름 | test_redis_pubsub.py, test_db_storage.py | fakeredis (자동) |
| `e2e` | 전체 파이프라인 시뮬레이션 | test_e2e_flow.py | fakeredis (자동) |

### 마커별 실행

```bash
# 형식 검증만
pytest tests/schema/ -m "format" -v

# 일관성 규칙만
pytest tests/schema/ -m "consistency" -v

# 통합 테스트만
pytest tests/ -m "integration" -v

# E2E만
pytest tests/ -m "e2e" -v
```

---

## Test Scenarios (IT-001 ~ IT-010)

| ID | Scenario | Expected | 상태 |
|----|----------|----------|------|
| IT-001 | Valid FALL_DETECTED → full pipeline | All streams receive, validation passes | ✅ |
| IT-002 | Invalid event_id format | Schema validation rejects | ✅ |
| IT-003 | Missing required field | Schema validation rejects | ✅ |
| IT-004 | CRITICAL event → alarm triggered | stream:alarms receives ALL_ON | ✅ |
| IT-005 | Event → dashboard message | stream:dashboard with context | ✅ |
| IT-006 | Event → cloud queue | Correct priority mapping | ✅ |
| IT-007 | Vision AI without confidence | Completeness check flags | ✅ |
| IT-008 | BAND event without worker_id | Completeness check flags | ✅ |
| IT-009 | 100 events rapidly | All processed, no loss | ✅ |
| IT-010 | Duplicate event_id | Idempotency key detects duplicate | ✅ |

---

## Test Environment

### Ports

| Service | Port | Purpose |
|---------|------|---------|
| Redis | 6380 | Redis Streams 테스트 |
| PostgreSQL | 5433 | Event 저장 테스트 |

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TEST_REDIS_HOST` | `localhost` | Redis 호스트 |
| `TEST_REDIS_PORT` | `6380` | Redis 포트 |
| `TEST_POSTGRES_HOST` | `localhost` | PostgreSQL 호스트 |
| `TEST_POSTGRES_PORT` | `5433` | PostgreSQL 포트 |
| `TEST_POSTGRES_DB` | `safety_test` | DB 이름 |
| `TEST_POSTGRES_USER` | `safety_test` | DB 사용자 |
| `TEST_POSTGRES_PASSWORD` | `test_password` | DB 비밀번호 |

---

## CI/CD Integration

GitHub Actions 워크플로우: `.github/workflows/schema-validation.yml`

### CI Stages

| Stage | Trigger | Tests | Duration |
|-------|---------|-------|----------|
| PR Check | Pull Request | Schema (format + completeness + boundary) | ~30s |
| Merge Check | Push to develop | All schema + integration + E2E | ~2min |

### Failure Policy

| Category | PR 차단 여부 |
|----------|-------------|
| Format validation fail | ❌ Block |
| Completeness fail | ❌ Block |
| Consistency fail | ❌ Block |
| Boundary fail | ⚠️ Warning |
| Integration fail | ❌ Block release |

---

## Schema Reference Documents

이 테스트는 아래 동결된 스키마 문서를 절대 기준으로 따릅니다:

| Document | Description |
|----------|-------------|
| `docs/interface-schema.md` | 인터페이스 마스터 문서 |
| `docs/event-message-schema.md` | 정규 이벤트 메시지 구조 |
| `docs/redis-streams-schema.md` | Redis Streams 메시지 구조 |
| `docs/aws-iot-message-schema.md` | AWS IoT MQTT 메시지 구조 |
| `docs/model-package-schema.md` | 모델 패키지 구조 |
| `docs/schema-validation-test.md` | 검증 규칙 및 테스트 기준 |

---

## Consistency Rules Implemented

| Rule | Description | 테스트 |
|------|-------------|--------|
| C-001 | FALL/COLLAPSE/FIRE → CRITICAL | test_event_consistency.py |
| C-002 | device_id prefix ↔ device_type | test_event_consistency.py |
| C-003 | idempotency_key = {site_id}:{event_id} | test_event_consistency.py |
| C-004 | CRITICAL→HIGH, WARNING→NORMAL, NORMAL→LOW | test_event_consistency.py |
| C-005 | New events start as ACTIVE | test_event_consistency.py |
| C-006 | 0.0 ≤ confidence ≤ 1.0 | test_event_consistency.py |
| C-007 | 0.0 ≤ gpu_utilization ≤ 1.0 | test_mqtt_schema.py |
| C-008 | pre_sec / post_sec > 0 | test_redis_stream_schema.py |

---

## For Other Sessions

> 아래는 PR #19 (Edge), PR #18 (AWS), PR #20 (Training) 세션이
> 자체 구현 시 이 테스트 스위트를 활용하는 방법입니다.

### Edge Device Session (S1 — PR #19)

**목적:** DeepStream 파이프라인, Device Gateway, Event Engine, Alarm Controller가 생성하는 메시지의 스키마 적합성 검증

**사용 모델:**
| 모델 | import 경로 | 용도 |
|-------|-------------|------|
| `SafetyEvent` | `tests.schema.models` | 정규 이벤트 메시지 최종 검증 |
| `DsEventsMessage` | `tests.schema.models` | stream:ds-events 발행 전 검증 |
| `SensorsMessage` | `tests.schema.models` | stream:sensors 발행 전 검증 |
| `AlarmsMessage` | `tests.schema.models` | stream:alarms 발행 전 검증 |
| `DashboardMessage` | `tests.schema.models` | stream:dashboard 발행 전 검증 |
| `ClipTriggerMessage` | `tests.schema.models` | stream:clip-trigger 발행 전 검증 |

**검증 예시:**
```python
from tests.schema.models import DsEventsMessage
# DeepStream 출력을 검증
msg = DsEventsMessage(**your_ds_output)  # ValidationError 시 스키마 위반
```

**사용 가능 테스트:**
```bash
# Edge가 생성하는 메시지 형식 검증
pytest tests/schema/test_event_format.py -v
pytest tests/schema/test_redis_stream_schema.py -v

# Edge Event Engine 로직 기대값 확인
pytest tests/integration/test_redis_pubsub.py -v

# Edge mock producer를 자체 구현으로 교체하여 E2E 검증
pytest tests/e2e/ -v
```

**Fixture 참고:**
- `tests/fixtures/valid_events.json` — 10종 정상 이벤트 샘플
- `tests/fixtures/redis_stream_messages.json` — 6개 stream별 메시지 샘플

**주의사항:**
- Redis는 null을 빈 문자열로 저장합니다. `worker_id=""` → Pydantic이 None으로 변환합니다.
- `inference` 필드는 JSON 문자열로 Redis에 저장하고, 소비 시 `json.loads()`로 파싱해야 합니다.

---

### AWS Cloud Session (S2 — PR #18)

**목적:** AWS Sync Service가 소비하는 cloud-queue 메시지와 MQTT 페이로드의 스키마 적합성 검증

**사용 모델:**
| 모델 | import 경로 | 용도 |
|-------|-------------|------|
| `CloudQueueMessage` | `tests.schema.models` | stream:cloud-queue 소비 시 검증 |
| `MqttEventPayload` | `tests.schema.models` | MQTT events 토픽 발행 전 검증 |
| `MqttStatusPayload` | `tests.schema.models` | MQTT status 토픽 발행 전 검증 |
| `MqttModelDeployCommand` | `tests.schema.models` | MQTT models 토픽(Cloud→Edge) 검증 |
| `MqttModelStatusReport` | `tests.schema.models` | MQTT models 토픽(Edge→Cloud) 검증 |

**검증 예시:**
```python
from tests.schema.models import MqttEventPayload
# IoT Core로 보낼 페이로드 검증
payload = MqttEventPayload(**your_mqtt_payload)  # 형식 오류 시 즉시 탐지
```

**사용 가능 테스트:**
```bash
# MQTT 페이로드 스키마 검증
pytest tests/schema/test_mqtt_schema.py -v

# Cloud queue 메시지 스키마 (소비 측)
pytest tests/schema/test_redis_stream_schema.py::TestCloudQueueStream -v

# AWS receiver mock으로 E2E 흐름 확인
pytest tests/integration/test_redis_pubsub.py::TestIT006CloudQueue -v
pytest tests/integration/test_redis_pubsub.py::TestAwsReceiverTransform -v
```

**Fixture 참고:**
- `tests/fixtures/mqtt_payloads.json` — 3개 MQTT 토픽(events, status, models) 페이로드
- `tests/fixtures/redis_stream_messages.json["stream:cloud-queue"]` — cloud queue 메시지 샘플

**주의사항:**
- `idempotency_key`는 반드시 `{site_id}:{event_id}` 형식 (C-003 규칙)
- `priority`는 risk_level에서 매핑: CRITICAL→HIGH, WARNING→NORMAL, NORMAL→LOW (C-004 규칙)
- `clip_s3_key` 경로 패턴: `events/{site_id}/{YYYY}/{MM}/{DD}/{event_id}.mp4`

---

### AI Training Session (S3 — PR #20)

**목적:** 모델 패키지 구조, registry.json, model_version 명명 규칙의 스키마 적합성 검증

**사용 모델:**
| 모델 | import 경로 | 용도 |
|-------|-------------|------|
| `ModelRegistry` | `tests.schema.models` | registry.json 전체 구조 검증 |
| `ModelEntry` | `tests.schema.models` | 개별 모델 엔트리 검증 |
| `ModelMetrics` | `tests.schema.models` | 모델 성능 메트릭 검증 |
| `MqttModelDeployCommand` | `tests.schema.models` | 배포 명령 페이로드 검증 |
| `MqttModelStatusReport` | `tests.schema.models` | 배포 상태 보고 검증 |

**검증 예시:**
```python
from tests.schema.models import ModelRegistry
import json
# registry.json 유효성 검증
with open("/models/registry.json") as f:
    registry = ModelRegistry(**json.load(f))  # 스키마 위반 시 예외
```

**사용 가능 테스트:**
```bash
# 모델 패키지 스키마 검증
pytest tests/schema/test_model_package.py -v

# model_version 형식 검증
pytest tests/schema/test_event_format.py::TestModelVersionFormat -v

# MQTT 모델 배포 페이로드
pytest tests/schema/test_mqtt_schema.py::TestMqttModelPayload -v
```

**Fixture 참고:**
- `tests/fixtures/model_registry.json` — registry.json + metadata 예시
- `tests/fixtures/mqtt_payloads.json["safety/{site_id}/models"]` — 배포 명령/상태 보고

**주의사항:**
- `model_version` 형식: `v{M}.{m}.{p}-{tool}-{target}` (tool: tao|pretrained|custom, target: ds|cloud)
- `status` 유효값: ACTIVE, STAGED, ROLLBACK, ARCHIVED
- `framework` 유효값: TAO, PyTorch, TensorFlow, ONNX
- `precision` 유효값: FP16, FP32, INT8

---

### 세션 간 통합 검증 실행 방법

```bash
# 1. 의존성 설치 (한 번만)
pip install -r requirements-test.txt

# 2. 자기 세션 관련 테스트만 실행
pytest tests/schema/test_event_format.py -v          # Edge (S1)
pytest tests/schema/test_mqtt_schema.py -v           # AWS (S2)
pytest tests/schema/test_model_package.py -v         # Training (S3)

# 3. 전체 스키마 호환성 검증 (병합 전 필수)
pytest tests/schema/ -v

# 4. 통합 흐름 검증 (mock 기반, 외부 의존성 없음)
pytest tests/integration/ tests/e2e/ -k "not Postgres" -v

# 5. 전체 테스트 (Docker 환경 포함)
./scripts/start-local-test-env.sh up
pytest tests/ -v
./scripts/start-local-test-env.sh down
```

---

## Known Issues & Limitations

- Platform 2.0/3.0 reserved fields는 null 검증만 수행 (로직 미구현)
- Redis empty string → None 변환 로직 포함 (Redis는 null을 지원하지 않음)
- PostgreSQL 테스트는 docker-compose 환경 필요 (`./scripts/start-local-test-env.sh up`)
- Load test는 100건으로 축소 (CI 속도 고려, 실제는 1000건 이상 권장)

---

## Troubleshooting

### `ModuleNotFoundError: No module named 'tests'`

```bash
# 프로젝트 루트에서 실행해야 합니다
cd /path/to/disabled-workshop-safety-platform-01
pytest tests/schema/ -v
```

### PostgreSQL 테스트가 SKIP 처리됨

```bash
# docker-compose 환경 시작
./scripts/start-local-test-env.sh up

# 상태 확인
./scripts/start-local-test-env.sh status
```

### Redis 연결 실패

```bash
# 기본 포트는 6380 (시스템 Redis와 충돌 방지)
export TEST_REDIS_PORT=6380
```
