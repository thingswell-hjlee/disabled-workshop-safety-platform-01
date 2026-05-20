#!/bin/bash
# ============================================================
# Run Dashboard Backend Tests
#
# Usage:
#   ./scripts/run-tests.sh                    # All tests
#   ./scripts/run-tests.sh test_event_validation  # Specific test
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="${PROJECT_ROOT}/apps/dashboard-backend"

echo "========================================"
echo " Running Dashboard Backend Tests"
echo "========================================"

# Set test environment
export AWS_MODE=mock
export CLOUD_DB_HOST=localhost
export CLOUD_DB_PORT=5432
export CLOUD_DB_NAME=safety_platform
export CLOUD_DB_USER=safety_admin
export CLOUD_DB_PASSWORD=safety_password
export SITE_ID=SITE-001

# Run tests
if [ -n "$1" ]; then
    echo "Running specific test: $1"
    python -m pytest "${BACKEND_DIR}/tests/$1.py" -v
else
    echo "Running all tests..."
    python -m pytest "${BACKEND_DIR}/tests/" -v --tb=short
fi

echo ""
echo "Tests completed."
