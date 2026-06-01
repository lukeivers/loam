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

"""The PERSISTED POSITION CURSOR (AC.CURSOR.* — D2 / D5 / Fork D1).

A cursor is a small YAML record that names a DEFINITE position in a
flow: ``{flow, step, branch_state, updated_at}`` (plan §1 piece 2). It
is the "you are here" dot the map (the flow definition) is useless
without.

Design posture (the load-bearing F2 from plan §10 doubt 1): **staleness
is the real risk, not absence.** A cursor that confidently names a wrong
position is WORSE than no cursor, because it defeats the pause-check by
making the agent *think* it knows where it is. So the cursor is built to
say "I don't know where I am" (UNRESOLVED) more readily than a human
would — resolution against a flow definition is REQUIRED, and any
contradiction by ground truth (the named step no longer exists in the
flow) resolves UNRESOLVED, never a wrong-but-confident position.

ACs proven here (method = builder's call per ODD §1.1):

  - **AC.CURSOR.1** — a cursor names ``{flow, step, branch_state,
    updated_at}`` and ``resolve_cursor`` resolves it to a step that
    EXISTS in the flow's node graph; a cursor pointing at a
    non-existent step resolves UNRESOLVED.
  - **AC.CURSOR.2** — ``advance_cursor`` moves the cursor to a
    transition target; afterwards ``step`` is the new step, the prior
    step is no longer current, and ``updated_at`` has advanced.
  - **AC.CURSOR.3** — a STALE cursor (the flow definition changed out
    from under it so the named step vanished) resolves UNRESOLVED, not
    to a false position.
  - **AC.CURSOR.4** — the methodology-flow cursor home is a TRACKED
    (committable) path (``docs/flows/<flow>.cursor.yaml``); the
    user-state flow-instance cursor home is under gitignored ``.loam/``.
    (Guards the build-cursor.md silent-drop near-miss — D2.)

Single-active-flow, explicit-write, file-home (D5 / Fork D1): one cursor
names exactly one flow + one step; advancement is by an EXPLICIT call,
never inferred from runtime signals.

Stdlib + PyYAML only.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import yaml

from loam_cli.flows.format import FlowDefinition

# AC.CURSOR.4 (D2) — the two cursor homes. A methodology flow's cursor
# is build-methodology, not shipped user-state, so it MUST be
# committable; a user-facing flow INSTANCE is per-workspace user-state.
_METHODOLOGY_CURSOR_DIR = "docs/flows"  # tracked.
_USER_STATE_CURSOR_DIR = ".loam/flows"  # gitignored user-state.


@dataclass(frozen=True)
class Cursor:
    """A persisted position record: the "you are here" dot.

    ``branch_state`` carries the disposition / gate-status / any
    branch-specific qualifier the flow's prose needs (e.g. "disposition
    build-new, gate G3 pending"). ``updated_at`` is an ISO-8601 UTC
    timestamp.
    """

    flow: str
    step: str
    branch_state: str = ""
    updated_at: str = ""

    def to_yaml(self) -> str:
        return yaml.safe_dump(
            {
                "flow": self.flow,
                "step": self.step,
                "branch_state": self.branch_state,
                "updated_at": self.updated_at,
            },
            sort_keys=False,
            default_flow_style=False,
        )


@dataclass(frozen=True)
class CursorResolution:
    """The result of resolving a cursor against a flow definition.

    ``resolved`` is True ONLY when the cursor names a step that exists in
    the flow's node graph (positive resolution). ``reason`` names why a
    resolution failed (UNRESOLVED), so the pause-check can surface a
    corrective message rather than an opaque halt.
    """

    resolved: bool
    flow: str = ""
    step: str = ""
    step_name: str = ""
    branch_state: str = ""
    reason: str = ""

    def one_sentence(self) -> str:
        """The one-sentence position restatement the pause-check
        requires (plan D4): "step <name> of flow <flow>, branch
        <branch_state>". Empty string when UNRESOLVED."""
        if not self.resolved:
            return ""
        branch = self.branch_state or "(none)"
        return (
            f"step {self.step_name or self.step} of flow {self.flow}, "
            f"branch {branch}"
        )


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_cursor(path: Path, cursor: Cursor) -> Cursor:
    """Write ``cursor`` to ``path`` (stamping ``updated_at`` if absent).

    Returns the written Cursor (with the stamped timestamp). Creates
    parent directories. AC.CURSOR.1 — the on-disk record names a
    definite ``{flow, step, branch_state, updated_at}``.
    """
    stamped = cursor
    if not stamped.updated_at:
        stamped = Cursor(
            flow=cursor.flow,
            step=cursor.step,
            branch_state=cursor.branch_state,
            updated_at=_now_iso(),
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stamped.to_yaml(), encoding="utf-8")
    return stamped


