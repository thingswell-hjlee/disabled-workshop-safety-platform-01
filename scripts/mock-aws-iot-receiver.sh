#!/bin/bash
# ============================================================
# Mock AWS IoT Receiver - Start Script
# 로컬 Mosquitto broker에 연결하여 IoT Core를 모사합니다.
#
# Prerequisites:
#   - docker compose up mosquitto (또는 로컬 mosquitto 실행)
#   - pip install paho-mqtt
#
# Usage:
#   ./scripts/mock-aws-iot-receiver.sh
#   ./scripts/mock-aws-iot-receiver.sh --host 192.168.1.10 --port 1883
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Default values (can be overridden by env or args)
MQTT_HOST="${MQTT_BROKER_HOST:-localhost}"
MQTT_PORT="${MQTT_BROKER_PORT:-1883}"

echo "Starting Mock AWS IoT Receiver..."
echo "  Broker: ${MQTT_HOST}:${MQTT_PORT}"
echo ""

python3 "${PROJECT_ROOT}/infra/aws/iot/mock-receiver.py" \
    --host "${MQTT_HOST}" \
    --port "${MQTT_PORT}" \
    "$@"
