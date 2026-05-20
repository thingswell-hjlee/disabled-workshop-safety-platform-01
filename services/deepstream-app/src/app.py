"""
DeepStream Application - Main Entry Point.

Platform 1.0 Edge AI 추론 서버의 DeepStream 파이프라인 애플리케이션.
- 카메라 설정 로드
- DeepStream 파이프라인 실행 (또는 mock mode)
- 추론 결과를 event-message-schema 기준으로 변환
- Redis Streams (stream:ds-events)에 이벤트 발행
- 장비 상태 이벤트 발행
- Health check HTTP 서버 제공

Usage:
  # Real mode (requires GPU + DeepStream SDK)
  python -m src.app

  # Mock mode (no GPU required)
  DEEPSTREAM_MOCK_MODE=true python -m src.app
"""

import logging
import signal
import sys
import time

from .config import load_config
from .event_schema import DSEvent, DeviceStatusEvent
from .healthcheck import HealthCheckServer
from .pipeline_manager import PipelineManager
from .redis_publisher import RedisPublisher

logger = logging.getLogger(__name__)


class DeepStreamApp:
    """Main DeepStream application orchestrator."""

    def __init__(self):
        self._config = load_config()
        self._publisher = RedisPublisher(self._config.redis)
        self._pipeline = PipelineManager(self._config)
        self._healthcheck: HealthCheckServer = None
        self._running = False

        # Wire up callbacks
        self._pipeline.set_inference_callback(self._on_inference)
        self._pipeline.set_status_callback(self._on_device_status)

    def start(self):
        """Start the application."""
        self._setup_logging()
        logger.info("=" * 60)
        logger.info("DeepStream 8-Channel Safety Pipeline")
        logger.info(f"  Site ID: {self._config.site_id}")
        logger.info(f"  Mock Mode: {self._config.mock_mode}")
        logger.info(f"  Cameras: {len(self._config.cameras)}")
        logger.info(f"  Model Version: {self._config.model.model_version}")
        logger.info(f"  Redis: {self._config.redis.host}:{self._config.redis.port}")
        logger.info(f"  Stream: {self._config.redis.stream_name}")
        logger.info(f"  Healthcheck Port: {self._config.healthcheck_port}")
        logger.info("=" * 60)

        # Connect to Redis
        if not self._publisher.connect():
            logger.error("Failed to connect to Redis. Retrying in 5s...")
            time.sleep(5)
            if not self._publisher.connect():
                logger.error("Cannot connect to Redis. Exiting.")
                sys.exit(1)

        # Ensure stream exists
        self._publisher.ensure_stream_exists()

        # Start health check server
        self._healthcheck = HealthCheckServer(
            port=self._config.healthcheck_port,
            health_provider=self._get_health_data,
        )
        self._healthcheck.start()

        # Start pipeline
        self._pipeline.start()
        self._running = True

        logger.info("Application started successfully")

    def stop(self):
        """Stop the application gracefully."""
        logger.info("Shutting down...")
        self._running = False
        self._pipeline.stop()
        if self._healthcheck:
            self._healthcheck.stop()
        self._publisher.disconnect()
        logger.info("Application stopped")

    def run_forever(self):
        """Run until interrupted."""
        self.start()

        # Setup signal handlers
        def signal_handler(sig, frame):
            logger.info(f"Received signal {sig}")
            self.stop()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        try:
            while self._running:
                time.sleep(1.0)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

    # ─── Callbacks ───────────────────────────────────────────────────────────

    def _on_inference(self, event: DSEvent):
        """Handle inference result from pipeline."""
        entry_id = self._publisher.publish_event(event)
        if entry_id:
            logger.info(
                f"[{event.device_id}] {event.event_type} "
                f"confidence={event.inference.pgie.confidence:.2f} "
                f"tracker_id={event.inference.tracker.object_id}"
            )
        else:
            logger.warning(
                f"Failed to publish event {event.event_id} - "
                f"Redis may be disconnected"
            )

    def _on_device_status(self, event: DeviceStatusEvent):
        """Handle device status change."""
        entry_id = self._publisher.publish_device_status(event)
        if entry_id:
            logger.info(
                f"[{event.device_id}] {event.event_type}"
            )
        else:
            logger.warning(
                f"Failed to publish status event {event.event_id}"
            )

    # ─── Health Data ─────────────────────────────────────────────────────────

    def _get_health_data(self) -> dict:
        """Provide health data for the healthcheck server."""
        redis_stats = self._publisher.stats
        camera_statuses = self._pipeline.get_camera_statuses()

        pipeline_healthy = self._pipeline.is_running
        redis_healthy = redis_stats["connected"]
        cameras_ok = self._pipeline.active_cameras > 0

        overall_healthy = pipeline_healthy and redis_healthy

        return {
            "status": "healthy" if overall_healthy else "unhealthy",
            "site_id": self._config.site_id,
            "mock_mode": self._config.mock_mode,
            "model_version": self._config.model.model_version,
            "pipeline": {
                "running": pipeline_healthy,
                "active_cameras": self._pipeline.active_cameras,
                "total_cameras": self._pipeline.total_cameras,
                "uptime_sec": self._pipeline.uptime_sec,
            },
            "redis": redis_stats,
            "cameras": camera_statuses,
        }

    # ─── Logging ─────────────────────────────────────────────────────────────

    def _setup_logging(self):
        """Configure logging."""
        log_level = getattr(logging, self._config.log_level.upper(), logging.INFO)
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        # Reduce noise from other libraries
        logging.getLogger("urllib3").setLevel(logging.WARNING)


def main():
    """Application entry point."""
    app = DeepStreamApp()
    app.run_forever()


if __name__ == "__main__":
    main()
