# Platform 1.0 시스템 상세 설계 (Design)

> **참조:** #[[file:.kiro/specs/inception.md]] | #[[file:.kiro/specs/requirements.md]]
> **핵심 기술:** NVIDIA DeepStream SDK + TAO Toolkit + TensorRT

---

## 1. 설계 개요

### 1.1 설계 목표

DeepStream SDK 기반 실시간 영상 수집·추론·이벤트 생성 파이프라인을 중심으로, 센서 융합·알람·대시보드·클라우드를 통합 동작시키는 Platform 1.0 시스템을 설계한다.

### 1.2 설계 원칙

| 원칙 | 적용 |
|------|------|
| **DeepStream-Native** | 영상 처리 전체를 GStreamer/DeepStream 파이프라인으로 구성 |
| **GPU-First** | 디코딩·추론·인코딩 모두 GPU 가속 활용 |
| **Event-Driven** | 모든 감지 결과를 이벤트로 변환하여 비동기 처리 |
| **Config-Driven** | 모델, ROI, 임계치, 소스를 설정 파일로 외부화 |
| **Fail-Safe** | 네트워크·GPU·카메라 장애 시 안전 기능 유지 |
| **Hot-Swappable** | 모델 교체 시 파이프라인 중단 최소화 |

---

## 2. DeepStream 파이프라인 상세 설계

### 2.1 파이프라인 전체 구조

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DeepStream Application (deepstream-safety-app)            │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │ Source Group (8 RTSP Sources)                                         │   │
│  │                                                                       │   │
│  │  [uridecodebin:CAM-001] ──┐                                          │   │
│  │  [uridecodebin:CAM-002] ──┤                                          │   │
│  │  [uridecodebin:CAM-003] ──┤                                          │   │
│  │  [uridecodebin:CAM-004] ──┼──→ [nvstreammux (batch-size=8)]          │   │
│  │  [uridecodebin:CAM-005] ──┤         │                                │   │
│  │  [uridecodebin:CAM-006] ──┤         ▼                                │   │
│  │  [uridecodebin:CAM-007] ──┤    ┌─────────────────────────────┐      │   │
│  │  [uridecodebin:CAM-008] ──┘    │ Primary Inference (PGIE)     │      │   │
│  │                                  │ Model: PeopleNet/YOLOv8     │      │   │
│  │                                  │ Engine: TensorRT FP16       │      │   │
│  │                                  │ Batch: 8, Interval: 2       │      │   │
│  │                                  └─────────────┬───────────────┘      │   │
│  │                                                │                       │   │
│  │                                                ▼                       │   │
│  │                                  ┌─────────────────────────────┐      │   │
│  │                                  │ Tracker (nvtracker)          │      │   │
│  │                                  │ Algorithm: NvDCF             │      │   │
│  │                                  │ Max Targets: 50/source       │      │   │
│  │                                  └─────────────┬───────────────┘      │   │
│  │                                                │                       │   │
│  │                                                ▼                       │   │
│  │                                  ┌─────────────────────────────┐      │   │
│  │                                  │ Secondary Inference (SGIE)   │      │   │
│  │                                  │ Model: ActionRecognitionNet  │      │   │
│  │                                  │ Input: Tracked Objects       │      │   │
│  │                                  └─────────────┬───────────────┘      │   │
│  │                                                │                       │   │
│  │                                                ▼                       │   │
│  │                                  ┌─────────────────────────────┐      │   │
│  │                                  │ Analytics (nvdsanalytics)    │      │   │
│  │                                  │ - ROI: 위험구역 polygon      │      │   │
│  │                                  │ - Dwell: 미움직임 시간 감지   │      │   │
│  │                                  │ - Direction: 궤적 방향 분석   │      │   │
│  │                                  └─────────────┬───────────────┘      │   │
│  │                                                │                       │   │
│  │                                     ┌──────────┼──────────┐           │   │
│  │                                     ▼          ▼          ▼           │   │
│  │                              [nvmsgconv]  [nvdsosd]  [splitmuxsink]   │   │
│  │                                  │            │            │           │   │
│  │                                  ▼            ▼            ▼           │   │
│  │                            [nvmsgbroker]  [Display]  [NVR Clip]       │   │
│  │                            (Redis/MQTT)                               │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 DeepStream 설정 파일 구조

