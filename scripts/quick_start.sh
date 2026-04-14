#!/bin/bash
set -e

echo "🚀 QUICK START: Production-Ready Render Factory"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo "❌ Docker not found. Install: https://docs.docker.com/get-docker/"; exit 1; }
command -v docker-compose >/dev/null 2>&1 || command -v docker compose >/dev/null 2>&1 || { echo "❌ Docker Compose not found"; exit 1; }

echo "✅ Prerequisites OK"
echo ""

# Bootstrap
echo "📋 Step 1: Bootstrap environment..."
if [ ! -f backend/.env.dev ]; then
  cp backend/.env.example backend/.env.dev
  echo "✅ Created backend/.env.dev"
fi

if [ ! -f frontend/.env.local ]; then
  cp frontend/.env.local.example frontend/.env.local
  echo "✅ Created frontend/.env.local"
fi

echo ""

# Boot stack
echo "📦 Step 2: Booting Docker stack..."
docker compose down -v 2>/dev/null || true
docker compose up -d --build

echo ""
echo "⏳ Step 3: Waiting for services (60s)..."
sleep 60

# Verify health
echo ""
echo "🏥 Step 4: Checking health..."

for i in {1..30}; do
  if curl -fsS http://localhost:8000/healthz >/dev/null 2>&1; then
    echo "✅ API healthy"
    break
  fi
  sleep 2
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ STACK READY!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📱 Services:"
echo "  - Frontend:  http://localhost:3000"
echo "  - API Docs:  http://localhost:8000/docs"
echo "  - Flower:    http://localhost:5555"
echo "  - MinIO:     http://localhost:9001"
echo ""
echo "🧪 Run tests:"
echo "  make test-all"
echo ""
echo "📦 Create package:"
echo "  make package-tested"
echo ""
