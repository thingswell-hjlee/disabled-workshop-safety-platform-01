# Platform 1.0 구현 작업 분해 (Tasks)

> **참조:** #[[file:.kiro/specs/platform-roadmap.md]] | #[[file:.kiro/specs/design.md]]
> **범위:** Platform 1.0 (24주, 6개 마일스톤)

---

## 1. 작업 ID 체계

| 접두사 | 마일스톤 | 예시 |
|--------|----------|------|
| `T-M1-xxx` | M1: 인프라 구축 | T-M1-001 |
| `T-M2-xxx` | M2: DeepStream 파이프라인 | T-M2-001 |
| `T-M3-xxx` | M3: 센서 연동·이벤트 | T-M3-001 |
| `T-M4-xxx` | M4: 알람·대시보드 | T-M4-001 |
| `T-M5-xxx` | M5: 클라우드·학습기반 | T-M5-001 |
| `T-M6-xxx` | M6: 통합 검수 | T-M6-001 |

---

## 2. M1: 인프라 구축 (W1~W4)

### Sprint 1 (W1~W2): 서버·네트워크 셋업

| ID | 작업 | 담당 | 소요 | 의존성 | 완료 기준 |
|----|------|------|------|--------|-----------|
| T-M1-001 | Edge AI 서버 하드웨어 설치 (GPU, RAM, SSD) | Infra | 1d | - | 하드웨어 정상 부팅 |
| T-M1-002 | Ubuntu 22.04 LTS 설치 + SSH 설정 | Infra | 0.5d | 001 | 원격 접속 가능 |
| T-M1-003 | NVIDIA GPU Driver 535+ 설치 | Infra | 0.5d | 002 | `nvidia-smi` 정상 |
| T-M1-004 | CUDA 12.x + cuDNN 8.x 설치 | Infra | 0.5d | 003 | CUDA 샘플 실행 |
| T-M1-005 | Docker 24.x + NVIDIA Container Toolkit 설치 | Infra | 0.5d | 004 | `docker run --gpus all` 동작 |
| T-M1-006 | DeepStream 7.x 컨테이너 pull + 실행 확인 | Infra | 0.5d | 005 | 샘플 앱 실행 |
| T-M1-007 | 학습 서버 동일 환경 구축 (RTX 4090) | Infra | 2d | - | nvidia-smi + TAO 실행 |
| T-M1-008 | 네트워크 VLAN 구성 (10/20/30/40) | Infra | 1d | 001 | 각 VLAN ping 확인 |
| T-M1-009 | 방화벽 규칙 설정 (iptables/nftables) | Infra | 0.5d | 008 | 규칙 검증 |

### Sprint 2 (W3~W4): 장비 설치·프로젝트 기반

| ID | 작업 | 담당 | 소요 | 의존성 | 완료 기준 |
|----|------|------|------|--------|-----------|
| T-M1-010 | IP Camera 8대 설치 + RTSP URL 확인 | HW | 2d | 008 | 전 채널 ffprobe |
| T-M1-011 | 스마트밴드 8개 페어링 + BLE Gateway 설정 | HW | 1d | 008 | MQTT 데이터 수신 |
| T-M1-012 | 환경센서 2개 설치 + MQTT 발행 확인 | HW | 0.5d | 008 | 데이터 수신 |
| T-M1-013 | 화재감지 접점 배선 + GPIO 신호 확인 | HW | 0.5d | 001 | 접점 테스트 |
| T-M1-014 | 접점연동 알람장치(사이렌/경광등) 설치 | HW | 0.5d | 001 | GPIO 제어 동작 |
| T-M1-015 | NVR 설치 + 8채널 녹화 설정 | HW | 0.5d | 010 | 녹화 시작 확인 |
| T-M1-016 | Git Repository 구조 확정 + CI/CD 기본 (GitHub Actions) | Dev | 1d | - | Docker build 자동 |
| T-M1-017 | .env.example, 설정 파일 템플릿, Secret 관리 체계 | Dev | 0.5d | 016 | 보안 검증 |
| T-M1-018 | Docker Compose 파일 (전 서비스 정의) | Dev | 1d | 005 | compose up 성공 |


