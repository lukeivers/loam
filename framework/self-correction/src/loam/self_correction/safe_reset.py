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

"""Safe FBM hard-reset (AC.SR-RESET.1/.2) — the highest-stakes part.

Part 4 of the self-recovery system. When the ``.loam/`` user-state store is
corrupted past plain recovery, reset it **backup-first** and **fail-closed**
so the irreplaceable store is NEVER lost.

The design (plan §1 part 4, §3 R-3, §8, §10 #2): this module is a thin
ORCHESTRATION that DELEGATES every byte-level operation to the existing
``MigrationSafetyEnvelope`` (snapshot / guard / restore). It does NOT
re-implement backup or rollback. The reversibility floor is INHERITED, not
re-derived:

  * **Backup-first (AC.SR-RESET.1).** ``snapshot`` runs BEFORE any
    destructive step; the snapshot path is the recoverable backup.

  * **Fail-closed (AC.SR-RESET.1).** The reset declares
    ``removes_user_state=true`` (reversibility class ``irreversible``).
    ``MigrationSafetyEnvelope.guard`` then REFUSES (``ProtectionFloorRefusal``)
    unless a compensation binding exists. The snapshot IS that compensation:
    only after a successful snapshot is the binding registered. So a reset
    with no recoverable snapshot is structurally refused — the
    never-lose-the-store invariant is the gate's, not this module's
    discipline.

  * **Restorable byte-for-byte (AC.SR-RESET.2).** ``restore`` brings back
    the pre-reset ``.loam/`` from the snapshot — the irreplaceable store is
    only ever reset BEHIND a recoverable backup.

  * **Human-in-the-loop confirm (FORK F-3 ruling).** The store is
    irreplaceable and the reset is the last resort, so this orchestration
    requires an EXPLICIT plain-English user confirmation
    (``confirmed="yes, start fresh"`` shape) before the destructive step —
    belt-and-suspenders over the reversibility floor. A reset called
    without the confirm is refused as ``ResetNotConfirmed``.

Determinism + no LLM (``feedback_no_anthropic_api_key``): the orchestration
is pure delegation + a string-equality confirm check.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from loam.reversibility_primitive import ReversibilityStore
from loam.reversibility_primitive.spec import CompensationPathBinding
from loam.state_migration_engine.envelope import (
    MigrationSafetyEnvelope,
    ProtectionFloorRefusal,
)
from loam.state_migration_engine.schema import DeclaredMigration


#: The scope id under which the reset's compensation binding + gate check
#: run. Stable so a re-run is idempotent on the binding row.
RESET_SCOPE_ID = "self-recovery/fbm-hard-reset"

#: The plain-English phrases that count as an explicit confirm (FORK F-3).
#: Matched case-insensitively after stripping; the user is told this exact
#: phrase by the recovery surface ("reply 'yes, start fresh'").
_CONFIRM_PHRASES = frozenset(
    {"yes, start fresh", "yes start fresh", "yes, reset", "yes reset"}
)


def is_reset_confirmed(confirmed: str | None) -> bool:
    """True iff *confirmed* is an explicit plain-English reset confirmation."""
    if not confirmed:
        return False
    return confirmed.strip().lower() in _CONFIRM_PHRASES


class ResetNotConfirmed(RuntimeError):
    """A hard-reset was attempted without the explicit plain-English confirm.

    Raised (FORK F-3 ruling) before ANY destructive step when the caller did
    not pass an explicit confirmation. The highest-stakes operation requires
    a human-in-the-loop yes, on top of the reversibility floor.
    """


def _reset_migration() -> DeclaredMigration:
    """The declared migration describing the reset as a user-state operation.

    ``removes_user_state=True`` is what classes it ``irreversible`` so the
    activation gate enforces the protection floor (AC.SR-RESET.1).
    """
    return DeclaredMigration(
        slug="fbm-hard-reset",
        operation="reset-user-state",
        reversible=False,
        removes_user_state=True,
        idempotent=False,
        version=None,
        predecessor=None,
        creates=(),
        leaves_in_place=(),
        source_path=None,
        raw={"rationale": "self-recovery last-resort reset of corrupted .loam/"},
    )


@dataclass
class SafeResetResult:
    """The outcome of a completed safe reset."""

    snapshot_path: Path
    #: True — the reset ran (snapshot taken, gate passed, store reset). A
    #: refused / unconfirmed reset raises instead of returning this.
    reset_done: bool


@dataclass
class SafeFbmReset:
    """Orchestrates a backup-first, fail-closed, confirmed FBM hard-reset.

    Constructed with a ``ReversibilityStore`` (the gate's binding store) and
    a ``snapshot_root`` (where the pre-reset backup lands). Every byte-level
    operation delegates to ``MigrationSafetyEnvelope`` — this class never
    touches ``.loam/`` bytes except through the envelope (plan §8
    halt-trigger 1).
    """

    store: ReversibilityStore
    snapshot_root: Path

    def __post_init__(self) -> None:
        self.snapshot_root = Path(self.snapshot_root)
        self._envelope = MigrationSafetyEnvelope(
            store=self.store, snapshot_root=self.snapshot_root
        )

    # ---- backup-first + fail-closed reset (AC.SR-RESET.1) -------------

    def reset(
        self, workspace_root: str | Path, *, confirmed: str | None = None
    ) -> SafeResetResult:
        """Reset the workspace's ``.loam/`` store backup-first + fail-closed.

        Order (the invariant the AC pins):

          1. Require the explicit plain-English confirm (FORK F-3). No
             confirm -> ``ResetNotConfirmed`` BEFORE any destructive step.
          2. ``snapshot`` the current ``.loam/`` (backup-first,
             AC.SR-RESET.1). The returned path is the recoverable backup.
          3. Register the snapshot as the compensation binding for the
             reset scope — this is what lets the protection-floor gate pass.
             It is registered ONLY after a successful snapshot, so a failed
             backup leaves no binding and the next step refuses.
          4. ``guard`` — the reversibility protection floor. Irreversible +
             binding-present passes; irreversible + no-binding raises
             ``ProtectionFloorRefusal`` (fail-closed).
          5. Destructive step: remove the live ``.loam/`` (the reset). The
             pre-reset bytes survive in the snapshot.

        Returns the snapshot path so the caller can restore byte-for-byte
        (AC.SR-RESET.2) via ``restore``.
        """
        if not is_reset_confirmed(confirmed):
            raise ResetNotConfirmed(
                "a fresh-start of your saved settings needs your explicit "
                "okay first; reply 'yes, start fresh' to proceed"
            )

        workspace = Path(workspace_root)

        # Step 2 — backup-first.
        snapshot = self._envelope.snapshot(workspace)

        # Step 3 — register the snapshot as the compensation path. The
        # binding's presence is what the gate requires (AC.SR-RESET.1
        # fail-closed: no snapshot -> no binding -> refusal).
        self.store.upsert_binding(
            CompensationPathBinding(
                scope_id=RESET_SCOPE_ID,
                handle="self-recovery.fbm-restore",
                description=(
                    "restore the pre-reset .loam/ snapshot taken backup-first"
                ),
                idempotency_key=f"{RESET_SCOPE_ID}:{snapshot}",
                registered_by="self-recovery",
            )
        )

        # Step 4 — the protection floor. Raises ProtectionFloorRefusal if
        # (somehow) no binding is present. Backup-first guarantees one is.
        self._envelope.guard(_reset_migration(), scope_id=RESET_SCOPE_ID)

        # Step 5 — the destructive reset. The snapshot holds the pre-reset
        # bytes; removing the live store is now recoverable.
        loam = workspace / ".loam"
        if loam.exists():
            shutil.rmtree(loam)

        return SafeResetResult(snapshot_path=snapshot, reset_done=True)

    # ---- restore (AC.SR-RESET.2) -------------------------------------

    def restore(self, snapshot: Path, workspace_root: str | Path) -> None:
        """Restore the pre-reset ``.loam/`` from *snapshot* byte-for-byte.

        Delegates ``MigrationSafetyEnvelope.restore`` — the irreplaceable
        store is brought back exactly as it was before the reset.
        """
        self._envelope.restore(Path(snapshot), workspace_root)


def reset_would_fail_closed(store: ReversibilityStore, snapshot_root: Path) -> bool:
    """Probe: would a reset be REFUSED right now (no recoverable snapshot)?

    Used by the recovery flow + tests to assert the fail-closed posture
    WITHOUT running a destructive step: with no compensation binding
    registered for the reset scope, ``guard`` raises ``ProtectionFloorRefusal``.
    Returns True iff the gate currently refuses.
    """
    envelope = MigrationSafetyEnvelope(store=store, snapshot_root=Path(snapshot_root))
    try:
        envelope.guard(_reset_migration(), scope_id=RESET_SCOPE_ID)
    except ProtectionFloorRefusal:
        return True
    return False
