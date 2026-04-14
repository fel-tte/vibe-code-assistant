#!/usr/bin/env python3
"""
Generate comprehensive test execution report
"""

import os
import sys
import re
from datetime import datetime
from pathlib import Path


def parse_log_file(log_path: Path) -> dict:
    """Parse a test log file and extract status"""
    if not log_path.exists():
        return {"status": "SKIPPED", "details": "Log file not found"}

    content = log_path.read_text()

    # Check for status
    if "Status: PASSED" in content:
        status = "PASSED"
    elif "Status: FAILED" in content:
        status = "FAILED"
    else:
        status = "UNKNOWN"

    # Extract key metrics
    details = {}

    # For pytest logs
    if "passed" in content:
        match = re.search(r'(\d+) passed', content)
        if match:
            details['passed'] = int(match.group(1))

    if "failed" in content:
        match = re.search(r'(\d+) failed', content)
        if match:
            details['failed'] = int(match.group(1))

    # For load test logs
    if "Success rate:" in content:
        match = re.search(r'Success rate:\s+([\d.]+)%', content)
        if match:
            details['success_rate'] = float(match.group(1))

    if "p50:" in content:
        match = re.search(r'p50:\s+([\d.]+)', content)
        if match:
            details['p50_latency'] = float(match.group(1))

    return {"status": status, "details": details}


def generate_summary(result_dir: Path) -> str:
    """Generate summary markdown"""

    test_results = {}

    # Scan all log files
    for log_file in result_dir.glob("*.log"):
        test_name = log_file.stem
        test_results[test_name] = parse_log_file(log_file)

    # Count results
    total = len(test_results)
    passed = sum(1 for r in test_results.values() if r["status"] == "PASSED")
    failed = sum(1 for r in test_results.values() if r["status"] == "FAILED")
    skipped = sum(1 for r in test_results.values() if r["status"] == "SKIPPED")

    success_rate = (passed / total * 100) if total > 0 else 0

    # Generate summary
    summary = f"""
# TEST EXECUTION SUMMARY

**Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Overall Results

| Metric | Value |
|--------|-------|
| Total Tests | {total} |
| ✅ Passed | {passed} |
| ❌ Failed | {failed} |
| ⏭️ Skipped | {skipped} |
| Success Rate | {success_rate:.1f}% |

## Test Breakdown

"""

    # Phase 1: Backend Tests
    summary += "### Backend Tests\n\n"
    backend_tests = [
        "01_smoke_imports",
        "02_integration_tests",
        "03_provider_factory",
        "04_database_state",
        "05_migration_head"
    ]

    for test_name in backend_tests:
        if test_name in test_results:
            result = test_results[test_name]
            status_icon = "✅" if result["status"] == "PASSED" else "❌"
            summary += f"- {status_icon} **{test_name}**: {result['status']}\n"

            if result.get("details"):
                if "passed" in result["details"]:
                    summary += f"  - Passed: {result['details']['passed']}\n"
                if "failed" in result["details"]:
                    summary += f"  - Failed: {result['details']['failed']}\n"

    summary += "\n"

    # Phase 2: E2E Tests
    summary += "### E2E Tests\n\n"
    e2e_tests = ["06_playwright_e2e"]

    for test_name in e2e_tests:
        if test_name in test_results:
            result = test_results[test_name]
            status_icon = "✅" if result["status"] == "PASSED" else "❌"
            summary += f"- {status_icon} **{test_name}**: {result['status']}\n"

    summary += "\n"

    # Phase 3: Performance Tests
    summary += "### Performance Tests\n\n"
    perf_tests = ["07_load_test_100_jobs", "08_stress_test"]

    for test_name in perf_tests:
        if test_name in test_results:
            result = test_results[test_name]
            status_icon = "✅" if result["status"] == "PASSED" else "❌"
            summary += f"- {status_icon} **{test_name}**: {result['status']}\n"

            if result.get("details"):
                if "success_rate" in result["details"]:
                    summary += f"  - Success Rate: {result['details']['success_rate']:.1f}%\n"
                if "p50_latency" in result["details"]:
                    summary += f"  - p50 Latency: {result['details']['p50_latency']:.3f}s\n"

    summary += "\n"

    # Phase 4: Health Checks
    summary += "### Health Checks\n\n"
    health_tests = [
        "09_health_check",
        "10_detailed_health",
        "11_worker_health",
        "12_database_metrics"
    ]

    for test_name in health_tests:
        if test_name in test_results:
            result = test_results[test_name]
            status_icon = "✅" if result["status"] == "PASSED" else "❌"
            summary += f"- {status_icon} **{test_name}**: {result['status']}\n"

    summary += "\n"

    # Production Readiness
    summary += "## Production Readiness\n\n"

    if success_rate >= 95:
        summary += "🎉 **READY FOR PRODUCTION**\n\n"
        summary += "- All critical tests passed\n"
        summary += "- System is stable under load\n"
        summary += "- Health checks passing\n"
    elif success_rate >= 80:
        summary += "⚠️ **NEEDS ATTENTION**\n\n"
        summary += "- Some tests failed\n"
        summary += "- Review failed tests before production deployment\n"
    else:
        summary += "❌ **NOT READY**\n\n"
        summary += "- Multiple test failures detected\n"
        summary += "- System requires fixes before production\n"

    summary += f"\n---\n\n**Full logs:** `{result_dir}/`\n"

    return summary


def generate_detailed_report(result_dir: Path) -> str:
    """Generate detailed markdown report"""

    report = f"""
# COMPREHENSIVE TEST EXECUTION REPORT

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Result Directory:** `{result_dir}/`

---

## Executive Summary

"""

    # Add summary
    summary_path = result_dir / "SUMMARY.md"
    summary_md = summary_path.read_text() if summary_path.exists() else ""
    report += summary_md

    report += """

---

## Detailed Test Results

"""

    # Add each test log
    for log_file in sorted(result_dir.glob("*.log")):
        test_name = log_file.stem
        content = log_file.read_text()

        report += f"""
### {test_name}

<details>
<summary>View Log</summary>

```
{content}
```

</details>

"""

    # Add resource usage
    stats_file = result_dir / "docker_stats.txt"
    if stats_file.exists():
        report += """

---

## Resource Usage

```
"""
        report += stats_file.read_text()
        report += """
```

"""

    return report


def main():
    if len(sys.argv) < 2:
        print("Usage: generate_test_report.py <result_dir>")
        sys.exit(1)

    result_dir = Path(sys.argv[1])

    if not result_dir.exists():
        print(f"Error: {result_dir} does not exist")
        sys.exit(1)

    print("📝 Generating test reports...")

    # Generate summary
    summary = generate_summary(result_dir)
    (result_dir / "SUMMARY.md").write_text(summary)
    print(f"✅ Summary: {result_dir / 'SUMMARY.md'}")

    # Generate detailed report
    detailed = generate_detailed_report(result_dir)
    (result_dir / "TEST_REPORT.md").write_text(detailed)
    print(f"✅ Detailed report: {result_dir / 'TEST_REPORT.md'}")

    print("📊 Test reports generated successfully")


if __name__ == "__main__":
    main()
