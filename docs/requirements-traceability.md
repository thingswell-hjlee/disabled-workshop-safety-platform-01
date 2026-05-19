# Requirements Traceability Matrix (요구사항 추적 매트릭스)

> **참조:** .kiro/specs/requirements.md (103개) | docs/design.md | docs/software-architecture.md
> **목적:** 모든 요구사항과 설계·구현·테스트 항목 간 추적성 확보
> **총 요구사항:** 103개 (P0: 74, P1: 23, P2: 6)

---

## 1. 매핑 규칙

### 1.1 컬럼 정의

| 컬럼 | 설명 |
|------|------|
| Requirement ID | 요구사항 고유 식별자 |
| Priority | P0 / P1 / P2 |
| Platform | 적용 플랫폼 (1.0 / 2.0) |
| Category | 기능 분류 |
| Design Section | design.md 내 관련 섹션 번호 |
| Implementation Module | software-architecture.md 내 구현 모듈 |
| Test Type | 테스트 유형 (Unit/Integration/E2E/Performance/Scenario) |
| Status | 상태 (Planned / In Progress / Done / Verified) |

### 1.2 Status 정의

| 상태 | 설명 |
|------|------|
| Planned | 설계 완료, 구현 대기 |
| In Progress | 구현 진행 중 |
| Done | 구현 완료, 테스트 대기 |
| Verified | 테스트 합격 확인 |

---

## 2. FR-DS: DeepStream 파이프라인 (23개)

| Requirement ID | Priority | Platform | Category | Design Section | Implementation Module | Test Type | Status |
|----------------|----------|----------|----------|----------------|----------------------|-----------|--------|
| FR-DS-001 | P0 | 1.0 | 영상수집 | §4.1 파이프라인 구조 | deepstream-pipeline-service | Integration | Planned |
| FR-DS-002 | P0 | 1.0 | 영상수집 | §4.1 nvstreammux | deepstream-pipeline-service | Unit | Planned |
| FR-DS-003 | P0 | 1.0 | 영상수집 | §4.1 GPU디코딩 | deepstream-pipeline-service | Performance | Planned |
| FR-DS-004 | P0 | 1.0 | 영상수집 | §4.1 해상도/FPS | deepstream-pipeline-service | Performance | Planned |
| FR-DS-005 | P1 | 1.0 | 영상수집 | §4.1 Source Group | deepstream-pipeline-service | Integration | Planned |
| FR-DS-006 | P0 | 1.0 | 영상수집 | §4.5 nvmsgconv | deepstream-pipeline-service, config-management | Unit | Planned |
| FR-DS-007 | P0 | 1.0 | 추론 | §4.2 PGIE | deepstream-pipeline-service, inference-service | Scenario | Planned |
| FR-DS-008 | P0 | 1.0 | 추론 | §5.1 TensorRT | inference-service | Unit | Planned |
| FR-DS-009 | P0 | 1.0 | 추론 | §4.3 SGIE | deepstream-pipeline-service, inference-service | Scenario | Planned |
| FR-DS-010 | P0 | 1.0 | 추론 | §5.3 성능목표 | deepstream-pipeline-service | Performance | Planned |
| FR-DS-011 | P0 | 1.0 | 추론 | §4.5 이벤트JSON | deepstream-pipeline-service | Unit | Planned |
| FR-DS-012 | P0 | 1.0 | 추론 | §4.2 threshold | config-management-service | Unit | Planned |
| FR-DS-013 | P1 | 1.0 | 추론 | §5.2 핫스왑 | inference-service | Integration | Planned |
| FR-DS-014 | P0 | 1.0 | 추적 | §4.3 nvtracker | deepstream-pipeline-service | Unit | Planned |
| FR-DS-015 | P0 | 1.0 | 추적 | §4.3 tracking_id | deepstream-pipeline-service | Integration | Planned |
| FR-DS-016 | P0 | 1.0 | 추적 | §4.4 Dwell Time | deepstream-pipeline-service | Scenario | Planned |
| FR-DS-017 | P1 | 1.0 | 추적 | §4.3 ID매핑 | deepstream-pipeline-service, event-engine | Integration | Planned |
| FR-DS-018 | P0 | 1.0 | 분석 | §4.4 ROI | deepstream-pipeline-service | Scenario | Planned |
| FR-DS-019 | P0 | 1.0 | 분석 | §4.4 YAML설정 | config-management-service | Unit | Planned |
| FR-DS-020 | P1 | 1.0 | 분석 | §4.4 Line Crossing | deepstream-pipeline-service | Integration | Planned |
| FR-DS-021 | P0 | 1.0 | 이벤트 | §4.5 nvmsgconv | deepstream-pipeline-service | Unit | Planned |
| FR-DS-022 | P0 | 1.0 | 이벤트 | §4.5 nvmsgbroker | deepstream-pipeline-service | Integration | Planned |
| FR-DS-023 | P0 | 1.0 | 녹화 | §11, §12 롤링버퍼 | rolling-buffer-service | Integration | Planned |

