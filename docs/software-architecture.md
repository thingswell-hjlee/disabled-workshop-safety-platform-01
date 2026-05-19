# Platform 1.0 소프트웨어 아키텍처 (Software Architecture)

> **참조:** docs/design.md | .kiro/specs/requirements.md
> **범위:** Platform 1.0 전체 소프트웨어 모듈 구조
> **원칙:** 모듈 간 Redis Streams 기반 loose coupling, Docker 컨테이너 배포

---

## 1. 전체 소프트웨어 모듈 구조

### 1.1 모듈 의존성 다이어그램

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Edge AI Server                                    │
│                                                                          │
│  ┌──────────────────┐     ┌──────────────────┐                          │
│  │ deepstream-       │     │ device-gateway-   │                          │
│  │ pipeline-service  │     │ service           │                          │
│  │ (GPU, :8001)      │     │ (:8002)           │                          │
│  └────────┬──────────┘     └────────┬──────────┘                          │
│           │ stream:ds-events         │ stream:sensors                     │
│           └────────────┬─────────────┘                                    │
│                        ▼                                                  │
│  ┌──────────────────────────────────────┐                                │
│  │ event-engine-service (:8003)          │                                │
│  │ - 위험등급 판정, 중복억제, 라우팅     │                                │
│  └──┬──────────┬──────────┬─────────────┘                                │
│     │          │          │                                              │
│     ▼          ▼          ▼                                              │
│  ┌────────┐ ┌────────┐ ┌────────────┐  ┌──────────────────┐            │
│  │alarm-  │ │rolling-│ │aws-sync-   │  │ dashboard-       │            │
│  │control │ │buffer- │ │agent       │  │ backend (:8080)  │            │
│  │(:8004) │ │service │ │(:8005)     │  │                  │            │
│  └────────┘ └────────┘ └────────────┘  └────────┬─────────┘            │
│       │          │                               │                       │
│       ▼          ▼                               ▼                       │
│  [GPIO Out] [local-storage-service]     [dashboard-frontend (:3000)]    │
│                                                                          │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐      │
│  │ config-mgmt-     │  │ logging-monitor- │  │ inference-       │      │
│  │ service          │  │ service          │  │ service (GPU)    │      │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘      │
│                                                                          │
│  Infrastructure: [Redis 7] [Mosquitto MQTT] [SQLite/PostgreSQL]          │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                      Training Server                                      │
│                                                                          │
│  ┌──────────────────┐  ┌──────────────────┐                            │
│  │ local-training-  │  │ model-management-│                            │
│  │ service (GPU)    │  │ service          │                            │
│  └──────────────────┘  └──────────────────┘                            │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.2 모듈 목록 요약 (16개)

| # | 모듈명 | 위치 | GPU | Port | 핵심 역할 |
|---|--------|------|-----|------|-----------|
| 1 | edge-ai-service | Edge | - | - | 전체 오케스트레이션 (Docker Compose) |
| 2 | deepstream-pipeline-service | Edge | ✅ | 8001 | 8채널 RTSP 수집·추론·추적·분석·이벤트 |
| 3 | inference-service | Edge | ✅ | - | TensorRT 엔진 관리, 모델 핫스왑 |
| 4 | device-gateway-service | Edge | ❌ | 8002 | 밴드·센서·화재 데이터 수집 |
| 5 | event-engine-service | Edge | ❌ | 8003 | 위험등급 판정, 중복억제, 라우팅 |
| 6 | rolling-buffer-service | Edge | ❌ | - | 영상 버퍼 관리, 이벤트 클립 추출 |
| 7 | alarm-control-service | Edge | ❌ | 8004 | GPIO 사이렌/경광등 제어 |
| 8 | local-storage-service | Edge | ❌ | - | 이벤트·클립·로그 로컬 저장 |
| 9 | aws-sync-agent | Edge | ❌ | 8005 | AWS IoT/S3 동기화, 오프라인 큐잉 |
| 10 | dashboard-backend | Edge | ❌ | 8080 | REST API + WebSocket |
| 11 | dashboard-frontend | Edge | ❌ | 3000 | React/Next.js 관리 UI |
| 12 | local-training-service | Train | ✅ | 8006 | TAO 학습·검증·최적화 |
| 13 | model-management-service | Train | ❌ | 8007 | 모델 버전·배포·롤백 관리 |
| 14 | config-management-service | Edge | ❌ | - | 설정 파일 로드, Hot-reload |
| 15 | logging-monitoring-service | Edge | ❌ | - | 구조화 로그, 메트릭 수집, 헬스체크 |
| 16 | edge-ai-service (orchestrator) | Edge | - | - | systemd + Docker Compose 관리 |



