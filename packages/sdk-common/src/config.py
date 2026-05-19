"""Configuration Loader - YAML 설정 파일 로더 (환경변수 치환 지원)"""
import os
import re
import yaml
from pathlib import Path
from typing import Any, Dict, Optional


def _resolve_env_vars(value: str) -> str:
    """
    문자열 내 ${VAR:-default} 패턴을 환경변수 값으로 치환.

    Examples:
        "${REDIS_HOST:-localhost}" → "my-redis-host" (if env set)
        "${REDIS_HOST:-localhost}" → "localhost" (if env not set)
    """
    pattern = r"\$\{([^}:]+)(?::-(.*?))?\}"

    def replacer(match):
        var_name = match.group(1)
        default_value = match.group(2) if match.group(2) is not None else ""
        return os.environ.get(var_name, default_value)

    if isinstance(value, str):
        return re.sub(pattern, replacer, value)
    return value


def _resolve_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    """재귀적으로 dict 내 모든 문자열의 환경변수를 치환."""
    resolved = {}
    for key, value in d.items():
        if isinstance(value, dict):
            resolved[key] = _resolve_dict(value)
        elif isinstance(value, list):
            resolved[key] = [
                _resolve_dict(item) if isinstance(item, dict)
                else _resolve_env_vars(item) if isinstance(item, str)
                else item
                for item in value
            ]
        elif isinstance(value, str):
            resolved[key] = _resolve_env_vars(value)
        else:
            resolved[key] = value
    return resolved


def load_config(
    config_path: str,
    resolve_env: bool = True,
) -> Dict[str, Any]:
    """
    YAML 설정 파일 로드.

    Args:
        config_path: 설정 파일 경로
        resolve_env: True이면 ${VAR:-default} 패턴 치환

    Returns:
        설정 딕셔너리

    Raises:
        FileNotFoundError: 파일이 존재하지 않을 때
        yaml.YAMLError: YAML 파싱 실패 시
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    if config is None:
        return {}

    if resolve_env:
        config = _resolve_dict(config)

    return config


def get_config_value(config: Dict[str, Any], key_path: str, default: Any = None) -> Any:
    """
    dot-notation으로 중첩 설정값 조회.

    Args:
        config: 설정 딕셔너리
        key_path: "redis.host" 형태의 키 경로
        default: 키가 없을 때 반환할 기본값

    Returns:
        설정값 또는 default
    """
    keys = key_path.split(".")
    current = config
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current
