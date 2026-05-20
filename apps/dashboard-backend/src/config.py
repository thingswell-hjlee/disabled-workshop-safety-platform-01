"""Dashboard Backend - Configuration Management

환경변수 기반 설정 관리. AWS_MODE=mock|live 스위치로 로컬/클라우드 모드 전환.
"""

import os
from enum import Enum
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class AWSMode(str, Enum):
    MOCK = "mock"
    LIVE = "live"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # --- Site ---
    site_id: str = Field(default="SITE-001", alias="SITE_ID")

    # --- Service ---
    service_name: str = "dashboard-backend"
    service_version: str = "1.0.0"
    host: str = "0.0.0.0"
    port: int = Field(default=8080, alias="DASHBOARD_PORT")

    # --- AWS Mode ---
    aws_mode: AWSMode = Field(default=AWSMode.MOCK, alias="AWS_MODE")

    # --- Database (PostgreSQL) ---
    db_host: str = Field(default="localhost", alias="CLOUD_DB_HOST")
    db_port: int = Field(default=5432, alias="CLOUD_DB_PORT")
    db_name: str = Field(default="safety_platform", alias="CLOUD_DB_NAME")
    db_user: str = Field(default="safety_admin", alias="CLOUD_DB_USER")
    db_password: str = Field(default="safety_password", alias="CLOUD_DB_PASSWORD")

    # --- Redis ---
    redis_host: str = Field(default="localhost", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_password: str = Field(default="", alias="REDIS_PASSWORD")

    # --- MQTT ---
    mqtt_host: str = Field(default="localhost", alias="MQTT_BROKER_HOST")
    mqtt_port: int = Field(default=1883, alias="MQTT_BROKER_PORT")

    # --- AWS IoT Core (live mode) ---
    aws_region: str = Field(default="ap-northeast-2", alias="AWS_REGION")
    aws_iot_endpoint: str = Field(default="", alias="AWS_IOT_ENDPOINT")
    aws_s3_bucket: str = Field(default="", alias="AWS_S3_BUCKET")
    aws_iot_cert_path: str = Field(default="/certs/device.pem.crt", alias="AWS_IOT_CERT_PATH")
    aws_iot_key_path: str = Field(default="/certs/device.pem.key", alias="AWS_IOT_KEY_PATH")
    aws_iot_ca_path: str = Field(default="/certs/root-CA.crt", alias="AWS_IOT_CA_PATH")

    # --- Auth ---
    jwt_secret: str = Field(default="dev-secret-key-change-in-production", alias="DASHBOARD_SECRET_KEY")
    jwt_expire_minutes: int = Field(default=30, alias="JWT_EXPIRY_MINUTES")

    # --- Logging ---
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    @property
    def database_url(self) -> str:
        """Construct asyncpg database URL."""
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def database_url_sync(self) -> str:
        """Construct synchronous database URL (for migrations/scripts)."""
        return (
            f"postgresql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def is_mock_mode(self) -> bool:
        return self.aws_mode == AWSMode.MOCK


# Singleton settings instance
settings = Settings()
