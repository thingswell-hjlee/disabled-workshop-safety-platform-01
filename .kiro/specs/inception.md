# AI기반 장애인직업재활시설 스마트안전시스템 구축

## 1. 프로젝트 개요

### 1.1 프로젝트 목적

장애인직업재활시설의 작업 현장에서 발생할 수 있는 안전사고를 **NVIDIA DeepStream SDK + TAO Toolkit** 기반 AI로 실시간 감지·판단·알림하여, 작업자의 생명과 안전을 보호하는 스마트안전시스템을 구축한다.

### 1.2 핵심 AI 기술

| 기술 | 역할 | 적용 플랫폼 |
|------|------|-------------|
| **NVIDIA DeepStream SDK** | RTSP 8채널 수집, 실시간 영상 분석, AI 추론, 이벤트 메타데이터 생성 | Platform 1.0~ |
| **NVIDIA TAO Toolkit** | 전이학습, 현장 맞춤 모델 학습, 오탐/미탐 재학습, 모델 최적화 | Platform 1.0(기본)~2.0(본격) |
| **NVIDIA TensorRT** | TAO 학습 모델의 Edge 추론 최적화 (FP16/INT8) | Platform 1.0~ |

### 1.3 핵심 설계 원칙

| 원칙 | 설명 |
|------|------|
| **Platform 3.0 목표 설계** | 초기 아키텍처는 다중 현장 SaaS 확장을 고려하여 설계 |
| **Platform 1.0 우선 구현** | DeepStream 기반 실시간 영상 수집·추론·이벤트 구조 우선 구현 |
| **현장 독립 동작** | 네트워크 장애 시에도 DeepStream 파이프라인 로컬 독립 동작 보장 |
| **NVIDIA 생태계 활용** | DeepStream → TAO → TensorRT 일관된 NVIDIA 워크플로우 적용 |
| **확장 가능한 ID 체계** | 현장/장비/작업자/이벤트/모델버전/위험등급 구조를 초기부터 설계 |

### 1.4 플랫폼 버전 정의

| 버전 | 목표 | 핵심 기술 |
|------|------|-----------|
| **Platform 1.0** | DeepStream 기반 실시간 감지→판단→알람 End-to-End | DeepStream SDK + TensorRT |
| **Platform 2.0** | TAO Toolkit 기반 현장 맞춤 AI 모델 학습·검증·최적화 본격 구현 | TAO Toolkit + DeepStream |
| **Platform 3.0** | TAO+DeepStream 기반 다중 현장 모델 운영, 자동 재학습, SaaS | TAO + DeepStream + 자동화 |


---

## 2. 시스템 구성

### 2.1 하드웨어 구성

| 장비 | 수량 | 역할 |
|------|------|------|
| IP Camera | 8개 | 작업 현장 영상 수집 (RTSP) |
| 스마트밴드 | 8개 | 작업자 생체·위치 데이터 수집 |
| 환경센서 | 2개 | 온도, 습도, 가스 등 환경 데이터 수집 |
| 화재감지 접점 | 1식 | 화재 발생 감지 및 접점 신호 전달 |
| 접점연동 알람장치 | 1식 | 위험 상황 발생 시 현장 경보(사이렌, 경광등) |
| 8채널 NVR 2TB | 1대 | 영상 녹화 및 저장 |

### 2.2 서버 구성

| 서버 | 핵심 기술 | 역할 |
|------|-----------|------|
| **판별형 Edge AI 서버** | DeepStream SDK + TensorRT | RTSP 8채널 수집, 실시간 AI 추론, 이벤트 생성, 현장 알람 제어, AWS 전송 |
| **로컬 AI 엣지 학습·최적화 서버** | TAO Toolkit + TensorRT | 현장 데이터 수집·정제·라벨링, TAO 모델 학습, TensorRT 최적화, DeepStream 배포 패키징 |
| **AWS 클라우드** | S3 + RDS + IoT Core | 모델 버전 관리, 모델 배포, 이벤트 로그 저장, 다중 현장 확장, 원격 유지보수 |

### 2.3 소프트웨어 구성

