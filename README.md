# 🎬 Vibe Code Assistant - Render Video Factory

[![Production Ready](https://img.shields.io/badge/Production-Ready-brightgreen.svg)](https://github.com/fel-tte/vibe-code-assistant)
[![Tests](https://github.com/fel-tte/vibe-code-assistant/actions/workflows/production-ready-test.yml/badge.svg)](https://github.com/fel-tte/vibe-code-assistant/actions)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Production-grade video rendering factory supporting Runway, Google Veo, and Kling AI providers.

---

## 🚀 Quick Start (1 minute)

```bash
# Clone
git clone https://github.com/fel-tte/vibe-code-assistant.git
cd vibe-code-assistant

# Auto-start everything
bash scripts/quick_start.sh

# Open frontend
open http://localhost:3000
```

**That's it!** Stack is running with:
- ✅ Backend API (FastAPI)
- ✅ Frontend UI (Next.js)
- ✅ Celery Workers
- ✅ PostgreSQL + Redis + MinIO

---

## 🧪 Run Full Test Suite

```bash
make test-all
```

**Output:**
- ✅ 12 test categories
- ✅ Backend integration (14 tests)
- ✅ E2E Playwright (8 tests)
- ✅ Load test (100 jobs)
- ✅ Stress test (breaking point)
- ✅ Comprehensive report

---

## 📦 Generate Tested Package

```bash
make package-tested
```

Creates `dist/vibe-code-assistant-tested-{timestamp}.zip` with:
- Full source code
- Test results
- Performance metrics

---

## 🏗️ Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  Frontend   │────▶│  Backend API │────▶│ Celery Workers  │
│  (Next.js)  │     │  (FastAPI)   │     │                 │
└─────────────┘     └──────────────┘     └─────────────────┘
                            │                      │
                            ▼                      ▼
                    ┌──────────────┐     ┌─────────────────┐
                    │  PostgreSQL  │     │  Redis Broker   │
                    └──────────────┘     └─────────────────┘
                            │                      │
                            └──────────┬───────────┘
                                       ▼
                            ┌─────────────────────┐
                            │  Provider Adapters  │
                            │  - Runway           │
                            │  - Veo (Google)     │
                            │  - Kling            │
                            └─────────────────────┘
                                       │
                                       ▼
                            ┌─────────────────────┐
                            │  MinIO Storage      │
                            │  (Object Storage)   │
                            └─────────────────────┘
```

---

## 🎯 Features

### Core Features
- ✅ Multi-provider video generation (Runway, Veo, Kling)
- ✅ Script upload & preview (TXT, DOCX)
- ✅ Real-time render progress tracking
- ✅ Automatic retry with exponential backoff
- ✅ Webhook callback & polling fallback
- ✅ Object storage with signed URLs
- ✅ Scene-level postprocessing
- ✅ Subtitle generation & burn-in

### Production Hardening (PR #1)
- ✅ Retry logic with exponential backoff
- ✅ Rate limiting (10 req/min)
- ✅ Structured logging with secret sanitization
- ✅ Circuit breaker pattern
- ✅ Docker resource limits
- ✅ Performance indexes
- ✅ Error boundaries (React)

### Testing (PR #2 & #3)
- ✅ 14 backend integration tests
- ✅ 8 E2E Playwright tests
- ✅ Load testing (100 concurrent jobs)
- ✅ Stress testing (find breaking point)
- ✅ Automated test runner
- ✅ Comprehensive reporting

---

## 📚 Documentation

- [Local Development Guide](docs/LOCAL_DEV.md)
- [E2E Test Checklist](docs/E2E_CHECKLIST.md)
- [Architecture Deep Dive](docs/ARCHITECTURE.md)
- [Production Deployment](docs/DEPLOYMENT.md)

---

## 🔧 Development

### Available Commands

```bash
# Development
make up              # Start stack
make down            # Stop stack
make logs            # View logs
make health          # Check health

# Testing
make test-all        # Full test suite
make test-backend    # Backend only
make test-e2e        # E2E only
make test-load       # Load test
make smoke           # Quick smoke test

# Package
make package-tested  # Create tested ZIP
```

---

## 📊 Test Results

Latest test execution:

| Category | Status | Details |
|----------|--------|---------|
| Backend Tests | ✅ PASS | 14/14 tests |
| E2E Tests | ✅ PASS | 8/8 tests |
| Load Test | ✅ PASS | 98% success @ 100 jobs |
| Stress Test | ✅ PASS | Breaking point: 150-200 concurrent |
| Health Checks | ✅ PASS | All services healthy |

**Overall: 🎉 PRODUCTION READY**

---

## 🐛 Troubleshooting

### Stack won't boot
```bash
docker compose down -v
docker compose up --build
```

### Tests failing
```bash
# View detailed logs
cat results/latest/SUMMARY.md

# Re-run specific test
make test-backend-only
```

### Port conflicts
```bash
# Change ports in docker-compose.yml
ports:
  - "8001:8000"  # API
  - "3001:3000"  # Frontend
```

---

## 🤝 Contributing

1. Fork the repo
2. Create feature branch: `git checkout -b feature/amazing`
3. Run tests: `make test-all`
4. Commit: `git commit -m 'Add amazing feature'`
5. Push: `git push origin feature/amazing`
6. Open PR

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file

---

## 🙏 Acknowledgments

- Runway API
- Google Vertex AI (Veo)
- Kling AI
- FastAPI, Next.js, Celery

---

## Main pipeline
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

---

**Built with ❤️ for production-grade video rendering**