---

## 3. FR-TAO: TAO Toolkit 학습·최적화 (14개)

| Requirement ID | Priority | Platform | Category | Design Section | Implementation Module | Test Type | Status |
|----------------|----------|----------|----------|----------------|----------------------|-----------|--------|
| FR-TAO-001 | P0 | 1.0 | 환경구축 | §3.2 소프트웨어스택 | local-training-service | Unit | Planned |
| FR-TAO-002 | P0 | 1.0 | 환경구축 | §5.1 모델최적화 | local-training-service | Unit | Planned |
| FR-TAO-003 | P0 | 1.0 | 최적화 | §5.1 TensorRT변환 | local-training-service | Unit | Planned |
| FR-TAO-004 | P0 | 1.0 | 배포 | §5.2 엔진로드 | inference-service, deepstream-pipeline | Integration | Planned |
| FR-TAO-005 | P0 | 1.0 | 데이터 | §12, §13 데이터수집 | rolling-buffer-service, local-storage | Integration | Planned |
| FR-TAO-006 | P1 | 1.0 | 데이터 | §13 데이터가공 | local-training-service | Unit | Planned |
| FR-TAO-007 | P0 | 1.0 | 학습 | §2.3 모델배포경로 | local-training-service | Integration | Planned |
| FR-TAO-008 | P0 | 1.0 | 학습 | §2.3 평가 | local-training-service | Unit | Planned |
| FR-TAO-009 | P0 | 1.0 | 배포 | §2.3 End-to-End | local-training, model-management, inference | E2E | Planned |
| FR-TAO-010 | P1 | 1.0 | 배포 | §5.2 롤백 | inference-service, model-management | Integration | Planned |
| FR-TAO-011 | P2 | 2.0 | 고도화 | §19 확장고려 | local-training-service | Scenario | Planned |
| FR-TAO-012 | P2 | 2.0 | 고도화 | §19 확장고려 | local-training-service | Integration | Planned |
| FR-TAO-013 | P2 | 2.0 | 고도화 | §19 확장고려 | local-training-service | E2E | Planned |
| FR-TAO-014 | P2 | 2.0 | 고도화 | §19 확장고려 | model-management-service | Integration | Planned |

---

## 4. FR-DEV: 장비 연동 (15개)

