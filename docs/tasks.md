# Platform 1.0 개발 태스크 (Tasks)

> **참조:** docs/design.md | docs/software-architecture.md | .kiro/specs/requirements.md
> **범위:** Platform 1.0 (24주, 6마일스톤, 11스프린트, 92개 작업)
> **우선순위:** P0 74개 요구사항 완전 구현 + P1 23개 부분 구현

---

## 1. 마일스톤 개요

| MS | 이름 | 기간 | 스프린트 | 작업 수 | 핵심 산출물 |
|----|------|------|----------|---------|-------------|
| M1 | 인프라 구축 | W1~W4 | S1~S2 | 18 | GPU 서버, 네트워크, 장비 설치, Docker |
| M2 | DeepStream 파이프라인 | W5~W10 | S3~S5 | 21 | 8채널 수집·추론·추적·분석·이벤트 발행 |
| M3 | 센서 연동·이벤트 엔진 | W11~W14 | S6~S7 | 14 | 밴드/센서/화재 + 위험등급 판정 |
| M4 | 알람·대시보드 | W15~W18 | S8~S9 | 18 | GPIO 알람 + Dashboard MVP |
| M5 | 클라우드·학습 기반 | W19~W21 | S10 | 11 | AWS IoT + TAO 기본 + 모델 배포 |
| M6 | 통합 검수 | W22~W24 | S11 | 10 | E2E 테스트 + 72시간 + 납품 |
| | **합계** | **24주** | **11** | **92** | |

---

## 2. 작업 ID 체계

`T-M{마일스톤}-{순번}` (예: T-M1-001)

---


## 3. M1: 인프라 구축 (W1~W4, 18개 작업)

### Sprint 1 (W1~W2): 서버·네트워크

| ID | 작업 | 담당 | 소요 | 의존성 | 완료 기준 | 관련 요구사항 |
|----|------|------|------|--------|-----------|--------------|
| T-M1-001 | Edge AI 서버 HW 설치 (GPU, RAM, SSD) | Infra | 1d | - | 부팅 정상 | NFR-017 |
| T-M1-002 | Ubuntu 22.04 LTS + SSH 설정 | Infra | 0.5d | 001 | 원격 접속 | NFR-017 |
| T-M1-003 | NVIDIA GPU Driver 535+ 설치 | Infra | 0.5d | 002 | nvidia-smi 정상 | FR-DS-003 |
| T-M1-004 | CUDA 12.x + cuDNN 8.x 설치 | Infra | 0.5d | 003 | CUDA 샘플 실행 | FR-DS-008 |
| T-M1-005 | Docker 24.x + NVIDIA Container Toolkit | Infra | 0.5d | 004 | --gpus all 동작 | NFR-017 |
| T-M1-006 | DeepStream 7.x 컨테이너 pull + 실행 확인 | Infra | 0.5d | 005 | 샘플 앱 실행 | FR-DS-001 |
| T-M1-007 | 학습 서버 동일 환경 구축 (RTX 4090) | Infra | 2d | - | TAO 실행 확인 | FR-TAO-001 |
| T-M1-008 | 네트워크 VLAN 구성 (10/20/30/40) | Infra | 1d | 001 | VLAN ping | NFR-014 |
| T-M1-009 | 방화벽 규칙 설정 | Infra | 0.5d | 008 | 규칙 검증 | NFR-014 |

### Sprint 2 (W3~W4): 장비 설치·프로젝트 기반

| ID | 작업 | 담당 | 소요 | 의존성 | 완료 기준 | 관련 요구사항 |
|----|------|------|------|--------|-----------|--------------|
| T-M1-010 | IP Camera 8대 설치 + RTSP URL 확인 | HW | 2d | 008 | ffprobe 전 채널 | FR-DS-001,004 |
| T-M1-011 | 스마트밴드 8개 페어링 + BLE Gateway | HW | 1d | 008 | MQTT 수신 | FR-DEV-001 |
| T-M1-012 | 환경센서 2개 설치 + MQTT 발행 | HW | 0.5d | 008 | 데이터 수신 | FR-DEV-007 |
| T-M1-013 | 화재감지 접점 배선 + GPIO 신호 확인 | HW | 0.5d | 001 | 접점 테스트 | FR-DEV-011 |
| T-M1-014 | 접점연동 알람장치 설치 (사이렌/경광등) | HW | 0.5d | 001 | GPIO 동작 | FR-EVT-008 |
| T-M1-015 | NVR 설치 + 8채널 녹화 설정 | HW | 0.5d | 010 | 녹화 시작 | FR-DEV-014 |
| T-M1-016 | Git Repository 구조 + CI/CD 기본 | Dev | 1d | - | Docker build 자동 | NFR-017 |
| T-M1-017 | .env.example + 설정 템플릿 + Secret 관리 | Dev | 0.5d | 016 | 보안 검증 | NFR-015 |
| T-M1-018 | Docker Compose 전 서비스 정의 | Dev | 1d | 005 | compose up 성공 | NFR-017 |



