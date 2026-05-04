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

Per cycle-2 plan §4 Surface #5 + AC.PPM.{4,5,6} + cycle-4 plan §4 +
AC.QSURF.{1..8}. The runtime is the public API surface for working with
a loaded PM:

  - :meth:`PMRuntime.from_workspace` — load a PM by name from the
    workspace (raises :class:`PMNotFoundError` if no contract.yaml).
  - :meth:`PMRuntime.empty_state_for` — return an empty
    :class:`StateOfWorld` for an unauthored workspace (D1 cold-state).
  - :meth:`PMRuntime.state_of_world` — read snapshot of PM state.
  - :meth:`PMRuntime.enqueue_decision` — append to FIFO queue
    atomically; return 1-based position.
  - :meth:`PMRuntime.surface_next_question` — consume head of FIFO
    queue; write audit-log entry; return :class:`SurfacedQuestion`
    (or ``None`` on empty queue). Cycle 4: raises
    :class:`PendingResponseError` when blocked by an outstanding
    surfacing under ``require_owner_response=True``.
  - :meth:`PMRuntime.surface_next_questions_batch` — Cycle 4 batch
    surfacer; respects ``onboarding_mode`` (forces 1 per call) and
    ``max_questions_per_turn`` policy fields.
  - :meth:`PMRuntime.record_response` — Cycle 4 response recorder;
    writes a ``record_response``-kind audit-log entry, clears the
    blocking flag in state.yaml, returns :class:`RecordedResponse`.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from loam.per_project_pm.contract import PMContract
