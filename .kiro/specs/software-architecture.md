# Software Architecture - NVIDIA 기반 소프트웨어 아키텍처

> **참조:** #[[file:.kiro/specs/inception.md]] | #[[file:.kiro/specs/design.md]]
> **핵심:** DeepStream SDK + TAO Toolkit + TensorRT 기반 계층 아키텍처

---

## 1. 아키텍처 개요

### 1.1 시스템 계층 구조

```
┌─────────────────────────────────────────────────────────────────────────┐
│ Layer 6: Presentation                                                    │
│   [Dashboard UI (React/Next.js)] [Mobile Alert] [Remote Admin]          │
├─────────────────────────────────────────────────────────────────────────┤
│ Layer 5: API & Integration                                               │
│   [Dashboard Backend (FastAPI)] [WebSocket] [REST API v1]               │
├─────────────────────────────────────────────────────────────────────────┤
│ Layer 4: Application Services                                            │
│   [Event Processor] [Alarm Controller] [Cloud Sync] [Sensor Service]    │
├─────────────────────────────────────────────────────────────────────────┤
│ Layer 3: AI / ML Engine                                                  │
│   ┌──────────────────────────┐  ┌──────────────────────────────┐       │
│   │ DeepStream Pipeline      │  │ TAO Training Pipeline         │       │
│   │ (Edge AI 서버)            │  │ (학습·최적화 서버)             │       │
│   │                           │  │                               │       │
│   │ nvinfer (TensorRT)       │  │ TAO train/prune/export       │       │
│   │ nvtracker (NvDCF)        │  │ TensorRT calibrate           │       │
│   │ nvdsanalytics (ROI)      │  │ Model Registry               │       │
│   └──────────────────────────┘  └──────────────────────────────┘       │
├─────────────────────────────────────────────────────────────────────────┤
│ Layer 2: Data & Messaging                                                │
│   [Redis Streams] [MQTT Broker] [PostgreSQL] [File Storage (NFS)]       │
├─────────────────────────────────────────────────────────────────────────┤
│ Layer 1: Infrastructure                                                  │
│   [NVIDIA GPU + CUDA + cuDNN] [Docker + NVIDIA Container Toolkit]       │
│   [Ubuntu 22.04 LTS] [Network (LAN/Internet)] [GPIO/RS-485]            │
├─────────────────────────────────────────────────────────────────────────┤
│ Layer 0: Physical Devices                                                │
│   [IP Camera x8] [Smart Band x8] [Env Sensor x2] [Fire Contact]        │
│   [NVR] [Alarm Device (Siren/Light)]                                    │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.2 물리 서버 배치

```
┌────────────────────────────────────┐  ┌────────────────────────────────┐
│   판별형 Edge AI 서버               │  │   학습·최적화 서버              │
│   (RTX 3060+, 16GB RAM)           │  │   (RTX 4090/A5000, 32GB RAM)  │
│                                    │  │                                │
│   • DeepStream Pipeline            │  │   • TAO Toolkit (Docker)       │
│   • Event Processor                │  │   • TAO Manager API            │
│   • Alarm Controller               │  │   • Data Collection            │
│   • Sensor Service                 │  │   • Label Tool (CVAT)          │
│   • Cloud Sync                     │  │   • TensorRT Optimization      │
│   • Dashboard Backend              │  │   • Model Deploy Agent         │
│   • Redis + Mosquitto              │  │   • Redis (학습 큐)             │
│                                    │  │                                │
│   [GPU: 추론 전용]                  │  │   [GPU: 학습 + 최적화]          │
└────────────────────────────────────┘  └────────────────────────────────┘
          │                                          │
          │          LAN (1Gbps)                     │
          └──────────────────────────────────────────┘
                              │
                        [Internet Gateway]
                              │
                    ┌─────────┴──────────┐
                    │    AWS Cloud        │
                    │  IoT Core + S3     │
                    │  RDS + ECS         │
                    └────────────────────┘
