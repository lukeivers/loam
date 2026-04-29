"""IPC wiring for self-correction.

Three named methods:

  - correction.record_part(episode_id, part_type, payload)
        Persists one of the four typed records. Pydantic validation at
        the IPC boundary — malformed payloads rejected with -32602.

  - correction.report_review_verdict(scope_id, verdict, reasons, reporter)
        Ruling #1 — any reviewer invokes on verdict=="fail". Verdicts
        other than "fail" are accepted and recorded as no-ops (no
        trigger fires).

  - correction.user_reported(description, related_scope_id?, reporter)
        Ruling #4 — caller identity enforced at the boundary. Rejects
        non-primary-persona callers with -32602.

This module does NOT install an activate_scope wrap — self-correction
is a consumer of the three-gate chain (brief hard constraint: no new
activation wrap).
"""

from __future__ import annotations

from typing import Any

from loam.orchestrator.ipc import ApplicationError, IPCServer
from pydantic import ValidationError

from .controller import SelfCorrectionController
from .spec import RECORD_MODELS, RecordType
from .triggers import (
    build_trigger_from_review_verdict,
    build_trigger_from_user_report,
)


def register_self_correction_ipc(
    *,
    server: IPCServer,
    controller: SelfCorrectionController,
) -> None:
    """Register self-correction IPC methods. No activate_scope wrap."""

    # ---- correction.record_part ------------------------------------

    async def record_part(params: dict[str, Any]) -> dict[str, Any]:
        episode_id = params.get("episode_id")
        part_type_raw = params.get("part_type")
        payload = params.get("payload")
        if not isinstance(episode_id, str):
            raise ApplicationError(-32602, "episode_id (string) required")
        if not isinstance(part_type_raw, str):
            raise ApplicationError(-32602, "part_type (string) required")
        if not isinstance(payload, dict):
            raise ApplicationError(-32602, "payload (object) required")
        try:
            record_type = RecordType(part_type_raw)
        except ValueError as exc:
            raise ApplicationError(
                -32602,
                f"part_type must be one of "
                f"{sorted(t.value for t in RecordType)!r}",
            ) from exc
        model = RECORD_MODELS[record_type]
        # Pydantic validation at the boundary (CR9).
        try:
            validated = model(episode_id=episode_id, **payload)
        except ValidationError as exc:
            raise ApplicationError(
                -32602,
                f"invalid payload for {record_type.value}: {exc.errors()}",
                data={"errors": exc.errors()},
            ) from exc
        controller.record_part(
            episode_id=episode_id,
            record_type=record_type,
            payload=validated.model_dump(mode="json"),
        )
        return {"ok": True, "episode_id": episode_id, "part_type": record_type.value}

    # ---- correction.report_review_verdict --------------------------

    async def report_review_verdict(params: dict[str, Any]) -> dict[str, Any]:
        scope_id = params.get("scope_id")
        verdict = params.get("verdict")
        reasons = params.get("reasons") or []
        reporter = params.get("reporter") or "unknown"
        if not isinstance(scope_id, str):
            raise ApplicationError(-32602, "scope_id (string) required")
        if not isinstance(verdict, str):
            raise ApplicationError(-32602, "verdict (string) required")
        if not isinstance(reasons, list) or not all(
            isinstance(r, str) for r in reasons
        ):
            raise ApplicationError(
                -32602, "reasons must be a list[str]"
            )
        if not isinstance(reporter, str):
            raise ApplicationError(-32602, "reporter (string) required")
        trigger = build_trigger_from_review_verdict(
            scope_id=scope_id,
            verdict=verdict,
            reasons=reasons,
            reporter=reporter,
        )
        if trigger is None:
            # verdict != "fail" — recorded but no trigger fires.
            return {"ok": True, "trigger_fired": False, "verdict": verdict}
        result = await controller.intake(trigger)
        return {
            "ok": True,
            "trigger_fired": True,
            "trigger_id": trigger.trigger_id,
            "episode_id": result.episode_id if result else None,
            "deduplicated": result is None,
        }

    # ---- correction.user_reported ----------------------------------

    async def user_reported(params: dict[str, Any]) -> dict[str, Any]:
        description = params.get("description")
        related_scope_id = params.get("related_scope_id")
        reporter = params.get("reporter")
        if not isinstance(description, str) or not description:
            raise ApplicationError(
                -32602, "description (non-empty string) required"
            )
        if related_scope_id is not None and not isinstance(
            related_scope_id, str
        ):
            raise ApplicationError(
                -32602, "related_scope_id must be string or null"
            )
        if not isinstance(reporter, str) or not reporter:
            raise ApplicationError(
                -32602, "reporter (non-empty string) required"
            )
        # Ruling #4: primary-persona-only caller identity check.
        controller.authorize_user_report_caller(reporter)
        trigger = build_trigger_from_user_report(
            description=description,
            related_scope_id=related_scope_id,
            reporter=reporter,
        )
        result = await controller.intake(trigger)
        return {
            "ok": True,
            "trigger_id": trigger.trigger_id,
            "episode_id": result.episode_id if result else None,
            "deduplicated": result is None,
        }

    server.register("correction.record_part", record_part)
    server.register("correction.report_review_verdict", report_review_verdict)
    server.register("correction.user_reported", user_reported)
