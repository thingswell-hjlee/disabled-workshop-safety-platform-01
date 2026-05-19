# Platform 1.0 시스템 상세 설계 (Design)

> **참조:** .kiro/specs/inception.md | .kiro/specs/requirements.md
> **범위:** Platform 1.0 (DeepStream 기반 실시간 감지·판단·알람)
> **핵심 기술:** NVIDIA DeepStream SDK + TAO Toolkit + TensorRT
> **설계 기준:** Platform 3.0 확장 가능 아키텍처

---

## 1. 전체 시스템 아키텍처

### 1.1 시스템 구성 개요

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                            현장 (On-Premise)                                  │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    판별형 Edge AI 서버                                │    │
│  │                                                                     │    │
│  │  [DeepStream Pipeline] ←── [IP Camera x8 RTSP]                     │    │
│  │       │                                                             │    │
│  │       ├──→ [Event Engine] ←── [Sensor Service] ←── [밴드/센서/화재] │    │
│  │       │         │                                                   │    │
│  │       │         ├──→ [Alarm Controller] ──→ [사이렌/경광등]          │    │
│  │       │         ├──→ [Rolling Buffer] ──→ [Local Storage]           │    │
│  │       │         ├──→ [Dashboard Backend] ──→ [Dashboard UI]         │    │
│  │       │         └──→ [AWS Sync Agent] ──→ [AWS Cloud]              │    │
│  │       │                                                             │    │
│  │       └──→ [NVR Service] ──→ [8채널 NVR 2TB]                       │    │
│  │                                                                     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                 로컬 AI 엣지 학습·최적화 서버                         │    │
│  │                                                                     │    │
│  │  [Data Collector] → [TAO Training] → [TensorRT Export]             │    │
│  │       → [Model Deploy Agent] → Edge AI 서버 Hot-swap                │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└──────────────────────────────────┬───────────────────────────────────────────┘
                                   │ Internet (MQTT over TLS / HTTPS)
                                   ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│  AWS Cloud: [IoT Core] [S3] [RDS] [ECS Dashboard] [Model Registry]          │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Patent-Aligned Context Intelligence Layer 적용

| Layer | 시스템 구현 | Platform |
|-------|------------|----------|
| **Perception** | DeepStream (nvinfer PGIE/SGIE, nvtracker, nvdsanalytics) + Sensor Service | 1.0 |
| **Cognition** | Event Engine (위험등급 판정, 센서 융합, 중복 억제, confidence 필터) | 1.0 |
| **Action** | Alarm Controller + Dashboard Alert + AWS Sync + NVR Clip | 1.0 |
| **Evolution** | TAO Fine-tuning → TensorRT → DeepStream Hot-swap | 1.0(기본)~2.0 |
| **Resilience** | 로컬 독립 동작, 이벤트 큐잉, Watchdog, 장비 장애 격리 | 1.0 |

### 1.3 설계 원칙

| 원칙 | 적용 |
|------|------|
| **DeepStream-Native** | 영상 처리 전체를 GStreamer/DeepStream 파이프라인으로 구성 |
| **GPU-First** | 디코딩·추론 모두 GPU 가속 (nvv4l2decoder, nvinfer TensorRT) |
| **Event-Driven** | 모든 감지 결과를 이벤트로 변환, Redis Streams 비동기 처리 |
| **Config-Driven** | 모델, ROI, 임계치, 소스를 YAML 설정 파일로 외부화 |
| **Fail-Safe** | 네트워크·GPU·카메라 장애 시 안전 기능 유지 |
| **Hot-Swappable** | 모델 교체 시 DeepStream 파이프라인 중단 최소화 |
| **Platform 3.0 Ready** | site_id, API 버전, 메시지 큐 기반 loose coupling |



---

## 2. Platform 1.0 동작 흐름

### 2.1 Critical Path (영상 감지 → 알람)

```
[IP Camera RTSP] → [DeepStream: GPU Decode → PGIE → Tracker → SGIE → Analytics]
    → [nvmsgconv: JSON 이벤트 생성] → [Redis: stream:ds-events]
    → [Event Engine: 위험등급 판정] → [Redis: stream:alarms]
    → [Alarm Controller: GPIO 출력] → [사이렌/경광등 동작]
                                                    
    동시 라우팅:
    → [Redis: stream:dashboard] → [Dashboard WebSocket] → [관리자 브라우저]
    → [Redis: stream:cloud-queue] → [AWS Sync Agent] → [AWS IoT Core]
    → [Rolling Buffer: 이벤트 전후 ±30초 클립 저장]
```

