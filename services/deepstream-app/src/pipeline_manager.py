"""
DeepStream Pipeline Manager.

NVIDIA DeepStream SDK 기반 멀티채널 RTSP 파이프라인 관리.
- 1채널 → 4채널 → 8채널 확장 지원
- 카메라 연결 끊김/재연결 자동 처리
- 추론 결과 콜백으로 이벤트 변환

실제 DeepStream SDK가 없는 환경에서는 mock mode로 동작합니다.
"""

import logging
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional

from .config import AppConfig, CameraConfig
from .event_schema import (
    BBox,
    CLASS_EVENT_MAP,
    DSEvent,
    DeviceStatusEvent,
    InferenceResult,
    PGIEResult,
    TrackerResult,
    generate_event_id,
    generate_timestamp,
)

logger = logging.getLogger(__name__)


class CameraState(Enum):
    """Camera connection state."""
    CONNECTED = "CONNECTED"
    DISCONNECTED = "DISCONNECTED"
    RECONNECTING = "RECONNECTING"
    ERROR = "ERROR"


@dataclass
class CameraStatus:
    """Runtime camera status."""
    camera_id: str
    device_id: str
    state: CameraState = CameraState.DISCONNECTED
    pipeline_index: int = 0
    frames_processed: int = 0
    last_frame_time: float = 0.0
    reconnect_attempts: int = 0
    last_error: Optional[str] = None
    connected_at: Optional[float] = None
    disconnected_at: Optional[float] = None


