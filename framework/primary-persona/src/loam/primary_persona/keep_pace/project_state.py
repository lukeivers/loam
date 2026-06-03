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

"""Slice D — inject the per-project ground-truth STATE record into the
keep-pace turn-start lens.

The accuracy fix. Slice C built the per-project STATE derivation
(:mod:`loam_cli.audit.registry` — ``derive_project_state`` over a
``PROJECT_REGISTRY`` of loam + cairn, each keyed to its REAL ground-truth
markers). That derivation reached only a CLI verb + a release gate — never
the lens the persona reads each turn. This module CONSUMES that derivation
and surfaces a CONCISE, accurate, ground-truth-derived per-project status
into the turn-start context, so the persona's session-start context carries
the REAL build/sealed/merged status (e.g. Cairn's verify/ledger/execute =
BUILT) instead of stale written prose.

It does NOT re-derive anything: the git/disk probes live in Slice C. This
module adds only (a) a concise renderer, (b) a short-TTL in-process cache so
the per-turn cost is zero in steady state (no git I/O within the TTL window),
and (c) the keep-pace turn contributor + its registration.

PERF + CONCISENESS GUARDS (load-bearing — the whole point of the overhaul is
LESS junk + MORE accuracy in the turn-start context):

  * The block is SHORT — one line per project, modules grouped by liveness
    class (``Cairn: verify, ledger, execute, pilot, cause = built (merged)``),
    hard-capped at :data:`_STATE_BLOCK_CHAR_CAP`. NOT a per-module evidence
    dump. The removed junk is not traded for a new wall of status text.
  * Deriving STATE runs git probes; they are cached with a short TTL
    (:data:`_STATE_TTL_SECONDS`) so a turn within the window is a dict lookup,
    not a git probe. The cache is in-process + expiring (never persisted — no
    drift surface).
  * FAIL-SOFT throughout: any probe error for a project OMITS that project
    (never a hang, never a partial/wrong status); an all-fail / registry-error
    / ``loam_cli``-absent path returns ``""`` (no block). A status surface that
    is slow or wrong is worse than absent.

Stdlib-only. The ``loam_cli`` dependency is imported LAZILY inside the
derivation call (mirroring ``work_visibility.py``'s ``loam_cli`` import) so an
absent ``loam_cli`` degrades to no block rather than an import-time failure.
"""

from __future__ import annotations

import time
from typing import Any, Callable, Optional

# Short TTL for the derived-state cache. A turn fires every prompt; within the
# TTL the contributor reuses the cached record (zero git I/O). 60 s bounds
# staleness to a single working burst; a fresh session re-derives cold.
_STATE_TTL_SECONDS = 60.0

# Hard ceiling on the rendered block. The block is one short line per project;
# this cap is the explicit "do not trade removed junk for a wall of text" guard.
_STATE_BLOCK_CHAR_CAP = 600

# In-process TTL cache: project name -> (monotonic timestamp, derived record).
# A ``None`` record is NOT cached (a probe failure re-tries next turn).
_STATE_CACHE: dict[str, tuple[float, Any]] = {}

# Human-readable liveness phrasing for the concise line. Keys are the
# ``Liveness.value`` strings the STATE engine emits. An unrecognized class
# falls back to the raw value (fail-soft — never a KeyError).
_LIVENESS_PHRASE = {
    "merged": "built (merged)",
    "sealed": "built (sealed, not yet merged)",
    "built": "built",
    "wired": "wired",
    "unbuilt": "not built",
    "dark": "dark",
    "unknown": "status unknown",
}

# Order the liveness groups so the BUILT classes lead each project line (the
# load-bearing signal: what is done). An unlisted class sorts last.
_LIVENESS_ORDER = [
    "merged",
    "sealed",
    "built",
    "wired",
    "unknown",
    "dark",
    "unbuilt",
]


def _derive_cached(
    name: str,
    *,
    now: Optional[float] = None,
) -> Any:
    """Derive a registered project's STATE record, TTL-cached, fail-soft.

    Returns the freshly-derived (or cached-within-TTL)
    :class:`loam_cli.audit.record.StateOfLoam`, or ``None`` when the name is
    unregistered OR any derivation error occurs (a missing ``loam_cli``, a git
    probe failure). A ``None`` is never cached — a transient probe failure is
    re-tried on the next turn. The ``loam_cli`` import is lazy + inside the try
    so an absent ``loam_cli`` degrades to ``None`` (no block), never an
    import-time crash (mirrors ``work_visibility.py``).
    """
    ts = time.monotonic() if now is None else now
    cached = _STATE_CACHE.get(name)
    if cached is not None and (ts - cached[0]) < _STATE_TTL_SECONDS:
        return cached[1]
    try:
        from loam_cli.audit.registry import derive_project_state  # noqa: WPS433

        record = derive_project_state(name)
    except Exception:  # noqa: BLE001 — fail-soft; project omitted, never a hang
        return None
    if record is None:
        return None
    _STATE_CACHE[name] = (ts, record)
    return record


