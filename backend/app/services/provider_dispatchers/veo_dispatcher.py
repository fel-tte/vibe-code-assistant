from __future__ import annotations

from app.providers.veo.adapter import VeoAdapter
from .base import DispatchResult

_adapter = VeoAdapter()


async def dispatch_veo_video(payload: dict) -> DispatchResult:
    """Dispatch a video generation request to the real Veo API via VeoAdapter.

    ``payload`` is a normalised scene dispatch dict as produced by
    ``render_dispatch_service.build_scene_dispatch_payload``.
    """
    result = await _adapter.submit(scene_payload=payload, callback_url=payload.get("callback_url"))
    return DispatchResult(
        accepted=result.accepted,
        provider_operation_name=result.provider_operation_name,
        raw_response=result.raw_response,
        error_message=result.error_message,
    )
