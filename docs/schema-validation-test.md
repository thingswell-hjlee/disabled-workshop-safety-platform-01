# Schema Validation Test Criteria

> **Status:** FROZEN (Platform 1.0)
> **Last Updated:** 2025-05-19
> **Purpose:** 인터페이스 스키마 검증 규칙, 테스트 케이스, CI 통합 계획 정의

## Overview

모든 인터페이스 스키마의 정합성을 보장하기 위한 검증 규칙과 테스트 전략을 정의합니다.

---

## 1. Test Categories

| Category | Purpose | Scope |
|----------|---------|-------|
| **Format Validation** | ID 형식, 타임스탬프 형식, enum 값 검증 | 단일 필드 |
| **Completeness** | 필수 필드 존재 여부 확인 | 메시지 레벨 |
| **Consistency** | 필드 간 논리적 정합성 | 메시지 레벨 |
| **Boundary** | 경계값, 범위 초과, 엣지 케이스 | 필드/메시지 레벨 |

---

## 2. Format Validation Rules

### 2.1 ID Format Patterns

| ID Type | Regex Pattern | Valid Examples | Invalid Examples |
|---------|--------------|----------------|------------------|
| `event_id` | `^EVT-\d{14}-\d{3}$` | `EVT-20250519120000-001` | `EVT-2025051912-001`, `EVT-20250519120000-1` |
| `site_id` | `^SITE-\d{3}$` | `SITE-001` | `SITE-01`, `SITE-1000` |
| `device_id` | `^(CAM\|BAND\|ENV\|FIRE\|NVR\|ALARM)-\d{3}$` | `CAM-001`, `BAND-012` | `CAM-1`, `CAMERA-001` |
| `worker_id` | `^WKR-\d{4}$` | `WKR-0001` | `WKR-001`, `WORKER-0001` |
| `camera_id` | `^CAM-\d{3}$` | `CAM-001` | `CAM-01` |
| `band_id` | `^BAND-\d{3}$` | `BAND-001` | `BAND-01` |
| `sensor_id` | `^ENV-\d{3}$` | `ENV-001` | `ENV-01` |
| `model_version` | `^v\d+\.\d+\.\d+-(tao\|pretrained\|custom)-(ds\|cloud)$` | `v1.0.0-tao-ds` | `v1.0-tao-ds`, `1.0.0-tao-ds` |

### 2.2 Timestamp Validation

| Rule | Validation |
|------|-----------|
| Format | ISO 8601 UTC: `YYYY-MM-DDTHH:mm:ss.mmmZ` |
| Timezone | Must end with `Z` (UTC) |
| Range | Not in future (max +5 seconds tolerance) |
| Precision | Millisecond (3 decimal places) |


### 2.3 Enum Validation

| Enum | Valid Values |
|------|-------------|
| `event_type` | FALL_DETECTED, COLLAPSE_DETECTED, ZONE_INTRUSION, STILLNESS_DETECTED, HAZARDOUS_ACTION, FIRE_DETECTED, HEARTRATE_ABNORMAL, TEMPERATURE_ABNORMAL, BAND_FALL_DETECTED, BAND_DISCONNECTED, ENV_THRESHOLD_EXCEEDED, DEVICE_OFFLINE, DEVICE_ONLINE, NORMAL_RESTORED, SYSTEM_ALERT |
| `risk_level` | CRITICAL, WARNING, NORMAL |
| `device_type` | IP_CAMERA, SMART_BAND, ENV_SENSOR, FIRE_CONTACT, ALARM_DEVICE, NVR |
| `device_status` | CONNECTED, DISCONNECTED, ERROR, RECONNECTING |
| `event_state` | ACTIVE, ACKNOWLEDGED, ARCHIVED |
| `action` (alarm) | SIREN_ON, LIGHT_ON, ALL_ON, ALL_OFF |
| `priority` (cloud queue) | HIGH, NORMAL, LOW |

---

## 3. Completeness Rules

### 3.1 Required Fields per Message Type

| Message/Stream | Required Fields |
|----------------|-----------------|
| Canonical Event | event_id, site_id, device_id, event_type, risk_level, timestamp, event_state |
| stream:ds-events | event_id, site_id, source_id, device_id, event_type, timestamp, model_version, inference.pgie, inference.tracker |
| stream:sensors | event_id, site_id, device_id, event_type, timestamp, data_type, value, source |
| stream:alarms | event_id, site_id, risk_level, action, timestamp, source_event_type |
| stream:dashboard | event_id, site_id, device_id, event_type, risk_level, timestamp, event_state, context |
| stream:cloud-queue | event_id, site_id, device_id, event_type, risk_level, timestamp, idempotency_key, priority |
| stream:clip-trigger | event_id, site_id, device_id, trigger_ts, pre_sec, post_sec |
| MQTT events | event_id, site_id, device_id, event_type, risk_level, timestamp, context_summary, idempotency_key |
| MQTT status | site_id, timestamp, edge_status, deepstream_fps, gpu_utilization, active_cameras, active_bands, pending_cloud_events |

