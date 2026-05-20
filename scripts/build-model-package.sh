#!/usr/bin/env bash
# =============================================================================
# build-model-package.sh
# Platform 1.0 - 모델 패키지 빌드 스크립트
#
# 학습 완료된 모델을 model-package-schema.md 규격에 맞는 배포 패키지로 조립합니다.
#
# Usage:
#   ./scripts/build-model-package.sh \
#     --version v1.0.0-tao-ds \
#     --engine /path/to/model.engine \
#     --output /models/staged/v1.0.0-tao-ds
#
# Options:
#   --version       모델 버전 (v{M}.{m}.{p}-{tool}-{target})
#   --engine        TensorRT engine 파일 경로
#   --onnx          ONNX 모델 경로 (optional, for cloud target)
#   --output        출력 패키지 경로
#   --site-id       사이트 ID (default: SITE-001)
#   --precision     정밀도 (default: FP16)
#   --framework     학습 프레임워크 (default: TAO)
#   --metrics-file  학습 메트릭 JSON 파일 경로 (optional)
# =============================================================================

set -euo pipefail

# --- Defaults ---
SITE_ID="SITE-001"
PRECISION="FP16"
FRAMEWORK="TAO"
MODEL_NAME="safety_detector"
MODEL_TYPE="pgie"
NUM_CLASSES=6
INPUT_WIDTH=960
INPUT_HEIGHT=544
INPUT_CHANNELS=3
METRICS_FILE=""
ENGINE_PATH=""
ONNX_PATH=""
OUTPUT_PATH=""
MODEL_VERSION=""

# --- Parse Arguments ---
while [[ $# -gt 0 ]]; do
    case $1 in
        --version) MODEL_VERSION="$2"; shift 2 ;;
        --engine) ENGINE_PATH="$2"; shift 2 ;;
        --onnx) ONNX_PATH="$2"; shift 2 ;;
        --output) OUTPUT_PATH="$2"; shift 2 ;;
        --site-id) SITE_ID="$2"; shift 2 ;;
        --precision) PRECISION="$2"; shift 2 ;;
        --framework) FRAMEWORK="$2"; shift 2 ;;
        --metrics-file) METRICS_FILE="$2"; shift 2 ;;
        -h|--help)
            echo "Usage: $0 --version <ver> --engine <path> --output <path>"
            echo ""
            echo "Options:"
            echo "  --version       Model version (v{M}.{m}.{p}-{tool}-{target})"
            echo "  --engine        TensorRT engine file path"
            echo "  --onnx          ONNX model path (optional)"
            echo "  --output        Output package directory"
            echo "  --site-id       Site ID (default: SITE-001)"
            echo "  --precision     Precision (default: FP16)"
            echo "  --framework     Framework (default: TAO)"
            echo "  --metrics-file  Training metrics JSON file"
            exit 0
            ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

# --- Validation ---
if [ -z "$MODEL_VERSION" ]; then
    echo "[ERROR] --version is required"
    exit 1
fi

if [ -z "$OUTPUT_PATH" ]; then
    echo "[ERROR] --output is required"
    exit 1
fi

# Validate model version format
if ! [[ "$MODEL_VERSION" =~ ^v[0-9]+\.[0-9]+\.[0-9]+-(tao|pretrained|custom)-(ds|cloud)$ ]]; then
    echo "[ERROR] Invalid model version format: $MODEL_VERSION"
    echo "Expected: v{M}.{m}.{p}-{tool}-{target} (e.g., v1.0.0-tao-ds)"
    exit 1
fi

if [ -z "$ENGINE_PATH" ] && [ -z "$ONNX_PATH" ]; then
    echo "[ERROR] Either --engine or --onnx is required"
    exit 1
fi

echo "============================================="
echo " Build Model Package"
echo " Version:   $MODEL_VERSION"
echo " Site:      $SITE_ID"
echo " Precision: $PRECISION"
echo " Framework: $FRAMEWORK"
echo " Output:    $OUTPUT_PATH"
echo "============================================="

# --- Create Directory Structure ---
echo ""
echo "[1/6] Creating directory structure..."
mkdir -p "$OUTPUT_PATH/pgie"
mkdir -p "$OUTPUT_PATH/sgie"

# --- Copy Engine/ONNX File ---
echo "[2/6] Copying model files..."
if [ -n "$ENGINE_PATH" ] && [ -f "$ENGINE_PATH" ]; then
    cp "$ENGINE_PATH" "$OUTPUT_PATH/pgie/model.engine"
    echo "  Copied engine: $ENGINE_PATH"
elif [ -n "$ENGINE_PATH" ]; then
    echo "  [WARN] Engine file not found: $ENGINE_PATH (creating placeholder)"
    echo "PLACEHOLDER: TensorRT engine - $MODEL_VERSION" > "$OUTPUT_PATH/pgie/model.engine"
fi

if [ -n "$ONNX_PATH" ] && [ -f "$ONNX_PATH" ]; then
    cp "$ONNX_PATH" "$OUTPUT_PATH/pgie/model.onnx"
    echo "  Copied ONNX: $ONNX_PATH"
fi

# --- Generate labels.txt ---
echo "[3/6] Generating labels.txt..."
cat > "$OUTPUT_PATH/pgie/labels.txt" << 'EOF'
person
fall
collapse
fire
intrusion
hazardous_action
EOF
echo "  Generated 6 class labels"

# --- Generate config.txt (DeepStream nvinfer) ---
echo "[4/6] Generating config.txt..."
cat > "$OUTPUT_PATH/pgie/config.txt" << EOF
# DeepStream nvinfer Configuration - Safety Detector (PGIE)
# model_version: $MODEL_VERSION | precision: $PRECISION