---

## 2. edge-ai-service (오케스트레이터)

### 역할
- Docker Compose 기반 전체 서비스 라이프사이클 관리
- systemd 연동 (부팅 시 자동 시작, watchdog)
- 서비스 간 의존성 관리 (redis → deepstream → event-engine → ...)

### 구성 파일
```
edge-ai-service/
├── docker-compose.yml       # 전 서비스 정의
├── docker-compose.prod.yml  # 프로덕션 오버라이드
├── .env                     # 환경변수 (gitignore)
├── .env.example             # 환경변수 템플릿
└── systemd/
    └── safety-platform.service  # systemd 유닛 파일
```

### 의존성 순서
```
redis, mosquitto → deepstream-pipeline → device-gateway → event-engine
    → alarm-control, rolling-buffer, aws-sync, dashboard-backend
```

---

## 3. deepstream-pipeline-service

### 역할
- IP Camera 8대 RTSP 스트림 동시 수집 (nvstreammux)
- GPU 하드웨어 디코딩 (nvv4l2decoder)
- Primary Inference: 사람 감지 (PeopleNet/YOLOv8, TensorRT FP16)
- Object Tracking: NvDCF 기반 추적 ID 부여
- Secondary Inference: 행동 분석 (낙상/쓰러짐/미움직임)
- Analytics: ROI 위험구역 침입, Dwell Time 감지
- 이벤트 JSON 생성 → Redis Stream 발행
- OSD 시각화 + RTSP 출력 (대시보드용)
- 이벤트 기반 영상 클립 트리거

### 기술 스택
- NVIDIA DeepStream SDK 7.x
- GStreamer 1.x
- TensorRT 8.6+ (nvinfer)
- Redis (nvmsgbroker 커스텀 어댑터)

### 설정 파일
```
deepstream-pipeline-service/
├── configs/
│   ├── deepstream_app_config.yml
│   ├── source_list.yml          # 8채널 RTSP URL
│   ├── pgie_config.yml          # Primary 추론 설정
│   ├── sgie_action_config.yml   # Secondary 추론 설정
│   ├── tracker_config.yml       # NvDCF 설정
│   ├── analytics_config.yml     # 전체 분석 설정
│   ├── msgconv_config.yml       # JSON 변환 스키마
│   └── msgbroker_config.yml     # Redis 연결 정보
├── roi/
│   ├── CAM-001_roi.yml ~ CAM-008_roi.yml
├── models/                      # → /models volume mount
└── Dockerfile
```

### 입출력

| 방향 | 데이터 | 프로토콜 |
|------|--------|----------|
| IN | 8x RTSP 스트림 (1080p@15fps) | RTSP (Camera VLAN) |
| OUT | stream:ds-events (JSON 이벤트) | Redis Streams |
| OUT | RTSP 서버 (OSD 포함 영상) | RTSP (:8554) |
| OUT | 영상 클립 파일 (.mp4) | Local File System |

### API 엔드포인트 (DeepStream Manager)

| Method | Path | 설명 |
|--------|------|------|
| GET | /health | 파이프라인 상태, FPS, GPU |
| GET | /pipeline/sources | 카메라 목록·상태 |
| POST | /pipeline/sources/{id}/reconnect | 카메라 수동 재연결 |
| GET | /models | 로드된 모델 목록 |
| POST | /models/{id}/reload | 모델 핫스왑 요청 |
| GET | /analytics/zones | ROI 설정 조회 |
| PUT | /analytics/zones/{cam_id} | ROI 설정 변경 |

