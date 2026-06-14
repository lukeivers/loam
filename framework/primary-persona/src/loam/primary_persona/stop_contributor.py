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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied. See the License for the specific language governing
# permissions and limitations under the License.

"""Stop-hook contributor framework (principle-foundation-structural-
enforcement, D-PFSE.3 — built fresh).

THE PROBLEM (plan §3.3 / RF-2). AC.PFSE.4 (permission-ask) + AC.PFSE.7
(terminology-drift) both want a "Stop-hook contributor" — a check that,
at turn-close, inspects the turn's OUTBOUND reply and surfaces an
advisory. The existing Stop emitter (`stop_emitter.cli_stop`) is
single-purpose (recover transcript -> detached memory-write) with NO
contributor registry; the Stop-hook contract requires exit-0-always +
fast-return. This module is the contributor framework: a registry of
Stop contributors, each given the turn's outbound reply + workspace
context, each returning an optional advisory line, composed into a
Stop-output payload WITHOUT breaking the exit-0-always / fail-soft
contract.

THE OUTPUT CONTRACT (confirmed against the Claude Code Stop-hook docs).
A Stop hook that wants to surface an advisory WITHOUT blocking the
turn-close emits a JSON object on stdout carrying ``systemMessage`` (a
user-visible warning) and/or ``hookSpecificOutput.additionalContext``
(a model-visible reminder). Both are non-blocking; the turn closes
normally. Empty stdout + exit 0 = no effect. This framework emits
``systemMessage`` only (the advisory is for the operator / the next
turn's attention), and NEVER ``decision: block`` (the contributors are
advisory, not gates — a turn-close is never blocked by a style note).

THE FRAMEWORK shape mirrors ``context_composer.Contributor`` for
consistency, but the trigger + input + output differ: input is the
turn's outbound reply text + workspace context; output is an optional
advisory string composed into a single Stop ``systemMessage``.

Stdlib + Protocol only; NO network/LLM call (the contributors are
deterministic regex / git-read). Fail-soft per contributor so one
broken contributor cannot break the Stop hook.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Protocol


@dataclass(frozen=True)
class StopAdvisory:
    """One contributor's advisory output.

    ``name`` is the contributor's registered name (for the audit/log
    surface). ``message`` is the advisory text composed into the Stop
    ``systemMessage``. A contributor that finds nothing returns None
    (NOT an empty StopAdvisory) so the composer can skip it.
    """

    name: str
    message: str


class StopContributor(Protocol):
    """A Stop-hook contributor.

    Given the turn's outbound reply text + a context dict (workspace
    root, session id, ...), returns a ``StopAdvisory`` when it has
    something to surface, or None when the turn is clean. Contributors
    MUST be deterministic + side-effect-light (no LLM, no network) —
    they run on the Stop hot path under the exit-0-fast contract.
    """

    def __call__(
        self, *, outbound_reply: str, context: dict[str, Any]
    ) -> StopAdvisory | None: ...


@dataclass(frozen=True)
class RegisteredStopContributor:
    """A Stop contributor bound to the registry with a name."""

    name: str
    fn: Callable[..., StopAdvisory | None]


class StopContributorRegistry:
    """Ordered registry of Stop contributors.

    Registration order is composition order. A duplicate name raises
    (a registry with two contributors of the same name is a wiring
    bug). The registry is the framework D-PFSE.3 names; the two
    contributors (permission-ask AC.PFSE.4, terminology-drift
    AC.PFSE.7) register against it.
    """

    def __init__(self) -> None:
        self._contributors: list[RegisteredStopContributor] = []

    def register(
        self,
        name: str,
        fn: Callable[..., StopAdvisory | None],
    ) -> None:
        if any(c.name == name for c in self._contributors):
            raise ValueError(
                f"Stop contributor {name!r} already registered "
                f"(duplicate name)"
            )
        self._contributors.append(
            RegisteredStopContributor(name=name, fn=fn)
        )

    def names(self) -> list[str]:
        return [c.name for c in self._contributors]

    def compose(
        self,
        *,
        outbound_reply: str,
        context: dict[str, Any],
    ) -> list[StopAdvisory]:
        """Run every registered contributor (in registration order) and
        collect their non-None advisories.

        FAIL-SOFT per contributor: a contributor that raises is skipped
        (its exception is swallowed) so one broken contributor cannot
        break the Stop hook's exit-0 contract. A contributor returning
        None is skipped silently.
        """
        out: list[StopAdvisory] = []
        for c in self._contributors:
            try:
                advisory = c.fn(
                    outbound_reply=outbound_reply, context=context
                )
            except Exception:  # noqa: BLE001 — fail-soft per contributor
                continue
            if advisory is not None:
                out.append(advisory)
        return out


def compose_stop_systemmessage(advisories: list[StopAdvisory]) -> str | None:
    """Compose a list of advisories into a single Stop ``systemMessage``
    string, or None when there are no advisories.

    The composed message names each contributor + its advisory so the
    operator sees which check fired. Returns None on the empty list so
    the caller emits empty stdout (no effect — the turn closes clean).
    """
    if not advisories:
        return None
    lines = ["loam turn-close advisories:"]
    for a in advisories:
        lines.append(f"  - [{a.name}] {a.message}")
    return "\n".join(lines)


def build_stop_output(
    advisories: list[StopAdvisory],
) -> dict[str, Any] | None:
    """Build the Stop-hook stdout JSON payload from advisories, or None.

    Emits ``systemMessage`` only (advisory, user-visible, non-blocking).
    NEVER emits ``decision: block`` — the contributors are advisory, not
    gates; a turn-close is never blocked by a style/consistency note.
    Returns None when there are no advisories (caller emits empty
    stdout).
    """
    message = compose_stop_systemmessage(advisories)
    if message is None:
        return None
    return {"systemMessage": message}


# ---------------------------------------------------------------------
# The production registry + the two contributors (AC.PFSE.4 + AC.PFSE.7).
# ---------------------------------------------------------------------


def build_default_registry() -> StopContributorRegistry:
    """Build the production Stop-contributor registry with the two
    shipped contributors registered in order: permission-ask
    (AC.PFSE.4) then terminology-drift (AC.PFSE.7).

    Imported lazily to keep the framework module import-light and to
    avoid a circular import (the contributors import this module for the
    StopAdvisory type).
    """
    from .stop_contributors_builtin import (
        permission_ask_contributor,
        terminology_drift_contributor,
    )

    registry = StopContributorRegistry()
    registry.register("permission-ask", permission_ask_contributor)
    registry.register(
        "terminology-drift", terminology_drift_contributor
    )
    return registry


def run_stop_contributors(
    *,
    outbound_reply: str,
    workspace_root: Path,
    session_id: str | None = None,
    registry: StopContributorRegistry | None = None,
) -> dict[str, Any] | None:
    """Production entry point: run the Stop contributors over one turn's
    outbound reply and return the Stop-output payload (or None).

    FAIL-SOFT end-to-end: any internal error returns None (no advisory,
    turn closes clean) — the exit-0-always contract is never at risk
    from a contributor or the composer. The caller (cli_stop) treats
    None as "emit empty stdout".
    """
    try:
        reg = registry if registry is not None else build_default_registry()
        context: dict[str, Any] = {
            "workspace_root": workspace_root,
            "session_id": session_id,
        }
        advisories = reg.compose(
            outbound_reply=outbound_reply, context=context
        )
        return build_stop_output(advisories)
    except Exception:  # noqa: BLE001 — fail-soft; never break exit-0
        return None
