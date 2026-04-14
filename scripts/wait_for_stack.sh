#!/bin/bash
set -e

MAX_WAIT=300  # 5 minutes
INTERVAL=5

wait_for_service() {
  local url=$1
  local name=$2
  local elapsed=0

  echo -n "  Waiting for ${name}..."

  while [ $elapsed -lt $MAX_WAIT ]; do
    if curl -fsS "${url}" > /dev/null 2>&1; then
      echo " ✅"
      return 0
    fi

    sleep $INTERVAL
    elapsed=$((elapsed + INTERVAL))
    echo -n "."
  done

  echo " ❌ (timeout)"
  return 1
}

echo "🏥 Checking service health..."
echo ""

# Check Postgres
wait_for_service "http://localhost:8000/healthz/postgres" "Postgres"

# Check Redis
wait_for_service "http://localhost:8000/healthz/redis" "Redis"

# Check API
wait_for_service "http://localhost:8000/healthz" "API"

# Check Workers
wait_for_service "http://localhost:8000/healthz/workers" "Workers"

# Check Frontend
wait_for_service "http://localhost:3000" "Frontend"

# Check Edge Relay
wait_for_service "http://localhost:8080/healthz" "Edge Relay"

echo ""
echo "✅ All services healthy!"
