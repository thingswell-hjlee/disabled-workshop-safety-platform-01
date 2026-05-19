# Event Processor Service

> 이벤트 수신 → 위험등급 판정 → 알람/대시보드/클라우드 라우팅을 담당하는 서비스

## 역할

- AI Inference 이벤트 수신 (stream:events)
- 위험등급 판정 (CRITICAL/WARNING/NORMAL)
- 중복 이벤트 억제 (동일 장비 10초 이내)
- 이벤트 라우팅: 알람, 대시보드, 클라우드, NVR 클립
- 이벤트 상태 관리 (ACTIVE → ACKNOWLEDGED → ARCHIVED)
- 알람 해제(Acknowledge) 처리

## API 엔드포인트

| Method | Path | 설명 |
|--------|------|------|
| GET | /health | 서비스 헬스체크 |
| GET | /api/v1/events | 이벤트 목록 (필터링) |
| GET | /api/v1/events/{id} | 이벤트 상세 |
| POST | /api/v1/events/{id}/acknowledge | 알람 해제 |
| GET | /api/v1/events/stats | 처리 통계 |
| GET | /api/v1/rules | 판정 규칙 조회 |
| PUT | /api/v1/rules | 판정 규칙 변경 |

## Redis Stream I/O

**입력:** `stream:events`
**출력:** `stream:alarms`, `stream:dashboard`, `stream:cloud_queue`