### 3.2 Conditional Required Fields

| Condition | Required Fields |
|-----------|-----------------|
| event_type ∈ {Vision AI events} | confidence, model_version |
| event_type ∈ {SMART_BAND events} | worker_id |
| event_type = ENV_THRESHOLD_EXCEEDED | context.sensor_snapshot |


---

## 4. Consistency Rules

| Rule ID | Description | Validation |
|---------|-------------|------------|
| C-001 | risk_level matches event_type | FALL_DETECTED, COLLAPSE_DETECTED, FIRE_DETECTED → CRITICAL |
| C-002 | device_id prefix matches device_type | CAM-* → IP_CAMERA, BAND-* → SMART_BAND, etc. |
| C-003 | idempotency_key format | Must equal `{site_id}:{event_id}` |
| C-004 | priority matches risk_level | CRITICAL→HIGH, WARNING→NORMAL, NORMAL→LOW |
| C-005 | event_state initial value | New events must start as `ACTIVE` |
| C-006 | confidence range | 0.0 ≤ confidence ≤ 1.0 |
| C-007 | gpu_utilization range | 0.0 ≤ gpu_utilization ≤ 1.0 |
| C-008 | pre_sec / post_sec | Must be positive integers (default 30) |
| C-009 | timestamp ordering | Event timestamp ≤ alarm/dashboard/cloud timestamp |

---

## 5. Boundary Test Cases

### 5.1 event_id Format Tests

| Test Case | Input | Expected |
|-----------|-------|----------|
| Valid format | `EVT-20250519120000-001` | ✅ Pass |
| Missing prefix | `20250519120000-001` | ❌ Fail |
| Wrong separator | `EVT_20250519120000_001` | ❌ Fail |
| Short timestamp | `EVT-2025051912-001` | ❌ Fail |
| Short sequence | `EVT-20250519120000-01` | ❌ Fail |
| Long sequence | `EVT-20250519120000-0001` | ❌ Fail |
| Non-numeric timestamp | `EVT-2025051912000A-001` | ❌ Fail |
| Empty string | `` | ❌ Fail |
| Null | `null` | ❌ Fail |

### 5.2 device_id Format Tests

| Test Case | Input | Expected |
|-----------|-------|----------|
| Valid CAM | `CAM-001` | ✅ Pass |
| Valid BAND | `BAND-012` | ✅ Pass |
| Valid ENV | `ENV-003` | ✅ Pass |
| Valid FIRE | `FIRE-001` | ✅ Pass |
| Valid NVR | `NVR-001` | ✅ Pass |
| Valid ALARM | `ALARM-001` | ✅ Pass |
| Invalid prefix | `CAMERA-001` | ❌ Fail |
| Short number | `CAM-01` | ❌ Fail |
| Long number | `CAM-0001` | ❌ Fail |
| Lowercase | `cam-001` | ❌ Fail |
| No prefix | `001` | ❌ Fail |
| Extra dash | `CAM--001` | ❌ Fail |

### 5.3 Confidence Boundary Tests

| Test Case | Input | Expected |
|-----------|-------|----------|
| Minimum valid | `0.0` | ✅ Pass |
| Maximum valid | `1.0` | ✅ Pass |
| Mid-range | `0.5` | ✅ Pass |
| Below minimum | `-0.01` | ❌ Fail |
| Above maximum | `1.01` | ❌ Fail |
| High precision | `0.999999` | ✅ Pass |

### 5.4 Timestamp Boundary Tests

| Test Case | Input | Expected |
|-----------|-------|----------|
| Valid UTC | `2025-05-19T12:00:00.123Z` | ✅ Pass |
| No milliseconds | `2025-05-19T12:00:00Z` | ❌ Fail (must have ms) |
| Non-UTC timezone | `2025-05-19T12:00:00.123+09:00` | ❌ Fail |
| Future timestamp (>5s) | `2099-01-01T00:00:00.000Z` | ❌ Fail |
| Invalid date | `2025-13-45T99:99:99.999Z` | ❌ Fail |
| Empty string | `` | ❌ Fail |


---

## 6. Automated Validation Approach

### 6.1 Technology Stack

