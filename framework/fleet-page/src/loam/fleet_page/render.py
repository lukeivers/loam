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

"""The fleet page renderer (WS-A3).

``render_page(...)`` is a PURE function: injected, already-read source
data → one self-contained HTML string.  No I/O, no source reads — the
``generate`` layer does the reading and passes the results here, so the
same renderer serves fixtures (AC.PAGE.1), a degraded source
(AC.PAGE.3), and the real cron regeneration identically.

Four panels, in the §5 ordering (live feed LEADS):

1. **Live agents** — the alive runs from WS-A2's fleet JSON
   (status / liveness / elapsed / cost).            (AC.PAGE.1)
2. **Recent outcomes** — the finished (not-alive) runs from the same
   JSON (objective / stage / exit / cost).          (AC.PAGE.1)
3. **This week's cost (token proxy)** — ``cost_by_prompt`` token
   counts, labeled a proxy, never dollars.          (AC.PAGE.1)
4. **Needs a human** — the per-project-pm decision queue. (AC.PAGE.1)

A source that is UNAVAILABLE is passed as ``None`` and renders a
"source unavailable" label; a source that is EMPTY is passed as its
empty value (``{"runs": []}`` / ``[]``) and renders an explicit empty
state — the two are never conflated (AC.PAGE.3; §5 "must not imply zero
activity").  Every injected string is HTML-escaped.  Wide cells wrap and
each table scrolls inside its own container, so a long run path or
objective never forces horizontal body overflow (AC.PAGE.1).
"""

from __future__ import annotations

from html import escape
from typing import Any

# The sentinel for "this source could not be read" (uninstalled, store
# missing, reader raised).  Distinct from an empty-but-present source.
MISSING = None

_MISSING_LABEL = "source unavailable"


def _fmt_elapsed(seconds: float | None) -> str:
    """Human elapsed span; ``—`` when the record carried no timestamps."""
    if seconds is None:
        return "—"
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds}s"
    if seconds < 3600:
        return f"{seconds // 60}m {seconds % 60}s"
    return f"{seconds // 3600}h {(seconds % 3600) // 60}m"


def _fmt_age(seconds: float | None) -> str:
    """Artifact age for the liveness cell; ``—`` when unknown."""
    if seconds is None:
        return "—"
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds}s ago"
    if seconds < 3600:
        return f"{seconds // 60}m ago"
    return f"{seconds // 3600}h ago"


def _fmt_cost(run: dict) -> str:
    """Honest cost cell (D-A3-6): the real ``cost_usd`` when present,
    else the collector's ``cost_source`` string (e.g. ``absent``) — never
    a fabricated ``$0.00``."""
    cost = run.get("cost_usd")
    if isinstance(cost, (int, float)):
        return f"${cost:.2f}"
    source = run.get("cost_source")
    return escape(str(source)) if source else "—"


def _liveness_badge(alive: bool, age_s: float | None) -> str:
    if alive:
        return (f'<span class="badge live">live</span> '
                f'<span class="muted">{_fmt_age(age_s)}</span>')
    return (f'<span class="badge dead">stale</span> '
            f'<span class="muted">{_fmt_age(age_s)}</span>')


def _text(value: Any, empty: str = "—") -> str:
    if value is None:
        return empty
    s = str(value).strip()
    return escape(s) if s else empty


def _panel_missing(title: str) -> str:
    return (
        f'<section class="panel"><h2>{escape(title)}</h2>'
        f'<p class="unavailable">{_MISSING_LABEL} '
        f'<span class="muted">— panel omitted, not zero</span></p>'
        f'</section>'
    )


def _split_runs(fleet: dict) -> tuple[list[dict], list[dict]]:
    runs = fleet.get("runs") or []
    live = [r for r in runs if r.get("alive")]
    finished = [r for r in runs if not r.get("alive")]
    return live, finished