---

## 4. inference-service

### 역할
- TensorRT 엔진 파일 관리 (/models/active, staged, rollback)
- 모델 핫스왑 실행: staged → active 전환 + DeepStream reload 트리거
- 배포 후 검증 (10프레임 추론 정확도 확인)
- 실패 시 자동 롤백 (rollback → active 복원)
- 모델 메타데이터 관리 (registry.json)

### 동작 흐름
```
[Model Deploy Request] → [staged/ 에 .engine 배치]
    → [DeepStream nvinfer reload API 호출]
    → [10프레임 검증: confidence 분포 확인]
    → 성공: active/ 갱신, registry.json 업데이트
    → 실패: rollback/ 복원, 알림 발송
```

### 통합
- deepstream-pipeline-service의 `/models/{id}/reload` API 호출
- model-management-service에서 배포 명령 수신

---

## 5. device-gateway-service

### 역할
- 스마트밴드 8개: MQTT 토픽 구독 → 데이터 정규화
- 환경센서 2개: MQTT 토픽 구독 → 임계치 비교 → 이벤트 생성
- 화재감지 접점: GPIO 폴링 (5초) + 인터럽트 → FIRE_DETECTED 즉시 발생
- 바이오 이상 판단: 심박/체온 범위 확인 → 이벤트 생성
- 장비 연결 상태 모니터링 (밴드 30초 미수신 → BAND_DISCONNECTED)

### 입출력

| 방향 | 데이터 | 프로토콜 |
|------|--------|----------|
| IN | 밴드 심박/체온/가속도/위치 | MQTT |
| IN | 환경 온도/습도/CO/VOC | MQTT |
| IN | 화재감지 접점 신호 | GPIO Pin 22 |
| OUT | stream:sensors (정규화 이벤트) | Redis Streams |

### API 엔드포인트

| Method | Path | 설명 |
|--------|------|------|
| GET | /health | 서비스 상태, 연결 장비 수 |
| GET | /devices | 전체 장비 상태 목록 |
| GET | /devices/{id} | 개별 장비 상세 |
| GET | /devices/{id}/data/latest | 최신 데이터 |

---

## 6. event-engine-service

### 역할
- stream:ds-events + stream:sensors 통합 소비
- 이벤트 정규화 (DeepStream/센서 통합 스키마)
- 중복 억제 (10초 윈도우, key: device_id + event_type + tracking_id)
- 위험등급 판정 (YAML 규칙 엔진)
- confidence 필터링 (하향/무시 로직)
- 이벤트 라우팅 (alarms, dashboard, cloud-queue, rolling-buffer 트리거)
- 이벤트 상태 관리 (ACTIVE → ACKNOWLEDGED → ARCHIVED)

### 입출력

| 방향 | Stream | 데이터 |
|------|--------|--------|
| IN | stream:ds-events | DeepStream 감지 이벤트 |
| IN | stream:sensors | 센서/밴드/화재 이벤트 |
| OUT | stream:alarms | 알람 명령 (CRITICAL/WARNING) |
| OUT | stream:dashboard | 대시보드 실시간 표시 |
| OUT | stream:cloud-queue | AWS 전송 큐 |

### API 엔드포인트

| Method | Path | 설명 |
|--------|------|------|
| GET | /health | 처리량, 큐 깊이 |
| GET | /events | 이벤트 목록 (필터) |
| GET | /events/{id} | 이벤트 상세 |
| POST | /events/{id}/acknowledge | 알람 해제 |
| GET | /rules | 판정 규칙 조회 |
| PUT | /rules | 판정 규칙 변경 |

---

## 7. rolling-buffer-service

### 역할
- 채널별 최근 60초 영상 프레임을 메모리 링 버퍼로 유지
- 이벤트 트리거 시 전후 ±30초 클립 추출 → MP4 저장
- local-storage-service에 메타데이터 기록
- aws-sync-agent에 S3 업로드 요청