def read_cursor(path: Path) -> Cursor | None:
    """Read a cursor from ``path``; return None when absent / empty /
    unparseable / missing the required ``flow`` + ``step`` fields.

    A missing-or-corrupt cursor returns None rather than a fabricated
    position — "no cursor" is an honest UNRESOLVED input to the
    pause-check, never a guessed position (plan §10 doubt 1).
    """
    try:
        if not path.exists():
            return None
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return None
    if not raw.strip():
        return None
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError:
        return None
    if not isinstance(data, dict):
        return None
    flow = data.get("flow")
    step = data.get("step")
    if not isinstance(flow, str) or not flow:
        return None
    if not isinstance(step, str) or not step:
        return None
    return Cursor(
        flow=flow,
        step=step,
        branch_state=str(data.get("branch_state") or ""),
        updated_at=str(data.get("updated_at") or ""),
    )


def resolve_cursor(
    cursor: Cursor | None,
    definition: FlowDefinition | None,
) -> CursorResolution:
    """Resolve a cursor against a flow definition (AC.CURSOR.1 / .3).

    Positive-resolution gate (plan D4): resolves to RESOLVED ONLY when

      - the cursor is present, AND
      - a flow definition is present, AND
      - the cursor's ``flow`` matches the definition's ``flow``, AND
      - the cursor's ``step`` EXISTS in the definition's node graph.

    Any other case — absent cursor, absent definition, flow-name
    mismatch, or a step that vanished from a mutated flow (AC.CURSOR.3
    staleness) — resolves UNRESOLVED with a naming ``reason``. The
    cursor never resolves to a wrong-but-confident position.
    """
    if cursor is None:
        return CursorResolution(
            resolved=False, reason="no cursor on disk (or unparseable)"
        )
    if definition is None:
        return CursorResolution(
            resolved=False,
            flow=cursor.flow,
            step=cursor.step,
            branch_state=cursor.branch_state,
            reason=(
                f"flow definition for '{cursor.flow}' could not be "
                "loaded; cannot confirm the cursor's position"
            ),
        )
    if cursor.flow != definition.flow:
        return CursorResolution(
            resolved=False,
            flow=cursor.flow,
            step=cursor.step,
            branch_state=cursor.branch_state,
            reason=(
                f"cursor names flow '{cursor.flow}' but the loaded "
                f"definition is flow '{definition.flow}'"
            ),
        )
    step = definition.get_step(cursor.step)
    if step is None:
        # AC.CURSOR.3 — the named step vanished from the flow (the flow
        # definition changed out from under it). Resolve UNRESOLVED,
        # NEVER a false position.
        return CursorResolution(
            resolved=False,
            flow=cursor.flow,
            step=cursor.step,
            branch_state=cursor.branch_state,
            reason=(
                f"cursor names step '{cursor.step}' which no longer "
                f"exists in flow '{definition.flow}' (stale cursor — "
                "the flow changed out from under it)"
            ),
        )
    return CursorResolution(
        resolved=True,
        flow=cursor.flow,
        step=step.id,
        step_name=step.name,
        branch_state=cursor.branch_state,
        reason="",
    )


def advance_cursor(
    path: Path,
    definition: FlowDefinition,
    target_step: str,
    branch_state: str | None = None,
) -> Cursor:
    """Advance the on-disk cursor to ``target_step`` (AC.CURSOR.2).

    Requires the current cursor to resolve against ``definition`` and
    ``target_step`` to be a declared transition target of the current
    step (an explicit, validated advance — no inferred jumps, D5 /
    plan §7 anti-auto-advance). Returns the new Cursor.

    Raises ValueError when the current cursor is unresolved or the
    requested transition is not declared — refusing to advance from an
    unknown position is the pause-by-default posture.
    """
    cursor = read_cursor(path)
    resolution = resolve_cursor(cursor, definition)
    if not resolution.resolved or cursor is None:
        raise ValueError(
            "cannot advance: current cursor is unresolved "
            f"({resolution.reason}). Re-establish position first "
            "(pause-if-lost)."
        )
    current = definition.get_step(cursor.step)
    assert current is not None  # resolved => current step exists.
    if target_step not in current.transitions:
        raise ValueError(
            f"cannot advance: '{target_step}' is not a declared "
            f"transition from step '{current.id}' "
            f"(declared: {list(current.transitions)})"
        )
    new_branch = (
        branch_state if branch_state is not None else cursor.branch_state
    )
    new_cursor = Cursor(
        flow=cursor.flow,
        step=target_step,
        branch_state=new_branch,
        updated_at=_now_iso(),
    )
    return write_cursor(path, new_cursor)


def methodology_cursor_path(repo_root: Path, flow: str) -> Path:
    """The TRACKED (committable) cursor home for a methodology flow
    (AC.CURSOR.4 / D2)."""
    return repo_root / _METHODOLOGY_CURSOR_DIR / f"{flow}.cursor.yaml"


def user_state_cursor_path(workspace_root: Path, flow: str) -> Path:
    """The gitignored ``.loam/`` cursor home for a user-facing flow
    INSTANCE (AC.CURSOR.4 / D2)."""
    return workspace_root / _USER_STATE_CURSOR_DIR / f"{flow}.cursor.yaml"
