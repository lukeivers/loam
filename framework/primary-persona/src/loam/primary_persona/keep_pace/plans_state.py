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

"""Plan-state surfacing + query (FBM correctness cycle, Slice 1 —
AC.PSI.2 + AC.PSI.3).

The Slice-D discipline verbatim (``project_state.py`` is the
precedent): this module CONSUMES the loam-cli plan-state derivation
(:mod:`loam_cli.audit.plan_state` — fresh-from-git, never prose) and
adds only

  (a) a concise renderer for the turn-start lens — ONE plans block,
      in-flight plans + their REAL build-state, one short line each,
      TTL-cached, hard-capped, fail-soft (AC.PSI.2);
  (b) the keep-pace turn contributor + its registration;
  (c) the production QUERY entry point — "what stored plan/decision
      state exists matching this topic?" — whose empty result is
      explicitly scoped (what was searched / what was not), never a
      bare "nothing exists" (AC.PSI.3, the dated-scoped-negative form
      from the reconciliation memory). This is the surface the
      AC.CLG.* claim guard consumes.

It does NOT re-derive anything: the git/disk probes live in loam-cli
(the Slice-C/D "consumer, never a re-deriver" discipline). The
``loam_cli`` import is LAZY inside the derivation call so an absent
``loam_cli`` degrades to no block / a scoped-unavailable query result,
never an import-time failure.
"""

from __future__ import annotations

import re
import time
from typing import Any, Callable, Optional

# Short TTL for the derived plan-state cache (mirrors Slice D's
# ``_STATE_TTL_SECONDS``): within the window a turn (or a claim-guard
# query burst) is a dict lookup, not a git probe.
_PLANS_TTL_SECONDS = 60.0

# Hard ceiling on the rendered plans block (AC.PSI.2 — ambient
# plan-state without context re-bloat; the Slice-D anti-bloat cap).
_PLANS_BLOCK_CHAR_CAP = 600

# In-process TTL cache: (monotonic timestamp, derived mapping). A
# ``None`` result is never cached (a transient failure re-tries).
_PLANS_CACHE: list[tuple[float, dict[str, tuple[Any, ...]]]] = []

# Topic tokens shorter than this carry no identity signal.
_MIN_TOKEN_LEN = 3

# Generic work-vocabulary tokens that match every plan and would
# spuriously resolve any topic (AC.PSI.3 match precision — the same
# precision the AC.CLG.3 no-alarm-fatigue contract leans on).
_GENERIC_TOKENS = frozenset(
    {
        "the", "and", "for", "not", "was", "were", "with", "that",
        "this", "have", "has", "had", "been", "are", "is", "its",
        "plan", "plans", "planned", "planning", "build", "built",
        "builds", "building", "work", "item", "cycle", "doc", "docs",
        "loam", "amendment", "slice", "feature",
    }
)

_TOKEN_RE = re.compile(r"[A-Za-z0-9]+")

# The honest coverage statement (AC.PSI.3 + plan §7 / §10 #4): the
# index covers governed plan-docs + git evidence; these named surfaces
# are NOT searched, and the scoped-negative result says so.
_UNSEARCHED_SURFACES: tuple[str, ...] = (
    "scratch/research artefacts (.scratch/claude-output)",
    "chat/session history",
    "external trackers",
)


def _tokens(text: str) -> frozenset[str]:
    """Identity tokens: lowercased alnum runs, length-floored, minus
    the generic work vocabulary."""
    return frozenset(
        t.lower()
        for t in _TOKEN_RE.findall(text or "")
        if len(t) >= _MIN_TOKEN_LEN and t.lower() not in _GENERIC_TOKENS
    )


