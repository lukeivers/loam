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

"""Per-project PM runtime — `PMRuntime`.

Per cycle-2 plan §4 Surface #5 + AC.PPM.{4,5,6}. The runtime is the
public API surface for working with a loaded PM:

  - :meth:`PMRuntime.from_workspace` — load a PM by name from the
    workspace (raises :class:`PMNotFoundError` if no contract.yaml).
  - :meth:`PMRuntime.empty_state_for` — return an empty
    :class:`StateOfWorld` for an unauthored workspace (D1 cold-state).
  - :meth:`PMRuntime.state_of_world` — read snapshot of PM state.
  - :meth:`PMRuntime.enqueue_decision` — append to FIFO queue
    atomically; return 1-based position.
  - :meth:`PMRuntime.surface_next_question` — consume head of FIFO
    queue; write audit-log entry; return :class:`SurfacedQuestion`
    (or ``None`` on empty queue).

Cycle 4 will extend with ``record_response``,
``surface_next_questions_batch``, and the ``require_owner_response``
blocking enforcement (see ``surfacing.py`` in Cycle 4).
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from loam.per_project_pm.contract import PMContract
from loam.per_project_pm.errors import (
    PMNotFoundError,
    PMStateCorruptedError,
)
from loam.per_project_pm.loader import (
    ACCEPTED_SCHEMA_VERSION,
    atomic_write_yaml,
    load_contract,
    load_decision_queue,
    load_state_yaml,
    workspace_state_dir_for,
)
from loam.per_project_pm.state import StateOfWorld, SurfacedQuestion


_AUDIT_FILE_PATTERN = re.compile(r"^(\d{4}-\d{2}-\d{2})-(\d{4})\.yaml$")


def _utc_now_iso() -> str:
    """ISO 8601 UTC timestamp with timezone suffix.

    Format: ``2026-05-04T10:35:00.123456+00:00``. Used for
    ``enqueued_at`` / ``surfaced_at`` / audit-log ``timestamp``.
    """
    return datetime.now(tz=timezone.utc).isoformat()


def _utc_today() -> str:
    """UTC date (``YYYY-MM-DD``) for audit-log filename scope."""
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")


def _next_audit_seq(audit_dir: Path, today: str) -> int:
    """Compute the next 1-based monotonic counter for audit-log entries
    on ``today`` in ``audit_dir``.

    Per AC.PPM.5 + cycle-2 plan §2 F2.E: ``<NNNN>`` is 4-digit zero-
    padded monotonic counter scoped to (pm-name, UTC date), reset to
    ``0001`` at midnight UTC. Computed at write time by reading the
    directory listing and incrementing the max suffix found
    (stdlib only; no SQLite).

    Returns 1 if no entries exist for ``today`` (or the dir doesn't
    exist yet).
    """
    if not audit_dir.is_dir():
        return 1
    max_seq = 0
    for entry in audit_dir.iterdir():
        if not entry.is_file():
            continue
        match = _AUDIT_FILE_PATTERN.match(entry.name)
        if not match:
            continue
        if match.group(1) != today:
            continue
        seq = int(match.group(2))
        if seq > max_seq:
            max_seq = seq
    return max_seq + 1


class PMRuntime:
    """Workspace-state-anchored PM runtime.

    Construct via :meth:`from_workspace` (loads from disk) or
    :meth:`empty_state_for` (returns the empty-state classmethod
    helper, not a runtime — for callers that just want the
    cold-state :class:`StateOfWorld`).

    Mutations (``enqueue_decision``, ``surface_next_question``) write
    state to disk synchronously via tmp+rename so two processes (or a
    process + a session restart) see consistent state without an
    in-memory cache. Per cycle-2 plan-doc §5 — correctness over
    perf at Cycle 2's scale.
    """

    def __init__(
        self,
        *,
        contract: PMContract,
        pm_dir: Path,
    ) -> None:
        self._contract = contract
        self._pm_dir = pm_dir

    # ---- factory + empty-state ------------------------------------

    @classmethod
    def from_workspace(
        cls,
        workspace_root: Path | str,
        pm_name: str,
    ) -> "PMRuntime":
        """Load PM at ``<workspace>/workspace/.loam/pms/<pm_name>/``.

        Raises :class:`PMNotFoundError` if ``contract.yaml`` is absent.
        Raises :class:`PMStateCorruptedError` on schema mismatch.

        Per AC.PPM.4.
        """
        pm_dir = workspace_state_dir_for(workspace_root, pm_name)
        contract = load_contract(pm_dir)
        # Validate state.yaml + decision-queue.yaml at load time so
        # PMStateCorruptedError surfaces eagerly — but tolerate file
        # absence (lazy creation on first write).
        load_state_yaml(pm_dir)
        load_decision_queue(pm_dir)
        return cls(contract=contract, pm_dir=pm_dir)

    @classmethod
    def empty_state_for(cls, workspace_root: Path | str) -> StateOfWorld:
        """Return the empty :class:`StateOfWorld` for an unauthored
        workspace.

        Per cycle-2 plan-doc §2 F2.D: ``PMNotFoundError`` is the loader
        boundary's fail-loud signal; this helper is the callsite's
        normal-empty-project shape. Used at D1 cold-state smoke +
        the persona-side flow when "no PM authored yet" is the
        expected branch.

        Note: doesn't require any PM-name input — empty state is
        global to the workspace (no PM = no state). Workspace_root is
        accepted for symmetry with :meth:`from_workspace` and for
        future extensions that might want to record the path on the
        empty state.
        """
        # Workspace_root is accepted but not currently used; the empty
        # state-of-world has nothing to anchor to a path. Routing
        # through workspace_state_dir_for() would require a pm_name,
        # which we don't have for an unauthored project.
        _ = workspace_root  # suppress unused warning; documented intent
        return StateOfWorld(
            pm_loaded=False,
            handle=None,
            project_name=None,
            queue_depth=0,
            pending_questions=(),
            last_surfaced_at=None,
            workspace_state_dir=None,
        )

    # ---- properties ------------------------------------------------

    @property
    def contract(self) -> PMContract:
        """The loaded :class:`PMContract`."""
        return self._contract

    @property
    def workspace_state_dir(self) -> Path:
        """``<workspace>/workspace/.loam/pms/<handle>/``."""
        return self._pm_dir

    # ---- read API -------------------------------------------------

    def state_of_world(self) -> StateOfWorld:
        """Read snapshot of PM state-of-world.

        Re-reads state.yaml + decision-queue.yaml every call (no
        in-memory cache; correctness over perf at Cycle 2). Returns a
        :class:`StateOfWorld` with ``pm_loaded=True``.
        """
        state = load_state_yaml(self._pm_dir)
        queue = load_decision_queue(self._pm_dir)
        pending_texts = tuple(entry["text"] for entry in queue)
        return StateOfWorld(
            pm_loaded=True,
            handle=self._contract.handle,
            project_name=self._contract.project_name,
            queue_depth=len(queue),
            pending_questions=pending_texts,
            last_surfaced_at=state.get("last_surfaced_at"),
            workspace_state_dir=self._pm_dir,
        )

    # ---- write API ------------------------------------------------

    def enqueue_decision(
        self,
        question_text: str,
        *,
        provenance: str | None = None,
    ) -> int:
        """Append a decision to the FIFO queue.

        Per AC.PPM.6:

          - Appends to ``decision-queue.yaml``.
          - Returns 1-based enqueued position (the position the new
            entry holds in the queue immediately after append).
          - Persists synchronously via tmp+rename (no in-memory drift).
          - Records ``enqueued_at`` ISO 8601 timestamp.

        Raises ``ValueError`` if ``question_text`` is empty.
        """
        if not question_text:
            raise ValueError("question_text must be non-empty")

        queue = load_decision_queue(self._pm_dir)
        entry = {
            "text": question_text,
            "provenance": provenance,
            "enqueued_at": _utc_now_iso(),
        }
        queue.append(entry)

        atomic_write_yaml(
            self._pm_dir / "decision-queue.yaml",
            {
                "schema_version": ACCEPTED_SCHEMA_VERSION,
                "queue": queue,
            },
        )
        return len(queue)

    def surface_next_question(self) -> SurfacedQuestion | None:
        """Consume head of FIFO queue; return :class:`SurfacedQuestion`
        or ``None`` on empty queue.

        Per AC.PPM.5:

          - Returns ``None`` (not exception) when queue is empty —
            empty is normal.
          - Pops the head, writes a new ``decision-queue.yaml``,
            writes the audit-log entry at
            ``audit-log/<YYYY-MM-DD>-<NNNN>.yaml``, updates
            ``state.yaml`` with new ``last_surfaced_at``.
          - All three writes are atomic (tmp+rename); the order is:
              1. write audit-log entry (so the surfacing is durable
                 even if the dequeue write fails — the audit-log is
                 the source of truth for what was surfaced).
              2. write decision-queue.yaml without the consumed head.
              3. update state.yaml's last_surfaced_at.
            A crash between (1) and (2) leaves the queue with an
            already-surfaced head; the next call detects this via
            audit-log scan (Cycle 4 hardens; Cycle 2 the simple
            re-surface is acceptable since the audit-log makes the
            duplication observable).
        """
        queue = load_decision_queue(self._pm_dir)
        if not queue:
            return None

        head = queue[0]
        position_pre = 1  # FIFO consumption — head is always position 1
        queue_depth_pre = len(queue)
        queue_depth_post = queue_depth_pre - 1
        surfaced_at_iso = _utc_now_iso()
        today_utc = _utc_today()

        # 1. Write the audit-log entry first (durable record).
        audit_dir = self._pm_dir / "audit-log"
        audit_dir.mkdir(parents=True, exist_ok=True)
        seq = _next_audit_seq(audit_dir, today_utc)
        audit_filename = f"{today_utc}-{seq:04d}.yaml"
        audit_path = audit_dir / audit_filename
        audit_payload = {
            "schema_version": ACCEPTED_SCHEMA_VERSION,
            "event_kind": "surface_question",
            "timestamp": surfaced_at_iso,
            "pm_handle": self._contract.handle,
            "question_text": head["text"],
            "question_provenance": head.get("provenance"),
            "queue_position_pre": position_pre,
            "queue_depth_pre": queue_depth_pre,
            "queue_depth_post": queue_depth_post,
        }
        atomic_write_yaml(audit_path, audit_payload)

        # 2. Write decision-queue.yaml without the consumed head.
        new_queue = queue[1:]
        atomic_write_yaml(
            self._pm_dir / "decision-queue.yaml",
            {
                "schema_version": ACCEPTED_SCHEMA_VERSION,
                "queue": new_queue,
            },
        )

        # 3. Update state.yaml's last_surfaced_at.
        state = load_state_yaml(self._pm_dir)
        state["last_surfaced_at"] = surfaced_at_iso
        atomic_write_yaml(
            self._pm_dir / "state.yaml",
            {
                "schema_version": ACCEPTED_SCHEMA_VERSION,
                "in_flight": state.get("in_flight") or [],
                "last_surfaced_at": state["last_surfaced_at"],
                "notes": state.get("notes") or "",
            },
        )

        return SurfacedQuestion(
            text=head["text"],
            provenance=head.get("provenance"),
            queue_position=position_pre,
            surfaced_at=surfaced_at_iso,
            audit_path=audit_path,
        )
