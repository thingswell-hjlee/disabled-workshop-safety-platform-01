# System Overview - 장애인직업재활시설 스마트안전시스템

## 1. 시스템 개요

AI 기반 장애인직업재활시설 스마트안전시스템은 현장 작업자의 안전을 실시간으로 감지·판단·알림하는 통합 안전 플랫폼이다.

### 1.1 핵심 가치

- **생명 보호**: 위험 상황 즉시 감지 및 알람
- **현장 독립**: 네트워크 장애 시에도 로컬 안전 기능 보장
- **지능 진화**: 현장 데이터 기반 AI 모델 지속 개선
- **확장 가능**: 다중 현장, SaaS 전환 대비 설계

### 1.2 시스템 계층 구조

```
┌─────────────────────────────────────────────────┐
│              Presentation Layer                   │
│         (관리자 대시보드 - Web)                    │
├─────────────────────────────────────────────────┤
│              Application Layer                    │
│    (API Gateway, Event Processing, Auth)         │
├─────────────────────────────────────────────────┤
│              AI/ML Layer                          │
│  (Edge Inference, Training, Model Management)    │
├─────────────────────────────────────────────────┤
│              Data Layer                           │
│  (Event Store, Time-series DB, Model Registry)   │
├─────────────────────────────────────────────────┤
│              Device Layer                         │
│  (Camera, Band, Sensor, Fire, NVR, Alarm)        │
└─────────────────────────────────────────────────┘
```

## 2. 주요 서브시스템

| 서브시스템 | 위치 | 역할 |
|-----------|------|------|
| Device Gateway | Edge | 장비 연동, 데이터 수집, 프로토콜 변환 |
| AI Inference Engine | Edge | 실시간 위험 감지·판단·분류 |
| Alarm Controller | Edge | 접점 제어, 현장 경보 발동 |
| Training Pipeline | Local Server | 데이터 수집·가공·학습·최적화 |
| Cloud Sync | Edge → Cloud | 이벤트 전송, 모델 동기화 |
| Dashboard API | Cloud | REST/WebSocket API 서비스 |
| Dashboard UI | Cloud | 실시간 모니터링 웹 인터페이스 |
| Model Registry | Cloud | 모델 버전 관리, 배포 제어 |

## 3. 데이터 흐름 개요

### 3.1 실시간 안전 감지 흐름 (Critical Path)

```
[센서/카메라/밴드] → [Device Gateway] → [AI Inference Engine] → [Risk Classifier]
                                                                      │
                                              ┌───────────────────────┼────────────┐
                                              ▼                       ▼            ▼
                                       [Alarm Controller]    [Event Store]   [Dashboard]
                                              │
                                              ▼
                                       [사이렌/경광등]
```

### 3.2 모델 개선 흐름

```
[AI Inference Results] → [Data Collector] → [Training Pipeline] → [Model Optimizer]
                                                                        │
                                                                        ▼
                                                               [Edge AI Deployment]
                                                                        │
                                                                        ▼
                                                               [Cloud Registry Sync]
```

### 3.3 클라우드 동기화 흐름

```
[Edge Event Store] ──(정상)──→ [Cloud Event Store] → [Dashboard API] → [원격 대시보드]
                   ──(장애)──→ [Local Redis Queue] ──(복구)──→ [Cloud Sync]
```

## 4. 네트워크 토폴로지

### 4.1 현장 네트워크 (On-Premise)

```
                    ┌─── [Internet Gateway] ───── AWS Cloud
                    │
              [L2/L3 Switch]
                    │
     ┌──────────────┼──────────────┐
     │              │              │
[Edge AI Server] [Train Server] [NVR]
     │
     ├── [Camera VLAN] ── CAM-001 ~ CAM-008
     ├── [Sensor VLAN] ── ENV-001, ENV-002, FIRE-001
     ├── [Band AP] ── BAND-001 ~ BAND-008
     └── [Alarm] ── ALARM-001
```

### 4.2 VLAN 분리 설계

| VLAN | 용도 | 대역 |
|------|------|------|
| VLAN 10 | 카메라 | 192.168.10.0/24 |
| VLAN 20 | 센서/밴드 | 192.168.20.0/24 |
| VLAN 30 | 서버 간 통신 | 192.168.30.0/24 |
| VLAN 40 | 관리/인터넷 | 192.168.40.0/24 |

## 5. 핵심 설계 원칙

| 원칙 | 적용 |
|------|------|
| **Fail-Safe** | 네트워크 장애 시 로컬 안전 기능 100% 유지 |
| **Loose Coupling** | 서비스 간 MQTT/Redis 기반 비동기 통신 |
| **Event-Driven** | 모든 상태 변경을 이벤트로 기록 |
| **Config-Driven** | 임계치, 규칙, 장비 설정을 외부화 |
| **Observable** | 모든 서비스에 헬스체크, 메트릭, 구조화 로그 |
| **Containerized** | Docker 기반 일관된 배포 |

## 6. 기술 스택 요약

| 계층 | 기술 |
|------|------|
| Device Protocol | RTSP, MQTT, BLE/Wi-Fi, GPIO/RS-485 |
| Edge Runtime | Python 3.11, TensorRT, ONNX Runtime |
| Message Broker | Mosquitto (MQTT), Redis Streams |
| Local Storage | Redis, SQLite (이벤트 큐), NFS (학습 데이터) |
| Cloud Compute | AWS ECS/Lambda |
| Cloud Storage | S3, RDS (PostgreSQL), DynamoDB |
| Frontend | React, Next.js, WebSocket |
| Backend API | FastAPI (Python) |
| Container | Docker, Docker Compose |
| CI/CD | GitHub Actions |

---

*참조: [platform-1.0-architecture.md](./platform-1.0-architecture.md) | [device-ai-server-flow.md](./device-ai-server-flow.md)*