```


---

## 2. 컴포넌트 상세

### 2.1 Edge AI 서버 컴포넌트

```
┌─────────────────────────────────────────────────────────────────┐
│                    Edge AI Server                                 │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │          DeepStream Application Container                │    │
│  │                                                          │    │
│  │  ┌─────────┐ ┌────────┐ ┌────────┐ ┌──────────────┐   │    │
│  │  │ Source  │→│ PGIE   │→│Tracker │→│ SGIE         │   │    │
│  │  │ Manager │ │(TensorRT)│ │(NvDCF) │ │(Action Recog)│   │    │
│  │  └─────────┘ └────────┘ └────────┘ └──────┬───────┘   │    │
│  │                                             │            │    │
│  │  ┌──────────────┐  ┌───────────┐  ┌───────▼───────┐   │    │
│  │  │ NVR Recorder │←─│ OSD       │←─│ Analytics     │   │    │
│  │  │ (splitmux)   │  │(nvdsosd)  │  │(nvdsanalytics)│   │    │
│  │  └──────────────┘  └───────────┘  └───────┬───────┘   │    │
│  │                                             │            │    │
│  │  ┌──────────────────────────────────────────▼───────┐   │    │
│  │  │ Message Converter + Broker (nvmsgconv/broker)     │   │    │
│  │  │ Output: Redis Stream (stream:ds-events)           │   │    │
│  │  └──────────────────────────────────────────────────┘   │    │
│  │                                                          │    │
│  │  [DeepStream Manager API: :8001]                        │    │
│  │  - GET /health (pipeline status, fps, GPU)              │    │
│  │  - GET /pipeline/sources (카메라 목록·상태)              │    │
│  │  - POST /pipeline/sources/{id}/reconnect               │    │
│  │  - GET /models (로드된 모델 목록)                        │    │
│  │  - POST /models/{id}/reload (핫스왑)                    │    │
│  │  - GET /analytics/zones (ROI 설정 조회)                 │    │
│  │  - PUT /analytics/zones/{cam_id} (ROI 변경)            │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐   │
│  │ Event      │ │ Alarm      │ │ Sensor     │ │ Cloud      │   │
│  │ Processor  │ │ Controller │ │ Service    │ │ Sync       │   │
│  │ :8003      │ │ :8004      │ │ :8002      │ │ :8005      │   │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘   │
│                                                                  │
│  ┌────────────┐ ┌────────────┐                                  │
│  │ Dashboard  │ │ Redis 7    │                                  │
│  │ Backend    │ │ + Mosquitto│                                  │
│  │ :8080      │ │ :6379/1883 │                                  │
│  └────────────┘ └────────────┘                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 학습·최적화 서버 컴포넌트

