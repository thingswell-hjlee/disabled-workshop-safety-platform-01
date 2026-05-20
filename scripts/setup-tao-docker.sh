#!/usr/bin/env bash
# =============================================================================
# setup-tao-docker.sh
# Platform 1.0 - TAO Toolkit Docker 실행 스크립트
#
# Usage:
#   ./scripts/setup-tao-docker.sh interactive   # 대화형 세션
#   ./scripts/setup-tao-docker.sh train <spec>  # 학습 실행
#   ./scripts/setup-tao-docker.sh export <model_path> <output_path>
#   ./scripts/setup-tao-docker.sh evaluate <model_path> <spec>
#   ./scripts/setup-tao-docker.sh convert <onnx_path> <engine_path>
# =============================================================================

set -euo pipefail

# --- Configuration ---
TAO_IMAGE="nvcr.io/nvidia/tao/tao-toolkit:5.5.0-tf2.11.0"
TRT_IMAGE="nvcr.io/nvidia/tensorrt:24.05-py3"
CONTAINER_NAME="safety-tao-training"
TRT_CONTAINER_NAME="safety-tensorrt-converter"
ENCRYPTION_KEY="${TAO_KEY:-tlt_encode}"
NUM_GPUS="${NUM_GPUS:-1}"
GPU_INDEX="${GPU_INDEX:-0}"

# Project paths (relative to project root)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DATASETS_DIR="$PROJECT_ROOT/services/training-pipeline/datasets"
CONFIGS_DIR="$PROJECT_ROOT/services/training-pipeline/configs"
MODELS_DIR="$PROJECT_ROOT/models"
EXPERIMENTS_DIR="${TAO_EXPERIMENTS_DIR:-/tmp/tao-experiments}"

# Ensure experiments directory exists
mkdir -p "$EXPERIMENTS_DIR"

# --- Functions ---
check_prerequisites() {
    echo "[CHECK] Verifying prerequisites..."
    
    # Docker
    if ! command -v docker &> /dev/null; then
        echo "[ERROR] Docker not installed"
        exit 1
    fi
    
    # NVIDIA Docker runtime
    if ! docker info 2>/dev/null | grep -q "nvidia"; then
        echo "[WARN] NVIDIA runtime not detected. GPU access may not work."
    fi
    
    # GPU access
    if ! nvidia-smi &> /dev/null; then
        echo "[WARN] nvidia-smi not available. GPU features will be limited."
    fi
    
    echo "[CHECK] Prerequisites OK"
}

pull_images() {
    echo "[PULL] Pulling Docker images..."
    docker pull "$TAO_IMAGE" || echo "[WARN] Failed to pull TAO image. Using cached version."
    docker pull "$TRT_IMAGE" || echo "[WARN] Failed to pull TRT image. Using cached version."
}

run_interactive() {
    echo "[RUN] Starting TAO interactive session..."
    echo "  Container: $CONTAINER_NAME"
    echo "  Image: $TAO_IMAGE"
    echo "  Mounts:"
    echo "    datasets → /workspace/datasets"
    echo "    configs  → /workspace/configs"
    echo "    models   → /workspace/models"
    echo "    experiments → /workspace/experiments"
    echo ""
    
    docker run --rm -it \
        --name "$CONTAINER_NAME" \
        --gpus "device=$GPU_INDEX" \
        --shm-size=8g \
        -e "KEY=$ENCRYPTION_KEY" \
        -e "NUM_GPUS=$NUM_GPUS" \
        -v "$DATASETS_DIR:/workspace/datasets" \
        -v "$CONFIGS_DIR:/workspace/configs" \
        -v "$MODELS_DIR:/workspace/models" \
        -v "$EXPERIMENTS_DIR:/workspace/experiments" \
        -w /workspace \
        "$TAO_IMAGE" \
        /bin/bash
}

run_train() {
    local spec_file="${1:-}"
    if [ -z "$spec_file" ]; then
        echo "[ERROR] Training spec file required"
        echo "Usage: $0 train <spec_file>"
        exit 1
    fi
    
    echo "[TRAIN] Starting training..."
    echo "  Spec: $spec_file"
    
    docker run --rm \
        --name "$CONTAINER_NAME" \
        --gpus "device=$GPU_INDEX" \
        --shm-size=8g \
        -e "KEY=$ENCRYPTION_KEY" \
        -e "NUM_GPUS=$NUM_GPUS" \
        -v "$DATASETS_DIR:/workspace/datasets" \
        -v "$CONFIGS_DIR:/workspace/configs" \
        -v "$MODELS_DIR:/workspace/models" \
        -v "$EXPERIMENTS_DIR:/workspace/experiments" \
        -w /workspace \
        "$TAO_IMAGE" \
        detectnet_v2 train \
        -e "/workspace/configs/$spec_file" \
        -r /workspace/experiments/detectnet_v2 \
        -k "$ENCRYPTION_KEY" \
        -n model \
        --gpus "$NUM_GPUS"
}

