# Platform 1.0 개발 순서 (Development Sequence)

> **참조:** docs/tasks.md | docs/design.md
> **핵심:** Critical Path 기반 병렬 개발 + 의존성 관리

---

## 1. Critical Path (20주)

```
M1 인프라 (W1~W4)
 │
 ├──→ M2 DeepStream 파이프라인 (W5~W10) ──────────────────┐
 │         │                                               │
 │         └──→ M3 센서·이벤트 엔진 (W11~W14)              │
 │                    │                                    │
 │                    └──→ M4 알람·대시보드 (W15~W18)       │
 │                              │                          │
 │                              └──→ M6 통합 검수 (W22~W24)│
 │                                        ▲                │
 └──→ M5 클라우드·학습 (W19~W21) ──────────┘               │
      (M2 완료 후 병렬 가능)                                │
```

**Critical Path:** M1 → M2 → M3 → M4 → M6 = 20주
**병렬 경로:** M5는 W19부터 독립 진행 (M2 결과물만 필요)

---

## 2. 주차별 개발 순서

| 주차 | 마일스톤 | 핵심 작업 | 산출물 |
|------|----------|-----------|--------|
| W1~W2 | M1-S1 | GPU 서버 셋업, NVIDIA 환경, 네트워크 | 서버 Ready |
| W3~W4 | M1-S2 | 장비 설치, Docker, CI/CD | 인프라 완료 |
| W5~W6 | M2-S3 | DeepStream 기본 + PGIE | 사람 감지 동작 |
| W7~W8 | M2-S4 | Tracker + SGIE 행동 분석 | 낙상/쓰러짐 감지 |
| W9~W10 | M2-S5 | Analytics + 이벤트 Redis 발행 | 전체 파이프라인 |
| W11~W12 | M3-S6 | 센서 서비스 + 이벤트 엔진 | 위험등급 판정 |
| W13~W14 | M3-S7 | 이벤트 라우팅 + 클립 + 통합 | 융합 판정 완성 |
| W15~W16 | M4-S8 | 알람 GPIO + Backend API | 알람+API 동작 |
| W17~W18 | M4-S9 | Dashboard UI MVP | 관리 UI 완성 |
| W19~W21 | M5-S10 | AWS IoT + TAO 기본 + 모델 배포 | 클라우드 연동 |
| W22~W24 | M6-S11 | E2E + 72시간 + 납품 | **검수 합격** |

---

## 3. 의존성 매트릭스

| 작업 | 선행 조건 | 후행 작업 | 병렬 가능 |
|------|-----------|-----------|-----------|
| DeepStream 파이프라인 | GPU 서버 + 카메라 설치 | 이벤트 엔진 | - |
| Event Engine | DeepStream Redis 발행 | 알람, 대시보드, 클라우드 | - |
| Device Gateway | MQTT 브로커 + 밴드/센서 설치 | Event Engine 통합 | DeepStream과 병렬 |
| Alarm Controller | Event Engine 라우팅 | 통합 테스트 | Dashboard와 병렬 |
| Dashboard Backend | Event Engine 라우팅 | Dashboard UI | Alarm과 병렬 |
| Dashboard UI | Backend API 완성 | 통합 테스트 | - |
| AWS Sync | Event Engine 클라우드 큐 | 통합 테스트 | Dashboard와 병렬 |
| TAO 학습 환경 | 학습 서버 구축 | 모델 배포 경로 | Edge 개발과 병렬 |
| 모델 배포 | TAO 환경 + DeepStream 핫스왑 API | 통합 테스트 | - |

---

## 4. 병렬 개발 전략

### 4.1 팀 구성별 병렬화