```
┌─────────────────────────────────────────────────────────────────┐
│                 Training & Optimization Server                    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              TAO Toolkit Container                        │    │
│  │                                                          │    │
│  │  [tao model train]    - 전이학습 실행                     │    │
│  │  [tao model evaluate] - mAP/precision/recall 평가        │    │
│  │  [tao model prune]    - 모델 경량화                      │    │
│  │  [tao model export]   - ONNX/TRT 내보내기               │    │
│  │  [tao model calibrate]- INT8 캘리브레이션                 │    │
│  │                                                          │    │
│  │  Mounted Volumes:                                        │    │
│  │  /data/raw      → 수집된 원시 영상                       │    │
│  │  /data/labeled  → 라벨링된 데이터셋                      │    │
│  │  /data/splits   → train/val/test 분할                   │    │
│  │  /models/tao    → TAO 학습 결과                         │    │
│  │  /models/trt    → TensorRT 최적화 엔진                  │    │
│  │  /specs         → TAO 학습 설정 파일                     │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐    │
│  │ TAO Manager    │  │ Data Collector │  │ Deploy Agent   │    │
│  │ API :8006      │  │ Service        │  │ Service        │    │
│  │                │  │                │  │                │    │
│  │ - /datasets    │  │ - Edge이벤트   │  │ - Edge배포     │    │
│  │ - /training    │  │   클립 수집    │  │ - 핫스왑 요청  │    │
│  │ - /models      │  │ - NVR 영상    │  │ - 검증·롤백    │    │
│  │ - /deploy      │  │   추출        │  │ - 클라우드     │    │
│  │ - /pipeline    │  │ - 라벨 관리   │  │   동기화       │    │
│  └────────────────┘  └────────────────┘  └────────────────┘    │
│                                                                  │
│  ┌────────────────┐  ┌────────────────┐                         │
│  │ Label Tool     │  │ Redis          │                         │
│  │ (CVAT) :8888   │  │ :6379          │                         │
│  └────────────────┘  └────────────────┘                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. NVIDIA 소프트웨어 스택

### 3.1 기술 스택 의존성 계층

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                          │
│  DeepStream App | TAO Training | Dashboard | Event Services │
├─────────────────────────────────────────────────────────────┤
│                    SDK / Framework Layer                      │
│  DeepStream 7.x | TAO Toolkit 5.x | GStreamer 1.x          │
├─────────────────────────────────────────────────────────────┤
│                    Runtime Layer                              │
│  TensorRT 8.x | cuDNN 8.x | NCCL | OpenCV (GPU)           │
├─────────────────────────────────────────────────────────────┤
│                    Driver / CUDA Layer                        │
│  NVIDIA GPU Driver 535+ | CUDA 12.x                         │
├─────────────────────────────────────────────────────────────┤
│                    Container Layer                            │
│  Docker 24.x | NVIDIA Container Toolkit                     │
├─────────────────────────────────────────────────────────────┤
│                    OS Layer                                   │
│  Ubuntu 22.04 LTS (x86_64)                                  │
├─────────────────────────────────────────────────────────────┤
│                    Hardware Layer                             │
│  NVIDIA GPU (RTX 3060+ Edge / RTX 4090+ Training)           │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 컨테이너 이미지 구성

| 컨테이너 | Base Image | GPU | 용도 |
|----------|-----------|-----|------|
| deepstream-app | `nvcr.io/nvidia/deepstream:7.0-triton-multiarch` | ✅ | 영상 수집·추론·이벤트 |
| tao-toolkit | `nvcr.io/nvidia/tao/tao-toolkit:5.3.0-pyt` | ✅ | 모델 학습·최적화 |
| event-processor | `python:3.11-slim` | ❌ | 이벤트 판정·라우팅 |
| alarm-controller | `python:3.11-slim` | ❌ | GPIO 알람 제어 |
| sensor-service | `python:3.11-slim` | ❌ | 밴드·센서 데이터 수집 |
| cloud-sync | `python:3.11-slim` | ❌ | AWS 동기화 |
| dashboard-backend | `python:3.11-slim` | ❌ | REST + WebSocket API |
| tao-manager | `python:3.11-slim` | ❌ | TAO 작업 관리 API |
| redis | `redis:7-alpine` | ❌ | 메시지 브로커 + 큐 |
| mosquitto | `eclipse-mosquitto:2` | ❌ | MQTT 브로커 |


---

## 4. 데이터 흐름 아키텍처

### 4.1 실시간 감지 경로 (Critical Path)

```
[IP Camera RTSP]
    │ (H.264/H.265, 1080p@15fps)
    ▼
[DeepStream: nvv4l2decoder] ── GPU HW Decode
    │
    ▼
[DeepStream: nvstreammux] ── Batch 8 frames
    │
    ▼
[DeepStream: nvinfer PGIE] ── TensorRT FP16, PeopleNet
    │ (person bbox + confidence)
    ▼
[DeepStream: nvtracker] ── NvDCF, tracking_id 부여
    │
    ▼
[DeepStream: nvinfer SGIE] ── TensorRT FP16, ActionRecognition
    │ (action class: fall/collapse/normal)
    ▼
[DeepStream: nvdsanalytics] ── ROI 침입, Dwell Time 판단
    │
    ▼
[DeepStream: nvmsgconv] ── JSON 이벤트 메타데이터 생성
    │
    ▼
[Redis Stream: stream:ds-events] ── 이벤트 발행
    │
    ▼
[Event Processor] ── 위험등급 판정 (YAML 규칙)
    │
    ├──→ [stream:alarms] → [Alarm Controller] → [GPIO: 사이렌/경광등]
    ├──→ [stream:dashboard] → [Dashboard Backend] → [WebSocket → Browser]
    └──→ [stream:cloud-queue] → [Cloud Sync] → [AWS IoT Core]
