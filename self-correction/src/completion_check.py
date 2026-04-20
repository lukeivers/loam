"""Terminal-transition pre-check for four-part structural enforcement.

Subscribes to the correction scope's own emitter and intercepts
`StateTransitioned(to_state=completed)` BEFORE the transition commits.
If the four record types are not all present in
`correction_episode_records`, raises `-32070 CORRECTION_INCOMPLETE_RECORDS`.

CRITICAL: pyee's `on("*")` fires AFTER the transition has already been
persisted. That pattern is too late — the state is already `completed`.
We instead gate the transition at the IPC-call level: the controller
exposes `request_complete(scope_id)` which runs the check first, then
calls `runtime.complete(scope_id)` only on pass. The pyee subscription
here is a belt-and-braces audit layer: if a completion happens without
going through `request_complete` (e.g. somebody calls the runtime
directly), we emit a refused span so the violation is visible even
though we cannot retroactively roll back the state change.

The hard enforcement path is `request_complete` — the pyee audit is
the structural integrity check. No LLM in either path.
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from pos_orchestrator.ipc import ApplicationError

from . import observability as obs
from .spec import (
    IPC_CORRECTION_INCOMPLETE_RECORDS,
    REQUIRED_RECORD_TYPES,
    RecordType,
)
from .store import CorrectionStore


class CompletionPrecheck:
    """Pre-check that enforces the four-part protocol at completion.

    The check is deterministic: look up the episode by the correction
    scope id, query the record-type set, compare against
    REQUIRED_RECORD_TYPES.
    """

    def __init__(self, *, store: CorrectionStore) -> None:
        self._store = store

    def run_or_raise(self, *, correction_scope_id: str) -> None:
        ep = self._store.get_episode_by_scope(correction_scope_id)
        if ep is None:
            # Not a correction scope — no enforcement. Completion
            # check only applies to registered correction episodes.
            return

        present = self._store.record_types_for(ep.episode_id)
        missing = REQUIRED_RECORD_TYPES - present
        if missing:
            # Deterministic refusal — no LLM.
            missing_list = sorted(m.value for m in missing)
            obs.episode_refused(
                episode_id=ep.episode_id,
                reason="incomplete_records",
                code=IPC_CORRECTION_INCOMPLETE_RECORDS,
                details={"missing_record_types": ",".join(missing_list)},
            )
            raise ApplicationError(
                IPC_CORRECTION_INCOMPLETE_RECORDS,
                (
                    f"correction episode {ep.episode_id!r} cannot "
                    f"complete: missing record types "
                    f"{missing_list!r}. All four of "
                    f"{sorted(t.value for t in REQUIRED_RECORD_TYPES)!r} "
                    f"are required (four-part protocol)."
                ),
                data={
                    "episode_id": ep.episode_id,
                    "correction_scope_id": correction_scope_id,
                    "missing": missing_list,
                    "present": sorted(p.value for p in present),
                },
            )

    def audit_subscription(
        self, scope_runtime: Any, *, notify: Callable[[str, str], Awaitable[None]] | None = None
    ) -> None:
        """Belt-and-braces audit — subscribe to the runtime's `*`
        emitter and log any `StateTransitioned(completed)` on a
        correction scope that does not pass the check.

        The audit only fires when a caller bypassed `request_complete`.
        We cannot stop the transition (pyee is post-hoc) — we emit a
        refused span and, if `notify` is provided, dispatch a one-on-one
        channel escalation.
        """
        def _on_event(event: Any) -> None:
            from scope_of_work import ScopeState

            if getattr(event, "to_state", None) != ScopeState.completed:
                return
            scope_id = getattr(event, "scope_id", None)
            if not scope_id:
                return
            ep = self._store.get_episode_by_scope(scope_id)
            if ep is None:
                return
            present = self._store.record_types_for(ep.episode_id)
            missing = REQUIRED_RECORD_TYPES - present
            if missing:
                missing_list = sorted(m.value for m in missing)
                obs.episode_refused(
                    episode_id=ep.episode_id,
                    reason="audit:incomplete_records_bypass",
                    code=IPC_CORRECTION_INCOMPLETE_RECORDS,
                    details={"missing_record_types": ",".join(missing_list)},
                )
                if notify is not None:
                    import asyncio
                    try:
                        loop = asyncio.get_running_loop()
                        loop.create_task(
                            notify(ep.episode_id, ",".join(missing_list))
                        )
                    except RuntimeError:
                        pass

        scope_runtime.emitter.on("*", _on_event)