---

## 3. M2: DeepStream 파이프라인 (W5~W10)

### Sprint 3 (W5~W6): 기본 파이프라인 구축

| ID | 작업 | 담당 | 소요 | 의존성 | 완료 기준 |
|----|------|------|------|--------|-----------|
| T-M2-001 | DeepStream 앱 프로젝트 구조 생성 (configs/, models/, roi/) | AI | 0.5d | M1 | 디렉토리 구조 확인 |
| T-M2-002 | 단일 RTSP 소스 디코딩 + 표시 (uridecodebin + nvdsosd) | AI | 1d | 001 | 1채널 영상 표시 |
| T-M2-003 | 8채널 RTSP 소스 등록 (source_list.yml 작성) | AI | 0.5d | 002 | 8채널 동시 |
| T-M2-004 | nvstreammux 설정 (batch-size=8, 해상도 정규화) | AI | 0.5d | 003 | 배치 처리 확인 |
| T-M2-005 | PeopleNet 사전학습 모델 다운로드 (NGC) | AI | 0.5d | - | 모델 파일 확보 |
| T-M2-006 | PeopleNet → TensorRT FP16 엔진 변환 (tao export / trtexec) | AI | 1d | 005 | .engine 생성 |
| T-M2-007 | PGIE 설정 (pgie_config.yml) + 사람 감지 동작 확인 | AI | 1d | 006, 004 | bbox 표시 |

### Sprint 4 (W7~W8): 추적·행동 분석

| ID | 작업 | 담당 | 소요 | 의존성 | 완료 기준 |
|----|------|------|------|--------|-----------|
| T-M2-008 | nvtracker (NvDCF) 설정 + 적용 | AI | 1d | 007 | tracking_id 부여 |
| T-M2-009 | Tracker 파라미터 튜닝 (max_targets, 궤적 유지 시간) | AI | 1d | 008 | ID 연속성 검증 |
| T-M2-010 | ActionRecognitionNet 모델 준비 (NGC 또는 커스텀) | AI | 1d | - | 모델 파일 확보 |
| T-M2-011 | ActionRecognition → TensorRT 엔진 변환 | AI | 1d | 010 | .engine 생성 |
| T-M2-012 | SGIE 설정 (sgie_action_config.yml) + 행동 분류 동작 | AI | 2d | 011, 008 | fall/normal 분류 |
| T-M2-013 | 8채널 동시 PGIE + Tracker + SGIE 성능 측정 | AI | 1d | 012 | FPS ≥ 15/ch |

### Sprint 5 (W9~W10): 분석·이벤트 발행

| ID | 작업 | 담당 | 소요 | 의존성 | 완료 기준 |
|----|------|------|------|--------|-----------|
| T-M2-014 | nvdsanalytics 설정: 카메라별 ROI polygon 정의 | AI | 1d | 013 | ROI 설정 파일 |
| T-M2-015 | ROI 침입 감지 동작 확인 | AI | 1d | 014 | 진입 시 이벤트 |
| T-M2-016 | Dwell Time (미움직임 30초) 감지 설정 | AI | 0.5d | 014 | 시간 초과 감지 |
| T-M2-017 | nvmsgconv: 이벤트 JSON 변환 스키마 정의 | Dev | 1d | 013 | JSON 출력 검증 |
| T-M2-018 | nvmsgbroker: Redis Stream 연결 + 이벤트 발행 | Dev | 1d | 017 | Redis 수신 확인 |
| T-M2-019 | 영상 클립 저장 (splitmuxsink, 이벤트 ±30초) | Dev | 1d | 018 | 클립 파일 생성 |
| T-M2-020 | DeepStream Manager API 구현 (/health, /sources, /models) | Dev | 2d | 018 | API 응답 확인 |
| T-M2-021 | DeepStream 전체 파이프라인 통합 테스트 | AI | 1d | 020 | 8채널 End-to-End |

