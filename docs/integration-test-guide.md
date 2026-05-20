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

### Edge Device Session (S1)

- 이벤트를 생성할 때 `tests/fixtures/valid_events.json`의 형식을 따르세요
- `tests/schema/models.py`의 `SafetyEvent`, `DsEventsMessage`, `SensorsMessage` 모델로 검증 가능
- 실행: `pytest tests/schema/test_event_format.py -v`

### AWS Cloud Session (S2)

- MQTT 페이로드는 `tests/fixtures/mqtt_payloads.json` 참고
- `tests/schema/models.py`의 `MqttEventPayload`, `MqttStatusPayload` 모델 사용
- Cloud queue 메시지 형식: `CloudQueueMessage` 모델 참고
- 실행: `pytest tests/schema/test_mqtt_schema.py -v`

### AI Training Session (S3)

- 모델 패키지 구조: `tests/fixtures/model_registry.json` 참고
- `tests/schema/models.py`의 `ModelRegistry`, `ModelEntry` 모델 사용
- 실행: `pytest tests/schema/test_model_package.py -v`

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