def _live_panel(fleet: dict | None) -> str:
    if fleet is MISSING:
        return _panel_missing("Live agents")
    live, _ = _split_runs(fleet)
    if not live:
        return (
            '<section class="panel"><h2>Live agents</h2>'
            '<p class="empty">No agents are running right now.</p>'
            '</section>'
        )
    rows = []
    for r in live:
        rows.append(
            "<tr>"
            f'<td class="wrap">{_text(r.get("workspace"))}'
            f'<div class="sub">{_text(r.get("objective"), "")}</div></td>'
            f"<td>{_text(r.get('stage'))}</td>"
            f"<td>{_liveness_badge(True, r.get('artifact_age_s'))}</td>"
            f"<td>{_fmt_elapsed(r.get('elapsed_s'))}</td>"
            f"<td>{_fmt_cost(r)}</td>"
            "</tr>"
        )
    return (
        '<section class="panel"><h2>Live agents '
        f'<span class="count">{len(live)}</span></h2>'
        '<div class="scroll"><table>'
        "<thead><tr><th>Workspace / objective</th><th>Status</th>"
        "<th>Liveness</th><th>Elapsed</th><th>Cost</th></tr></thead>"
        f'<tbody>{"".join(rows)}</tbody>'
        "</table></div></section>"
    )


def _outcomes_panel(fleet: dict | None) -> str:
    if fleet is MISSING:
        return _panel_missing("Recent outcomes")
    _, finished = _split_runs(fleet)
    if not finished:
        return (
            '<section class="panel"><h2>Recent outcomes</h2>'
            '<p class="empty">No finished runs on record.</p>'
            '</section>'
        )
    rows = []
    for r in finished:
        exit_status = r.get("exit_status")
        ok = exit_status == 0
        badge = (f'<span class="badge {"ok" if ok else "warn"}">'
                 f'{_text(exit_status, "?")}</span>')
        label = _text(r.get("objective")) if r.get("objective") \
            else _text(r.get("workspace"))
        rows.append(
            "<tr>"
            f'<td class="wrap">{label}</td>'
            f"<td>{_text(r.get('stage'))}</td>"
            f"<td>{badge}</td>"
            f"<td>{_fmt_cost(r)}</td>"
            "</tr>"
        )
    return (
        '<section class="panel"><h2>Recent outcomes '
        f'<span class="count">{len(finished)}</span></h2>'
        '<div class="scroll"><table>'
        "<thead><tr><th>Objective</th><th>Last stage</th>"
        "<th>Exit</th><th>Cost</th></tr></thead>"
        f'<tbody>{"".join(rows)}</tbody>'
        "</table></div></section>"
    )


def _cost_panel(cost_rows: list[dict] | None) -> str:
    if cost_rows is MISSING:
        return _panel_missing("This week's cost")
    if not cost_rows:
        return (
            "<section class=\"panel\"><h2>This week's cost "
            '<span class="proxy">token proxy</span></h2>'
            '<p class="empty">No recorded token cost this window.</p>'
            "</section>"
        )
    # Rank by total tokens desc (D-A3-4: proxy ranks consumption, never
    # dollars).  A stable name tiebreak keeps output deterministic.
    def _total(row: dict) -> int:
        return int(row.get("input_tokens") or 0) + int(row.get("output_tokens") or 0)

    ranked = sorted(cost_rows, key=lambda r: (-_total(r), str(r.get("prompt_name"))))
    rows = []
    for row in ranked:
        rows.append(
            "<tr>"
            f'<td class="wrap">{_text(row.get("prompt_name"))}</td>'
            f"<td>{int(row.get('input_tokens') or 0):,}</td>"
            f"<td>{int(row.get('output_tokens') or 0):,}</td>"
            f"<td>{int(row.get('call_count') or 0):,}</td>"
            "</tr>"
        )
    return (
        "<section class=\"panel\"><h2>This week's cost "
        '<span class="proxy">token proxy — ranks consumption, not billing-grade</span>'
        "</h2>"
        '<div class="scroll"><table>'
        "<thead><tr><th>Prompt</th><th>Input tok</th><th>Output tok</th>"
        "<th>Calls</th></tr></thead>"
        f'<tbody>{"".join(rows)}</tbody>'
        "</table></div></section>"
    )


def _decisions_panel(decisions: list[dict] | None) -> str:
    if decisions is MISSING:
        return _panel_missing("Needs a human")
    if not decisions:
        return (
            '<section class="panel"><h2>Needs a human</h2>'
            '<p class="empty">Nothing is waiting on you.</p>'
            '</section>'
        )
    items = []
    for d in decisions:
        prov = d.get("provenance")
        when = d.get("enqueued_at")
        meta_bits = []
        if prov:
            meta_bits.append(_text(prov))
        if when:
            meta_bits.append(_text(when))
        meta = (f'<div class="sub">{" · ".join(meta_bits)}</div>'
                if meta_bits else "")
        items.append(
            f'<li class="wrap">{_text(d.get("text"))}{meta}</li>'
        )
    return (
        '<section class="panel needs-human"><h2>Needs a human '
        f'<span class="count">{len(decisions)}</span></h2>'
        f'<ul class="decisions">{"".join(items)}</ul></section>'
    )