```
services/deepstream-app/
├── configs/
│   ├── deepstream_app_config.yml       # 메인 앱 설정
│   ├── source_list.yml                 # RTSP 소스 목록 (8채널)
│   ├── pgie_config.yml                 # Primary Inference 설정
│   ├── sgie_action_config.yml          # Secondary Inference (행동 분석)
│   ├── tracker_config.yml              # NvDCF Tracker 설정
│   ├── analytics_config.yml            # ROI, Dwell, Direction 규칙
│   ├── msgconv_config.yml              # 메시지 변환 (JSON 스키마)
│   └── msgbroker_config.yml            # Redis/MQTT 브로커 연결
├── models/
│   ├── peoplenet/
│   │   ├── resnet34_peoplenet_fp16.engine
│   │   └── labels.txt
│   └── action_recognition/
│       ├── action_recognition_fp16.engine
│       └── labels.txt
└── roi/
    ├── CAM-001_roi.yml                 # 카메라별 위험구역 polygon
    ├── CAM-002_roi.yml
    └── ...
```


### 2.3 Primary Inference (PGIE) 설계

| 항목 | 설정 |
|------|------|
| **모델** | PeopleNet (TAO pretrained) 또는 YOLOv8-safety |
| **엔진** | TensorRT FP16 (.engine) |
| **입력** | 960×544 (PeopleNet) 또는 640×640 (YOLO) |
| **배치** | 8 (8채널 동시) |
| **interval** | 2 (매 2프레임마다 추론, 실효 7.5fps) |
| **출력** | class_id, confidence, bbox, source_id |
| **클래스** | person, bag (PeopleNet) / person, hazard (YOLO) |
| **threshold** | 0.7 (설정 파일로 조정 가능) |

### 2.4 Secondary Inference (SGIE) 설계

| 항목 | 설정 |
|------|------|
| **모델** | ActionRecognitionNet (TAO pretrained) |
| **입력** | Primary에서 감지된 person 객체의 크롭 이미지 |
| **출력** | action_class (normal/fall/collapse/stillness) |
| **threshold** | 0.65 (행동별 개별 설정 가능) |
| **적용 조건** | person confidence ≥ 0.7인 객체만 |

### 2.5 Tracker (nvtracker) 설계

| 항목 | 설정 |
|------|------|
| **알고리즘** | NvDCF (NVIDIA DCF Tracker) |
| **최대 추적 대상** | 50/source (400 total) |
| **재식별** | 외형 특징 기반 ReID (Platform 2.0 확장) |
| **궤적 유지** | 60초 (이후 ID 해제) |
| **출력** | tracking_id, 위치, 속도, 궤적 history |

### 2.6 Analytics (nvdsanalytics) 설계

| 분석 유형 | 규칙 | 이벤트 |
|-----------|------|--------|
| **ROI 침입** | polygon 내 person 진입 | ZONE_INTRUSION (CRITICAL) |
| **Dwell Time** | 동일 위치 30초 이상 체류 | STILLNESS_DETECTED (WARNING) |
| **Direction** | 금지 방향 이동 감지 | WRONG_DIRECTION (WARNING) |
| **Overcounting** | ROI 내 동시 인원 초과 | OVERCROWDING (WARNING) |

---

## 3. TAO Toolkit 학습 워크플로우 설계

### 3.1 학습 파이프라인 구조

