#!/bin/bash
# ============================================================
# Platform 1.0 Local Test Environment
# ============================================================
# Docker Compose 기반 테스트 환경 시작/중지
#
# Usage:
#   ./scripts/start-local-test-env.sh up      # 환경 시작
#   ./scripts/start-local-test-env.sh down    # 환경 중지
#   ./scripts/start-local-test-env.sh status  # 상태 확인
#   ./scripts/start-local-test-env.sh reset   # 초기화 후 재시작
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

COMPOSE_FILE="docker-compose.test.yml"
ACTION="${1:-up}"

echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN} Platform 1.0 Test Environment Manager${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""

case "$ACTION" in
    up)
        echo -e "${BLUE}Starting test environment...${NC}"
        docker-compose -f "$COMPOSE_FILE" up -d

        echo -e "${YELLOW}Waiting for services to be healthy...${NC}"
        sleep 3

        # Check Redis
        if docker exec safety-redis-test redis-cli ping | grep -q PONG; then
            echo -e "${GREEN}  ✅ Redis (port 6380): READY${NC}"
        else
            echo -e "${RED}  ❌ Redis: NOT READY${NC}"
        fi

        # Check PostgreSQL
        if docker exec safety-postgres-test pg_isready -U safety_test | grep -q "accepting"; then
            echo -e "${GREEN}  ✅ PostgreSQL (port 5433): READY${NC}"
        else
            echo -e "${RED}  ❌ PostgreSQL: NOT READY${NC}"
        fi

        echo ""
        echo -e "${GREEN}Test environment ready!${NC}"
        echo -e "  Redis:      localhost:6380"
        echo -e "  PostgreSQL: localhost:5433 (db: safety_test, user: safety_test)"
        echo ""
        echo -e "Run tests with: ${YELLOW}./scripts/run-integration-tests.sh --all${NC}"
        ;;

    down)
        echo -e "${BLUE}Stopping test environment...${NC}"
        docker-compose -f "$COMPOSE_FILE" down
        echo -e "${GREEN}Test environment stopped.${NC}"
        ;;

    status)
        echo -e "${BLUE}Test environment status:${NC}"
        docker-compose -f "$COMPOSE_FILE" ps
        ;;

    reset)
        echo -e "${YELLOW}Resetting test environment...${NC}"
        docker-compose -f "$COMPOSE_FILE" down -v
        docker-compose -f "$COMPOSE_FILE" up -d
        sleep 3
        echo -e "${GREEN}Test environment reset complete.${NC}"
        ;;

    *)
        echo -e "${RED}Unknown action: $ACTION${NC}"
        echo "Usage: $0 {up|down|status|reset}"
        exit 1
        ;;
esac