**지연 시간 예산 (End-to-End ≤ 5초):**

| 구간 | 목표 |
|------|------|
| RTSP 수신 → GPU 디코딩 | ≤ 50ms |
| PGIE 추론 (batch=8) | ≤ 70ms |
| Tracker + SGIE | ≤ 50ms |
| Analytics → Event JSON | ≤ 30ms |
| Redis 발행 → Event Engine | ≤ 20ms |
| Event Engine → Alarm GPIO | ≤ 50ms |
| **합계 (카메라→알람)** | **≤ 270ms** |
| 시스템 마진 | ≤ 4.7초|
| **검수 기준** | **≤ 5초** |

### 2.2 센서 감지 → 알람 경로

```
[스마트밴드/환경센서/화재감지] → [MQTT] → [Sensor Service]
    → [Redis: stream:sensors] → [Event Engine: 융합 판정]
    → [알람/대시보드/클라우드 라우팅]
```

### 2.3 모델 배포 경로

```
[학습 서버: TAO train 완료] → [TAO export → .engine]
    → [SCP/NFS → Edge AI 서버 /models/staged/]
    → [Deploy Agent: API → DeepStream nvinfer reload]
    → [검증 (10프레임 정확도)] → 성공: 활성화 / 실패: 롤백
```

---

## 3. Edge AI 서버 설계

### 3.1 하드웨어 요구사항

| 항목 | 최소 사양 | 권장 사양 |
|------|-----------|-----------|
| GPU | NVIDIA RTX 3060 (12GB VRAM) | RTX 4070 Ti (12GB) |
| CPU | Intel i7-12700 / AMD Ryzen 7 | Intel i9-13900 |
| RAM | 16GB DDR4 | 32GB DDR5 |
| 저장장치 | 512GB NVMe SSD | 1TB NVMe + 2TB HDD |
| 네트워크 | 1Gbps LAN (2포트) | 2.5Gbps LAN |
| OS | Ubuntu 22.04 LTS | Ubuntu 22.04 LTS |
| GPU Driver | 535+ | 545+ |
| CUDA | 12.2+ | 12.4 |

### 3.2 소프트웨어 스택

```
┌─────────────────────────────────────────────────┐
│ Application Layer                                │
│  DeepStream App | Event Engine | Dashboard API  │
├─────────────────────────────────────────────────┤
│ SDK / Framework                                  │
│  DeepStream 7.x | GStreamer 1.x | FastAPI       │
├─────────────────────────────────────────────────┤
│ Runtime                                          │
│  TensorRT 8.6+ | cuDNN 8.9 | Redis 7 | MQTT   │
├─────────────────────────────────────────────────┤
│ Container                                        │
│  Docker 24.x | NVIDIA Container Toolkit 1.14    │
├─────────────────────────────────────────────────┤
│ OS / Driver                                      │
│  Ubuntu 22.04 LTS | NVIDIA Driver 535+          │
├─────────────────────────────────────────────────┤
│ Hardware                                         │
│  NVIDIA GPU (RTX 3060+) | x86_64 Server         │
└─────────────────────────────────────────────────┘
```

### 3.3 컨테이너 구성

| 컨테이너 | Base Image | GPU | Port | 역할 |
|----------|-----------|-----|------|------|
| deepstream-app | nvcr.io/nvidia/deepstream:7.0 | ✅ | 8001 | 영상 수집·추론·이벤트 |
| event-engine | python:3.11-slim | ❌ | 8003 | 위험등급 판정·라우팅 |
| alarm-controller | python:3.11-slim | ❌ | 8004 | GPIO 알람 제어 |
| sensor-service | python:3.11-slim | ❌ | 8002 | 밴드·센서·화재 수집 |
| cloud-sync | python:3.11-slim | ❌ | 8005 | AWS 동기화 |
| dashboard-backend | python:3.11-slim | ❌ | 8080 | REST + WebSocket API |
| dashboard-ui | node:20-alpine | ❌ | 3000 | React/Next.js UI |
| redis | redis:7-alpine | ❌ | 6379 | 메시지 브로커 |
| mosquitto | eclipse-mosquitto:2 | ❌ | 1883 | MQTT 브로커 |

---