| Layer | Tool | Purpose |
|-------|------|---------|
| Schema Definition | JSON Schema (Draft 2020-12) | Declarative schema definition |
| Python Validation | Pydantic v2 | Runtime validation + type safety |
| Test Framework | pytest | Unit/integration test execution |
| CI Runner | GitHub Actions | Automated test pipeline |

### 6.2 Pydantic Model Example

```python
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
import re

class SafetyEvent(BaseModel):
    event_id: str = Field(..., pattern=r"^EVT-\d{14}-\d{3}$")
    site_id: str = Field(..., pattern=r"^SITE-\d{3}$")
    device_id: str = Field(..., pattern=r"^(CAM|BAND|ENV|FIRE|NVR|ALARM)-\d{3}$")
    event_type: str = Field(...)
    risk_level: str = Field(..., pattern=r"^(CRITICAL|WARNING|NORMAL)$")
    timestamp: str = Field(...)
    event_state: str = Field(..., pattern=r"^(ACTIVE|ACKNOWLEDGED|ARCHIVED)$")
    
    # Platform 1.0 optional
    worker_id: Optional[str] = Field(None, pattern=r"^WKR-\d{4}$")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    model_version: Optional[str] = Field(
        None, pattern=r"^v\d+\.\d+\.\d+-(tao|pretrained|custom)-(ds|cloud)$"
    )
    
    # Platform 2.0 reserved
    feedback_type: Optional[str] = None
    activity_index_history: Optional[list] = None
    baseline_profile: Optional[dict] = None
    
    # Platform 3.0 reserved
    reanalysis_result: Optional[dict] = None
    audit_hash: Optional[str] = None
    rag_reference: Optional[dict] = None

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v: str) -> str:
        pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$"
        if not re.match(pattern, v):
            raise ValueError("Timestamp must be ISO 8601 UTC with milliseconds")
        return v

    @field_validator("event_type")
    @classmethod
    def validate_event_type(cls, v: str) -> str:
        valid_types = {
            "FALL_DETECTED", "COLLAPSE_DETECTED", "ZONE_INTRUSION",
            "STILLNESS_DETECTED", "HAZARDOUS_ACTION", "FIRE_DETECTED",
            "HEARTRATE_ABNORMAL", "TEMPERATURE_ABNORMAL", "BAND_FALL_DETECTED",
            "BAND_DISCONNECTED", "ENV_THRESHOLD_EXCEEDED", "DEVICE_OFFLINE",
            "DEVICE_ONLINE", "NORMAL_RESTORED", "SYSTEM_ALERT"
        }
        if v not in valid_types:
            raise ValueError(f"Invalid event_type: {v}")
        return v
```

### 6.3 JSON Schema Example

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "safety-event-v1.0",
  "type": "object",
  "required": ["event_id", "site_id", "device_id", "event_type", "risk_level", "timestamp", "event_state"],
  "properties": {
    "event_id": {
      "type": "string",
      "pattern": "^EVT-\\d{14}-\\d{3}$"
    },
    "site_id": {
      "type": "string",
      "pattern": "^SITE-\\d{3}$"
    },
    "device_id": {
      "type": "string",
      "pattern": "^(CAM|BAND|ENV|FIRE|NVR|ALARM)-\\d{3}$"
    },
    "event_type": {
      "type": "string",
      "enum": [
        "FALL_DETECTED", "COLLAPSE_DETECTED", "ZONE_INTRUSION",
        "STILLNESS_DETECTED", "HAZARDOUS_ACTION", "FIRE_DETECTED",
        "HEARTRATE_ABNORMAL", "TEMPERATURE_ABNORMAL", "BAND_FALL_DETECTED",
        "BAND_DISCONNECTED", "ENV_THRESHOLD_EXCEEDED", "DEVICE_OFFLINE",
        "DEVICE_ONLINE", "NORMAL_RESTORED", "SYSTEM_ALERT"
      ]
    },
    "risk_level": {
      "type": "string",
      "enum": ["CRITICAL", "WARNING", "NORMAL"]
    },
    "timestamp": {
      "type": "string",
      "pattern": "^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}\\.\\d{3}Z$"
    },
    "event_state": {
      "type": "string",
      "enum": ["ACTIVE", "ACKNOWLEDGED", "ARCHIVED"]
    },
    "confidence": {
      "type": ["number", "null"],
      "minimum": 0.0,
      "maximum": 1.0
    }
  }
}
```


---

## 7. Integration Test: Redis → Validate

### Test Flow

```
[Test Publisher] → Redis Stream → [Consumer] → [Schema Validator] → [Assert]
```

### Test Scenarios

| Test ID | Scenario | Expected |
|---------|----------|----------|
| IT-001 | Publish valid FALL_DETECTED to stream:ds-events | Consumer processes, validation passes |
| IT-002 | Publish invalid event_id format | Consumer rejects, dead-letter queue |
| IT-003 | Publish missing required field | Consumer rejects, error logged |
| IT-004 | Publish CRITICAL event → verify alarm triggered | stream:alarms receives message |
| IT-005 | Publish event → verify dashboard message | stream:dashboard receives formatted message |
| IT-006 | Publish event → verify cloud queue | stream:cloud-queue with correct priority |
| IT-007 | Publish Vision AI event without confidence | Validation fails |
| IT-008 | Publish BAND event without worker_id | Validation fails |
| IT-009 | Publish 1000 events rapidly | All processed, no data loss |
| IT-010 | Consumer crash and recovery | Pending messages re-claimed |

### Integration Test Code Structure

```python
import pytest
import redis
import json
from schema_validator import SafetyEvent

