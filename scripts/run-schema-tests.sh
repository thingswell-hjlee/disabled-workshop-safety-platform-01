#!/bin/bash
# ============================================================
# Platform 1.0 Schema Validation Tests
# ============================================================
# 스키마 검증 테스트만 실행 (외부 의존성 없음)
# Usage: ./scripts/run-schema-tests.sh [--html]
#
# 카테고리별 실행:
#   ./scripts/run-schema-tests.sh format
#   ./scripts/run-schema-tests.sh completeness
#   ./scripts/run-schema-tests.sh consistency
#   ./scripts/run-schema-tests.sh boundary
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN} Platform 1.0 Schema Validation Tests${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Check dependencies
if ! python3 -c "import pydantic" 2>/dev/null; then
    echo -e "${YELLOW}Installing test dependencies...${NC}"
    pip3 install -r requirements-test.txt --quiet
fi

# Determine test scope
MARKER="${1:-}"
HTML_FLAG=""

if [[ "$MARKER" == "--html" ]]; then
    HTML_FLAG="--html=reports/schema-test-report.html --self-contained-html"
    mkdir -p reports
    MARKER=""
elif [[ "$2" == "--html" ]]; then
    HTML_FLAG="--html=reports/schema-test-report.html --self-contained-html"
    mkdir -p reports
fi

if [[ -n "$MARKER" && "$MARKER" != "--html" ]]; then
    echo -e "${YELLOW}Running marker: ${MARKER}${NC}"
    python3 -m pytest tests/schema/ -m "$MARKER" -v --tb=short $HTML_FLAG
else
    echo -e "${YELLOW}Running ALL schema tests${NC}"
    python3 -m pytest tests/schema/ -v --tb=short $HTML_FLAG
fi

EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ Schema validation tests PASSED${NC}"
else
    echo -e "${RED}❌ Schema validation tests FAILED${NC}"
fi

exit $EXIT_CODE
