"""Device Gateway - Model Tests"""
import pytest
from src.models import (
    DeviceInfo,
    DeviceStatus,
    DeviceType,
    FrameMessage,
    BioMessage,
    SensorMessage,
    FireContactMessage,
    StreamDataType,
)


class TestDeviceInfo:
    def test_create_camera_device(self):
        device = DeviceInfo(
            device_id="CAM-001",
            site_id="SITE-001",
            device_type=DeviceType.IP_CAMERA,
            status=DeviceStatus.CONNECTED,
        )
        assert device.device_id == "CAM-001"
        assert device.device_type == DeviceType.IP_CAMERA
        assert device.status == DeviceStatus.CONNECTED

    def test_create_band_device(self):
        device = DeviceInfo(
            device_id="BAND-001",
            site_id="SITE-001",
            device_type=DeviceType.SMART_BAND,
            status=DeviceStatus.CONNECTED,
            metadata={"worker_id": "WKR-0001"},
        )
        assert device.metadata["worker_id"] == "WKR-0001"


class TestFrameMessage:
    def test_create_frame_message(self):
        msg = FrameMessage(
            device_id="CAM-001",
            site_id="SITE-001",
            timestamp="2025-05-19T12:00:00.000Z",
            frame_seq=1,
            resolution="640x640",
        )
        assert msg.device_id == "CAM-001"
        assert msg.frame_seq == 1
        assert msg.encoding == "raw_bgr"


class TestBioMessage:
    def test_create_heartrate_message(self):
        msg = BioMessage(
            device_id="BAND-001",
            worker_id="WKR-0001",
            site_id="SITE-001",
            timestamp="2025-05-19T12:00:00.000Z",
            data_type=StreamDataType.HEARTRATE,
            value={"bpm": 72},
            battery_level=85,
        )
        assert msg.value["bpm"] == 72
        assert msg.battery_level == 85


class TestSensorMessage:
    def test_create_env_message(self):
        msg = SensorMessage(
            device_id="ENV-001",
            site_id="SITE-001",
            zone="작업장A",
            timestamp="2025-05-19T12:00:00.000Z",
            temperature=25.3,
            humidity=45.2,
            co_ppm=2.1,
            voc_ppb=120.0,
        )
        assert msg.temperature == 25.3
        assert msg.zone == "작업장A"


class TestFireContactMessage:
    def test_create_fire_detected(self):
        msg = FireContactMessage(
            device_id="FIRE-001",
            site_id="SITE-001",
            timestamp="2025-05-19T12:00:00.000Z",
            status="DETECTED",
            raw_signal=1,
        )
        assert msg.status == "DETECTED"
        assert msg.raw_signal == 1

    def test_create_fire_normal(self):
        msg = FireContactMessage(
            device_id="FIRE-001",
            site_id="SITE-001",
            timestamp="2025-05-19T12:00:00.000Z",
        )
        assert msg.status == "NORMAL"
        assert msg.raw_signal == 0
