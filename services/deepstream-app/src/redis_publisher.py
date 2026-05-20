"""
Redis Streams Publisher for DeepStream events.

stream:ds-events에 이벤트를 발행합니다.
- MAXLEN으로 스트림 크기를 제한 (10,000 entries)
- 연결 끊김 시 자동 재연결
- 발행 실패 시 로그 기록 및 재시도
"""

import json
import logging
import time
from typing import Optional

import redis

from .config import RedisConfig
from .event_schema import DSEvent, DeviceStatusEvent

logger = logging.getLogger(__name__)


class RedisPublisher:
    """Redis Streams publisher for DeepStream inference events."""

    def __init__(self, config: RedisConfig):
        self._config = config
        self._client: Optional[redis.Redis] = None
        self._connected = False
        self._publish_count = 0
        self._error_count = 0
        self._last_error: Optional[str] = None

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def stats(self) -> dict:
        """Publisher statistics."""
        return {
            "connected": self._connected,
            "publish_count": self._publish_count,
            "error_count": self._error_count,
            "last_error": self._last_error,
            "stream_name": self._config.stream_name,
        }

    def connect(self) -> bool:
        """Connect to Redis."""
        try:
            self._client = redis.Redis(
                host=self._config.host,
                port=self._config.port,
                db=self._config.db,
                password=self._config.password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
            )
            # Test connection
            self._client.ping()
            self._connected = True
            logger.info(
                f"Connected to Redis at {self._config.host}:{self._config.port}, "
                f"stream: {self._config.stream_name}"
            )
            return True
        except redis.ConnectionError as e:
            self._connected = False
            self._last_error = str(e)
            logger.error(f"Failed to connect to Redis: {e}")
            return False

    def disconnect(self):
        """Disconnect from Redis."""
        if self._client:
            try:
                self._client.close()
            except Exception:
                pass
            self._client = None
            self._connected = False
            logger.info("Disconnected from Redis")

    def ensure_stream_exists(self):
        """Ensure the stream and consumer group exist."""
        if not self._client:
            return

        try:
            # Create consumer group (creates stream if needed)
            self._client.xgroup_create(
                self._config.stream_name,
                self._config.consumer_group,
                id="0",
                mkstream=True,
            )
            logger.info(
                f"Created consumer group '{self._config.consumer_group}' "
                f"on stream '{self._config.stream_name}'"
            )
        except redis.ResponseError as e:
            if "BUSYGROUP" in str(e):
                # Consumer group already exists - OK
                logger.debug(
                    f"Consumer group '{self._config.consumer_group}' already exists"
                )
            else:
                raise

    def publish_event(self, event: DSEvent) -> Optional[str]:
        """
        Publish a DeepStream event to Redis Streams.

        Returns the stream entry ID on success, None on failure.
        """
        if not self._client or not self._connected:
            if not self.connect():
                return None

        try:
            event_dict = event.to_redis_dict()
            entry_id = self._client.xadd(
                self._config.stream_name,
                event_dict,
                maxlen=self._config.max_stream_length,
                approximate=True,
            )
            self._publish_count += 1
            logger.debug(
                f"Published event {event.event_id} to {self._config.stream_name} "
                f"[entry_id={entry_id}]"
            )
            return entry_id
        except redis.ConnectionError as e:
            self._connected = False
            self._error_count += 1
            self._last_error = str(e)
            logger.error(f"Redis connection lost while publishing: {e}")
            return None
        except Exception as e:
            self._error_count += 1
            self._last_error = str(e)
            logger.error(f"Failed to publish event: {e}")
            return None

    def publish_device_status(self, event: DeviceStatusEvent) -> Optional[str]:
        """Publish a device status event to Redis Streams."""
        if not self._client or not self._connected:
            if not self.connect():
                return None

        try:
            event_dict = event.to_redis_dict()
            entry_id = self._client.xadd(
                self._config.stream_name,
                event_dict,
                maxlen=self._config.max_stream_length,
                approximate=True,
            )
            self._publish_count += 1
            logger.debug(
                f"Published device status {event.event_type} for {event.device_id} "
                f"[entry_id={entry_id}]"
            )
            return entry_id
        except redis.ConnectionError as e:
            self._connected = False
            self._error_count += 1
            self._last_error = str(e)
            logger.error(f"Redis connection lost: {e}")
            return None
        except Exception as e:
            self._error_count += 1
            self._last_error = str(e)
            logger.error(f"Failed to publish device status: {e}")
            return None

    def get_stream_info(self) -> Optional[dict]:
        """Get stream info for monitoring."""
        if not self._client or not self._connected:
            return None
        try:
            info = self._client.xinfo_stream(self._config.stream_name)
            return {
                "length": info.get("length", 0),
                "first_entry": info.get("first-entry"),
                "last_entry": info.get("last-entry"),
            }
        except Exception:
            return None
