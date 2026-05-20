#!/usr/bin/env python3
"""
AWS IoT Core Mock Receiver

로컬 Mosquitto broker에 연결하여 safety/+/events, safety/+/status, safety/+/models
토픽을 구독하고, 수신된 메시지를 검증/출력합니다.

Usage:
    python infra/aws/iot/mock-receiver.py [--host localhost] [--port 1883]

Environment:
    MQTT_BROKER_HOST (default: localhost)
    MQTT_BROKER_PORT (default: 1883)
"""

import json
import os
import sys
import re
import argparse
from datetime import datetime, timezone, timedelta
from typing import Optional

try:
    import paho.mqtt.client as mqtt
except ImportError:
    print("ERROR: paho-mqtt not installed. Run: pip install paho-mqtt")
    sys.exit(1)


# --- Validation Constants ---
VALID_EVENT_TYPES = [
    "FALL_DETECTED", "COLLAPSE_DETECTED", "ZONE_INTRUSION",
    "STILLNESS_DETECTED", "HAZARDOUS_ACTION", "FIRE_DETECTED",
    "HEARTRATE_ABNORMAL", "TEMPERATURE_ABNORMAL",
    "BAND_FALL_DETECTED", "BAND_DISCONNECTED",
    "ENV_THRESHOLD_EXCEEDED", "DEVICE_OFFLINE", "DEVICE_ONLINE",
    "NORMAL_RESTORED", "SYSTEM_ALERT",
]

VALID_RISK_LEVELS = ["CRITICAL", "WARNING", "NORMAL"]
VALID_EDGE_STATUSES = ["HEALTHY", "DEGRADED", "ERROR"]
VALID_MODEL_ACTIONS = ["DEPLOY", "ROLLBACK", "STATUS_REQUEST", "DEPLOY_STATUS"]
VALID_DEPLOY_STATUSES = [
    "DOWNLOADING", "STAGED", "DEPLOYING", "ACTIVE", "FAILED", "ROLLBACK"
]

EVENT_ID_PATTERN = re.compile(r"^EVT-\d{14}-\d{3}$")
SITE_ID_PATTERN = re.compile(r"^SITE-\d{3}$")
DEVICE_ID_PATTERN = re.compile(r"^(CAM|BAND|ENV|FIRE|NVR|ALARM)-\d{3}$")

# CRITICAL events that must have risk_level=CRITICAL
CRITICAL_EVENT_TYPES = ["FALL_DETECTED", "COLLAPSE_DETECTED", "FIRE_DETECTED"]


class ValidationResult:
    def __init__(self, valid: bool, errors: list = None):
        self.valid = valid
        self.errors = errors or []

    def __str__(self):
        if self.valid:
            return "VALID"
        return f"INVALID: {'; '.join(self.errors)}"


def validate_timestamp(ts_str: str) -> Optional[str]:
    """Validate ISO 8601 UTC timestamp."""
    try:
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        if dt > now + timedelta(seconds=5):
            return "timestamp is in the future (max +5s tolerance)"
        return None
    except (ValueError, TypeError):
        return f"invalid timestamp format: {ts_str}"


