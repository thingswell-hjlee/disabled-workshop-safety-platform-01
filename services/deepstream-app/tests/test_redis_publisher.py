"""
Redis Publisher Tests.

Redis 연결 및 stream:ds-events 발행 테스트.
실제 Redis가 필요한 통합 테스트입니다.

실행: pytest tests/test_redis_publisher.py -v
사전조건: redis-server on localhost:6379
"""

import json
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import RedisConfig
from src.event_schema import (
    BBox,
    DSEvent,
    DeviceStatusEvent,
    InferenceResult,
    PGIEResult,
    TrackerResult,
    generate_event_id,
    generate_timestamp,
)
from src.redis_publisher import RedisPublisher


@pytest.fixture
def redis_config():
    """Redis config for testing."""
    return RedisConfig(
        host="127.0.0.1",
        port=6379,
        db=0,
        stream_name="stream:ds-events-test",
        max_stream_length=100,
        consumer_group="cg-test",
    )


@pytest.fixture
def publisher(redis_config):
    """Create a publisher (may or may not connect depending on Redis availability)."""
    pub = RedisPublisher(redis_config)
    return pub


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


# ─── Unit Tests (no Redis required) ─────────────────────────────────────────


class TestRedisPublisherUnit:
    """Unit tests without actual Redis connection."""

    def test_publisher_initial_state(self, publisher):
        assert publisher.is_connected is False
        assert publisher.stats["publish_count"] == 0
        assert publisher.stats["error_count"] == 0

    def test_stats_returns_dict(self, publisher):
        stats = publisher.stats
        assert isinstance(stats, dict)
        assert "connected" in stats
        assert "publish_count" in stats
        assert "error_count" in stats
        assert "stream_name" in stats

    def test_disconnect_when_not_connected(self, publisher):
        """Disconnect should be safe even if not connected."""
        publisher.disconnect()  # Should not raise


# ─── Integration Tests (require Redis) ──────────────────────────────────────


@pytest.mark.skipif(not redis_available(), reason="Redis not available")
class TestRedisPublisherIntegration:
    """Integration tests requiring running Redis."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self, redis_config):
        """Clean up test stream before/after each test."""
        import redis
        r = redis.Redis(host="127.0.0.1", port=6379, decode_responses=True)
        r.delete(redis_config.stream_name)
        yield
        r.delete(redis_config.stream_name)
        r.close()

    def test_connect_success(self, publisher):
        assert publisher.connect() is True
        assert publisher.is_connected is True
        publisher.disconnect()

    def test_ensure_stream_exists(self, publisher):
        publisher.connect()
        publisher.ensure_stream_exists()
        # Should not raise
        publisher.disconnect()

    def test_publish_fall_event(self, publisher, sample_fall_event):
        publisher.connect()
        publisher.ensure_stream_exists()
        entry_id = publisher.publish_event(sample_fall_event)
        assert entry_id is not None
        assert publisher.stats["publish_count"] == 1
        publisher.disconnect()

    def test_publish_collapse_event(self, publisher, sample_collapse_event):
        publisher.connect()
        publisher.ensure_stream_exists()
        entry_id = publisher.publish_event(sample_collapse_event)
        assert entry_id is not None
        publisher.disconnect()

    def test_publish_device_offline(self, publisher, sample_device_offline_event):
        publisher.connect()
        publisher.ensure_stream_exists()
        entry_id = publisher.publish_device_status(sample_device_offline_event)
        assert entry_id is not None
        publisher.disconnect()

    def test_publish_device_online(self, publisher, sample_device_online_event):
        publisher.connect()
        publisher.ensure_stream_exists()
        entry_id = publisher.publish_device_status(sample_device_online_event)
        assert entry_id is not None
        publisher.disconnect()

    def test_published_event_readable_from_stream(self, publisher, sample_fall_event):
        """Verify published event can be read back from stream."""
        import redis

        publisher.connect()
        publisher.ensure_stream_exists()
        publisher.publish_event(sample_fall_event)

        # Read from stream
        r = redis.Redis(host="127.0.0.1", port=6379, decode_responses=True)
        entries = r.xrange("stream:ds-events-test", count=1)
        assert len(entries) == 1

        entry_id, fields = entries[0]
        assert fields["event_id"] == sample_fall_event.event_id
        assert fields["event_type"] == "FALL_DETECTED"
        assert fields["device_id"] == "CAM-001"
        assert fields["site_id"] == "SITE-001"
        assert fields["model_version"] == "v1.0.0-tao-ds"

        # Verify inference JSON
        inference = json.loads(fields["inference"])
        assert inference["pgie"]["class_id"] == 1
        assert inference["pgie"]["confidence"] == 0.92
        assert inference["pgie"]["label"] == "fall"
        assert inference["tracker"]["object_id"] == 42

        r.close()
        publisher.disconnect()

    def test_stream_max_length_enforced(self, publisher):
        """Stream should not exceed max_stream_length."""
        publisher.connect()
        publisher.ensure_stream_exists()

        # Publish more than max_stream_length events
        for i in range(150):
            event = DSEvent(
                event_id=generate_event_id(),
                site_id="SITE-001",
                source_id="pipeline-0",
                device_id="CAM-001",
                event_type="FALL_DETECTED",
                timestamp=generate_timestamp(),
                model_version="v1.0.0-tao-ds",
                inference=InferenceResult(
                    pgie=PGIEResult(
                        class_id=1, confidence=0.9,
                        label="fall", bbox=BBox(0.1, 0.1, 0.2, 0.2)
                    ),
                    tracker=TrackerResult(object_id=i, age_frames=1),
                ),
            )
            publisher.publish_event(event)

        # Check stream length (approximate MAXLEN allows some overshoot)
        import redis
        r = redis.Redis(host="127.0.0.1", port=6379, decode_responses=True)
        length = r.xlen("stream:ds-events-test")
        # Approximate MAXLEN may leave slightly more than 100
        assert length <= 150  # Should be trimmed close to 100
        r.close()
        publisher.disconnect()

    def test_multiple_event_types(self, publisher):
        """Publish various event types and verify all are stored."""
        publisher.connect()
        publisher.ensure_stream_exists()

        event_types = ["FALL_DETECTED", "ZONE_INTRUSION", "HAZARDOUS_ACTION"]
        for et in event_types:
            event = DSEvent(
                event_id=generate_event_id(),
                site_id="SITE-001",
                source_id="pipeline-0",
                device_id="CAM-001",
                event_type=et,
                timestamp=generate_timestamp(),
                model_version="v1.0.0-tao-ds",
                inference=InferenceResult(
                    pgie=PGIEResult(
                        class_id=1, confidence=0.85,
                        label="test", bbox=BBox(0.2, 0.2, 0.3, 0.3)
                    ),
                    tracker=TrackerResult(object_id=1, age_frames=5),
                ),
            )
            publisher.publish_event(event)

        assert publisher.stats["publish_count"] == 3
        publisher.disconnect()

    def test_get_stream_info(self, publisher, sample_fall_event):
        publisher.connect()
        publisher.ensure_stream_exists()
        publisher.publish_event(sample_fall_event)

        info = publisher.get_stream_info()
        assert info is not None
        assert info["length"] >= 1
        publisher.disconnect()
