# Dashboard Backend - AWS Cloud Integration

> Platform 1.0 | AWS IoT Core / S3 / RDS (PostgreSQL) 연동 백엔드

## 개요

Edge AI 서버에서 전송되는 안전 이벤트를 AWS 클라우드에서 수신, 저장, 조회하는 기본 클라우드 구조입니다.

### 주요 기능

| 기능 | 설명 | 상태 |
|------|------|------|
| Event Ingest | MQTT payload → PostgreSQL 저장 | ✅ 구현 |
| Event Query | 필터링/페이지네이션 조회 API | ✅ 구현 |
| Event Acknowledge/Archive | 이벤트 상태 변경 | ✅ 구현 |
| Device Status | 장비 목록/상태 조회 | ✅ 구현 |
| Model Version | AI 모델 버전 조회 | ✅ 구현 |
| Edge Status | 엣지 서버 상태 보고 수신 | ✅ 구현 |
| Schema Validation | event-message-schema 검증 | ✅ 구현 |
| Mock Mode | AWS 계정 없이 로컬 테스트 | ✅ 구현 |

## 아키텍처

```
                     ┌─────────────────────────────────────┐
                     │         AWS Cloud (live mode)        │
                     │                                     │
Edge ─── MQTT ─────► │  IoT Core → Lambda → Dashboard API  │
                     │                          │           │
                     │                          ▼           │
                     │                     PostgreSQL       │
                     │                      (RDS)           │
                     └─────────────────────────────────────┘

                     ┌─────────────────────────────────────┐
                     │         Local (mock mode)            │
                     │                                     │
Mock ─── MQTT ─────► │  Mosquitto → Mock Receiver          │
                     │           → Dashboard API ──► PG    │
                     └─────────────────────────────────────┘
```

## 빠른 시작 (Local Mock Mode)

### Prerequisites

- Python 3.11+
- Docker (PostgreSQL 실행용)
- pip

### 1. PostgreSQL 실행 및 스키마 적용

```bash
chmod +x scripts/init-local-postgres.sh
./scripts/init-local-postgres.sh
```

### 2. 환경변수 설정

```bash
cp config/aws.env.example .env
# .env 파일에서 AWS_MODE=mock 확인
```

### 3. 의존성 설치

```bash
pip install -r apps/dashboard-backend/requirements.txt
```

### 4. 서버 실행

```bash
cd apps/dashboard-backend
uvicorn src.api:app --host 0.0.0.0 --port 8080 --reload
```

### 5. API 테스트

```bash
# Health check
curl http://localhost:8080/health

# Event ingest (valid payload)
curl -X POST http://localhost:8080/api/v1/events/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "EVT-20250519120000-001",
    "site_id": "SITE-001",
    "device_id": "CAM-001",
    "event_type": "FALL_DETECTED",
    "risk_level": "CRITICAL",
    "confidence": 0.92,
    "model_version": "v1.0.0-tao-ds",
    "timestamp": "2025-05-19T12:00:00.123Z",
    "context_summary": "작업장 A구역 낙상 감지",
    "clip_s3_key": null,
    "idempotency_key": "SITE-001:EVT-20250519120000-001"
  }'

# Event list
curl http://localhost:8080/api/v1/events

# Event detail
curl http://localhost:8080/api/v1/events/EVT-20250519120000-001

# Device list
curl http://localhost:8080/api/v1/devices

# Model versions
curl http://localhost:8080/api/v1/models

# Schema validation (no DB required)
curl -X POST http://localhost:8080/api/v1/validate/event \
  -H "Content-Type: application/json" \
  -d '{"event_type": "INVALID_TYPE"}'
```

## Mock MQTT Receiver

로컬 Mosquitto에 연결하여 IoT Core를 모사합니다.

```bash
# Mosquitto 실행 (docker compose 또는)
docker run -d --name mosquitto -p 1883:1883 eclipse-mosquitto:2

# Mock receiver 시작
pip install paho-mqtt
chmod +x scripts/mock-aws-iot-receiver.sh
./scripts/mock-aws-iot-receiver.sh

# 다른 터미널에서 테스트 메시지 발행
mosquitto_pub -h localhost -t "safety/SITE-001/events" -m '{
  "event_id": "EVT-20250519120000-001",
  "site_id": "SITE-001",
  "device_id": "CAM-001",
  "event_type": "FALL_DETECTED",
  "risk_level": "CRITICAL",
  "confidence": 0.92,
  "model_version": "v1.0.0-tao-ds",
  "timestamp": "2025-05-19T12:00:00.123Z",
  "context_summary": "낙상 감지",
  "clip_s3_key": null,
  "idempotency_key": "SITE-001:EVT-20250519120000-001"
}'
```

