"""
Pytest fixtures and configuration for DeepStream app tests.
"""

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import AppConfig, CameraConfig, ModelConfig, PipelineConfig, RedisConfig
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


@pytest.fixture
def sample_camera_config():
    """Sample camera configuration for testing."""
    return CameraConfig(
        camera_id="CAM-001",
        device_id="CAM-001",
        name="Test Camera 1",
        rtsp_url="rtsp://192.168.1.101:554/stream1",
        enabled=True,
        pipeline_index=0,
        width=1920,
        height=1080,
        fps=30,
        codec="H264",
        zone_label="A구역",
        reconnect_interval_sec=5,
        max_reconnect_attempts=10,
    )


@pytest.fixture
def sample_cameras_8ch():
    """8-channel camera configuration."""
    cameras = []
    for i in range(8):
        cameras.append(CameraConfig(
            camera_id=f"CAM-{i+1:03d}",
            device_id=f"CAM-{i+1:03d}",
            name=f"Test Camera {i+1}",
            rtsp_url=f"rtsp://192.168.1.{101+i}:554/stream1",
            enabled=True,
            pipeline_index=i,
        ))
    return cameras


@pytest.fixture
def mock_app_config(sample_cameras_8ch):
    """App config in mock mode."""
    return AppConfig(
        site_id="SITE-001",
        mock_mode=True,
        mock_event_interval_sec=0.1,  # Fast for testing
        healthcheck_port=18010,
        log_level="DEBUG",
        cameras=sample_cameras_8ch,
        redis=RedisConfig(
            host="localhost",
            port=6379,
            stream_name="stream:ds-events-test",
            max_stream_length=1000,
        ),
        model=ModelConfig(
            model_version="v1.0.0-tao-ds",
        ),
        pipeline=PipelineConfig(
            max_channels=8,
            batch_size=8,
        ),
    )


@pytest.fixture
def sample_fall_event():
    """Sample FALL_DETECTED event."""
    return DSEvent(
        event_id=generate_event_id(),
        site_id="SITE-001",
        source_id="pipeline-0",
        device_id="CAM-001",
        event_type="FALL_DETECTED",
        timestamp=generate_timestamp(),
        model_version="v1.0.0-tao-ds",
        inference=InferenceResult(
            pgie=PGIEResult(
                class_id=1,
                confidence=0.92,
                label="fall",
                bbox=BBox(x=0.35, y=0.45, w=0.15, h=0.20),
            ),
            tracker=TrackerResult(
                object_id=42,
                age_frames=15,
            ),
        ),
    )


@pytest.fixture
def sample_collapse_event():
    """Sample COLLAPSE_DETECTED event."""
    return DSEvent(
        event_id=generate_event_id(),
        site_id="SITE-001",
        source_id="pipeline-2",
        device_id="CAM-003",
        event_type="COLLAPSE_DETECTED",
        timestamp=generate_timestamp(),
        model_version="v1.0.0-tao-ds",
        inference=InferenceResult(
            pgie=PGIEResult(
                class_id=2,
                confidence=0.87,
                label="collapse",
                bbox=BBox(x=0.40, y=0.30, w=0.20, h=0.35),
            ),
            tracker=TrackerResult(
                object_id=55,
                age_frames=8,
            ),
        ),
    )


@pytest.fixture
def sample_device_offline_event():
    """Sample DEVICE_OFFLINE event."""
    return DeviceStatusEvent(
        event_id=generate_event_id(),
        site_id="SITE-001",
        source_id="pipeline-1",
        device_id="CAM-002",
        event_type="DEVICE_OFFLINE",
        timestamp=generate_timestamp(),
        model_version="v1.0.0-tao-ds",
    )


@pytest.fixture
def sample_device_online_event():
    """Sample DEVICE_ONLINE event."""
    return DeviceStatusEvent(
        event_id=generate_event_id(),
        site_id="SITE-001",
        source_id="pipeline-1",
        device_id="CAM-002",
        event_type="DEVICE_ONLINE",
        timestamp=generate_timestamp(),
        model_version="v1.0.0-tao-ds",
    )


@pytest.fixture
def cameras_config_file(tmp_path):
    """Temporary cameras config JSON file."""
    config_data = {
        "site_id": "SITE-001",
        "cameras": [
            {
                "camera_id": f"CAM-{i+1:03d}",
                "device_id": f"CAM-{i+1:03d}",
                "name": f"Test Camera {i+1}",
                "rtsp_url": f"rtsp://192.168.1.{101+i}:554/stream1",
                "enabled": True,
                "pipeline_index": i,
                "resolution": {"width": 1920, "height": 1080},
                "fps": 30,
                "codec": "H264",
                "zone_label": f"Zone {i+1}",
                "reconnect_interval_sec": 5,
                "max_reconnect_attempts": 10,
            }
            for i in range(8)
        ],
        "defaults": {
            "resolution": {"width": 1920, "height": 1080},
            "fps": 30,
            "codec": "H264",
            "reconnect_interval_sec": 5,
            "max_reconnect_attempts": 10,
        },
    }

    config_file = tmp_path / "cameras.json"
    config_file.write_text(json.dumps(config_data, ensure_ascii=False))
    return str(config_file)
