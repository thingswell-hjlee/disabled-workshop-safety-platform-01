# Platform 1.0 Interface Schema - Master Document

> **Status:** FROZEN (Platform 1.0)
> **Last Updated:** 2025-05-19
> **Purpose:** Multi-session development의 공통 인터페이스 스키마 정의

## 1. Design Principles

- Platform 1.0은 **최소 통합 동작(Minimal Integrated Operation)**에 필요한 스키마만 확정
- Platform 2.0/3.0 확장 필드는 `reserved` 또는 `optional (Platform 2.0+)`로 분리
- 모든 스키마에 `site_id`를 포함하여 멀티 사이트 확장 대비
- Timestamps: **ISO 8601 UTC** format

---

## 2. ID Format Definitions

| ID Type | Format | Pattern | Example |
|---------|--------|---------|---------|
| `site_id` | `SITE-NNN` | `^SITE-\d{3}$` | `SITE-001` |
| `device_id` | `{TYPE}-NNN` | `^(CAM\|BAND\|ENV\|FIRE\|NVR\|ALARM)-\d{3}$` | `CAM-001` |
| `worker_id` | `WKR-NNNN` | `^WKR-\d{4}$` | `WKR-0001` |
| `event_id` | `EVT-YYYYMMDDHHmmss-SEQ` | `^EVT-\d{14}-\d{3}$` | `EVT-20250519120000-001` |
| `camera_id` | `CAM-NNN` | `^CAM-\d{3}$` | `CAM-001` |
| `band_id` | `BAND-NNN` | `^BAND-\d{3}$` | `BAND-001` |
| `sensor_id` | `ENV-NNN` | `^ENV-\d{3}$` | `ENV-001` |

---

## 3. Enum Definitions

### 3.1 event_type

| Value | Source | Platform |
|-------|--------|----------|
| `FALL_DETECTED` | DeepStream (Vision AI) | 1.0 |
| `COLLAPSE_DETECTED` | DeepStream (Vision AI) | 1.0 |
| `ZONE_INTRUSION` | DeepStream (Vision AI) | 1.0 |
| `STILLNESS_DETECTED` | DeepStream (Vision AI) | 1.0 |
| `HAZARDOUS_ACTION` | DeepStream (Vision AI) | 1.0 |
| `FIRE_DETECTED` | DeepStream (Vision AI) / Fire Contact | 1.0 |
| `HEARTRATE_ABNORMAL` | Smart Band | 1.0 |
| `TEMPERATURE_ABNORMAL` | Smart Band | 1.0 |
| `BAND_FALL_DETECTED` | Smart Band | 1.0 |
| `BAND_DISCONNECTED` | Smart Band | 1.0 |
| `ENV_THRESHOLD_EXCEEDED` | Environmental Sensor | 1.0 |
| `DEVICE_OFFLINE` | Device Gateway | 1.0 |
| `DEVICE_ONLINE` | Device Gateway | 1.0 |
| `NORMAL_RESTORED` | Event Engine | 1.0 |
| `SYSTEM_ALERT` | System | 1.0 |

### 3.2 risk_level

| Value | Description |
|-------|-------------|
| `CRITICAL` | 즉시 경보 발동, 관리자 즉시 대응 필요 |
| `WARNING` | 주의 필요, 모니터링 강화 |
| `NORMAL` | 정상 상태 또는 복귀 |

### 3.3 device_type

| Value | Description |
|-------|-------------|
| `IP_CAMERA` | IP 카메라 (DeepStream 입력) |
| `SMART_BAND` | 스마트 밴드 (작업자 생체/낙상) |
| `ENV_SENSOR` | 환경 센서 (온습도, 가스, 미세먼지) |
| `FIRE_CONTACT` | 화재 접점 센서 |
| `ALARM_DEVICE` | 사이렌/경광등 출력 장치 |
| `NVR` | Network Video Recorder |

### 3.4 device_status

| Value | Description |
|-------|-------------|
| `CONNECTED` | 정상 연결 |
| `DISCONNECTED` | 연결 끊김 |
| `ERROR` | 오류 상태 |
| `RECONNECTING` | 재연결 시도 중 |