| Requirement ID | Priority | Platform | Category | Design Section | Implementation Module | Test Type | Status |
|----------------|----------|----------|----------|----------------|----------------------|-----------|--------|
| FR-DEV-001 | P0 | 1.0 | 밴드 | §7.1 데이터흐름 | device-gateway-service | Integration | Planned |
| FR-DEV-002 | P0 | 1.0 | 밴드 | §7.2 MQTT토픽 | device-gateway-service | Unit | Planned |
| FR-DEV-003 | P0 | 1.0 | 밴드 | §7.2 수집주기 | device-gateway-service | Performance | Planned |
| FR-DEV-004 | P0 | 1.0 | 밴드 | §6.2 ID체계 | device-gateway-service, config-management | Unit | Planned |
| FR-DEV-005 | P1 | 1.0 | 밴드 | §7.3 이상판단 | device-gateway-service | Integration | Planned |
| FR-DEV-006 | P1 | 1.0 | 밴드 | §7.3 배터리 | device-gateway-service | Unit | Planned |
| FR-DEV-007 | P0 | 1.0 | 환경 | §8.1 데이터흐름 | device-gateway-service | Integration | Planned |
| FR-DEV-008 | P0 | 1.0 | 환경 | §8.2 수집주기 | device-gateway-service | Performance | Planned |
| FR-DEV-009 | P0 | 1.0 | 환경 | §8.3 임계치 | device-gateway-service | Scenario | Planned |
| FR-DEV-010 | P1 | 1.0 | 환경 | §8.1 두절감지 | device-gateway-service | Integration | Planned |
| FR-DEV-011 | P0 | 1.0 | 화재 | §9.1 GPIO연결 | device-gateway-service | Unit | Planned |
| FR-DEV-012 | P0 | 1.0 | 화재 | §9.2 즉시이벤트 | device-gateway-service | Performance | Planned |
| FR-DEV-013 | P0 | 1.0 | 화재 | §9.2 디바운싱 | device-gateway-service | Unit | Planned |
| FR-DEV-014 | P0 | 1.0 | NVR | §11.1 연속녹화 | rolling-buffer-service | Integration | Planned |
| FR-DEV-015 | P1 | 1.0 | NVR | §11.3 용량알림 | local-storage-service, logging-monitoring | Unit | Planned |

---

## 5. FR-EVT: 이벤트 처리·알람 (13개)

| Requirement ID | Priority | Platform | Category | Design Section | Implementation Module | Test Type | Status |
|----------------|----------|----------|----------|----------------|----------------------|-----------|--------|
| FR-EVT-001 | P0 | 1.0 | 이벤트 | §15.1 아키텍처 | event-engine-service | Integration | Planned |
| FR-EVT-002 | P0 | 1.0 | 이벤트 | §15.2 규칙 | event-engine-service | Unit | Planned |
| FR-EVT-003 | P0 | 1.0 | 이벤트 | §15.2 CRITICAL | event-engine-service | Scenario | Planned |
| FR-EVT-004 | P0 | 1.0 | 이벤트 | §15.2 WARNING | event-engine-service | Scenario | Planned |
| FR-EVT-005 | P0 | 1.0 | 이벤트 | §15.1 중복억제 | event-engine-service | Unit | Planned |
| FR-EVT-006 | P1 | 1.0 | 이벤트 | §15.2 YAML규칙 | event-engine-service, config-management | Unit | Planned |
| FR-EVT-007 | P0 | 1.0 | 이벤트 | §15.2 confidence | event-engine-service | Unit | Planned |
| FR-EVT-008 | P0 | 1.0 | 알람 | §10.2 알람정책 | alarm-control-service | E2E | Planned |
| FR-EVT-009 | P0 | 1.0 | 알람 | §10.2 WARNING | alarm-control-service | Scenario | Planned |
| FR-EVT-010 | P0 | 1.0 | 알람 | §10.2 Acknowledge | alarm-control-service, dashboard-backend | Integration | Planned |
| FR-EVT-011 | P0 | 1.0 | 알람 | §10.2 이력 | alarm-control-service, local-storage | Unit | Planned |
| FR-EVT-012 | P0 | 1.0 | 알람 | §10.3 Edge독립 | alarm-control-service | E2E | Planned |
| FR-EVT-013 | P1 | 1.0 | 알람 | §10.2 해제기록 | alarm-control-service | Unit | Planned |

---

## 6. FR-DSH: 관리자 대시보드 (12개)