---

## 4. M3: 센서 연동·이벤트 (W11~W14)

### Sprint 6 (W11~W12): 센서 서비스 + 이벤트 처리

| ID | 작업 | 담당 | 소요 | 의존성 | 완료 기준 |
|----|------|------|------|--------|-----------|
| T-M3-001 | Sensor Service: MQTT 클라이언트 (밴드 토픽 구독) | Dev | 1d | M1 | 8밴드 수신 |
| T-M3-002 | Sensor Service: 환경센서 MQTT 수신 + Redis 발행 | Dev | 0.5d | 001 | 데이터 수신 |
| T-M3-003 | Sensor Service: 화재감지 GPIO 폴링 + 이벤트 발행 | Dev | 1d | 001 | 접점 이벤트 |
| T-M3-004 | Sensor Service: 바이오 이상 판단 (심박/체온 임계치) | Dev | 1d | 001 | 이상 이벤트 |
| T-M3-005 | Event Processor: Redis stream:ds-events + stream:sensors 수신 | Dev | 1d | M2-018 | 통합 수신 |
| T-M3-006 | 위험등급 판정 규칙 엔진 구현 (YAML 로드) | Dev | 2d | 005 | 규칙 동작 |
| T-M3-007 | 이벤트 중복 억제 로직 (10초 윈도우) | Dev | 1d | 006 | 중복 차단 |
| T-M3-008 | confidence 기반 등급 하향 로직 | Dev | 0.5d | 006 | 필터 동작 |

### Sprint 7 (W13~W14): 이벤트 라우팅 + 통합 검증

| ID | 작업 | 담당 | 소요 | 의존성 | 완료 기준 |
|----|------|------|------|--------|-----------|
| T-M3-009 | 이벤트 라우팅: stream:alarms, stream:dashboard, stream:cloud | Dev | 1d | 006 | 3개 스트림 발행 |
| T-M3-010 | 이벤트 저장 (로컬 SQLite + JSON 파일) | Dev | 1d | 009 | 조회 가능 |
| T-M3-011 | 이벤트 Acknowledge API | Dev | 0.5d | 010 | 상태 전이 확인 |
| T-M3-012 | DeepStream + 센서 융합 시나리오 통합 테스트 | QA | 2d | 011 | 전 시나리오 통과 |

---

## 5. M4: 알람·대시보드 (W15~W18)

### Sprint 8 (W15~W16): 알람 + Backend API

| ID | 작업 | 담당 | 소요 | 의존성 | 완료 기준 |
|----|------|------|------|--------|-----------|
| T-M4-001 | Alarm Controller: stream:alarms 수신 + GPIO 제어 | Dev | 1d | M3-009 | 물리 동작 |
| T-M4-002 | CRITICAL(사이렌+경광등) / WARNING(경광등) 차등 동작 | Dev | 0.5d | 001 | 차등 확인 |
| T-M4-003 | 알람 해제(Acknowledge) 로직 + GPIO OFF | Dev | 0.5d | 002 | 해제 동작 |
| T-M4-004 | 알람 동작/해제 이력 로깅 | Dev | 0.5d | 003 | 로그 확인 |
| T-M4-005 | Dashboard Backend: FastAPI 프로젝트 구성 | Dev | 0.5d | - | 서버 시작 |
| T-M4-006 | 인증 API (login, refresh, me) + JWT | Dev | 1d | 005 | 토큰 발급 |
| T-M4-007 | 대시보드 API: /dashboard/summary, /devices, /workers | Dev | 1d | 006 | 응답 확인 |
| T-M4-008 | 이벤트 API: /events (목록, 상세, acknowledge, 필터) | Dev | 1d | 007 | CRUD 동작 |
| T-M4-009 | 시스템 API: /system/health, /system/metrics | Dev | 0.5d | 007 | 상태 조회 |
| T-M4-010 | WebSocket: 실시간 이벤트 푸시 (stream:dashboard 구독) | Dev | 1d | 007 | 실시간 수신 |