| 구성요소 | 기술 | 역할 |
|----------|------|------|
| **DeepStream 파이프라인** | GStreamer + nvinfer + nvtracker | 8채널 영상 수집·디코딩·추론·추적·이벤트 생성 |
| **TAO 학습 환경** | TAO Toolkit (Docker) | 전이학습, 모델 미세조정, 성능 검증, 내보내기 |
| **TensorRT 최적화** | trtexec / TAO export | FP16/INT8 추론 엔진 생성 |
| **이벤트 프로세서** | Python + Redis | 이벤트 수신, 위험등급 판정, 알람 라우팅 |
| **관리자 대시보드** | React + FastAPI | 실시간 모니터링, 이벤트 이력, 시스템 관리 |
| **클라우드 동기화** | MQTT over TLS + boto3 | 이벤트·모델 클라우드 전송 |


---

## 3. NVIDIA 기술 상세 적용

### 3.1 NVIDIA DeepStream SDK (판별형 Edge AI 서버)

| 기능 | DeepStream 구성요소 | 설명 |
|------|---------------------|------|
| RTSP 8채널 수집 | `uridecodebin` + `nvstreammux` | 8대 IP Camera 동시 스트림 수집·멀티플렉싱 |
| GPU 디코딩 | `nvv4l2decoder` | 하드웨어 가속 H.264/H.265 디코딩 |
| AI 추론 | `nvinfer` (Primary) | TensorRT 엔진 기반 객체 감지 (YOLOv8/PeopleNet) |
| 2차 추론 | `nvinfer` (Secondary) | 행동 분석 (낙상/쓰러짐/미움직임) |
| 객체 추적 | `nvtracker` (NvDCF/DeepSORT) | 작업자 ID 추적, 궤적 분석 |
| 위험구역 | `nvdsanalytics` | ROI 기반 위험구역 침입 감지 |
| 메타데이터 | `nvmsgconv` + `nvmsgbroker` | 이벤트 JSON 생성 → Kafka/MQTT 발행 |
| OSD 표시 | `nvdsosd` | 바운딩 박스, 라벨, 궤적 시각화 |
| 녹화 | `nvv4l2h264enc` + `splitmuxsink` | 이벤트 기반 영상 클립 저장 |

**DeepStream 파이프라인 구조:**
```
[RTSP Source x8]
    → [nvstreammux (batch=8)]
    → [nvinfer: PeopleNet/YOLOv8 (TensorRT FP16)]
    → [nvtracker: NvDCF]
    → [nvinfer: Action Recognition (Secondary)]
    → [nvdsanalytics: ROI/Line Crossing]
    → [nvmsgconv → nvmsgbroker (Redis/MQTT)]
    → [nvdsosd → NVR/Display]
```

### 3.2 NVIDIA TAO Toolkit (학습·최적화 서버)

| 기능 | TAO 구성요소 | 설명 |
|------|-------------|------|
| 전이학습 | `tao model train` | NVIDIA 사전학습 모델 기반 현장 Fine-tuning |
| 감지 모델 | PeopleNet / DetectNet_v2 | 사람 감지, 자세 추정 |
| 행동 분석 | ActionRecognitionNet | 낙상, 쓰러짐, 장시간 미움직임 |
| 데이터 증강 | TAO augmentation | 회전, 크롭, 색상 변환, 모자이크 |
| 모델 평가 | `tao model evaluate` | mAP, precision, recall, F1 자동 산출 |
| 가지치기 | `tao model prune` | 모델 크기 축소 (불필요 파라미터 제거) |
| 내보내기 | `tao model export` | ONNX/TensorRT 엔진 내보내기 |
| INT8 양자화 | `tao model calibrate` | INT8 캘리브레이션으로 추론 가속 |

**TAO 학습 워크플로우:**
```
[현장 영상 수집] → [데이터 정제·라벨링]
    → [TAO Train: Fine-tuning (GPU)]
    → [TAO Evaluate: 성능 검증]
    → [TAO Prune: 모델 경량화]
    → [TAO Export: TensorRT 엔진 생성]
    → [DeepStream 배포 패키징]
    → [Edge AI 서버 Hot-swap 배포]
```

### 3.3 TensorRT (추론 최적화)

| 항목 | 내용 |
|------|------|
| 역할 | TAO 학습 모델을 Edge에서 최대 속도로 실행 |
| 정밀도 | FP16 (기본), INT8 (최적화 시) |
| 최적화 방식 | Layer/Tensor Fusion, Kernel Auto-Tuning |
| 배포 형태 | `.engine` 파일 → DeepStream `nvinfer` 로드 |
| 성능 목표 | 8채널 동시 추론 @ 15fps, 지연 ≤ 100ms/frame |


---

## 4. 시스템 아키텍처