| Requirement ID | Priority | Platform | Category | Design Section | Implementation Module | Test Type | Status |
|----------------|----------|----------|----------|----------------|----------------------|-----------|--------|
| FR-DSH-001 | P0 | 1.0 | 모니터링 | §17.2 메인페이지 | dashboard-frontend, deepstream-pipeline | Integration | Planned |
| FR-DSH-002 | P0 | 1.0 | 모니터링 | §17.2 센서표시 | dashboard-frontend, dashboard-backend | Integration | Planned |
| FR-DSH-003 | P0 | 1.0 | 모니터링 | §17.2 작업자 | dashboard-frontend, dashboard-backend | Integration | Planned |
| FR-DSH-004 | P0 | 1.0 | 모니터링 | §17.2 요약 | dashboard-frontend, dashboard-backend | Unit | Planned |
| FR-DSH-005 | P0 | 1.0 | 이벤트 | §17.2 이벤트로그 | dashboard-backend, local-storage | Integration | Planned |
| FR-DSH-006 | P1 | 1.0 | 이벤트 | §17.2 상세 | dashboard-frontend, dashboard-backend | Integration | Planned |
| FR-DSH-007 | P0 | 1.0 | 시스템 | §17.2 시스템상태 | dashboard-backend, logging-monitoring | Integration | Planned |
| FR-DSH-008 | P0 | 1.0 | 시스템 | §17.3 WebSocket | dashboard-backend, dashboard-frontend | Performance | Planned |
| FR-DSH-009 | P0 | 1.0 | 인증 | §17.2 JWT | dashboard-backend | Unit | Planned |
| FR-DSH-010 | P0 | 1.0 | 인증 | §17.2 계정CRUD | dashboard-backend | Unit | Planned |
| FR-DSH-011 | P1 | 1.0 | 인증 | §17.2 타임아웃 | dashboard-backend | Unit | Planned |
| FR-DSH-012 | P2 | 1.0 | 인증 | §17.3 WebPush | dashboard-frontend | Integration | Planned |

---

## 7. FR-CLD: 클라우드 연동 (8개)

| Requirement ID | Priority | Platform | Category | Design Section | Implementation Module | Test Type | Status |
|----------------|----------|----------|----------|----------------|----------------------|-----------|--------|
| FR-CLD-001 | P0 | 1.0 | 전송 | §16.1 전송아키텍처 | aws-sync-agent | Integration | Planned |
| FR-CLD-002 | P0 | 1.0 | 전송 | §16.4 오프라인큐 | aws-sync-agent | E2E | Planned |
| FR-CLD-003 | P1 | 1.0 | 전송 | §16.4 idempotency | aws-sync-agent | Unit | Planned |
| FR-CLD-004 | P0 | 1.0 | 저장 | §16.3 클립업로드 | aws-sync-agent, rolling-buffer | Integration | Planned |
| FR-CLD-005 | P0 | 1.0 | 모델 | §5.2 레지스트리 | model-management-service, aws-sync | Integration | Planned |
| FR-CLD-006 | P0 | 1.0 | 모니터링 | §17.1 원격접속 | dashboard-backend | Integration | Planned |
| FR-CLD-007 | P1 | 1.0 | 모델 | §2.3 모델배포 | model-management-service | Integration | Planned |
| FR-CLD-008 | P2 | 1.0 | 저장 | §16.4 보관정책 | aws-sync-agent | Unit | Planned |

---

## 8. NFR: 비기능 요구사항 (18개)

