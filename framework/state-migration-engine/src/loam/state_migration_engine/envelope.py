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

"""The migration SAFETY ENVELOPE — composes the reversibility primitive.

This module is where the replay engine WRAPS its safety in
``framework/reversibility-primitive`` AS A LIBRARY CALL (plan §2 / verified
ground). The composition is deliberate about WHAT the primitive owns vs what
this engine owns:

  * The reversibility primitive owns the *governance*: the reversibility-class
    decision matrix (``ActivationGate.check`` — R6..R12) that REFUSES a
    destructive operation lacking a compensation binding / safety approval
    (the protection floor, AC.MIG-SAFE.4). That refusal is a pure, synchronous
    library call — it needs only a ``ReversibilityStore`` + a ``ScopeSpec``
    carrying a ``reversibility_class``; no IPC server.

  * This engine owns the *byte-level snapshot*: the reversibility primitive's
    rollback runtime runs a registered COMPENSATION HANDLER, and the handler
    is what restores the actual ``.loam/`` bytes. So the engine provides the
    snapshot-of-bytes (``snapshot`` -> ``restore``) as the compensation path,
    and binds it to the migration scope. This is the intended seam: the
    primitive is a reversibility *governor*, not a filesystem backup library
    (it was never one). The snapshot is registered, the primitive governs.

Why this is NOT halt-trigger 2 (plan §8 #2): the envelope IS composable as a
library call -- ``ActivationGate`` + ``ReversibilityStore`` + ``ReversibilityClass``
are importable, constructible, and callable without standing up an IPC server.
The engine composes those; it does not author a parallel backup/rollback
mechanism (the boundary leak the plan warns against).
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from loam.reversibility_primitive import ActivationGate, ReversibilityStore
from loam.scope_of_work import (
    Budget,
    ReversibilityClass,
    ScopeSpec,
    SuccessCriterion,
)

from .schema import DeclaredMigration


def classify_migration(migration: DeclaredMigration) -> ReversibilityClass:
    """Map a declared migration to a reversibility class (AC.MIG-SAFE.4).

    The class is derived SOLELY from the declared file (AC.MIG-SCHEMA.3):

      * ``removes_user_state: true`` -> ``irreversible``. A migration that
        declares it removes / compresses / overwrites user-state is the
        protection-floor (G-star) case: the activation gate refuses it unless
        a compensation binding or safety approval is present.

      * everything else (the non-destructive declarative vocabulary --
        ``no-op`` / ``structural-only`` / ``schema-add-forward-additive`` /
        ``none-code-only``) -> ``fully_reversible``. A pre-replay snapshot
        makes the whole replay trivially recoverable, so the gate passes it
        without requiring a binding (R6).
    """
    if migration.removes_user_state:
        return ReversibilityClass.irreversible
    return ReversibilityClass.fully_reversible


def _spec_for(migration: DeclaredMigration) -> ScopeSpec:
    """A minimal ScopeSpec carrying the migration's reversibility class.

    The gate dispatches purely on ``reversibility_class`` (it does not run the
    migration); the rest of the spec is well-formed boilerplate.
    """
    return ScopeSpec(
        goal=f"apply declared user-state migration {migration.slug!r}",
        constraints=(),
        budget=Budget(time_seconds=300, money_cents=None),
        reversibility_class=classify_migration(migration),
        success_criteria=(
            SuccessCriterion(
                criterion_id="cursor-advanced",
                description="the applied cursor records this migration",
            ),
        ),
        observers=(),
        escalation_triggers=(),
    )


class ProtectionFloorRefusal(RuntimeError):
    """A migration was refused by the protection-floor activation gate.

    Raised (AC.MIG-SAFE.4) when a destructive migration (declared
    ``removes_user_state: true``, classed ``irreversible``) reaches the gate
    with no compensation binding + no safety approval. Surfaces the underlying
    reversibility refusal so the operator sees WHY the migration was blocked.
    """


@dataclass
class MigrationSafetyEnvelope:
    """Composes the reversibility primitive's governance over a replay.

    Constructed with a backing ``ReversibilityStore`` (the same SQLite store
    the primitive uses for compensation bindings). ``snapshot_root`` is where
    the pre-replay byte snapshot of ``.loam/`` is written.

    Usage (the replay engine drives this):

        env = MigrationSafetyEnvelope(store, snapshot_root)
        snap = env.snapshot(workspace_root)          # backup-first
        env.guard(migration, scope_id="...")         # protection floor
        try:
            ...apply declarative steps...
        except Exception:
            env.restore(snap, workspace_root)         # rollback-on-failure
            raise
    """

    store: ReversibilityStore
    snapshot_root: Path

    def __post_init__(self) -> None:
        self.snapshot_root = Path(self.snapshot_root)
        # The activation gate is the primitive's pure class-dispatch surface.
        # No safety_approval_resolver is injected -> R12 fail-closed posture:
        # an irreversible migration with no compensation binding is REFUSED.
        self.gate = ActivationGate(store=self.store)

    # ---- backup-first (AC.MIG-SAFE.1) ---------------------------------

    def snapshot(self, workspace_root: str | Path) -> Path:
        """Take a recoverable backup of the workspace's ``.loam/`` state.

        Copies ``<workspace>/.loam/`` into ``snapshot_root`` BEFORE any
        migration mutates user-state. Returns the snapshot path. If ``.loam/``
        does not yet exist (a brand-new instance), the snapshot is an empty
        marker dir -- restore then simply removes any ``.loam/`` the failed
        replay created.
        """
        loam = Path(workspace_root) / ".loam"
        self.snapshot_root.mkdir(parents=True, exist_ok=True)
        dest = self.snapshot_root / "loam-snapshot"
        if dest.exists():
            shutil.rmtree(dest)
        if loam.exists():
            shutil.copytree(loam, dest, symlinks=True)
        else:
            dest.mkdir(parents=True)
        return dest

    # ---- protection-floor gate (AC.MIG-SAFE.4) ------------------------

    def guard(self, migration: DeclaredMigration, *, scope_id: str) -> None:
        """Run the reversibility activation gate for *migration*.

        Composes ``ActivationGate.check`` (R6..R12). A non-destructive
        migration (``fully_reversible``) passes. A destructive migration
        (``irreversible``) with no compensation binding registered for
        *scope_id* RAISES ``ProtectionFloorRefusal`` -- surface-don't-delete.
        """
        spec = _spec_for(migration)
        try:
            self.gate.check(spec, scope_id=scope_id)
        except Exception as exc:  # ApplicationError(-32050) on refusal
            raise ProtectionFloorRefusal(
                f"migration {migration.slug!r} "
                f"(class={spec.reversibility_class.value}) refused by the "
                f"reversibility protection floor: {exc}. It declares "
                f"removes_user_state=true with no compensation binding; "
                f"register a compensation path or a safety approval before "
                f"applying it."
            ) from exc

    # ---- rollback-on-failure (AC.MIG-SAFE.2) --------------------------

    def restore(self, snapshot: Path, workspace_root: str | Path) -> None:
        """Restore ``.loam/`` from *snapshot* -- the rollback path.

        Replaces the (possibly half-migrated) ``<workspace>/.loam/`` with the
        snapshot taken before the replay began, leaving a consistent,
        recoverable instance (no half-migrated state). This is the byte-level
        work the reversibility primitive's compensation handler delegates to
        the engine.
        """
        loam = Path(workspace_root) / ".loam"
        if loam.exists():
            shutil.rmtree(loam)
        snap = Path(snapshot)
        # An empty snapshot (brand-new instance) means "there was no .loam/
        # before"; restoring it leaves no .loam/, which is correct.
        if any(snap.iterdir()):
            shutil.copytree(snap, loam, symlinks=True)