def validate_event_payload(payload: dict) -> ValidationResult:
    """Validate safety/{site_id}/events payload."""
    errors = []

    # Required fields
    required = ["event_id", "site_id", "device_id", "event_type",
                "risk_level", "timestamp", "context_summary", "idempotency_key"]
    for field in required:
        if field not in payload or payload[field] is None:
            errors.append(f"missing required field: {field}")

    if errors:
        return ValidationResult(False, errors)

    # Pattern validations
    if not EVENT_ID_PATTERN.match(payload.get("event_id", "")):
        errors.append(f"invalid event_id format: {payload.get('event_id')}")

    if not SITE_ID_PATTERN.match(payload.get("site_id", "")):
        errors.append(f"invalid site_id format: {payload.get('site_id')}")

    if not DEVICE_ID_PATTERN.match(payload.get("device_id", "")):
        errors.append(f"invalid device_id format: {payload.get('device_id')}")

    # Enum validations
    if payload.get("event_type") not in VALID_EVENT_TYPES:
        errors.append(f"invalid event_type: {payload.get('event_type')}")

    if payload.get("risk_level") not in VALID_RISK_LEVELS:
        errors.append(f"invalid risk_level: {payload.get('risk_level')}")

    # CRITICAL event types must have CRITICAL risk_level
    if (payload.get("event_type") in CRITICAL_EVENT_TYPES
            and payload.get("risk_level") != "CRITICAL"):
        errors.append(
            f"{payload.get('event_type')} must have risk_level=CRITICAL"
        )

    # Confidence range
    confidence = payload.get("confidence")
    if confidence is not None:
        if not isinstance(confidence, (int, float)) or confidence < 0.0 or confidence > 1.0:
            errors.append(f"confidence must be 0.0~1.0, got: {confidence}")

    # Timestamp validation
    ts_err = validate_timestamp(payload.get("timestamp", ""))
    if ts_err:
        errors.append(ts_err)

    # Idempotency key format
    expected_idem = f"{payload.get('site_id')}:{payload.get('event_id')}"
    if payload.get("idempotency_key") != expected_idem:
        errors.append(
            f"idempotency_key should be '{expected_idem}', "
            f"got: '{payload.get('idempotency_key')}'"
        )

    return ValidationResult(len(errors) == 0, errors)


def validate_status_payload(payload: dict) -> ValidationResult:
    """Validate safety/{site_id}/status payload."""
    errors = []

    required = ["site_id", "timestamp", "edge_status", "deepstream_fps",
                "gpu_utilization", "active_cameras", "active_bands",
                "pending_cloud_events"]
    for field in required:
        if field not in payload:
            errors.append(f"missing required field: {field}")

    if errors:
        return ValidationResult(False, errors)

    if payload.get("edge_status") not in VALID_EDGE_STATUSES:
        errors.append(f"invalid edge_status: {payload.get('edge_status')}")

    gpu = payload.get("gpu_utilization")
    if gpu is not None and (not isinstance(gpu, (int, float)) or gpu < 0.0 or gpu > 1.0):
        errors.append(f"gpu_utilization must be 0.0~1.0, got: {gpu}")

    if not isinstance(payload.get("deepstream_fps"), list):
        errors.append("deepstream_fps must be an array")

    return ValidationResult(len(errors) == 0, errors)


def validate_model_payload(payload: dict) -> ValidationResult:
    """Validate safety/{site_id}/models payload."""
    errors = []

    action = payload.get("action")
    if action not in VALID_MODEL_ACTIONS:
        errors.append(f"invalid action: {action}")
        return ValidationResult(False, errors)

    if action in ["DEPLOY", "ROLLBACK", "STATUS_REQUEST"]:
        # Cloud → Edge command
        for field in ["model_version", "model_type", "s3_uri", "timestamp"]:
            if field not in payload:
                errors.append(f"missing field for {action}: {field}")
    elif action == "DEPLOY_STATUS":
        # Edge → Cloud status
        for field in ["site_id", "model_version", "status", "timestamp"]:
            if field not in payload:
                errors.append(f"missing field for DEPLOY_STATUS: {field}")
        if payload.get("status") not in VALID_DEPLOY_STATUSES:
            errors.append(f"invalid deploy status: {payload.get('status')}")

    return ValidationResult(len(errors) == 0, errors)


# --- MQTT Callbacks ---
def on_connect(client, userdata, flags, rc, properties=None):
    """Called when connected to MQTT broker."""
    if rc == 0:
        print(f"[CONNECTED] Mock IoT receiver connected to broker")
        client.subscribe("safety/+/events", qos=1)
        client.subscribe("safety/+/status", qos=1)
        client.subscribe("safety/+/models", qos=1)
        print("[SUBSCRIBED] Topics: safety/+/events, safety/+/status, safety/+/models")
    else:
        print(f"[ERROR] Connection failed with code: {rc}")