## 4. M2: DeepStream 파이프라인 (W5~W10, 21개 작업)

### Sprint 3 (W5~W6): 기본 파이프라인

| ID | 작업 | 담당 | 소요 | 의존성 | 완료 기준 | 관련 요구사항 |
|----|------|------|------|--------|-----------|--------------|
| T-M2-001 | DeepStream 앱 프로젝트 구조 생성 | AI | 0.5d | M1 | 디렉토리 확인 | FR-DS-001 |
| T-M2-002 | 단일 RTSP 소스 디코딩 + 표시 | AI | 1d | 001 | 1채널 영상 | FR-DS-003 |
| T-M2-003 | 8채널 RTSP source_list.yml 작성 | AI | 0.5d | 002 | 8채널 동시 | FR-DS-001,006 |
| T-M2-004 | nvstreammux batch-size=8 설정 | AI | 0.5d | 003 | 배치 확인 | FR-DS-002 |
| T-M2-005 | PeopleNet NGC 모델 다운로드 | AI | 0.5d | - | 파일 확보 | FR-TAO-002 |
| T-M2-006 | PeopleNet → TensorRT FP16 엔진 변환 | AI | 1d | 005 | .engine 생성 | FR-TAO-003,FR-DS-008 |
| T-M2-007 | PGIE 설정 + 사람 감지 동작 확인 | AI | 1d | 006,004 | bbox 표시 | FR-DS-007 |

### Sprint 4 (W7~W8): 추적·행동 분석

| ID | 작업 | 담당 | 소요 | 의존성 | 완료 기준 | 관련 요구사항 |
|----|------|------|------|--------|-----------|--------------|
| T-M2-008 | nvtracker (NvDCF) 설정 + 적용 | AI | 1d | 007 | tracking_id | FR-DS-014 |
| T-M2-009 | Tracker 파라미터 튜닝 | AI | 1d | 008 | ID 연속성 | FR-DS-015 |
| T-M2-010 | ActionRecognitionNet 모델 준비 | AI | 1d | - | 모델 확보 | FR-DS-009 |
| T-M2-011 | ActionRecognition → TensorRT 변환 | AI | 1d | 010 | .engine 생성 | FR-TAO-003 |
| T-M2-012 | SGIE 설정 + 행동 분류 동작 | AI | 2d | 011,008 | fall/normal | FR-DS-009 |
| T-M2-013 | 8채널 동시 PGIE+Tracker+SGIE 성능 | AI | 1d | 012 | FPS ≥15/ch | NFR-001 |

### Sprint 5 (W9~W10): 분석·이벤트 발행

| ID | 작업 | 담당 | 소요 | 의존성 | 완료 기준 | 관련 요구사항 |
|----|------|------|------|--------|-----------|--------------|
| T-M2-014 | nvdsanalytics ROI polygon 설정 | AI | 1d | 013 | ROI 파일 | FR-DS-018,019 |
| T-M2-015 | ROI 침입 감지 동작 확인 | AI | 1d | 014 | 이벤트 발생 | FR-DS-018 |
| T-M2-016 | Dwell Time 미움직임 30초 감지 | AI | 0.5d | 014 | 시간 초과 | FR-DS-016 |
| T-M2-017 | nvmsgconv 이벤트 JSON 스키마 정의 | Dev | 1d | 013 | JSON 검증 | FR-DS-021 |
| T-M2-018 | nvmsgbroker Redis Stream 연결 | Dev | 1d | 017 | 수신 확인 | FR-DS-022 |
| T-M2-019 | 영상 클립 저장 (splitmuxsink ±30초) | Dev | 1d | 018 | 클립 생성 | FR-DS-023 |
| T-M2-020 | DeepStream Manager API (/health, /sources, /models) | Dev | 2d | 018 | API 응답 | NFR-018 |
| T-M2-021 | DeepStream 전체 파이프라인 통합 테스트 | AI | 1d | 020 | 8채널 E2E | FR-DS-001~023 |



