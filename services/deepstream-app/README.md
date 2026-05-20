# DeepStream 8-Channel Safety Pipeline

> Platform 1.0 - Edge AI 추론 서버 DeepStream 파이프라인 애플리케이션

## 개요

NVIDIA DeepStream SDK 기반 8채널 RTSP 카메라 실시간 영상 분석 파이프라인입니다.
낙상, 쓰러짐, 화재, 위험구역 침입, 위험행동을 감지하고 이벤트를 Redis Streams에 발행합니다.

### 주요 기능

| 기능 | 설명 |
|------|------|
| 8채널 RTSP 입력 | 카메라 8대 동시 처리 (1ch→4ch→8ch 확장) |
| TensorRT 추론 | FP16 최적화 모델 실시간 추론 |
| 객체 추적 | NvDCF 트래커 기반 멀티 객체 추적 |
| Redis 이벤트 발행 | `stream:ds-events` 스키마 준수 |
| 카메라 자동 재연결 | 연결 끊김 감지 및 자동 재시도 |
| 장비 상태 이벤트 | DEVICE_ONLINE/DEVICE_OFFLINE 발행 |
| Health Check | HTTP `/health` 엔드포인트 제공 |
| Mock Mode | GPU 없이 이벤트 발행 테스트 가능 |

## 아키텍처

```
┌─────────────────────────────────────────────────┐
│            DeepStream App (이 서비스)              │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌──────────┐  ┌──────────────┐  ┌───────────┐ │
│  │ Pipeline │→│ Event Schema │→│   Redis   │ │
│  │ Manager  │  │  Converter   │  │ Publisher │ │
│  └──────────┘  └──────────────┘  └───────────┘ │
│       ↑                               │        │
│  ┌──────────┐                    ┌────┴────┐   │
│  │  RTSP    │                    │ stream: │   │
│  │ Cameras  │                    │ds-events│   │
│  └──────────┘                    └─────────┘   │
│                                                 │
│  ┌──────────────────┐                          │
│  │ Health Check HTTP │ :8010                   │
│  └──────────────────┘                          │
└─────────────────────────────────────────────────┘
```

## 디렉토리 구조

```
services/deepstream-app/
├── configs/
│   ├── deepstream_config_1ch.txt   # 1채널 DeepStream 설정
│   ├── deepstream_config_4ch.txt   # 4채널 DeepStream 설정
│   ├── deepstream_config_8ch.txt   # 8채널 DeepStream 설정 (프로덕션)
│   ├── pgie_config.txt             # Primary GIE 추론 설정
│   ├── tracker_config.yml          # NvDCF 트래커 설정
│   ├── msg_conv_config.txt         # 메시지 변환 설정
│   └── labels.txt                  # 클래스 라벨
├── src/
│   ├── __init__.py
│   ├── __main__.py                 # Entry point
│   ├── app.py                      # 메인 애플리케이션 오케스트레이터
│   ├── config.py                   # 설정 로드 (환경변수 + JSON)
│   ├── event_schema.py             # 이벤트 스키마 (PR #16 준수)
│   ├── healthcheck.py              # HTTP 헬스체크 서버
│   ├── pipeline_manager.py         # DeepStream 파이프라인 관리
│   └── redis_publisher.py          # Redis Streams 발행
├── tests/
│   ├── conftest.py                 # 테스트 픽스처
│   ├── test_config.py              # 설정 테스트
│   ├── test_event_schema.py        # 스키마 검증 테스트
│   ├── test_pipeline_manager.py    # 파이프라인 테스트
│   ├── test_redis_publisher.py     # Redis 발행 테스트
│   └── test_integration.py         # 통합 테스트
├── Dockerfile
├── requirements.txt
├── pytest.ini
└── README.md
```

## 실행 방법

### 1. Mock Mode (GPU 불필요 - 개발/테스트)

```bash
# 사전조건: Redis 실행
docker run -d -p 6379:6379 redis:7-alpine

# 로컬 실행
cd services/deepstream-app
pip install -r requirements.txt
DEEPSTREAM_MOCK_MODE=true CAMERAS_CONFIG_PATH=../../config/cameras.example.json python -m src

# 또는 스크립트 사용
./scripts/run-deepstream-local.sh mock
```

### 2. Docker Compose (Mock Mode)

```bash
# Redis + DeepStream Mock 동시 실행
docker compose -f docker-compose.edge.yml up -d

# 로그 확인
docker logs -f safety-deepstream-mock
```

### 3. GPU Mode (NVIDIA GPU + DeepStream SDK 필요)

```bash
# 사전조건: NVIDIA GPU, DeepStream SDK 6.x/7.x, TensorRT 모델
DEEPSTREAM_MOCK_MODE=false ./scripts/run-deepstream-local.sh gpu
```