## 4. DeepStream 파이프라인 설계

### 4.1 파이프라인 전체 구조

```
[Source Group: 8x uridecodebin (RTSP)]
    │
    ▼
[nvstreammux: batch-size=8, width=1920, height=1080]
    │
    ▼
[PGIE (nvinfer): PeopleNet/YOLOv8, TensorRT FP16]
    │ output: person bbox + confidence
    ▼
[nvtracker: NvDCF, max_targets=50/source]
    │ output: tracking_id, trajectory
    ▼
[SGIE (nvinfer): ActionRecognitionNet, TensorRT FP16]
    │ output: action_class (normal/fall/collapse/stillness)
    ▼
[nvdsanalytics: ROI polygon, Dwell Time, Line Crossing]
    │ output: zone_intrusion, stillness_detected
    ▼
┌────────────────────────────────────────────┐
│ Tee (3-way split)                          │
│                                            │
│ Branch 1: [nvmsgconv] → [nvmsgbroker]     │
│            → Redis Stream: stream:ds-events│
│                                            │
│ Branch 2: [nvdsosd] → [nvv4l2h264enc]     │
│            → [splitmuxsink] → NVR/Clip    │
│                                            │
│ Branch 3: [nvdsosd] → [RTSP Server]       │
│            → Dashboard 영상 표시           │
└────────────────────────────────────────────┘
```

### 4.2 PGIE 설정 (Primary Inference)

```yaml
# pgie_config.yml
[property]
gpu-id=0
net-scale-factor=0.0039215697906911373
model-engine-file=/models/active/pgie/peoplenet_fp16.engine
labelfile-path=/models/active/pgie/labels.txt
batch-size=8
network-mode=2  # FP16
num-detected-classes=3
interval=2  # 매 2프레임마다 추론 (실효 7.5fps/ch)
gie-unique-id=1
process-mode=1  # primary
cluster-mode=2  # DBSCAN

[class-attrs-all]
pre-cluster-threshold=0.7
```

### 4.3 Tracker 설정 (NvDCF)

```yaml
# tracker_config.yml
[tracker]
tracker-width=640
tracker-height=384
gpu-id=0
ll-lib-file=/opt/nvidia/deepstream/deepstream/lib/libnvds_nvmultiobjecttracker.so
ll-config-file=tracker_config_NvDCF_perf.yml
enable-batch-process=1
enable-past-frame=1
display-tracking-id=1
```

### 4.4 Analytics 설정 (ROI/Dwell)

```yaml
# analytics_config.yml (per camera)
[property]
enable=1
config-width=1920
config-height=1080

[roi-filtering-stream-0]
enable=1
roi-CAM-001-DangerZone=380;400;600;400;600;700;380;700
inverse-roi=0

[overcrowding-stream-0]
enable=0

[line-crossing-stream-0]
enable=0
```

### 4.5 이벤트 메시지 변환 (nvmsgconv)

DeepStream이 생성하는 이벤트 JSON 스키마:

```json
{
  "event_id": "EVT-20250519120000-001",
  "site_id": "SITE-001",
  "source_id": 0,
  "device_id": "CAM-001",
  "event_type": "FALL_DETECTED",
  "timestamp": "2025-05-19T12:00:00.123Z",
  "model_version": "v1.0.0-tao-ds",
  "inference": {
    "pgie": {"class": "person", "confidence": 0.95, "bbox": [120, 80, 300, 450]},
    "sgie": {"class": "fall", "confidence": 0.88},
    "tracker": {"tracking_id": 42, "dwell_time_sec": 0.0}
  },
  "analytics": {
    "roi_name": "DangerZone-A",
    "in_roi": false,
    "line_crossed": false
  }
}
```



---

## 5. TensorRT 추론 구조

### 5.1 모델 최적화 흐름

```
[TAO 학습 결과 (.tlt/.etlt)]
    → [TAO export → ONNX]
    → [trtexec --onnx=model.onnx --fp16 --saveEngine=model_fp16.engine]
    → [DeepStream nvinfer 로드]
```

### 5.2 엔진 파일 관리

```
/models/
├── active/          # 현재 DeepStream 사용 중
│   ├── pgie/
│   │   ├── peoplenet_v1.0.0_fp16.engine
│   │   └── labels.txt
│   └── sgie/
│       ├── action_v1.0.0_fp16.engine
│       └── labels.txt
├── staged/          # 배포 대기
├── rollback/        # 이전 버전 (롤백용)
└── registry.json    # 로컬 모델 메타데이터
```

