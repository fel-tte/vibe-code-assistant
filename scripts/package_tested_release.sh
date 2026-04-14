#!/bin/bash
set -e

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
PACKAGE_NAME="vibe-code-assistant-tested-${TIMESTAMP}"

echo "📦 Creating tested release package..."

# Create package directory
mkdir -p "dist/${PACKAGE_NAME}"

# Copy source code
rsync -av \
  --exclude '.git' \
  --exclude 'node_modules' \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  --exclude '.env*' \
  --exclude 'results' \
  --exclude 'artifacts' \
  . "dist/${PACKAGE_NAME}/"

# Copy latest test results
if [ -d "results/latest" ]; then
  cp -r results/latest "dist/${PACKAGE_NAME}/TEST_RESULTS"
else
  mkdir -p "dist/${PACKAGE_NAME}/TEST_RESULTS"
  echo "No test results found. Run 'make test-all' first." > "dist/${PACKAGE_NAME}/TEST_RESULTS/README.txt"
fi

# Create README
cat > "dist/${PACKAGE_NAME}/TEST_RESULTS_README.md" << 'EOF'
# Test Results

This package includes test results from the full test suite execution.

## Files

- `TEST_REPORT.md` - Comprehensive test execution report
- `SUMMARY.md` - Executive summary
- `*.log` - Individual test logs

## Running Tests

```bash
# Full test suite
make test-all

# Individual categories
make test-backend-only
make test-e2e-only
make test-load-only
make test-stress-only
```

## Results

See `SUMMARY.md` for pass/fail status and production readiness assessment.
EOF

# Create ZIP
cd dist
zip -r "${PACKAGE_NAME}.zip" "${PACKAGE_NAME}"

echo "✅ Package created: dist/${PACKAGE_NAME}.zip"
echo "📊 Size: $(du -h "${PACKAGE_NAME}.zip" | cut -f1)"