### 4.1 전체 데이터 흐름

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          현장 (On-Premise)                                 │
│                                                                          │
│  [IP Camera x8] ──RTSP──→ ┌──────────────────────────────────┐          │
│                            │   판별형 Edge AI 서버              │          │
│  [스마트밴드x8] ──MQTT──→  │                                   │          │
│  [환경센서 x2]  ──MQTT──→  │  ┌─────────────────────────────┐ │          │
│  [화재감지 접점] ──GPIO──→  │  │  DeepStream Pipeline        │ │          │
│                            │  │  nvstreammux → nvinfer →     │ │          │
│                            │  │  nvtracker → nvdsanalytics → │ │          │
│                            │  │  nvmsgconv → Event Broker    │ │──→[알람]  │
│                            │  └─────────────────────────────┘ │          │
│                            │         │                        │          │
│                            │  [Event Processor] [Cloud Sync]  │          │
│                            └──────────┼───────────────────────┘          │
│                                       │                                   │
│  ┌────────────────────────────────────┼──────────────────────┐           │
│  │  로컬 AI 엣지 학습·최적화 서버      │                       │           │
│  │                                    ▼                       │           │
│  │  [데이터 수집] → [라벨링] → [TAO Train] → [TAO Export]     │           │
│  │                                              │             │           │
│  │  [TensorRT 최적화] ← [TAO Prune] ←──────────┘             │           │
│  │         │                                                  │           │
│  │         └──→ [DeepStream 배포 패키징] ──→ Edge AI 서버      │           │
│  └────────────────────────────────────────────────────────────┘           │
│                                                                          │
│  [8채널 NVR 2TB] ← 이벤트 기반 영상 클립 저장                              │
└──────────────────────────────────┼───────────────────────────────────────┘
                                   │ (인터넷)
                                   ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                          AWS 클라우드                                      │
