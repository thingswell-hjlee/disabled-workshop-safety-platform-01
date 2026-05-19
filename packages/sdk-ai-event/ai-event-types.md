# AI Event Types - Platform 1.0

## 1. 이벤트 유형 정의

### 1.1 CRITICAL 등급 이벤트

| event_type | 설명 | 트리거 조건 | 알람 동작 |
|------------|------|-------------|-----------|
| `FALL_DETECTED` | 작업자 낙상 감지 | 영상 AI 낙상 판단 (confidence ≥ 0.7) | 사이렌+경광등 |
| `ZONE_INTRUSION` | 위험구역 침입 | 설정된 polygon 영역 내 사람 감지 | 사이렌+경광등 |
| `FIRE_DETECTED` | 화재 감지 | 화재감지기 접점 신호 수신 | 사이렌+경광등 |
| `HEARTRATE_ABNORMAL` | 심박 이상 | 심박 < 40 또는 > 150 bpm | 사이렌+경광등 |
| `BAND_FALL_DETECTED` | 밴드 낙상 감지 | 가속도 급변 패턴 감지 | 사이렌+경광등 |

### 1.2 WARNING 등급 이벤트

| event_type | 설명 | 트리거 조건 | 알람 동작 |
|------------|------|-------------|-----------|
| `ABNORMAL_BEHAVIOR` | 이상행동 감지 | 장시간 부동 또는 급격한 움직임 | 경광등만 |
| `ENV_THRESHOLD_EXCEEDED` | 환경 임계치 초과 | 온도/습도/CO/VOC 임계치 초과 | 경광등만 |
| `TEMPERATURE_ABNORMAL` | 체온 이상 | 체온 < 35 또는 > 38.5°C | 경광등만 |
| `BAND_DISCONNECTED` | 밴드 연결 끊김 | 30초 이상 데이터 미수신 | 경광등만 |

### 1.3 NORMAL 등급 이벤트

| event_type | 설명 | 트리거 조건 | 알람 동작 |
|------------|------|-------------|-----------|
| `NORMAL_RESTORED` | 정상 복귀 | 이상 상태 해소 | 알람 없음 |
| `DEVICE_ONLINE` | 장비 온라인 복귀 | 오프라인→온라인 전환 | 알람 없음 |

### 1.4 시스템 이벤트

| event_type | 설명 | 트리거 조건 | 알람 동작 |
|------------|------|-------------|-----------|
| `DEVICE_OFFLINE` | 장비 오프라인 | 연결 끊김 + 재연결 실패 | 대시보드 경고 |
| `SYSTEM_ALERT` | 시스템 경고 | NVR 용량, GPU 장애 등 | 대시보드 경고 |

## 2. 위험등급 판정 규칙

### 2.1 기본 매핑

```yaml
risk_classification:
  CRITICAL:
    - FALL_DETECTED
    - ZONE_INTRUSION
    - FIRE_DETECTED
    - HEARTRATE_ABNORMAL
    - BAND_FALL_DETECTED
  WARNING:
    - ABNORMAL_BEHAVIOR
    - ENV_THRESHOLD_EXCEEDED
    - TEMPERATURE_ABNORMAL
    - BAND_DISCONNECTED
  NORMAL:
    - NORMAL_RESTORED
    - DEVICE_ONLINE
```

### 2.2 confidence 기반 필터

| event_type | 최소 confidence | 비고 |
|------------|----------------|------|
| FALL_DETECTED | 0.70 | 미만 시 WARNING으로 하향 |
| ABNORMAL_BEHAVIOR | 0.65 | 미만 시 무시 |
| ZONE_INTRUSION | 0.75 | 미만 시 WARNING으로 하향 |

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
  │         │          └── Alarm Controller GPIO 출력
  │         └── Risk Classifier 등급 판정
  └── AI Inference / Sensor Handler 이벤트 생성
```

### 3.1 상태 전이

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
| 접점 알람 (사이렌) | ✅ | ❌ | ❌ |
| 접점 알람 (경광등) | ✅ | ✅ | ❌ |
| 대시보드 팝업 | ✅ | ✅ | ❌ |
| Web Push | ✅ | ✅ | ❌ |
| 이벤트 로그 | ✅ | ✅ | ✅ |
| 클라우드 전송 | ✅ | ✅ | ✅ |
| NVR 클립 저장 | ✅ | ✅ | ❌ |

## 5. ID 생성 규칙

### 5.1 event_id

```
EVT-{YYYYMMDDHHmmss}-{SEQ}
예: EVT-20250519120000-001
```

- `timestamp`: 이벤트 발생 시각 (로컬 시간)
- `SEQ`: 동일 초 내 순번 (001~999)
- 유일성: timestamp + SEQ 조합으로 보장

### 5.2 기타 ID

| ID | 형식 | 예시 |
|----|------|------|
| site_id | `SITE-{NNN}` | SITE-001 |
| device_id | `{TYPE}-{NNN}` | CAM-001, BAND-003 |
| worker_id | `WKR-{NNNN}` | WKR-0001 |
| model_version | `v{M}.{m}.{p}-{target}` | v1.0.0-edge |

---

*버전: 0.1 | 작성일: 2025-05-19*
