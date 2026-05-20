"""
Configuration Loading Tests.

카메라 설정 파일 로드 및 환경 변수 기반 설정 테스트.
"""

import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import AppConfig, CameraConfig, load_cameras_config, load_config


class TestCamerasConfigLoad:
    """Test cameras.json loading."""

    def test_load_valid_config(self, cameras_config_file):
        cameras = load_cameras_config(cameras_config_file)
        assert len(cameras) == 8
        assert cameras[0].camera_id == "CAM-001"
        assert cameras[0].device_id == "CAM-001"
        assert cameras[0].rtsp_url == "rtsp://192.168.1.101:554/stream1"
        assert cameras[0].enabled is True
        assert cameras[0].pipeline_index == 0
        assert cameras[0].width == 1920
        assert cameras[0].height == 1080
        assert cameras[0].fps == 30

    def test_load_8_cameras(self, cameras_config_file):
        cameras = load_cameras_config(cameras_config_file)
        assert len(cameras) == 8
        for i, cam in enumerate(cameras):
            assert cam.camera_id == f"CAM-{i+1:03d}"
            assert cam.pipeline_index == i

    def test_load_nonexistent_file_raises(self):
        with pytest.raises(FileNotFoundError):
            load_cameras_config("/nonexistent/cameras.json")

    def test_camera_has_zone_label(self, cameras_config_file):
        cameras = load_cameras_config(cameras_config_file)
        assert cameras[0].zone_label == "Zone 1"

    def test_camera_reconnect_settings(self, cameras_config_file):
        cameras = load_cameras_config(cameras_config_file)
        assert cameras[0].reconnect_interval_sec == 5
        assert cameras[0].max_reconnect_attempts == 10


class TestAppConfigEnv:
    """Test environment variable based configuration."""

    def test_default_config(self, monkeypatch):
        # Remove any cameras config path and Redis env vars
        monkeypatch.setenv("CAMERAS_CONFIG_PATH", "/nonexistent")
        monkeypatch.delenv("REDIS_HOST", raising=False)
        monkeypatch.delenv("REDIS_PORT", raising=False)
        monkeypatch.delenv("SITE_ID", raising=False)
        monkeypatch.delenv("MODEL_VERSION", raising=False)
        monkeypatch.delenv("DEEPSTREAM_MOCK_MODE", raising=False)
        config = load_config()
        assert config.site_id == "SITE-001"
        assert config.mock_mode is False
        assert config.redis.host == "localhost"
        assert config.redis.port == 6379
        assert config.redis.stream_name == "stream:ds-events"
        assert config.model.model_version == "v1.0.0-tao-ds"

    def test_mock_mode_enabled(self, monkeypatch):
        monkeypatch.setenv("DEEPSTREAM_MOCK_MODE", "true")
        monkeypatch.setenv("CAMERAS_CONFIG_PATH", "/nonexistent")
        config = load_config()
        assert config.mock_mode is True

    def test_custom_redis_host(self, monkeypatch):
        monkeypatch.setenv("REDIS_HOST", "redis-server")
        monkeypatch.setenv("REDIS_PORT", "6380")
        monkeypatch.setenv("CAMERAS_CONFIG_PATH", "/nonexistent")
        config = load_config()
        assert config.redis.host == "redis-server"
        assert config.redis.port == 6380

    def test_custom_model_version(self, monkeypatch):
        monkeypatch.setenv("MODEL_VERSION", "v2.0.0-custom-ds")
        monkeypatch.setenv("CAMERAS_CONFIG_PATH", "/nonexistent")
        config = load_config()
        assert config.model.model_version == "v2.0.0-custom-ds"

    def test_config_loads_cameras_file(self, monkeypatch, cameras_config_file):
        monkeypatch.setenv("CAMERAS_CONFIG_PATH", cameras_config_file)
        config = load_config()
        assert len(config.cameras) == 8