│                                                                          │
│  [IoT Core] [S3: 모델·이벤트] [RDS: 메타데이터] [대시보드 API]             │
│  [모델 레지스트리] [원격 모니터링] [운영 리포트]                              │
└──────────────────────────────────────────────────────────────────────────┘
```

### 4.2 네트워크 장애 대응

| 상태 | 동작 방식 |
|------|-----------|
| **정상 연결** | DeepStream 이벤트 → Cloud 실시간 전송, 원격 모니터링 |
| **네트워크 장애** | DeepStream 파이프라인 로컬 독립 동작, 이벤트 Redis 큐잉 |
| **네트워크 복구** | 큐잉된 이벤트 일괄 동기화, 모델 업데이트 확인 |

---

## 5. 확장 가능한 ID 체계 설계

| ID 유형 | 형식 예시 | 설명 |
|---------|-----------|------|
| **현장 ID (site_id)** | `SITE-001` | 다중 현장 확장 대비 |
| **장비 ID (device_id)** | `CAM-001`, `BAND-003`, `ENV-002` | 장비 유형 + 일련번호 |
| **작업자 ID (worker_id)** | `WKR-0001` | 작업자 고유 식별 |
| **이벤트 ID (event_id)** | `EVT-{timestamp}-{seq}` | 시간 기반 유일성 보장 |
| **모델 버전 (model_version)** | `v1.0.0-tao-ds` | 시맨틱 버전 + 학습도구 + 배포대상 |
| **위험등급 (risk_level)** | `CRITICAL`, `WARNING`, `NORMAL` | 3단계 위험 분류 |
| **유지보수 로그 ID (maint_id)** | `MAINT-{date}-{seq}` | 유지보수 이력 추적 |


---

## 6. Platform 1.0 구현 범위 (DeepStream 중심)

### 6.1 목표

> DeepStream SDK 기반 실시간 영상 수집·추론·이벤트 생성 구조를 우선 구현하여, 센서→판단→알람 End-to-End 파이프라인을 통합 동작시킨다.

### 6.2 구현 범위

| 도메인 | 구현 내용 | 핵심 기술 |
|--------|-----------|-----------|
| 영상 수집·추론 | 8채널 RTSP → DeepStream 파이프라인 → 이벤트 | DeepStream SDK |
| AI 모델 | 사전학습 모델(PeopleNet/YOLOv8) TensorRT 변환 | TensorRT |
| 위험 감지 | 낙상, 쓰러짐, 장시간 미움직임, 위험구역 접근 | nvinfer + nvdsanalytics |
| 센서 연동 | 스마트밴드 8개, 환경센서 2개, 화재감지 접점 | MQTT + GPIO |
| 이벤트 처리 | 위험등급 판정, 알람 라우팅, 이벤트 저장 | Redis + Python |
| 현장 알람 | 접점연동 사이렌/경광등 GPIO 제어 | GPIO |
| 대시보드 | 실시간 현황, 이벤트 로그, 시스템 상태 (MVP) | React + FastAPI |
| 클라우드 | 이벤트 전송, 원격 모니터링, 모델 버전 관리 | AWS IoT + S3 |
| 학습 서버 | TAO 기본 환경 구축, 데이터 수집 파이프라인, 모델 배포 경로 | TAO Toolkit (기본) |

### 6.3 Platform 1.0 DeepStream 감지 모델

| 감지 유형 | 모델 | 추론 방식 | 등급 |
|-----------|------|-----------|------|
| 사람 감지 | PeopleNet (TAO pretrained) | Primary nvinfer | - |
| 낙상 감지 | ActionRecognitionNet | Secondary nvinfer | CRITICAL |
| 쓰러짐 감지 | Pose + Rule-based | nvinfer + analytics | CRITICAL |
| 장시간 미움직임 | nvtracker + 시간 규칙 | nvdsanalytics | WARNING |
| 위험구역 접근 | ROI polygon | nvdsanalytics | CRITICAL |
| 위험행동 | 급격한 움직임 패턴 | nvtracker 궤적 분석 | WARNING |

---

## 7. Platform 1.0 검수 기준

### 7.1 기능 검수

| 검수 항목 | 합격 기준 | 검증 방법 |
|-----------|-----------|-----------|
| DeepStream 8채널 수집 | 8대 RTSP 동시 디코딩·추론 정상 | 전 채널 동시 모니터링 |
| AI 위험 감지 | 낙상·쓰러짐·위험구역 감지율 ≥ 80% | 시나리오 10회 이상 테스트 |
| 추론 지연 | 프레임 수신 → 이벤트 생성 ≤ 200ms | 타임스탬프 측정 |
| 스마트밴드 연동 | 8밴드 동시 생체·위치 데이터 수신 | 전 밴드 실시간 확인 |
| 접점연동 알람 | CRITICAL 5초 이내 경보 동작 | End-to-End 테스트 |
| 네트워크 독립 동작 | 인터넷 차단 시 DeepStream+알람 정상 | 네트워크 분리 테스트 |
| 클라우드 동기화 | 복구 후 5분 이내 이벤트 동기화 | 장애→복구 시나리오 |
| 72시간 연속 운영 | 오류·메모리 누수 없음 | 장기 운영 테스트 |
| 모델 배포 | 학습서버 → Edge DeepStream 모델 교체 정상 | 모델 업데이트 테스트 |

### 7.2 검수 절차

1. **단위 테스트**: DeepStream 파이프라인 개별 요소 확인
2. **통합 테스트**: 전체 End-to-End (카메라→DeepStream→이벤트→알람→대시보드)
3. **시나리오 테스트**: 낙상, 쓰러짐, 위험구역 침입 시나리오
4. **장애 테스트**: 네트워크 장애, 카메라 장애, GPU 장애 대응
5. **성능 테스트**: 8채널 동시 처리 부하, 추론 지연 측정
6. **장기 운영 테스트**: 72시간 연속 운영 안정성

---

## 8. Platform 2.0 확장 범위 (TAO 본격 적용)

> TAO Toolkit 기반 현장 맞춤형 AI 모델 학습·검증·최적화 구조를 본격 구현

### 8.1 TAO 학습 파이프라인 고도화

- 현장 영상 자동 수집·라벨링 보조 도구
- TAO 기반 전이학습 자동화 (스케줄 학습)
- 오탐/미탐 피드백 루프 → 자동 재학습 트리거
- A/B 모델 배포: 기존 모델 vs 신규 모델 성능 비교
- 모델 성능 대시보드 (mAP, 오탐률, 미탐률 추이)

### 8.2 운영 관리 기능

- 작업자 관리, 장비 관리, 알림 규칙 관리
- 일간/주간/월간 안전 리포트 자동 생성
- 역할 기반 접근 제어 (RBAC)

### 8.3 감지 모델 확장

- 작업 유형별 위험행동 모델 분화
- 시간대·계절별 환경 보정 모델
- 다중 카메라 크로스뷰 추적

---

## 9. Platform 3.0 확장 범위 (TAO+DeepStream SaaS)

> TAO + DeepStream 기반 다중 현장 모델 운영, 자동 재학습, 원격 배포, SaaS형 AI 운영 플랫폼

### 9.1 다중 현장 AI 운영

- 현장별 DeepStream 설정 원격 관리
- 현장별 TAO 모델 독립 학습·배포
- 현장 간 모델 성능 비교·베스트 모델 공유
- 중앙 모델 레지스트리 + 현장별 배포 스케줄

### 9.2 자동화·지능화

- 자동 재학습 트리거 (성능 하락 감지 시)
- 연합학습 (Federated Learning) 기반 다중 현장 모델 개선
- 자동 모델 검증 + 자동 배포 파이프라인 (MLOps)
- 예측형 안전 관리 (사고 발생 전 조기 경보)

### 9.3 SaaS 전환

- 테넌트 격리 아키텍처, 구독 기반 과금
- 온보딩 자동화 (새 현장: DeepStream 설정 + TAO 모델 배포)
- API Gateway 기반 외부 연동
- 소방서·병원 자동 신고 연동

---

## 10. 기술 스택

| 레이어 | 기술 | 비고 |
|--------|------|------|
| **영상 수집·추론** | NVIDIA DeepStream SDK 6.x / 7.x | GStreamer 기반 파이프라인 |
| **AI 모델 학습** | NVIDIA TAO Toolkit 5.x | 전이학습, Fine-tuning |
| **추론 최적화** | NVIDIA TensorRT 8.x+ | FP16/INT8 엔진 생성 |
| **GPU 컴퓨팅** | CUDA 12.x + cuDNN 8.x | GPU 가속 기반 |
| Edge 서버 OS | Ubuntu 22.04 LTS + NVIDIA GPU Driver | 안정성 확보 |
| 데이터 파이프라인 | MQTT (Mosquitto) + Redis Stream | 경량 실시간 메시징 |
| 이벤트 큐 | Redis (로컬) + AWS IoT Core (클라우드) | 장애 시 로컬 큐잉 |
| 클라우드 | AWS S3, RDS (PostgreSQL), IoT Core, ECS | 원격 운영 |
| 대시보드 Frontend | React / Next.js | 실시간 모니터링 UI |
| 대시보드 Backend | FastAPI (Python) | REST + WebSocket API |
| 컨테이너 | Docker + Docker Compose + NVIDIA Container Toolkit | DeepStream/TAO 컨테이너 |
| IaC | Terraform | AWS 인프라 관리 (Platform 2.0+) |

---

## 11. 제약 사항 및 전제 조건

### 11.1 제약 사항

- Edge AI 서버: NVIDIA GPU 필수 (최소 RTX 3060, 권장 RTX 4080 이상)
- 학습 서버: NVIDIA GPU 필수 (권장 RTX 4090 / A5000 이상, VRAM 16GB+)
- DeepStream SDK는 Linux (Ubuntu) 전용
- TAO Toolkit은 Docker 환경에서 실행
- 현장 네트워크: 유선 LAN 기반 (Wi-Fi는 스마트밴드 연동용)
- 개인정보보호법, 장애인복지법, 산업안전보건법 준수

### 11.2 전제 조건

- NVIDIA GPU Driver + CUDA + cuDNN 설치 완료
- NVIDIA Container Toolkit 설치 완료
- DeepStream SDK 컨테이너 환경 준비
- TAO Toolkit Docker 이미지 준비
- 현장 네트워크 인프라 구축 완료
- AWS 계정 및 기본 인프라 설정 완료
- 작업자 동의 및 개인정보 처리 동의 확보

---

## 12. 향후 문서 확장 계획

| 문서 | 내용 | 시점 |
|------|------|------|
| `requirements.md` | DeepStream/TAO 기반 상세 요구사항 | inception 확정 후 |
| `design.md` | DeepStream 파이프라인 상세 설계, TAO 워크플로우 | 요구사항 확정 후 |
| `software-architecture.md` | NVIDIA 기반 소프트웨어 아키텍처 전체도 | 설계 확정 후 |
| `platform-roadmap.md` | Platform 1.0/2.0/3.0 상세 로드맵 | 설계 확정 후 |
| `tasks.md` | 구현 작업 분해, 스프린트 계획 | 설계 확정 후 |
| `test-plan.md` | DeepStream/TAO 테스트 전략, 검수 시나리오 | 설계 확정 후 |

---

## 변경 이력

| 버전 | 일자 | 작성자 | 내용 |
|------|------|--------|------|
| 0.1 | 2025-05-19 | AI | 초안 작성 |
| 0.2 | 2025-05-19 | AI | NVIDIA DeepStream SDK + TAO Toolkit 핵심 기술 반영, 플랫폼 버전별 기술 적용 재정의 |
