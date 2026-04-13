#!/usr/bin/env bash
# ===========================================================================
# stress_test.sh – Find the breaking point of the render pipeline
#
# Usage:
#   bash scripts/stress_test.sh [--base-url URL] [--max-concurrent N]
#
# Environment variables:
#   BACKEND_BASE_URL   – defaults to http://localhost:8000
#   MAX_CONCURRENT     – maximum concurrent jobs to test (default: 200)
#   JOBS_PER_LEVEL     – jobs per concurrency level (default: 100)
# ===========================================================================
set -euo pipefail

BACKEND_BASE_URL="${BACKEND_BASE_URL:-http://localhost:8000}"
MAX_CONCURRENT="${MAX_CONCURRENT:-200}"
JOBS_PER_LEVEL="${JOBS_PER_LEVEL:-100}"
MIN_SUCCESS_RATE="${MIN_SUCCESS_RATE:-0.80}"

# Parse optional flags
while [[ $# -gt 0 ]]; do
  case "$1" in
    --base-url)     BACKEND_BASE_URL="$2"; shift 2 ;;
    --max-concurrent) MAX_CONCURRENT="$2"; shift 2 ;;
    --jobs)         JOBS_PER_LEVEL="$2"; shift 2 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
LOAD_TEST="${REPO_ROOT}/backend/tests/load/test_load.py"

echo "🔥  STRESS TEST – Find Breaking Point"
echo "======================================"
echo "  Backend:         ${BACKEND_BASE_URL}"
echo "  Max concurrent:  ${MAX_CONCURRENT}"
echo "  Jobs per level:  ${JOBS_PER_LEVEL}"
echo "  Min success rate: ${MIN_SUCCESS_RATE}"
echo ""

# ---------------------------------------------------------------------------
# Pre-flight: check stack health
# ---------------------------------------------------------------------------
echo "🏥  Checking stack health..."
if ! curl -sf "${BACKEND_BASE_URL}/healthz" > /dev/null 2>&1; then
  echo "❌  Backend not reachable at ${BACKEND_BASE_URL}/healthz"
  echo "    Start the stack first: docker compose up -d"
  exit 1
fi
echo "✅  Stack is healthy"
echo ""

# ---------------------------------------------------------------------------
# Helper function
# ---------------------------------------------------------------------------
_run_level() {
  local concurrent=$1
  local log_file="/tmp/stress_test_level_${concurrent}.log"

  echo "──────────────────────────────────────"
  echo "🚀  Testing with ${concurrent} concurrent jobs..."

  python3 "${LOAD_TEST}" \
    --base-url "${BACKEND_BASE_URL}" \
    --jobs "${JOBS_PER_LEVEL}" \
    --concurrent "${concurrent}" \
    --min-success-rate "${MIN_SUCCESS_RATE}" \
    2>&1 | tee "${log_file}" | tail -20

  local exit_code=${PIPESTATUS[0]}

  # Check system health after each level
  if ! curl -sf "${BACKEND_BASE_URL}/healthz" > /dev/null 2>&1; then
    echo ""
    echo "💀  SYSTEM CRASHED at ${concurrent} concurrent jobs"
    echo "    Last healthy level was ${LAST_HEALTHY:-unknown}"
    exit 2
  fi

  return ${exit_code}
}

# ---------------------------------------------------------------------------
# Increasing load levels
# ---------------------------------------------------------------------------
LAST_HEALTHY=0
BROKE_AT=""

for CONCURRENT in 1 5 10 20 50 100 150 200; do
  # Stop if we've already exceeded MAX_CONCURRENT
  if [[ ${CONCURRENT} -gt ${MAX_CONCURRENT} ]]; then
    break
  fi

  if _run_level "${CONCURRENT}"; then
    LAST_HEALTHY="${CONCURRENT}"
    echo "✅  PASSED at ${CONCURRENT} concurrent"
    # Brief cooldown between levels
    sleep 5
  else
    BROKE_AT="${CONCURRENT}"
    echo ""
    echo "⚠️   DEGRADED at ${CONCURRENT} concurrent (below ${MIN_SUCCESS_RATE} success rate)"
    echo "    Continuing to next level to find hard crash point..."
    sleep 5
  fi
done

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo ""
echo "======================================"
echo "📊  STRESS TEST SUMMARY"
echo "======================================"
echo "  Last fully healthy level: ${LAST_HEALTHY} concurrent"
if [[ -n "${BROKE_AT}" ]]; then
  echo "  First degraded level:     ${BROKE_AT} concurrent"
else
  echo "  System survived up to:    ${MAX_CONCURRENT} concurrent (no degradation detected)"
fi
echo ""

# Final health check
if curl -sf "${BACKEND_BASE_URL}/healthz" > /dev/null 2>&1; then
  echo "💚  System is still healthy after stress test"
else
  echo "💀  System is unhealthy after stress test"
  exit 2
fi

echo ""
echo "✅  Stress test complete"