[property]
gpu-id=0
net-scale-factor=0.0039215697906911373
model-engine-file=/models/active/pgie/model.engine
labelfile-path=/models/active/pgie/labels.txt
batch-size=8
process-mode=1
model-color-format=0
network-mode=1
num-detected-classes=$NUM_CLASSES
interval=0
gie-unique-id=1
output-blob-names=output_cov/Sigmoid;output_bbox/BiasAdd
cluster-mode=2

[class-attrs-all]
pre-cluster-threshold=0.4
topk=20
nms-iou-threshold=0.5
EOF
echo "  Generated DeepStream nvinfer config"

# --- Generate metadata.json ---
echo "[5/6] Generating metadata.json..."
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%S.000Z")

# Calculate checksum
CHECKSUM="sha256:none"
if [ -f "$OUTPUT_PATH/pgie/model.engine" ]; then
    CHECKSUM="sha256:$(sha256sum "$OUTPUT_PATH/pgie/model.engine" | awk '{print $1}')"
fi

# Load metrics if provided
MAP_VAL="0.0"
MAP50_VAL="0.0"
INFER_MS="0.0"
TEST_SIZE="0"
if [ -n "$METRICS_FILE" ] && [ -f "$METRICS_FILE" ]; then
    MAP_VAL=$(python3 -c "import json; d=json.load(open('$METRICS_FILE')); print(d.get('mAP', 0.0))" 2>/dev/null || echo "0.0")
    MAP50_VAL=$(python3 -c "import json; d=json.load(open('$METRICS_FILE')); print(d.get('mAP_50', 0.0))" 2>/dev/null || echo "0.0")
    INFER_MS=$(python3 -c "import json; d=json.load(open('$METRICS_FILE')); print(d.get('inference_time_ms', 0.0))" 2>/dev/null || echo "0.0")
    TEST_SIZE=$(python3 -c "import json; d=json.load(open('$METRICS_FILE')); print(d.get('test_dataset_size', 0))" 2>/dev/null || echo "0")
fi

cat > "$OUTPUT_PATH/pgie/metadata.json" << EOF
{
  "model_version": "$MODEL_VERSION",
  "model_name": "$MODEL_NAME",
  "model_type": "$MODEL_TYPE",
  "framework": "$FRAMEWORK",
  "precision": "$PRECISION",
  "input_dims": {
    "channels": $INPUT_CHANNELS,
    "height": $INPUT_HEIGHT,
    "width": $INPUT_WIDTH
  },
  "classes": ["person", "fall", "collapse", "fire", "intrusion", "hazardous_action"],
  "num_classes": $NUM_CLASSES,
  "created_at": "$TIMESTAMP",
  "checksum": "$CHECKSUM",
  "training_config": {
    "base_model": "peoplenet_v2.6",
    "epochs": 100,
    "batch_size": 8,
    "learning_rate": 0.001,
    "dataset_version": "ds-v1.0"
  },
  "evaluation": {
    "mAP": $MAP_VAL,
    "mAP_50": $MAP50_VAL,
    "inference_time_ms": $INFER_MS,
    "test_dataset_size": $TEST_SIZE
  }
}
EOF
echo "  Generated metadata.json"

# --- Generate registry.json & model_manifest.json ---
echo "[6/6] Generating registry & manifest..."

cat > "$OUTPUT_PATH/registry.json" << EOF
{
  "schema_version": "1.0",
  "site_id": "$SITE_ID",
  "last_updated": "$TIMESTAMP",
  "models": [
    {
      "model_version": "$MODEL_VERSION",
      "model_type": "$MODEL_TYPE",
      "model_name": "$MODEL_NAME",
      "framework": "$FRAMEWORK",
      "precision": "$PRECISION",
      "engine_path": "/models/active/pgie/model.engine",
      "labels_path": "/models/active/pgie/labels.txt",
      "status": "STAGED",
      "deployed_at": "$TIMESTAMP",
      "metrics": {
        "mAP": $MAP_VAL,
        "inference_time_ms": $INFER_MS,
        "fps": 30,
        "classes": $NUM_CLASSES
      }
    }
  ]
}
EOF

cat > "$OUTPUT_PATH/model_manifest.json" << EOF
{
  "schema_version": "1.0",
  "site_id": "$SITE_ID",
  "last_updated": "$TIMESTAMP",
  "models": [
    {
      "model_version": "$MODEL_VERSION",
      "model_type": "$MODEL_TYPE",
      "model_name": "$MODEL_NAME",
      "framework": "$FRAMEWORK",
      "precision": "$PRECISION",
      "engine_path": "/models/active/pgie/model.engine",
      "labels_path": "/models/active/pgie/labels.txt",
      "config_path": "/models/active/pgie/config.txt",
      "status": "STAGED",
      "deployed_at": "$TIMESTAMP",
      "metrics": {
        "mAP": $MAP_VAL,
        "inference_time_ms": $INFER_MS,
        "fps": 30,
        "classes": $NUM_CLASSES
      }
    }
  ]
}
EOF
echo "  Generated registry.json and model_manifest.json"

# --- Summary ---
echo ""
echo "============================================="
echo " Package Build Complete!"
echo "============================================="
echo " Output: $OUTPUT_PATH"
echo ""
echo " Files:"
find "$OUTPUT_PATH" -type f | sort | while read -r f; do
    SIZE=$(stat --printf="%s" "$f" 2>/dev/null || stat -f%z "$f" 2>/dev/null || echo "?")
    echo "   $f ($SIZE bytes)"
done
echo ""
echo " Next steps:"
echo "   1. Validate: ./scripts/validate-model-package.sh $OUTPUT_PATH"
echo "   2. Deploy:   Copy to /models/staged/ on Edge AI server"
echo "   3. Activate: POST /models/{version}/reload"
echo "============================================="