### 5.3 성능 목표

| 모델 | 입력 크기 | 정밀도 | 배치 | 목표 지연 |
|------|-----------|--------|------|-----------|
| PGIE (PeopleNet) | 960×544 | FP16 | 8 | ≤ 15ms/frame |
| SGIE (ActionRecog) | 224×224 | FP16 | 최대 50 | ≤ 5ms/object |

---

## 6. 장비 연동 구조

### 6.1 전체 장비 연결 다이어그램

```
┌─────────────────────────────────────────────────────────┐
│ VLAN 10: Camera Network (192.168.10.0/24)               │
│   CAM-001~008 ──RTSP──→ Edge AI (DeepStream)            │
├─────────────────────────────────────────────────────────┤
│ VLAN 20: Sensor/Band Network (192.168.20.0/24)          │
│   BAND-001~008 ──BLE→Gateway──MQTT──→ Sensor Service    │
│   ENV-001~002 ──MQTT──→ Sensor Service                  │
├─────────────────────────────────────────────────────────┤
│ VLAN 30: Server Network (192.168.30.0/24)               │
│   Edge AI Server ←→ Training Server (LAN)               │
├─────────────────────────────────────────────────────────┤
│ VLAN 40: Management (192.168.40.0/24)                   │
│   Dashboard 접근, Internet, AWS 연결                     │
└─────────────────────────────────────────────────────────┘

GPIO (직접 연결):
  FIRE-001 ──GPIO IN──→ Edge AI Server
  ALARM-001 ──GPIO OUT──→ Edge AI Server (사이렌/경광등)
```

### 6.2 장비 ID 체계

| 장비 유형 | ID 형식 | 수량 | 프로토콜 |
|-----------|---------|------|----------|
| IP Camera | CAM-001~008 | 8 | RTSP |
| 스마트밴드 | BAND-001~008 | 8 | BLE→MQTT |
| 환경센서 | ENV-001~002 | 2 | MQTT |
| 화재감지 | FIRE-001 | 1 | GPIO/RS-485 |
| 알람장치 | ALARM-001 | 1 | GPIO Relay |
| NVR | NVR-001 | 1 | API/RTSP |

---

## 7. 스마트밴드 연동 구조

### 7.1 데이터 흐름

```
[Smart Band x8] ──BLE──→ [BLE Gateway AP] ──Wi-Fi──→ [MQTT Broker]
                                                          │
                                          [Sensor Service: MQTT Subscribe]
                                                          │
                                          [Redis: stream:sensors]
```

### 7.2 MQTT 토픽 구조

```
safety/{site_id}/band/{device_id}/heartrate    → {"bpm": 72, "ts": "..."}
safety/{site_id}/band/{device_id}/temperature  → {"celsius": 36.5, "ts": "..."}
safety/{site_id}/band/{device_id}/accel        → {"x": 0.1, "y": 9.8, "z": 0.2, "ts": "..."}
safety/{site_id}/band/{device_id}/location     → {"x": 12.5, "y": 8.3, "zone": "A", "ts": "..."}
safety/{site_id}/band/{device_id}/battery      → {"percent": 85, "ts": "..."}
safety/{site_id}/band/{device_id}/status       → {"connected": true, "ts": "..."}
```

### 7.3 이상 판단 규칙

| 조건 | 이벤트 | 등급 |
|------|--------|------|
| 심박 < 40 또는 > 150 bpm | HEARTRATE_ABNORMAL | CRITICAL |
| 체온 < 35 또는 > 38.5°C | TEMPERATURE_ABNORMAL | WARNING |
| 가속도 급변 패턴 (4G+ → 0G) | BAND_FALL_DETECTED | CRITICAL |
| 30초 이상 데이터 미수신 | BAND_DISCONNECTED | WARNING |
| 배터리 ≤ 20% | BATTERY_LOW | WARNING |

---

## 8. 환경센서 연동 구조

### 8.1 데이터 흐름

```
[Env Sensor x2] ──MQTT──→ [Sensor Service]
                                │
                    [임계치 비교 → 이벤트 생성]
                                │
                    [Redis: stream:sensors]
```

### 8.2 MQTT 토픽

