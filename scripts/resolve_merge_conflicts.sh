#!/bin/bash
set -e

echo "🔍 Checking for merge conflicts..."

# Check if there are unmerged files
if git diff --name-only --diff-filter=U | grep -q .; then
  echo "⚠️ Merge conflicts detected:"
  git diff --name-only --diff-filter=U
  echo ""
  echo "Auto-resolving common conflicts..."

  # Auto-resolve: prefer PR #3 (test runner) for Makefile
  if git diff --name-only --diff-filter=U | grep -q "Makefile"; then
    echo "  - Makefile: keeping version from PR #3"
    git checkout --theirs Makefile
    git add Makefile
  fi

  # Auto-resolve: merge docker-compose.yml (typically no conflicts)
  if git diff --name-only --diff-filter=U | grep -q "docker-compose.yml"; then
    echo "  - docker-compose.yml: manual merge required"
  fi

  # Check if all resolved
  if git diff --name-only --diff-filter=U | grep -q .; then
    echo ""
    echo "❌ Some conflicts still need manual resolution:"
    git diff --name-only --diff-filter=U
    exit 1
  else
    echo "✅ All conflicts resolved automatically"
    git commit --no-edit
  fi
else
  echo "✅ No merge conflicts"
fi