## 테스트 실행

```bash
# Schema validation 테스트 (DB 불필요)
pytest apps/dashboard-backend/tests/test_event_validation.py -v

# API 테스트 (DB 불필요 - validation endpoint만)
pytest apps/dashboard-backend/tests/test_event_api.py -v

# 전체 테스트
pytest apps/dashboard-backend/tests/ -v
```

## API 엔드포인트 목록

| Method | Path | 설명 |
|--------|------|------|
| GET | /health | 서비스 헬스 체크 |
| POST | /api/v1/events/ingest | 이벤트 수신 (IoT Rule 대체) |
| POST | /api/v1/validate/event | 이벤트 스키마 검증 (테스트용) |
| GET | /api/v1/events | 이벤트 목록 (필터, 페이지네이션) |
| GET | /api/v1/events/{event_id} | 이벤트 상세 |
| POST | /api/v1/events/{event_id}/acknowledge | 이벤트 확인 처리 |
| POST | /api/v1/events/{event_id}/archive | 이벤트 보관 처리 |
| GET | /api/v1/devices | 장비 목록 |
| GET | /api/v1/devices/{device_id} | 장비 상세 |
| PATCH | /api/v1/devices/{device_id}/status | 장비 상태 변경 |
| GET | /api/v1/models | 모델 버전 목록 |
| GET | /api/v1/models/{model_version} | 모델 상세 |
| POST | /api/v1/edge/status | Edge 상태 수신 |
| GET | /api/v1/edge/status/latest | 최신 Edge 상태 |
| GET | /api/v1/system/health | 시스템 전체 헬스 |
| POST | /api/v1/auth/login | 로그인 (mock) |
| WS | /ws/dashboard | WebSocket 실시간 스트림 |

## 환경변수

| 변수 | 기본값 | 설명 |
|------|--------|------|
| AWS_MODE | mock | mock: 로컬, live: AWS 연결 |
| CLOUD_DB_HOST | localhost | PostgreSQL 호스트 |
| CLOUD_DB_PORT | 5432 | PostgreSQL 포트 |
| CLOUD_DB_NAME | safety_platform | DB 이름 |
| CLOUD_DB_USER | safety_admin | DB 사용자 |
| CLOUD_DB_PASSWORD | safety_password | DB 비밀번호 |
| SITE_ID | SITE-001 | 현장 ID |
| DASHBOARD_PORT | 8080 | API 서버 포트 |
| LOG_LEVEL | INFO | 로그 레벨 |

## 프로젝트 구조

```
apps/dashboard-backend/
├── src/
│   ├── __init__.py
│   ├── api.py          # FastAPI 엔드포인트 (메인)
│   ├── config.py       # 환경변수 기반 설정
│   ├── database.py     # PostgreSQL 연결 관리
│   ├── schemas.py      # Pydantic v2 스키마 (검증)
│   ├── crud.py         # DB CRUD operations
│   └── models.py       # 추가 데이터 모델
├── tests/
│   ├── test_event_validation.py  # 스키마 검증 테스트
│   └── test_event_api.py         # API 테스트
├── config/
│   └── dashboard-backend.yaml
├── requirements.txt
├── Dockerfile
└── README.md
```

## 비용 고려사항

| 항목 | 예상 비용 | 비고 |
|------|-----------|------|
| RDS PostgreSQL (t3.micro) | ~$15/month | 프리 티어 대상 |
| IoT Core (1 thing) | ~$1/month | 메시지 기반 과금 |
| S3 (4.5GB/month) | ~$2/month | 클립 저장 |
| Lambda (IoT Rule) | ~$0.5/month | 이벤트 처리 |
| **합계** | **~$20/month** | Platform 1.0, 1 site |

## TODO (Platform 2.0+)

- [ ] JWT 인증 실제 구현 (현재 mock)
- [ ] WebSocket Redis pub/sub 연동
- [ ] S3 pre-signed URL 생성 API
- [ ] 모델 배포 상태 관리 API
- [ ] Event context (inference_detail) 저장
- [ ] Device health history API
- [ ] 다중 사이트 지원
- [ ] Alembic DB migration