```
safety/{site_id}/env/{device_id}/data → {
  "temperature": 25.3,
  "humidity": 45.2,
  "co_ppm": 2.1,
  "voc_ppb": 120,
  "ts": "2025-05-19T12:00:00.000Z"
}
```

### 8.3 임계치 설정 (YAML)

```yaml
# thresholds.yml
environment:
  temperature_max: 40.0  # °C
  humidity_max: 85.0     # %
  co_ppm_max: 50.0       # ppm
  voc_ppb_max: 500.0     # ppb
  hysteresis: 2.0        # 복귀 시 -2 적용
```

---

## 9. 화재접점 입력 구조

### 9.1 하드웨어 연결

```
[화재감지기] ──Dry Contact──→ [Edge AI GPIO Pin 22 (BCM)]
                              │
                    [Sensor Service: GPIO Polling 5초 + Interrupt]
                              │
                    [디바운싱 500ms → FIRE_DETECTED 이벤트]
```

### 9.2 동작 로직

1. **폴링**: 5초 주기로 GPIO 핀 상태 확인
2. **인터럽트**: GPIO RISING edge 감지 시 즉시 처리
3. **디바운싱**: 500ms 이내 재발생 무시
4. **이벤트**: `FIRE_DETECTED` → 즉시 CRITICAL (confidence 무관)
5. **독립성**: 네트워크/GPU 장애와 무관하게 항상 동작

---

## 10. 접점 알람 출력 구조

### 10.1 GPIO 핀 배치

| GPIO Pin (BCM) | 방향 | 연결 장비 | 동작 |
|----------------|------|-----------|------|
| 17 | OUTPUT | 사이렌 릴레이 | HIGH = ON |
| 27 | OUTPUT | 경광등 릴레이 | HIGH = ON |

### 10.2 알람 정책

| 위험등급 | 사이렌 | 경광등 | 해제 방식 |
|----------|--------|--------|-----------|
| CRITICAL | ON | ON | 수동 Acknowledge만 |
| WARNING | OFF | ON | 5분 자동 또는 수동 |
| NORMAL | OFF | OFF | - |

### 10.3 Edge 독립 동작

- Alarm Controller는 Redis stream:alarms에서 명령 수신
- **네트워크 장애 시에도** Event Engine → Redis → Alarm Controller 경로는 로컬 동작
- GPIO 직접 제어이므로 클라우드 의존성 없음

---

## 11. NVR 연동 구조

### 11.1 연속 녹화

- DeepStream `splitmuxsink`로 8채널 H.264 인코딩 → NVR 저장
- NVR은 RTSP Sub-stream 또는 직접 파일 저장 방식

### 11.2 이벤트 클립 저장

```
[이벤트 발생] → [Rolling Buffer에서 전후 ±30초 추출]
              → [/clips/EVT-{id}.mp4 저장]
              → [메타데이터 기록 (event_id, path, duration)]
              → [AWS S3 업로드 큐 등록]
```

### 11.3 저장 관리

| 항목 | 설정 |
|------|------|
| 연속 녹화 보관 | 14일 (2TB 기준 8채널 1080p) |
| 이벤트 클립 보관 | 90일 (로컬) + 1년 (S3) |
| 용량 80% 알림 | 관리자 대시보드 + 이벤트 |

---

## 12. 적응형 롤링버퍼 기본 구조

### 12.1 Platform 1.0 구현 범위

Platform 1.0에서는 **기본 롤링버퍼**를 구현한다:

```
[DeepStream 출력 프레임]
    → [Ring Buffer: 최근 60초 분량 메모리 유지]
    → [이벤트 트리거 시: 전 30초 + 후 30초 = 60초 클립 추출]
    → [MP4 파일 저장 → Local Storage]
```

### 12.2 기본 동작

| 항목 | Platform 1.0 설정 |
|------|-------------------|
| 버퍼 크기 | 60초 (채널당) |
| 프레임 품질 | 원본 1080p H.264 |
| 이벤트 트리거 | Event Engine의 CRITICAL/WARNING 이벤트 |
| 저장 형식 | MP4 (H.264 + AAC) |
| 메타데이터 | event_id, device_id, start_ts, end_ts, duration |

### 12.3 Platform 2.0/3.0 확장 구조 (설계 반영)

- **L0~L3 저장 품질 제어**: 이벤트 중요도에 따라 해상도/프레임레이트 차등
- **적응형 버퍼 크기**: 활동지수에 따라 30초~120초 동적 조정
- **Generative 재추론**: 저장된 클립에 새 모델로 재분석

