"""
Application configuration module.

환경 변수 및 설정 파일 기반 구성 관리.
설정값은 코드에 하드코딩하지 않고 환경설정 파일 또는 환경 변수에서 관리합니다.
"""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class CameraConfig:
    """개별 카메라 설정"""
    camera_id: str
    device_id: str
    name: str
    rtsp_url: str
    enabled: bool = True
    pipeline_index: int = 0
    width: int = 1920
    height: int = 1080
    fps: int = 30
    codec: str = "H264"
    zone_label: str = ""
    reconnect_interval_sec: int = 5
    max_reconnect_attempts: int = 10


@dataclass
class RedisConfig:
    """Redis 연결 설정"""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    stream_name: str = "stream:ds-events"
    max_stream_length: int = 10000
    consumer_group: str = "cg-event-engine"


@dataclass
class ModelConfig:
    """AI 모델 설정"""
    model_version: str = "v1.0.0-tao-ds"
    engine_path: str = "/models/active/pgie/model.engine"
    labels_path: str = "/models/active/pgie/labels.txt"
    config_path: str = "/models/active/pgie/config.txt"
    confidence_threshold: float = 0.5
    classes: List[str] = field(default_factory=lambda: [
        "person", "fall", "collapse", "fire", "intrusion", "hazardous_action"
    ])


@dataclass
class PipelineConfig:
    """DeepStream 파이프라인 설정"""
    max_channels: int = 8
    batch_size: int = 8
    gpu_id: int = 0
    tracker_enabled: bool = True
    tracker_type: str = "NvDCF"  # NvDCF or IOU
    output_width: int = 960
    output_height: int = 544


@dataclass
class AppConfig:
    """전체 애플리케이션 설정"""
    site_id: str = "SITE-001"
    mock_mode: bool = False
    mock_event_interval_sec: float = 5.0
    healthcheck_port: int = 8010
    log_level: str = "INFO"
    cameras: List[CameraConfig] = field(default_factory=list)
    redis: RedisConfig = field(default_factory=RedisConfig)
    model: ModelConfig = field(default_factory=ModelConfig)
    pipeline: PipelineConfig = field(default_factory=PipelineConfig)


def load_cameras_config(config_path: str) -> List[CameraConfig]:
    """카메라 설정 파일 로드"""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Camera config not found: {config_path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    cameras = []
    for cam in data.get("cameras", []):
        resolution = cam.get("resolution", {})
        cameras.append(CameraConfig(
            camera_id=cam["camera_id"],
            device_id=cam["device_id"],
            name=cam.get("name", ""),
            rtsp_url=cam["rtsp_url"],
            enabled=cam.get("enabled", True),
            pipeline_index=cam.get("pipeline_index", 0),
            width=resolution.get("width", 1920),
            height=resolution.get("height", 1080),
            fps=cam.get("fps", 30),
            codec=cam.get("codec", "H264"),
            zone_label=cam.get("zone_label", ""),
            reconnect_interval_sec=cam.get("reconnect_interval_sec", 5),
            max_reconnect_attempts=cam.get("max_reconnect_attempts", 10),
        ))
    return cameras


def load_config() -> AppConfig:
    """환경 변수 및 설정 파일에서 전체 설정 로드"""
    config = AppConfig(
        site_id=os.getenv("SITE_ID", "SITE-001"),
        mock_mode=os.getenv("DEEPSTREAM_MOCK_MODE", "false").lower() in ("true", "1", "yes"),
        mock_event_interval_sec=float(os.getenv("MOCK_EVENT_INTERVAL_SEC", "5.0")),
        healthcheck_port=int(os.getenv("HEALTHCHECK_PORT", "8010")),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
    )

    # Redis config
    config.redis = RedisConfig(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        db=int(os.getenv("REDIS_DB", "0")),
        password=os.getenv("REDIS_PASSWORD", None),
        stream_name=os.getenv("REDIS_STREAM_NAME", "stream:ds-events"),
        max_stream_length=int(os.getenv("REDIS_MAX_STREAM_LENGTH", "10000")),
    )

    # Model config
    config.model = ModelConfig(
        model_version=os.getenv("MODEL_VERSION", "v1.0.0-tao-ds"),
        engine_path=os.getenv("MODEL_ENGINE_PATH", "/models/active/pgie/model.engine"),
        labels_path=os.getenv("MODEL_LABELS_PATH", "/models/active/pgie/labels.txt"),
        config_path=os.getenv("MODEL_CONFIG_PATH", "/models/active/pgie/config.txt"),
        confidence_threshold=float(os.getenv("CONFIDENCE_THRESHOLD", "0.5")),
    )

    # Pipeline config
    config.pipeline = PipelineConfig(
        max_channels=int(os.getenv("MAX_CHANNELS", "8")),
        batch_size=int(os.getenv("BATCH_SIZE", "8")),
        gpu_id=int(os.getenv("GPU_ID", "0")),
        tracker_enabled=os.getenv("TRACKER_ENABLED", "true").lower() in ("true", "1"),
        tracker_type=os.getenv("TRACKER_TYPE", "NvDCF"),
    )

    # Camera config
    cameras_config_path = os.getenv(
        "CAMERAS_CONFIG_PATH",
        "/app/config/cameras.json"
    )
    if Path(cameras_config_path).exists():
        config.cameras = load_cameras_config(cameras_config_path)

    return config
