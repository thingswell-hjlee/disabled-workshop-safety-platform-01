# Device → AI Server 데이터 흐름 상세

## 1. 개요

현장 장비(Device)에서 Edge AI 서버로의 데이터 흐름을 상세히 정의한다.
이 문서는 Device Gateway Service와 AI Inference Engine 간의 인터페이스를 명세한다.

## 2. 장비별 데이터 흐름

### 2.1 IP Camera → AI Server

```
[IP Camera] ──RTSP──→ [Frame Grabber] ──Redis Stream──→ [AI Inference]
                            │
                            ├── 프레임 디코딩 (H.264/H.265)
                            ├── 해상도 정규화 (1920x1080 → 640x640 for inference)
                            ├── 메타데이터 부착 (device_id, timestamp, frame_seq)
                            └── 원본 프레임 → NVR 전달 (녹화용)
```

**데이터 형식:**
```json
{
  "stream": "stream:frames:CAM-001",
  "data": {
    "device_id": "CAM-001",
    "site_id": "SITE-001",
    "timestamp": "2025-05-19T12:00:00.123Z",
    "frame_seq": 12345,
    "resolution": "640x640",
    "encoding": "raw_bgr",
    "frame_ref": "redis_key:frame:CAM-001:12345"
  }
}
```

**처리 파이프라인:**
1. RTSP 연결 및 스트림 수신 (GStreamer/OpenCV)
2. 프레임 디코딩 (GPU 가속: NVDEC)
3. 리사이즈 및 전처리 (추론용 640x640)
4. Redis Stream에 프레임 메타데이터 발행
5. 프레임 바이너리는 Redis Key에 TTL(5s) 저장

### 2.2 스마트밴드 → AI Server

```
[Smart Band] ──BLE──→ [BLE Gateway] ──MQTT──→ [Band Handler] ──Redis Stream──→ [AI Inference]
                                                    │
                                                    ├── 심박수/체온: 5초 주기
                                                    ├── 가속도: 100ms 주기
                                                    └── 위치: 1초 주기
```

**MQTT 토픽 구조:**
```
safety/{site_id}/band/{device_id}/heartrate   → {"bpm": 72, "ts": "..."}
safety/{site_id}/band/{device_id}/temperature → {"celsius": 36.5, "ts": "..."}
safety/{site_id}/band/{device_id}/accel       → {"x": 0.1, "y": 9.8, "z": 0.2, "ts": "..."}
safety/{site_id}/band/{device_id}/location    → {"x": 12.5, "y": 8.3, "zone": "A", "ts": "..."}
```

**Redis Stream 정규화 데이터:**
```json
{
  "stream": "stream:bio",
  "data": {
    "device_id": "BAND-001",
    "worker_id": "WKR-0001",
    "site_id": "SITE-001",
    "timestamp": "2025-05-19T12:00:00.000Z",
    "data_type": "heartrate",
    "value": {"bpm": 72},
    "battery_level": 85
  }
}
```

### 2.3 환경센서 → AI Server

```
[Env Sensor] ──MQTT──→ [Sensor Handler] ──Redis Stream──→ [AI Inference]
                              │
                              ├── 온도/습도: 10초 주기
                              ├── CO/VOC: 10초 주기
                              └── 이상값 사전 필터링
```

**MQTT 토픽 구조:**
```
safety/{site_id}/env/{device_id}/data → {
  "temperature": 25.3,
  "humidity": 45.2,
  "co_ppm": 2.1,
  "voc_ppb": 120,
  "ts": "2025-05-19T12:00:00.000Z"
}
```

**Redis Stream 정규화 데이터:**
```json
{
  "stream": "stream:sensors",
  "data": {
    "device_id": "ENV-001",
    "site_id": "SITE-001",
    "zone": "작업장A",
    "timestamp": "2025-05-19T12:00:00.000Z",
    "temperature": 25.3,
    "humidity": 45.2,
    "co_ppm": 2.1,
    "voc_ppb": 120
  }
}
```

### 2.4 화재감지 접점 → AI Server

```
[Fire Detector] ──GPIO/RS-485──→ [Fire Handler] ──Redis Stream──→ [Event Processor]
                                       │                                  │
                                       ├── 폴링: 5초 주기                  ├── 즉시 CRITICAL
                                       ├── 디바운싱: 500ms                 └── 알람 직접 트리거
                                       └── 인터럽트 모드 지원
```

