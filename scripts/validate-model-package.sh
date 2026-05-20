#!/usr/bin/env bash
# =============================================================================
# validate-model-package.sh
# Platform 1.0 - 모델 패키지 유효성 검증 스크립트
#
# Usage: ./scripts/validate-model-package.sh <model_package_path>
# Example: ./scripts/validate-model-package.sh models/sample-model-package/
# =============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0

pass() { echo -e "${GREEN}[PASS]${NC} $1"; PASS_COUNT=$((PASS_COUNT + 1)); }
fail() { echo -e "${RED}[FAIL]${NC} $1"; FAIL_COUNT=$((FAIL_COUNT + 1)); }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; WARN_COUNT=$((WARN_COUNT + 1)); }

# --- Argument Check ---
if [ $# -lt 1 ]; then
    echo "Usage: $0 <model_package_path>"
    echo "Example: $0 models/sample-model-package/"
    exit 1
fi

PACKAGE_PATH="${1%/}"

echo "============================================="
echo " Model Package Validation"
echo " Path: $PACKAGE_PATH"
echo "============================================="
echo ""

# --- 1. Directory Structure ---
echo "--- [1/7] Directory Structure ---"

if [ -d "$PACKAGE_PATH" ]; then
    pass "Package directory exists"
else
    fail "Package directory not found: $PACKAGE_PATH"
    exit 1
fi

if [ -d "$PACKAGE_PATH/pgie" ]; then
    pass "pgie/ directory exists"
else
    fail "pgie/ directory missing"
fi

# sgie is optional for Platform 1.0
if [ -d "$PACKAGE_PATH/sgie" ]; then
    pass "sgie/ directory exists (optional)"
else
    warn "sgie/ directory missing (optional for Platform 1.0)"
fi

# --- 2. Required Files ---
echo ""
echo "--- [2/7] Required Files ---"

REQUIRED_FILES=(
    "registry.json"
    "model_manifest.json"
    "pgie/labels.txt"
    "pgie/config.txt"
    "pgie/metadata.json"
    "pgie/model.engine"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$PACKAGE_PATH/$file" ]; then
        pass "$file exists"
    else
        fail "$file missing"
    fi
done

# --- 3. registry.json Schema Validation ---
echo ""
echo "--- [3/7] registry.json Validation ---"

if [ -f "$PACKAGE_PATH/registry.json" ]; then
    # Check required fields
    REGISTRY_FIELDS=("schema_version" "site_id" "last_updated" "models")
    for field in "${REGISTRY_FIELDS[@]}"; do
        if grep -q "\"$field\"" "$PACKAGE_PATH/registry.json"; then
            pass "registry.json contains '$field'"
        else
            fail "registry.json missing field: '$field'"
        fi
    done

    # Validate site_id format
    SITE_ID=$(grep -o '"site_id"[[:space:]]*:[[:space:]]*"[^"]*"' "$PACKAGE_PATH/registry.json" | head -1 | grep -o 'SITE-[0-9]*')
    if [[ "$SITE_ID" =~ ^SITE-[0-9]{3}$ ]]; then
        pass "site_id format valid: $SITE_ID"
    else
        fail "site_id format invalid (expected SITE-NNN)"
    fi
fi

# --- 4. model_manifest.json Validation ---
echo ""
echo "--- [4/7] model_manifest.json Validation ---"

if [ -f "$PACKAGE_PATH/model_manifest.json" ]; then
    MANIFEST_FIELDS=("schema_version" "site_id" "last_updated" "models")
    for field in "${MANIFEST_FIELDS[@]}"; do
        if grep -q "\"$field\"" "$PACKAGE_PATH/model_manifest.json"; then
            pass "model_manifest.json contains '$field'"
        else
            fail "model_manifest.json missing field: '$field'"
        fi
    done

    # Validate model_version format
    MODEL_VERSION=$(grep -o '"model_version"[[:space:]]*:[[:space:]]*"[^"]*"' "$PACKAGE_PATH/model_manifest.json" | head -1 | sed 's/.*"\(v[^"]*\)".*/\1/')
    if [[ "$MODEL_VERSION" =~ ^v[0-9]+\.[0-9]+\.[0-9]+-(tao|pretrained|custom)-(ds|cloud)$ ]]; then
        pass "model_version format valid: $MODEL_VERSION"
    else
        fail "model_version format invalid: '$MODEL_VERSION' (expected v{M}.{m}.{p}-{tool}-{target})"
    fi

    # Check model status
    if grep -q '"status"[[:space:]]*:[[:space:]]*"ACTIVE"\|"status"[[:space:]]*:[[:space:]]*"STAGED"\|"status"[[:space:]]*:[[:space:]]*"ROLLBACK"' "$PACKAGE_PATH/model_manifest.json"; then
        pass "Model status is valid"
    else
        fail "Model status invalid (expected ACTIVE|STAGED|ROLLBACK)"
    fi
fi

# --- 5. labels.txt Validation ---
echo ""
echo "--- [5/7] labels.txt Validation ---"

if [ -f "$PACKAGE_PATH/pgie/labels.txt" ]; then
    LABEL_COUNT=$(wc -l < "$PACKAGE_PATH/pgie/labels.txt" | tr -d ' ')
    if [ "$LABEL_COUNT" -eq 6 ]; then
        pass "labels.txt has 6 classes"
    else
        fail "labels.txt has $LABEL_COUNT classes (expected 6)"
    fi

    # Check required class names
    EXPECTED_CLASSES=("person" "fall" "collapse" "fire" "intrusion" "hazardous_action")
    for class_name in "${EXPECTED_CLASSES[@]}"; do
        if grep -q "^${class_name}$" "$PACKAGE_PATH/pgie/labels.txt"; then
            pass "Class '$class_name' found in labels.txt"
        else
            fail "Class '$class_name' missing from labels.txt"
        fi
    done
fi

# --- 6. metadata.json Validation ---
echo ""
echo "--- [6/7] metadata.json Validation ---"

if [ -f "$PACKAGE_PATH/pgie/metadata.json" ]; then
    META_FIELDS=("model_version" "model_name" "model_type" "framework" "precision" "input_dims" "classes" "num_classes" "created_at" "checksum")
    for field in "${META_FIELDS[@]}"; do
        if grep -q "\"$field\"" "$PACKAGE_PATH/pgie/metadata.json"; then
            pass "metadata.json contains '$field'"
        else
            fail "metadata.json missing field: '$field'"
        fi
    done

    # Check num_classes matches labels
    NUM_CLASSES=$(grep -o '"num_classes"[[:space:]]*:[[:space:]]*[0-9]*' "$PACKAGE_PATH/pgie/metadata.json" | grep -o '[0-9]*$')
    if [ "$NUM_CLASSES" = "6" ]; then
        pass "num_classes = 6 (matches labels.txt)"
    else
        fail "num_classes = $NUM_CLASSES (expected 6)"
    fi

    # Check input dimensions
    if grep -q '"height"[[:space:]]*:[[:space:]]*544' "$PACKAGE_PATH/pgie/metadata.json" && \
       grep -q '"width"[[:space:]]*:[[:space:]]*960' "$PACKAGE_PATH/pgie/metadata.json"; then
        pass "Input dimensions: 960x544 (correct)"
    else
        warn "Input dimensions differ from standard 960x544"
    fi
fi

# --- 7. Model Version Rule Validation ---
echo ""
echo "--- [7/7] Cross-validation ---"

if [ -f "$PACKAGE_PATH/model_manifest.json" ] && [ -f "$PACKAGE_PATH/pgie/metadata.json" ]; then
    MANIFEST_VER=$(grep -o '"model_version"[[:space:]]*:[[:space:]]*"[^"]*"' "$PACKAGE_PATH/model_manifest.json" | head -1 | sed 's/.*"\(v[^"]*\)".*/\1/')
    META_VER=$(grep -o '"model_version"[[:space:]]*:[[:space:]]*"[^"]*"' "$PACKAGE_PATH/pgie/metadata.json" | head -1 | sed 's/.*"\(v[^"]*\)".*/\1/')

    if [ "$MANIFEST_VER" = "$META_VER" ]; then
        pass "model_version consistent across files: $MANIFEST_VER"
    else
        fail "model_version mismatch: manifest=$MANIFEST_VER, metadata=$META_VER"
    fi
fi

if [ -f "$PACKAGE_PATH/registry.json" ] && [ -f "$PACKAGE_PATH/model_manifest.json" ]; then
    REG_SITE=$(grep -o '"site_id"[[:space:]]*:[[:space:]]*"[^"]*"' "$PACKAGE_PATH/registry.json" | head -1 | sed 's/.*"\(SITE-[^"]*\)".*/\1/')
    MAN_SITE=$(grep -o '"site_id"[[:space:]]*:[[:space:]]*"[^"]*"' "$PACKAGE_PATH/model_manifest.json" | head -1 | sed 's/.*"\(SITE-[^"]*\)".*/\1/')

    if [ "$REG_SITE" = "$MAN_SITE" ]; then
        pass "site_id consistent: $REG_SITE"
    else
        fail "site_id mismatch: registry=$REG_SITE, manifest=$MAN_SITE"
    fi
fi

# --- Summary ---
echo ""
echo "============================================="
echo " Validation Summary"
echo "============================================="
echo -e " ${GREEN}PASS:${NC} $PASS_COUNT"
echo -e " ${RED}FAIL:${NC} $FAIL_COUNT"
echo -e " ${YELLOW}WARN:${NC} $WARN_COUNT"
echo "============================================="

if [ $FAIL_COUNT -gt 0 ]; then
    echo -e "${RED}VALIDATION FAILED${NC}"
    exit 1
else
    echo -e "${GREEN}VALIDATION PASSED${NC}"
    exit 0
fi
