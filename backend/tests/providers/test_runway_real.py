"""
Real provider integration tests.

These tests exercise the actual Runway / Kling / Veo APIs and therefore:
  - Require valid API credentials in environment variables.
  - Cost real money / consume real quota.
  - Are skipped automatically unless the relevant env var is set.

Run selectively with:
    pytest backend/tests/providers/ -v -m real_provider

Environment variables
---------------------
RUNWAYML_API_SECRET   – skip unless set
KLING_ACCESS_KEY      – skip unless set (also needs KLING_SECRET_KEY)
GEMINI_API_KEY        – skip unless set (Veo / Google)
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

import pytest

# Ensure backend package is importable from any working directory.
BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

pytestmark = pytest.mark.real_provider


# ---------------------------------------------------------------------------
# Runway
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    not os.getenv("RUNWAYML_API_SECRET"),
    reason="RUNWAYML_API_SECRET not set – skipping real Runway tests",
)
class TestRunwayRealAPI:
    """Submit a task to Runway and poll until completion (costs quota)."""

    def test_submit_and_poll_until_complete(self):
        """
        Submit a real text-to-video task to Runway Gen-4 and wait up to
        5 minutes for a completed result with a video URL.
        """
        from app.providers.runway.adapter import RunwayAdapter

        adapter = RunwayAdapter()

        scene_payload = {
            "scene_index": 1,
            "title": "Real Runway test",
            "provider": "runway",
            "resolved_prompt_text": "A serene mountain lake at sunrise with gentle ripples on the water surface.",
            "prompt_text": "A serene mountain lake at sunrise.",
            "resolved_duration_seconds": 5,
            "duration_seconds": 5,
            "aspect_ratio": "16:9",
        }

        # Submit
        result = asyncio.run(adapter.submit(scene_payload, callback_url=None))
        assert result is not None
        task_id = result.provider_task_id or result.provider_operation_name
        assert task_id, f"Expected a provider task ID, got: {result}"
        print(f"[runway-real] Task submitted: {task_id}")

        # Poll until terminal state (max 5 minutes)
        max_attempts = 60
        for attempt in range(max_attempts):
            status = asyncio.run(
                adapter.query(provider_task_id=task_id, provider_operation_name=None)
            )
            state = str(status.state or "").lower()
            print(f"[runway-real] Attempt {attempt + 1}/{max_attempts}: state={state}")

            if state == "succeeded":
                assert status.output_video_url, "Completed but no output URL"
                print(f"[runway-real] ✅ Video URL: {status.output_video_url}")
                return

            if state in ("failed", "error", "canceled"):
                pytest.fail(f"Task failed in state '{state}': {status.error_message}")

            asyncio.run(asyncio.sleep(5))

        pytest.fail(f"Task {task_id} did not complete within {max_attempts * 5} seconds")

    def test_mock_submit_when_no_secret(self, monkeypatch):
        """
        When RUNWAYML_API_SECRET is absent the adapter falls back to mock mode
        without raising an error (provider_allow_mock_fallback=True).
        """
        monkeypatch.delenv("RUNWAYML_API_SECRET", raising=False)

        # Re-import settings after env change to pick up the cleared value.
        import importlib
        import app.core.config as cfg_module
        importlib.reload(cfg_module)
        from app.core.config import settings as reloaded_settings
        reloaded_settings.runway_api_secret = None
        reloaded_settings.provider_allow_mock_fallback = True

        from app.providers.runway.adapter import RunwayAdapter
        adapter = RunwayAdapter()

        scene_payload = {
            "scene_index": 1,
            "title": "Mock fallback test",
            "provider": "runway",
            "resolved_prompt_text": "Test prompt for mock mode.",
            "resolved_duration_seconds": 5,
            "aspect_ratio": "16:9",
        }

        result = asyncio.run(adapter.submit(scene_payload, callback_url=None))
        assert result is not None
        assert result.provider_task_id or result.provider_operation_name


# ---------------------------------------------------------------------------
# Kling
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    not os.getenv("KLING_ACCESS_KEY"),
    reason="KLING_ACCESS_KEY not set – skipping real Kling tests",
)
class TestKlingRealAPI:
    """Submit a task to Kling and poll until completion (costs quota)."""

    def test_submit_and_poll_until_complete(self):
        """
        Submit a real text-to-video request to Kling and wait up to
        5 minutes for a completed result.
        """
        from app.providers.kling.adapter import KlingAdapter

        adapter = KlingAdapter()

        scene_payload = {
            "scene_index": 1,
            "title": "Real Kling test",
            "provider": "kling",
            "resolved_prompt_text": "A peaceful bamboo forest with sunlight filtering through the leaves.",
            "prompt_text": "Peaceful bamboo forest at dawn.",
            "resolved_duration_seconds": 5,
            "duration_seconds": 5,
            "aspect_ratio": "16:9",
        }

        result = asyncio.run(adapter.submit(scene_payload, callback_url=None))
        assert result is not None
        task_id = result.provider_task_id or result.provider_operation_name
        assert task_id, f"Expected a provider task ID, got: {result}"
        print(f"[kling-real] Task submitted: {task_id}")

        max_attempts = 60
        for attempt in range(max_attempts):
            status = asyncio.run(
                adapter.query(provider_task_id=task_id, provider_operation_name=None)
            )
            state = str(status.state or "").lower()
            print(f"[kling-real] Attempt {attempt + 1}/{max_attempts}: state={state}")

            if state == "succeeded":
                assert status.output_video_url, "Completed but no output URL"
                print(f"[kling-real] ✅ Video URL: {status.output_video_url}")
                return

            if state in ("failed", "error", "canceled"):
                pytest.fail(f"Task failed in state '{state}': {status.error_message}")

            asyncio.run(asyncio.sleep(5))

        pytest.fail(f"Task {task_id} did not complete within {max_attempts * 5} seconds")


# ---------------------------------------------------------------------------
# Veo
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    not os.getenv("GEMINI_API_KEY") and not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
    reason="Neither GEMINI_API_KEY nor GOOGLE_APPLICATION_CREDENTIALS set – skipping real Veo tests",
)
class TestVeoRealAPI:
    """Submit a task to Google Veo and poll until completion (costs quota)."""

    def test_submit_and_poll_until_complete(self):
        """
        Submit a real text-to-video request to Veo and wait up to
        8 minutes for a completed result.
        """
        from app.providers.veo.adapter import VeoAdapter

        adapter = VeoAdapter()

        scene_payload = {
            "scene_index": 1,
            "title": "Real Veo test",
            "provider": "veo",
            "resolved_prompt_text": "A time-lapse of clouds moving over a mountain peak at golden hour.",
            "prompt_text": "Time-lapse clouds mountain golden hour.",
            "resolved_duration_seconds": 4,
            "duration_seconds": 4,
            "aspect_ratio": "16:9",
        }

        result = asyncio.run(adapter.submit(scene_payload, callback_url=None))
        assert result is not None
        operation_name = result.provider_operation_name or result.provider_task_id
        assert operation_name, f"Expected an operation name, got: {result}"
        print(f"[veo-real] Operation submitted: {operation_name}")

        max_attempts = 96  # 8 minutes at 5-second intervals
        for attempt in range(max_attempts):
            status = asyncio.run(
                adapter.query(provider_task_id=None, provider_operation_name=operation_name)
            )
            state = str(status.state or "").lower()
            print(f"[veo-real] Attempt {attempt + 1}/{max_attempts}: state={state}")

            if state == "succeeded":
                assert status.output_video_url, "Completed but no output URL"
                print(f"[veo-real] ✅ Video URL: {status.output_video_url}")
                return

            if state in ("failed", "error", "canceled"):
                pytest.fail(f"Operation failed in state '{state}': {status.error_message}")

            asyncio.run(asyncio.sleep(5))

        pytest.fail(f"Operation {operation_name} did not complete within {max_attempts * 5} seconds")


# ---------------------------------------------------------------------------
# Provider factory smoke test (always runs)
# ---------------------------------------------------------------------------

class TestProviderFactory:
    """Basic provider factory tests – run without any credentials."""

    def test_runway_adapter_instantiates(self):
        from app.providers.runway.adapter import RunwayAdapter
        adapter = RunwayAdapter()
        assert adapter.provider_name == "runway"

    def test_kling_adapter_instantiates(self):
        from app.providers.kling.adapter import KlingAdapter
        adapter = KlingAdapter()
        assert adapter.provider_name == "kling"

    def test_veo_adapter_instantiates(self):
        from app.providers.veo.adapter import VeoAdapter
        adapter = VeoAdapter()
        assert adapter.provider_name == "veo"

    def test_mock_client_factory_returns_client(self):
        """get_provider_client returns a usable provider client."""
        from app.providers.factory import get_provider_client
        client = get_provider_client("runway")
        assert hasattr(client, "dispatch_scene")
        assert hasattr(client, "poll_scene")