def _project_line(display_name: str, record: Any) -> str:
    """One concise status line for a project: modules grouped by liveness.

    ``Cairn: verify, ledger, execute, pilot, cause = built (merged)`` — at most
    a few liveness groups, comma-joined module names. Returns ``""`` when the
    record carries no rows (nothing to surface). Fail-soft on a malformed row.
    """
    groups: dict[str, list[str]] = {}
    try:
        rows = list(getattr(record, "components", ()) or ())
    except Exception:  # noqa: BLE001 — fail-soft; treat as no rows
        rows = []
    for row in rows:
        try:
            cls = str(getattr(getattr(row, "liveness", None), "value", "") or "")
            comp = str(getattr(row, "name", "") or "")
        except Exception:  # noqa: BLE001 — fail-soft; skip the malformed row
            continue
        if not cls or not comp:
            continue
        groups.setdefault(cls, []).append(comp)
    if not groups:
        return ""

    def _order(cls: str) -> int:
        return _LIVENESS_ORDER.index(cls) if cls in _LIVENESS_ORDER else len(
            _LIVENESS_ORDER
        )

    parts: list[str] = []
    for cls in sorted(groups, key=_order):
        phrase = _LIVENESS_PHRASE.get(cls, cls)
        mods = ", ".join(groups[cls])
        parts.append(f"{mods} = {phrase}")
    head = str(getattr(record, "head_sha", "") or "")
    head_tag = f" (@ {head[:9]})" if head and head != "UNKNOWN" else ""
    return f"  - {display_name}{head_tag}: " + "; ".join(parts)


def render_project_state_block(
    *,
    names: Optional[tuple[str, ...]] = None,
    now: Optional[float] = None,
    derive: Optional[Callable[..., Any]] = None,
) -> str:
    """Render the CONCISE, accurate, ground-truth-derived STATE block
    (the production entry point — no pre-arranged state).

    Derives each registered project's STATE (TTL-cached) and renders one short
    line per project, modules grouped by liveness class. Returns ``""`` when no
    project resolves (registry empty, ``loam_cli`` absent, or every derivation
    failed) — never a hang, never a partial/wrong status.

    AC-FBM-STATE-LIVE-4 (outcome-altitude): run with no fixtures against the
    live loam + cairn repos, the block names BOTH projects and shows Cairn's
    verify/ledger/execute as BUILT — so the persona cannot, from this context,
    claim they "remain to be built".

    *names* overrides the registered project set (tests scope it). *derive*
    overrides the per-project derivation (tests inject a raising / fixture
    derivation); production uses the TTL-cached registry derivation. *now*
    pins the cache clock (tests).
    """
    derive_fn = derive if derive is not None else (
        lambda n: _derive_cached(n, now=now)
    )
    try:
        if names is not None:
            project_names: tuple[str, ...] = names
        else:
            from loam_cli.audit.registry import (  # noqa: WPS433
                registered_project_names,
            )

            project_names = registered_project_names()
    except Exception:  # noqa: BLE001 — fail-soft; no registry => no block
        return ""

    lines: list[str] = []
    for name in project_names:
        try:
            record = derive_fn(name)
        except Exception:  # noqa: BLE001 — fail-soft; OMIT this project
            continue
        if record is None:
            continue
        line = _project_line(name.capitalize(), record)
        if line:
            lines.append(line)

    if not lines:
        return ""
    block = (
        "[project-state] Current ground-truth build status (derived live, "
        "not from prose):\n" + "\n".join(lines)
    )
    if len(block) > _STATE_BLOCK_CHAR_CAP:
        block = block[:_STATE_BLOCK_CHAR_CAP].rstrip()
    return block


def build_project_state_contributor(
    *,
    names: Optional[tuple[str, ...]] = None,
) -> Callable[[dict], str]:
    """Return the keep-pace turn contributor (``fn(context: dict) -> str``).

    Surfaces the concise ground-truth STATE block on every turn. Fail-soft: any
    boundary error yields ``""`` (no block) so the composer's turn proceeds
    (the AC46.2 graceful-empty contract the sibling contributors honour).
    """

    def contributor(context: dict) -> str:  # noqa: ARG001 — context unused (status is repo-global)
        try:
            return render_project_state_block(names=names)
        except Exception:  # noqa: BLE001 — fail-soft; turn proceeds
            return ""

    return contributor


def register_project_state_contributor(
    composer: object,
    *,
    name: str = "project-state",
    names: Optional[tuple[str, ...]] = None,
) -> Callable[[dict], str]:
    """Register the ground-truth STATE turn contributor on a
    ``ComposedContextPayload`` at ``TriggerKind.turn`` (AC-FBM-STATE-LENS-1).

    Registers ALONGSIDE the gated ``memory-retrieval`` contributor in the live
    composer's production branch — a SEPARATE named block so a STATE-probe
    failure cannot suppress the memory-retrieval block (and vice versa). The
    contributor returns a ``str`` always (``""`` on no content) so
    ``_serialise_turn``'s ``text.strip()`` is safe.
    """
    from ..context_composer import TriggerKind  # noqa: WPS433

    fn = build_project_state_contributor(names=names)
    composer.register(name=name, trigger_kind=TriggerKind.turn, fn=fn)
    return fn
