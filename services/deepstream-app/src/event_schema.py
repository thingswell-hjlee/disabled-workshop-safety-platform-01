"""
Event Schema Models - PR #16 event-message-schema 기준 준수.

stream:ds-events 메시지 구조를 정확히 따릅니다.
event_id: EVT-YYYYMMDDHHmmss-SEQ
device_id: CAM-NNN
event_type: FALL_DETECTED, COLLAPSE_DETECTED, ZONE_INTRUSION, etc.
risk_level: CRITICAL, WARNING, NORMAL
"""

import re
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Optional


# ─── Enums ───────────────────────────────────────────────────────────────────

VALID_EVENT_TYPES = {
    "FALL_DETECTED",
    "COLLAPSE_DETECTED",
    "ZONE_INTRUSION",
    "STILLNESS_DETECTED",
    "HAZARDOUS_ACTION",
    "FIRE_DETECTED",
    "HEARTRATE_ABNORMAL",
    "TEMPERATURE_ABNORMAL",
    "BAND_FALL_DETECTED",
    "BAND_DISCONNECTED",
    "ENV_THRESHOLD_EXCEEDED",
    "DEVICE_OFFLINE",
    "DEVICE_ONLINE",
    "NORMAL_RESTORED",
    "SYSTEM_ALERT",
}

VALID_RISK_LEVELS = {"CRITICAL", "WARNING", "NORMAL"}

# Vision AI event types (from DeepStream)
VISION_AI_EVENT_TYPES = {
    "FALL_DETECTED",
    "COLLAPSE_DETECTED",
    "ZONE_INTRUSION",
    "STILLNESS_DETECTED",
    "HAZARDOUS_ACTION",
    "FIRE_DETECTED",
}

# Critical risk level mandatory for these events
CRITICAL_EVENT_TYPES = {
    "FALL_DETECTED",
    "COLLAPSE_DETECTED",
    "FIRE_DETECTED",
}

# Class ID → event_type mapping (DeepStream inference class)
CLASS_EVENT_MAP = {
    0: ("person", "NORMAL_RESTORED", "NORMAL"),  # person detected, not an alert
    1: ("fall", "FALL_DETECTED", "CRITICAL"),
    2: ("collapse", "COLLAPSE_DETECTED", "CRITICAL"),
    3: ("fire", "FIRE_DETECTED", "CRITICAL"),
    4: ("intrusion", "ZONE_INTRUSION", "WARNING"),
    5: ("hazardous_action", "HAZARDOUS_ACTION", "WARNING"),
}

# ─── ID Patterns ─────────────────────────────────────────────────────────────

EVENT_ID_PATTERN = re.compile(r"^EVT-\d{14}-\d{3}$")
SITE_ID_PATTERN = re.compile(r"^SITE-\d{3}$")
DEVICE_ID_PATTERN = re.compile(r"^(CAM|BAND|ENV|FIRE|NVR|ALARM)-\d{3}$")
MODEL_VERSION_PATTERN = re.compile(
    r"^v\d+\.\d+\.\d+-(tao|pretrained|custom)-(ds|cloud)$"
)


# ─── Event ID Generator ─────────────────────────────────────────────────────

class EventIdGenerator:
    """Thread-safe event ID generator following EVT-YYYYMMDDHHmmss-SEQ format."""

    def __init__(self):
        self._lock = threading.Lock()
        self._last_timestamp: str = ""
        self._sequence: int = 0

    def generate(self) -> str:
        """Generate next event ID."""
        with self._lock:
            now = datetime.now(timezone.utc)
            ts_str = now.strftime("%Y%m%d%H%M%S")

            if ts_str == self._last_timestamp:
                self._sequence += 1
            else:
                self._last_timestamp = ts_str
                self._sequence = 1

            if self._sequence > 999:
                # Overflow - shouldn't happen in practice at 30fps
                self._sequence = 1

            return f"EVT-{ts_str}-{self._sequence:03d}"


# Global event ID generator instance
_event_id_gen = EventIdGenerator()


def generate_event_id() -> str:
    """Generate a unique event ID."""
    return _event_id_gen.generate()


def generate_timestamp() -> str:
    """Generate ISO 8601 UTC timestamp with millisecond precision."""
    now = datetime.now(timezone.utc)
    return now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"


# ─── Data Classes ────────────────────────────────────────────────────────────

@dataclass
class BBox:
    """Normalized bounding box (0.0~1.0)."""
    x: float
    y: float
    w: float
    h: float


@dataclass
class PGIEResult:
    """Primary GIE inference result."""
    class_id: int
    confidence: float
    label: str
    bbox: BBox


@dataclass
class TrackerResult:
    """Object tracker state."""
    object_id: int
    age_frames: int


@dataclass
class InferenceResult:
    """Complete inference result for stream:ds-events."""
    pgie: PGIEResult
    tracker: TrackerResult
    sgie: Optional[dict] = None  # Reserved for Platform 2.0+


