# Platform 1.0 데이터 모델 (Data Model)

> **참조:** docs/design.md | .kiro/specs/requirements.md
> **저장소:** SQLite (Platform 1.0) → PostgreSQL (Platform 2.0+)
> **원칙:** 모든 테이블에 site_id 포함, Platform 2.0/3.0 확장 필드 예약

---

## 설계 원칙

1. **site_id 필수**: 모든 엔티티에 현장 ID 포함 (다중 현장 확장 대비)
2. **확장 필드 예약**: Platform 2.0/3.0 기능용 nullable 필드 미리 정의
3. **타임스탬프 표준**: ISO 8601 (UTC), `created_at` / `updated_at` 공통
4. **ID 형식**: 정의된 ID 체계 준수 (EVT-, CAM-, BAND- 등)
5. **JSON 필드**: 유연한 확장이 필요한 곳에 JSON/JSONB 사용

---

## 1. Site (현장)

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| site_id | VARCHAR(10) | PK | 현장 ID (SITE-001) |
| name | VARCHAR(100) | ✅ | 현장명 |
| address | VARCHAR(200) | ✅ | 주소 |
| timezone | VARCHAR(30) | ✅ | 타임존 (Asia/Seoul) |
| status | ENUM | ✅ | ACTIVE / INACTIVE |
| config | JSON | ❌ | 현장별 설정 오버라이드 |
| created_at | TIMESTAMP | ✅ | 생성일시 |
| updated_at | TIMESTAMP | ✅ | 수정일시 |

> Platform 1.0: 단일 현장 (SITE-001). 구조만 확보.

---

## 2. Zone (구역)

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| zone_id | VARCHAR(20) | PK | 구역 ID (ZONE-A, ZONE-B) |
| site_id | VARCHAR(10) | FK | 소속 현장 |
| name | VARCHAR(50) | ✅ | 구역명 (작업장A, 장비실) |
| zone_type | ENUM | ✅ | WORK / DANGER / REST / PASSAGE |
| polygon | JSON | ❌ | ROI 좌표 (카메라별 매핑용) |
| camera_ids | JSON | ❌ | 관련 카메라 ID 목록 |
| created_at | TIMESTAMP | ✅ | 생성일시 |

---

## 3. Worker (작업자)

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| worker_id | VARCHAR(10) | PK | 작업자 ID (WKR-0001) |
| site_id | VARCHAR(10) | FK | 소속 현장 |
| name | VARCHAR(50) | ✅ | 이름 |
| band_device_id | VARCHAR(10) | ❌ | 착용 밴드 ID |
| zone_id | VARCHAR(20) | ❌ | 현재 위치 구역 |
| status | ENUM | ✅ | ACTIVE / INACTIVE / LEAVE |
| emergency_contact | VARCHAR(20) | ❌ | 비상 연락처 |
| created_at | TIMESTAMP | ✅ | 등록일시 |
| updated_at | TIMESTAMP | ✅ | 수정일시 |

---

## 4. Device (장비 - 공통)

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| device_id | VARCHAR(10) | PK | 장비 ID (CAM-001, BAND-003) |
| site_id | VARCHAR(10) | FK | 소속 현장 |
| device_type | ENUM | ✅ | IP_CAMERA / SMART_BAND / ENV_SENSOR / FIRE_CONTACT / ALARM / NVR |
| name | VARCHAR(50) | ✅ | 장비명 |
| zone_id | VARCHAR(20) | ❌ | 설치 구역 |
| status | ENUM | ✅ | CONNECTED / DISCONNECTED / ERROR / MAINTENANCE |
| ip_address | VARCHAR(15) | ❌ | IP 주소 (네트워크 장비) |
| firmware_version | VARCHAR(20) | ❌ | 펌웨어 버전 |
| last_heartbeat | TIMESTAMP | ❌ | 마지막 통신 시각 |
| metadata | JSON | ❌ | 장비별 추가 정보 |
| created_at | TIMESTAMP | ✅ | 등록일시 |
| updated_at | TIMESTAMP | ✅ | 수정일시 |

