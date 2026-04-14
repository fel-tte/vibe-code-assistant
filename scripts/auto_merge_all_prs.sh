#!/bin/bash
set -e

echo "🔄 Auto-merging all PRs..."
echo ""

# Ensure we're on main
git checkout main
git pull origin main

# Create integration branch
BRANCH_NAME="production-ready-v1.0-$(date +%Y%m%d_%H%M%S)"
git checkout -b "$BRANCH_NAME"

echo "📦 Merging PR #1: Production Hardening..."
git fetch origin copilot/upgrade-video-factory-standards
git merge origin/copilot/upgrade-video-factory-standards --no-edit -m "Merge PR #1: Production Hardening"

echo "📦 Merging PR #2: E2E Test Suite..."
git fetch origin copilot/create-production-grade-e2e-test-suite
git merge origin/copilot/create-production-grade-e2e-test-suite --no-edit -m "Merge PR #2: E2E Test Suite"

echo "📦 Merging PR #3: Automated Test Runner..."
git fetch origin copilot/add-automated-test-suite-runner
git merge origin/copilot/add-automated-test-suite-runner --no-edit -m "Merge PR #3: Automated Test Runner"

echo ""
echo "✅ All PRs merged into branch: $BRANCH_NAME"
echo ""
echo "Next steps:"
echo "1. Push branch: git push origin $BRANCH_NAME"
echo "2. Create PR: gh pr create --base main --head $BRANCH_NAME"
echo "3. Merge PR to trigger tests"