@dataclass
class DSEvent:
    """
    DeepStream event message for stream:ds-events.

    Follows redis-streams-schema.md Section 1 exactly.
    """
    event_id: str
    site_id: str
    source_id: str  # e.g., "pipeline-0"
    device_id: str  # e.g., "CAM-001"
    event_type: str
    timestamp: str
    model_version: str
    inference: InferenceResult
    analytics: Optional[dict] = None  # Reserved for Platform 2.0+

    def to_redis_dict(self) -> dict:
        """
        Convert to flat dict for Redis XADD.

        Redis Streams stores fields as flat key-value strings.
        Nested objects are JSON-serialized.
        """
        import json

        inference_dict = {
            "pgie": {
                "class_id": self.inference.pgie.class_id,
                "confidence": self.inference.pgie.confidence,
                "label": self.inference.pgie.label,
                "bbox": asdict(self.inference.pgie.bbox),
            },
            "tracker": {
                "object_id": self.inference.tracker.object_id,
                "age_frames": self.inference.tracker.age_frames,
            },
            "sgie": self.inference.sgie,
        }

        return {
            "event_id": self.event_id,
            "site_id": self.site_id,
            "source_id": self.source_id,
            "device_id": self.device_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "model_version": self.model_version,
            "inference": json.dumps(inference_dict),
            "analytics": json.dumps(self.analytics),
        }

    @classmethod
    def from_redis_dict(cls, data: dict) -> "DSEvent":
        """Reconstruct DSEvent from Redis hash fields."""
        import json

        inference_raw = json.loads(data["inference"])
        pgie_raw = inference_raw["pgie"]
        tracker_raw = inference_raw["tracker"]

        return cls(
            event_id=data["event_id"],
            site_id=data["site_id"],
            source_id=data["source_id"],
            device_id=data["device_id"],
            event_type=data["event_type"],
            timestamp=data["timestamp"],
            model_version=data["model_version"],
            inference=InferenceResult(
                pgie=PGIEResult(
                    class_id=pgie_raw["class_id"],
                    confidence=pgie_raw["confidence"],
                    label=pgie_raw["label"],
                    bbox=BBox(**pgie_raw["bbox"]),
                ),
                tracker=TrackerResult(
                    object_id=tracker_raw["object_id"],
                    age_frames=tracker_raw["age_frames"],
                ),
                sgie=inference_raw.get("sgie"),
            ),
            analytics=json.loads(data.get("analytics", "null")),
        )


@dataclass
class DeviceStatusEvent:
    """Device status event (DEVICE_ONLINE / DEVICE_OFFLINE)."""
    event_id: str
    site_id: str
    source_id: str
    device_id: str
    event_type: str  # DEVICE_ONLINE or DEVICE_OFFLINE
    timestamp: str
    model_version: str
    inference: Optional[dict] = field(default=None)
    analytics: Optional[dict] = None

    def to_redis_dict(self) -> dict:
        """Convert to flat dict for Redis XADD."""
        import json

        # For device status events, inference is a minimal placeholder
        inference_placeholder = {
            "pgie": {
                "class_id": -1,
                "confidence": 0.0,
                "label": "device_status",
                "bbox": {"x": 0.0, "y": 0.0, "w": 0.0, "h": 0.0},
            },
            "tracker": {
                "object_id": -1,
                "age_frames": 0,
            },
            "sgie": None,
        }

        return {
            "event_id": self.event_id,
            "site_id": self.site_id,
            "source_id": self.source_id,
            "device_id": self.device_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "model_version": self.model_version,
            "inference": json.dumps(inference_placeholder),
            "analytics": json.dumps(self.analytics),
        }


# ─── Validation ──────────────────────────────────────────────────────────────

def validate_ds_event(event_dict: dict) -> list:
    """
    Validate a stream:ds-events message against schema rules.

    Returns list of validation errors (empty = valid).
    """
    errors = []

    # Required fields
    required = [
        "event_id", "site_id", "source_id", "device_id",
        "event_type", "timestamp", "model_version", "inference"
    ]
    for f in required:
        if f not in event_dict or event_dict[f] is None:
            errors.append(f"Missing required field: {f}")

    if errors:
        return errors

    # Format validation
    if not EVENT_ID_PATTERN.match(event_dict["event_id"]):
        errors.append(
            f"Invalid event_id format: {event_dict['event_id']} "
            f"(expected EVT-YYYYMMDDHHmmss-SEQ)"
        )

    if not SITE_ID_PATTERN.match(event_dict["site_id"]):
        errors.append(f"Invalid site_id format: {event_dict['site_id']}")

    if not DEVICE_ID_PATTERN.match(event_dict["device_id"]):
        errors.append(f"Invalid device_id format: {event_dict['device_id']}")

    if event_dict["event_type"] not in VALID_EVENT_TYPES:
        errors.append(f"Invalid event_type: {event_dict['event_type']}")

    if not MODEL_VERSION_PATTERN.match(event_dict["model_version"]):
        errors.append(
            f"Invalid model_version format: {event_dict['model_version']}"
        )

    # Timestamp format: YYYY-MM-DDTHH:mm:ss.mmmZ
    ts_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$")
    if not ts_pattern.match(event_dict["timestamp"]):
        errors.append(
            f"Invalid timestamp format: {event_dict['timestamp']} "
            f"(expected ISO 8601 UTC with ms)"
        )

    # Consistency: CRITICAL event types must have CRITICAL risk_level
    # (Note: risk_level is in the canonical event, not in ds-events stream directly,
    # but we validate event_type consistency)

    # Inference validation
    import json
    try:
        inference = event_dict["inference"]
        if isinstance(inference, str):
            inference = json.loads(inference)

        pgie = inference.get("pgie")
        if not pgie:
            errors.append("Missing inference.pgie")
        else:
            if not (0.0 <= pgie.get("confidence", -1) <= 1.0):
                errors.append(
                    f"confidence out of range: {pgie.get('confidence')}"
                )
            bbox = pgie.get("bbox", {})
            for k in ("x", "y", "w", "h"):
                val = bbox.get(k)
                if val is None or not (0.0 <= val <= 1.0):
                    if event_dict["event_type"] not in ("DEVICE_ONLINE", "DEVICE_OFFLINE"):
                        errors.append(f"bbox.{k} out of range: {val}")

        tracker = inference.get("tracker")
        if not tracker:
            errors.append("Missing inference.tracker")

    except (json.JSONDecodeError, TypeError) as e:
        errors.append(f"Invalid inference JSON: {e}")

    return errors