```
W5~W10:
  [AI팀] → DeepStream 파이프라인 (PGIE→Tracker→SGIE→Analytics)
  [Dev팀] → Device Gateway 기본 구조 (M3 사전 준비)
  [Infra] → Docker Compose 고도화

W11~W14:
  [AI팀] → DeepStream 튜닝 + 성능 최적화
  [Dev팀] → Event Engine + Sensor Service 구현
  [Dev팀] → Local Storage + Rolling Buffer

W15~W18:
  [Dev팀] → Alarm Controller + Dashboard Backend
  [FE팀] → Dashboard UI (Backend API 완성 즉시 시작)
  [Cloud] → AWS 인프라 구축 (M5 사전 준비)

W19~W21:
  [Dev팀] → AWS Sync Agent
  [AI팀] → TAO 환경 + 모델 배포 경로
  [FE팀] → Dashboard UI 완성 + 폴리싱
```

### 4.2 인터페이스 선행 정의

병렬 개발을 위해 **인터페이스를 먼저 확정**:

| 인터페이스 | 확정 시점 | 의존하는 팀 |
|-----------|-----------|-------------|
| Redis Stream 스키마 (stream:ds-events) | W5 | Dev (Event Engine) |
| Redis Stream 스키마 (stream:sensors) | W5 | Dev (Event Engine) |
| Event Engine 출력 스키마 (alarms/dashboard/cloud) | W10 | Dev (Alarm, Dashboard, Cloud) |
| Dashboard Backend API 명세 | W14 | FE (Dashboard UI) |
| 모델 배포 API (/models/{id}/reload) | W9 | AI (TAO 배포) |

---

## 5. 스프린트 정의

| Sprint | 기간 | 목표 | 데모 가능 산출물 |
|--------|------|------|-----------------|
| S1 | W1~W2 | GPU 서버 부팅, 네트워크 | nvidia-smi + DeepStream 샘플 |
| S2 | W3~W4 | 전 장비 신호 확인 | 카메라 ffprobe + MQTT 수신 |
| S3 | W5~W6 | 8채널 PGIE 사람 감지 | bbox 표시 영상 8채널 |
| S4 | W7~W8 | 추적 + 행동 분류 | fall/normal 분류 표시 |
| S5 | W9~W10 | ROI + 이벤트 Redis | Redis에서 이벤트 JSON 수신 |
| S6 | W11~W12 | 센서 이벤트 + 위험등급 | 등급 판정 로그 확인 |
| S7 | W13~W14 | 융합 판정 + 클립 | 낙상→CRITICAL→클립 생성 |
| S8 | W15~W16 | 알람 동작 + API | 물리 사이렌 동작 |
| S9 | W17~W18 | Dashboard MVP | 8채널 영상 + 이벤트 목록 |
| S10 | W19~W21 | AWS + 모델 배포 | 클라우드 이벤트 수신 확인 |
| S11 | W22~W24 | 검수 합격 | **최종 검수 보고서** |

---

## 6. 개발 시작 우선순위 (Top 10)

| 순위 | 작업 | 이유 |
|------|------|------|
| 1 | GPU 서버 + DeepStream 환경 | 전체 파이프라인의 기반 |
| 2 | 8채널 RTSP 수집 + PGIE 감지 | Critical Path 시작점 |
| 3 | nvtracker + SGIE 행동 분석 | AI 감지 핵심 기능 |
| 4 | nvdsanalytics ROI + 이벤트 발행 | 위험 감지 완성 |
| 5 | Event Engine 위험등급 판정 | 이벤트→알람 연결고리 |
| 6 | Alarm Controller GPIO 제어 | 안전 기능 핵심 |
| 7 | Device Gateway 센서 수집 | 센서 융합 판단 |
| 8 | 네트워크 장애 독립 동작 구조 | 안전 필수 요건 |
| 9 | Dashboard Backend API | UI 연동 기반 |
| 10 | AWS IoT 이벤트 전송 | 원격 모니터링 |

---

## 변경 이력

| 버전 | 일자 | 내용 |
|------|------|------|
| 1.0 | 2025-05-19 | Platform 1.0 개발 순서 초안 |
