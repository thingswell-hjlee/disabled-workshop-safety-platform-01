# AI기반 장애인직업재활시설 스마트안전시스템 구축

## 1. 프로젝트 개요

### 1.1 프로젝트 목적

장애인직업재활시설의 작업 현장에서 발생할 수 있는 안전사고를 **NVIDIA DeepStream SDK + TAO Toolkit + TensorRT** 기반 AI로 실시간 감지·판단·알림하여, 작업자의 생명과 안전을 보호하는 스마트안전시스템을 구축한다.

### 1.2 핵심 AI 개발 기술

| 기술 | 역할 | 적용 시점 |
|------|------|-----------|
| **NVIDIA DeepStream SDK** | IP Camera 8대 RTSP 수집, 실시간 영상 분석, AI 모델 추론, 이벤트 메타데이터 생성, TensorRT 모델 실행, 현장 Edge AI 서버 실시간 판별 | Platform 1.0~ |
| **NVIDIA TAO Toolkit** | 현장 영상 데이터 기반 전이학습, 낙상/쓰러짐/장시간 미움직임/위험구역 접근/위험행동 감지 모델 학습, 오탐·미탐 데이터 기반 재학습, 모델 성능 검증, DeepStream 배포용 모델 최적화, 현장 특화 AI 모델 고도화 | Platform 1.0(기본)~2.0(본격) |
| **NVIDIA TensorRT** | TAO로 학습된 모델을 Edge AI 서버에서 빠르게 실행하기 위한 추론 최적화 (FP16/INT8) | Platform 1.0~ |

### 1.3 핵심 설계 원칙

| 원칙 | 설명 |
|------|------|
| **Platform 3.0 목표 설계** | 초기 시스템 설정과 아키텍처는 Platform 3.0을 목표로 설계 |
| **Platform 1.0 우선 구현** | 1차 구현은 DeepStream 기반 실시간 영상 수집·추론·이벤트 구조 우선 |
| **현장 독립 동작** | 네트워크 장애 시에도 DeepStream 파이프라인 + 알람 로컬 독립 동작 보장 |
| **NVIDIA 생태계 일관** | DeepStream → TAO → TensorRT 일관된 NVIDIA 워크플로우 적용 |
| **확장 가능 ID 체계** | 현장/장비/작업자/이벤트/모델버전/위험등급 구조를 초기부터 설계 |
| **Patent-Aligned** | 등록 청구항의 기술 요소를 Context Intelligence Layer로 구조화 |


### 1.4 플랫폼 버전 정의

| 버전 | 목표 | 핵심 기술 | 범위 |
|------|------|-----------|------|
| **Platform 1.0** | DeepStream 기반 실시간 감지→판단→알람 End-to-End | DeepStream SDK + TensorRT | 핵심 안전 기능 통합 동작 |
| **Platform 2.0** | TAO Toolkit 기반 현장 맞춤 AI 모델 학습·검증·최적화 본격 구현 | TAO Toolkit + DeepStream | 운영 기능 + AI 개선 |
| **Platform 3.0** | TAO+DeepStream 다중 현장 모델 운영, 자동 재학습, 원격 배포, SaaS화 | TAO + DeepStream + MLOps | 고도화·SaaS 전환 |

---

## 2. Patent-Aligned Context Intelligence Layer

등록 청구항의 기술 요소를 다음과 같이 구조화하여 시스템에 반영한다.

### 2.1 Context Intelligence Layer 구조