### Platform 1.0 구현
```
[DeepStream 인코딩 출력] → [Ring Buffer (60초/채널)]
    → [Event Trigger] → [±30초 추출] → [MP4 Mux] → [/clips/ 저장]
```

### 데이터 구조 (RollingBufferSegment)
```json
{
  "segment_id": "SEG-20250519120000-CAM001",
  "device_id": "CAM-001",
  "start_ts": "2025-05-19T11:59:00.000Z",
  "end_ts": "2025-05-19T12:00:00.000Z",
  "duration_sec": 60,
  "quality_level": 0,
  "buffer_duration_sec": 60,
  "status": "active"
}
```

---

## 8. alarm-control-service

### 역할
- stream:alarms 소비 → GPIO 제어 (사이렌 Pin 17, 경광등 Pin 27)
- CRITICAL: 사이렌 + 경광등 동시 ON
- WARNING: 경광등만 ON (5분 자동 해제)
- Acknowledge 수신 시 전체 OFF
- 동작/해제 이력 로깅

### 독립 동작 보장
- Redis 로컬 동작 → 네트워크 장애 무관
- GPIO 직접 제어 → 클라우드 의존성 없음
- event-engine이 로컬에서 판정 → 알람 명령 발행

### API 엔드포인트

| Method | Path | 설명 |
|--------|------|------|
| GET | /health | GPIO 상태 |
| GET | /alarm/status | 현재 알람 상태 |
| POST | /alarm/trigger | 수동 알람 발동 (테스트) |
| POST | /alarm/clear | 수동 해제 |
| POST | /alarm/test | 1초 테스트 동작 |
| GET | /alarm/logs | 동작 이력 |

---

## 9. local-storage-service

### 역할
- 이벤트 데이터 로컬 저장 (SQLite, Platform 2.0: PostgreSQL)
- 영상 클립 파일 관리 (생성, 조회, 삭제, 보관 정책)
- 로컬 이벤트 큐 백업 (Redis 장애 대비)
- 디스크 용량 모니터링 (80% 알림)

### 저장소 구조
```
/data/
├── events.db          # SQLite (이벤트, 장비상태, 모델이력)
├── clips/             # 이벤트 영상 클립
│   └── {YYYY}/{MM}/{DD}/EVT-{id}.mp4
├── queue-backup/      # Redis 장애 시 이벤트 백업
└── logs/              # 구조화 로그 파일
```

---

## 10. aws-sync-agent

### 역할
- stream:cloud-queue 소비 → AWS IoT Core (MQTT over TLS) 전송
- 영상 클립 → AWS S3 Multipart Upload
- 네트워크 장애 감지 → 오프라인 모드 전환 → 로컬 큐잉
- 네트워크 복구 → 큐 Flush (우선순위: CRITICAL > WARNING > NORMAL)
- idempotency key 기반 중복 방지

### 연결 정보
- AWS IoT Endpoint: X.509 인증서 기반
- S3 Bucket: IAM STS 임시 자격 증명
- 토픽: `safety/{site_id}/events`, `safety/{site_id}/status`

### API 엔드포인트

| Method | Path | 설명 |
|--------|------|------|
| GET | /health | 연결 상태, 큐 깊이 |
| GET | /sync/status | 온라인/오프라인 상태 |
| GET | /sync/queue | 대기 큐 현황 |
| POST | /sync/flush | 즉시 전송 시도 |
| POST | /sync/pause | 동기화 일시 중지 |
| POST | /sync/resume | 동기화 재개 |

---

## 11. dashboard-backend

### 역할
- REST API: 이벤트 조회, 장비 상태, 시스템 메트릭, 인증
- WebSocket: 실시간 이벤트 푸시 (≤ 3초 갱신)
- JWT 인증 (access 30분, refresh 7일)
- 계정 관리 (CRUD, 잠금, 타임아웃)

