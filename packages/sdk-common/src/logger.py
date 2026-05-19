"""Structured JSON Logger - 중앙화된 로깅 설정"""
import logging
import json
import sys
from datetime import datetime, timezone
from typing import Optional


class JsonFormatter(logging.Formatter):
    """구조화된 JSON 로그 포맷터 (NFR-041 준수)"""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service": getattr(record, "service", "unknown"),
            "site_id": getattr(record, "site_id", "SITE-001"),
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Optional fields
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Extra fields from record
        for key in ("event_id", "device_id", "worker_id", "risk_level", "duration_ms"):
            value = getattr(record, key, None)
            if value is not None:
                log_entry[key] = value

        return json.dumps(log_entry, ensure_ascii=False)


def get_logger(
    service_name: str,
    level: str = "INFO",
    site_id: str = "SITE-001",
) -> logging.Logger:
    """
    서비스별 구조화 로거 생성.

    Args:
        service_name: 서비스 이름 (예: "device-gateway")
        level: 로그 레벨 (DEBUG, INFO, WARNING, ERROR)
        site_id: 현장 ID

    Returns:
        logging.Logger with JSON formatter
    """
    logger = logging.getLogger(service_name)

    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    # Add service and site_id as default extras
    old_factory = logging.getLogRecordFactory()

    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.service = service_name
        record.site_id = site_id
        return record

    logging.setLogRecordFactory(record_factory)
    logger.addHandler(handler)
    logger.propagate = False

    return logger
