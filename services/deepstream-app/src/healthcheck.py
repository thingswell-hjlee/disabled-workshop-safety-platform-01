"""
Health Check HTTP Server.

로컬 healthcheck 엔드포인트를 제공합니다.
- GET /health - 전체 시스템 상태
- GET /health/cameras - 카메라 연결 상태
- GET /health/redis - Redis 연결 상태
- GET /health/pipeline - 파이프라인 상태

Docker HEALTHCHECK와 외부 모니터링에서 사용합니다.
"""

import json
import logging
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class HealthCheckHandler(BaseHTTPRequestHandler):
    """HTTP request handler for health checks."""

    # Class-level reference to health data provider
    _get_health_data: Optional[Callable] = None

    def do_GET(self):
        """Handle GET requests."""
        if self.path == "/health":
            self._respond_health()
        elif self.path == "/health/cameras":
            self._respond_cameras()
        elif self.path == "/health/redis":
            self._respond_redis()
        elif self.path == "/health/pipeline":
            self._respond_pipeline()
        else:
            self._respond(404, {"error": "Not found"})

    def _respond_health(self):
        """Full health status."""
        data = self._get_health() if self._get_health_data else {}
        status_code = 200 if data.get("status") == "healthy" else 503
        self._respond(status_code, data)

    def _respond_cameras(self):
        """Camera status only."""
        data = self._get_health() if self._get_health_data else {}
        cameras = data.get("cameras", {})
        self._respond(200, cameras)

    def _respond_redis(self):
        """Redis status only."""
        data = self._get_health() if self._get_health_data else {}
        redis_info = data.get("redis", {})
        status_code = 200 if redis_info.get("connected") else 503
        self._respond(status_code, redis_info)

    def _respond_pipeline(self):
        """Pipeline status only."""
        data = self._get_health() if self._get_health_data else {}
        pipeline = data.get("pipeline", {})
        status_code = 200 if pipeline.get("running") else 503
        self._respond(status_code, pipeline)

    def _respond(self, status_code: int, data: dict):
        """Send JSON response."""
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def _get_health(self) -> dict:
        """Get health data from provider."""
        if self._get_health_data:
            return self._get_health_data()
        return {"status": "unknown"}

    def log_message(self, format, *args):
        """Suppress default HTTP access logs."""
        pass


class HealthCheckServer:
    """Threaded HTTP health check server."""

    def __init__(self, port: int, health_provider: Callable[[], dict]):
        self._port = port
        self._health_provider = health_provider
        self._server: Optional[HTTPServer] = None
        self._thread: Optional[threading.Thread] = None

    def start(self):
        """Start the health check server."""
        # Set the class-level callback
        HealthCheckHandler._get_health_data = self._health_provider

        self._server = HTTPServer(("0.0.0.0", self._port), HealthCheckHandler)
        self._thread = threading.Thread(
            target=self._server.serve_forever,
            daemon=True,
            name="healthcheck-server",
        )
        self._thread.start()
        logger.info(f"Health check server started on port {self._port}")

    def stop(self):
        """Stop the health check server."""
        if self._server:
            self._server.shutdown()
            self._server = None
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None
        logger.info("Health check server stopped")
