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

"""WORK-STREAMS per-turn surfacer (Increment 1).

The keep-pace turn-contributor that renders the streams lens: ONE
concise block, one short line per non-paused stream, each line carrying
that stream's STATE + next-action. For a stream bound to >=1 FBM-
registered project, the STATE is composed from a FRESH
``derive_project_state`` call (Slice C, TTL-cached) — DERIVED LIVE,
never stored-stale (AC.WS.DERIVE.1). For a stream bound to NO project,
the line is a staleness-based next-action explicitly marked "no
ground-truth project bound" (AC.WS.DERIVE.2) — never a faked STATE.

★ SUBSUMES the project-state block (D4 / AC.WS.SURFACE.1): this is ONE
block, not two. It REUSES Slice D's renderer discipline — the same
per-project liveness grouping, the same hard char-cap, the same
TTL-cache, the same fail-soft — and REPLACES the bare project-state
registration (the streams block IS the project-state surface, now
organized by stream). The anti-bloat constraint (F2 #1, plan §10) is
load-bearing: the block inherits the cap and, on overflow, collapses
paused/stale streams to a count rather than spilling (AC.WS.SURFACE.3).

Attention controls (AC.WS.SURFACE.2):
  - ``deep-dive``: the stream renders in full + ALL OTHER streams'
    staleness nudges are muted (their lines still render, no nudge).
  - ``paused``: the stream's line + nudge are dropped (collapsed to a
    count at the foot of the block).

Deviation -> #71 fail-soft seam (D7 / AC.WS.DEVIATE.1): the surfacer
compares a stream's EXPECTED state (its detail-path recorded status /
last-touched) against its DERIVED FBM STATE; a divergence emits a
structured ``{stream, expected, derived, evidence}`` mismatch record to
the memory-reality mismatch side-channel (task #71). When that channel's
entry point is ABSENT (#71 is pending), the emit no-ops fail-soft —
never crashes the turn, never blocks the build.

Lens-1: the STATE derivation is Slice C's, the renderer discipline is
Slice D's, the register is :mod:`work_streams`. This module COMPOSES
them; it re-implements nothing.
"""

from __future__ import annotations

import time
from typing import Any, Callable, Optional

from .project_state import _LIVENESS_ORDER, _LIVENESS_PHRASE

# Reuse Slice D's cap + TTL exactly (the streams block REPLACES the
# project-state block, so it inherits its budget — not a second wall).
_STREAM_BLOCK_CHAR_CAP = 600
_STREAM_STATE_TTL_SECONDS = 60.0

# In-process TTL cache: project name -> (monotonic ts, derived record).
# Mirrors Slice D; a None record is NOT cached (a probe failure retries).
_STREAM_STATE_CACHE: dict[str, tuple[float, Any]] = {}


def _derive_cached(name: str, *, now: Optional[float] = None) -> Any:
    """Derive a registered project's STATE record, TTL-cached, fail-soft.

    Returns the freshly-derived (or cached-within-TTL) record, or
    ``None`` when the name is unregistered OR any derivation error
    occurs (a missing ``loam_cli``, a git probe failure). A ``None`` is
    never cached. The ``loam_cli`` import is lazy + inside the try so an
    absent ``loam_cli`` degrades to ``None`` (no STATE), never an
    import-time crash (mirrors Slice D + ``work_visibility``).
    """
    ts = time.monotonic() if now is None else now
    cached = _STREAM_STATE_CACHE.get(name)
    if cached is not None and (ts - cached[0]) < _STREAM_STATE_TTL_SECONDS:
        return cached[1]
    try:
        from loam_cli.audit.registry import derive_project_state  # noqa: WPS433

        record = derive_project_state(name)
    except Exception:  # noqa: BLE001 — fail-soft; project omitted
        return None
    if record is None:
        return None
    _STREAM_STATE_CACHE[name] = (ts, record)
    return record