```
┌─────────────────────────────────────────────────────────────────┐
│              TAO Training Pipeline (학습·최적화 서버)              │
│                                                                  │
│  ┌────────────┐    ┌────────────┐    ┌────────────┐            │
│  │ Data       │    │ TAO        │    │ Validation │            │
│  │ Collection │ →  │ Training   │ →  │ & Metrics  │            │
│  │            │    │            │    │            │            │
│  │ - NVR영상  │    │ - train    │    │ - evaluate │            │
│  │ - 이벤트클립│    │ - prune    │    │ - compare  │            │
│  │ - 라벨링   │    │ - retrain  │    │ - report   │            │
│  └────────────┘    └────────────┘    └─────┬──────┘            │
│                                             │                    │
│                                             ▼                    │
│                    ┌────────────┐    ┌────────────┐            │
│                    │ Deploy     │ ←  │ Export &   │            │
│                    │ to Edge    │    │ Optimize   │            │
│                    │            │    │            │            │
│                    │ - hot-swap │    │ - export   │            │
│                    │ - verify   │    │ - trtexec  │            │
│                    │ - rollback │    │ - INT8 cal │            │
│                    └────────────┘    └────────────┘            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 TAO 모델 학습 설정

#### 3.2.1 PeopleNet Fine-tuning (Platform 1.0)

```yaml
# tao_train_spec.yaml
model:
  pretrained_model: "peoplenet_vunpruned_v2.6.2"
  arch: "detectnet_v2"
  backbone: "resnet34"

training:
  epochs: 80
  batch_size: 16
  learning_rate: 0.001
  lr_scheduler: "cosine"
  augmentation:
    horizontal_flip: true
    color_jitter: 0.3
    random_crop: true

dataset:
  format: "kitti"
  train_split: 0.8
  val_split: 0.1
  test_split: 0.1
  classes: ["person", "person_fallen", "person_still"]

export:
  precision: "fp16"
  target: "deepstream"
  input_dims: [3, 544, 960]
```

#### 3.2.2 ActionRecognitionNet Fine-tuning (Platform 2.0 준비)

```yaml
model:
  pretrained_model: "actionrecognitionnet_v1.0"
  arch: "action_recognition"

training:
  epochs: 50
  sequence_length: 16  # 16 frames per clip
  batch_size: 8
  classes: ["normal", "fall", "collapse", "stillness", "hazardous_action"]
```

### 3.3 모델 버전 관리 체계

| 항목 | 형식 | 예시 |
|------|------|------|
| 버전 | `v{major}.{minor}.{patch}-{tool}-{target}` | `v1.2.0-tao-ds` |
| tool | tao (TAO 학습) / pretrained (사전학습 그대로) | - |
| target | ds (DeepStream) / cloud (클라우드 평가용) | - |
| 파일명 | `{model_type}_{version}_{precision}.engine` | `peoplenet_v1.2.0-tao-ds_fp16.engine` |


---

## 4. 이벤트 처리 설계

### 4.1 이벤트 흐름

```
[DeepStream nvmsgconv]                    [MQTT: 센서/밴드]
        │                                         │
        ▼                                         ▼
┌──────────────────────────────────────────────────────┐
│              Event Processor Service                   │
│                                                       │
│  [Redis Stream: stream:ds-events]  [stream:sensors]  │
│              │                           │            │
│              └─────────┬─────────────────┘            │
│                        ▼                              │
│              [Risk Classifier]                        │
│              (YAML rules engine)                      │
│                        │                              │
│         ┌──────────────┼──────────────┐              │
│         ▼              ▼              ▼              │
│   [stream:alarms] [stream:dashboard] [stream:cloud]  │
│                                                       │
└──────────────────────────────────────────────────────┘
```

### 4.2 DeepStream 이벤트 JSON 스키마

```json
{
  "event_id": "EVT-20250519120000-001",
  "site_id": "SITE-001",
  "source_id": 0,
  "device_id": "CAM-001",
  "event_type": "FALL_DETECTED",
  "risk_level": "CRITICAL",
  "timestamp": "2025-05-19T12:00:00.123Z",
  "model_version": "v1.0.0-tao-ds",
  "inference": {
    "primary": {
      "class": "person",
      "confidence": 0.95,
      "bbox": {"x": 120, "y": 80, "w": 180, "h": 370}
    },
    "secondary": {
      "class": "fall",
      "confidence": 0.88
    },
    "tracker": {
      "tracking_id": 42,
      "age_frames": 150,
      "velocity": {"vx": 0.0, "vy": 2.1}
    }
  },
  "analytics": {
    "roi_name": "작업장A-기계구역",
    "dwell_time_sec": 0.0,
    "in_roi": true
  },
  "worker_id": "WKR-0002",
  "clip_path": "/clips/EVT-20250519120000-001.mp4"
}
```

### 4.3 위험등급 판정 규칙 (YAML)

```yaml
# risk_classification_rules.yaml
classification:
  CRITICAL:
    conditions:
      - event_type: "FALL_DETECTED"
        min_confidence: 0.70
      - event_type: "COLLAPSE_DETECTED"
        min_confidence: 0.70
      - event_type: "ZONE_INTRUSION"
        min_confidence: 0.75
      - event_type: "FIRE_DETECTED"
        source: "contact"
      - event_type: "HEARTRATE_ABNORMAL"
        source: "band"
    alarm_actions: ["SIREN_ON", "LIGHT_ON"]
    routes: ["alarm", "dashboard", "cloud", "nvr_clip"]

  WARNING:
    conditions:
      - event_type: "STILLNESS_DETECTED"
        dwell_time_min_sec: 30
      - event_type: "ENV_THRESHOLD_EXCEEDED"
      - event_type: "TEMPERATURE_ABNORMAL"
      - event_type: "HAZARDOUS_ACTION"
        min_confidence: 0.65
    alarm_actions: ["LIGHT_ON"]
    routes: ["alarm", "dashboard", "cloud"]

  NORMAL:
    conditions:
      - event_type: "NORMAL_RESTORED"
      - event_type: "DEVICE_ONLINE"
    alarm_actions: []
    routes: ["cloud", "log"]