def on_message(client, userdata, msg):
    """Called when a message is received."""
    topic = msg.topic
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    try:
        payload = json.loads(msg.payload.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"[{timestamp}] [ERROR] Invalid JSON on {topic}: {e}")
        return

    # Determine topic type and validate
    parts = topic.split("/")
    if len(parts) != 3:
        print(f"[{timestamp}] [ERROR] Unexpected topic format: {topic}")
        return

    topic_type = parts[2]

    if topic_type == "events":
        result = validate_event_payload(payload)
        icon = "🚨" if payload.get("risk_level") == "CRITICAL" else "⚠️" if payload.get("risk_level") == "WARNING" else "ℹ️"
        print(f"\n[{timestamp}] {icon} EVENT on {topic}")
        print(f"  event_id: {payload.get('event_id')}")
        print(f"  type: {payload.get('event_type')} | risk: {payload.get('risk_level')}")
        print(f"  device: {payload.get('device_id')} | worker: {payload.get('worker_id')}")
        print(f"  confidence: {payload.get('confidence')} | model: {payload.get('model_version')}")
        print(f"  validation: {result}")

    elif topic_type == "status":
        result = validate_status_payload(payload)
        status = payload.get("edge_status", "UNKNOWN")
        icon = "✅" if status == "HEALTHY" else "🟡" if status == "DEGRADED" else "🔴"
        print(f"\n[{timestamp}] {icon} STATUS on {topic}")
        print(f"  edge_status: {status} | cameras: {payload.get('active_cameras')} | bands: {payload.get('active_bands')}")
        print(f"  gpu: {payload.get('gpu_utilization')} | pending: {payload.get('pending_cloud_events')}")
        print(f"  validation: {result}")

    elif topic_type == "models":
        result = validate_model_payload(payload)
        action = payload.get("action", "UNKNOWN")
        print(f"\n[{timestamp}] 🤖 MODEL on {topic}")
        print(f"  action: {action} | version: {payload.get('model_version')}")
        print(f"  status: {payload.get('status', 'N/A')}")
        print(f"  validation: {result}")

    else:
        print(f"\n[{timestamp}] [UNKNOWN] Unrecognized topic type: {topic}")

    if not result.valid:
        for err in result.errors:
            print(f"  ❌ {err}")


def on_disconnect(client, userdata, rc, properties=None):
    """Called when disconnected."""
    if rc != 0:
        print(f"[DISCONNECTED] Unexpected disconnection (rc={rc}), reconnecting...")
    else:
        print("[DISCONNECTED] Clean disconnect")


def main():
    parser = argparse.ArgumentParser(description="AWS IoT Core Mock Receiver")
    parser.add_argument("--host", default=os.getenv("MQTT_BROKER_HOST", "localhost"),
                        help="MQTT broker host")
    parser.add_argument("--port", type=int,
                        default=int(os.getenv("MQTT_BROKER_PORT", "1883")),
                        help="MQTT broker port")
    args = parser.parse_args()

    print("=" * 60)
    print(" AWS IoT Core Mock Receiver")
    print(f" Broker: {args.host}:{args.port}")
    print(f" Topics: safety/+/events, safety/+/status, safety/+/models")
    print("=" * 60)

    client = mqtt.Client(
        client_id="mock-iot-receiver",
        protocol=mqtt.MQTTv5,
    )
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect

    try:
        client.connect(args.host, args.port, keepalive=60)
        client.loop_forever()
    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Mock receiver stopped.")
        client.disconnect()
    except ConnectionRefusedError:
        print(f"[ERROR] Cannot connect to MQTT broker at {args.host}:{args.port}")
        print("  Make sure Mosquitto is running: docker compose up mosquitto")
        sys.exit(1)


if __name__ == "__main__":
    main()