### 기술 스택
- FastAPI + Uvicorn
- python-jose (JWT), passlib (bcrypt)
- Redis (실시간 데이터), SQLite (이력)
- WebSocket (실시간 푸시)

### API 그룹

| 그룹 | Prefix | 설명 |
|------|--------|------|
| Auth | /api/v1/auth/ | 로그인, 갱신, 사용자 정보 |
| Dashboard | /api/v1/dashboard/ | 요약, 장비, 작업자 |
| Events | /api/v1/events/ | 목록, 상세, Acknowledge |
| System | /api/v1/system/ | 헬스, 메트릭, DeepStream 상태 |
| Alarm | /api/v1/alarm/ | 알람 상태, 제어 |
| WebSocket | /ws/dashboard | 실시간 이벤트 스트림 |

---

## 12. dashboard-frontend

### 역할
- 관리자 웹 UI (React/Next.js)
- 8채널 영상 실시간 표시 (RTSP→WebRTC/HLS)
- 이벤트 알림 팝업 (WebSocket)
- 이벤트 로그 조회·필터·Acknowledge
- 시스템 상태 모니터링 (GPU, 장비, 네트워크)
- 반응형 레이아웃 (데스크탑 1920px 기준)

### 기술 스택
- Next.js 14+ (App Router)
- React 18+, TypeScript
- TailwindCSS, shadcn/ui
- WebSocket (실시간), Axios (REST)
- JSMpeg 또는 WebRTC (영상 표시)

### 주요 라우트

| 경로 | 페이지 |
|------|--------|
| /login | 로그인 |
| / | 메인 대시보드 (영상 + 요약) |
| /events | 이벤트 로그 |
| /events/[id] | 이벤트 상세 |
| /system | 시스템 상태 |
| /settings | 설정 (ROI, 임계치) |

---

## 13. local-training-service

### 역할 (학습·최적화 서버)
- TAO Toolkit Docker 컨테이너 실행
- NGC 사전학습 모델 관리 (다운로드, 검증)
- Fine-tuning 파이프라인 실행 (spec 파일 기반)
- 학습 결과 평가 (mAP, Precision, Recall, F1)
- TAO export → TensorRT 엔진 변환
- 데이터 수집·라벨링 보조 도구 연동

### TAO 워크플로우
```
[tao model train]      → 학습 실행
[tao model evaluate]   → 성능 평가
[tao model prune]      → 경량화 (Platform 2.0)
[tao model export]     → ONNX/TensorRT 변환
[trtexec]              → .engine 최종 생성
```

### API 엔드포인트

| Method | Path | 설명 |
|--------|------|------|
| GET | /health | GPU 상태, 파이프라인 상태 |
| GET | /datasets | 데이터셋 목록 |
| POST | /training/jobs | 학습 작업 생성 |
| GET | /training/jobs/{id} | 학습 진행 상태 |
| POST | /models/{version}/export | TensorRT 변환 |
| GET | /models | 학습 완료 모델 목록 |

---

## 14. model-management-service

### 역할 (학습 서버)
- 모델 버전 관리 (v{M}.{m}.{p}-{tool}-{target})
- Edge AI 서버로 모델 배포 (SCP + API 호출)
- 배포 상태 추적 (staged → deploying → active / failed → rollback)
- 클라우드 모델 레지스트리 동기화 (S3 + DynamoDB)
- 배포 이력 관리

### API 엔드포인트

| Method | Path | 설명 |
|--------|------|------|
| GET | /health | 서비스 상태 |
| GET | /models | 모델 목록 (전 버전) |
| GET | /models/{version} | 모델 상세 (메트릭 포함) |
| POST | /deploy/{version} | Edge 배포 시작 |
| GET | /deploy/status | 현재 배포 상태 |
| POST | /deploy/rollback | 이전 버전 롤백 |
| POST | /sync/cloud | 클라우드 동기화 |

---

## 15. config-management-service