@pytest.fixture
def redis_client():
    return redis.Redis(host="localhost", port=6379, decode_responses=True)

class TestRedisSchemaValidation:
    def test_valid_fall_event_passes_validation(self, redis_client):
        """IT-001: Valid FALL_DETECTED event passes schema validation"""
        event = {
            "event_id": "EVT-20250519120000-001",
            "site_id": "SITE-001",
            "source_id": "pipeline-0",
            "device_id": "CAM-001",
            "event_type": "FALL_DETECTED",
            "timestamp": "2025-05-19T12:00:00.123Z",
            "model_version": "v1.0.0-tao-ds",
            "inference": json.dumps({
                "pgie": {
                    "class_id": 2,
                    "confidence": 0.92,
                    "label": "fall",
                    "bbox": {"x": 0.35, "y": 0.45, "w": 0.15, "h": 0.20}
                },
                "tracker": {"object_id": 42, "age_frames": 15}
            })
        }
        redis_client.xadd("stream:ds-events", event)
        # Consumer validates and processes
        
    def test_invalid_event_id_rejected(self, redis_client):
        """IT-002: Invalid event_id format is rejected"""
        event = {
            "event_id": "INVALID-FORMAT",
            "site_id": "SITE-001",
            "device_id": "CAM-001",
            "event_type": "FALL_DETECTED",
            "timestamp": "2025-05-19T12:00:00.123Z",
        }
        # Should fail validation
        with pytest.raises(ValueError):
            SafetyEvent(**event)
```


---

## 8. CI Integration Plan

### 8.1 GitHub Actions Workflow

```yaml
name: Schema Validation

on:
  push:
    paths:
      - 'packages/sdk-common/**'
      - 'packages/sdk-ai-event/**'
      - 'docs/*-schema.md'
  pull_request:
    paths:
      - 'packages/sdk-common/**'
      - 'packages/sdk-ai-event/**'

jobs:
  schema-validation:
    runs-on: ubuntu-latest
    services:
      redis:
        image: redis:7
        ports:
          - 6379:6379
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install pydantic pytest redis jsonschema
      - name: Run format validation tests
        run: pytest tests/schema/ -m "format" -v
      - name: Run completeness tests
        run: pytest tests/schema/ -m "completeness" -v
      - name: Run consistency tests
        run: pytest tests/schema/ -m "consistency" -v
      - name: Run boundary tests
        run: pytest tests/schema/ -m "boundary" -v
      - name: Run integration tests
        run: pytest tests/schema/ -m "integration" -v
```

### 8.2 Test Markers

```python
# conftest.py
import pytest

def pytest_configure(config):
    config.addinivalue_line("markers", "format: Format validation tests")
    config.addinivalue_line("markers", "completeness: Completeness tests")
    config.addinivalue_line("markers", "consistency: Consistency tests")
    config.addinivalue_line("markers", "boundary: Boundary value tests")
    config.addinivalue_line("markers", "integration: Integration tests (requires Redis)")
```

### 8.3 CI Stages

| Stage | Trigger | Tests | Duration |
|-------|---------|-------|----------|
| **PR Check** | Pull Request | Format + Completeness + Boundary | ~30s |
| **Merge Check** | Push to main | All categories | ~2min |
| **Nightly** | Cron (daily) | All + Integration + Load | ~10min |

### 8.4 Failure Policy

| Severity | Action |
|----------|--------|
| Format validation fail | ❌ Block PR merge |
| Completeness fail | ❌ Block PR merge |
| Consistency fail | ❌ Block PR merge |
| Boundary fail | ⚠️ Warning (non-blocking for patch) |
| Integration fail | ❌ Block release |