run_export() {
    local model_path="${1:-}"
    local output_path="${2:-/workspace/models/export/safety_detector.onnx}"
    
    if [ -z "$model_path" ]; then
        echo "[ERROR] Model path required"
        echo "Usage: $0 export <model_path> [output_path]"
        exit 1
    fi
    
    echo "[EXPORT] Exporting model to ONNX..."
    echo "  Model: $model_path"
    echo "  Output: $output_path"
    
    docker run --rm \
        --name "$CONTAINER_NAME" \
        --gpus "device=$GPU_INDEX" \
        -e "KEY=$ENCRYPTION_KEY" \
        -v "$CONFIGS_DIR:/workspace/configs" \
        -v "$MODELS_DIR:/workspace/models" \
        -v "$EXPERIMENTS_DIR:/workspace/experiments" \
        -w /workspace \
        "$TAO_IMAGE" \
        detectnet_v2 export \
        -m "$model_path" \
        -o "$output_path" \
        -k "$ENCRYPTION_KEY" \
        --data_type fp16 \
        --batch_size 8 \
        --max_batch_size 8 \
        --input_dims "3,544,960"
}

run_evaluate() {
    local model_path="${1:-}"
    local spec_file="${2:-}"
    
    if [ -z "$model_path" ] || [ -z "$spec_file" ]; then
        echo "[ERROR] Model path and spec file required"
        echo "Usage: $0 evaluate <model_path> <spec_file>"
        exit 1
    fi
    
    echo "[EVAL] Evaluating model..."
    
    docker run --rm \
        --name "$CONTAINER_NAME" \
        --gpus "device=$GPU_INDEX" \
        -e "KEY=$ENCRYPTION_KEY" \
        -v "$DATASETS_DIR:/workspace/datasets" \
        -v "$CONFIGS_DIR:/workspace/configs" \
        -v "$MODELS_DIR:/workspace/models" \
        -v "$EXPERIMENTS_DIR:/workspace/experiments" \
        -w /workspace \
        "$TAO_IMAGE" \
        detectnet_v2 evaluate \
        -m "$model_path" \
        -e "/workspace/configs/$spec_file" \
        -k "$ENCRYPTION_KEY"
}

run_convert() {
    local onnx_path="${1:-}"
    local engine_path="${2:-}"
    
    if [ -z "$onnx_path" ] || [ -z "$engine_path" ]; then
        echo "[ERROR] ONNX path and engine output path required"
        echo "Usage: $0 convert <onnx_path> <engine_path>"
        exit 1
    fi
    
    echo "[CONVERT] Converting ONNX to TensorRT..."
    echo "  ONNX: $onnx_path"
    echo "  Engine: $engine_path"
    
    docker run --rm \
        --name "$TRT_CONTAINER_NAME" \
        --gpus "device=$GPU_INDEX" \
        -v "$MODELS_DIR:/workspace/models" \
        -w /workspace \
        "$TRT_IMAGE" \
        /usr/src/tensorrt/bin/trtexec \
        --onnx="$onnx_path" \
        --saveEngine="$engine_path" \
        --fp16 \
        --workspace=4096 \
        --minShapes=input:1x3x544x960 \
        --optShapes=input:8x3x544x960 \
        --maxShapes=input:8x3x544x960 \
        --verbose
}

# --- Main ---
ACTION="${1:-help}"
shift || true

case "$ACTION" in
    interactive)
        check_prerequisites
        run_interactive
        ;;
    train)
        check_prerequisites
        run_train "$@"
        ;;
    export)
        check_prerequisites
        run_export "$@"
        ;;
    evaluate)
        check_prerequisites
        run_evaluate "$@"
        ;;
    convert)
        check_prerequisites
        run_convert "$@"
        ;;
    pull)
        pull_images
        ;;
    help|*)
        echo "TAO Toolkit Docker Runner - Platform 1.0"
        echo ""
        echo "Usage: $0 <action> [options]"
        echo ""
        echo "Actions:"
        echo "  interactive          Start interactive TAO session"
        echo "  train <spec>         Run training with spec file"
        echo "  export <model> [out] Export model to ONNX"
        echo "  evaluate <model> <spec>  Evaluate model"
        echo "  convert <onnx> <engine>  Convert ONNX to TensorRT"
        echo "  pull                 Pull Docker images"
        echo "  help                 Show this help"
        echo ""
        echo "Environment Variables:"
        echo "  TAO_KEY              TAO encryption key (default: tlt_encode)"
        echo "  NUM_GPUS             Number of GPUs (default: 1)"
        echo "  GPU_INDEX            GPU device index (default: 0)"
        echo "  TAO_EXPERIMENTS_DIR  Experiments directory (default: /tmp/tao-experiments)"
        ;;
esac