## 환경 변수

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `SITE_ID` | `SITE-001` | 사이트 ID |
| `DEEPSTREAM_MOCK_MODE` | `false` | Mock 모드 활성화 |
| `MOCK_EVENT_INTERVAL_SEC` | `5.0` | Mock 이벤트 생성 간격 (초) |
| `HEALTHCHECK_PORT` | `8010` | 헬스체크 HTTP 포트 |
| `REDIS_HOST` | `localhost` | Redis 호스트 |
| `REDIS_PORT` | `6379` | Redis 포트 |
| `REDIS_STREAM_NAME` | `stream:ds-events` | Redis Stream 이름 |
| `REDIS_MAX_STREAM_LENGTH` | `10000` | Stream 최대 길이 |
| `MODEL_VERSION` | `v1.0.0-tao-ds` | 모델 버전 |
| `MODEL_ENGINE_PATH` | `/models/active/pgie/model.engine` | TensorRT 엔진 경로 |
| `MAX_CHANNELS` | `8` | 최대 카메라 채널 수 |
| `BATCH_SIZE` | `8` | DeepStream 배치 크기 |
| `GPU_ID` | `0` | GPU 인덱스 |
| `CAMERAS_CONFIG_PATH` | `/app/config/cameras.json` | 카메라 설정 파일 경로 |
| `LOG_LEVEL` | `INFO` | 로그 레벨 |

## 카메라 설정

`config/cameras.example.json` 파일을 참조하여 카메라를 설정합니다:

```json
{
  "site_id": "SITE-001",
  "cameras": [
    {
      "camera_id": "CAM-001",
      "device_id": "CAM-001",
      "name": "작업장 A구역 프레스실",
      "rtsp_url": "rtsp://192.168.1.101:554/stream1",
      "enabled": true,
      "pipeline_index": 0,
      "resolution": { "width": 1920, "height": 1080 },
      "fps": 30,
      "zone_label": "A구역 프레스실"
    }
  ]
}
```

## Health Check

```bash
# 전체 상태
curl http://localhost:8010/health

# 카메라 상태
curl http://localhost:8010/health/cameras

# Redis 상태
curl http://localhost:8010/health/redis

# 파이프라인 상태
curl http://localhost:8010/health/pipeline
```

응답 예시:
```json
{
  "status": "healthy",
  "site_id": "SITE-001",
  "mock_mode": true,
  "model_version": "v1.0.0-tao-ds",
  "pipeline": {
    "running": true,
    "active_cameras": 8,
    "total_cameras": 8,
    "uptime_sec": 120
  },
  "redis": {
    "connected": true,
    "publish_count": 24,
    "error_count": 0
  }
}
```

## 테스트 실행

```bash
cd services/deepstream-app

# 전체 테스트 (Redis 필요)
pytest

# 단위 테스트만 (Redis 불필요)
pytest tests/test_event_schema.py tests/test_config.py tests/test_pipeline_manager.py

# 통합 테스트 (Redis 필요)
pytest tests/test_integration.py -v

# Redis 발행 테스트
pytest tests/test_redis_publisher.py -v
```

## 이벤트 스키마 (stream:ds-events)

PR #16 `redis-streams-schema.md` Section 1 준수:

```json
{
  "event_id": "EVT-20250519120000-001",
  "site_id": "SITE-001",
  "source_id": "pipeline-0",
  "device_id": "CAM-001",
  "event_type": "FALL_DETECTED",
  "timestamp": "2025-05-19T12:00:00.123Z",
  "model_version": "v1.0.0-tao-ds",
  "inference": "{\"pgie\":{\"class_id\":1,\"confidence\":0.92,\"label\":\"fall\",\"bbox\":{\"x\":0.35,\"y\":0.45,\"w\":0.15,\"h\":0.20}},\"tracker\":{\"object_id\":42,\"age_frames\":15},\"sgie\":null}",
  "analytics": "null"
}
```

## 감지 이벤트 유형

| event_type | Class ID | risk_level | 설명 |
|-----------|----------|-----------|------|
| `FALL_DETECTED` | 1 | CRITICAL | 낙상 감지 |
| `COLLAPSE_DETECTED` | 2 | CRITICAL | 쓰러짐 감지 |
| `FIRE_DETECTED` | 3 | CRITICAL | 화재 감지 |
| `ZONE_INTRUSION` | 4 | WARNING | 위험구역 침입 |
| `HAZARDOUS_ACTION` | 5 | WARNING | 위험행동 감지 |
| `STILLNESS_DETECTED` | - | WARNING | 장시간 미움직임 |
| `DEVICE_OFFLINE` | - | NORMAL | 카메라 연결 끊김 |
| `DEVICE_ONLINE` | - | NORMAL | 카메라 연결 복구 |

## TensorRT 모델 경로

```
/models/
├── active/pgie/
│   ├── model.engine          # TensorRT FP16 엔진
│   ├── labels.txt            # 클래스 라벨
│   └── config.txt            # nvinfer 설정
├── staged/{version}/         # 배포 대기 모델
└── rollback/{version}/       # 롤백 대기 모델
```

## RTSP 카메라 연결 확인

```bash
# 모든 카메라 연결 확인
./scripts/check-rtsp-cameras.sh

# 단일 카메라 확인
./scripts/check-rtsp-cameras.sh rtsp://192.168.1.101:554/stream1
```

## Redis Stream 모니터링

```bash
# 이벤트 실시간 확인
redis-cli XREAD COUNT 10 BLOCK 5000 STREAMS stream:ds-events $

# 스트림 길이 확인
redis-cli XLEN stream:ds-events

# 최근 이벤트 조회
redis-cli XREVRANGE stream:ds-events + - COUNT 5
```

## 확장 계획

- **Platform 1.0 (현재):** Mock mode + 기본 이벤트 발행, 8ch 설정 준비
- **Platform 2.0:** SGIE (Secondary GIE) 추가, 행동 분류기, 활동지수 연동
- **Platform 3.0:** Generative 재추론, 예측형 위험도 분석 통합