```

**지연 시간 예산 (End-to-End ≤ 5초):**

| 구간 | 목표 지연 |
|------|-----------|
| RTSP 수신 → GPU 디코딩 | ≤ 50ms |
| 디코딩 → PGIE 추론 | ≤ 70ms |
| PGIE → Tracker → SGIE | ≤ 50ms |
| SGIE → Analytics → Event | ≤ 30ms |
| Event → Redis 발행 | ≤ 5ms |
| Redis → Event Processor 판정 | ≤ 20ms |
| Event Processor → Alarm GPIO | ≤ 50ms |
| **합계 (카메라→알람)** | **≤ 275ms** |
| 네트워크 마진 + 시스템 부하 | ≤ 4.7초 |
| **검수 기준** | **≤ 5초** |

### 4.2 모델 학습·배포 경로

```
[Edge AI 서버]                    [학습·최적화 서버]              [AWS Cloud]
     │                                  │                           │
     │ ①이벤트 클립 전송               │                           │
     │──────────────────────────────→  │                           │
     │                                  │                           │
     │                          ② 데이터 정제·라벨링               │
     │                          ③ TAO train (Fine-tuning)         │
     │                          ④ TAO evaluate (검증)             │
     │                          ⑤ TAO prune (경량화)              │
     │                          ⑥ TAO export (TensorRT)          │
     │                                  │                           │
     │ ⑦ 모델 배포 (.engine)           │                           │
     │←─────────────────────────────── │                           │
     │                                  │                           │
     │ ⑧ DeepStream 모델 핫스왑        │ ⑨ 모델 클라우드 동기화    │
     │ (nvinfer reload)                │──────────────────────────→│
     │                                  │                           │
     │ ⑩ 배포 검증 (10프레임 정확도)    │                           │
     │ (실패 시 ⑪ 롤백)                │                           │
```

### 4.3 센서 융합 경로

```
[스마트밴드 x8] ──BLE/WiFi──→ [BLE Gateway] ──MQTT──→ [Sensor Service]
[환경센서 x2]  ──────────────────MQTT──────────────→ [Sensor Service]
[화재감지 접점] ──GPIO────────────────────────────→ [Sensor Service]
                                                           │
                                                    [Redis: stream:sensors]
                                                           │
                                              [Event Processor: 융합 판단]
                                                           │
                                         ┌─────────────────┼─────────────┐
                                         ▼                 ▼             ▼
                                   [알람]          [대시보드]       [클라우드]
```

---

## 5. 확장성 설계 (Platform 3.0 대비)

### 5.1 다중 현장 아키텍처 (목표 상태)

```
┌──────────────────────────────────────────────────────────────────┐
│                        AWS Cloud (Central)                         │
│                                                                   │
│  [API Gateway] [Model Registry] [Event Store] [Admin Dashboard]  │
│  [MLOps Pipeline] [Federated Learning Coordinator]                │
│                                                                   │
└───────────┬──────────────────┬──────────────────┬────────────────┘
            │                  │                  │
     ┌──────┴──────┐   ┌──────┴──────┐   ┌──────┴──────┐
     │ Site A       │   │ Site B       │   │ Site C       │
     │ Edge AI      │   │ Edge AI      │   │ Edge AI      │
     │ DeepStream   │   │ DeepStream   │   │ DeepStream   │
     │ + TAO Local  │   │ + TAO Local  │   │ + TAO Local  │
     └─────────────┘   └─────────────┘   └─────────────┘
```

### 5.2 확장 포인트

| 확장 포인트 | Platform 1.0 (현재) | Platform 3.0 (목표) |
|------------|--------------------|--------------------|
| 현장 수 | 1 | N (멀티 테넌트) |
| 카메라 수 | 8 | 현장당 16~32 |
| AI 모델 수 | 2 (PGIE + SGIE) | 현장당 5+ (특화 모델) |
| 학습 주기 | 수동 | 자동 (성능 하락 트리거) |
| 모델 배포 | 수동 (API 호출) | 자동 (MLOps 파이프라인) |
| 대시보드 | 단일 현장 | 멀티 사이트 통합 |

### 5.3 설정 외부화 원칙

모든 변경 가능한 값을 코드가 아닌 설정 파일/환경변수로 관리:

| 설정 유형 | 파일 | 변경 주체 |
|-----------|------|-----------|
| DeepStream 소스 (카메라 URL) | `source_list.yml` | 관리자 |
| AI 모델 경로·파라미터 | `pgie_config.yml` | 배포 시스템 |
| 위험구역 ROI | `roi/{cam_id}.yml` | 관리자 |
| 위험등급 규칙 | `risk_rules.yml` | 관리자 |
| 센서 임계치 | `thresholds.yml` | 관리자 |
| 서비스 연결 정보 | `.env` / Secrets | 인프라 팀 |

---

## 6. 장애 대응 아키텍처

### 6.1 장애 시나리오별 대응

| 장애 유형 | 영향 범위 | 자동 대응 | 수동 대응 |
|-----------|-----------|-----------|-----------|
| 인터넷 끊김 | 클라우드 동기화 중단 | 로컬 큐잉 + DeepStream 독립 동작 | 네트워크 복구 |
| 카메라 1대 장애 | 해당 채널 추론 중단 | 나머지 7채널 정상 + 재연결 시도 | 카메라 교체 |
| GPU 장애 | 영상 AI 추론 불가 | 센서 기반 판단 유지 + 알람 동작 | GPU 교체/재시작 |
| Redis 장애 | 내부 메시지 중단 | systemd 재시작 + 파일 백업 큐 | 수동 점검 |
| DeepStream 크래시 | 전체 영상 분석 중단 | systemd watchdog 5초 내 재시작 | 로그 분석 |
| 모델 배포 실패 | 신규 모델 미작동 | 이전 모델 자동 롤백 | 모델 재학습 |
| 학습 서버 장애 | 모델 개선 불가 | Edge AI는 독립 동작 계속 | 서버 복구 |

### 6.2 Watchdog 설계

```yaml
# systemd service: deepstream-safety.service
[Service]
ExecStart=/usr/bin/docker compose up deepstream-app
Restart=always
RestartSec=5
WatchdogSec=30

