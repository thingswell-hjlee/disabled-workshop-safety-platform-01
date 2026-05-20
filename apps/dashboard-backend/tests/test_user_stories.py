"""
User Story Acceptance Tests (US-AWS-001 ~ US-AWS-005)

PR #21 Integration Test 세션에서 정의된 유저스토리별 Acceptance Criteria를
명시적으로 검증하는 테스트입니다.

실행:
    python3 -m pytest apps/dashboard-backend/tests/test_user_stories.py -v
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch
from pydantic import ValidationError
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.schemas import IoTEventPayload, IoTStatusPayload, EventType, RiskLevel
from src.api import app


def _now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


# ============================================================
# US-AWS-001: Edge 이벤트 수신
# AC: MQTT payload(safety/{site_id}/events)를 수신하고,
#     context_summary, clip_s3_key, idempotency_key 필수 필드 검증 후
#     POST /api/v1/events/ingest로 저장할 수 있어야 한다.
# ============================================================
class TestUSAWS001_EdgeEventReceive:
    """US-AWS-001: Edge 이벤트 수신"""

    def test_mqtt_event_payload_model_exists(self):
        """IoTEventPayload 모델이 MQTT events 토픽 필드를 모두 포함한다."""
        fields = IoTEventPayload.model_fields
        required_fields = [
            "event_id", "site_id", "device_id", "event_type",
            "risk_level", "timestamp", "context_summary", "idempotency_key"
        ]
        for f in required_fields:
            assert f in fields, f"Missing required field: {f}"

    def test_mqtt_status_payload_model_exists(self):
        """IoTStatusPayload 모델이 MQTT status 토픽 필드를 모두 포함한다."""
        fields = IoTStatusPayload.model_fields
        required_fields = [
            "site_id", "timestamp", "edge_status", "deepstream_fps",
            "gpu_utilization", "active_cameras", "active_bands", "pending_cloud_events"
        ]
        for f in required_fields:
            assert f in fields, f"Missing required field: {f}"

    def test_context_summary_is_required(self):
        """context_summary 누락 시 검증 실패."""
        with pytest.raises(ValidationError):
            IoTEventPayload(
                event_id="EVT-20250519120000-001", site_id="SITE-001",
                device_id="FIRE-001", event_type="FIRE_DETECTED",
                risk_level="CRITICAL", timestamp=_now_iso(),
                idempotency_key="SITE-001:EVT-20250519120000-001"
                # context_summary 누락
            )

    def test_ingest_endpoint_exists(self):
        """POST /api/v1/events/ingest 엔드포인트가 존재한다."""
        routes = [(r.path, getattr(r, 'methods', set())) for r in app.routes if hasattr(r, 'path')]
        ingest = [r for r in routes if r[0] == "/api/v1/events/ingest"]
        assert len(ingest) == 1
        assert "POST" in ingest[0][1]

    @pytest.mark.asyncio
    async def test_ingest_validates_payload(self):
        """Ingest API가 잘못된 payload를 422로 거부한다."""
        from httpx import AsyncClient, ASGITransport
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.post("/api/v1/events/ingest", json={
                "event_id": "INVALID",
                "site_id": "WRONG",
            })
        assert response.status_code == 422


# ============================================================
# US-AWS-002: 이벤트 DB 저장
# AC: 검증 통과한 이벤트를 PostgreSQL에 저장하고,
#     idempotency_key 중복 시 ON CONFLICT DO NOTHING으로 처리한다.
#     DDL에 event_id PK, idempotency_key UNIQUE, NOT NULL 제약이 존재해야 한다.
# ============================================================
class TestUSAWS002_EventDBStorage:
    """US-AWS-002: 이벤트 DB 저장"""

    def test_ddl_file_exists(self):
        """PostgreSQL DDL 파일이 존재한다."""
        ddl_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "infra", "aws", "rds", "init-schema.sql"
        )
        assert os.path.exists(ddl_path), f"DDL not found at {ddl_path}"

    def test_ddl_has_events_table(self):
        """DDL에 events 테이블이 정의되어 있다."""
        ddl_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "infra", "aws", "rds", "init-schema.sql"
        )
        with open(ddl_path) as f:
            content = f.read()
        assert "CREATE TABLE IF NOT EXISTS events" in content

    def test_ddl_event_id_primary_key(self):
        """events 테이블에 event_id PRIMARY KEY 제약이 있다."""
        ddl_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "infra", "aws", "rds", "init-schema.sql"
        )
        with open(ddl_path) as f:
            content = f.read()
        assert "event_id" in content and "PRIMARY KEY" in content

    def test_ddl_idempotency_key_unique(self):
        """events 테이블에 idempotency_key UNIQUE 제약이 있다."""
        ddl_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "infra", "aws", "rds", "init-schema.sql"
        )
        with open(ddl_path) as f:
            content = f.read()
        assert "idempotency_key" in content and "UNIQUE" in content

    def test_ddl_not_null_constraints(self):
        """events 테이블에 필수 필드 NOT NULL 제약이 있다."""
        ddl_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "infra", "aws", "rds", "init-schema.sql"
        )
        with open(ddl_path) as f:
            content = f.read()
        # site_id, device_id, event_type, risk_level, timestamp 모두 NOT NULL
        assert "site_id         VARCHAR(10)  NOT NULL" in content
        assert "device_id       VARCHAR(10)  NOT NULL" in content
        assert "event_type      VARCHAR(30)  NOT NULL" in content
        assert "risk_level      VARCHAR(10)  NOT NULL" in content

    def test_crud_on_conflict_do_nothing(self):
        """CRUD insert에 ON CONFLICT DO NOTHING이 구현되어 있다."""
        crud_path = os.path.join(
            os.path.dirname(__file__), "..", "src", "crud.py"
        )
        with open(crud_path) as f:
            content = f.read()
        assert "ON CONFLICT" in content
        assert "DO NOTHING" in content

    def test_crud_returns_duplicate_skipped(self):
        """중복 이벤트 시 'duplicate_skipped' 상태를 반환한다."""
        crud_path = os.path.join(
            os.path.dirname(__file__), "..", "src", "crud.py"
        )
        with open(crud_path) as f:
            content = f.read()
        assert "duplicate_skipped" in content


# ============================================================
# US-AWS-003: 이벤트 목록/상세 API
# AC: GET /api/v1/events (필터, 페이지네이션),
#     GET /api/v1/events/{event_id},
#     POST /api/v1/events/{event_id}/acknowledge,
#     POST /api/v1/events/{event_id}/archive
# ============================================================
class TestUSAWS003_EventListDetailAPI:
    """US-AWS-003: 이벤트 목록/상세 API"""

    def test_event_list_endpoint(self):
        """GET /api/v1/events 엔드포인트가 존재한다."""
        routes = [r.path for r in app.routes if hasattr(r, 'path')]
        assert "/api/v1/events" in routes

    def test_event_detail_endpoint(self):
        """GET /api/v1/events/{event_id} 엔드포인트가 존재한다."""
        routes = [r.path for r in app.routes if hasattr(r, 'path')]
        assert "/api/v1/events/{event_id}" in routes

    def test_event_acknowledge_endpoint(self):
        """POST /api/v1/events/{event_id}/acknowledge 엔드포인트가 존재한다."""
        routes = [(r.path, getattr(r, 'methods', set())) for r in app.routes if hasattr(r, 'path')]
        ack = [r for r in routes if r[0] == "/api/v1/events/{event_id}/acknowledge"]
        assert len(ack) == 1
        assert "POST" in ack[0][1]

    def test_event_archive_endpoint(self):
        """POST /api/v1/events/{event_id}/archive 엔드포인트가 존재한다."""
        routes = [(r.path, getattr(r, 'methods', set())) for r in app.routes if hasattr(r, 'path')]
        archive = [r for r in routes if r[0] == "/api/v1/events/{event_id}/archive"]
        assert len(archive) == 1
        assert "POST" in archive[0][1]

    @pytest.mark.asyncio
    async def test_validate_endpoint_returns_valid_true(self):
        """유효한 이벤트를 /validate/event에 보내면 valid=True 반환."""
        from httpx import AsyncClient, ASGITransport
        transport = ASGITransport(app=app)
        payload = {
            "event_id": "EVT-20250519120000-001",
            "site_id": "SITE-001",
            "device_id": "CAM-001",
            "event_type": "FALL_DETECTED",
            "risk_level": "CRITICAL",
            "confidence": 0.92,
            "model_version": "v1.0.0-tao-ds",
            "timestamp": _now_iso(),
            "context_summary": "Test",
            "idempotency_key": "SITE-001:EVT-20250519120000-001",
        }
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.post("/api/v1/validate/event", json=payload)
        assert response.status_code == 200
        assert response.json()["valid"] is True


# ============================================================
# US-AWS-004: 장비 상태 저장
# AC: GET /api/v1/devices, GET /api/v1/devices/{device_id},
#     PATCH /api/v1/devices/{device_id}/status 존재.
#     DeviceType 6종, DeviceStatus 4종 enum 준수.
# ============================================================
class TestUSAWS004_DeviceStatus:
    """US-AWS-004: 장비 상태 저장"""

    def test_device_list_endpoint(self):
        """GET /api/v1/devices 엔드포인트가 존재한다."""
        routes = [r.path for r in app.routes if hasattr(r, 'path')]
        assert "/api/v1/devices" in routes

    def test_device_detail_endpoint(self):
        """GET /api/v1/devices/{device_id} 엔드포인트가 존재한다."""
        routes = [r.path for r in app.routes if hasattr(r, 'path')]
        assert "/api/v1/devices/{device_id}" in routes

    def test_device_status_update_endpoint(self):
        """PATCH /api/v1/devices/{device_id}/status 엔드포인트가 존재한다."""
        routes = [(r.path, getattr(r, 'methods', set())) for r in app.routes if hasattr(r, 'path')]
        status = [r for r in routes if r[0] == "/api/v1/devices/{device_id}/status"]
        assert len(status) == 1
        assert "PATCH" in status[0][1]

    def test_device_type_enum_has_6_values(self):
        """DeviceType enum이 PR #16 기준 6종을 포함한다."""
        from src.schemas import DeviceType
        expected = {"IP_CAMERA", "SMART_BAND", "ENV_SENSOR", "FIRE_CONTACT", "ALARM_DEVICE", "NVR"}
        actual = {e.value for e in DeviceType}
        assert actual == expected

    def test_device_status_enum_has_4_values(self):
        """DeviceStatus enum이 PR #16 기준 4종을 포함한다."""
        from src.schemas import DeviceStatus
        expected = {"CONNECTED", "DISCONNECTED", "ERROR", "RECONNECTING"}
        actual = {e.value for e in DeviceStatus}
        assert actual == expected

    def test_ddl_has_devices_table(self):
        """DDL에 devices 테이블이 정의되어 있다."""
        ddl_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "infra", "aws", "rds", "init-schema.sql"
        )
        with open(ddl_path) as f:
            content = f.read()
        assert "CREATE TABLE IF NOT EXISTS devices" in content

    def test_ddl_device_type_check_constraint(self):
        """devices 테이블에 device_type CHECK 제약이 있다."""
        ddl_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "infra", "aws", "rds", "init-schema.sql"
        )
        with open(ddl_path) as f:
            content = f.read()
        assert "IP_CAMERA" in content
        assert "SMART_BAND" in content
        assert "ALARM_DEVICE" in content