## 5. M3: 센서 연동·이벤트 엔진 (W11~W14, 14개 작업)

### Sprint 6 (W11~W12): 센서 서비스 + 이벤트 처리

| ID | 작업 | 담당 | 소요 | 의존성 | 완료 기준 | 관련 요구사항 |
|----|------|------|------|--------|-----------|--------------|
| T-M3-001 | Device Gateway: MQTT 밴드 8개 수신 | Dev | 1d | M1 | 8밴드 수신 | FR-DEV-001,002,003 |
| T-M3-002 | Device Gateway: 환경센서 MQTT 수신 | Dev | 0.5d | 001 | 데이터 수신 | FR-DEV-007,008 |
| T-M3-003 | Device Gateway: 화재 GPIO 폴링 + 이벤트 | Dev | 1d | 001 | 접점 이벤트 | FR-DEV-011,012,013 |
| T-M3-004 | Device Gateway: 바이오 이상 판단 | Dev | 1d | 001 | 이상 이벤트 | FR-DEV-002 |
| T-M3-005 | Device Gateway: device_id↔worker_id 매핑 | Dev | 0.5d | 001 | 매핑 확인 | FR-DEV-004 |
| T-M3-006 | Event Engine: stream:ds-events + stream:sensors 수신 | Dev | 1d | M2-018 | 통합 수신 | FR-EVT-001 |
| T-M3-007 | Event Engine: 위험등급 YAML 규칙 엔진 | Dev | 2d | 006 | 규칙 동작 | FR-EVT-002,003,004 |
| T-M3-008 | Event Engine: 중복 억제 (10초 윈도우) | Dev | 1d | 007 | 중복 차단 | FR-EVT-005 |
| T-M3-009 | Event Engine: confidence 기반 등급 하향 | Dev | 0.5d | 007 | 필터 동작 | FR-EVT-007 |

### Sprint 7 (W13~W14): 이벤트 라우팅 + 통합

| ID | 작업 | 담당 | 소요 | 의존성 | 완료 기준 | 관련 요구사항 |
|----|------|------|------|--------|-----------|--------------|
| T-M3-010 | Event Engine: 라우팅 (alarms/dashboard/cloud) | Dev | 1d | 007 | 3스트림 | FR-EVT-002 |
| T-M3-011 | Local Storage: 이벤트 SQLite 저장 | Dev | 1d | 010 | 조회 가능 | NFR-006 |
| T-M3-012 | Rolling Buffer: 이벤트 트리거 클립 추출 | Dev | 1.5d | 010 | ±30초 클립 | FR-DS-023 |
| T-M3-013 | Event Engine: Acknowledge API | Dev | 0.5d | 011 | 상태 전이 | FR-EVT-010 |
| T-M3-014 | DeepStream + 센서 융합 시나리오 통합 테스트 | QA | 2d | 013 | 전 시나리오 | FR-EVT-001~007 |



## 6. M4: 알람·대시보드 (W15~W18, 18개 작업)

### Sprint 8 (W15~W16): 알람 + Backend API