---

## 5. Camera (IP 카메라 - Device 확장)

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| device_id | VARCHAR(10) | PK/FK | Device 참조 |
| rtsp_url | VARCHAR(200) | ✅ | RTSP 스트림 URL |
| resolution | VARCHAR(10) | ✅ | 해상도 (1920x1080) |
| fps | INT | ✅ | 프레임레이트 |
| source_id | INT | ✅ | DeepStream source 번호 (0~7) |
| roi_config_path | VARCHAR(100) | ❌ | ROI 설정 파일 경로 |
| recording_enabled | BOOLEAN | ✅ | NVR 녹화 활성화 |

---

## 6. SmartBand (스마트밴드 - Device 확장)

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| device_id | VARCHAR(10) | PK/FK | Device 참조 |
| worker_id | VARCHAR(10) | FK | 착용 작업자 |
| mac_address | VARCHAR(17) | ✅ | BLE MAC 주소 |
| battery_level | INT | ❌ | 배터리 잔량 (%) |
| data_interval_ms | JSON | ✅ | 수집 주기 {"heartrate": 5000, "accel": 100, "location": 1000} |

---

## 7. EnvironmentSensor (환경센서 - Device 확장)

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| device_id | VARCHAR(10) | PK/FK | Device 참조 |
| sensor_types | JSON | ✅ | 측정 항목 ["temperature", "humidity", "co", "voc"] |
| thresholds | JSON | ✅ | 임계치 {"temperature_max": 40.0, "co_ppm_max": 50} |
| collection_interval_sec | INT | ✅ | 수집 주기 (초) |

---

## 8. FireContact (화재감지 접점 - Device 확장)

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| device_id | VARCHAR(10) | PK/FK | Device 참조 |
| gpio_pin | INT | ✅ | GPIO 핀 번호 (BCM) |
| interface_type | ENUM | ✅ | GPIO / RS485 |
| polling_interval_ms | INT | ✅ | 폴링 주기 (ms) |
| debounce_ms | INT | ✅ | 디바운싱 시간 (ms) |
| contact_state | ENUM | ✅ | NORMAL / DETECTED / FAULT |

---

## 9. AlarmDevice (알람장치 - Device 확장)

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| device_id | VARCHAR(10) | PK/FK | Device 참조 |
| siren_gpio_pin | INT | ✅ | 사이렌 GPIO 핀 |
| light_gpio_pin | INT | ✅ | 경광등 GPIO 핀 |
| active_high | BOOLEAN | ✅ | HIGH 시 동작 여부 |
| current_state | ENUM | ✅ | IDLE / SIREN_ON / LIGHT_ON / BOTH_ON |

---

## 10. Event (이벤트)

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| event_id | VARCHAR(25) | PK | 이벤트 ID (EVT-YYYYMMDDHHmmss-SEQ) |
| site_id | VARCHAR(10) | FK | 현장 |
| device_id | VARCHAR(10) | FK | 발생 장비 |
| worker_id | VARCHAR(10) | ❌ | 관련 작업자 |
| event_type | VARCHAR(30) | ✅ | FALL_DETECTED, ZONE_INTRUSION 등 |
| risk_level | ENUM | ✅ | CRITICAL / WARNING / NORMAL |
| confidence | FLOAT | ❌ | AI 신뢰도 (0.0~1.0) |
| model_version | VARCHAR(30) | ❌ | 사용 모델 버전 |
| timestamp | TIMESTAMP | ✅ | 이벤트 발생 시각 |
| state | ENUM | ✅ | ACTIVE / ACKNOWLEDGED / ARCHIVED |
| acknowledged_by | VARCHAR(30) | ❌ | 해제자 ID |
| acknowledged_at | TIMESTAMP | ❌ | 해제 시각 |
| ack_reason | TEXT | ❌ | 해제 사유 |
| clip_path | VARCHAR(200) | ❌ | 영상 클립 경로 |
| clip_s3_key | VARCHAR(200) | ❌ | S3 업로드 키 |
| idempotency_key | VARCHAR(30) | ✅ | 중복 방지 키 |
| synced_to_cloud | BOOLEAN | ✅ | 클라우드 전송 완료 여부 |
| feedback_type | ENUM | ❌ | 확장: TRUE_POSITIVE / FALSE_POSITIVE / MISSED (Platform 2.0) |
| reanalysis_result | JSON | ❌ | 확장: Generative 재추론 결과 (Platform 3.0) |
| created_at | TIMESTAMP | ✅ | 레코드 생성 시각 |

