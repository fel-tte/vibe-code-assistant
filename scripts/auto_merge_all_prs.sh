#!/usr/bin/env bash
# auto_merge_all_prs.sh – Merge all 3 PR branches into the current branch locally
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*" >&2; exit 1; }

PR_BRANCHES=(
  "origin/copilot/upgrade-video-factory-standards"
  "origin/copilot/create-production-grade-e2e-test-suite"
  "origin/copilot/add-automated-test-suite-runner"
)

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
info "Current branch: ${CURRENT_BRANCH}"

# Fetch all PR branches
info "Fetching PR branches..."
git fetch origin \
  copilot/upgrade-video-factory-standards \
  copilot/create-production-grade-e2e-test-suite \
  copilot/add-automated-test-suite-runner

# Merge each branch
for branch in "${PR_BRANCHES[@]}"; do
  info "Merging ${branch}..."
  if git merge --no-edit "$branch"; then
    info "  ✅ Merged ${branch}"
  else
    error "  ❌ Merge conflict on ${branch}. Resolve conflicts and re-run."
  fi
done

info "🎉 All 3 PR branches merged successfully into '${CURRENT_BRANCH}'!"
echo ""
info "Next steps:"
echo "  1. Run tests:        make test-backend"
echo "  2. Start stack:      ./scripts/quick_start.sh"
echo "  3. Full test suite:  ./scripts/run_full_test_suite.sh"
