# Dashboard Backend API

> 관리자 대시보드를 위한 REST API + WebSocket 서비스

## 역할

- 실시간 현황 데이터 제공 (WebSocket)
- 이벤트 로그 조회·필터링
- 장비·작업자 상태 조회
- 시스템 모니터링 데이터 제공
- 관리자 인증 (JWT)
- 알람 해제 명령 프록시

## API 엔드포인트

### 인증
| Method | Path | 설명 |
|--------|------|------|
| POST | /api/v1/auth/login | 로그인 (JWT 발급) |
| POST | /api/v1/auth/refresh | 토큰 갱신 |
| GET | /api/v1/auth/me | 현재 사용자 정보 |

### 대시보드 현황
| Method | Path | 설명 |
|--------|------|------|
| GET | /api/v1/dashboard/summary | 전체 현황 요약 |
| GET | /api/v1/dashboard/devices | 장비 상태 목록 |
| GET | /api/v1/dashboard/workers | 작업자 상태 목록 |
| WS | /ws/dashboard | 실시간 데이터 스트림 |

### 이벤트
| Method | Path | 설명 |
|--------|------|------|
| GET | /api/v1/events | 이벤트 목록 (필터) |
| GET | /api/v1/events/{id} | 이벤트 상세 |
| POST | /api/v1/events/{id}/acknowledge | 알람 해제 |

### 시스템
| Method | Path | 설명 |
|--------|------|------|
| GET | /api/v1/system/health | 전 서비스 상태 |
| GET | /api/v1/system/metrics | 시스템 메트릭 |

## 기술 스택

- FastAPI + WebSocket
- JWT (python-jose)
- bcrypt (passlib)
- Redis (실시간 데이터 소스)
