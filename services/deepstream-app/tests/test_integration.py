"""
Integration Tests - End-to-End Mock Pipeline → Redis.

Mock 모드 파이프라인이 이벤트를 생성하고 Redis Stream에 발행하는 전체 흐름을 검증합니다.

사전조건: redis-server on localhost:6379
실행: pytest tests/test_integration.py -v -m integration
"""

import json
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import AppConfig, CameraConfig, ModelConfig, PipelineConfig, RedisConfig
from src.event_schema import (
    DSEvent,
    DeviceStatusEvent,
    generate_event_id,
    generate_timestamp,
    validate_ds_event,
)
from src.pipeline_manager import PipelineManager
from src.redis_publisher import RedisPublisher


def redis_available():
    """Check if Redis is available."""
    try:
        import redis
        r = redis.Redis(host="127.0.0.1", port=6379, socket_connect_timeout=1)
        r.ping()
        r.close()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not redis_available(), reason="Redis not available"
)


@pytest.fixture
def integration_config():
    """Integration test config."""
    cameras = [
        CameraConfig(
            camera_id=f"CAM-{i+1:03d}",
            device_id=f"CAM-{i+1:03d}",
            name=f"Test Camera {i+1}",
            rtsp_url=f"rtsp://192.168.1.{101+i}:554/stream1",
            enabled=True,
            pipeline_index=i,
        )
        for i in range(4)
    ]

    return AppConfig(
        site_id="SITE-001",
        mock_mode=True,
        mock_event_interval_sec=0.1,
        healthcheck_port=18011,
        cameras=cameras,
        redis=RedisConfig(
            host="127.0.0.1",
            port=6379,
            stream_name="stream:ds-events-integration-test",
            max_stream_length=1000,
            consumer_group="cg-integration-test",
        ),
        model=ModelConfig(model_version="v1.0.0-tao-ds"),
        pipeline=PipelineConfig(max_channels=4),
    )


@pytest.fixture
def redis_client():
    """Redis client for verification."""
    import redis
    r = redis.Redis(host="127.0.0.1", port=6379, decode_responses=True)
    yield r
    r.close()


@pytest.fixture(autouse=True)
def cleanup_stream(redis_client, integration_config):
    """Clean test stream before/after."""
    redis_client.delete(integration_config.redis.stream_name)
    yield
    redis_client.delete(integration_config.redis.stream_name)