> Platform 1.0 데이터 구조에 `quality_level`, `buffer_duration_sec` 필드를 예약하여 확장 대비

---

## 13. 이벤트 전후 데이터 저장 구조

### 13.1 이벤트 컨텍스트 저장

이벤트 발생 시 관련 데이터를 `EventContext`로 묶어 저장:

```json
{
  "event_id": "EVT-20250519120000-001",
  "context": {
    "video_clip": {
      "path": "/clips/EVT-20250519120000-001.mp4",
      "start_ts": "2025-05-19T11:59:30.000Z",
      "end_ts": "2025-05-19T12:00:30.000Z",
      "duration_sec": 60,
      "quality_level": 0
    },
    "sensor_snapshot": {
      "band_data": {"bpm": 72, "temp": 36.5, "accel_peak": 1.2},
      "env_data": {"temperature": 25.3, "co_ppm": 2.1},
      "fire_status": "NORMAL"
    },
    "inference_detail": {
      "pgie_conf": 0.95,
      "sgie_conf": 0.88,
      "tracking_id": 42,
      "dwell_time_sec": 0.0,
      "roi_name": "DangerZone-A"
    },
    "system_state": {
      "gpu_util": 65.2,
      "active_cameras": 8,
      "network_status": "connected"
    }
  }
}
```

### 13.2 Platform 2.0/3.0 확장 필드 (예약)

```json
{
  "extended_context": {
    "activity_index_history": [],
    "generative_reanalysis": null,
    "audit_hash": null,
    "rag_reference": null
  }
}
```

---

## 14. 기본 활동지수 산출 구조

### 14.1 Platform 1.0 기본 활동지수

작업자별 실시간 활동 수준을 수치화하여 이상 감지 보조 지표로 활용:

```
ActivityIndex = w1 * MovementScore + w2 * PostureScore + w3 * HeartRateScore
```

| 요소 | 산출 방법 | 가중치 (기본) |
|------|-----------|--------------|
| MovementScore | nvtracker 궤적 속도 + 가속도 | 0.4 |
| PostureScore | SGIE action class (정상=1.0, 이상=0.0) | 0.4 |
| HeartRateScore | 심박수 정상 범위 비율 | 0.2 |

### 14.2 활동지수 활용

| 활동지수 | 상태 | 동작 |
|----------|------|------|
| 0.7 ~ 1.0 | 정상 활동 | 모니터링만 |
| 0.4 ~ 0.7 | 저활동 | 주의 관찰 |
| 0.0 ~ 0.4 | 이상 징후 | WARNING 이벤트 후보 |
| 30초 이상 0.1 미만 | 미움직임 확정 | STILLNESS 이벤트 |

### 14.3 Platform 2.0/3.0 확장

- 시간대별 기준선 자동 학습
- 작업자별 개인 정상 범위 프로파일링
- 활동지수 기반 적응형 버퍼 크기 조정

---

## 15. 이벤트 처리 및 위험등급 판별 구조

### 15.1 Event Engine 아키텍처

```
┌────────────────────────────────────────────────────────┐
│                   Event Engine Service                   │
│                                                         │
│  [Redis Consumer: stream:ds-events + stream:sensors]   │
│              │                                          │
│              ▼                                          │
│  ┌──────────────────────────────────────┐              │
│  │ Stage 1: Event Normalization         │              │
│  │ - DeepStream 이벤트 + 센서 이벤트    │              │
│  │ - 통합 스키마 변환                    │              │
│  └──────────────┬───────────────────────┘              │
│                  │                                      │
│                  ▼                                      │
│  ┌──────────────────────────────────────┐              │
│  │ Stage 2: Deduplication               │              │
│  │ - 동일 장비 + 유형: 10초 윈도우       │              │
│  │ - key: (device_id, event_type, tid)  │              │
│  └──────────────┬───────────────────────┘              │
│                  │                                      │
│                  ▼                                      │
│  ┌──────────────────────────────────────┐              │
│  │ Stage 3: Risk Classification         │              │
│  │ - YAML 규칙 엔진 기반                 │              │
│  │ - confidence 필터 (하향/무시)         │              │
│  │ - 복합 이벤트 평가                    │              │
│  └──────────────┬───────────────────────┘              │
│                  │                                      │
│                  ▼                                      │
│  ┌──────────────────────────────────────┐              │
│  │ Stage 4: Routing                     │              │
│  │ - stream:alarms (CRITICAL/WARNING)   │              │
│  │ - stream:dashboard (전체)            │              │
│  │ - stream:cloud-queue (전체)          │              │
│  │ - Rolling Buffer 트리거              │              │
│  └──────────────────────────────────────┘              │
└────────────────────────────────────────────────────────┘
```