### 3.5 event_state

| Value | Description |
|-------|-------------|
| `ACTIVE` | 이벤트 활성 상태 (미처리) |
| `ACKNOWLEDGED` | 관리자 확인 완료 |
| `ARCHIVED` | 보관 (처리 완료) |

---

## 4. Timestamp Format

- **Format:** ISO 8601 UTC
- **Pattern:** `YYYY-MM-DDTHH:mm:ss.mmmZ`
- **Example:** `2025-05-19T12:00:00.123Z`
- **Resolution:** Millisecond
- **Timezone:** Always UTC (Z suffix)

---

## 5. Model Version Naming

- **Format:** `v{major}.{minor}.{patch}-{tool}-{target}`
- **Pattern:** `^v\d+\.\d+\.\d+-(tao|pretrained|custom)-(ds|cloud)$`

| Field | Values | Description |
|-------|--------|-------------|
| `major` | 0-N | Breaking changes |
| `minor` | 0-N | Feature additions |
| `patch` | 0-N | Bug fixes |
| `tool` | `tao`, `pretrained`, `custom` | Training tool/origin |
| `target` | `ds`, `cloud` | Deployment target |

**Examples:**
- `v1.0.0-tao-ds` — TAO Toolkit으로 학습, DeepStream 배포
- `v1.0.0-pretrained-ds` — 사전학습 모델, DeepStream 배포
- `v2.1.0-custom-cloud` — 커스텀 학습, 클라우드 평가용

---

## 6. Session Boundary Table

아래 표는 4개 개발 세션이 각각 소유하는 인터페이스를 정의합니다. 세션 간 충돌을 방지하기 위해 각 인터페이스의 **Publisher(Producer)**와 **Subscriber(Consumer)**를 명확히 합니다.

| Interface | Owner Session | Publisher | Subscriber |
|-----------|--------------|-----------|------------|
| `stream:ds-events` | Edge Device | DeepStream Pipeline | Event Engine |
| `stream:sensors` | Edge Device | Device Gateway | Event Engine |
| `stream:alarms` | Edge Device | Event Engine | Alarm Controller |
| `stream:dashboard` | Edge Device | Event Engine | Dashboard Backend |
| `stream:cloud-queue` | AWS Cloud | Event Engine | AWS Sync Service |
| `stream:clip-trigger` | Edge Device | Event Engine | Rolling Buffer |
| MQTT `safety/{site_id}/events` | AWS Cloud | AWS Sync Service | IoT Core |
| MQTT `safety/{site_id}/status` | AWS Cloud | Edge Status Reporter | IoT Core |
| MQTT `safety/{site_id}/models` | AI Training | Cloud Model Manager | Edge Deployer |
| Model Registry (`registry.json`) | AI Training | Model Pipeline | DeepStream Loader |
| WebSocket `/ws/events` | Integration Test | Dashboard Backend | Dashboard UI |

### Session Definitions

| Session | Scope | Primary Components |
|---------|-------|--------------------|
| **S1: Edge Device** | 엣지 디바이스 통합 | DeepStream, Device Gateway, Event Engine, Alarm Controller, Rolling Buffer |
| **S2: AWS Cloud** | 클라우드 동기화 | AWS Sync, IoT Core, S3, DynamoDB, Lambda |
| **S3: AI Training** | AI 모델 학습/배포 | TAO Toolkit, Model Registry, Deployment Pipeline |
| **S4: Integration Test** | 통합 테스트 | E2E Test, Schema Validation, Load Test |

---

## 7. Cross-Reference

| Document | Description |
|----------|-------------|
| [redis-streams-schema.md](./redis-streams-schema.md) | Redis Streams 메시지 구조 상세 |
| [aws-iot-message-schema.md](./aws-iot-message-schema.md) | AWS IoT Core MQTT 메시지 구조 |
| [event-message-schema.md](./event-message-schema.md) | 정규 이벤트 메시지 (단일 진실 원천) |
| [model-package-schema.md](./model-package-schema.md) | 모델 패키지 폴더 구조/버전 명명 |
| [schema-validation-test.md](./schema-validation-test.md) | 스키마 검증 테스트 기준 |