### Sprint 9 (W17~W18): Dashboard UI

| ID | 작업 | 담당 | 소요 | 의존성 | 완료 기준 |
|----|------|------|------|--------|-----------|
| T-M4-011 | Dashboard UI 프로젝트 구성 (Next.js) | FE | 0.5d | - | 빌드 성공 |
| T-M4-012 | 로그인 페이지 + JWT 연동 | FE | 1d | 011, M4-006 | 인증 동작 |
| T-M4-013 | 메인: 8채널 영상 그리드 (RTSP→HLS/WebRTC) | FE | 2d | 012 | 8채널 표시 |
| T-M4-014 | 메인: 위험등급 요약 + 작업자 상태 + 센서 게이지 | FE | 2d | 013 | 실시간 갱신 |
| T-M4-015 | 이벤트 로그 페이지 (목록, 필터, 상세, Acknowledge) | FE | 2d | 014 | 전 기능 동작 |
| T-M4-016 | 시스템 상태 페이지 (장비, GPU, DeepStream, 네트워크) | FE | 1d | 015 | 상태 표시 |
| T-M4-017 | 실시간 알림 팝업 (WebSocket 연동) | FE | 1d | 016 | 이벤트 팝업 |
| T-M4-018 | UI 반응형 + 접근성 검수 | FE | 1d | 017 | 검수 통과 |

---

## 6. M5: 클라우드·학습기반 (W19~W21)

### Sprint 10 (W19~W21): Cloud + TAO 기반

| ID | 작업 | 담당 | 소요 | 의존성 | 완료 기준 |
|----|------|------|------|--------|-----------|
| T-M5-001 | Cloud Sync: AWS IoT Core 연결 (X.509 인증서) | Dev | 1d | M1 | 연결 성공 |
| T-M5-002 | 이벤트 전송 (stream:cloud-queue → IoT Core MQTT) | Dev | 1d | 001 | 클라우드 수신 |
| T-M5-003 | 오프라인 큐잉 + 복구 시 자동 재전송 | Dev | 1d | 002 | 장애→복구 동작 |
| T-M5-004 | 영상 클립 S3 업로드 | Dev | 0.5d | 002 | S3 확인 |
| T-M5-005 | 모델 레지스트리 (S3 + DynamoDB) 구축 | Cloud | 1d | - | 업로드/조회 |
| T-M5-006 | TAO Toolkit Docker 환경 구축 (학습 서버) | AI | 1d | M1-007 | tao 명령 실행 |
| T-M5-007 | PeopleNet NGC 모델 → TAO export → TensorRT 변환 검증 | AI | 1d | 006 | 엔진 동작 |
| T-M5-008 | 기본 Fine-tuning 테스트 (소량 데이터) | AI | 1d | 007 | 학습 완료 |
| T-M5-009 | 모델 배포 경로: 학습서버 → Edge (SCP + API reload) | Dev | 1d | 008 | 핫스왑 동작 |
| T-M5-010 | 배포 후 검증 + 실패 시 롤백 로직 | Dev | 1d | 009 | 롤백 동작 |
| T-M5-011 | TAO Manager API 기본 구현 (/pipeline, /deploy) | Dev | 1d | 010 | API 응답 |


---

## 7. M6: 통합 검수 (W22~W24)

### Sprint 11 (W22~W24): 검수·납품