def _derive_all_cached(
    *, now: Optional[float] = None
) -> Optional[dict[str, tuple[Any, ...]]]:
    """Derive every registered project's plan-states, TTL-cached,
    fail-soft (AC.PSI.2 — a derivation failure yields ``None``, never
    a wedge or a wrong state). Lazy ``loam_cli`` import mirrors
    ``project_state._derive_cached``.
    """
    ts = time.monotonic() if now is None else now
    if _PLANS_CACHE and (ts - _PLANS_CACHE[0][0]) < _PLANS_TTL_SECONDS:
        return _PLANS_CACHE[0][1]
    try:
        from loam_cli.audit.plan_state import (  # noqa: WPS433
            derive_all_plan_states,
        )

        derived = derive_all_plan_states()
    except Exception:  # noqa: BLE001 — fail-soft; no block / scoped-unavailable
        return None
    _PLANS_CACHE.clear()
    _PLANS_CACHE.append((ts, derived))
    return derived


def _plan_line(plan: Any) -> str:
    """One concise in-flight line: title + real build-state phrase.

    Plain language; the evidence count makes the state concrete
    without dumping SHAs into the lens.
    """
    title = str(getattr(plan, "title", "") or getattr(plan, "slug", ""))
    state = str(getattr(plan, "build_state", ""))
    evidence = tuple(getattr(plan, "seal_evidence", ()) or ())
    if state == "partially-sealed":
        n = len(evidence)
        phrase = f"partially built ({n} build/seal commit{'s' if n != 1 else ''})"
    else:
        phrase = "planned, no build evidence yet"
    return f"  - {title} — {phrase}"


def render_plans_block(
    *,
    now: Optional[float] = None,
    derive: Optional[Callable[[], Optional[dict[str, tuple[Any, ...]]]]] = None,
) -> str:
    """Render the ONE concise in-flight plans block (AC.PSI.2 — the
    production surfacing entry point, no pre-arranged state).

    In-flight = every plan whose derived state is NOT sealed —
    partially-built plans lead (the load-bearing signal: what is in
    flight and how real it is), pending plans follow. Derived live
    (TTL-cached), hard-capped at :data:`_PLANS_BLOCK_CHAR_CAP`,
    fail-soft: a derivation failure returns ``""`` (no block), never a
    wedge or a wrong state.

    *derive* overrides the derivation (tests inject fixtures /
    raisers); *now* pins the cache clock.
    """
    derive_fn = derive if derive is not None else (
        lambda: _derive_all_cached(now=now)
    )
    try:
        derived = derive_fn()
    except Exception:  # noqa: BLE001 — fail-soft; no block
        return ""
    if not derived:
        return ""
    partial: list[str] = []
    pending: list[str] = []
    try:
        for _project, plans in sorted(derived.items()):
            for plan in plans:
                state = str(getattr(plan, "build_state", ""))
                if state == "sealed":
                    continue
                line = _plan_line(plan)
                if state == "partially-sealed":
                    partial.append(line)
                else:
                    pending.append(line)
    except Exception:  # noqa: BLE001 — fail-soft; a wrong block is worse than none
        return ""
    lines = partial + pending
    if not lines:
        return ""
    block = (
        "[plan-state] In-flight plans + REAL build-state (derived live "
        "from git, never from plan prose):\n" + "\n".join(lines)
    )
    if len(block) > _PLANS_BLOCK_CHAR_CAP:
        block = block[:_PLANS_BLOCK_CHAR_CAP].rstrip()
    return block


def build_plans_contributor() -> Callable[[dict], str]:
    """The keep-pace turn contributor (``fn(context: dict) -> str``)
    for the plans block (AC.PSI.2). Fail-soft: any boundary error
    yields ``""`` so the composer's turn proceeds (the AC46.2
    graceful-empty contract the sibling contributors honour)."""

    def contributor(context: dict) -> str:  # noqa: ARG001 — plan-state is repo-global
        try:
            return render_plans_block()
        except Exception:  # noqa: BLE001 — fail-soft; turn proceeds
            return ""

    return contributor


