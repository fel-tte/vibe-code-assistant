#!/bin/bash
set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create results directory
mkdir -p results/logs
mkdir -p artifacts/test-results

# Timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULT_DIR="results/${TIMESTAMP}"
mkdir -p "$RESULT_DIR"

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🧪 FULL TEST SUITE EXECUTION${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Timestamp: ${TIMESTAMP}"
echo "Results dir: ${RESULT_DIR}"
echo ""

# Track overall status
OVERALL_STATUS=0

# Function to run test and capture result
run_test() {
  local test_name=$1
  local test_command=$2
  local log_file="${RESULT_DIR}/${test_name}.log"

  echo -e "${YELLOW}▶ Running: ${test_name}${NC}"
  echo "Command: ${test_command}" > "${log_file}"
  echo "Started: $(date)" >> "${log_file}"
  echo "" >> "${log_file}"

  if eval "${test_command}" >> "${log_file}" 2>&1; then
    echo -e "${GREEN}✅ PASSED: ${test_name}${NC}"
    echo "Status: PASSED" >> "${log_file}"
    echo "Finished: $(date)" >> "${log_file}"
    return 0
  else
    echo -e "${RED}❌ FAILED: ${test_name}${NC}"
    echo "Status: FAILED" >> "${log_file}"
    echo "Finished: $(date)" >> "${log_file}"
    OVERALL_STATUS=1
    return 1
  fi
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PHASE 1: Stack Bootstrap
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}PHASE 1: Stack Bootstrap${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Clean previous containers
echo -e "${YELLOW}🧹 Cleaning previous containers...${NC}"
docker compose down -v 2>/dev/null || true

# Boot stack
echo -e "${YELLOW}📦 Booting stack...${NC}"
docker compose up -d --build

# Wait for services
echo -e "${YELLOW}⏳ Waiting for services to be healthy...${NC}"
./scripts/wait_for_stack.sh || {
  echo -e "${RED}❌ Stack failed to boot${NC}"
  docker compose logs --tail=50
  exit 1
}

echo -e "${GREEN}✅ Stack ready${NC}"
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PHASE 2: Backend Tests
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}PHASE 2: Backend Tests${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Smoke tests
run_test "01_smoke_imports" \
  "docker compose exec -T api python -m compileall app"

# Integration tests
run_test "02_integration_tests" \
  "docker compose exec -T api pytest tests/integration/ -v -m integration --tb=short"

# Provider factory tests
run_test "03_provider_factory" \
  "docker compose exec -T api pytest tests/providers/test_provider_factory.py -v"

# Database state verification
run_test "04_database_state" \
  "docker compose exec -T api python scripts/verify_database_state.py"

# Migration head check
run_test "05_migration_head" \
  "docker compose exec -T api python scripts/check_single_alembic_head.py"

echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PHASE 3: E2E Tests
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}PHASE 3: E2E Tests${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

run_test "06_playwright_e2e" \
  "docker compose run --rm --profile e2e playwright"

echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PHASE 4: Performance Tests
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}PHASE 4: Performance Tests${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Load test
run_test "07_load_test_100_jobs" \
  "python backend/tests/load/test_load.py --jobs 100 --concurrent 10 --min-success-rate 0.95"

# Stress test
run_test "08_stress_test" \
  "bash scripts/stress_test.sh"

echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PHASE 5: Health & Observability
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}PHASE 5: Health & Observability${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# System health check
run_test "09_health_check" \
  "curl -fsS http://localhost:8000/healthz"

# Detailed health
run_test "10_detailed_health" \
  "curl -fsS http://localhost:8000/healthz/detailed"

# Worker health
run_test "11_worker_health" \
  "curl -fsS http://localhost:8000/healthz/workers"

# Database metrics
run_test "12_database_metrics" \
  "docker compose exec -T api python scripts/collect_db_metrics.py"

# Resource usage
echo -e "${YELLOW}▶ Collecting resource usage...${NC}"
docker stats --no-stream > "${RESULT_DIR}/docker_stats.txt"
echo -e "${GREEN}✅ Resource usage captured${NC}"

echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PHASE 6: Generate Report
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}PHASE 6: Generate Report${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo -e "${YELLOW}📝 Generating comprehensive report...${NC}"
python scripts/generate_test_report.py "${RESULT_DIR}"

# Copy to latest
cp -r "${RESULT_DIR}" results/latest

echo -e "${GREEN}✅ Report generated: ${RESULT_DIR}/TEST_REPORT.md${NC}"
echo ""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Summary
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📊 TEST EXECUTION SUMMARY${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

cat "${RESULT_DIR}/SUMMARY.md"

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📁 Full Report: ${RESULT_DIR}/TEST_REPORT.md${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if [ $OVERALL_STATUS -eq 0 ]; then
  echo -e "${GREEN}🎉 ALL TESTS PASSED - PRODUCTION READY${NC}"
  exit 0
else
  echo -e "${RED}❌ SOME TESTS FAILED - REVIEW REQUIRED${NC}"
  exit 1
fi