---

## 11. EventContext (이벤트 컨텍스트)

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| context_id | VARCHAR(30) | PK | 컨텍스트 ID |
| event_id | VARCHAR(25) | FK | 연결 이벤트 |
| video_clip | JSON | ❌ | {path, start_ts, end_ts, duration_sec, quality_level} |
| sensor_snapshot | JSON | ❌ | {band_data, env_data, fire_status} |
| inference_detail | JSON | ❌ | {pgie_conf, sgie_conf, tracking_id, dwell_time, roi_name} |
| system_state | JSON | ❌ | {gpu_util, active_cameras, network_status} |
| activity_index | FLOAT | ❌ | 이벤트 시점 활동지수 |
| quality_level | INT | ✅ | 저장 품질 (0=원본, 확장: 0~3) |
| buffer_duration_sec | INT | ✅ | 버퍼 길이 (기본 60, 확장: 30~120) |
| extended_context | JSON | ❌ | 확장: {activity_history, audit_hash, rag_ref} (Platform 2.0/3.0) |
| created_at | TIMESTAMP | ✅ | 생성일시 |

---

## 12. RollingBufferSegment (롤링버퍼 세그먼트)

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| segment_id | VARCHAR(40) | PK | 세그먼트 ID |
| device_id | VARCHAR(10) | FK | 카메라 ID |
| site_id | VARCHAR(10) | FK | 현장 |
| start_ts | TIMESTAMP | ✅ | 시작 시각 |
| end_ts | TIMESTAMP | ✅ | 종료 시각 |
| duration_sec | INT | ✅ | 길이 (초) |
| file_path | VARCHAR(200) | ❌ | 저장 파일 경로 (추출 시) |
| quality_level | INT | ✅ | 품질 레벨 (기본 0) |
| buffer_duration_sec | INT | ✅ | 버퍼 크기 (기본 60) |
| status | ENUM | ✅ | ACTIVE / EXTRACTED / EXPIRED |
| triggered_by_event | VARCHAR(25) | ❌ | 추출 트리거 이벤트 ID |
| created_at | TIMESTAMP | ✅ | 생성일시 |

---

## 13. ActivityIndex (활동지수)

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| record_id | VARCHAR(40) | PK | 레코드 ID |
| site_id | VARCHAR(10) | FK | 현장 |
| worker_id | VARCHAR(10) | FK | 작업자 |
| timestamp | TIMESTAMP | ✅ | 산출 시각 |
| movement_score | FLOAT | ✅ | 이동 점수 (0.0~1.0) |
| posture_score | FLOAT | ✅ | 자세 점수 (0.0~1.0) |
| heartrate_score | FLOAT | ✅ | 심박 점수 (0.0~1.0) |
| composite_index | FLOAT | ✅ | 종합 활동지수 (0.0~1.0) |
| weights | JSON | ✅ | 가중치 {movement: 0.4, posture: 0.4, heartrate: 0.2} |
| baseline_profile | JSON | ❌ | 확장: 개인 기준선 (Platform 2.0) |
| created_at | TIMESTAMP | ✅ | 생성일시 |

---

