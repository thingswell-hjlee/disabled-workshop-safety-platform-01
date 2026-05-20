"""
Platform 1.0 End-to-End Tests
==============================
전체 이벤트 흐름을 시뮬레이션하는 E2E 테스트 모듈.

테스트 흐름:
1. Edge에서 샘플 이벤트 JSON 생성
2. event-message-schema validation
3. Redis Stream publish (stream:ds-events / stream:sensors)
4. Event Engine consume & process
5. Downstream streams 발행 (alarms, dashboard, cloud-queue, clip-trigger)
6. AWS mock receiver가 cloud-queue 소비
7. MQTT 페이로드 변환 검증
8. DB 저장 (mock 또는 local PostgreSQL)
9. 결과 리포트 생성
"""
