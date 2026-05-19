# Alarm Controller Service

> 접점연동 현장 경보 장치(사이렌, 경광등)를 GPIO로 직접 제어하는 서비스

## 역할

- CRITICAL 이벤트: 사이렌 + 경광등 동시 동작
- WARNING 이벤트: 경광등만 동작
- 수동 알람 해제 (Acknowledge)
- 알람 동작 이력 로깅
- Edge AI 서버에서 로컬 독립 동작 (클라우드 비의존)

## 핵심 설계

- **로컬 독립**: 네트워크 장애 시에도 알람 동작 보장
- **GPIO 직접 제어**: Edge AI 서버 GPIO를 통해 릴레이 직접 제어
- **이벤트 시간 제한**: CRITICAL은 수동 해제, WARNING은 5분 후 자동 해제

## API 엔드포인트

| Method | Path | 설명 |
|--------|------|------|
| GET | /health | 헬스체크 (GPIO 상태 포함) |
| GET | /api/v1/alarm/status | 현재 알람 상태 |
| POST | /api/v1/alarm/trigger | 수동 알람 발동 |
| POST | /api/v1/alarm/clear | 알람 해제 |
| GET | /api/v1/alarm/logs | 알람 동작 이력 |
| POST | /api/v1/alarm/test | 알람 장비 테스트 |

## Redis Stream 입력

- `stream:alarms` (from event-processor)
