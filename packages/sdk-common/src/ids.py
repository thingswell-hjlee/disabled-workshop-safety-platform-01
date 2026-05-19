"""ID Generation Utilities - Platform 확장 대비 ID 체계"""
import threading
from datetime import datetime, timezone


_seq_lock = threading.Lock()
_seq_counter: dict = {}


def _next_seq(prefix: str) -> int:
    """Thread-safe sequence counter per prefix per second."""
    with _seq_lock:
        now_sec = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        key = f"{prefix}:{now_sec}"
        _seq_counter[key] = _seq_counter.get(key, 0) + 1
        # Cleanup old keys
        for k in list(_seq_counter.keys()):
            if k != key:
                del _seq_counter[k]
        return _seq_counter[key]


def generate_event_id() -> str:
    """
    이벤트 ID 생성.
    Format: EVT-YYYYMMDDHHmmss-SEQ (예: EVT-20250519120000-001)
    """
    now = datetime.now(timezone.utc)
    ts = now.strftime("%Y%m%d%H%M%S")
    seq = _next_seq("EVT")
    return f"EVT-{ts}-{seq:03d}"


def generate_maint_id() -> str:
    """
    유지보수 로그 ID 생성.
    Format: MAINT-YYYYMMDD-SEQ (예: MAINT-20250519-001)
    """
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y%m%d")
    seq = _next_seq("MAINT")
    return f"MAINT-{date_str}-{seq:03d}"


def validate_device_id(device_id: str) -> bool:
    """장비 ID 형식 검증: {TYPE}-{NNN}"""
    import re
    pattern = r"^(CAM|BAND|ENV|FIRE|NVR|ALARM)-\d{3}$"
    return bool(re.match(pattern, device_id))


def validate_site_id(site_id: str) -> bool:
    """현장 ID 형식 검증: SITE-{NNN}"""
    import re
    return bool(re.match(r"^SITE-\d{3}$", site_id))


def validate_worker_id(worker_id: str) -> bool:
    """작업자 ID 형식 검증: WKR-{NNNN}"""
    import re
    return bool(re.match(r"^WKR-\d{4}$", worker_id))


def validate_event_id(event_id: str) -> bool:
    """이벤트 ID 형식 검증: EVT-{14digits}-{3digits}"""
    import re
    return bool(re.match(r"^EVT-\d{14}-\d{3}$", event_id))
