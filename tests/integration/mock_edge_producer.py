"""
Mock Edge Event Producer
=========================
Edge AI 서버의 이벤트 생성을 시뮬레이션한다.
DeepStream Pipeline, Device Gateway 역할을 mock으로 대체.

사용 흐름:
1. EdgeEventProducer 인스턴스 생성
2. produce_ds_event() → stream:ds-events 발행
3. produce_sensor_event() → stream:sensors 발행
4. Event Engine이 소비하여 후속 스트림에 전달

Reference: docs/redis-streams-schema.md
"""

import json
import time
from datetime import datetime, timezone
from typing import Optional


class EdgeEventProducer:
    """Edge 서버의 이벤트 생성을 시뮬레이션하는 Mock Producer"""

    def __init__(self, redis_client, site_id: str = "SITE-001"):
        self.redis = redis_client
        self.site_id = site_id
        self._seq_counter = 0

    def _generate_event_id(self) -> str:
        """EVT-YYYYMMDDHHmmss-SEQ 형식의 event_id 생성"""
        self._seq_counter += 1
        now = datetime.now(timezone.utc)
        ts = now.strftime("%Y%m%d%H%M%S")
        return f"EVT-{ts}-{self._seq_counter:03d}"

    def _get_timestamp(self) -> str:
        """ISO 8601 UTC timestamp with milliseconds"""
        now = datetime.now(timezone.utc)
        return now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"

    def produce_ds_event(
        self,
        event_type: str = "FALL_DETECTED",
        device_id: str = "CAM-001",
        confidence: float = 0.92,
        class_label: str = "fall",
        class_id: int = 2,
        model_version: str = "v1.0.0-tao-ds",
        event_id: Optional[str] = None,
    ) -> dict:
        """
        stream:ds-events에 DeepStream 추론 결과 발행.
        
        Returns:
            Published message dict (for assertion)
        """
        if event_id is None:
            event_id = self._generate_event_id()

        message = {
            "event_id": event_id,
            "site_id": self.site_id,
            "source_id": "pipeline-0",
            "device_id": device_id,
            "event_type": event_type,
            "timestamp": self._get_timestamp(),
            "model_version": model_version,
            "inference": json.dumps({
                "pgie": {
                    "class_id": class_id,
                    "confidence": confidence,
                    "label": class_label,
                    "bbox": {"x": 0.35, "y": 0.45, "w": 0.15, "h": 0.20},
                },
                "sgie": None,
                "tracker": {
                    "object_id": self._seq_counter,
                    "age_frames": 15,
                },
            }),
            "analytics": "",
        }

        self.redis.xadd("stream:ds-events", message, maxlen=10000)
        return message

    def produce_sensor_event(
        self,
        event_type: str = "HEARTRATE_ABNORMAL",
        device_id: str = "BAND-003",
        worker_id: str = "WKR-0012",
        data_type: str = "HEARTRATE",
        value: float = 142.0,
        source: str = "SMART_BAND",
        event_id: Optional[str] = None,
    ) -> dict:
        """
        stream:sensors에 센서 이벤트 발행.
        
        Returns:
            Published message dict
        """
        if event_id is None:
            event_id = self._generate_event_id()

        message = {
            "event_id": event_id,
            "site_id": self.site_id,
            "device_id": device_id,
            "worker_id": worker_id or "",
            "event_type": event_type,
            "timestamp": self._get_timestamp(),
            "data_type": data_type,
            "value": str(value),
            "source": source,
        }

        self.redis.xadd("stream:sensors", message, maxlen=50000)
        return message

    def produce_env_event(
        self,
        device_id: str = "ENV-001",
        data_type: str = "GAS",
        value: float = 28.5,
        event_id: Optional[str] = None,
    ) -> dict:
        """stream:sensors에 환경센서 이벤트 발행"""
        return self.produce_sensor_event(
            event_type="ENV_THRESHOLD_EXCEEDED",
            device_id=device_id,
            worker_id="",
            data_type=data_type,
            value=value,
            source="ENV_SENSOR",
            event_id=event_id,
        )

    def produce_fire_event(self, event_id: Optional[str] = None) -> dict:
        """stream:sensors에 화재 접점 이벤트 발행"""
        return self.produce_sensor_event(
            event_type="FIRE_DETECTED",
            device_id="FIRE-001",
            worker_id="",
            data_type="FIRE_CONTACT",
            value=1.0,
            source="FIRE_CONTACT",
            event_id=event_id,
        )