| ID | 작업 | 담당 | 소요 | 의존성 | 완료 기준 | 관련 요구사항 |
|----|------|------|------|--------|-----------|--------------|
| T-M4-001 | Alarm Controller: stream:alarms 수신 + GPIO 제어 | Dev | 1d | M3-010 | 물리 동작 | FR-EVT-008,012 |
| T-M4-002 | CRITICAL/WARNING 차등 동작 | Dev | 0.5d | 001 | 차등 확인 | FR-EVT-008,009 |
| T-M4-003 | 알람 Acknowledge + GPIO OFF | Dev | 0.5d | 002 | 해제 동작 | FR-EVT-010 |
| T-M4-004 | 알람 동작/해제 이력 로깅 | Dev | 0.5d | 003 | 로그 확인 | FR-EVT-011 |
| T-M4-005 | Dashboard Backend: FastAPI 프로젝트 | Dev | 0.5d | - | 서버 시작 | FR-DSH-009 |
| T-M4-006 | 인증 API (login/refresh/me) + JWT | Dev | 1d | 005 | 토큰 발급 | FR-DSH-009,010 |
| T-M4-007 | 대시보드 API: /dashboard/summary,devices,workers | Dev | 1d | 006 | 응답 확인 | FR-DSH-001~004 |
| T-M4-008 | 이벤트 API: /events (목록/상세/acknowledge/필터) | Dev | 1d | 007 | CRUD 동작 | FR-DSH-005 |
| T-M4-009 | 시스템 API: /system/health, /system/metrics | Dev | 0.5d | 007 | 상태 조회 | FR-DSH-007 |
| T-M4-010 | WebSocket: 실시간 이벤트 푸시 | Dev | 1d | 007 | 실시간 수신 | FR-DSH-008 |

### Sprint 9 (W17~W18): Dashboard UI

| ID | 작업 | 담당 | 소요 | 의존성 | 완료 기준 | 관련 요구사항 |
|----|------|------|------|--------|-----------|--------------|
| T-M4-011 | Dashboard UI Next.js 프로젝트 구성 | FE | 0.5d | - | 빌드 성공 | FR-DSH-001 |
| T-M4-012 | 로그인 페이지 + JWT 연동 | FE | 1d | 011,006 | 인증 동작 | FR-DSH-009 |
| T-M4-013 | 메인: 8채널 영상 그리드 (RTSP→WebRTC/HLS) | FE | 2d | 012 | 8채널 표시 | FR-DSH-001 |
| T-M4-014 | 메인: 위험등급 요약 + 작업자 상태 + 센서 게이지 | FE | 2d | 013 | 실시간 갱신 | FR-DSH-002,003,004 |
| T-M4-015 | 이벤트 로그 페이지 (목록/필터/상세/Acknowledge) | FE | 2d | 014 | 전 기능 | FR-DSH-005 |
| T-M4-016 | 시스템 상태 페이지 (장비/GPU/DeepStream/네트워크) | FE | 1d | 015 | 상태 표시 | FR-DSH-007 |
| T-M4-017 | 실시간 알림 팝업 (WebSocket) | FE | 1d | 016 | 이벤트 팝업 | FR-DSH-008 |
| T-M4-018 | UI 반응형 + 접근성 점검 | FE | 1d | 017 | 검수 통과 | FR-DSH-001 |



## 7. M5: 클라우드·학습 기반 (W19~W21, 11개 작업)

### Sprint 10 (W19~W21): Cloud + TAO

| ID | 작업 | 담당 | 소요 | 의존성 | 완료 기준 | 관련 요구사항 |
|----|------|------|------|--------|-----------|--------------|
| T-M5-001 | AWS Sync Agent: IoT Core 연결 (X.509) | Dev | 1d | M1 | 연결 성공 | FR-CLD-001,NFR-014 |
| T-M5-002 | 이벤트 전송 (stream:cloud-queue → IoT MQTT) | Dev | 1d | 001 | 클라우드 수신 | FR-CLD-001 |
| T-M5-003 | 오프라인 큐잉 + 복구 시 자동 재전송 | Dev | 1d | 002 | 장애→복구 | FR-CLD-002,NFR-008 |
| T-M5-004 | 영상 클립 S3 업로드 | Dev | 0.5d | 002 | S3 확인 | FR-CLD-004 |
| T-M5-005 | 모델 레지스트리 (S3+DynamoDB) 구축 | Cloud | 1d | - | 업로드/조회 | FR-CLD-005 |
| T-M5-006 | TAO Toolkit Docker 환경 구축 (학습 서버) | AI | 1d | M1-007 | tao 명령 | FR-TAO-001 |
| T-M5-007 | NGC 모델 → TAO export → TensorRT 검증 | AI | 1d | 006 | 엔진 동작 | FR-TAO-003,004 |
| T-M5-008 | 기본 Fine-tuning 테스트 (소량 데이터) | AI | 1d | 007 | 학습 완료 | FR-TAO-007,008 |
| T-M5-009 | 모델 배포 경로: 학습서버 → Edge (SCP + reload) | Dev | 1d | 008 | 핫스왑 | FR-TAO-009 |
| T-M5-010 | 배포 후 검증 + 롤백 로직 | Dev | 1d | 009 | 롤백 동작 | FR-TAO-010 |
| T-M5-011 | 원격 대시보드 HTTPS + JWT 접속 확인 | Dev | 0.5d | M4 | 외부 접속 | FR-CLD-006 |

