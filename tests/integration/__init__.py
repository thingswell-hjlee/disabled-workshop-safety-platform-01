"""
Platform 1.0 Integration Tests
================================
Redis Streams publish/consume, Edge mock producer, AWS mock receiver,
PostgreSQL storage 통합 테스트 모듈.

이 모듈은 실제 Redis (fakeredis 또는 docker Redis) 환경에서
이벤트 흐름의 통합 동작을 검증한다.
"""
