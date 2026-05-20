#!/bin/bash
# ============================================================
# RTSP Camera Connection Checker
# Platform 1.0 - Edge Device Software
#
# Usage:
#   ./scripts/check-rtsp-cameras.sh                     # Check all cameras from config
#   ./scripts/check-rtsp-cameras.sh rtsp://ip:port/path # Check single URL
#
# Prerequisites:
#   - ffprobe (from ffmpeg package)
#   - jq (for JSON parsing)
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CONFIG_FILE="${CAMERAS_CONFIG_PATH:-$PROJECT_ROOT/config/cameras.example.json}"

TIMEOUT=5  # seconds

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_single_rtsp() {
    local url="$1"
    local name="${2:-$url}"
    local camera_id="${3:-unknown}"

    printf "  %-10s %-30s " "$camera_id" "$name"

    # Try to probe the RTSP stream
    if ffprobe -v quiet -rtsp_transport tcp -timeout "$((TIMEOUT * 1000000))" \
        -show_streams -select_streams v "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}[CONNECTED]${NC}"
        return 0
    else
        echo -e "${RED}[FAILED]${NC}"
        return 1
    fi
}

echo "============================================"
echo "  RTSP Camera Connection Checker"
echo "============================================"
echo ""

# Check prerequisites
if ! command -v ffprobe &> /dev/null; then
    echo -e "${YELLOW}WARNING: ffprobe not found. Install ffmpeg:${NC}"
    echo "  sudo apt install ffmpeg"
    echo ""
    echo "Falling back to TCP port check..."
    USE_TCP_CHECK=true
fi

# Single URL mode
if [ -n "$1" ] && [[ "$1" == rtsp://* ]]; then
    echo "Checking single URL: $1"
    echo ""
    check_single_rtsp "$1" "Manual Check" "MANUAL"
    exit $?
fi

# Check all cameras from config
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}ERROR: Config file not found: $CONFIG_FILE${NC}"
    echo "Copy config/cameras.example.json to your config path."
    exit 1
fi

echo "Config: $CONFIG_FILE"
echo ""

# Check if jq is available
if ! command -v jq &> /dev/null; then
    echo -e "${RED}ERROR: jq not found. Install: sudo apt install jq${NC}"
    exit 1
fi

# Parse cameras and check each one
TOTAL=0
CONNECTED=0
FAILED=0

echo "Results:"
echo "  ---------- ------------------------------ --------"

while IFS= read -r line; do
    camera_id=$(echo "$line" | jq -r '.camera_id')
    name=$(echo "$line" | jq -r '.name')
    rtsp_url=$(echo "$line" | jq -r '.rtsp_url')
    enabled=$(echo "$line" | jq -r '.enabled')

    if [ "$enabled" = "false" ]; then
        printf "  %-10s %-30s " "$camera_id" "$name"
        echo -e "${YELLOW}[DISABLED]${NC}"
        continue
    fi

    TOTAL=$((TOTAL + 1))

    if [ "$USE_TCP_CHECK" = "true" ]; then
        # Fallback: TCP port check only
        host=$(echo "$rtsp_url" | sed -E 's|rtsp://([^:/]+).*|\1|')
        port=$(echo "$rtsp_url" | sed -E 's|rtsp://[^:]+:([0-9]+).*|\1|')
        port="${port:-554}"

        printf "  %-10s %-30s " "$camera_id" "$name"
        if timeout "$TIMEOUT" bash -c "echo > /dev/tcp/$host/$port" 2>/dev/null; then
            echo -e "${GREEN}[PORT OK]${NC}"
            CONNECTED=$((CONNECTED + 1))
        else
            echo -e "${RED}[UNREACHABLE]${NC}"
            FAILED=$((FAILED + 1))
        fi
    else
        if check_single_rtsp "$rtsp_url" "$name" "$camera_id"; then
            CONNECTED=$((CONNECTED + 1))
        else
            FAILED=$((FAILED + 1))
        fi
    fi
done < <(jq -c '.cameras[]' "$CONFIG_FILE")

echo ""
echo "============================================"
echo "  Summary: $CONNECTED/$TOTAL connected, $FAILED failed"
echo "============================================"

if [ "$FAILED" -gt 0 ]; then
    exit 1
fi
exit 0