| Requirement ID | Priority | Platform | Category | Design Section | Implementation Module | Test Type | Status |
|----------------|----------|----------|----------|----------------|----------------------|-----------|--------|
| NFR-001 | P0 | 1.0 | 성능 | §2.1, §5.3 | deepstream-pipeline-service | Performance | Planned |
| NFR-002 | P0 | 1.0 | 성능 | §2.1 지연예산 | deepstream-pipeline, event-engine | Performance | Planned |
| NFR-003 | P0 | 1.0 | 성능 | §2.1 End-to-End | 전체 파이프라인 | E2E | Planned |
| NFR-004 | P1 | 1.0 | 성능 | §3.1 GPU사양 | deepstream-pipeline-service | Performance | Planned |
| NFR-005 | P1 | 1.0 | 성능 | §17.2 로딩 | dashboard-frontend | Performance | Planned |
| NFR-006 | P0 | 1.0 | 가용성 | §18.1 독립동작 | 전체 시스템 | E2E (72hr) | Planned |
| NFR-007 | P0 | 1.0 | 가용성 | §18.1 로컬독립 | 전체 시스템 | E2E | Planned |
| NFR-008 | P0 | 1.0 | 가용성 | §16.4 동기화 | aws-sync-agent | E2E | Planned |
| NFR-009 | P0 | 1.0 | 가용성 | §18.3 Watchdog | edge-ai-service (systemd) | Integration | Planned |
| NFR-010 | P0 | 1.0 | 가용성 | §18.1 장비격리 | deepstream-pipeline-service | Integration | Planned |
| NFR-011 | P1 | 1.0 | 가용성 | §18.1 GPU장애 | device-gateway, event-engine, alarm | E2E | Planned |
| NFR-012 | P0 | 1.0 | 확장성 | §19.2 site_id | 전체 데이터 모델 | Unit | Planned |
| NFR-013 | P1 | 1.0 | 확장성 | §19.2 설정외부화 | config-management-service | Unit | Planned |
| NFR-014 | P0 | 1.0 | 보안 | §16.1 TLS | aws-sync-agent | Integration | Planned |
| NFR-015 | P0 | 1.0 | 보안 | §17.2 JWT/bcrypt | dashboard-backend | Unit | Planned |
| NFR-016 | P1 | 1.0 | 보안 | §16 접근로그 | logging-monitoring-service | Unit | Planned |
| NFR-017 | P0 | 1.0 | 운영 | §3.3 Docker | edge-ai-service (docker-compose) | Integration | Planned |
| NFR-018 | P1 | 1.0 | 운영 | §16 /health + JSON | logging-monitoring-service | Unit | Planned |

---

## 9. 통계 요약

### 9.1 요구사항 개수 검증

| Category | Total | P0 | P1 | P2 | Planned | In Progress | Done | Verified |
|----------|-------|----|----|-----|---------|-------------|------|----------|
| FR-DS | 23 | 19 | 4 | 0 | 23 | 0 | 0 | 0 |
| FR-TAO | 14 | 8 | 2 | 4 | 14 | 0 | 0 | 0 |
| FR-DEV | 15 | 11 | 4 | 0 | 15 | 0 | 0 | 0 |
| FR-EVT | 13 | 11 | 2 | 0 | 13 | 0 | 0 | 0 |
| FR-DSH | 12 | 9 | 2 | 1 | 12 | 0 | 0 | 0 |
| FR-CLD | 8 | 5 | 2 | 1 | 8 | 0 | 0 | 0 |
| NFR | 18 | 11 | 7 | 0 | 18 | 0 | 0 | 0 |
| **합계** | **103** | **74** | **23** | **6** | **103** | **0** | **0** | **0** |

### 9.2 모듈별 요구사항 커버리지

| Implementation Module | 관련 요구사항 수 | P0 수 |
|----------------------|-----------------|-------|
| deepstream-pipeline-service | 24 | 20 |
| event-engine-service | 14 | 12 |
| device-gateway-service | 15 | 11 |
| alarm-control-service | 8 | 7 |
| dashboard-backend | 12 | 9 |
| dashboard-frontend | 7 | 5 |
| aws-sync-agent | 8 | 5 |
| rolling-buffer-service | 4 | 3 |
| inference-service | 6 | 4 |
| local-training-service | 10 | 6 |
| model-management-service | 5 | 3 |
| config-management-service | 5 | 3 |
| local-storage-service | 4 | 3 |
| logging-monitoring-service | 4 | 1 |
| edge-ai-service | 3 | 2 |

### 9.3 테스트 유형 분포

| Test Type | 요구사항 수 |
|-----------|------------|
| Unit | 36 |
| Integration | 38 |
| E2E | 12 |
| Performance | 10 |
| Scenario | 7 |
| **합계** | **103** |

---

## 변경 이력

| 버전 | 일자 | 내용 |
|------|------|------|
| 1.0 | 2025-05-19 | 103개 요구사항 추적 매트릭스 초안 |
