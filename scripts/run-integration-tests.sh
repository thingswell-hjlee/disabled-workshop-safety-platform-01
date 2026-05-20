#!/bin/bash
# ============================================================
# Platform 1.0 Integration Tests
# ============================================================
# 통합 테스트 실행 (fakeredis 기반 → 외부 의존성 없음)
# PostgreSQL 테스트는 docker-compose 환경 필요
#
# Usage:
#   ./scripts/run-integration-tests.sh          # fakeredis만 (기본)
#   ./scripts/run-integration-tests.sh --all    # PostgreSQL 포함
#   ./scripts/run-integration-tests.sh --e2e    # E2E만 실행
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN} Platform 1.0 Integration Tests${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Check dependencies
if ! python3 -c "import pydantic; import fakeredis" 2>/dev/null; then
    echo -e "${YELLOW}Installing test dependencies...${NC}"
    pip3 install -r requirements-test.txt --quiet
fi

MODE="${1:-default}"

case "$MODE" in
    --all)
        echo -e "${BLUE}Mode: ALL (integration + e2e + PostgreSQL)${NC}"
        echo -e "${YELLOW}Note: Requires docker-compose test environment${NC}"
        echo ""
        python3 -m pytest tests/integration/ tests/e2e/ -v --tb=short \
            --html=reports/integration-test-report.html --self-contained-html 2>/dev/null || \
        python3 -m pytest tests/integration/ tests/e2e/ -v --tb=short
        ;;
    --e2e)
        echo -e "${BLUE}Mode: E2E only${NC}"
        echo ""
        python3 -m pytest tests/e2e/ -v --tb=short
        ;;
    --no-postgres)
        echo -e "${BLUE}Mode: Integration without PostgreSQL${NC}"
        echo ""
        python3 -m pytest tests/integration/ tests/e2e/ -v --tb=short -k "not Postgres"
        ;;
    *)
        echo -e "${BLUE}Mode: Default (fakeredis, no PostgreSQL)${NC}"
        echo ""
        python3 -m pytest tests/integration/ tests/e2e/ -v --tb=short -k "not Postgres"
        ;;
esac

EXIT_CODE=$?

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ Integration tests PASSED${NC}"
else
    echo -e "${RED}❌ Integration tests FAILED${NC}"
fi

exit $EXIT_CODE