### 역할
- 전 서비스 설정 파일 중앙 관리 (YAML)
- 환경변수 치환 (`${VAR:-default}` 패턴)
- 설정 변경 시 관련 서비스에 reload 시그널 발송
- 설정 버전 이력 관리

### 관리 설정 파일 목록

| 설정 파일 | 대상 서비스 | 내용 |
|-----------|-------------|------|
| source_list.yml | deepstream-pipeline | 카메라 RTSP URL |
| pgie_config.yml | deepstream-pipeline | Primary 추론 설정 |
| sgie_action_config.yml | deepstream-pipeline | Secondary 추론 설정 |
| tracker_config.yml | deepstream-pipeline | Tracker 설정 |
| roi/*.yml | deepstream-pipeline | 카메라별 위험구역 |
| thresholds.yml | device-gateway | 센서 임계치 |
| risk_rules.yml | event-engine | 위험등급 규칙 |
| alarm_policy.yml | alarm-control | 알람 정책 |
| aws_config.yml | aws-sync-agent | AWS 연결 정보 |

---

## 16. logging-monitoring-service

### 역할
- 전 서비스 구조화 JSON 로그 수집
- /health 엔드포인트 통합 모니터링
- 시스템 메트릭 수집 (CPU, GPU, RAM, Disk, Redis)
- 이상 감지 시 내부 알림 (SYSTEM_ALERT 이벤트)
- 로그 파일 로테이션 (7일 보관)

### 메트릭 수집 항목

| 메트릭 | 소스 | 주기 | 알림 조건 |
|--------|------|------|-----------|
| DeepStream FPS | deepstream-pipeline /health | 5초 | < 10fps |
| GPU 사용률 | nvidia-smi (NVML) | 5초 | > 90% |
| GPU 메모리 | nvidia-smi | 5초 | > 90% VRAM |
| CPU 사용률 | /proc/stat | 10초 | > 80% |
| RAM 사용률 | /proc/meminfo | 10초 | > 85% |
| 디스크 사용률 | df | 60초 | > 80% |
| Redis 메모리 | INFO memory | 30초 | > 400MB |
| 이벤트 처리량 | event-engine /health | 10초 | - |
| 카메라 상태 | deepstream-pipeline /sources | 10초 | DISCONNECTED |
| 네트워크 상태 | aws-sync /health | 30초 | OFFLINE |

### 로그 형식 (JSON)

```json
{
  "timestamp": "2025-05-19T12:00:00.123Z",
  "level": "INFO",
  "service": "event-engine",
  "site_id": "SITE-001",
  "message": "Event processed",
  "event_id": "EVT-20250519120000-001",
  "risk_level": "CRITICAL",
  "duration_ms": 12
}
```

---

## 모듈 간 통신 매트릭스

| From → To | 프로토콜 | Stream/Topic | 데이터 |
|-----------|----------|--------------|--------|
| deepstream → event-engine | Redis | stream:ds-events | 감지 이벤트 JSON |
| device-gateway → event-engine | Redis | stream:sensors | 센서 이벤트 JSON |
| event-engine → alarm-control | Redis | stream:alarms | 알람 명령 |
| event-engine → dashboard-backend | Redis | stream:dashboard | 실시간 표시 |
| event-engine → aws-sync | Redis | stream:cloud-queue | 전송 큐 |
| event-engine → rolling-buffer | Redis | stream:clip-trigger | 클립 추출 명령 |
| dashboard-backend → Browser | WebSocket | /ws/dashboard | 실시간 푸시 |
| aws-sync → AWS IoT | MQTT/TLS | safety/{site}/events | 이벤트 전송 |
| aws-sync → AWS S3 | HTTPS | PUT object | 영상 클립 |
| model-mgmt → deepstream | HTTP | /models/{id}/reload | 모델 핫스왑 |
| training → model-mgmt | Internal | File + API | 학습 완료 모델 |

---

## 변경 이력

| 버전 | 일자 | 내용 |
|------|------|------|
| 1.0 | 2025-05-19 | Platform 1.0 소프트웨어 아키텍처 초안 (16개 모듈) |
