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

"""First-run↔update parity registry + idempotent replay
(session-`/clear`-safety G — sub-amendment 3 of 3).

D-SCS.2 (owner-RATIFIED): a NEW lightweight replay-on-update registry,
explicitly NOT an extension of ``first-run-inventory.yaml``. That file
is a venv/services provisioning manifest with no per-item update-path,
and the existing re-run model (``run_first_run_scaffold`` →
``already_scaffolded`` short-circuit, AC36.3 — re-run is a by-design
no-op) IS the exact mechanism of the defect this plan closes: a
newly-added state-mutating setup step is never replayed against an
existing workspace, so the workspace silently misses it. Reusing
``first-run-inventory.yaml`` would entrench the bug; this registry is
the structural alternative (§11 evidence).

The class being fixed (plan §2 gap G, owner-generalized): ANY
state-mutating first-run/setup step needs a registered, idempotent
update-path the workspace-update process discovers + replays for
EXISTING (already-initialized) workspaces. The empty objective-tracker
(R1's backfill is the first registered consumer, AC.SCS-G.3) is the
instance; the missing class-mechanism is the root structural hole.

Design (D-SCS-G.build.*, builder's call narrated at build):

- ``ParityStep``: a named state-mutating setup step + its idempotent
  update-path callable. The update-path takes a workspace root and is
  contractually idempotent (a second replay is a no-op; it does NOT
  clobber user-authored state) — the registry does not enforce
  idempotency mechanically (it cannot inspect an opaque callable), it
  contracts it and AC.SCS-G.2 verifies a registered step honours it.
- module-level ``_REGISTRY`` + ``register_parity_step`` +
  ``discover_parity_steps``: the single discoverable surface
  (AC.SCS-G.1) the workspace-update process enumerates with no code
  change to the discoverer when a step is added.
- ``replay_parity_steps``: the workspace-update driver. Runs each
  registered step's update-path against an existing workspace; a step
  whose update-path is absent (None) or raises surfaces a structured,
  NON-SILENT gap (AC.SCS-G.4 — the failure class being fixed cannot
  recur as a silent skip) while still replaying the remaining steps;
  the run is idempotent (AC.SCS-G.2).

Per ODD §2.5 every branch traces to a named AC: the discovery surface
(G.1), the idempotent replay (G.2), the R1-registration (G.3), the
non-silent gap surfacing (G.4). There is no unbacked defensive branch
— the absent/failed-update-path branch is AC.SCS-G.4, not a swallow.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


# ---- the parity step ------------------------------------------------


# An update-path takes the workspace root and applies the registered
# step's state mutation idempotently against an EXISTING workspace.
# Return value is opaque (the step's own structured result); the
# replay driver records it for the report but does not interpret it.
UpdatePath = Callable[[Path], Any]


@dataclass(frozen=True)
class ParityStep:
    """A state-mutating first-run/setup step that must also run on
    update, plus its idempotent update-path.

    ``name`` is the stable identifier the workspace-update process
    enumerates (AC.SCS-G.1). ``update_path`` is the idempotent
    callable replayed against an existing workspace (AC.SCS-G.2); it
    is ``None`` when a step is registered as participating in the
    parity contract but its update-path has not been wired — that
    absence is surfaced NON-silently by the replay driver (AC.SCS-G.4),
    never swallowed.
    """

    name: str
    update_path: UpdatePath | None = None
    description: str = ""


# ---- the registry (single discoverable surface — AC.SCS-G.1) --------


_REGISTRY: dict[str, ParityStep] = {}


class ParityStepCollisionError(Exception):
    """Two steps registered under the same name. Names are the stable
    enumeration key; a silent overwrite would make the discovery
    surface lie about what runs on update."""


def register_parity_step(step: ParityStep) -> None:
    """Register a state-mutating setup step in the parity registry.

    The workspace-update process discovers it via
    ``discover_parity_steps`` with NO code change to the discoverer
    (AC.SCS-G.1 — adding a step is a registration, not a discoverer
    edit). A duplicate name raises rather than silently overwriting
    (a silent overwrite would corrupt the single-discoverable-surface
    contract)."""
    if step.name in _REGISTRY:
        raise ParityStepCollisionError(
            f"parity step {step.name!r} already registered; names are the "
            f"stable enumeration key and must be unique"
        )
    _REGISTRY[step.name] = step


def discover_parity_steps() -> tuple[ParityStep, ...]:
    """Enumerate every registered state-mutating setup step.

    This is the single registry surface the workspace-update process
    consumes to answer "what must also run on update" (AC.SCS-G.1).
    Order is registration order (deterministic)."""
    return tuple(_REGISTRY.values())


def unregister_parity_step(name: str) -> None:
    """Remove a step (test-isolation seam; production never calls
    this). Absent name is a no-op — unregistering is idempotent."""
    _REGISTRY.pop(name, None)


# ---- the workspace-update replay driver (AC.SCS-G.2 / G.4) ----------


@dataclass(frozen=True)
class ParityStepOutcome:
    """One step's replay result.

    ``status`` is one of:
      - ``"replayed"``      — the update-path ran (idempotently);
                              ``result`` carries its opaque return.
      - ``"absent"``        — the step has no wired update-path;
                              surfaced NON-silently (AC.SCS-G.4),
                              not swallowed.
      - ``"failed"``        — the update-path raised; the error class
                              + message are surfaced NON-silently
                              (AC.SCS-G.4); remaining steps still run.
    """

    name: str
    status: str
    detail: str = ""
    result: Any = None


@dataclass(frozen=True)
class ParityReplayReport:
    """Structured outcome of one ``replay_parity_steps`` invocation.

    ``ok`` is True iff every registered step replayed cleanly (no
    ``absent``/``failed``). ``gaps`` lists the non-clean steps so the
    update process surfaces them explicitly (AC.SCS-G.4) rather than
    the failure class recurring as a silent skip."""

    outcomes: tuple[ParityStepOutcome, ...] = ()
    ok: bool = True
    gaps: tuple[str, ...] = field(default_factory=tuple)


def replay_parity_steps(workspace_root: Path | str) -> ParityReplayReport:
    """Replay every registered parity step's update-path against an
    EXISTING workspace (the workspace-update process entry-point).

    Idempotent (AC.SCS-G.2): each registered step's update-path is
    contractually idempotent (query-then-skip / sentinel / content-
    hash — the step's own concern); a second ``replay_parity_steps``
    against the same workspace is therefore a no-op and never clobbers
    user-authored state.

    Non-silent on gaps (AC.SCS-G.4): a step with no wired update-path
    (``update_path is None``) is reported ``absent``; a step whose
    update-path raises is reported ``failed`` with the error class +
    message. Either way the gap is surfaced in the report (``ok=False``,
    listed in ``gaps``) — the workspace-update process does NOT silently
    skip, so the exact failure class being fixed (a setup step silently
    not replayed) cannot recur. Remaining steps still replay so one
    broken step does not strand the rest.
    """
    ws = Path(workspace_root)
    outcomes: list[ParityStepOutcome] = []
    gaps: list[str] = []

    for step in discover_parity_steps():
        if step.update_path is None:
            outcomes.append(
                ParityStepOutcome(
                    name=step.name,
                    status="absent",
                    detail=(
                        f"parity step {step.name!r} is registered but has "
                        f"no wired update-path; update process surfaces "
                        f"the gap (not a silent skip)"
                    ),
                )
            )
            gaps.append(step.name)
            continue
        try:
            result = step.update_path(ws)
        except Exception as exc:  # AC.SCS-G.4 — surface, do not swallow
            outcomes.append(
                ParityStepOutcome(
                    name=step.name,
                    status="failed",
                    detail=f"{type(exc).__name__}: {exc}",
                )
            )
            gaps.append(step.name)
            continue
        outcomes.append(
            ParityStepOutcome(
                name=step.name,
                status="replayed",
                result=result,
            )
        )

    return ParityReplayReport(
        outcomes=tuple(outcomes),
        ok=not gaps,
        gaps=tuple(gaps),
    )


# ---- R1's tracker backfill as the first registered consumer (G.3) ---


# AC.SCS-G.3: R1's existing-workspace tracker backfill is registered
# THROUGH this mechanism — the parity registry is the structural home
# by which an existing workspace's tracker gets backfilled; the
# AC.SCS-R1.4 outcome-altitude run routes through G (not a one-off
# bypass). The update-path is a thin adapter onto R1's
# ``backfill_tracker_for_existing_workspace`` (sub-amendment 2), whose
# idempotency (query-then-skip, amendment-39 already_seeded precedent,
# no clobber) satisfies the AC.SCS-G.2 idempotent-replay contract.
TRACKER_BACKFILL_STEP_NAME = "tracker-backfill"


def _tracker_backfill_update_path(workspace_root: Path) -> Any:
    # Lazy import — keeps objective-tracker off the registry module's
    # import-time surface (mirrors tracker_seed / tracker_context's
    # lazy-import discipline; the registry itself is stdlib-only).
    from .tracker_seed import backfill_tracker_for_existing_workspace

    return backfill_tracker_for_existing_workspace(workspace_root)


def register_default_parity_steps() -> None:
    """Register the framework's built-in parity steps.

    Idempotent: re-registering an already-present step is a no-op
    (the workspace-update process may call this defensively before
    ``replay_parity_steps`` without a collision). Currently the sole
    built-in is R1's tracker backfill (AC.SCS-G.3)."""
    if TRACKER_BACKFILL_STEP_NAME not in _REGISTRY:
        register_parity_step(
            ParityStep(
                name=TRACKER_BACKFILL_STEP_NAME,
                update_path=_tracker_backfill_update_path,
                description=(
                    "Backfill the objective-tracker for an existing "
                    "workspace (session-`/clear`-safety R1; closes the "
                    "fresh-clone-only seeding hole)."
                ),
            )
        )


# Register the built-in parity step at import time so the
# workspace-update process discovers it without an explicit
# registration call (AC.SCS-G.3 — R1 backfill is reachable via the G
# registry's discovery+replay path, not a one-off bypass).
register_default_parity_steps()
