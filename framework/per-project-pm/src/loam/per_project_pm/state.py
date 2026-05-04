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

"""State-of-world + surfaced-question dataclasses.

Per cycle-2 plan §4 Surface #5:

  - :class:`StateOfWorld` — read snapshot returned by
    :meth:`~loam.per_project_pm.runtime.PMRuntime.state_of_world`.
    Frozen dataclass; persona reads named fields.
  - :class:`SurfacedQuestion` — return value of
    :meth:`~loam.per_project_pm.runtime.PMRuntime.surface_next_question`.
    Frozen dataclass; carries text + provenance + position + audit
    path so the persona-side surfacing flow has full provenance for
    relay + logging.

Both are stdlib ``@dataclass(frozen=True)`` (no Pydantic) — Cycle 2
returns these from runtime APIs; they don't need Pydantic validation
since they're constructed in-process from already-validated state.
Pydantic models are reserved for the persisted contract + (future)
schema-validated state file shapes.
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
    """

    pm_loaded: bool
    handle: str | None
    project_name: str | None
    queue_depth: int
    pending_questions: tuple[str, ...]
    last_surfaced_at: str | None
    workspace_state_dir: Path | None


@dataclass(frozen=True)
class SurfacedQuestion:
    """Return value of
    :meth:`~loam.per_project_pm.runtime.PMRuntime.surface_next_question`.

    Carries everything the persona-side surfacing flow needs:

      - ``text`` — the question text as enqueued (verbatim).
      - ``provenance`` — caller-supplied tag (e.g., source module,
        decision-context). May be ``None``.
      - ``queue_position`` — 1-based position the question occupied
        before being surfaced (always 1 at Cycle 2's FIFO consumption,
        but the field is recorded for forward-compat with Cycle 4's
        batched/blocking surfacing).
      - ``surfaced_at`` — ISO 8601 UTC timestamp of the surface call.
      - ``audit_path`` — absolute path to the audit-log entry just
        written; the persona-side flow logs this for traceability.
    """

    text: str
    provenance: str | None
    queue_position: int
    surfaced_at: str
    audit_path: Path
