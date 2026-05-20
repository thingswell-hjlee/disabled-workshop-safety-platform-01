# Platform 1.0 User Story Test Result Template

> **Purpose:** 통합시험 결과를 유저스토리별 PASS/FAIL로 정리하는 리포트 템플릿
> **사용 시점:** PR 병합 전 검증, 릴리스 검증, 정기 회귀 시험
> **Reference:** docs/user-story-to-test-traceability.md

---

## 사용 방법

1. 이 템플릿을 복사하여 `docs/test-results/YYYY-MM-DD-{목적}.md` 파일로 생성한다.
2. 테스트를 실행하고 각 유저스토리별 결과를 기록한다.
3. 미통과 항목에 대해 원인과 조치 계획을 작성한다.
4. PR 본문 또는 코멘트에 결과 링크를 첨부한다.

---

## Test Result Report

### 기본 정보

| 항목 | 내용 |
|------|------|
| **보고일** | YYYY-MM-DD |
| **시험 목적** | (예: PR #XX 병합 전 검증 / Platform 1.0 릴리스 검증) |
| **시험 환경** | (예: fakeredis only / Docker Redis+PostgreSQL / 실 Edge 환경) |
| **실행자** | (세션 또는 담당자) |
| **브랜치** | (예: feature/integration-schema-validation) |
| **커밋** | (예: 7454b37) |
| **Python 버전** | (예: 3.11.x) |
| **pytest 버전** | (예: 8.4.x) |

---

### 실행 명령

```bash
# 실행한 명령을 기록
pytest tests/ -v --tb=short -k "not Postgres"
```

---

### 전체 요약

| 지표 | 값 |
|------|-----|
| **총 테스트 수** | _____ |
| **PASSED** | _____ |
| **FAILED** | _____ |
| **SKIPPED** | _____ |
| **ERROR** | _____ |
| **실행 시간** | _____s |
| **전체 판정** | ✅ PASS / ❌ FAIL |

---

### 유저스토리별 결과

#### S1: Edge Device SW

| User Story | 제목 | AC 수 | PASS | FAIL | SKIP | 판정 |
|------------|------|-------|------|------|------|------|
| US-EDGE-001 | RTSP 카메라 수집 | 5 | ___ | ___ | ___ | ⬜ |
| US-EDGE-002 | 낙상/쓰러짐 이벤트 생성 | 6 | ___ | ___ | ___ | ⬜ |
| US-EDGE-003 | Redis Streams 이벤트 발행 | 7 | ___ | ___ | ___ | ⬜ |
| US-EDGE-004 | 카메라 연결 끊김/재연결 | 4 | ___ | ___ | ___ | ⬜ |

#### S2: AWS Cloud SW

| User Story | 제목 | AC 수 | PASS | FAIL | SKIP | 판정 |
|------------|------|-------|------|------|------|------|
| US-AWS-001 | Edge 이벤트 수신 | 5 | ___ | ___ | ___ | ⬜ |
| US-AWS-002 | 이벤트 DB 저장 | 5 | ___ | ___ | ___ | ⬜ |
| US-AWS-003 | 이벤트 조회 API | 5 | ___ | ___ | ___ | ⬜ |
| US-AWS-004 | 장비 상태 저장 | 4 | ___ | ___ | ___ | ⬜ |

#### S3: AI Training SW

| User Story | 제목 | AC 수 | PASS | FAIL | SKIP | 판정 |
|------------|------|-------|------|------|------|------|
| US-AI-001 | 모델 패키지 생성 | 5 | ___ | ___ | ___ | ⬜ |
| US-AI-002 | 모델 버전 검증 | 5 | ___ | ___ | ___ | ⬜ |
| US-AI-003 | 학습 데이터셋 구조 | 4 | ___ | ___ | ___ | ⬜ |

#### S4: Integration Test

| User Story | 제목 | AC 수 | PASS | FAIL | SKIP | 판정 |
|------------|------|-------|------|------|------|------|
| US-INT-001 | Schema Validation | 6 | ___ | ___ | ___ | ⬜ |
| US-INT-002 | Edge→Redis→AWS E2E | 6 | ___ | ___ | ___ | ⬜ |
| US-INT-003 | Model Package Validation | 5 | ___ | ___ | ___ | ⬜ |

---

### 판정 기준

| 기호 | 의미 | 조건 |
|------|------|------|
| ✅ | PASS | 해당 US의 모든 매핑된 TC가 PASS |
| ⚠️ | PARTIAL | 1개 이상 SKIP이나 NOT_IMPL 존재 (FAIL은 없음) |
| ❌ | FAIL | 1개 이상 FAIL 존재 |
| ⬜ | NOT_TESTED | 테스트 미실행 |

---

### FAIL 상세 (해당 시 작성)

| # | User Story | TC ID | 실패 테스트 | 오류 메시지 | 원인 분석 | 조치 계획 |
|---|-----------|-------|------------|------------|-----------|-----------|
| 1 | | | | | | |
| 2 | | | | | | |
| 3 | | | | | | |

---

### 미구현(NOT_IMPL) 항목 현황

| # | User Story | AC ID | 설명 | 담당 세션 | 예상 구현 PR |
|---|-----------|-------|------|-----------|-------------|
| 1 | | | | | |
| 2 | | | | | |

---

### 리스크 및 특이사항

| # | 항목 | 영향도 | 설명 |
|---|------|--------|------|
| 1 | | | |
| 2 | | | |

---

### 최종 판정

| 항목 | 결과 |
|------|------|
| **병합 가능 여부** | ✅ 가능 / ❌ 불가 / ⚠️ 조건부 가능 |
| **조건** | (조건부 시 기재) |
| **다음 액션** | |

---

### 서명

| 역할 | 이름 | 날짜 | 서명 |
|------|------|------|------|
| 시험 실행 | | | |
| 시험 검토 | | | |
| 병합 승인 | | | |

---

---

## 예시: PR #21 Integration Test 결과

> 아래는 이 템플릿의 실제 사용 예시입니다.

### 기본 정보

| 항목 | 내용 |
|------|------|
| **보고일** | 2025-05-20 |
| **시험 목적** | PR #21 Integration Test 병합 전 검증 |
| **시험 환경** | Docker Redis 7 (port 6380) + PostgreSQL 15 (port 5433) |
| **실행자** | Integration Test Session (S4) |
| **브랜치** | feature/integration-schema-validation |
| **커밋** | 7454b37 |
| **Python 버전** | 3.9.25 |
| **pytest 버전** | 8.4.2 |

### 실행 명령

```bash
pytest tests/ -v --tb=short
```

### 전체 요약

| 지표 | 값 |
|------|-----|
| **총 테스트 수** | 230 |
| **PASSED** | 230 |
| **FAILED** | 0 |
| **SKIPPED** | 0 |
| **ERROR** | 0 |
| **실행 시간** | 0.40s |
| **전체 판정** | ✅ PASS |

### 유저스토리별 결과 (예시)

#### S4: Integration Test

| User Story | 제목 | AC 수 | PASS | FAIL | SKIP | 판정 |
|------------|------|-------|------|------|------|------|
| US-INT-001 | Schema Validation | 6 | 6 | 0 | 0 | ✅ |
| US-INT-002 | Edge→Redis→AWS E2E | 6 | 6 | 0 | 0 | ✅ |
| US-INT-003 | Model Package Validation | 5 | 5 | 0 | 0 | ✅ |

#### S1: Edge Device SW (PR #21 테스트 기준)

| User Story | 제목 | AC 수 | PASS | FAIL | SKIP | 판정 |
|------------|------|-------|------|------|------|------|
| US-EDGE-001 | RTSP 카메라 수집 | 5 | 0 | 0 | 5 | ⬜ |
| US-EDGE-002 | 낙상/쓰러짐 이벤트 생성 | 6 | 5 | 0 | 1 | ⚠️ |
| US-EDGE-003 | Redis Streams 이벤트 발행 | 7 | 7 | 0 | 0 | ✅ |
| US-EDGE-004 | 카메라 연결 끊김/재연결 | 4 | 3 | 0 | 1 | ⚠️ |

### 최종 판정

| 항목 | 결과 |
|------|------|
| **병합 가능 여부** | ✅ 가능 |
| **조건** | S4 담당 범위(US-INT-*) 전체 PASS 확인 |
| **다음 액션** | PR #22 (Edge fix) → PR #23 (Training fix) → PR #24 (AWS fix) |

---

*템플릿 작성: Integration Test Session (S4) | 버전: 1.0*