# ============================================================
# US-AWS-005: MQTT Payload 검증
# AC: 15종 event_type, 3종 risk_level strict validation.
#     C-001 CRITICAL 규칙, C-003 idempotency_key 형식,
#     confidence 범위, timestamp future 거부, model_version 형식.
# ============================================================
class TestUSAWS005_MQTTPayloadValidation:
    """US-AWS-005: MQTT Payload 검증"""

    def test_all_15_event_types_defined(self):
        """PR #16 기준 15종 event_type enum이 정의되어 있다."""
        expected = [
            "FALL_DETECTED", "COLLAPSE_DETECTED", "ZONE_INTRUSION",
            "STILLNESS_DETECTED", "HAZARDOUS_ACTION", "FIRE_DETECTED",
            "HEARTRATE_ABNORMAL", "TEMPERATURE_ABNORMAL",
            "BAND_FALL_DETECTED", "BAND_DISCONNECTED",
            "ENV_THRESHOLD_EXCEEDED", "DEVICE_OFFLINE", "DEVICE_ONLINE",
            "NORMAL_RESTORED", "SYSTEM_ALERT",
        ]
        actual = [e.value for e in EventType]
        assert sorted(actual) == sorted(expected)
        assert len(actual) == 15

    def test_3_risk_levels_defined(self):
        """PR #16 기준 3종 risk_level enum이 정의되어 있다."""
        expected = {"CRITICAL", "WARNING", "NORMAL"}
        actual = {e.value for e in RiskLevel}
        assert actual == expected

    def test_c001_fall_detected_must_be_critical(self):
        """C-001: FALL_DETECTED는 반드시 CRITICAL이어야 한다."""
        with pytest.raises(ValidationError) as exc_info:
            IoTEventPayload(
                event_id="EVT-20250519120000-001", site_id="SITE-001",
                device_id="CAM-001", event_type="FALL_DETECTED",
                risk_level="WARNING", confidence=0.9,
                model_version="v1.0.0-tao-ds", timestamp=_now_iso(),
                context_summary="test",
                idempotency_key="SITE-001:EVT-20250519120000-001"
            )
        assert "CRITICAL" in str(exc_info.value)

    def test_c001_collapse_detected_must_be_critical(self):
        """C-001: COLLAPSE_DETECTED는 반드시 CRITICAL이어야 한다."""
        with pytest.raises(ValidationError):
            IoTEventPayload(
                event_id="EVT-20250519120000-001", site_id="SITE-001",
                device_id="CAM-001", event_type="COLLAPSE_DETECTED",
                risk_level="NORMAL", confidence=0.9,
                model_version="v1.0.0-tao-ds", timestamp=_now_iso(),
                context_summary="test",
                idempotency_key="SITE-001:EVT-20250519120000-001"
            )

    def test_c001_fire_detected_must_be_critical(self):
        """C-001: FIRE_DETECTED는 반드시 CRITICAL이어야 한다."""
        with pytest.raises(ValidationError):
            IoTEventPayload(
                event_id="EVT-20250519120000-001", site_id="SITE-001",
                device_id="FIRE-001", event_type="FIRE_DETECTED",
                risk_level="WARNING", timestamp=_now_iso(),
                context_summary="test",
                idempotency_key="SITE-001:EVT-20250519120000-001"
            )

    def test_c003_idempotency_key_format(self):
        """C-003: idempotency_key는 {site_id}:{event_id} 형식이어야 한다."""
        with pytest.raises(ValidationError) as exc_info:
            IoTEventPayload(
                event_id="EVT-20250519120000-001", site_id="SITE-001",
                device_id="FIRE-001", event_type="FIRE_DETECTED",
                risk_level="CRITICAL", timestamp=_now_iso(),
                context_summary="test",
                idempotency_key="EVT-20250519120000-001"  # site_id prefix 누락
            )
        assert "idempotency_key" in str(exc_info.value)

    def test_c003_idempotency_key_correct_passes(self):
        """C-003: 올바른 idempotency_key 형식은 통과한다."""
        event = IoTEventPayload(
            event_id="EVT-20250519120000-001", site_id="SITE-001",
            device_id="FIRE-001", event_type="FIRE_DETECTED",
            risk_level="CRITICAL", timestamp=_now_iso(),
            context_summary="test",
            idempotency_key="SITE-001:EVT-20250519120000-001"
        )
        assert event.idempotency_key == "SITE-001:EVT-20250519120000-001"

    def test_confidence_range_0_to_1(self):
        """confidence는 0.0~1.0 범위여야 한다."""
        with pytest.raises(ValidationError):
            IoTEventPayload(
                event_id="EVT-20250519120000-001", site_id="SITE-001",
                device_id="CAM-001", event_type="FALL_DETECTED",
                risk_level="CRITICAL", confidence=1.5,
                model_version="v1.0.0-tao-ds", timestamp=_now_iso(),
                context_summary="test",
                idempotency_key="SITE-001:EVT-20250519120000-001"
            )

    def test_timestamp_future_rejected(self):
        """미래 timestamp(+5초 초과)는 거부된다."""
        future = (datetime.now(timezone.utc) + timedelta(minutes=10)).strftime(
            "%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        with pytest.raises(ValidationError) as exc_info:
            IoTEventPayload(
                event_id="EVT-20250519120000-001", site_id="SITE-001",
                device_id="FIRE-001", event_type="FIRE_DETECTED",
                risk_level="CRITICAL", timestamp=future,
                context_summary="test",
                idempotency_key="SITE-001:EVT-20250519120000-001"
            )
        assert "future" in str(exc_info.value)

    def test_model_version_format_validation(self):
        """model_version은 v{M}.{m}.{p}-{tool}-{target} 형식이어야 한다."""
        with pytest.raises(ValidationError) as exc_info:
            IoTEventPayload(
                event_id="EVT-20250519120000-001", site_id="SITE-001",
                device_id="CAM-001", event_type="FALL_DETECTED",
                risk_level="CRITICAL", confidence=0.9,
                model_version="v1.0.0-edge",  # wrong format
                timestamp=_now_iso(), context_summary="test",
                idempotency_key="SITE-001:EVT-20250519120000-001"
            )
        assert "model_version" in str(exc_info.value)

    def test_invalid_event_type_rejected(self):
        """유효하지 않은 event_type은 거부된다."""
        with pytest.raises(ValidationError):
            IoTEventPayload(
                event_id="EVT-20250519120000-001", site_id="SITE-001",
                device_id="CAM-001", event_type="EXPLOSION",
                risk_level="CRITICAL", timestamp=_now_iso(),
                context_summary="test",
                idempotency_key="SITE-001:EVT-20250519120000-001"
            )

    def test_invalid_risk_level_rejected(self):
        """유효하지 않은 risk_level은 거부된다."""
        with pytest.raises(ValidationError):
            IoTEventPayload(
                event_id="EVT-20250519120000-001", site_id="SITE-001",
                device_id="CAM-001", event_type="FALL_DETECTED",
                risk_level="HIGH", confidence=0.9,
                model_version="v1.0.0-tao-ds", timestamp=_now_iso(),
                context_summary="test",
                idempotency_key="SITE-001:EVT-20250519120000-001"
            )