## 14. RiskLevel (위험등급 설정)

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| rule_id | VARCHAR(20) | PK | 규칙 ID |
| site_id | VARCHAR(10) | FK | 현장 |
| event_type | VARCHAR(30) | ✅ | 이벤트 유형 |
| risk_level | ENUM | ✅ | CRITICAL / WARNING / NORMAL |
| min_confidence | FLOAT | ❌ | 최소 confidence (없으면 무조건 적용) |
| source_filter | VARCHAR(20) | ❌ | 소스 필터 (contact, band 등) |
| alarm_actions | JSON | ✅ | ["SIREN_ON", "LIGHT_ON"] |
| routes | JSON | ✅ | ["alarm", "dashboard", "cloud"] |
| enabled | BOOLEAN | ✅ | 활성화 여부 |
| created_at | TIMESTAMP | ✅ | 생성일시 |
| updated_at | TIMESTAMP | ✅ | 수정일시 |

---

## 15. AlarmAction (알람 동작 이력)

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| action_id | VARCHAR(30) | PK | 동작 ID |
| site_id | VARCHAR(10) | FK | 현장 |
| event_id | VARCHAR(25) | FK | 트리거 이벤트 |
| action_type | ENUM | ✅ | SIREN_ON / LIGHT_ON / ALL_ON / ALL_OFF |
| risk_level | ENUM | ✅ | 트리거 등급 |
| triggered_at | TIMESTAMP | ✅ | 동작 시각 |
| cleared_at | TIMESTAMP | ❌ | 해제 시각 |
| cleared_by | VARCHAR(30) | ❌ | 해제자 |
| clear_reason | TEXT | ❌ | 해제 사유 |
| auto_cleared | BOOLEAN | ✅ | 자동 해제 여부 |

---

## 16. ModelVersion (모델 버전)

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| model_version | VARCHAR(30) | PK | 버전 ID (v1.0.0-tao-ds) |
| site_id | VARCHAR(10) | FK | 학습 현장 |
| model_type | ENUM | ✅ | PGIE_DETECTION / SGIE_ACTION / CUSTOM |
| model_name | VARCHAR(50) | ✅ | 모델명 (PeopleNet, ActionRecog) |
| framework | ENUM | ✅ | TENSORRT / ONNX / TAO |
| precision | ENUM | ✅ | FP16 / INT8 / FP32 |
| engine_path | VARCHAR(200) | ✅ | .engine 파일 경로 |
| file_size_mb | FLOAT | ❌ | 파일 크기 |
| trained_at | TIMESTAMP | ❌ | 학습 완료 시각 |
| dataset_id | VARCHAR(30) | ❌ | 학습 데이터셋 ID |
| metrics | JSON | ❌ | {mAP, precision, recall, f1, inference_ms} |
| status | ENUM | ✅ | STAGED / ACTIVE / ROLLBACK / ARCHIVED |
| deployed_at | TIMESTAMP | ❌ | 배포 시각 |
| s3_key | VARCHAR(200) | ❌ | 클라우드 저장 경로 |
| created_at | TIMESTAMP | ✅ | 생성일시 |

---

## 17. DeviceHealth (장비 헬스)

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| health_id | VARCHAR(40) | PK | 레코드 ID |
| device_id | VARCHAR(10) | FK | 장비 ID |
| site_id | VARCHAR(10) | FK | 현장 |
| timestamp | TIMESTAMP | ✅ | 측정 시각 |
| status | ENUM | ✅ | CONNECTED / DISCONNECTED / ERROR |
| metrics | JSON | ❌ | 장비별 메트릭 (fps, battery, signal 등) |
| gpu_metrics | JSON | ❌ | GPU 메트릭 (서버 전용: util%, memory%) |
| error_message | TEXT | ❌ | 에러 상세 |
| created_at | TIMESTAMP | ✅ | 생성일시 |

---