class PipelineManager:
    """
    Manages DeepStream multi-source RTSP pipeline.

    In real mode: Uses GStreamer/DeepStream to process RTSP streams.
    In mock mode: Simulates pipeline operation without GPU/DeepStream.
    """

    def __init__(self, config: AppConfig):
        self._config = config
        self._running = False
        self._cameras: Dict[str, CameraStatus] = {}
        self._on_inference_callback: Optional[Callable] = None
        self._on_status_callback: Optional[Callable] = None
        self._pipeline_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._start_time: float = 0.0

        # Initialize camera status
        for cam in config.cameras:
            if cam.enabled:
                self._cameras[cam.camera_id] = CameraStatus(
                    camera_id=cam.camera_id,
                    device_id=cam.device_id,
                    pipeline_index=cam.pipeline_index,
                )

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def active_cameras(self) -> int:
        """Number of currently connected cameras."""
        return sum(
            1 for s in self._cameras.values()
            if s.state == CameraState.CONNECTED
        )

    @property
    def total_cameras(self) -> int:
        """Total configured cameras."""
        return len(self._cameras)

    @property
    def uptime_sec(self) -> int:
        """Pipeline uptime in seconds."""
        if self._start_time == 0:
            return 0
        return int(time.time() - self._start_time)

    def set_inference_callback(self, callback: Callable[[DSEvent], None]):
        """Set callback for inference results."""
        self._on_inference_callback = callback

    def set_status_callback(self, callback: Callable[[DeviceStatusEvent], None]):
        """Set callback for device status changes."""
        self._on_status_callback = callback

    def get_camera_statuses(self) -> Dict[str, dict]:
        """Get all camera statuses."""
        result = {}
        with self._lock:
            for cam_id, status in self._cameras.items():
                result[cam_id] = {
                    "camera_id": status.camera_id,
                    "device_id": status.device_id,
                    "state": status.state.value,
                    "pipeline_index": status.pipeline_index,
                    "frames_processed": status.frames_processed,
                    "reconnect_attempts": status.reconnect_attempts,
                    "last_error": status.last_error,
                }
        return result

    def start(self):
        """Start the pipeline (mock or real)."""
        if self._running:
            logger.warning("Pipeline already running")
            return

        self._running = True
        self._start_time = time.time()

        if self._config.mock_mode:
            logger.info("Starting pipeline in MOCK mode")
            self._pipeline_thread = threading.Thread(
                target=self._mock_pipeline_loop,
                daemon=True,
                name="mock-pipeline",
            )
        else:
            logger.info("Starting DeepStream pipeline (real mode)")
            self._pipeline_thread = threading.Thread(
                target=self._deepstream_pipeline_loop,
                daemon=True,
                name="deepstream-pipeline",
            )

        self._pipeline_thread.start()

        # Emit DEVICE_ONLINE for all cameras
        self._emit_all_cameras_online()

    def stop(self):
        """Stop the pipeline."""
        if not self._running:
            return

        logger.info("Stopping pipeline...")
        self._running = False

        # Emit DEVICE_OFFLINE for all cameras
        self._emit_all_cameras_offline()

        if self._pipeline_thread:
            self._pipeline_thread.join(timeout=10)
            self._pipeline_thread = None

        self._start_time = 0.0
        logger.info("Pipeline stopped")

    def simulate_camera_disconnect(self, camera_id: str):
        """Simulate a camera disconnection (for testing)."""
        if camera_id in self._cameras:
            self._handle_camera_disconnect(camera_id, "Simulated disconnect")

    def simulate_camera_reconnect(self, camera_id: str):
        """Simulate a camera reconnection (for testing)."""
        if camera_id in self._cameras:
            self._handle_camera_reconnect(camera_id)

    # ─── Private Methods ─────────────────────────────────────────────────────

    def _emit_all_cameras_online(self):
        """Emit DEVICE_ONLINE events for all enabled cameras."""
        for cam_id, status in self._cameras.items():
            status.state = CameraState.CONNECTED
            status.connected_at = time.time()
            self._emit_device_status(cam_id, "DEVICE_ONLINE")

    def _emit_all_cameras_offline(self):
        """Emit DEVICE_OFFLINE events for all connected cameras."""
        for cam_id, status in self._cameras.items():
            if status.state == CameraState.CONNECTED:
                status.state = CameraState.DISCONNECTED
                status.disconnected_at = time.time()
                self._emit_device_status(cam_id, "DEVICE_OFFLINE")

    def _handle_camera_disconnect(self, camera_id: str, reason: str = ""):
        """Handle camera disconnection."""
        with self._lock:
            if camera_id not in self._cameras:
                return
            status = self._cameras[camera_id]
            status.state = CameraState.DISCONNECTED
            status.disconnected_at = time.time()
            status.reconnect_attempts += 1
            status.last_error = reason

        logger.warning(
            f"Camera {camera_id} disconnected: {reason} "
            f"(attempt {status.reconnect_attempts})"
        )
        self._emit_device_status(camera_id, "DEVICE_OFFLINE")

    def _handle_camera_reconnect(self, camera_id: str):
        """Handle camera reconnection."""
        with self._lock:
            if camera_id not in self._cameras:
                return
            status = self._cameras[camera_id]
            status.state = CameraState.CONNECTED
            status.connected_at = time.time()
            status.last_error = None

        logger.info(f"Camera {camera_id} reconnected")
        self._emit_device_status(camera_id, "DEVICE_ONLINE")

    def _emit_device_status(self, camera_id: str, event_type: str):
        """Emit a device status event."""
        if not self._on_status_callback:
            return

        status = self._cameras.get(camera_id)
        if not status:
            return

        event = DeviceStatusEvent(
            event_id=generate_event_id(),
            site_id=self._config.site_id,
            source_id=f"pipeline-{status.pipeline_index}",
            device_id=status.device_id,
            event_type=event_type,
            timestamp=generate_timestamp(),
            model_version=self._config.model.model_version,
        )

        try:
            self._on_status_callback(event)
        except Exception as e:
            logger.error(f"Error in status callback: {e}")

    def _emit_inference_event(
        self,
        camera_id: str,
        class_id: int,
        confidence: float,
        bbox: BBox,
        tracker_id: int,
        age_frames: int,
    ):
        """Create and emit an inference event."""
        if not self._on_inference_callback:
            return

        status = self._cameras.get(camera_id)
        if not status:
            return

        # Map class_id to event_type and risk_level
        class_info = CLASS_EVENT_MAP.get(class_id)
        if not class_info:
            return

        label, event_type, risk_level = class_info

        # Skip normal person detection (class_id=0) unless needed
        if class_id == 0:
            return

        event = DSEvent(
            event_id=generate_event_id(),
            site_id=self._config.site_id,
            source_id=f"pipeline-{status.pipeline_index}",
            device_id=status.device_id,
            event_type=event_type,
            timestamp=generate_timestamp(),
            model_version=self._config.model.model_version,
            inference=InferenceResult(
                pgie=PGIEResult(
                    class_id=class_id,
                    confidence=confidence,
                    label=label,
                    bbox=bbox,
                ),
                tracker=TrackerResult(
                    object_id=tracker_id,
                    age_frames=age_frames,
                ),
            ),
        )

        try:
            self._on_inference_callback(event)
        except Exception as e:
            logger.error(f"Error in inference callback: {e}")

    # ─── Mock Pipeline ───────────────────────────────────────────────────────

    def _mock_pipeline_loop(self):
        """Mock pipeline loop - generates synthetic inference events."""
        import random

        logger.info(
            f"Mock pipeline started with {len(self._cameras)} cameras, "
            f"interval={self._config.mock_event_interval_sec}s"
        )

        tracker_counter = 0
        frame_counter = 0

        while self._running:
            time.sleep(self._config.mock_event_interval_sec)

            if not self._running:
                break

            # Pick a random connected camera
            connected = [
                cam_id for cam_id, s in self._cameras.items()
                if s.state == CameraState.CONNECTED
            ]
            if not connected:
                continue

            camera_id = random.choice(connected)
            status = self._cameras[camera_id]
            status.frames_processed += 1
            status.last_frame_time = time.time()
            frame_counter += 1

            # Generate a random detection event
            # Weighted: fall=30%, collapse=10%, fire=5%, intrusion=30%, hazardous=25%
            weights = [0.30, 0.10, 0.05, 0.30, 0.25]
            class_ids = [1, 2, 3, 4, 5]
            class_id = random.choices(class_ids, weights=weights, k=1)[0]

            confidence = random.uniform(0.55, 0.98)
            bbox = BBox(
                x=random.uniform(0.1, 0.7),
                y=random.uniform(0.1, 0.7),
                w=random.uniform(0.05, 0.3),
                h=random.uniform(0.05, 0.4),
            )

            tracker_counter += 1

            self._emit_inference_event(
                camera_id=camera_id,
                class_id=class_id,
                confidence=confidence,
                bbox=bbox,
                tracker_id=tracker_counter % 1000,
                age_frames=random.randint(1, 300),
            )

        logger.info("Mock pipeline stopped")

    # ─── Real DeepStream Pipeline ────────────────────────────────────────────

    def _deepstream_pipeline_loop(self):
        """
        Real DeepStream pipeline loop.

        Requires NVIDIA DeepStream SDK and GPU.
        This is the integration point for actual GStreamer/DeepStream pipeline.
        """
        try:
            # Check if DeepStream is available
            import gi
            gi.require_version("Gst", "1.0")
            from gi.repository import Gst
            Gst.init(None)

            logger.info("GStreamer initialized successfully")
            # TODO: Full DeepStream pipeline implementation
            # For Platform 1.0, the actual pipeline will be configured via
            # DeepStream config files and launched as a subprocess or via
            # python bindings.
            self._run_deepstream_native()

        except ImportError:
            logger.error(
                "DeepStream/GStreamer not available. "
                "Set DEEPSTREAM_MOCK_MODE=true for testing without GPU."
            )
            self._running = False
        except Exception as e:
            logger.error(f"DeepStream pipeline error: {e}")
            self._running = False

    def _run_deepstream_native(self):
        """
        Run native DeepStream pipeline.

        Uses deepstream-app or Python bindings to process multi-source RTSP.
        Platform 1.0: Configured via deepstream_config_*.txt files.
        """
        # This will be the actual DeepStream integration point.
        # For now, log that real mode requires proper setup.
        logger.info(
            "DeepStream native pipeline would be initialized here. "
            "Requires NVIDIA GPU + DeepStream SDK 6.x/7.x. "
            "Use config files in services/deepstream-app/configs/"
        )

        # Keep thread alive while running
        while self._running:
            time.sleep(1.0)
