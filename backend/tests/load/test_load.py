"""
Load testing script for the render pipeline API.

Sends concurrent POST /api/v1/render/jobs requests and measures throughput,
latency, and success rates.  The API must be running before executing this
script.

Usage
-----
# Quick 10-job smoke run (default):
    python backend/tests/load/test_load.py

# 100 jobs, 10 at a time:
    python backend/tests/load/test_load.py --jobs 100 --concurrent 10

# Point at a non-default host:
    python backend/tests/load/test_load.py --base-url http://localhost:8000 --jobs 50

Dependencies (install with pip):
    httpx

pytest integration
------------------
When collected by pytest the module exports ``TestLoadRunner`` so that a
minimal smoke run executes as part of the test suite (max 5 jobs).
"""
from __future__ import annotations

import argparse
import asyncio
import statistics
import sys
import time
from dataclasses import dataclass, field
from typing import Any

import httpx

DEFAULT_BASE_URL = "http://localhost:8000"
DEFAULT_JOBS = 10
DEFAULT_CONCURRENCY = 5
DEFAULT_TIMEOUT = 60.0


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class JobResult:
    index: int
    status: str          # "success" | "error" | "exception"
    elapsed_seconds: float
    http_code: int | None = None
    job_id: str | None = None
    error: str | None = None


@dataclass
class LoadTestReport:
    total: int
    success: int
    error: int
    exception: int
    avg_seconds: float
    min_seconds: float
    max_seconds: float
    p50_seconds: float
    p95_seconds: float
    p99_seconds: float
    results: list[JobResult] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        return self.success / self.total if self.total > 0 else 0.0

    def print_summary(self) -> None:  # pragma: no cover
        print()
        print("=" * 60)
        print("📊  LOAD TEST RESULTS")
        print("=" * 60)
        print(f"Total jobs:          {self.total}")
        print(f"Successful:          {self.success}  ({self.success_rate * 100:.1f} %)")
        print(f"HTTP errors:         {self.error}  ({self.error / self.total * 100:.1f} %)")
        print(f"Exceptions:          {self.exception}  ({self.exception / self.total * 100:.1f} %)")
        print(f"Avg response time:   {self.avg_seconds:.3f} s")
        print(f"Min response time:   {self.min_seconds:.3f} s")
        print(f"Max response time:   {self.max_seconds:.3f} s")
        print(f"p50 response time:   {self.p50_seconds:.3f} s")
        print(f"p95 response time:   {self.p95_seconds:.3f} s")
        print(f"p99 response time:   {self.p99_seconds:.3f} s")
        print("=" * 60)


# ---------------------------------------------------------------------------
# Core async helpers
# ---------------------------------------------------------------------------

def _build_job_payload(idx: int, provider: str = "runway") -> dict[str, Any]:
    return {
        "project_id": f"load-test-{idx}-{int(time.time())}",
        "provider": provider,
        "aspect_ratio": "16:9",
        "subtitle_mode": "soft",
        "planned_scenes": [
            {
                "scene_index": 1,
                "title": f"Load test scene {idx}",
                "script_text": f"A cinematic load test shot, job {idx}.",
                "provider_target_duration_sec": 5,
                "target_duration_sec": 5,
                "visual_prompt": f"Load test visual prompt {idx}",
            }
        ],
    }


