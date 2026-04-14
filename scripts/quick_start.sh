#!/usr/bin/env bash
# quick_start.sh – One-command setup: bootstrap env, start docker, verify health
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info()    { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*" >&2; exit 1; }

# ── 1. Bootstrap env files ──────────────────────────────────────────────────
info "Bootstrapping environment files..."
[[ -f backend/.env.dev ]] || cp backend/.env.example backend/.env.dev
[[ -f frontend/.env.local ]] || { [[ -f frontend/.env.local.example ]] && cp frontend/.env.local.example frontend/.env.local || true; }

# ── 2. Start Docker stack ────────────────────────────────────────────────────
info "Starting Docker Compose stack (this may take a few minutes on first run)..."
docker compose up -d --build

# ── 3. Wait for services ─────────────────────────────────────────────────────
info "Waiting for API to become healthy (up to 120 s)..."
TIMEOUT=120
ELAPSED=0
until curl -sf http://localhost:8000/healthz >/dev/null 2>&1; do
  sleep 3
  ELAPSED=$((ELAPSED + 3))
  if [[ $ELAPSED -ge $TIMEOUT ]]; then
    error "API did not become healthy within ${TIMEOUT}s. Check: docker compose logs api"
  fi
  echo -n "."
done
echo ""

# ── 4. Health check ───────────────────────────────────────────────────────────
STATUS=$(curl -sf http://localhost:8000/healthz | python3 -c "import sys,json; print(json.load(sys.stdin).get('status','unknown'))" 2>/dev/null || echo "error")
if [[ "$STATUS" == "ok" || "$STATUS" == "degraded" ]]; then
  info "API health: ${STATUS}"
else
  warn "API health status: ${STATUS} – stack may not be fully ready"
fi

# ── 5. Summary ────────────────────────────────────────────────────────────────
echo ""
info "🚀 Stack is running!"
echo "   Frontend  : http://localhost:3000"
echo "   API docs  : http://localhost:8000/docs"
echo "   Flower    : http://localhost:5555"
echo "   MinIO     : http://localhost:9001  (minioadmin / minioadmin)"
echo ""
info "To run tests:      make test-backend"
info "To stop the stack: docker compose down"
