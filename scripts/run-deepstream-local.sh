#!/bin/bash
# ============================================================
# DeepStream App - Local Execution Script
# Platform 1.0 - Edge Device Software
#
# Usage:
#   ./scripts/run-deepstream-local.sh          # Mock mode (default)
#   ./scripts/run-deepstream-local.sh mock     # Mock mode explicitly
#   ./scripts/run-deepstream-local.sh gpu      # GPU mode (requires NVIDIA GPU)
#
# Prerequisites:
#   - Redis running on localhost:6379
#   - Python 3.11+ with dependencies installed
#   - For GPU mode: NVIDIA GPU + DeepStream SDK
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
APP_DIR="$PROJECT_ROOT/services/deepstream-app"

MODE="${1:-mock}"

echo "============================================"
echo "  DeepStream 8-Channel Safety Pipeline"
echo "  Mode: $MODE"
echo "============================================"

# Check Redis connectivity
echo "[1/3] Checking Redis connection..."
if ! redis-cli ping > /dev/null 2>&1; then
    echo "ERROR: Redis is not running on localhost:6379"
    echo "Start Redis: docker run -d -p 6379:6379 redis:7-alpine"
    exit 1
fi
echo "  Redis: OK"

# Set environment variables
export SITE_ID="${SITE_ID:-SITE-001}"
export REDIS_HOST="${REDIS_HOST:-localhost}"
export REDIS_PORT="${REDIS_PORT:-6379}"
export REDIS_STREAM_NAME="${REDIS_STREAM_NAME:-stream:ds-events}"
export MODEL_VERSION="${MODEL_VERSION:-v1.0.0-tao-ds}"
export HEALTHCHECK_PORT="${HEALTHCHECK_PORT:-8010}"
export LOG_LEVEL="${LOG_LEVEL:-INFO}"
export MAX_CHANNELS="${MAX_CHANNELS:-8}"
export CAMERAS_CONFIG_PATH="${CAMERAS_CONFIG_PATH:-$PROJECT_ROOT/config/cameras.example.json}"

if [ "$MODE" = "mock" ]; then
    export DEEPSTREAM_MOCK_MODE=true
    export MOCK_EVENT_INTERVAL_SEC="${MOCK_EVENT_INTERVAL_SEC:-5.0}"
    echo "  Mock Mode: Events every ${MOCK_EVENT_INTERVAL_SEC}s"
elif [ "$MODE" = "gpu" ]; then
    export DEEPSTREAM_MOCK_MODE=false
    # Check for NVIDIA GPU
    if ! nvidia-smi > /dev/null 2>&1; then
        echo "ERROR: NVIDIA GPU not detected. Use 'mock' mode instead."
        exit 1
    fi
    echo "  GPU: $(nvidia-smi --query-gpu=name --format=csv,noheader | head -1)"
else
    echo "ERROR: Unknown mode '$MODE'. Use 'mock' or 'gpu'."
    exit 1
fi

# Install dependencies if needed
echo "[2/3] Checking dependencies..."
if ! python3 -c "import redis" 2>/dev/null; then
    echo "  Installing dependencies..."
    pip install -r "$APP_DIR/requirements.txt" --quiet
fi
echo "  Dependencies: OK"

# Run the application
echo "[3/3] Starting DeepStream App..."
echo ""
cd "$APP_DIR"
python3 -m src