## 18. MaintenanceLog (유지보수 로그)

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| maint_id | VARCHAR(20) | PK | 유지보수 ID (MAINT-YYYYMMDD-SEQ) |
| site_id | VARCHAR(10) | FK | 현장 |
| device_id | VARCHAR(10) | ❌ | 대상 장비 (null이면 시스템 전체) |
| maint_type | ENUM | ✅ | MODEL_DEPLOY / CONFIG_CHANGE / HW_REPAIR / SW_UPDATE |
| description | TEXT | ✅ | 작업 내용 |
| performed_by | VARCHAR(30) | ✅ | 작업자 |
| performed_at | TIMESTAMP | ✅ | 수행 시각 |
| result | ENUM | ✅ | SUCCESS / FAILED / ROLLED_BACK |
| before_state | JSON | ❌ | 변경 전 상태 |
| after_state | JSON | ❌ | 변경 후 상태 |
| created_at | TIMESTAMP | ✅ | 생성일시 |

---

## 19. AuditLog (감사 로그)

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| audit_id | VARCHAR(40) | PK | 감사 로그 ID |
| site_id | VARCHAR(10) | FK | 현장 |
| timestamp | TIMESTAMP | ✅ | 발생 시각 |
| actor | VARCHAR(30) | ✅ | 행위자 (user_id 또는 system) |
| action | VARCHAR(50) | ✅ | 행위 (LOGIN, ACKNOWLEDGE, CONFIG_CHANGE 등) |
| resource_type | VARCHAR(30) | ✅ | 대상 유형 (event, device, model, user) |
| resource_id | VARCHAR(50) | ❌ | 대상 ID |
| details | JSON | ❌ | 상세 정보 |
| ip_address | VARCHAR(45) | ❌ | 접속 IP |
| audit_hash | VARCHAR(64) | ❌ | 확장: 해시체인 해시값 (Platform 3.0) |
| prev_hash | VARCHAR(64) | ❌ | 확장: 이전 레코드 해시 (Platform 3.0) |
| created_at | TIMESTAMP | ✅ | 생성일시 |

> Platform 1.0: audit_hash / prev_hash는 null. Platform 3.0에서 해시체인 무결성 검증 활성화.

---

## ER 다이어그램 (주요 관계)

```
Site (1) ──→ (N) Zone
Site (1) ──→ (N) Device
Site (1) ──→ (N) Worker
Site (1) ──→ (N) Event

Device (1) ──→ (0..1) Camera
Device (1) ──→ (0..1) SmartBand
Device (1) ──→ (0..1) EnvironmentSensor
Device (1) ──→ (0..1) FireContact
Device (1) ──→ (0..1) AlarmDevice
Device (1) ──→ (N) DeviceHealth

Worker (1) ──→ (0..1) SmartBand
Worker (1) ──→ (N) Event
Worker (1) ──→ (N) ActivityIndex

Event (1) ──→ (1) EventContext
Event (1) ──→ (N) AlarmAction
Event (1) ──→ (0..1) RollingBufferSegment

ModelVersion (N) ──→ Site
MaintenanceLog (N) ──→ Site, Device
AuditLog (N) ──→ Site
RiskLevel (N) ──→ Site
```

---

## Platform 2.0/3.0 확장 필드 요약

| 엔티티 | 확장 필드 | 목적 | 시점 |
|--------|-----------|------|------|
| Event | feedback_type | 오탐/미탐 태깅 → 재학습 | 2.0 |
| Event | reanalysis_result | Generative 재추론 | 3.0 |
| EventContext | extended_context | 활동 이력, RAG, 감사 해시 | 2.0/3.0 |
| EventContext | quality_level | L0~L3 저장 품질 | 2.0 |
| EventContext | buffer_duration_sec | 적응형 버퍼 크기 | 2.0 |
| ActivityIndex | baseline_profile | 개인 기준선 프로파일 | 2.0 |
| AuditLog | audit_hash, prev_hash | 해시체인 무결성 | 3.0 |

---

## 변경 이력

| 버전 | 일자 | 내용 |
|------|------|------|
| 1.0 | 2025-05-19 | Platform 1.0 데이터 모델 초안 (19개 엔티티) |