_CSS = """
:root{
  --bg:#f7f7f8;--card:#ffffff;--ink:#1c1c1e;--muted:#6b6b70;--line:#e4e4e7;
  --live:#1a7f37;--live-bg:#e7f6ec;--dead:#8a6d00;--dead-bg:#fbf3d6;
  --ok:#1a7f37;--ok-bg:#e7f6ec;--warn:#b3261e;--warn-bg:#fbe9e7;
  --accent:#5b4bd6;--miss:#b3261e;
}
@media (prefers-color-scheme:dark){
  :root{
    --bg:#131316;--card:#1d1d21;--ink:#ececf0;--muted:#9a9aa2;--line:#2c2c31;
    --live:#4ac26b;--live-bg:#12331d;--dead:#e0c04a;--dead-bg:#332b0f;
    --ok:#4ac26b;--ok-bg:#12331d;--warn:#f2837a;--warn-bg:#331615;
    --accent:#a99bff;--miss:#f2837a;
  }
}
*{box-sizing:border-box;}
body{margin:0;background:var(--bg);color:var(--ink);
  font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
  padding:24px;max-width:1100px;margin:0 auto;overflow-wrap:anywhere;}
header{display:flex;flex-wrap:wrap;gap:8px;align-items:baseline;
  justify-content:space-between;margin-bottom:20px;}
h1{font-size:22px;margin:0;}
.stamp{color:var(--muted);font-size:13px;}
.panel{background:var(--card);border:1px solid var(--line);border-radius:12px;
  padding:16px 18px;margin-bottom:18px;}
.panel h2{font-size:16px;margin:0 0 12px;display:flex;flex-wrap:wrap;
  align-items:baseline;gap:8px;}
.count{background:var(--accent);color:#fff;border-radius:999px;
  font-size:12px;padding:1px 9px;font-weight:600;}
.proxy{color:var(--muted);font-size:12px;font-weight:400;}
.scroll{overflow-x:auto;-webkit-overflow-scrolling:touch;}
table{width:100%;border-collapse:collapse;min-width:0;}
th,td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--line);
  vertical-align:top;font-size:14px;}
th{color:var(--muted);font-weight:600;font-size:12px;text-transform:uppercase;
  letter-spacing:.03em;white-space:nowrap;}
td.wrap,li.wrap{overflow-wrap:anywhere;word-break:break-word;}
.sub{color:var(--muted);font-size:12px;margin-top:2px;}
.muted{color:var(--muted);font-size:12px;}
.badge{display:inline-block;border-radius:6px;padding:1px 7px;font-size:12px;
  font-weight:600;}
.badge.live{color:var(--live);background:var(--live-bg);}
.badge.dead{color:var(--dead);background:var(--dead-bg);}
.badge.ok{color:var(--ok);background:var(--ok-bg);}
.badge.warn{color:var(--warn);background:var(--warn-bg);}
.empty{color:var(--muted);margin:0;}
.unavailable{color:var(--miss);margin:0;font-weight:600;}
.decisions{margin:0;padding-left:18px;}
.decisions li{margin-bottom:10px;}
.needs-human{border-left:3px solid var(--accent);}
""".strip()


def render_page(
    *,
    fleet: dict | None,
    cost_rows: list[dict] | None,
    decisions: list[dict] | None,
    generated_iso: str,
) -> str:
    """Render the whole page (AC.PAGE.1 / AC.PAGE.3).

    ``fleet`` / ``cost_rows`` / ``decisions`` are the already-read source
    values, or ``None`` (``MISSING``) when that source was unavailable.
    Returns one self-contained HTML string."""
    body = (
        _live_panel(fleet)
        + _outcomes_panel(fleet)
        + _cost_panel(cost_rows)
        + _decisions_panel(decisions)
    )
    stamp = escape(str(generated_iso))
    return (
        "<!doctype html>\n"
        '<html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        "<title>Agent fleet</title>"
        f"<style>{_CSS}</style></head><body>"
        "<header><h1>Agent fleet</h1>"
        f'<span class="stamp">regenerated {stamp}</span></header>'
        f"{body}"
        "</body></html>\n"
    )