---

## 8. M6: 통합 검수 (W22~W24, 10개 작업)

### Sprint 11 (W22~W24): 검수·납품

| ID | 작업 | 담당 | 소요 | 의존성 | 완료 기준 | 관련 요구사항 |
|----|------|------|------|--------|-----------|--------------|
| T-M6-001 | E2E 시나리오 테스트 (낙상/화재/위험구역) | QA | 2d | M1~M5 | 합격 | FR-DS,FR-EVT |
| T-M6-002 | 센서 융합 시나리오 (화재+심박) | QA | 1d | 001 | 복합 동작 | FR-EVT-003,004 |
| T-M6-003 | 성능 테스트: 8채널 FPS, 추론 지연, GPU | QA | 1d | 001 | NFR 달성 | NFR-001~004 |
| T-M6-004 | 네트워크 장애 테스트 | QA | 1d | 001 | 독립 동작 | NFR-007,008 |
| T-M6-005 | 카메라 1대 장애 → 7채널 정상 | QA | 0.5d | 001 | 격리 동작 | NFR-010 |
| T-M6-006 | DeepStream watchdog 자동 재시작 | QA | 0.5d | 001 | 5초 이내 | NFR-009 |
| T-M6-007 | 72시간 연속 운영 테스트 | QA | 3d | 001~006 | 에러 없음 | NFR-006 |
| T-M6-008 | 모델 배포 검증 (TAO→Edge 핫스왑) | QA | 1d | M5-009 | 정상 교체 | FR-TAO-009 |
| T-M6-009 | 보안 검증 (TLS, JWT, Secret) | QA | 1d | - | 요건 충족 | NFR-014,015 |
| T-M6-010 | 최종 검수 보고서 + 운영 매뉴얼 + 납품 | PM | 2d | 001~009 | 검수 합격 | 전체 |

---

## 9. 역할 정의

| 약칭 | 역할 | 담당 범위 |
|------|------|-----------|
| AI | AI Engineer | DeepStream, 모델 학습·최적화, TensorRT |
| Dev | Backend Developer | 서비스 구현 (Event Engine, Cloud Sync, API) |
| FE | Frontend Developer | Dashboard UI (React/Next.js) |
| Infra | Infrastructure | 서버, 네트워크, Docker, CI/CD |
| HW | Hardware | 카메라, 센서, 밴드, 알람 장비 설치 |
| Cloud | Cloud Engineer | AWS 인프라, IoT Core, S3, RDS |
| QA | QA Engineer | 테스트, 검수, 성능 측정 |
| PM | Project Manager | 일정 관리, 보고서, 납품 |

---

## 10. Platform 2.0/3.0 확장 태스크 (이번 미구현)

### Platform 2.0 (향후)
- TAO 학습 파이프라인 자동화 (수집→학습→평가→배포)
- 오탐/미탐 피드백 루프 + 자동 재학습 트리거
- A/B 모델 배포 (카나리)
- L0~L3 적응형 저장 품질 제어
- 활동지수 프로파일링 (개인별 기준선)
- 운영 관리 기능 (작업자/장비/리포트/RBAC)

### Platform 3.0 (향후)
- Generative 재추론 (저장 클립 + 신규 모델)
- RAG 기반 자연어 이벤트 검색
- 해시체인 감사 로그 (위변조 방지)
- 다중 현장 SaaS (테넌트 격리, 온보딩 자동화)
- MLOps 자동화 (성능 하락 트리거 → 재학습 → 배포)
- 외부 연동 (소방서/병원 자동 신고)

---

## 변경 이력

| 버전 | 일자 | 내용 |
|------|------|------|
| 1.0 | 2025-05-19 | Platform 1.0 개발 태스크 초안 (92개 작업, 24주) |
