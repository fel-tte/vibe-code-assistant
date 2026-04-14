# TEST EXECUTION REPORT

## Production-Grade E2E Test Suite

### Overview

This document describes the comprehensive end-to-end testing suite added to the
render pipeline monorepo. All tests are designed to simulate real-world execution
from stack boot through video output verification.

---

## 📁 Test File Index

| File | Type | Description |
|---|---|---|
| `e2e/tests/test_full_render_pipeline.spec.ts` | Playwright E2E | Full pipeline: health → create → submit → callback → complete |
| `e2e/tests/render-job-edge-relay.spec.ts` | Playwright E2E | Edge relay, incident drawer, bulk actions |
| `e2e/fixtures/sample_script.txt` | Fixture | 5-scene sample script for upload tests |
| `backend/tests/integration/test_render_pipeline_integration.py` | Integration | Database-layer tests with real SQLite/Postgres |
| `backend/tests/load/test_load.py` | Load | Concurrent job creation throughput test |
| `backend/tests/providers/test_runway_real.py` | Provider | Real API tests (skipped without credentials) |
| `scripts/stress_test.sh` | Stress | Incremental concurrency stress test |
| `.github/workflows/e2e-real.yml` | CI | Nightly full-stack E2E + optional load test |

---

## 🧪 Test Descriptions

### 1. E2E Playwright Suite (`e2e/tests/test_full_render_pipeline.spec.ts`)

**Tests included:**

| Test | What it verifies |
|---|---|
| `backend healthcheck` | API `/healthz` endpoint is reachable and returns success |
| `full pipeline` | Create job → provider submission → callback → `completed` status + output URL |
| `database state` | All required fields present in completed job via status API |
| `error scenario` | Provider failure callback → job enters `failed`/`error` state, incident created |
| `multi-scene pipeline` | 2-scene job: all scenes dispatched, callbacks delivered, job merges |
| `load: 5 concurrent` | 5 parallel jobs, ≥4 succeed, system stays healthy |
| `frontend page` | Completed job page renders final video and URL via `data-testid` selectors |
| `storage signed URL` | `/api/v1/storage/jobs/{id}/final-download` returns key or signed URL |

**Environment variables:**

| Variable | Default | Purpose |
|---|---|---|
| `BACKEND_BASE_URL` | `http://localhost:8000` | Backend API base URL |
| `FRONTEND_BASE_URL` | `http://localhost:3000` | Frontend base URL |
| `EDGE_BASE_URL` | `http://localhost:8080` | Edge relay base URL |
| `E2E_PROVIDER` | `runway` | Provider to use (`runway`, `kling`, `veo`) |
| `E2E_DELIVERY_MODE` | `edge-callback` | How provider callbacks are delivered |

---

### 2. Backend Integration Tests (`backend/tests/integration/`)

**Run without Docker** — uses an in-memory SQLite database.

**Test classes:**

| Class | Tests |
|---|---|
| `TestRenderJobCreation` | Single scene, multi-scene, JSON payload validation, not-found query, queue filter |
| `TestRenderJobStateTransitions` | Status persistence, scene completion counters, full job completion |
| `TestConcurrentJobs` | 5 jobs without collision, multi-provider storage |
| `TestErrorRecovery` | Error state + message persistence, scene failure codes |
| `TestDatabaseSchema` | Required columns on `RenderJob` and `RenderSceneTask` models |

**How to run:**

```bash
cd backend
DATABASE_URL="sqlite:///:memory:" pytest tests/integration/ -v -m integration
```

**Against real Postgres:**

```bash
DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/render_factory" \
  pytest tests/integration/ -v -m integration
```

---

### 3. Load Test (`backend/tests/load/test_load.py`)

Sends concurrent `POST /api/v1/render/jobs` requests and measures:
- Success rate
- Average / min / max / p50 / p95 / p99 response times

**Quick smoke (via pytest):**

```bash
# Requires backend running at http://localhost:8000
pytest backend/tests/load/test_load.py::TestLoadRunner::test_load_smoke_5_jobs -v
```

**Full load test:**

```bash
# 100 jobs, 10 concurrent – expects ≥ 95 % success rate
python backend/tests/load/test_load.py --jobs 100 --concurrent 10

# Custom target
python backend/tests/load/test_load.py \
  --base-url http://localhost:8000 \
  --jobs 50 \
  --concurrent 5 \
  --provider runway \
  --min-success-rate 0.90
```