class TestEndToEndMockPipeline:
    """End-to-end: mock pipeline → Redis stream → validate schema."""

    def test_mock_pipeline_publishes_to_redis(self, integration_config, redis_client):
        """IT-001: Mock pipeline generates events and publishes to Redis."""
        publisher = RedisPublisher(integration_config.redis)
        assert publisher.connect() is True
        publisher.ensure_stream_exists()

        pipeline = PipelineManager(integration_config)

        published_events = []

        def on_inference(event):
            entry_id = publisher.publish_event(event)
            if entry_id:
                published_events.append(event)

        def on_status(event):
            publisher.publish_device_status(event)

        pipeline.set_inference_callback(on_inference)
        pipeline.set_status_callback(on_status)

        pipeline.start()
        time.sleep(1.0)  # Let mock generate events
        pipeline.stop()
        publisher.disconnect()

        # Should have published events
        assert len(published_events) >= 1

        # Verify events are in Redis
        stream_len = redis_client.xlen(integration_config.redis.stream_name)
        assert stream_len >= 1

    def test_published_events_pass_schema_validation(
        self, integration_config, redis_client
    ):
        """IT-002: All published events pass schema validation."""
        publisher = RedisPublisher(integration_config.redis)
        publisher.connect()
        publisher.ensure_stream_exists()

        pipeline = PipelineManager(integration_config)

        def on_inference(event):
            publisher.publish_event(event)

        def on_status(event):
            publisher.publish_device_status(event)

        pipeline.set_inference_callback(on_inference)
        pipeline.set_status_callback(on_status)
        pipeline.start()
        time.sleep(0.8)
        pipeline.stop()
        publisher.disconnect()

        # Read all events and validate
        entries = redis_client.xrange(integration_config.redis.stream_name)
        assert len(entries) >= 1

        for entry_id, fields in entries:
            errors = validate_ds_event(fields)
            assert errors == [], (
                f"Entry {entry_id} failed validation: {errors}\n"
                f"Fields: {fields}"
            )

    def test_camera_disconnect_event_published(
        self, integration_config, redis_client
    ):
        """IT-003: Camera disconnect generates DEVICE_OFFLINE in Redis."""
        publisher = RedisPublisher(integration_config.redis)
        publisher.connect()
        publisher.ensure_stream_exists()

        pipeline = PipelineManager(integration_config)

        def on_inference(event):
            publisher.publish_event(event)

        def on_status(event):
            publisher.publish_device_status(event)

        pipeline.set_inference_callback(on_inference)
        pipeline.set_status_callback(on_status)
        pipeline.start()
        time.sleep(0.2)

        # Simulate camera disconnect
        pipeline.simulate_camera_disconnect("CAM-001")
        time.sleep(0.2)
        pipeline.stop()
        publisher.disconnect()

        # Find DEVICE_OFFLINE event in stream
        entries = redis_client.xrange(integration_config.redis.stream_name)
        offline_events = [
            fields for _, fields in entries
            if fields.get("event_type") == "DEVICE_OFFLINE"
            and fields.get("device_id") == "CAM-001"
        ]
        assert len(offline_events) >= 1

    def test_camera_reconnect_event_sequence(
        self, integration_config, redis_client
    ):
        """IT-004: Disconnect → Reconnect produces correct event sequence."""
        publisher = RedisPublisher(integration_config.redis)
        publisher.connect()
        publisher.ensure_stream_exists()

        pipeline = PipelineManager(integration_config)

        def on_inference(event):
            publisher.publish_event(event)

        def on_status(event):
            publisher.publish_device_status(event)

        pipeline.set_inference_callback(on_inference)
        pipeline.set_status_callback(on_status)
        pipeline.start()
        time.sleep(0.2)

        pipeline.simulate_camera_disconnect("CAM-003")
        time.sleep(0.1)
        pipeline.simulate_camera_reconnect("CAM-003")
        time.sleep(0.1)
        pipeline.stop()
        publisher.disconnect()

        # Check event sequence for CAM-003
        entries = redis_client.xrange(integration_config.redis.stream_name)
        cam3_events = [
            fields for _, fields in entries
            if fields.get("device_id") == "CAM-003"
            and fields.get("event_type") in ("DEVICE_ONLINE", "DEVICE_OFFLINE")
        ]

        # Should have: DEVICE_ONLINE (start) → DEVICE_OFFLINE → DEVICE_ONLINE → DEVICE_OFFLINE (stop)
        event_types = [e["event_type"] for e in cam3_events]
        assert "DEVICE_ONLINE" in event_types
        assert "DEVICE_OFFLINE" in event_types

    def test_all_vision_event_types_publishable(
        self, integration_config, redis_client
    ):
        """IT-005: All Vision AI event types can be published correctly."""
        from src.event_schema import BBox, InferenceResult, PGIEResult, TrackerResult

        publisher = RedisPublisher(integration_config.redis)
        publisher.connect()
        publisher.ensure_stream_exists()

        vision_events = [
            ("FALL_DETECTED", 1, "fall"),
            ("COLLAPSE_DETECTED", 2, "collapse"),
            ("FIRE_DETECTED", 3, "fire"),
            ("ZONE_INTRUSION", 4, "intrusion"),
            ("HAZARDOUS_ACTION", 5, "hazardous_action"),
            ("STILLNESS_DETECTED", 0, "stillness"),
        ]

        for event_type, class_id, label in vision_events:
            event = DSEvent(
                event_id=generate_event_id(),
                site_id="SITE-001",
                source_id="pipeline-0",
                device_id="CAM-001",
                event_type=event_type,
                timestamp=generate_timestamp(),
                model_version="v1.0.0-tao-ds",
                inference=InferenceResult(
                    pgie=PGIEResult(
                        class_id=class_id,
                        confidence=0.88,
                        label=label,
                        bbox=BBox(x=0.2, y=0.3, w=0.1, h=0.15),
                    ),
                    tracker=TrackerResult(object_id=10, age_frames=5),
                ),
            )
            entry_id = publisher.publish_event(event)
            assert entry_id is not None, f"Failed to publish {event_type}"

        publisher.disconnect()

        # Verify all in stream
        entries = redis_client.xrange(integration_config.redis.stream_name)
        published_types = {fields["event_type"] for _, fields in entries}
        for event_type, _, _ in vision_events:
            assert event_type in published_types, f"{event_type} not found in stream"
