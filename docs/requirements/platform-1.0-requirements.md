# Platform 1.0 Requirements Overview

## 1. 문서 목적

Platform 1.0의 전체 요구사항을 개괄하고, 세부 요구사항 문서로의 네비게이션을 제공한다.

## 2. Platform 1.0 범위 정의

### 2.1 목표

> 전체 시스템의 가장 필수적이고 기본적인 기능을 **통합 동작**시키는 것

### 2.2 핵심 파이프라인

```
[센서/카메라/밴드] → [데이터 수집] → [AI 추론] → [위험 판정] → [알람 동작] → [대시보드 표시]
```

### 2.3 구현 범위 요약

| 도메인 | Platform 1.0 범위 |
|--------|-------------------|
| 장비 연동 | 8 Camera + 8 Band + 2 Sensor + Fire + NVR |
| AI 추론 | 낙상, 이상행동, 위험구역 침입, 센서 임계치, 바이오 이상 |
| 알람 | 접점연동 사이렌/경광등 + 대시보드 알림 |
| 대시보드 | 실시간 현황, 이벤트 로그, 시스템 상태 (MVP) |
| 클라우드 | 이벤트 전송, 원격 모니터링, 모델 버전 관리 |
| 학습 서버 | 데이터 수집, Fine-tuning, 모델 최적화, Edge 배포 |

## 3. 요구사항 분류 체계

### 3.1 기능 요구사항 (FR)

| 분류 | ID 접두사 | 문서 |
|------|-----------|------|
| 장비 연동 | FR-DEV-xxx | [functional-requirements.md](./functional-requirements.md) |
| AI 추론 | FR-AI-xxx | [functional-requirements.md](./functional-requirements.md) |
| 알람·알림 | FR-ALM-xxx | [functional-requirements.md](./functional-requirements.md) |
| 대시보드 | FR-DSH-xxx | [functional-requirements.md](./functional-requirements.md) |
| 클라우드 | FR-CLD-xxx | [functional-requirements.md](./functional-requirements.md) |
| 학습 서버 | FR-TRN-xxx | [functional-requirements.md](./functional-requirements.md) |

### 3.2 비기능 요구사항 (NFR)

| 분류 | 문서 |
|------|------|
| 성능 | [non-functional-requirements.md](./non-functional-requirements.md) |
| 가용성·안정성 | [non-functional-requirements.md](./non-functional-requirements.md) |
| 확장성 | [non-functional-requirements.md](./non-functional-requirements.md) |
| 보안 | [non-functional-requirements.md](./non-functional-requirements.md) |
| 운영·유지보수 | [non-functional-requirements.md](./non-functional-requirements.md) |

## 4. 우선순위 정의

| 등급 | 설명 | 검수 영향 |
|------|------|-----------|
| **P0 (필수)** | Platform 1.0 검수 합격에 반드시 필요 | 미충족 시 검수 불합격 |
| **P1 (중요)** | 출시에 포함되어야 하나 일부 제한 허용 | 제한적 동작 시 조건부 합격 |
| **P2 (권장)** | 포함되면 좋으나 2.0으로 이월 가능 | 미구현 시에도 합격 |

## 5. 검수 기준 요약

### 5.1 기능 검수 (P0 항목)

| # | 검수 항목 | 합격 기준 |
|---|-----------|-----------|
| 1 | 전 장비 동시 연동 | 8CAM + 8BAND + 2ENV + FIRE 동시 수신 |
| 2 | AI 위험 감지 | 낙상·이상행동·위험구역 감지율 ≥ 80% |
| 3 | 알람 동작 | CRITICAL 이벤트 → 5초 이내 현장 경보 |
| 4 | 네트워크 독립 | 인터넷 차단 시 감지→판단→알람 정상 동작 |
| 5 | 연속 운영 | 72시간 무중단 운영 |
| 6 | 클라우드 동기화 | 네트워크 복구 후 5분 이내 이벤트 동기화 |
| 7 | 모델 배포 | 학습서버→Edge 무중단 배포 성공 |

### 5.2 검수 절차

1. 단위 테스트 → 2. 통합 테스트 → 3. 시나리오 테스트 → 4. 장애 테스트 → 5. 장기 운영 테스트

## 6. 관련 문서

| 문서 | 설명 |
|------|------|
| [functional-requirements.md](./functional-requirements.md) | 기능 요구사항 상세 |
| [non-functional-requirements.md](./non-functional-requirements.md) | 비기능 요구사항 상세 |
| [../../.kiro/specs/inception.md](../../.kiro/specs/inception.md) | 프로젝트 기획서 |
| [../../.kiro/specs/requirements.md](../../.kiro/specs/requirements.md) | 전체 요구사항 원본 |

---

*버전: 0.1 | 작성일: 2025-05-19*
