"""SDK Common - Config Loader Tests"""
import os
import pytest
import tempfile
from src.config import load_config, get_config_value, _resolve_env_vars


class TestResolveEnvVars:
    def test_with_default(self):
        result = _resolve_env_vars("${NONEXIST_VAR:-fallback}")
        assert result == "fallback"

    def test_with_env_set(self, monkeypatch):
        monkeypatch.setenv("TEST_HOST", "my-host")
        result = _resolve_env_vars("${TEST_HOST:-localhost}")
        assert result == "my-host"

    def test_no_default(self):
        result = _resolve_env_vars("${NONEXIST_VAR}")
        assert result == ""

    def test_plain_string(self):
        result = _resolve_env_vars("plain_value")
        assert result == "plain_value"


class TestLoadConfig:
    def test_load_valid_yaml(self, tmp_path):
        config_file = tmp_path / "test.yaml"
        config_file.write_text("service:\n  name: test\n  port: 8001\n")
        config = load_config(str(config_file))
        assert config["service"]["name"] == "test"
        assert config["service"]["port"] == 8001

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            load_config("/nonexistent/path.yaml")

    def test_env_resolution(self, tmp_path, monkeypatch):
        monkeypatch.setenv("MY_PORT", "9999")
        config_file = tmp_path / "test.yaml"
        config_file.write_text("port: ${MY_PORT:-8080}\n")
        config = load_config(str(config_file))
        assert config["port"] == "9999"


class TestGetConfigValue:
    def test_nested_key(self):
        config = {"redis": {"host": "localhost", "port": 6379}}
        assert get_config_value(config, "redis.host") == "localhost"
        assert get_config_value(config, "redis.port") == 6379

    def test_missing_key_default(self):
        config = {"redis": {"host": "localhost"}}
        assert get_config_value(config, "redis.password", "secret") == "secret"

    def test_deep_nested(self):
        config = {"a": {"b": {"c": 42}}}
        assert get_config_value(config, "a.b.c") == 42