deduplication:
  window_seconds: 10
  key: ["device_id", "event_type", "tracking_id"]
```

---

## 5. 서비스 간 통신 설계

### 5.1 Redis Streams

| Stream | Publisher | Subscriber | 데이터 |
|--------|-----------|------------|--------|
| `stream:ds-events` | DeepStream (nvmsgbroker) | Event Processor | AI 감지 이벤트 |
| `stream:sensors` | Sensor Service (MQTT→Redis) | Event Processor | 환경/밴드/화재 |
| `stream:alarms` | Event Processor | Alarm Controller | 알람 명령 |
| `stream:dashboard` | Event Processor | Dashboard Backend | 실시간 표시 |
| `stream:cloud-queue` | Event Processor | Cloud Sync | 클라우드 전송 큐 |

### 5.2 MQTT 토픽

| 토픽 | Publisher | 데이터 |
|------|-----------|--------|
| `safety/{site_id}/band/{device_id}/#` | 스마트밴드 Gateway | 심박, 체온, 가속도, 위치 |
| `safety/{site_id}/env/{device_id}/data` | 환경센서 | 온도, 습도, CO, VOC |
| `safety/{site_id}/ds/status` | DeepStream App | 파이프라인 상태 |

### 5.3 REST API 엔드포인트 요약

| 서비스 | Port | 주요 API |
|--------|------|----------|
| DeepStream Manager | 8001 | /health, /pipeline/status, /sources, /models |
| Event Processor | 8003 | /health, /events, /events/{id}/acknowledge, /rules |
| Alarm Controller | 8004 | /health, /alarm/status, /alarm/trigger, /alarm/clear |
| Cloud Sync | 8005 | /health, /sync/status, /sync/queue, /sync/flush |
| Dashboard Backend | 8080 | /health, /auth, /dashboard, /events, /system |
| TAO Manager | 8006 | /health, /pipeline/status, /datasets, /training, /deploy |

---

## 6. 배포 설계

### 6.1 Docker Compose 구성 (Edge AI 서버)

```yaml
services:
  deepstream-app:
    image: nvcr.io/nvidia/deepstream:7.0-triton-multiarch
    runtime: nvidia
    volumes:
      - ./configs:/app/configs
      - ./models:/app/models
      - ./clips:/app/clips
    network_mode: host  # RTSP 성능 최적화
    restart: always

  event-processor:
    build: ./services/event-processor
    depends_on: [redis]
    restart: always

  alarm-controller:
    build: ./services/alarm-controller
    privileged: true  # GPIO
    depends_on: [redis]
    restart: always

  cloud-sync:
    build: ./services/cloud-sync
    depends_on: [redis]
    volumes: [./certs:/certs:ro]
    restart: always

  dashboard-backend:
    build: ./apps/dashboard-backend
    ports: ["8080:8080"]
    depends_on: [redis]
    restart: always

  sensor-service:
    build: ./services/sensor-service
    depends_on: [redis, mosquitto]
    restart: always

  redis:
    image: redis:7-alpine
    restart: always

  mosquitto:
    image: eclipse-mosquitto:2
    ports: ["1883:1883"]
    restart: always
```