async def _create_one_job(
    client: httpx.AsyncClient,
    base_url: str,
    idx: int,
    provider: str = "runway",
) -> JobResult:
    payload = _build_job_payload(idx, provider)
    start = time.perf_counter()
    try:
        resp = await client.post(
            f"{base_url}/api/v1/render/jobs",
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        elapsed = time.perf_counter() - start

        if resp.status_code in (200, 201):
            try:
                data = resp.json()
                inner = data.get("data") or data
                job_id = inner.get("id") or inner.get("job_id")
            except Exception:
                job_id = None
            return JobResult(
                index=idx,
                status="success",
                elapsed_seconds=elapsed,
                http_code=resp.status_code,
                job_id=job_id,
            )
        else:
            return JobResult(
                index=idx,
                status="error",
                elapsed_seconds=elapsed,
                http_code=resp.status_code,
                error=resp.text[:200],
            )
    except Exception as exc:
        elapsed = time.perf_counter() - start
        return JobResult(
            index=idx,
            status="exception",
            elapsed_seconds=elapsed,
            error=str(exc)[:200],
        )


def _percentile(sorted_values: list[float], pct: float) -> float:
    if not sorted_values:
        return 0.0
    idx = int(len(sorted_values) * pct / 100)
    idx = min(idx, len(sorted_values) - 1)
    return sorted_values[idx]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def run_load_test(
    base_url: str = DEFAULT_BASE_URL,
    num_jobs: int = DEFAULT_JOBS,
    concurrency: int = DEFAULT_CONCURRENCY,
    provider: str = "runway",
    timeout_seconds: float = DEFAULT_TIMEOUT,
    verbose: bool = True,
) -> LoadTestReport:
    """
    Run a load test against the render jobs endpoint.

    Parameters
    ----------
    base_url:         Backend base URL (no trailing slash).
    num_jobs:         Total number of jobs to create.
    concurrency:      Maximum parallel requests in each batch.
    provider:         Video provider name ("runway", "kling", "veo").
    timeout_seconds:  Per-request HTTP timeout.
    verbose:          Print progress to stdout when True.

    Returns
    -------
    LoadTestReport with aggregated metrics.
    """
    if verbose:
        print(f"🚀  Load test starting: {num_jobs} jobs, {concurrency} concurrent, provider={provider}")

    results: list[JobResult] = []
    semaphore = asyncio.Semaphore(concurrency)

    async def bounded(idx: int) -> JobResult:
        async with semaphore:
            return await _create_one_job(client, base_url, idx, provider)

    async with httpx.AsyncClient(timeout=timeout_seconds) as client:
        tasks = [bounded(i) for i in range(num_jobs)]
        batch_results = await asyncio.gather(*tasks, return_exceptions=False)
        results.extend(batch_results)

        # Post-run health check
        if verbose:
            try:
                health_resp = await client.get(f"{base_url}/healthz")
                print(f"💚  System health after load: {health_resp.status_code}")
            except Exception as exc:
                print(f"⚠️   Health check failed: {exc}")

    success = sum(1 for r in results if r.status == "success")
    error = sum(1 for r in results if r.status == "error")
    exception = sum(1 for r in results if r.status == "exception")
    times = sorted(r.elapsed_seconds for r in results)

    report = LoadTestReport(
        total=len(results),
        success=success,
        error=error,
        exception=exception,
        avg_seconds=statistics.mean(times) if times else 0.0,
        min_seconds=min(times) if times else 0.0,
        max_seconds=max(times) if times else 0.0,
        p50_seconds=_percentile(times, 50),
        p95_seconds=_percentile(times, 95),
        p99_seconds=_percentile(times, 99),
        results=results,
    )

    if verbose:
        report.print_summary()

    return report


# ---------------------------------------------------------------------------
# pytest integration (lightweight smoke run)
# ---------------------------------------------------------------------------

class TestLoadRunner:
    """
    Minimal pytest wrapper.  Skipped automatically unless the backend is
    reachable at DEFAULT_BASE_URL (or BACKEND_BASE_URL env var).
    """

    @staticmethod
    def _backend_url() -> str:
        import os
        return os.getenv("BACKEND_BASE_URL", DEFAULT_BASE_URL).rstrip("/")

    @staticmethod
    def _is_backend_available(url: str) -> bool:
        try:
            import urllib.request
            urllib.request.urlopen(f"{url}/healthz", timeout=3)
            return True
        except Exception:
            return False

    def test_load_smoke_5_jobs(self):
        """Smoke load: 5 jobs with 2 concurrent – expects 80 %+ success rate."""
        import pytest as _pytest

        url = self._backend_url()
        if not self._is_backend_available(url):
            _pytest.skip(f"Backend not reachable at {url} – skipping load smoke test")

        report = asyncio.run(
            run_load_test(
                base_url=url,
                num_jobs=5,
                concurrency=2,
                verbose=False,
            )
        )

        assert report.total == 5, f"Expected 5 results, got {report.total}"
        assert report.success_rate >= 0.8, (
            f"Success rate {report.success_rate:.1%} below 80 % threshold. "
            f"Errors: {report.error}, Exceptions: {report.exception}"
        )
        assert report.avg_seconds < 30.0, (
            f"Average response time {report.avg_seconds:.2f}s exceeds 30 s limit"
        )


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render pipeline load test")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL, help="Backend base URL")
    parser.add_argument("--jobs", type=int, default=DEFAULT_JOBS, help="Total jobs to create")
    parser.add_argument("--concurrent", type=int, default=DEFAULT_CONCURRENCY, help="Max concurrent requests")
    parser.add_argument("--provider", default="runway", choices=["runway", "kling", "veo"], help="Provider name")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="Per-request timeout (s)")
    parser.add_argument("--min-success-rate", type=float, default=0.95, help="Minimum acceptable success rate (0-1)")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:  # pragma: no cover
    args = _parse_args(argv)
    report = asyncio.run(
        run_load_test(
            base_url=args.base_url.rstrip("/"),
            num_jobs=args.jobs,
            concurrency=args.concurrent,
            provider=args.provider,
            timeout_seconds=args.timeout,
            verbose=True,
        )
    )

    if report.success_rate < args.min_success_rate:
        print(
            f"\n❌  FAILED: success rate {report.success_rate:.1%} "
            f"is below required {args.min_success_rate:.1%}",
            file=sys.stderr,
        )
        return 1

    print(f"\n✅  PASSED: success rate {report.success_rate:.1%}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