```
┌─────────────────────────────────────────────────────────────────────────┐
│              Patent-Aligned Context Intelligence Layer                    │
│                                                                         │
│  ┌─────────────────┐  ┌──────────────────┐  ┌───────────────────────┐ │
│  │ Perception Layer │  │ Cognition Layer  │  │ Action Layer          │ │
│  │ (인지 계층)       │  │ (판단 계층)      │  │ (대응 계층)            │ │
│  │                   │  │                  │  │                       │ │
│  │ • DeepStream      │  │ • Risk Classifier│  │ • Alarm Controller   │ │
│  │   RTSP 8ch 수집   │  │   위험등급 판정  │  │   접점 경보 제어      │ │
│  │ • nvinfer PGIE    │  │ • Event Fusion   │  │ • Dashboard Alert    │ │
│  │   사람 감지       │  │   영상+센서 융합  │  │   관리자 실시간 알림  │ │
│  │ • nvinfer SGIE    │  │ • Pattern Engine │  │ • Cloud Sync         │ │
│  │   행동 분류       │  │   이상 패턴 판단  │  │   원격 이벤트 전송   │ │
│  │ • nvtracker       │  │ • Dedup Engine   │  │ • NVR Clip           │ │
│  │   객체 추적       │  │   중복 이벤트 억제│  │   증거 영상 저장     │ │
│  │ • nvdsanalytics   │  │                  │  │                       │ │
│  │   ROI/궤적 분석   │  │                  │  │                       │ │
│  │ • Sensor Fusion   │  │                  │  │                       │ │
│  │   밴드/환경/화재  │  │                  │  │                       │ │
│  └─────────────────┘  └──────────────────┘  └───────────────────────┘ │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    Evolution Layer (진화 계층)                     │   │
│  │                                                                   │   │
│  │  • TAO Toolkit 현장 데이터 전이학습                                │   │
│  │  • 오탐/미탐 피드백 → 재학습 트리거                                │   │
│  │  • TensorRT 최적화 → DeepStream Hot-swap 배포                     │   │
│  │  • 모델 버전 관리 + 성능 추적 + 자동 롤백                          │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    Resilience Layer (자율 계층)                    │   │
│  │                                                                   │   │
│  │  • 네트워크 장애 시 로컬 독립 동작 (DeepStream + 알람)             │   │
│  │  • 이벤트 로컬 큐잉 → 복구 시 자동 동기화                          │   │
│  │  • 프로세스 자동 재시작 (Watchdog)                                  │   │
│  │  • 단일 장비 장애 격리 (나머지 정상 운영)                           │   │
│  │  • GPU 장애 시 센서 기반 판단 유지                                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```


### 2.2 청구항 기술 요소 ↔ 시스템 매핑

| 청구항 기술 요소 | 시스템 구현 | NVIDIA 기술 | Platform |
|-----------------|------------|-------------|----------|
| 영상 기반 실시간 위험 감지 | DeepStream 8채널 RTSP + nvinfer 추론 | DeepStream SDK + TensorRT | 1.0 |
| 다중 센서 융합 판단 | Event Processor: 영상 + 밴드 + 환경 통합 | Redis Streams | 1.0 |
| 위험등급 자동 분류 | Risk Classifier (YAML 규칙 엔진) | - | 1.0 |
| 현장 즉시 경보 발동 | Alarm Controller GPIO 직접 제어 | - | 1.0 |
| 현장 독립 동작 보장 | 네트워크 장애 시 DeepStream 로컬 동작 | DeepStream Offline | 1.0 |
| 현장 데이터 기반 모델 진화 | TAO Toolkit Fine-tuning + 재학습 | TAO Toolkit | 1.0(기본)~2.0 |
| 모델 무중단 배포 | TensorRT 엔진 Hot-swap (nvinfer reload) | TensorRT + DeepStream | 1.0 |
| 원격 모니터링·관제 | 관리자 대시보드 + AWS 클라우드 | FastAPI + WebSocket | 1.0 |
| 다중 현장 확장 | site_id 기반 멀티 테넌트 설계 | - | 3.0 |
| 자동 재학습·배포 | MLOps 파이프라인 (성능 하락 트리거) | TAO + TensorRT | 3.0 |

---

## 3. 시스템 구성

### 3.1 하드웨어 구성

| 장비 | 수량 | 역할 |
|------|------|------|
| IP Camera | 8개 | 작업 현장 영상 수집 (RTSP H.264/H.265) |
| 스마트밴드 | 8개 | 작업자 심박·체온·가속도·위치 수집 |
| 환경센서 | 2개 | 온도, 습도, CO, VOC 수집 |
| 화재감지 접점 | 1식 | 화재 접점 신호(Dry Contact) 전달 |
| 접점연동 알람장치 | 1식 | 사이렌 + 경광등 현장 경보 |
| 8채널 NVR 2TB | 1대 | 영상 녹화 + 이벤트 클립 저장 |

### 3.2 서버 구성

