#!/bin/bash
# ============================================================
# Initialize Local PostgreSQL for Development
#
# Docker로 PostgreSQL을 실행하고 Platform 1.0 스키마를 적용합니다.
#
# Prerequisites:
#   - Docker installed and running
#
# Usage:
#   ./scripts/init-local-postgres.sh
#   ./scripts/init-local-postgres.sh --reset  (기존 데이터 삭제 후 재생성)
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Configuration (override with environment variables)
DB_CONTAINER_NAME="${DB_CONTAINER_NAME:-safety-postgres}"
DB_HOST="${CLOUD_DB_HOST:-localhost}"
DB_PORT="${CLOUD_DB_PORT:-5432}"
DB_NAME="${CLOUD_DB_NAME:-safety_platform}"
DB_USER="${CLOUD_DB_USER:-safety_admin}"
DB_PASSWORD="${CLOUD_DB_PASSWORD:-safety_password}"

SCHEMA_FILE="${PROJECT_ROOT}/infra/aws/rds/init-schema.sql"
SEED_FILE="${PROJECT_ROOT}/infra/aws/rds/seed-data.sql"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN} Local PostgreSQL Setup${NC}"
echo -e "${GREEN}========================================${NC}"

# Check if --reset flag is provided
if [ "$1" == "--reset" ]; then
    echo -e "${YELLOW}Resetting: Removing existing container...${NC}"
    docker rm -f "${DB_CONTAINER_NAME}" 2>/dev/null || true
    docker volume rm "safety_pg_data" 2>/dev/null || true
fi

# Check if container already exists
if docker ps -a --format '{{.Names}}' | grep -q "^${DB_CONTAINER_NAME}$"; then
    if docker ps --format '{{.Names}}' | grep -q "^${DB_CONTAINER_NAME}$"; then
        echo -e "${YELLOW}PostgreSQL container already running.${NC}"
    else
        echo "Starting existing container..."
        docker start "${DB_CONTAINER_NAME}"
    fi
else
    echo "Creating PostgreSQL container..."
    docker run -d \
        --name "${DB_CONTAINER_NAME}" \
        -e POSTGRES_DB="${DB_NAME}" \
        -e POSTGRES_USER="${DB_USER}" \
        -e POSTGRES_PASSWORD="${DB_PASSWORD}" \
        -p "${DB_PORT}:5432" \
        -v safety_pg_data:/var/lib/postgresql/data \
        postgres:16-alpine

    echo "Waiting for PostgreSQL to be ready..."
    sleep 3
    for i in $(seq 1 30); do
        if docker exec "${DB_CONTAINER_NAME}" pg_isready -U "${DB_USER}" -d "${DB_NAME}" > /dev/null 2>&1; then
            break
        fi
        echo "  Waiting... ($i/30)"
        sleep 1
    done
fi

# Verify connection
if ! docker exec "${DB_CONTAINER_NAME}" pg_isready -U "${DB_USER}" -d "${DB_NAME}" > /dev/null 2>&1; then
    echo -e "${RED}ERROR: PostgreSQL is not ready!${NC}"
    exit 1
fi

echo -e "${GREEN}PostgreSQL is ready.${NC}"

# Apply schema
echo ""
echo "Applying schema: ${SCHEMA_FILE}"
docker exec -i "${DB_CONTAINER_NAME}" \
    psql -U "${DB_USER}" -d "${DB_NAME}" < "${SCHEMA_FILE}"

echo -e "${GREEN}Schema applied successfully.${NC}"

# Apply seed data
echo ""
echo "Applying seed data: ${SEED_FILE}"
docker exec -i "${DB_CONTAINER_NAME}" \
    psql -U "${DB_USER}" -d "${DB_NAME}" < "${SEED_FILE}"

echo -e "${GREEN}Seed data applied successfully.${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN} Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Connection Info:"
echo "  Host: ${DB_HOST}"
echo "  Port: ${DB_PORT}"
echo "  Database: ${DB_NAME}"
echo "  User: ${DB_USER}"
echo "  Password: ${DB_PASSWORD}"
echo ""
echo "Connection String:"
echo "  postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}"
echo ""
echo "Environment Variables (add to .env):"
echo "  CLOUD_DB_HOST=${DB_HOST}"
echo "  CLOUD_DB_PORT=${DB_PORT}"
echo "  CLOUD_DB_NAME=${DB_NAME}"
echo "  CLOUD_DB_USER=${DB_USER}"
echo "  CLOUD_DB_PASSWORD=${DB_PASSWORD}"
