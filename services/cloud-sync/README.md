# Cloud Sync Service

> Edge AI 서버에서 발생한 이벤트를 AWS 클라우드로 안정적으로 전송하는 서비스

## 역할

- 이벤트 데이터 AWS IoT Core (MQTT over TLS) 전송
- 네트워크 장애 시 로컬 Redis 큐에 이벤트 저장
- 네트워크 복구 시 큐잉된 이벤트 자동 재전송 (5분 이내)
- idempotency key 기반 중복 전송 방지
- 우선순위 기반 전송 (CRITICAL > WARNING > NORMAL)
- 영상 클립 S3 업로드

## 핵심 설계

- **Offline-First**: 네트워크 없어도 큐잉 동작
- **At-Least-Once**: 전송 보장 (idempotency로 중복 방지)
- **Priority Queue**: CRITICAL 이벤트 우선 전송
- **Exponential Backoff**: 실패 시 재시도 간격 증가

## API 엔드포인트

| Method | Path | 설명 |
|--------|------|------|
| GET | /health | 헬스체크 (클라우드 연결 상태 포함) |
| GET | /api/v1/sync/status | 동기화 상태 |
| GET | /api/v1/sync/queue | 대기 큐 상태 |
| POST | /api/v1/sync/flush | 즉시 전송 |
| POST | /api/v1/sync/pause | 동기화 일시 중지 |
| POST | /api/v1/sync/resume | 동기화 재개 |
| GET | /api/v1/sync/stats | 동기화 통계 |
| GET | /api/v1/sync/connection | 연결 정보 |
| POST | /api/v1/sync/reconnect | 재연결 시도 |

## Redis Stream 입력

- `stream:cloud_queue` (from event-processor)
