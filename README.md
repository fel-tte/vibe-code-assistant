# Render Factory Monorepo

![CI](https://github.com/fel-tte/vibe-code-assistant/actions/workflows/ci.yml/badge.svg)
![Production Ready Test](https://github.com/fel-tte/vibe-code-assistant/actions/workflows/production-ready-test.yml/badge.svg)
![E2E Real World](https://github.com/fel-tte/vibe-code-assistant/actions/workflows/e2e-real.yml/badge.svg)

Production-grade render video factory monorepo – FastAPI backend, Next.js frontend, Celery workers, multi-provider video generation (Runway / Kling / Veo).

## Quick Start

```bash
# One-command setup (bootstraps env + starts Docker + verifies health)
./scripts/quick_start.sh
```

Or step-by-step:

```bash
cp backend/.env.example backend/.env.dev
cp frontend/.env.local.example frontend/.env.local
docker compose up -d --build
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| API docs | http://localhost:8000/docs |
| Flower (Celery) | http://localhost:5555 |
| MinIO console | http://localhost:9001 |

## Architecture

```
┌─────────────┐    ┌──────────────┐    ┌───────────────┐
│  Next.js UI │───▶│  FastAPI API │───▶│ Celery Worker │
│  (port 3000)│    │  (port 8000) │    │               │
└─────────────┘    └──────┬───────┘    └───────┬───────┘
                          │                     │
              ┌───────────▼──────┐   ┌──────────▼────────┐
              │   PostgreSQL DB  │   │  Provider Adapters │
              │   + Redis cache  │   │  Runway/Kling/Veo  │
              └──────────────────┘   └──────────┬─────────┘
                                                 │
                                      ┌──────────▼─────────┐
                                      │  MinIO Object Store │
                                      │  (final video URLs) │
                                      └────────────────────┘
```

## Main Pipeline

1. Upload `.txt` / `.docx` script
2. Build preview payload
3. Edit / validate preview
4. Create project from confirmed preview
5. Prepare provider-specific plan / payloads
6. Create render job
7. Dispatch scene tasks to provider adapters
8. Provider callback and/or polling updates scene state
9. Upload assets to object storage
10. Merge clips + burn subtitles
11. Expose final status and final video URL

## Testing

| Test Type | Command | Description |
|-----------|---------|-------------|
| Unit tests | `make test-backend` | Fast unit tests (SQLite) |
| Integration tests | `make test-integration` | Pipeline integration tests |
| Full suite | `./scripts/run_full_test_suite.sh` | Unit + integration + smoke |
| Load test | `python scripts/load/test_load.py` | 100 concurrent jobs |
| Stress test | `./scripts/stress_test.sh` | Find breaking point |
| E2E (local) | `make e2e-local` | Playwright end-to-end |

## CI/CD Workflows

| Workflow | Trigger | Description |
|----------|---------|-------------|
| `ci.yml` | Push / PR | Compile check + unit tests |
| `production-ready-test.yml` | Push to main / PR | Full test suite + release artifact |
| `e2e-real.yml` | Manual / Nightly | Real-world E2E with Docker stack |
| `alembic-check.yml` | Push / PR | Migration lineage validation |

## Scope

- FastAPI backend API
- Frontend UI (Next.js)
- Celery workers
- Redis / Postgres
- Alembic migrations
- Provider abstraction layer
- Veo / Runway / Kling adapters
- Webhook callback ingestion
- Poll fallback
- Object storage / MinIO / signed URL
- Render job status API
- Healthcheck endpoints
- Docker Compose local dev stack
- Production-grade E2E test suite
- Load & stress testing scripts

## Provenance

Primary base: `render_factory_repo.zip`.
Supplemental merges:
- `template_engine_bundle(2).zip` for frontend scaffold and script upload patterns.
- `full_render_pipeline_and_bandit_bundle.zip` for realtime progress widget.
- snippets from uploaded text/library for the locked render execution chain and preview-first editing flow.

Parts explicitly marked mock or TODO are integration points where the source material only contained scaffolding or intentionally mocked provider calls.