| 서버 | 핵심 기술 | 역할 |
|------|-----------|------|
| **판별형 Edge AI 서버** | DeepStream SDK + TensorRT | RTSP 8채널 수집, 실시간 AI 추론 (낙상/쓰러짐/미움직임 감지), 위험 이벤트 생성, 현장 알람 제어, AWS 이벤트 전송 |
| **로컬 AI 엣지 학습·최적화 서버** | TAO Toolkit + TensorRT | 현장 데이터 수집, 영상·센서·밴드 데이터 정제, 라벨링, TAO 기반 모델 학습, 모델 검증, TensorRT 최적화, DeepStream 배포용 모델 패키징 |
| **AWS 클라우드** | IoT Core + S3 + RDS | 모델 버전 관리, 모델 배포 관리, 이벤트 로그 저장, 다중 현장 확장, 운영 리포트, 원격 유지보수 |

### 3.3 소프트웨어 구성

| 구성요소 | 기술 | 역할 |
|----------|------|------|
| **DeepStream 파이프라인** | nvstreammux → nvinfer → nvtracker → nvdsanalytics → nvmsgconv | 8채널 영상 수집·디코딩·추론·추적·분석·이벤트 생성 |
| **TAO 학습 환경** | TAO Toolkit Docker Container | 전이학습, Fine-tuning, Prune, Export, Calibrate |
| **TensorRT 최적화** | trtexec / TAO export | FP16/INT8 추론 엔진 생성 (.engine) |
| **이벤트 프로세서** | Python + Redis Streams | DeepStream 이벤트 + 센서 이벤트 통합 수신, 위험등급 판정, 라우팅 |
| **알람 컨트롤러** | Python + GPIO | 접점연동 사이렌/경광등 직접 제어 |
| **센서 서비스** | Python + MQTT | 스마트밴드/환경센서/화재감지 데이터 수신·판단 |
| **관리자 대시보드** | React/Next.js + FastAPI + WebSocket | 실시간 모니터링, 이벤트 이력, 시스템 관리 |
| **클라우드 동기화** | MQTT over TLS + boto3 | 이벤트·모델 AWS 전송, 오프라인 큐잉 |


---

## 4. DeepStream 파이프라인 구조 (Edge AI 서버)

```
[IP Camera x8 RTSP]
    → [nvv4l2decoder: GPU HW Decode (H.264/H.265)]
    → [nvstreammux: Batch=8, 1080p→추론 해상도 정규화]
    → [nvinfer PGIE: PeopleNet/YOLOv8 (TensorRT FP16) - 사람 감지]
    → [nvtracker: NvDCF - 작업자 추적 ID, 궤적 분석]
    → [nvinfer SGIE: ActionRecognitionNet (TensorRT FP16) - 낙상/쓰러짐/미움직임]
    → [nvdsanalytics: ROI 위험구역 침입, Dwell Time 감지]
    → [nvmsgconv: 이벤트 JSON 메타데이터 생성]
    → [nvmsgbroker: Redis Stream 발행 (stream:ds-events)]
    → [nvdsosd: 바운딩 박스·라벨 시각화 → NVR/Display]
    → [splitmuxsink: 이벤트 전후 ±30초 영상 클립 저장]
```

## 5. TAO Toolkit 워크플로우 (학습·최적화 서버)

```
[현장 영상 데이터 수집] → [데이터 정제·라벨링 (KITTI/COCO 형식)]
    → [TAO Train: 사전학습 모델(PeopleNet/ActionRecognitionNet) Fine-tuning]
    → [TAO Evaluate: mAP, Precision, Recall, F1 자동 산출]
    → [TAO Prune: 불필요 파라미터 제거 (모델 경량화)]
    → [TAO Export: ONNX/TensorRT 엔진 내보내기]
    → [TensorRT Calibrate: INT8 캘리브레이션 (Platform 2.0)]
    → [DeepStream 배포 패키징: .engine + labels.txt + config.yml]
    → [Edge AI 서버 Hot-swap 배포 (nvinfer model reload)]
    → [배포 후 검증 → 실패 시 자동 롤백]
```

---

## 6. 시스템 아키텍처

### 6.1 전체 데이터 흐름

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          현장 (On-Premise)                                 │
│                                                                          │
│  [IP Camera x8] ──RTSP──→ ┌──────────────────────────────────┐          │
│                            │   판별형 Edge AI 서버              │          │
│  [스마트밴드x8] ──MQTT──→  │                                   │          │
│  [환경센서 x2]  ──MQTT──→  │  [DeepStream Pipeline]           │          │
│  [화재감지 접점] ──GPIO──→  │  [Sensor Service]                │──→[알람]  │
│                            │  [Event Processor]               │          │
│                            │  [Cloud Sync] [Dashboard API]    │          │
│                            └──────────┬───────────────────────┘          │
│                                       │                                   │
│  [로컬 AI 엣지 학습·최적화 서버]        │                                   │
│  [TAO Toolkit] [라벨링] [TensorRT] ←──┘                                   │
│                                                                          │
│  [8채널 NVR 2TB] ← 이벤트 클립 저장                                        │
└──────────────────────────────────┼───────────────────────────────────────┘
                                   │ (인터넷)
                                   ▼