### 15.2 위험등급 판정 규칙 (YAML)

```yaml
# risk_rules.yml
classification:
  CRITICAL:
    - event_type: FALL_DETECTED
      min_confidence: 0.70
    - event_type: COLLAPSE_DETECTED
      min_confidence: 0.70
    - event_type: ZONE_INTRUSION
      min_confidence: 0.75
    - event_type: FIRE_DETECTED
      source: contact  # confidence 무관
    - event_type: HEARTRATE_ABNORMAL
      source: band
    - event_type: BAND_FALL_DETECTED
      source: band

  WARNING:
    - event_type: STILLNESS_DETECTED
      dwell_time_min_sec: 30
    - event_type: ENV_THRESHOLD_EXCEEDED
    - event_type: TEMPERATURE_ABNORMAL
    - event_type: HAZARDOUS_ACTION
      min_confidence: 0.65
    - event_type: BAND_DISCONNECTED

deduplication:
  window_seconds: 10
  key_fields: [device_id, event_type, tracking_id]

confidence_downgrade:
  fall_below_0.7: WARNING
  behavior_below_0.65: IGNORE
```

---

## 16. AWS 이벤트 전송 구조

### 16.1 전송 아키텍처

```
[Event Engine] → [Redis: stream:cloud-queue]
                       │
              [AWS Sync Agent]
                       │
              ┌────────┴────────┐
              │  Online Mode    │ → [AWS IoT Core MQTT over TLS]
              │                 │      → IoT Rule → Lambda → RDS
              │  Offline Mode   │ → [Local Redis Queue (최대 10,000건)]
              │                 │      → 복구 시 순차 재전송
              └─────────────────┘
```

### 16.2 전송 데이터 (이벤트 메타데이터)

```json
{
  "event_id": "EVT-20250519120000-001",
  "site_id": "SITE-001",
  "device_id": "CAM-001",
  "worker_id": "WKR-0002",
  "event_type": "FALL_DETECTED",
  "risk_level": "CRITICAL",
  "confidence": 0.88,
  "model_version": "v1.0.0-tao-ds",
  "timestamp": "2025-05-19T12:00:00.123Z",
  "clip_s3_key": "events/SITE-001/2025/05/19/EVT-20250519120000-001.mp4",
  "context_summary": {
    "tracking_id": 42,
    "zone": "DangerZone-A",
    "activity_index": 0.15,
    "active_cameras": 8
  },
  "idempotency_key": "EVT-20250519120000-001"
}
```

### 16.3 영상 클립 업로드

- 이벤트 발생 → 클립 MP4 생성 → S3 Multipart Upload
- 업로드 실패 시 로컬 보관 + 재시도 큐

### 16.4 오프라인 큐잉 정책

| 항목 | 설정 |
|------|------|
| 큐 최대 크기 | 10,000건 |
| 우선순위 | CRITICAL > WARNING > NORMAL |
| 재전송 간격 | 5초 (Exponential Backoff: 5→10→20→40→60초) |
| 복구 후 동기화 | 5분 이내 전량 전송 |
| idempotency | event_id 기반 중복 방지 (24시간 TTL) |

---

## 17. 관리자 대시보드 구조

### 17.1 아키텍처

```
[Browser] ←──HTTPS/WSS──→ [Dashboard Backend (FastAPI)]
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
            [Redis Streams]  [Local SQLite]  [DeepStream RTSP]
            (실시간 이벤트)   (이벤트 이력)   (영상 스트림)
```

### 17.2 주요 페이지 구성

| 페이지 | 기능 | 데이터 소스 |
|--------|------|-------------|
| 메인 | 8채널 영상 + 위험등급 요약 + 작업자 상태 | RTSP + WebSocket |
| 이벤트 로그 | 시간순 목록, 필터, 상세, Acknowledge | REST API |
| 시스템 상태 | 장비 연결, GPU, DeepStream, 네트워크 | REST + WebSocket |
| 설정 | ROI 설정, 임계치, 알람 규칙 | REST API |
| 로그인 | ID/PW + JWT 발급 | REST API |

