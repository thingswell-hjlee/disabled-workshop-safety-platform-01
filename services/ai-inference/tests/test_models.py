"""AI Inference Engine - Model Tests"""
import pytest
from src.models import (
    EventType, RiskLevel, ModelType,
    DetectionResult, InferenceEvent, ModelInfo,
    ZoneConfig, InferenceStats, ThresholdConfig, BoundingBox,
)


class TestDetectionResult:
    def test_fall_detection(self):
        result = DetectionResult(
            event_type=EventType.FALL_DETECTED,
            confidence=0.92,
            bbox=BoundingBox(x=120, y=80, width=300, height=450),
            zone="작업장A",
            model_version="v1.0.0-edge",
        )
        assert result.confidence == 0.92
        assert result.event_type == EventType.FALL_DETECTED
        assert result.bbox.x == 120

    def test_zone_intrusion(self):
        result = DetectionResult(
            event_type=EventType.ZONE_INTRUSION,
            confidence=0.88,
            zone="장비실-접근금지",
            model_version="v1.0.0-edge",
        )
        assert result.event_type == EventType.ZONE_INTRUSION


class TestInferenceEvent:
    def test_create_critical_event(self):
        event = InferenceEvent(
            event_id="EVT-20250519120000-001",
            site_id="SITE-001",
            device_id="CAM-003",
            worker_id="WKR-0002",
            event_type=EventType.FALL_DETECTED,
            risk_level=RiskLevel.CRITICAL,
            confidence=0.92,
            model_version="v1.0.0-edge",
            timestamp="2025-05-19T12:00:00.123Z",
            payload={"bbox": [120, 80, 300, 450]},
        )
        assert event.risk_level == RiskLevel.CRITICAL
        assert event.event_id.startswith("EVT-")


class TestThresholdConfig:
    def test_default_thresholds(self):
        config = ThresholdConfig()
        assert config.temperature_max == 40.0
        assert config.co_ppm_max == 50.0
        assert config.heartrate_min == 40
        assert config.heartrate_max == 150
        assert config.band_timeout_seconds == 30

    def test_custom_thresholds(self):
        config = ThresholdConfig(
            temperature_max=45.0,
            co_ppm_max=100.0,
        )
        assert config.temperature_max == 45.0
        assert config.co_ppm_max == 100.0


class TestZoneConfig:
    def test_create_zone(self):
        zone = ZoneConfig(
            camera_id="CAM-001",
            zone_name="위험구역A",
            polygon=[[0, 0], [100, 0], [100, 100], [0, 100]],
        )
        assert zone.enabled is True
        assert len(zone.polygon) == 4


class TestModelInfo:
    def test_tensorrt_model(self):
        model = ModelInfo(
            model_id="yolov8-safety",
            model_type=ModelType.OBJECT_DETECTION,
            model_version="v1.0.0-edge",
            framework="tensorrt",
        )
        assert model.framework == "tensorrt"
        assert model.input_shape == [1, 3, 640, 640]
