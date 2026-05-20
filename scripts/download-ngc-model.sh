#!/usr/bin/env bash
# =============================================================================
# download-ngc-model.sh
# Platform 1.0 - NGC Pretrained Model Download Script
#
# Usage:
#   ./scripts/download-ngc-model.sh peoplenet      # Download PeopleNet v2.6
#   ./scripts/download-ngc-model.sh detectnet_v2   # Download DetectNet_v2
#   ./scripts/download-ngc-model.sh all            # Download all recommended models
#   ./scripts/download-ngc-model.sh --list         # List available models
#
# Prerequisites:
#   - NGC CLI installed (ngc --version)
#   - NGC API Key configured (ngc config set or NGC_API_KEY env)
# =============================================================================

set -euo pipefail

# --- Configuration ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
MODELS_DIR="$PROJECT_ROOT/models/pretrained"

# Model definitions
declare -A MODEL_PATHS=(
    ["peoplenet"]="nvidia/tao/peoplenet:trainable_v2.6"
    ["detectnet_v2"]="nvidia/tao/pretrained_detectnet_v2:resnet18"
    ["yolov4"]="nvidia/tao/pretrained_object_detection:yolov4"
    ["actionrecognition"]="nvidia/tao/actionrecognitionnet:trainable_v2.0"
)

declare -A MODEL_DESCRIPTIONS=(
    ["peoplenet"]="PeopleNet v2.6 - 사람 감지 (Platform 1.0 권장 Base)"
    ["detectnet_v2"]="DetectNet_v2 ResNet18 - 경량 객체 감지"
    ["yolov4"]="YOLOv4 - 범용 객체 감지"
    ["actionrecognition"]="ActionRecognitionNet - 행동 인식"
)

# --- Functions ---
check_ngc() {
    if ! command -v ngc &> /dev/null; then
        echo "[ERROR] NGC CLI not installed."
        echo ""
        echo "Install NGC CLI:"
        echo "  wget -q https://api.ngc.nvidia.com/v2/resources/nvidia/ngc-apps/ngc_cli/versions/3.41.2/files/ngccli_linux.zip -O /tmp/ngccli.zip"
        echo "  unzip -q /tmp/ngccli.zip -d /usr/local/bin/"
        echo "  chmod +x /usr/local/bin/ngc-cli/ngc"
        echo ""
        echo "Configure NGC:"
        echo "  ngc config set"
        echo "  (Enter your NGC API Key)"
        exit 1
    fi
    
    # Check if configured
    if [ -z "${NGC_API_KEY:-}" ] && [ ! -f "$HOME/.ngc/config" ]; then
        echo "[ERROR] NGC not configured."
        echo ""
        echo "Options:"
        echo "  1. Run: ngc config set"
        echo "  2. Set environment: export NGC_API_KEY=<your-key>"
        exit 1
    fi
    
    echo "[CHECK] NGC CLI OK"
}

list_models() {
    echo "Available Pretrained Models for Platform 1.0:"
    echo ""
    echo "┌──────────────────┬──────────────────────────────────────────────────┐"
    echo "│ Model ID         │ Description                                      │"
    echo "├──────────────────┼──────────────────────────────────────────────────┤"
    for model_id in "${!MODEL_DESCRIPTIONS[@]}"; do
        printf "│ %-16s │ %-48s │\n" "$model_id" "${MODEL_DESCRIPTIONS[$model_id]}"
    done
    echo "└──────────────────┴──────────────────────────────────────────────────┘"
    echo ""
    echo "Usage: $0 <model_id>"
}

download_model() {
    local model_id="$1"
    local ngc_path="${MODEL_PATHS[$model_id]:-}"
    
    if [ -z "$ngc_path" ]; then
        echo "[ERROR] Unknown model: $model_id"
        list_models
        exit 1
    fi
    
    local dest_dir="$MODELS_DIR/${model_id}"
    
    echo "[DOWNLOAD] $model_id"
    echo "  NGC Path: $ngc_path"
    echo "  Dest:     $dest_dir"
    echo ""
    
    # Check if already downloaded
    if [ -d "$dest_dir" ] && [ "$(ls -A "$dest_dir" 2>/dev/null)" ]; then
        echo "  [INFO] Model already exists at $dest_dir"
        read -p "  Overwrite? [y/N] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "  Skipped."
            return 0
        fi
        rm -rf "$dest_dir"
    fi
    
    mkdir -p "$dest_dir"
    
    # Download using NGC CLI
    echo "  Downloading..."
    ngc registry model download-version "$ngc_path" --dest "$dest_dir" || {
        echo "  [ERROR] Download failed for $model_id"
        echo "  Check NGC authentication and network connectivity."
        return 1
    }
    
    echo "  [OK] Downloaded: $dest_dir"
    echo "  Files:"
    find "$dest_dir" -type f | while read -r f; do
        local size
        size=$(stat --printf="%s" "$f" 2>/dev/null || stat -f%z "$f" 2>/dev/null || echo "?")
        echo "    $(basename "$f") ($size bytes)"
    done
    echo ""
}

download_all() {
    echo "Downloading all recommended models..."
    echo ""
    
    local success=0
    local failed=0
    
    for model_id in "peoplenet" "detectnet_v2"; do
        if download_model "$model_id"; then
            ((success++))
        else
            ((failed++))
        fi
    done
    
    echo ""
    echo "============================================="
    echo " Download Summary"
    echo " Success: $success"
    echo " Failed:  $failed"
    echo "============================================="
}

# --- Main ---
ACTION="${1:---list}"

case "$ACTION" in
    --list|-l|list)
        list_models
        ;;
    all)
        check_ngc
        download_all
        ;;
    --help|-h|help)
        echo "NGC Model Download Script - Platform 1.0"
        echo ""
        echo "Usage: $0 <model_id|all|--list>"
        echo ""
        list_models
        ;;
    *)
        check_ngc
        download_model "$ACTION"
        ;;
esac