### 6.2 학습·최적화 서버 배포

```yaml
services:
  tao-toolkit:
    image: nvcr.io/nvidia/tao/tao-toolkit:5.3.0-pyt
    runtime: nvidia
    volumes:
      - ./data:/data
      - ./models:/models
      - ./specs:/specs
    shm_size: "16g"

  tao-manager:
    build: ./services/tao-manager
    depends_on: [redis]
    ports: ["8006:8006"]
    restart: always

  label-tool:
    image: cvat/cvat:latest  # or custom labeling UI
    ports: ["8888:8888"]
```

---

## 7. 모델 배포 (Edge 배포 경로)

### 7.1 배포 프로세스

```
[학습 서버: TAO train 완료]
    → [TAO export → .etlt / .onnx]
    → [trtexec → .engine (FP16/INT8)]
    → [DeepStream 모델 디렉토리에 복사 (NFS/SCP)]
    → [DeepStream Manager API: /models/{id}/reload]
    → [nvinfer 모델 핫스왑 (파이프라인 유지)]
    → [Post-deploy 검증: 10프레임 추론 정확도 확인]
    → [실패 시 자동 롤백 (이전 .engine 복원)]
    → [성공 시 model_version 업데이트 + 클라우드 동기화]
```

### 7.2 모델 저장 경로

```
/models/
├── active/                  # 현재 DeepStream이 사용 중인 모델
│   ├── pgie/
│   │   ├── model.engine
│   │   ├── labels.txt
│   │   └── config.yml
│   └── sgie_action/
│       ├── model.engine
│       └── labels.txt
├── staged/                  # 배포 대기 중인 새 모델
│   └── ...
├── rollback/                # 롤백용 이전 모델
│   └── ...
└── registry.json            # 로컬 모델 버전 레지스트리
```

---

## 8. 데이터 모델

### 8.1 이벤트 저장 스키마 (PostgreSQL)

```sql
CREATE TABLE events (
    event_id        VARCHAR(30) PRIMARY KEY,
    site_id         VARCHAR(10) NOT NULL,
    device_id       VARCHAR(10) NOT NULL,
    worker_id       VARCHAR(10),
    event_type      VARCHAR(30) NOT NULL,
    risk_level      VARCHAR(10) NOT NULL,
    confidence      FLOAT,
    model_version   VARCHAR(30),
    timestamp       TIMESTAMPTZ NOT NULL,
    payload         JSONB,
    clip_path       VARCHAR(255),
    state           VARCHAR(15) DEFAULT 'ACTIVE',
    acknowledged_by VARCHAR(30),
    acknowledged_at TIMESTAMPTZ,
    ack_reason      TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_events_timestamp ON events (timestamp DESC);
CREATE INDEX idx_events_risk ON events (risk_level, state);
CREATE INDEX idx_events_site ON events (site_id, timestamp DESC);
```

### 8.2 모델 레지스트리 스키마

```sql
CREATE TABLE model_registry (
    model_version   VARCHAR(30) PRIMARY KEY,
    model_type      VARCHAR(30) NOT NULL,
    trained_at      TIMESTAMPTZ,
    site_id         VARCHAR(10),
    tool            VARCHAR(10),  -- 'tao' | 'pretrained'
    precision       VARCHAR(5),   -- 'fp16' | 'int8'
    metrics         JSONB,
    file_path       VARCHAR(255),
    file_size_mb    FLOAT,
    deployed_to     VARCHAR(30)[],
    status          VARCHAR(10) DEFAULT 'staged',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 변경 이력

| 버전 | 일자 | 내용 |
|------|------|------|
| 0.1 | 2025-05-19 | NVIDIA DeepStream/TAO 기반 시스템 상세 설계 초안 |