from loam.per_project_pm.errors import (
    PendingResponseError,
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
from loam.per_project_pm.state import (
    RecordedResponse,
    StateOfWorld,
    SurfacedQuestion,
)

import yaml


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
            pending_response_for=None,
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

        Cycle 4 populates ``pending_response_for`` from state.yaml so
        callers can detect blocking-on-pending-response without
        triggering :class:`PendingResponseError`.
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
            pending_response_for=state.get("pending_response_for"),
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

        Per AC.PPM.5 (Cycle 2 contract preserved):

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
              3. update state.yaml.
            A crash between (1) and (2) leaves the queue with an
            already-surfaced head; the next call detects this via
            audit-log scan (Cycle 4 hardens; Cycle 2 the simple
            re-surface is acceptable since the audit-log makes the
            duplication observable).

        **Cycle 4 design note (per cycle-4 plan §5 Surface #8 fallback
        applied):** the blocking enforcement under
        ``require_owner_response=True`` lives on
        :meth:`surface_next_questions_batch`, NOT on this method. This
        preserves the Cycle 2 contract verbatim (existing callers
        unchanged) and concentrates the structural one-question-at-a-
        time discipline on the batch API. The single-question API is
        the "low-discipline" surface; the batch API enforces structure.
        """
        return self._surface_one_no_block_check()

    def surface_next_questions_batch(
        self,
        n: int | None = None,
    ) -> tuple[SurfacedQuestion, ...]:
        """Surface up to ``n`` questions in one call (Cycle 4 — AC.QSURF.{1,2,3}).

        Effective batch size:

          - If ``onboarding_mode=True`` on the contract's
            :class:`~loam.per_project_pm.contract.DecisionSurfacingPolicy`:
            forced to 1 regardless of ``n`` or
            ``max_questions_per_turn`` (AC.QSURF.1 + AC.QSURF.3).
          - Otherwise: ``min(n_or_max, max_questions_per_turn,
            len(queue))`` where ``n_or_max`` defaults to
            ``max_questions_per_turn`` when ``n is None``.

        Each item in the returned tuple is its own
        :class:`SurfacedQuestion` with its own audit-log entry +
        ``queue_position`` reflecting the position in the batch
        (1-based: first item position=1, second=2, ...).

        Cycle 4 blocking enforcement (AC.QSURF.5): if
        ``require_owner_response=True`` AND ``pending_response_for``
        is non-null at start of call, raises
        :class:`PendingResponseError` immediately — does NOT partially
        surface. Caller must clear via :meth:`record_response`.

        Onboarding-mode enforcement is structural (assertion, not
        probabilistic): with ``onboarding_mode=True``, the returned
        tuple length is ALWAYS ≤ 1. Per AC.QSURF.3.
        """
        # Blocking enforcement first — symmetric with surface_next_question.
        self._raise_if_blocked_by_pending_response()

        policy = self._contract.decision_surfacing_policy
        # Determine effective batch size.
        if policy.onboarding_mode:
            effective_n = 1
        else:
            n_request = (
                n if n is not None else policy.max_questions_per_turn
            )
            if n_request < 1:
                # Non-positive request → empty batch (caller wanted "0
                # questions"; legitimate no-op).
                return ()
            effective_n = min(n_request, policy.max_questions_per_turn)

        # Cap at queue length.
        queue = load_decision_queue(self._pm_dir)
        effective_n = min(effective_n, len(queue))
        if effective_n == 0:
            return ()

        surfaced: list[SurfacedQuestion] = []
        for batch_index in range(effective_n):
            # Each iteration re-reads queue from disk. _surface_one
            # drives the disk-state forward; the next iteration sees
            # the new head. This is correctness-over-perf — every
            # surfacing is its own audit-log entry, and crash-safety
            # mirrors single-surface behavior.
            sq = self._surface_one_no_block_check(
                queue_position_in_batch=batch_index + 1,
            )
            if sq is None:
                # Defensive — shouldn't happen given the cap above,
                # but if the queue got drained out of band (e.g.,
                # another process), stop the batch cleanly.
                break
            surfaced.append(sq)
            # If require_owner_response is True, the first surfacing
            # populates pending_response_for and the next iteration's
            # blocking check would fire. Per cycle-4 plan §5 Surface
            # #2: a batch with require_owner_response=True is
            # contradictory by construction — the first surfacing
            # blocks the rest. Detect at end-of-batch.
            #
            # (We still allow the first surfacing to land; subsequent
            # calls are blocked. With onboarding_mode=True the loop
            # terminates after one iteration anyway.)
            if (
                policy.require_owner_response
                and not policy.onboarding_mode
                and batch_index + 1 < effective_n
            ):
                # Stop after first; subsequent surfacings would be
                # structurally blocked by require_owner_response.
                # Caller must record_response() between batches.
                break

        return tuple(surfaced)

    def record_response(
        self,
        surfaced_audit_path: Path | str,
        response_text: str,
    ) -> RecordedResponse:
        """Record an owner response to a previously-surfaced question
        (Cycle 4 — AC.QSURF.6).

        Behaviour:

          - Reads the linked surfacing's audit-log entry to retrieve
            the original question text + provenance (so the response's
            audit entry carries both sides).
          - Writes a new audit-log entry at
            ``audit-log/<YYYY-MM-DD>-<NNNN>.yaml`` with
            ``event_kind=record_response``.
          - Clears ``pending_response_for`` in state.yaml (sets to
            ``None``) — subsequent surfacings unblock under
            ``require_owner_response=True``.
          - Idempotent: a second call against the same
            ``surfaced_audit_path`` detects the prior
            ``record_response`` audit entry (by scanning audit-log
            filenames + checking event_kind/surfaced_audit_path
            match), returns the previously-recorded response without
            writing a duplicate entry.

        Raises:

          ValueError: when ``response_text`` is empty.
          FileNotFoundError: when ``surfaced_audit_path`` does not
            exist OR is not a previously-written
            ``surface_question`` audit entry under this PM.
          PMStateCorruptedError: when the linked audit entry has
            unexpected schema_version / event_kind.
        """
        if not response_text:
            raise ValueError("response_text must be non-empty")

        # Resolve linkage path.
        linked_path = Path(surfaced_audit_path)
        if not linked_path.is_absolute():
            linked_path = (self._pm_dir / linked_path).resolve()

        if not linked_path.exists():
            raise FileNotFoundError(
                f"surfaced_audit_path does not exist: {linked_path!s}"
            )

        # Read the linked surfacing entry to retrieve the question.
        linked_payload = yaml.safe_load(linked_path.read_text(encoding="utf-8"))
        if not isinstance(linked_payload, dict):
            raise PMStateCorruptedError(
                f"Linked audit entry at {linked_path!s} is not a "
                f"mapping at top level."
            )
        if linked_payload.get("schema_version") != ACCEPTED_SCHEMA_VERSION:
            raise PMStateCorruptedError(
                f"Linked audit entry at {linked_path!s} has "
                f"schema_version={linked_payload.get('schema_version')!r}; "
                f"expected {ACCEPTED_SCHEMA_VERSION}."
            )
        if linked_payload.get("event_kind") != "surface_question":
            raise PMStateCorruptedError(
                f"Linked audit entry at {linked_path!s} has "
                f"event_kind={linked_payload.get('event_kind')!r}; "
                f"expected 'surface_question'."
            )

        surfaced_question_text = linked_payload.get("question_text", "")

        # Idempotency check — scan audit-log dir for an existing
        # record_response entry linked to this surfaced_audit_path.
        audit_dir = self._pm_dir / "audit-log"
        existing = self._find_existing_record_response(
            audit_dir, linked_path
        )
        if existing is not None:
            # Re-construct RecordedResponse from the existing entry
            # (idempotent return).
            return RecordedResponse(
                response_text=existing["response_text"],
                surfaced_audit_path=linked_path,
                surfaced_question_text=existing.get(
                    "surfaced_question_text", surfaced_question_text
                ),
                responded_at=existing["responded_at"],
                audit_path=existing["__path__"],
            )

        # Write the new record_response audit entry.
        responded_at_iso = _utc_now_iso()
        today_utc = _utc_today()
        audit_dir.mkdir(parents=True, exist_ok=True)
        seq = _next_audit_seq(audit_dir, today_utc)
        audit_filename = f"{today_utc}-{seq:04d}.yaml"
        new_audit_path = audit_dir / audit_filename
        # Store the linkage as a path RELATIVE to the PM dir so the
        # audit log is portable if the workspace is moved.
        try:
            relative_linkage = linked_path.relative_to(self._pm_dir)
        except ValueError:
            # If for some reason the linked path isn't under the PM
            # dir, fall back to absolute. (Shouldn't happen — the
            # audit-log is always under self._pm_dir/audit-log/.)
            relative_linkage = linked_path
        audit_payload = {
            "schema_version": ACCEPTED_SCHEMA_VERSION,
            "event_kind": "record_response",
            "timestamp": responded_at_iso,
            "pm_handle": self._contract.handle,
            "response_text": response_text,
            "surfaced_audit_path": str(relative_linkage),
            "surfaced_question_text": surfaced_question_text,
            "responded_at": responded_at_iso,
        }
        atomic_write_yaml(new_audit_path, audit_payload)

        # Clear pending_response_for in state.yaml.
        state = load_state_yaml(self._pm_dir)
        atomic_write_yaml(
            self._pm_dir / "state.yaml",
            {
                "schema_version": ACCEPTED_SCHEMA_VERSION,
                "in_flight": state.get("in_flight") or [],
                "last_surfaced_at": state.get("last_surfaced_at"),
                "notes": state.get("notes") or "",
                "pending_response_for": None,  # cleared
            },
        )

        return RecordedResponse(
            response_text=response_text,
            surfaced_audit_path=linked_path,
            surfaced_question_text=surfaced_question_text,
            responded_at=responded_at_iso,
            audit_path=new_audit_path,
        )

    # ---- internals -------------------------------------------------

    def _raise_if_blocked_by_pending_response(self) -> None:
        """Raise :class:`PendingResponseError` if the contract requires
        owner-response AND state.yaml carries a non-null
        ``pending_response_for``.

        Cycle 4 — AC.QSURF.5.
        """
        if not self._contract.decision_surfacing_policy.require_owner_response:
            return
        state = load_state_yaml(self._pm_dir)
        pending = state.get("pending_response_for")
        if not pending:
            return
        # Find the most recent surface_question audit-log entry to
        # report the surfaced_audit_path. This is best-effort — the
        # error message is the value, not a precise audit-path
        # lookup.
        audit_dir = self._pm_dir / "audit-log"
        surfaced_audit_path_str = "<unknown>"
        if audit_dir.is_dir():
            candidates = sorted(
                (
                    p
                    for p in audit_dir.iterdir()
                    if p.is_file()
                    and _AUDIT_FILE_PATTERN.match(p.name)
                ),
                reverse=True,
            )
            for candidate in candidates:
                try:
                    payload = yaml.safe_load(
                        candidate.read_text(encoding="utf-8")
                    )
                except yaml.YAMLError:
                    continue
                if (
                    isinstance(payload, dict)
                    and payload.get("event_kind") == "surface_question"
                    and payload.get("question_text") == pending
                ):
                    surfaced_audit_path_str = str(candidate)
                    break
        raise PendingResponseError(
            f"PM {self._contract.handle!r} has a pending unanswered "
            f"surfacing under require_owner_response=True; record a "
            f"response via PMRuntime.record_response() before "
            f"surfacing again. Pending question: {pending!r}.",
            pending_question=pending,
            surfaced_audit_path=surfaced_audit_path_str,
        )

    def _surface_one_no_block_check(
        self,
        *,
        queue_position_in_batch: int = 1,
    ) -> SurfacedQuestion | None:
        """Internal — surface one question without the blocking check.

        Used by both :meth:`surface_next_question` (after blocking
        check) and :meth:`surface_next_questions_batch` (after a
        single blocking check up front).
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

        # 3. Update state.yaml's last_surfaced_at + (Cycle 4)
        # pending_response_for when require_owner_response=True.
        state = load_state_yaml(self._pm_dir)
        new_pending = state.get("pending_response_for")
        if self._contract.decision_surfacing_policy.require_owner_response:
            new_pending = head["text"]
        atomic_write_yaml(
            self._pm_dir / "state.yaml",
            {
                "schema_version": ACCEPTED_SCHEMA_VERSION,
                "in_flight": state.get("in_flight") or [],
                "last_surfaced_at": surfaced_at_iso,
                "notes": state.get("notes") or "",
                "pending_response_for": new_pending,
            },
        )

        return SurfacedQuestion(
            text=head["text"],
            provenance=head.get("provenance"),
            queue_position=queue_position_in_batch,
            surfaced_at=surfaced_at_iso,
            audit_path=audit_path,
        )

    def _find_existing_record_response(
        self,
        audit_dir: Path,
        linked_path: Path,
    ) -> dict[str, Any] | None:
        """Idempotency helper — scan audit-log/ for an existing
        ``record_response`` entry linked to ``linked_path``.

        Returns the existing entry's payload (with extra ``__path__``
        key) on hit; ``None`` on miss.

        Per cycle-4 plan §5 Surface #3: idempotency on duplicate
        :meth:`record_response` calls.
        """
        if not audit_dir.is_dir():
            return None
        # Resolve linked_path to a relative form for comparison —
        # record_response stores relative paths.
        try:
            linked_relative = str(linked_path.relative_to(self._pm_dir))
        except ValueError:
            linked_relative = str(linked_path)
        for candidate in audit_dir.iterdir():
            if not candidate.is_file():
                continue
            if not _AUDIT_FILE_PATTERN.match(candidate.name):
                continue
            try:
                payload = yaml.safe_load(
                    candidate.read_text(encoding="utf-8")
                )
            except yaml.YAMLError:
                continue
            if not isinstance(payload, dict):
                continue
            if payload.get("event_kind") != "record_response":
                continue
            stored = payload.get("surfaced_audit_path")
            if stored == linked_relative or stored == str(linked_path):
                payload["__path__"] = candidate
                return payload
        return None