# Health check: deepstream-app container
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8001/health"]
  interval: 10s
  timeout: 5s
  retries: 3
  start_period: 30s
```

---

## 7. 보안 아키텍처

### 7.1 네트워크 분리

```
┌─────────────────────────────────────────────────────────┐
│ VLAN 10: Camera Network (192.168.10.0/24)               │
│   - IP Camera x8 (RTSP only, 인터넷 차단)               │
├─────────────────────────────────────────────────────────┤
│ VLAN 20: Sensor/Band Network (192.168.20.0/24)          │
│   - 환경센서, 스마트밴드 AP (MQTT only)                  │
├─────────────────────────────────────────────────────────┤
│ VLAN 30: Server Network (192.168.30.0/24)               │
│   - Edge AI 서버, 학습 서버 (내부 통신)                  │
├─────────────────────────────────────────────────────────┤
│ VLAN 40: Management/Internet (192.168.40.0/24)          │
│   - 대시보드 접근, 클라우드 연결, 관리                    │
└─────────────────────────────────────────────────────────┘
```

### 7.2 인증·암호화 매트릭스

| 통신 경로 | 인증 | 암호화 | 비고 |
|-----------|------|--------|------|
| Camera → DeepStream | IP 기반 ACL | 없음 (VLAN 격리) | 내부 네트워크 |
| Sensor → MQTT | Username/PW | TLS (선택) | 내부 네트워크 |
| Edge → AWS IoT | X.509 인증서 | TLS 1.2+ | 필수 |
| Edge → AWS S3 | IAM STS | HTTPS | 필수 |
| Browser → Dashboard | JWT | HTTPS | 필수 |
| 학습서버 → Edge | API Key | 내부 LAN | 모델 배포 |

---

## 8. 모니터링·관측성

### 8.1 메트릭 수집

| 메트릭 | 소스 | 수집 주기 | 알림 조건 |
|--------|------|-----------|-----------|
| DeepStream FPS | DeepStream Manager API | 5초 | < 10fps |
| GPU 사용률 | nvidia-smi / NVML | 5초 | > 90% |
| GPU 메모리 | nvidia-smi / NVML | 5초 | > 90% |
| 추론 지연 | DeepStream probe | 10초 | > 200ms |
| 이벤트 처리량 | Event Processor | 10초 | - |
| Redis 메모리 | Redis INFO | 30초 | > 400MB |
| 디스크 사용률 | system | 60초 | > 80% |
| 카메라 상태 | DeepStream source | 10초 | DISCONNECTED |

### 8.2 로그 아키텍처

```
[모든 서비스] ──JSON 구조화 로그──→ [stdout/stderr]
                                        │
                                        ▼
                              [Docker log driver]
                                        │
                              ┌─────────┼──────────┐
                              ▼                    ▼
                     [로컬 파일 보관]        [CloudWatch (선택)]
                     (/var/log/safety/)      (Platform 2.0+)
```

---

## 변경 이력

| 버전 | 일자 | 내용 |
|------|------|------|
| 0.1 | 2025-05-19 | NVIDIA DeepStream/TAO 기반 소프트웨어 아키텍처 초안 |