### 17.3 실시간 통신

- **WebSocket** (`/ws/dashboard`): 이벤트 알림, 장비 상태 변경, 활동지수
- **갱신 주기**: ≤ 3초 (WebSocket push)
- **영상**: DeepStream RTSP → WebRTC 또는 HLS 변환

---

## 18. 네트워크 장애 시 로컬 독립 운전 구조

### 18.1 독립 동작 범위

| 기능 | 인터넷 정상 | 인터넷 장애 | 비고 |
|------|-------------|-------------|------|
| DeepStream 8채널 추론 | ✅ | ✅ | GPU 로컬 |
| 위험등급 판정 | ✅ | ✅ | Redis 로컬 |
| 접점 알람 동작 | ✅ | ✅ | GPIO 직접 |
| 이벤트 저장 | ✅ | ✅ | 로컬 SQLite |
| 영상 클립 저장 | ✅ | ✅ | 로컬 디스크 |
| 대시보드 (로컬) | ✅ | ✅ | LAN 접근 |
| AWS 이벤트 전송 | ✅ | ❌→큐잉 | 복구 시 재전송 |
| 원격 대시보드 | ✅ | ❌ | 인터넷 필요 |
| 모델 클라우드 동기화 | ✅ | ❌ | 로컬 모델 유지 |

### 18.2 장애 감지 메커니즘

```
[Cloud Sync Agent: 30초 간격 Health Ping]
    → Ping 실패 3회 연속 → "OFFLINE" 모드 전환
    → 이벤트 로컬 큐잉 시작
    → Ping 성공 → "ONLINE" 복귀 → 큐 Flush
```

### 18.3 Watchdog 설계

```yaml
# systemd service (각 컨테이너)
[Service]
Restart=always
RestartSec=5
WatchdogSec=30

# Docker healthcheck
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:{port}/health"]
  interval: 10s
  timeout: 5s
  retries: 3
  start_period: 30s
```

---

## 19. Platform 2.0/3.0 확장 고려사항

### 19.1 Platform 1.0에서 확장 대비로 반영하는 설계 요소

| 확장 기능 | Platform 1.0 반영 | 확장 시점 |
|-----------|-------------------|-----------|
| L0~L3 저장 품질 제어 | `quality_level` 필드 예약 (기본값 0) | 2.0 |
| 적응형 버퍼 크기 | `buffer_duration_sec` 필드 예약 (기본값 60) | 2.0 |
| 활동지수 프로파일링 | 기본 산출 구조 구현 (고정 가중치) | 2.0 |
| Generative 재추론 | `reanalysis_result` 필드 예약 (null) | 3.0 |
| RAG 기반 검색 | 이벤트 메타데이터 구조화 저장 | 3.0 |
| 해시체인 감사 로그 | `audit_hash` 필드 예약 (null) | 3.0 |
| 다중 현장 | `site_id` 전 데이터 포함 | 3.0 |
| 자동 재학습 트리거 | 오탐/미탐 피드백 저장 구조 | 2.0 |
| A/B 모델 배포 | model_version 체계 (active/staged/rollback) | 2.0 |

### 19.2 데이터 구조 확장 원칙

1. **모든 스키마에 예약 필드 포함** (null 허용)
2. **API 버전 관리** (`/api/v1/`) - 하위 호환 유지
3. **이벤트 소싱**: 상태 변경은 이벤트로 기록 (재생 가능)
4. **설정 외부화**: 모든 임계치/규칙은 YAML/DB, 코드 하드코딩 금지
5. **메시지 큐 기반**: 서비스 간 Redis Streams loose coupling

### 19.3 Platform 3.0 멀티 사이트 구조 준비

```
Platform 1.0:
  [SITE-001] ──→ [AWS Cloud (단일 계정)]

Platform 3.0 (목표):
  [SITE-001] ──→ ┐
  [SITE-002] ──→ ├──→ [AWS Cloud (멀티 테넌트)]
  [SITE-003] ──→ ┘     ├── 중앙 모델 레지스트리
                        ├── 통합 대시보드
                        └── 현장별 격리 데이터
```

---

## 변경 이력

| 버전 | 일자 | 내용 |
|------|------|------|
| 1.0 | 2025-05-19 | Platform 1.0 시스템 상세 설계 초안 (19개 섹션) |
