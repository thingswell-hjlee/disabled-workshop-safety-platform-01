"""
Platform 1.0 Integration Test - Shared Configuration & Fixtures
================================================================
Provides pytest markers, shared fixtures, and test environment setup.
"""

import json
import os
from pathlib import Path
from typing import Generator

import pytest

# ──────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────

FIXTURES_DIR = Path(__file__).parent / "fixtures"

REDIS_HOST = os.environ.get("TEST_REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("TEST_REDIS_PORT", "6380"))

POSTGRES_HOST = os.environ.get("TEST_POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.environ.get("TEST_POSTGRES_PORT", "5433"))
POSTGRES_DB = os.environ.get("TEST_POSTGRES_DB", "safety_test")
POSTGRES_USER = os.environ.get("TEST_POSTGRES_USER", "safety_test")
POSTGRES_PASSWORD = os.environ.get("TEST_POSTGRES_PASSWORD", "test_password")

# Redis Stream Names (from PR #16 redis-streams-schema.md)
STREAM_DS_EVENTS = "stream:ds-events"
STREAM_SENSORS = "stream:sensors"
STREAM_ALARMS = "stream:alarms"
STREAM_DASHBOARD = "stream:dashboard"
STREAM_CLOUD_QUEUE = "stream:cloud-queue"
STREAM_CLIP_TRIGGER = "stream:clip-trigger"

ALL_STREAMS = [
    STREAM_DS_EVENTS,
    STREAM_SENSORS,
    STREAM_ALARMS,
    STREAM_DASHBOARD,
    STREAM_CLOUD_QUEUE,
    STREAM_CLIP_TRIGGER,
]


# ──────────────────────────────────────────────────────────────────────
# Fixture Loaders
# ──────────────────────────────────────────────────────────────────────


@pytest.fixture
def valid_events() -> list:
    """Load valid event fixtures from JSON."""
    with open(FIXTURES_DIR / "valid_events.json", "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def invalid_events() -> list:
    """Load invalid event fixtures from JSON."""
    with open(FIXTURES_DIR / "invalid_events.json", "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def redis_stream_messages() -> dict:
    """Load Redis stream message fixtures."""
    with open(FIXTURES_DIR / "redis_stream_messages.json", "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def mqtt_payloads() -> dict:
    """Load MQTT payload fixtures."""
    with open(FIXTURES_DIR / "mqtt_payloads.json", "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def model_registry() -> dict:
    """Load model registry fixture."""
    with open(FIXTURES_DIR / "model_registry.json", "r", encoding="utf-8") as f:
        return json.load(f)


# ──────────────────────────────────────────────────────────────────────
# Redis Fixtures
# ──────────────────────────────────────────────────────────────────────


@pytest.fixture
def fakeredis_client():
    """Provide a fakeredis client for unit/schema tests (no real Redis needed)."""
    import fakeredis

    client = fakeredis.FakeRedis(decode_responses=True)
    yield client
    client.flushall()
    client.close()


@pytest.fixture
def redis_client():
    """Provide a real Redis client for integration tests."""
    import redis

    client = redis.Redis(
        host=REDIS_HOST, port=REDIS_PORT, decode_responses=True, db=0
    )
    try:
        client.ping()
    except redis.ConnectionError:
        pytest.skip(f"Redis not available at {REDIS_HOST}:{REDIS_PORT}")
    yield client
    # Cleanup: delete test streams
    for stream in ALL_STREAMS:
        client.delete(stream)
    client.close()


# ──────────────────────────────────────────────────────────────────────
# PostgreSQL Fixtures
# ──────────────────────────────────────────────────────────────────────


@pytest.fixture
def pg_connection():
    """Provide a PostgreSQL connection for integration tests."""
    try:
        import psycopg2

        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            dbname=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
        )
        conn.autocommit = True
        yield conn
        # Cleanup
        with conn.cursor() as cur:
            cur.execute("DELETE FROM safety_events")
        conn.close()
    except Exception:
        pytest.skip(
            f"PostgreSQL not available at {POSTGRES_HOST}:{POSTGRES_PORT}"
        )
