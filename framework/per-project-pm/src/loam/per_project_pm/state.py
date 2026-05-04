# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""State-of-world + surfaced-question + recorded-response dataclasses.

Per cycle-2 plan §4 Surface #5 + cycle-4 plan §4 + §5:

  - :class:`StateOfWorld` — read snapshot returned by
    :meth:`~loam.per_project_pm.runtime.PMRuntime.state_of_world`.
    Frozen dataclass; persona reads named fields. Cycle 4 extends
    with the ``pending_response_for`` field so callers can detect
    blocking-on-pending-response without re-reading state.yaml.
  - :class:`SurfacedQuestion` — return value of
    :meth:`~loam.per_project_pm.runtime.PMRuntime.surface_next_question`
    (and one element of the tuple returned by
    :meth:`~loam.per_project_pm.runtime.PMRuntime.surface_next_questions_batch`).
    Frozen dataclass; carries text + provenance + position + audit
    path so the persona-side surfacing flow has full provenance for
    relay + logging.
  - :class:`RecordedResponse` — return value of
    :meth:`~loam.per_project_pm.runtime.PMRuntime.record_response`
    (Cycle 4). Carries the response + linkage back to the surfaced
    question's audit-log path so audit trails are bidirectionally
    traceable.

All three are stdlib ``@dataclass(frozen=True)`` (no Pydantic) — Cycles
2 + 4 return these from runtime APIs; they don't need Pydantic
validation since they're constructed in-process from already-validated
state. Pydantic models are reserved for the persisted contract + (future)
schema-validated state file shapes.

Cycle 4 adds the :prop:`SurfacedQuestion.is_audit_block_trigger` and
:prop:`RecordedResponse.is_audit_block_trigger` properties (per cycle-4
plan §5 Surface #5 + AC.QSURF.8). Both return ``True`` at Cycle 4 by
construction — every surfaced decision and every recorded response
satisfies the ``audit-block-on-telegram`` SKILL's "decision was made"
trigger condition. The property mechanism (vs an always-True field)
preserves a forward-compat extension point: future cycles may want to
gate on event metadata (e.g., a "low-stakes status update" event
shape that doesn't trigger the audit-block).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class StateOfWorld:
    """Read snapshot of PM state-of-world.

    Returned by
    :meth:`~loam.per_project_pm.runtime.PMRuntime.state_of_world` on a
    loaded PM, or by
    :meth:`~loam.per_project_pm.runtime.PMRuntime.empty_state_for` on an
    unauthored workspace (D1 cold-state).

    Empty-state semantics (``pm_loaded=False``): all other fields are
    ``None`` / ``0`` / empty tuple — the persona can branch on
    ``pm_loaded`` without inspecting the rest. This is the
    cycle-2 plan §4 Surface #5 + F2.D resolution.

    Loaded-state semantics (``pm_loaded=True``):

      - ``handle`` / ``project_name`` from contract.yaml.
      - ``queue_depth`` from decision-queue.yaml (count of pending).
      - ``pending_questions`` is a snapshot of pending question texts
        (immutable tuple — caller cannot mutate the queue via this).
      - ``last_surfaced_at`` from state.yaml; ``None`` if nothing has
        been surfaced yet.
      - ``workspace_state_dir`` is the resolved
        ``<workspace>/workspace/.loam/pms/<handle>/`` path.
      - ``pending_response_for`` (Cycle 4) — the question text awaiting
        a recorded response, or ``None`` if no surfacing is currently
        blocking under ``require_owner_response=True``. Reads cleanly
        as a "do I need to record a response before surfacing more?"
        signal.
    """

    pm_loaded: bool
    handle: str | None
    project_name: str | None
    queue_depth: int
    pending_questions: tuple[str, ...]
    last_surfaced_at: str | None
    workspace_state_dir: Path | None
    pending_response_for: str | None = None


@dataclass(frozen=True)
class SurfacedQuestion:
    """Return value of
    :meth:`~loam.per_project_pm.runtime.PMRuntime.surface_next_question`
    (and one element of the tuple returned by
    :meth:`~loam.per_project_pm.runtime.PMRuntime.surface_next_questions_batch`).

    Carries everything the persona-side surfacing flow needs:

      - ``text`` — the question text as enqueued (verbatim).
      - ``provenance`` — caller-supplied tag (e.g., source module,
        decision-context). May be ``None``.
      - ``queue_position`` — 1-based position the question occupied
        before being surfaced (always 1 for ``surface_next_question`` at
        Cycle 2's FIFO consumption; ``surface_next_questions_batch``
        returns positions 1, 2, 3... for the batch).
      - ``surfaced_at`` — ISO 8601 UTC timestamp of the surface call.
      - ``audit_path`` — absolute path to the audit-log entry just
        written; the persona-side flow logs this for traceability and
        passes it to
        :meth:`~loam.per_project_pm.runtime.PMRuntime.record_response`
        as the linkage key when recording the user's reply.
    """

    text: str
    provenance: str | None
    queue_position: int
    surfaced_at: str
    audit_path: Path

    @property
    def is_audit_block_trigger(self) -> bool:
        """Whether this PM event satisfies the
        ``audit-block-on-telegram`` SKILL's "decision was made"
        trigger condition.

        Per cycle-4 plan §5 Surface #5 + AC.QSURF.8: every
        :class:`SurfacedQuestion` event is a "decision was made"
        moment from the user's perspective (the persona is asking
        them to decide), so the SKILL's surface-when-meaningful
        rule fires. Cycle 4 returns ``True`` unconditionally; future
        cycles may gate on event metadata (e.g., a "low-stakes
        status update" event shape that doesn't trigger the
        audit-block — out of Cycle 4 scope).

        Composes with:
        ``plugins/loam-skills/skills/audit-block-on-telegram/SKILL.md``.
        """
        return True


@dataclass(frozen=True)
class RecordedResponse:
    """Return value of
    :meth:`~loam.per_project_pm.runtime.PMRuntime.record_response`
    (Cycle 4 surface).

    Carries the response + linkage back to the surfaced question, so
    the audit trail is bidirectionally traceable: the surfaced
    question's audit-log entry names what was asked; the response's
    audit-log entry names what was answered + which question it
    answered.

      - ``response_text`` — the owner's response, verbatim.
      - ``surfaced_audit_path`` — absolute path to the surfaced
        question's audit-log entry (the linkage key).
      - ``surfaced_question_text`` — the question text the response
        answers (read from the linked surfacing audit-log entry at
        record time, so a caller has the full pair without reading
        two files).
      - ``responded_at`` — ISO 8601 UTC timestamp of the
        ``record_response`` call.
      - ``audit_path`` — absolute path to the response's own
        audit-log entry (kind ``record_response``); the persona logs
        this for traceability alongside the surfacing path.
    """

    response_text: str
    surfaced_audit_path: Path
    surfaced_question_text: str
    responded_at: str
    audit_path: Path

    @property
    def is_audit_block_trigger(self) -> bool:
        """Whether this PM event satisfies the
        ``audit-block-on-telegram`` SKILL's "decision was made"
        trigger condition.

        Per cycle-4 plan §5 Surface #5 + AC.QSURF.8: a recorded
        response is a closed decision — the user gave a ruling, the
        PM persisted it. The persona surfacing the result of that
        decision to the user (or downstream agents) carries the
        "decision was made" semantic; the audit-block surfaces.
        Cycle 4 returns ``True`` unconditionally; future cycles may
        gate.

        Composes with:
        ``plugins/loam-skills/skills/audit-block-on-telegram/SKILL.md``.
        """
        return True