class MockEventEngine:
    """
    Event Engine의 핵심 로직을 시뮬레이션.
    stream:ds-events / stream:sensors를 소비하여
    stream:alarms, stream:dashboard, stream:cloud-queue, stream:clip-trigger에 발행.
    """

    CRITICAL_EVENTS = {"FALL_DETECTED", "COLLAPSE_DETECTED", "FIRE_DETECTED"}
    RISK_TO_PRIORITY = {"CRITICAL": "HIGH", "WARNING": "NORMAL", "NORMAL": "LOW"}

    def __init__(self, redis_client, site_id: str = "SITE-001"):
        self.redis = redis_client
        self.site_id = site_id

    def _determine_risk_level(self, event_type: str) -> str:
        """event_type에 따른 risk_level 결정"""
        if event_type in self.CRITICAL_EVENTS:
            return "CRITICAL"
        elif event_type in {"DEVICE_ONLINE", "DEVICE_OFFLINE", "NORMAL_RESTORED"}:
            return "NORMAL"
        return "WARNING"

    def _determine_alarm_action(self, risk_level: str) -> str:
        """risk_level에 따른 알람 action 결정"""
        if risk_level == "CRITICAL":
            return "ALL_ON"
        elif risk_level == "WARNING":
            return "LIGHT_ON"
        return "ALL_OFF"

    def process_ds_event(self, event_data: dict) -> dict:
        """
        stream:ds-events 메시지를 처리하여 후속 스트림에 발행.
        
        Returns:
            처리 결과 (각 스트림 발행 여부)
        """
        event_type = event_data["event_type"]
        risk_level = self._determine_risk_level(event_type)
        timestamp = event_data["timestamp"]
        event_id = event_data["event_id"]

        inference = json.loads(event_data["inference"]) if isinstance(event_data["inference"], str) else event_data["inference"]
        confidence = inference.get("pgie", {}).get("confidence", 0.0) if inference.get("pgie") else 0.0

        result = {"alarm": False, "dashboard": False, "cloud_queue": False, "clip_trigger": False}

        # stream:alarms
        alarm_msg = {
            "event_id": event_id,
            "site_id": self.site_id,
            "risk_level": risk_level,
            "action": self._determine_alarm_action(risk_level),
            "timestamp": timestamp,
            "source_event_type": event_type,
        }
        self.redis.xadd("stream:alarms", alarm_msg, maxlen=1000)
        result["alarm"] = True

        # stream:dashboard
        dashboard_msg = {
            "event_id": event_id,
            "site_id": self.site_id,
            "device_id": event_data["device_id"],
            "worker_id": "",
            "event_type": event_type,
            "risk_level": risk_level,
            "timestamp": timestamp,
            "event_state": "ACTIVE",
            "confidence": str(confidence),
            "model_version": event_data.get("model_version", ""),
            "context": json.dumps({
                "summary": f"{event_type} detected (confidence: {confidence:.0%})",
                "location": "",
                "clip_available": True,
            }),
        }
        self.redis.xadd("stream:dashboard", dashboard_msg, maxlen=5000)
        result["dashboard"] = True

        # stream:cloud-queue
        priority = self.RISK_TO_PRIORITY.get(risk_level, "LOW")
        cloud_msg = {
            "event_id": event_id,
            "site_id": self.site_id,
            "device_id": event_data["device_id"],
            "worker_id": "",
            "event_type": event_type,
            "risk_level": risk_level,
            "timestamp": timestamp,
            "idempotency_key": f"{self.site_id}:{event_id}",
            "priority": priority,
            "clip_path": f"/data/clips/{event_id}.mp4",
            "confidence": str(confidence),
            "model_version": event_data.get("model_version", ""),
        }
        self.redis.xadd("stream:cloud-queue", cloud_msg, maxlen=10000)
        result["cloud_queue"] = True

        # stream:clip-trigger (only for camera events)
        if event_data["device_id"].startswith("CAM"):
            clip_msg = {
                "event_id": event_id,
                "site_id": self.site_id,
                "device_id": event_data["device_id"],
                "trigger_ts": timestamp,
                "pre_sec": "30",
                "post_sec": "30",
            }
            self.redis.xadd("stream:clip-trigger", clip_msg, maxlen=1000)
            result["clip_trigger"] = True

        return result
