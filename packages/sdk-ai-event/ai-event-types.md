# AI Event Types - Platform 1.0

> **PR #16 동결 스키마 기준** (docs/event-message-schema.md, docs/interface-schema.md)

## 1. 이벤트 유형 정의 (15종)

### 1.1 CRITICAL 등급 이벤트 (C-001 규칙)

> FALL_DETECTED, COLLAPSE_DETECTED, FIRE_DETECTED → 반드시 CRITICAL

| event_type | 설명 | 소스 | 트리거 조건 |
|------------|------|------|-------------|
| `FALL_DETECTED` | 작업자 낙상 감지 | DeepStream (Vision AI) | 영상 AI 낙상 판단 |
| `COLLAPSE_DETECTED` | 작업자 쓰러짐 감지 | DeepStream (Vision AI) | 영상 AI 쓰러짐 판단 |
| `FIRE_DETECTED` | 화재 감지 | DeepStream / Fire Contact | 화재감지기 접점 또는 영상 AI |

### 1.2 WARNING 등급 이벤트

| event_type | 설명 | 소스 | 트리거 조건 |
|------------|------|------|-------------|
| `ZONE_INTRUSION` | 위험구역 침입 | DeepStream (Vision AI) | 설정 polygon 영역 내 사람 감지 |
| `STILLNESS_DETECTED` | 장시간 미움직임 | DeepStream (Vision AI) | 설정 시간 이상 부동 |
| `HAZARDOUS_ACTION` | 위험행동 감지 | DeepStream (Vision AI) | 위험행동 패턴 판단 |
| `HEARTRATE_ABNORMAL` | 심박 이상 | Smart Band | 심박 < 40 또는 > 150 bpm |
| `TEMPERATURE_ABNORMAL` | 체온 이상 | Smart Band | 체온 < 35 또는 > 38.5°C |
| `BAND_FALL_DETECTED` | 밴드 낙상 감지 | Smart Band | 가속도 급변 패턴 감지 |
| `BAND_DISCONNECTED` | 밴드 연결 끊김 | Smart Band | 30초 이상 데이터 미수신 |
| `ENV_THRESHOLD_EXCEEDED` | 환경 임계치 초과 | Environmental Sensor | 온습도/가스/미세먼지 임계치 초과 |

### 1.3 NORMAL 등급 이벤트

| event_type | 설명 | 소스 | 트리거 조건 |
|------------|------|------|-------------|
| `DEVICE_OFFLINE` | 장비 오프라인 | Device Gateway | 연결 끊김 + 재연결 실패 |
| `DEVICE_ONLINE` | 장비 온라인 복귀 | Device Gateway | 오프라인→온라인 전환 |
| `NORMAL_RESTORED` | 정상 복귀 | Event Engine | 이상 상태 해소 |
| `SYSTEM_ALERT` | 시스템 경고 | System | NVR 용량, GPU 장애 등 |

## 2. 위험등급 판정 규칙

### 2.1 기본 매핑 (PR #16 C-001)

```yaml
risk_classification:
  CRITICAL:
    - FALL_DETECTED
    - COLLAPSE_DETECTED
    - FIRE_DETECTED
  WARNING:
    - ZONE_INTRUSION
    - STILLNESS_DETECTED
    - HAZARDOUS_ACTION
    - HEARTRATE_ABNORMAL
    - TEMPERATURE_ABNORMAL
    - BAND_FALL_DETECTED
    - BAND_DISCONNECTED
    - ENV_THRESHOLD_EXCEEDED
  NORMAL:
    - DEVICE_OFFLINE
    - DEVICE_ONLINE
    - NORMAL_RESTORED
    - SYSTEM_ALERT
```

### 2.2 confidence 기반 필터

| event_type | 최소 confidence | 비고 |
|------------|----------------|------|
| FALL_DETECTED | 0.70 | 미만 시 이벤트 생성하지 않음 |
| COLLAPSE_DETECTED | 0.70 | 미만 시 이벤트 생성하지 않음 |
| ZONE_INTRUSION | 0.75 | 미만 시 이벤트 생성하지 않음 |
| STILLNESS_DETECTED | 0.65 | 미만 시 이벤트 생성하지 않음 |
| HAZARDOUS_ACTION | 0.70 | 미만 시 이벤트 생성하지 않음 |

### 2.3 복합 판정 규칙

- 동일 시간대(5초 이내) 복수 이벤트 발생 시 최고 등급 적용
- 동일 장비에서 동일 유형 반복(10초 이내) 시 중복 이벤트 억제
- 화재 접점(`FIRE_DETECTED`)은 confidence 무관, 항상 CRITICAL

## 3. 이벤트 생명주기

```
[생성] → [판정] → [알람 발동] → [대시보드 표시] → [해제(Acknowledge)] → [아카이브]
  │         │          │              │                 │                    │
  │         │          │              │                 │                    └── 클라우드 저장
  │         │          │              │                 └── 관리자 수동 해제
  │         │          │              └── WebSocket 실시간 전송
  │         │          └── Alarm Controller (stream:alarms)
  │         └── Event Engine 등급 판정
  └── AI Inference / Device Gateway 이벤트 생성
```

### 3.1 상태 전이 (event_state)

```
ACTIVE → ACKNOWLEDGED → ARCHIVED
  │           │
  │           └── (관리자 해제)
  └── (자동 해소: NORMAL_RESTORED 수신 시)
```

## 4. 이벤트 라우팅

### 4.1 등급별 라우팅

| 목적지 | CRITICAL | WARNING | NORMAL |
|--------|----------|---------|--------|
| stream:alarms (사이렌+경광등) | ALL_ON | LIGHT_ON | ALL_OFF |
| stream:dashboard | ✅ | ✅ | ✅ |
| stream:cloud-queue | HIGH | NORMAL | LOW |
| stream:clip-trigger | ✅ | ✅ | ❌ |

## 5. ID 생성 규칙

### 5.1 event_id

```
EVT-{YYYYMMDDHHmmss}-{SEQ}
예: EVT-20250519120000-001
Pattern: ^EVT-\d{14}-\d{3}$
```

### 5.2 기타 ID (PR #16 동결)

| ID | 형식 | Pattern | 예시 |
|----|------|---------|------|
| site_id | `SITE-{NNN}` | `^SITE-\d{3}$` | SITE-001 |
| device_id | `{TYPE}-{NNN}` | `^(CAM\|BAND\|ENV\|FIRE\|NVR\|ALARM)-\d{3}$` | CAM-001 |
| worker_id | `WKR-{NNNN}` | `^WKR-\d{4}$` | WKR-0001 |
| model_version | `v{M}.{m}.{p}-{tool}-{target}` | `^v\d+\.\d+\.\d+-(tao\|pretrained\|custom)-(ds\|cloud)$` | v1.0.0-tao-ds |

---

*버전: 1.0 | PR #16 동결 기준 | 작성일: 2025-05-20*