┌──────────────────────────────────────────────────────────────────────────┐
│  AWS 클라우드: [IoT Core] [S3] [RDS] [대시보드] [모델 레지스트리]           │
└──────────────────────────────────────────────────────────────────────────┘
```

### 6.2 네트워크 장애 대응

| 상태 | 동작 방식 |
|------|-----------|
| **정상** | DeepStream 이벤트 → Cloud 실시간 전송 |
| **장애** | DeepStream 로컬 독립 동작 + 알람 정상 + 이벤트 Redis 큐잉 |
| **복구** | 큐잉된 이벤트 5분 이내 일괄 동기화 |

---

## 7. 확장 가능한 ID 체계

| ID 유형 | 형식 | 설명 |
|---------|------|------|
| site_id | `SITE-001` | 다중 현장 확장 대비 |
| device_id | `CAM-001`, `BAND-003` | 장비 유형 + 일련번호 |
| worker_id | `WKR-0001` | 작업자 고유 식별 |
| event_id | `EVT-{YYYYMMDDHHmmss}-{SEQ}` | 시간 기반 유일성 |
| model_version | `v1.0.0-tao-ds` | 시맨틱 + 학습도구 + 배포대상 |
| risk_level | `CRITICAL` / `WARNING` / `NORMAL` | 3단계 위험 분류 |
| maint_id | `MAINT-{date}-{SEQ}` | 유지보수 이력 추적 |

---

## 8. Platform 1.0 검수 기준 요약

| 검수 항목 | 합격 기준 |
|-----------|-----------|
| DeepStream 8채널 수집·추론 | 8대 동시 RTSP, 15fps, GPU 디코딩 |
| AI 위험 감지 | 낙상·쓰러짐·위험구역 감지율 ≥ 80% |
| 추론 지연 | 프레임→이벤트 ≤ 200ms |
| 접점 알람 | CRITICAL 5초 이내 사이렌+경광등 동작 |
| 네트워크 독립 | 인터넷 차단 시 감지+판단+알람 정상 |
| 72시간 연속 운영 | 메모리 누수/크래시 없음 |
| 모델 배포 | TAO→TensorRT→DeepStream 핫스왑 정상 |

---

## 9. 기술 스택

| 레이어 | 기술 |
|--------|------|
| 영상 수집·추론 | NVIDIA DeepStream SDK 7.x |
| AI 모델 학습 | NVIDIA TAO Toolkit 5.x |
| 추론 최적화 | NVIDIA TensorRT 8.x+ (FP16/INT8) |
| GPU 컴퓨팅 | CUDA 12.x + cuDNN 8.x |
| Edge 서버 OS | Ubuntu 22.04 LTS + NVIDIA GPU Driver 535+ |
| 컨테이너 | Docker 24.x + NVIDIA Container Toolkit |
| 메시지 브로커 | Redis 7 (Streams) + Mosquitto (MQTT) |
| 대시보드 Backend | FastAPI (Python 3.11) |
| 대시보드 Frontend | React / Next.js |
| 클라우드 | AWS IoT Core, S3, RDS (PostgreSQL), ECS |

---

## 10. 향후 문서

| 문서 | 내용 |
|------|------|
| `requirements.md` | 103개 요구사항 (P0: 74, P1: 23, P2: 6) |
| `design.md` | DeepStream 파이프라인·TAO 워크플로우 상세 설계 |
| `software-architecture.md` | 6계층 NVIDIA 기반 아키텍처 |
| `platform-roadmap.md` | Platform 1.0/2.0/3.0 상세 로드맵 |
| `tasks.md` | 92개 작업, 24주, 6마일스톤 |
| `test-plan.md` | 5레벨 테스트, 76개 TC, 72시간 검증 |

---

## 변경 이력

| 버전 | 일자 | 내용 |
|------|------|------|
| 0.1 | 2025-05-19 | 초안 작성 |
| 1.0 | 2025-05-19 | NVIDIA DeepStream/TAO/TensorRT 전면 반영, Patent-Aligned Context Intelligence Layer 구조화 |