**Redis Stream 데이터:**
```json
{
  "stream": "stream:sensors",
  "data": {
    "device_id": "FIRE-001",
    "site_id": "SITE-001",
    "timestamp": "2025-05-19T12:00:00.000Z",
    "sensor_type": "fire_contact",
    "status": "DETECTED",
    "raw_signal": 1
  }
}
```

> **주의**: 화재 감지는 AI 추론을 거치지 않고 Event Processor에서 즉시 CRITICAL 이벤트로 분류한다.

## 3. AI Inference 처리 흐름

### 3.1 영상 기반 추론

```
[stream:frames:*] → [Frame Buffer] → [Batch Inference] → [Post-Processing] → [stream:events]
                         │                    │                   │
                         ├── 채널별 큐         ├── TensorRT        ├── NMS
                         ├── 최신 N프레임      ├── Batch=8          ├── Confidence Filter
                         └── Drop 정책         └── GPU 처리         └── Risk Classification
```

**추론 결과:**
```json
{
  "stream": "stream:events",
  "data": {
    "event_id": "EVT-20250519120000-001",
    "site_id": "SITE-001",
    "device_id": "CAM-001",
    "timestamp": "2025-05-19T12:00:00.123Z",
    "event_type": "FALL_DETECTED",
    "confidence": 0.92,
    "model_version": "v1.0.0-edge",
    "risk_level": "CRITICAL",
    "details": {
      "bbox": [120, 80, 300, 450],
      "frame_seq": 12345,
      "zone": "작업장A"
    }
  }
}
```

### 3.2 센서 기반 판단

```
[stream:sensors] → [Threshold Engine] → [stream:events]
                         │
                         ├── 설정 파일 기반 임계치 비교
                         ├── 복합 조건 평가 (Platform 2.0)
                         └── 히스테리시스 적용 (떨림 방지)
```

### 3.3 바이오 데이터 판단

```
[stream:bio] → [Bio Analyzer] → [stream:events]
                    │
                    ├── 심박수 범위 체크 (40~150 bpm)
                    ├── 체온 범위 체크 (35~38.5°C)
                    ├── 가속도 낙상 패턴 감지
                    └── 데이터 미수신 감지 (30초)
```

## 4. 타이밍 요구사항

| 경로 | 최대 지연 | 측정 지점 |
|------|-----------|-----------|
| Camera → Frame Grab | 100ms | RTSP 수신 → Redis 저장 |
| Frame → AI Inference | 500ms | Redis 읽기 → 추론 완료 |
| AI Result → Event Process | 100ms | 추론 결과 → 등급 판정 |
| Event → Alarm Trigger | 200ms | 등급 판정 → GPIO 출력 |
| **End-to-End (Camera → Alarm)** | **≤ 2초** | 프레임 수신 → 알람 동작 |
| Sensor → Event | 500ms | MQTT 수신 → 이벤트 발생 |
| Fire Contact → Alarm | **≤ 1초** | 접점 신호 → 알람 동작 |

## 5. 에러 처리

### 5.1 장비 연결 끊김

```
[연결 끊김 감지] → [재연결 시도 (3회, 5초 간격)]
                         │
                    ┌────┴────┐
                    ▼         ▼
              [복구 성공]  [복구 실패]
                    │         │
                    ▼         ▼
              [정상 운영]  [DEVICE_OFFLINE 이벤트 발생]
                              │
                              ▼
                        [대시보드 경고 표시]
```

### 5.2 Redis 연결 장애

```
[Redis 연결 실패] → [로컬 파일 버퍼 전환] → [Redis 복구 감지] → [버퍼 데이터 재전송]
```

### 5.3 GPU 장애

```
[GPU 에러 감지] → [CPU Fallback 모드 전환] → [영상 추론 주기 감소 (15fps → 5fps)]
                                              → [센서/바이오 판단은 정상 유지]
                                              → [관리자 알림 발송]
```

---

*참조: [system-overview.md](./system-overview.md) | [platform-1.0-architecture.md](./platform-1.0-architecture.md)*