---

### 4. Stress Test (`scripts/stress_test.sh`)

Incrementally increases concurrency (1 → 5 → 10 → 20 → 50 → 100 → 150 → 200)
to find the system's breaking point.

```bash
bash scripts/stress_test.sh
# or
bash scripts/stress_test.sh --base-url http://localhost:8000 --max-concurrent 100
```

**Environment variables:**

| Variable | Default | Purpose |
|---|---|---|
| `BACKEND_BASE_URL` | `http://localhost:8000` | Backend API URL |
| `MAX_CONCURRENT` | `200` | Maximum concurrency level |
| `JOBS_PER_LEVEL` | `100` | Jobs per concurrency level |
| `MIN_SUCCESS_RATE` | `0.80` | Minimum acceptable success rate |

---

### 5. Real Provider Tests (`backend/tests/providers/test_runway_real.py`)

**Automatically skipped** unless the relevant API key is set in the environment.

| Class | Skip condition |
|---|---|
| `TestRunwayRealAPI` | `RUNWAYML_API_SECRET` not set |
| `TestKlingRealAPI` | `KLING_ACCESS_KEY` not set |
| `TestVeoRealAPI` | `GEMINI_API_KEY` and `GOOGLE_APPLICATION_CREDENTIALS` both unset |
| `TestProviderFactory` | Never skipped – tests mock client and adapter instantiation |

**Run (requires API key):**

```bash
RUNWAYML_API_SECRET=xxx pytest backend/tests/providers/ -v -m real_provider
```

---

## 📊 Success Criteria

| Test Type | Target | Metric |
|---|---|---|
| Backend integration | 100 % pass | All DB / service tests |
| E2E Playwright | 100 % pass | Full pipeline end-to-end |
| Load test (10 jobs, 5 concurrent) | ≥ 95 % success | Response time < 30 s avg |
| Load test (100 jobs, 10 concurrent) | ≥ 95 % success | p95 < 10 s |
| Stress test | ≥ 50 concurrent | No hard crash, graceful degradation |
| Provider factory tests | 100 % pass | Adapter instantiation |

---

## 🚀 Execution Order (Full Stack)

```bash
# 1. Boot the full stack
docker compose up -d --build

# 2. Wait for health
python scripts/ci/wait_for_stack.py 300

# 3. Backend integration tests (no Docker needed)
cd backend
DATABASE_URL="sqlite:///:memory:" pytest tests/integration/ -v -m integration

# 4. Provider factory smoke
pytest tests/providers/test_runway_real.py::TestProviderFactory -v

# 5. Full pipeline E2E (Playwright)
cd e2e
npm install && npx playwright install --with-deps chromium
npx playwright test tests/test_full_render_pipeline.spec.ts

# 6. Edge relay E2E (existing)
npx playwright test tests/render-job-edge-relay.spec.ts

# 7. Load test (optional)
cd ..
python backend/tests/load/test_load.py --jobs 100 --concurrent 10

# 8. Stress test (optional)
bash scripts/stress_test.sh

# 9. Tear down
docker compose down -v
```

---

## 🔄 CI Integration

The new workflow `.github/workflows/e2e-real.yml` provides:

- **`backend-integration`** job: runs integration tests + provider factory tests on
  every trigger without Docker.
- **`full-pipeline-e2e`** job: boots the full stack and runs
  `test_full_render_pipeline.spec.ts` with the selected provider and delivery mode.
- **`load-test`** job: optional (manual trigger only), runs a 10-job load test
  against the booted stack.

The workflow is triggered:
- Manually via `workflow_dispatch` with configurable provider, delivery mode, and
  optional load test.
- Nightly at 02:00 UTC on the default branch.

---

## 📋 Checklist

- [x] E2E test suite (`e2e/tests/test_full_render_pipeline.spec.ts`)
- [x] Integration tests (`backend/tests/integration/`)
- [x] Load test script (`backend/tests/load/test_load.py`)
- [x] Stress test script (`scripts/stress_test.sh`)
- [x] Real provider tests (`backend/tests/providers/test_runway_real.py`)
- [x] Test fixture (`e2e/fixtures/sample_script.txt`)
- [x] CI pipeline (`.github/workflows/e2e-real.yml`)
- [x] Test execution report (`TEST_EXECUTION_REPORT.md`)