| ID | 작업 | 담당 | 소요 | 의존성 | 완료 기준 |
|----|------|------|------|--------|-----------|
| T-M6-001 | End-to-End 시나리오 테스트 (낙상/쓰러짐/위험구역) | QA | 2d | M1~M5 | 전 시나리오 합격 |
| T-M6-002 | 센서 융합 시나리오 (화재접점 + 심박이상) | QA | 1d | 001 | 복합 이벤트 동작 |
| T-M6-003 | 성능 테스트: 8채널 FPS, 추론 지연, GPU 사용률 | QA | 1d | 001 | NFR 달성 |
| T-M6-004 | 네트워크 장애 테스트: 인터넷 차단 → 로컬 동작 → 복구 동기화 | QA | 1d | 001 | 독립 동작 + 동기화 |
| T-M6-005 | 카메라 1대 장애 → 나머지 7채널 정상 동작 | QA | 0.5d | 001 | 부분 장애 격리 |
| T-M6-006 | GPU 장애 시 graceful degradation 확인 | QA | 0.5d | 001 | 센서 판단 유지 |
| T-M6-007 | 72시간 연속 운영 테스트 | QA | 3d | 001~006 | 에러/누수 없음 |
| T-M6-008 | 모델 배포 검증: 학습서버 → Edge DeepStream 모델 교체 | QA | 1d | M5-009 | 핫스왑 성공 |
| T-M6-009 | 보안 검증: TLS, JWT, Secret 관리, 접근 로그 | QA | 1d | - | 보안 요건 충족 |
| T-M6-010 | 최종 검수 보고서 작성 | PM | 2d | 001~009 | 보고서 제출 |
| T-M6-011 | 운영 매뉴얼 + 장애 대응 매뉴얼 작성 | Dev | 2d | 010 | 문서 완료 |
| T-M6-012 | 납품 (코드 + 문서 + 설정 + 모델) | PM | 1d | 011 | 인수인계 |

---

## 8. 작업 통계

| 마일스톤 | 작업 수 | 기간 | 핵심 산출물 |
|----------|---------|------|-------------|
| M1: 인프라 | 18 | 4주 | GPU 서버, 네트워크, 장비 설치 |
| M2: DeepStream | 21 | 6주 | 8채널 파이프라인 + 모델 추론 |
| M3: 센서·이벤트 | 12 | 4주 | 센서 융합 + 이벤트 처리 |
| M4: 알람·대시보드 | 18 | 4주 | 알람 제어 + Dashboard MVP |
| M5: 클라우드·학습 | 11 | 3주 | AWS 연동 + TAO 기본 환경 |
| M6: 통합 검수 | 12 | 3주 | 검수 합격 + 납품 |
| **합계** | **92** | **24주** | Platform 1.0 완성 |

---

## 9. 의존성 그래프 (Critical Path)

```
M1 (인프라)
 │
 ├──→ M2 (DeepStream) ──────────────────┐
 │         │                             │
 │         └──→ M3 (센서·이벤트) ──→ M4 (알람·대시보드) ──→ M6 (검수)
 │                     │                                      ▲
 └──→ M5 (클라우드·학습기반) ─────────────────────────────────┘
```

**Critical Path:** M1 → M2 → M3 → M4 → M6 (20주)
**병렬 가능:** M5는 M2 완료 후 병렬 진행 가능

---

## 10. 역할 정의

| 역할 | 약칭 | 담당 범위 |
|------|------|-----------|
| AI Engineer | AI | DeepStream 파이프라인, 모델 학습·최적화 |
| Backend Developer | Dev | 서비스 구현 (Event Processor, Cloud Sync, API) |
| Frontend Developer | FE | Dashboard UI (React/Next.js) |
| Infrastructure | Infra | 서버, 네트워크, Docker, CI/CD |
| Hardware | HW | 카메라, 센서, 밴드, 알람 장비 설치 |
| Cloud Engineer | Cloud | AWS 인프라, IoT Core, S3, RDS |
| QA | QA | 테스트, 검수, 성능 측정 |
| Project Manager | PM | 일정 관리, 검수 보고서, 납품 |

---

## 변경 이력

| 버전 | 일자 | 내용 |
|------|------|------|
| 0.1 | 2025-05-19 | Platform 1.0 구현 작업 분해 초안 (92개 작업, 24주) |
