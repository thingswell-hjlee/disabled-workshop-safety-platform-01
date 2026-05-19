# Database

데이터베이스 스키마 및 초기 데이터 관리입니다.

## 구성

| 폴더 | 설명 |
|------|------|
| `migrations/` | 스키마 마이그레이션 (버전 관리) |
| `seeds/` | 초기 데이터 (장비 설정, 기본 계정, 임계치 등) |

## 데이터베이스

| DB | 용도 | 위치 |
|----|------|------|
| PostgreSQL | 이벤트, 메타데이터, 사용자 | Cloud (RDS) + Local |
| Redis | 실시간 큐, 캐시, 세션 | Edge Local |
| SQLite | 오프라인 이벤트 백업 | Edge Local |

## 핵심 테이블 (Platform 1.0)

- `events` - 안전 이벤트 기록
- `devices` - 장비 정보 및 상태
- `workers` - 작업자 정보
- `users` - 관리자 계정
- `model_versions` - AI 모델 버전 이력
- `alarm_logs` - 알람 동작 이력