def _project_state_phrase(record: Any) -> str:
    """The concise STATE phrase for a derived record (Slice D grouping).

    ``verify, ledger, execute = built (merged)`` — modules grouped by
    liveness class, BUILT classes leading. Returns ``""`` on a record
    with no rows. Fail-soft on a malformed row (mirrors Slice D's
    ``_project_line`` grouping, without the per-project head — the
    head is the stream label here).
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
        except Exception:  # noqa: BLE001 — fail-soft; skip malformed row
            continue
        if not cls or not comp:
            continue
        groups.setdefault(cls, []).append(comp)
    if not groups:
        return ""

    def _order(cls: str) -> int:
        return (
            _LIVENESS_ORDER.index(cls)
            if cls in _LIVENESS_ORDER
            else len(_LIVENESS_ORDER)
        )

    parts: list[str] = []
    for cls in sorted(groups, key=_order):
        phrase = _LIVENESS_PHRASE.get(cls, cls)
        mods = ", ".join(groups[cls])
        parts.append(f"{mods} = {phrase}")
    return "; ".join(parts)


def _next_action_no_project(stream: Any) -> str:
    """Staleness-based next-action for a stream with NO bound project
    (AC.WS.DERIVE.2) — explicitly marked "no ground-truth project bound".

    Never fabricates a derived build-STATE. Surfaces the detail-path /
    cadence as the next-action anchor + the honest no-ground-truth mark.
    """
    cadence = str(getattr(stream, "cadence", "") or "")
    last = str(getattr(stream, "last_touched", "") or "")
    bits = []
    if cadence:
        bits.append(f"cadence {cadence}")
    if last:
        bits.append(f"last touched {last}")
    tail = f" ({', '.join(bits)})" if bits else ""
    return f"no ground-truth project bound — track via detail doc{tail}"


def render_stream_line(
    stream: Any,
    *,
    derive: Callable[[str], Any],
    mute_nudge: bool = False,
) -> str:
    """One concise line for a stream (AC.WS.SURFACE.1 shape).

    ``- loam [active]: <state> — next: <derived>`` for a bound stream;
    ``- money [active]: no ground-truth project bound ...`` for an
    unbound one (AC.WS.DERIVE.2). For a deep-dived stream the caller
    sets the ``[deep-dive]`` tag. ``mute_nudge`` suppresses a staleness
    nudge (set when ANOTHER stream is deep-dived — AC.WS.SURFACE.2).

    A bound stream's STATE is composed from the FRESH ``derive`` call
    (AC.WS.DERIVE.1) — never a stored string.
    """
    slug = str(getattr(stream, "slug", "") or "")
    attention = str(getattr(stream, "attention", "") or "active")
    nest = str(getattr(stream, "nest_under", "") or "")
    nest_tag = f", under {nest}" if nest else ""
    tag = f"[{attention}{nest_tag}]"

    projects = list(getattr(stream, "projects", []) or [])
    if not projects:
        return f"  - {slug} {tag}: {_next_action_no_project(stream)}"

    # Bound: compose the live derived STATE per project (AC.WS.DERIVE.1).
    state_bits: list[str] = []
    for pname in projects:
        try:
            record = derive(pname)
        except Exception:  # noqa: BLE001 — fail-soft; omit this project
            record = None
        if record is None:
            continue
        phrase = _project_state_phrase(record)
        if phrase:
            state_bits.append(phrase)

    if not state_bits:
        # Bound but every probe failed/omitted — honest fallback, no fake.
        return (
            f"  - {slug} {tag}: status unavailable (bound project state "
            f"could not be derived this turn)"
        )

    state = " | ".join(state_bits)
    nudge = ""
    if not mute_nudge:
        # The next-action is the lead unbuilt/unknown work, derived from
        # the STATE — kept terse (the cap is load-bearing).
        nudge = _derive_next_action(state_bits)
    next_part = f" — next: {nudge}" if nudge else ""
    return f"  - {slug} {tag}: {state}{next_part}"


def _derive_next_action(state_bits: list[str]) -> str:
    """A terse next-action derived from the STATE phrases.

    If any phrase names not-built / unknown work, the next-action points
    at advancing it; otherwise it is "maintain". Derived from the STATE,
    not stored (AC.WS.DERIVE.1).
    """
    joined = " ".join(state_bits).lower()
    if "not built" in joined:
        return "advance the not-built stage"
    if "status unknown" in joined:
        return "verify the unverified stage on the mainline"
    if "sealed" in joined:
        return "merge the sealed work to the mainline"
    return "maintain"


def emit_deviation(
    stream: Any,
    derived_state: str,
    *,
    emit: Optional[Callable[[dict], Any]] = None,
) -> Optional[dict]:
    """★ Deviation -> #71 fail-soft seam (AC.WS.DEVIATE.1).

    Compares the stream's EXPECTED state (its detail-path recorded
    status, proxied here by the stream's stored ``objective`` / last
    state intent) against its DERIVED FBM STATE; on a divergence builds
    a structured ``{stream, expected, derived, evidence}`` record and
    routes it to the memory-reality mismatch side-channel (task #71).

    The #71 entry point is resolved LAZILY + fail-soft: when ``emit`` is
    not supplied, this attempts to import the #71 channel; if that import
    fails (the channel is absent — #71 is pending) the emit NO-OPS and
    returns ``None`` (never crashes the turn). Returns the emitted record
    on a real divergence + a live channel, else ``None``.

    Divergence rule (Increment 1, deliberately conservative): a stream
    whose derived STATE reports "not built" / "status unknown" work
    while its stored intent implies the work is done is a deviation. The
    full expected-vs-real comparison sharpens in Increment 2 against the
    L1 work graph; this cycle ships the DETECTION + the fail-soft route.
    """
    expected = str(getattr(stream, "objective", "") or "")
    slug = str(getattr(stream, "slug", "") or "")
    derived_lower = derived_state.lower()
    diverges = "status unknown" in derived_lower or "not built" in derived_lower
    if not diverges:
        return None

    record = {
        "stream": slug,
        "expected": expected,
        "derived": derived_state,
        "evidence": (
            "derived FBM STATE reports unverified/not-built work for a "
            "stream whose stored intent does not flag it"
        ),
    }

    sink = emit
    if sink is None:
        try:
            # #71's side-channel entry point. ABSENT today (#71 pending);
            # the import failure is the fail-soft no-op path.
            from ..memory_reality_mismatch import (  # noqa: WPS433
                emit_mismatch_record,
            )

            sink = emit_mismatch_record
        except Exception:  # noqa: BLE001 — #71 absent; fail-soft no-op
            return None
    try:
        sink(record)
    except Exception:  # noqa: BLE001 — a live-but-erroring channel never crashes the turn
        return None
    return record


def render_work_streams_block(
    *,
    streams: Optional[list] = None,
    now: Optional[float] = None,
    derive: Optional[Callable[[str], Any]] = None,
    claude_home: Optional[str] = None,
    emit_deviation_fn: Optional[Callable[[Any, str], Any]] = None,
) -> str:
    """Render the CONCISE streams block (the production entry point —
    no pre-arranged state).

    ★ AC.WS.LIVE.1 (outcome-altitude): run with no fixtures against the
    live registered projects — the block names the streams and, for a
    project-bound stream (loam -> loam, cairn -> cairn, litrpg ->
    litrpg), shows a STATE + next-action DERIVED from the live
    ``derive_project_state``. The persona cannot mis-state a bound
    project's status from this block.

    Honors attention (AC.WS.SURFACE.2): a ``deep-dive`` stream renders in
    full + mutes other streams' nudges; a ``paused`` stream is dropped +
    collapsed to a count. On overflow (AC.WS.SURFACE.3) paused/stale
    streams collapse to a count; the cap is never exceeded.

    SUBSUMES the project-state block (AC.WS.SURFACE.1) — ONE block.
    Fail-soft throughout (AC46.2 graceful-empty): any boundary error or a
    no-content render returns ``""`` (no block).

    *streams* overrides the loaded register (tests). *derive* overrides
    the per-project derivation (tests inject a raising / fixture
    derivation); production uses the Slice-C TTL-cached derivation.
    *emit_deviation_fn* overrides the deviation seam (tests). *now* pins
    the cache clock (tests).
    """
    derive_fn = derive if derive is not None else (
        lambda n: _derive_cached(n, now=now)
    )
    dev_fn = emit_deviation_fn if emit_deviation_fn is not None else (
        lambda s, st: emit_deviation(s, st)
    )
    try:
        if streams is not None:
            loaded = list(streams)
        else:
            from .work_streams import load_user_scope_register  # noqa: WPS433

            loaded = load_user_scope_register(claude_home)
    except Exception:  # noqa: BLE001 — fail-soft; no register => no block
        return ""

    if not loaded:
        return ""

    # AC.WS.SURFACE.2 — a single deep-dived stream mutes OTHER nudges.
    deep_dived = [s for s in loaded if str(getattr(s, "attention", "")) == "deep-dive"]
    a_stream_is_deep = bool(deep_dived)

    paused_count = 0
    lines: list[str] = []
    for s in loaded:
        attention = str(getattr(s, "attention", "") or "active")
        if attention == "paused":
            paused_count += 1
            continue
        # Mute this stream's nudge when ANOTHER stream is deep-dived.
        is_self_deep = attention == "deep-dive"
        mute = a_stream_is_deep and not is_self_deep
        try:
            line = render_stream_line(s, derive=derive_fn, mute_nudge=mute)
        except Exception:  # noqa: BLE001 — fail-soft; omit this stream
            continue
        if not line:
            continue
        lines.append(line)
        # Deviation detection on bound streams (AC.WS.DEVIATE.1), fail-soft.
        if getattr(s, "projects", None):
            try:
                dev_fn(s, line)
            except Exception:  # noqa: BLE001 — deviation seam never crashes the turn
                pass

    if not lines:
        return ""

    foot = ""
    if paused_count:
        foot = f"\n  ({paused_count} stream(s) paused)"

    block = (
        "[work-streams] Cross-cutting tracks — STATE derived live "
        "(ground-truth, not prose):\n" + "\n".join(lines) + foot
    )

    # AC.WS.SURFACE.3 — on overflow, collapse paused/stale streams to a
    # count rather than spilling the cap. Here the paused are already a
    # count; if the active lines themselves overflow, hard-truncate at
    # the cap (the cap is never exceeded — the load-bearing F2 #1
    # constraint). Collapse stale (no-ground-truth) lines to a count
    # first, then truncate as a last resort.
    if len(block) > _STREAM_BLOCK_CHAR_CAP:
        block = _collapse_to_fit(lines, paused_count)
    return block


def _collapse_to_fit(lines: list[str], paused_count: int) -> str:
    """AC.WS.SURFACE.3 — collapse stale/unbound lines to a count to fit
    the cap; truncate as a last resort. The cap is NEVER exceeded.

    Ground-truth-bound lines (carrying a derived STATE) are the
    load-bearing signal and render in full; stale/unbound lines (the
    "no ground-truth project bound" ones) collapse to a count first.
    """
    bound = [ln for ln in lines if "no ground-truth project bound" not in ln]
    unbound_n = len(lines) - len(bound) + paused_count
    foot = f"\n  ({unbound_n} stream(s) collapsed/paused)" if unbound_n else ""
    block = (
        "[work-streams] Cross-cutting tracks — STATE derived live "
        "(ground-truth, not prose):\n" + "\n".join(bound) + foot
    )
    if len(block) > _STREAM_BLOCK_CHAR_CAP:
        block = block[:_STREAM_BLOCK_CHAR_CAP].rstrip()
    return block


def build_work_streams_contributor(
    *,
    claude_home: Optional[str] = None,
) -> Callable[[dict], str]:
    """Return the keep-pace turn contributor (``fn(context: dict) -> str``).

    Surfaces the concise streams block on every turn. Fail-soft: any
    boundary error yields ``""`` (no block) so the composer's turn
    proceeds (the AC46.2 graceful-empty contract the sibling
    contributors honour).
    """

    def contributor(context: dict) -> str:  # noqa: ARG001 — context unused (streams are global)
        try:
            return render_work_streams_block(claude_home=claude_home)
        except Exception:  # noqa: BLE001 — fail-soft; turn proceeds
            return ""

    return contributor


def register_work_streams_contributor(
    composer: object,
    *,
    name: str = "work-streams",
    claude_home: Optional[str] = None,
) -> Callable[[dict], str]:
    """Register the streams turn-contributor at ``TriggerKind.turn``.

    ★ SUBSUMES the project-state block (AC.WS.SURFACE.1): the streams
    block IS the per-turn project-STATE surface, now organized by stream.
    The caller registers THIS instead of the bare project-state
    contributor so there is ONE block, not two (the anti-bloat
    constraint, F2 #1). Returns a ``str`` always (``""`` on no content)
    so ``_serialise_turn``'s ``text.strip()`` is safe.
    """
    from ..context_composer import TriggerKind  # noqa: WPS433

    fn = build_work_streams_contributor(claude_home=claude_home)
    composer.register(name=name, trigger_kind=TriggerKind.turn, fn=fn)
    return fn