def register_plans_contributor(
    composer: object,
    *,
    name: str = "plan-state",
) -> Callable[[dict], str]:
    """Register the plans-block turn contributor on a
    ``ComposedContextPayload`` at ``TriggerKind.turn`` (AC.PSI.2 —
    registered ADDITIVELY alongside the existing turn contributors; a
    plans-derivation failure cannot suppress any sibling block)."""
    from ..context_composer import TriggerKind  # noqa: WPS433

    fn = build_plans_contributor()
    composer.register(name=name, trigger_kind=TriggerKind.turn, fn=fn)
    return fn


def _match_overlap(
    topic_tokens: frozenset[str], plan: Any
) -> int:
    """Token overlap between a topic and one plan's identity
    (slug words + title words). The match gate requires >= 2
    overlapping tokens for a 3+-token topic, >= 1 for a short (1–2
    token) topic — the short-topic tokens already passed the generic-
    vocabulary filter, so a surviving token is distinctive (the
    2026-06-09 ask, "subagent migration", resolves on its one
    distinctive token). Precision-first for longer topics — the
    AC.CLG.3 no-false-steer budget."""
    identity = _tokens(
        str(getattr(plan, "slug", "")).replace("-", " ")
        + " "
        + str(getattr(plan, "title", ""))
    )
    return len(topic_tokens & identity)


def query_plan_state(
    topic: str,
    *,
    derive: Optional[Callable[[], Optional[dict[str, tuple[Any, ...]]]]] = None,
) -> dict[str, Any]:
    """The production query entry point (AC.PSI.3): what stored
    plan/decision state exists matching *topic*?

    Searches the derived index — plan-docs INCLUDING the sealed
    archive, each with its build-state + seal-commit evidence — and
    returns::

        {
          "matches":   [ {project, slug, title, build_state,
                          seal_evidence, in_sealed_archive}, ... ],
          "searched":  (<the surfaces actually searched>, ...),
          "unsearched": (<named surfaces NOT searched>, ...),
        }

    On no match the result is an EXPLICITLY-SCOPED empty — ``matches``
    empty, ``searched`` naming exactly what was covered — never a bare
    "nothing exists" (the no-eternal-negatives form from the
    reconciliation memory). When the derivation itself is unavailable,
    ``searched`` is EMPTY (claiming coverage that didn't happen would
    be the same lie one level up) and ``unsearched`` says the index
    was unavailable.

    *derive* is the test seam (mirrors :func:`render_plans_block`).
    """
    derive_fn = derive if derive is not None else _derive_all_cached
    try:
        derived = derive_fn()
    except Exception:  # noqa: BLE001 — degrade to scoped-unavailable
        derived = None
    if derived is None:
        return {
            "matches": [],
            "searched": (),
            "unsearched": _UNSEARCHED_SURFACES
            + ("plan-doc index (derivation unavailable this call)",),
        }

    topic_tokens = _tokens(topic)
    min_overlap = 2 if len(topic_tokens) >= 3 else 1
    scored: list[tuple[int, dict[str, Any]]] = []
    for _project, plans in sorted(derived.items()):
        for plan in plans:
            overlap = _match_overlap(topic_tokens, plan)
            if topic_tokens and overlap >= min_overlap:
                scored.append(
                    (
                        overlap,
                        {
                            "project": str(getattr(plan, "project", "")),
                            "slug": str(getattr(plan, "slug", "")),
                            "title": str(getattr(plan, "title", "")),
                            "build_state": str(
                                getattr(plan, "build_state", "")
                            ),
                            "seal_evidence": tuple(
                                getattr(plan, "seal_evidence", ()) or ()
                            ),
                            "in_sealed_archive": bool(
                                getattr(plan, "in_sealed_archive", False)
                            ),
                        },
                    )
                )
    scored.sort(key=lambda pair: (-pair[0], pair[1]["slug"]))
    searched = tuple(
        f"{project} plan-docs (docs/plans incl. sealed archive) + git "
        f"apply/seal commit subjects"
        for project in sorted(derived.keys())
    )
    return {
        "matches": [m for _o, m in scored],
        "searched": searched,
        "unsearched": _UNSEARCHED_SURFACES,
    }
