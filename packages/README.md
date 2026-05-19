# Packages

서비스 간 공유되는 라이브러리·SDK 모음입니다.

## 구성

| Package | 설명 |
|---------|------|
| `sdk-common` | 공통 유틸리티, ID 생성, 로깅, 설정 로더, 상수 정의 |
| `sdk-ai-event` | AI 이벤트 스키마 정의, 타입, 검증, 샘플 데이터 |

## 설계 원칙

- 모든 서비스가 동일한 데이터 스키마를 사용하도록 공유 패키지로 관리
- site_id, device_id, worker_id, event_id 등 ID 생성 로직 중앙화
- JSON Schema 기반 데이터 검증
