"""
Pipeline Manager Tests.

Mock mode 파이프라인 동작, 카메라 연결/끊김 이벤트 테스트.
"""

import sys
import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import AppConfig, CameraConfig, ModelConfig, PipelineConfig, RedisConfig
from src.event_schema import DSEvent, DeviceStatusEvent
from src.pipeline_manager import CameraState, PipelineManager


@pytest.fixture
def pipeline_config():
    """Minimal pipeline config for testing."""
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
        mock_event_interval_sec=0.1,  # Fast for testing
        healthcheck_port=18010,
        cameras=cameras,
        redis=RedisConfig(stream_name="stream:ds-events-test"),
        model=ModelConfig(model_version="v1.0.0-tao-ds"),
        pipeline=PipelineConfig(max_channels=4),
    )


@pytest.fixture
def pipeline(pipeline_config):
    """Create pipeline manager."""
    pm = PipelineManager(pipeline_config)
    yield pm
    if pm.is_running:
        pm.stop()


class TestPipelineManagerBasic:
    """Basic pipeline manager tests."""

    def test_initial_state(self, pipeline):
        assert pipeline.is_running is False
        assert pipeline.total_cameras == 4
        assert pipeline.active_cameras == 0
        assert pipeline.uptime_sec == 0

    def test_start_sets_running(self, pipeline):
        inference_cb = MagicMock()
        status_cb = MagicMock()
        pipeline.set_inference_callback(inference_cb)
        pipeline.set_status_callback(status_cb)

        pipeline.start()
        assert pipeline.is_running is True
        time.sleep(0.2)
        assert pipeline.active_cameras == 4  # All cameras should be "online" in mock

        pipeline.stop()
        assert pipeline.is_running is False

    def test_stop_emits_offline_events(self, pipeline):
        status_events = []

        def on_status(event):
            status_events.append(event)

        pipeline.set_status_callback(on_status)
        pipeline.set_inference_callback(MagicMock())
        pipeline.start()
        time.sleep(0.1)

        pipeline.stop()
        time.sleep(0.1)

        # Should have DEVICE_ONLINE events (4 cameras) + DEVICE_OFFLINE events (4 cameras)
        online_events = [e for e in status_events if e.event_type == "DEVICE_ONLINE"]
        offline_events = [e for e in status_events if e.event_type == "DEVICE_OFFLINE"]
        assert len(online_events) == 4
        assert len(offline_events) == 4


class TestCameraDisconnect:
    """Camera disconnect/reconnect event handling."""

    def test_simulate_camera_disconnect(self, pipeline):
        status_events = []

        def on_status(event):
            status_events.append(event)

        pipeline.set_status_callback(on_status)
        pipeline.set_inference_callback(MagicMock())
        pipeline.start()
        time.sleep(0.1)

        # Clear initial DEVICE_ONLINE events
        status_events.clear()

        # Simulate disconnect
        pipeline.simulate_camera_disconnect("CAM-001")
        time.sleep(0.1)

        assert len(status_events) == 1
        assert status_events[0].event_type == "DEVICE_OFFLINE"
        assert status_events[0].device_id == "CAM-001"
        assert status_events[0].site_id == "SITE-001"

        pipeline.stop()

    def test_simulate_camera_reconnect(self, pipeline):
        status_events = []

        def on_status(event):
            status_events.append(event)

        pipeline.set_status_callback(on_status)
        pipeline.set_inference_callback(MagicMock())
        pipeline.start()
        time.sleep(0.1)

        status_events.clear()

        # Disconnect then reconnect
        pipeline.simulate_camera_disconnect("CAM-002")
        time.sleep(0.05)
        pipeline.simulate_camera_reconnect("CAM-002")
        time.sleep(0.05)

        offline_events = [e for e in status_events if e.event_type == "DEVICE_OFFLINE"]
        online_events = [e for e in status_events if e.event_type == "DEVICE_ONLINE"]
        assert len(offline_events) == 1
        assert len(online_events) == 1
        assert offline_events[0].device_id == "CAM-002"
        assert online_events[0].device_id == "CAM-002"

        pipeline.stop()

    def test_camera_statuses_api(self, pipeline):
        pipeline.set_status_callback(MagicMock())
        pipeline.set_inference_callback(MagicMock())
        pipeline.start()
        time.sleep(0.1)

        statuses = pipeline.get_camera_statuses()
        assert len(statuses) == 4
        assert "CAM-001" in statuses
        assert statuses["CAM-001"]["state"] == "CONNECTED"

        pipeline.simulate_camera_disconnect("CAM-001")
        time.sleep(0.05)

        statuses = pipeline.get_camera_statuses()
        assert statuses["CAM-001"]["state"] == "DISCONNECTED"

        pipeline.stop()


class TestMockInferenceEvents:
    """Mock mode inference event generation."""

    def test_mock_generates_events(self, pipeline):
        inference_events = []

        def on_inference(event):
            inference_events.append(event)

        pipeline.set_inference_callback(on_inference)
        pipeline.set_status_callback(MagicMock())
        pipeline.start()

        # Wait for a few mock events
        time.sleep(0.5)
        pipeline.stop()

        # Should have generated at least 1 event
        assert len(inference_events) >= 1

    def test_mock_events_have_valid_structure(self, pipeline):
        inference_events = []

        def on_inference(event):
            inference_events.append(event)

        pipeline.set_inference_callback(on_inference)
        pipeline.set_status_callback(MagicMock())
        pipeline.start()

        time.sleep(0.5)
        pipeline.stop()

        for event in inference_events:
            assert isinstance(event, DSEvent)
            assert event.site_id == "SITE-001"
            assert event.device_id.startswith("CAM-")
            assert event.model_version == "v1.0.0-tao-ds"
            assert event.inference.pgie.confidence >= 0.0
            assert event.inference.pgie.confidence <= 1.0
            assert event.inference.pgie.bbox.x >= 0.0
            assert event.inference.pgie.bbox.x <= 1.0

    def test_mock_events_come_from_connected_cameras(self, pipeline):
        inference_events = []

        def on_inference(event):
            inference_events.append(event)

        pipeline.set_inference_callback(on_inference)
        pipeline.set_status_callback(MagicMock())
        pipeline.start()
        time.sleep(0.1)

        # Disconnect CAM-001
        pipeline.simulate_camera_disconnect("CAM-001")
        # Clear previous events
        inference_events.clear()

        time.sleep(0.5)
        pipeline.stop()

        # No events should come from disconnected camera
        for event in inference_events:
            assert event.device_id != "CAM-001"
