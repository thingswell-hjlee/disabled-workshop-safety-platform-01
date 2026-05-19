# Platform 1.0 Architecture

## 1. 아키텍처 목표

Platform 1.0은 **센서 → AI 판단 → 알람**의 End-to-End 파이프라인을 안정적으로 동작시키는 것을 목표로 한다.

### 1.1 설계 제약

- Edge AI 서버 1대로 모든 추론 처리
- 학습·최적화 서버 1대로 모델 개선
- 단일 현장 (site_id: SITE-001)
- AWS 클라우드 최소 구성

### 1.2 확장 대비 설계

- 모든 데이터에 site_id 포함 (다중 현장 대비)
- 서비스 간 메시지 기반 통신 (마이크로서비스 전환 대비)
- API 버전 관리 (/api/v1/)
- 설정 외부화 (YAML/JSON config)

## 2. 서비스 구성도

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Edge AI Server                                    │
│                                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │ Device       │  │ AI Inference │  │ Event        │  │ Alarm      │ │
│  │ Gateway      │→ │ Engine       │→ │ Processor    │→ │ Controller │ │
│  │ Service      │  │ Service      │  │ Service      │  │ Service    │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └────────────┘ │
│         │                  │                 │                          │
│         ▼                  ▼                 ▼                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                    Redis (Message Broker + Queue)                  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│         │                  │                 │                          │
│         ▼                  ▼                 ▼                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                 │
│  │ Cloud Sync   │  │ NVR          │  │ Dashboard    │                 │
│  │ Service      │  │ Service      │  │ Backend      │                 │
│  └──────────────┘  └──────────────┘  └──────────────┘                 │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                      Training Server                                     │
│                                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                 │
│  │ Data         │  │ Training     │  │ Model        │                 │
│  │ Collector    │→ │ Pipeline     │→ │ Optimizer    │                 │
│  └──────────────┘  └──────────────┘  └──────────────┘                 │
│                                              │                          │
│                                              ▼                          │
│                                       ┌──────────────┐                 │
│                                       │ Deployer     │                 │
│                                       │ Service      │                 │
│                                       └──────────────┘                 │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## 3. 서비스 상세

### 3.1 Device Gateway Service

| 항목 | 내용 |
|------|------|
| **역할** | 모든 장비로부터 데이터 수신 및 정규화 |
| **입력** | RTSP (Camera), MQTT (Sensor/Band), GPIO (Fire) |
| **출력** | Redis Stream (정규화된 센서 데이터, 영상 프레임) |
| **기술** | Python, OpenCV, paho-mqtt, pyserial |

### 3.2 AI Inference Engine Service

| 항목 | 내용 |
|------|------|
| **역할** | 영상·센서·바이오 데이터 기반 위험 감지 |
| **입력** | Redis Stream (프레임, 센서 데이터) |
| **출력** | Redis Stream (이벤트: 감지 결과 + confidence + 등급) |
| **기술** | TensorRT, ONNX Runtime, Python |
| **모델** | YOLOv8 (객체감지), Custom (낙상/이상행동) |

### 3.3 Event Processor Service

| 항목 | 내용 |
|------|------|
| **역할** | 이벤트 수신, 위험등급 판정, 라우팅 |
| **입력** | Redis Stream (AI 감지 이벤트) |
| **출력** | 알람 트리거, 이벤트 저장, 클라우드 전송 큐 |
| **기술** | Python, Rule Engine (YAML config) |

### 3.4 Alarm Controller Service

| 항목 | 내용 |
|------|------|
| **역할** | 접점 출력 제어 (사이렌, 경광등) |
| **입력** | Redis Stream (알람 명령) |
| **출력** | GPIO/Relay 제어 신호 |
| **기술** | Python, RPi.GPIO / pyserial |

### 3.5 Cloud Sync Service

| 항목 | 내용 |
|------|------|
| **역할** | 이벤트·상태 데이터 클라우드 전송 |
| **입력** | Redis Queue (이벤트 데이터) |
| **출력** | AWS IoT Core (MQTT over TLS) |
| **장애 대응** | 네트워크 장애 시 로컬 큐잉, 복구 시 자동 재전송 |

### 3.6 Dashboard Backend

| 항목 | 내용 |
|------|------|
| **역할** | REST API + WebSocket 실시간 데이터 제공 |
| **입력** | Redis Stream (실시간), PostgreSQL (이력) |
| **출력** | HTTP/WebSocket → Dashboard UI |
| **기술** | FastAPI, WebSocket, JWT Auth |

## 4. 통신 프로토콜

### 4.1 내부 통신 (Redis Streams)

| Stream | Publisher | Subscriber | 데이터 |
|--------|-----------|------------|--------|
| `stream:frames:{device_id}` | Device Gateway | AI Inference | 영상 프레임 |
| `stream:sensors` | Device Gateway | AI Inference | 센서 데이터 |
| `stream:bio` | Device Gateway | AI Inference | 바이오 데이터 |
| `stream:events` | AI Inference | Event Processor | 감지 이벤트 |
| `stream:alarms` | Event Processor | Alarm Controller | 알람 명령 |
| `stream:cloud_queue` | Event Processor | Cloud Sync | 클라우드 전송 큐 |
| `stream:dashboard` | Event Processor | Dashboard Backend | 실시간 표시 |

### 4.2 외부 통신

| 경로 | 프로토콜 | 인증 | 용도 |
|------|----------|------|------|
| Edge → AWS IoT | MQTT over TLS | X.509 인증서 | 이벤트 전송 |
| Edge → AWS S3 | HTTPS | IAM Role | 모델·클립 업로드 |
| Browser → Dashboard | HTTPS + WSS | JWT | 대시보드 접근 |

## 5. 배포 구성 (Docker Compose)

```yaml
# Edge AI Server
services:
  device-gateway:
    image: safety-platform/device-gateway:1.0
    restart: always
    devices: ["/dev/video0", "/dev/ttyUSB0"]
    
  ai-inference:
    image: safety-platform/ai-inference:1.0
    restart: always
    deploy:
      resources:
        reservations:
          devices:
            - capabilities: [gpu]
    
  event-processor:
    image: safety-platform/event-processor:1.0
    restart: always
    
  alarm-controller:
    image: safety-platform/alarm-controller:1.0
    restart: always
    privileged: true
    
  cloud-sync:
    image: safety-platform/cloud-sync:1.0
    restart: always
    
  dashboard-backend:
    image: safety-platform/dashboard-backend:1.0
    restart: always
    ports: ["8080:8080"]
    
  dashboard-ui:
    image: safety-platform/dashboard-ui:1.0
    restart: always
    ports: ["443:443"]
    
  redis:
    image: redis:7-alpine
    restart: always
    
  mosquitto:
    image: eclipse-mosquitto:2
    restart: always
```

## 6. 장애 대응 매트릭스

| 장애 유형 | 영향 | 대응 |
|-----------|------|------|
| 인터넷 끊김 | 클라우드 동기화 중단 | 로컬 큐잉 → 자동 복구 |
| 카메라 1대 장애 | 해당 채널 추론 중단 | 나머지 7채널 정상 운영 |
| Redis 장애 | 내부 통신 중단 | systemd 자동 재시작, 이벤트 로컬 파일 백업 |
| GPU 장애 | 영상 AI 추론 불가 | 센서·바이오 기반 판단 유지, 알람 동작 |
| Edge 서버 전체 장애 | 전 기능 중단 | UPS 전원, watchdog 자동 재시작 |

---

*참조: [system-overview.md](./system-overview.md) | [device-ai-server-flow.md](./device-ai-server-flow.md)*
