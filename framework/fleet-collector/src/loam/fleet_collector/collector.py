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

"""The fleet collector bridge (WS-A2).

``collect_fleet(roots)`` globs the on-disk records isolated agents
actually produce — ``handsoff-loop`` run dirs (``run_record.jsonl`` +
``run_summary.json``) and any co-located ``subloam-driver`` cost summary
— and emits one fleet-state dict describing every known run (live and
recent).  It is READ-ONLY over both contracts (it never writes into a
run dir, never modifies either producing component).  The renderer
(WS-A3) consumes the emitted JSON; this module is the bridge, not the
view.

Every field the collector emits maps to WS-A2's acceptance criteria
(BACKPLANE-PLAN §5): the seven named fields
``{workspace, objective, stage, elapsed, alive, cost_usd, exit_status}``
(AC.FLEET.1), plus ``cost_source`` (the constraint that a missing cost
is honest about its absence, never fabricated).  Liveness is the reused
``probe_liveness`` (AC.FLEET.1: "matches the artifact evidence" — the
one shared reader, never a second hand-rolled probe).  The JSONL read is
tolerant of a partial mid-write last line (AC.FLEET.2).
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ._liveness import probe_liveness

# The handsoff-loop run-record filename (RUN_RECORD_NAME in
# handsoff_loop.progress) and the run-summary filename
# (build_from_intent._finish).  Read-side mirror of those producer
# contracts.
RUN_RECORD_NAME = "run_record.jsonl"
RUN_SUMMARY_NAME = "run_summary.json"

# The heartbeat stage is a liveness pseudo-stage, not pipeline progress
# (D-A2-3): the reported stage is the last NON-heartbeat event's stage.
HEARTBEAT_STAGE = "heartbeat"

# A subloam-driver cost summary is recognised by the full key-set it
# carries (D-A2-2): all three keys present together.  Detecting on the
# full set — not ``cost_usd`` alone — keeps ``run_summary.json`` (which
# carries none of them) and any future sidecar from false-matching.
_COST_KEYS = ("cost_usd", "cost_source", "exit_status")


@dataclass
class FleetRun:
    """One agent run's fleet-state row.

    The seven AC.FLEET.1 fields plus the honesty companions
    ``cost_source`` (never a fabricated cost) and ``artifact_age_s``
    (the concrete artifact-probe evidence the ``alive`` bool is drawn
    from, so the alive/dead judgment is auditable)."""

    run_dir: str
    workspace: str
    objective: str | None
    stage: str | None
    elapsed_s: float | None
    alive: bool
    artifact_age_s: float | None
    cost_usd: float | None
    cost_source: str
    exit_status: Any

    def as_dict(self) -> dict:
        return {
            "run_dir": self.run_dir,
            "workspace": self.workspace,
            "objective": self.objective,
            "stage": self.stage,
            "elapsed_s": self.elapsed_s,
            "alive": self.alive,
            "artifact_age_s": self.artifact_age_s,
            "cost_usd": self.cost_usd,
            "cost_source": self.cost_source,
            "exit_status": self.exit_status,
        }


def _read_run_record(record_path: Path) -> list[dict]:
    """Tolerant JSONL read (AC.FLEET.2).

    Returns the list of complete events.  A partial (mid-write) last
    line — or any single malformed line — is skipped, never raised: the
    run still appears with its last COMPLETE state.  This is the reason
    the collector does not reuse ``RunRecord.events()`` (which
    ``json.loads`` every line and would crash on a partial trailing
    line)."""
    events: list[dict] = []
    try:
        text = record_path.read_text(encoding="utf-8")
    except OSError:
        return events
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            # A partial last line (or a torn line) is not fatal — skip it
            # and keep every complete event before it.
            continue
    return events


def _stage_from_events(events: list[dict]) -> str | None:
    """Last NON-heartbeat stage (D-A2-3); fall back to the last stage if
    every event is a heartbeat."""
    for ev in reversed(events):
        stage = ev.get("stage")
        if stage and stage != HEARTBEAT_STAGE:
            return str(stage)
    if events:
        last = events[-1].get("stage")
        return str(last) if last else None
    return None


def _elapsed_from_events(events: list[dict], *, alive: bool,
                         now: float) -> float | None:
    """Wall-clock span of recorded activity.

    From the first event's ``ts`` to now (a live run is still running) or
    to the last event's ``ts`` (a finished/dead run stopped writing).
    ``None`` when the record carries no usable timestamps."""
    tss = [ev["ts"] for ev in events
           if isinstance(ev.get("ts"), (int, float))]
    if not tss:
        return None
    first = min(tss)
    end = now if alive else max(tss)
    return round(end - first, 1)


def _objective_from_summary(summary: dict | None) -> str | None:
    """objective from ``run_summary.json`` (D-A2-1).

    ``design.objective`` is the confirmed build objective; ``intent``
    is the fallback echo.  ``None`` when no summary exists (a live run is
    not yet summarised — the collector never invents an objective)."""
    if not summary:
        return None
    design = summary.get("design")
    if isinstance(design, dict):
        obj = design.get("objective")
        if isinstance(obj, str) and obj.strip():
            return obj
    intent = summary.get("intent")
    if isinstance(intent, dict):
        obj = intent.get("objective")
        if isinstance(obj, str) and obj.strip():
            return obj
    return None


def _read_json(path: Path) -> dict | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _cost_from_run_dir(run_dir: Path) -> tuple[float | None, str, Any]:
    """cost_usd / cost_source / exit_status from a co-located driver
    summary (D-A2-2).

    A ``subloam-driver`` summary is any top-level ``*.json`` in the run
    dir carrying the full cost key-set.  Absent → the honest triple
    ``(None, "absent", None)``: a missing cost is never fabricated
    (constraint), and ``run_summary.json`` cannot false-match because it
    carries none of the cost keys."""
    for candidate in sorted(run_dir.glob("*.json")):
        if candidate.name == RUN_SUMMARY_NAME:
            continue
        data = _read_json(candidate)
        if data is None:
            continue
        if all(k in data for k in _COST_KEYS):
            cost = data.get("cost_usd")
            cost_usd = cost if isinstance(cost, (int, float)) else None
            source = data.get("cost_source")
            cost_source = str(source) if source else "absent"
            return cost_usd, cost_source, data.get("exit_status")
    return None, "absent", None


def _workspace_for(run_dir: Path) -> str:
    """workspace = the run dir's owning workspace tree (D-A2-4).

    A run dir is ``<workspace>/runs/<ts>``; the workspace is two levels
    up.  When the dir is not under a ``runs/`` parent, fall back to the
    immediate parent."""
    parent = run_dir.parent
    if parent.name == "runs":
        return str(parent.parent)
    return str(parent)


def _is_run_dir(path: Path) -> bool:
    """A run dir is identified by its handsoff-loop run record."""
    return (path / RUN_RECORD_NAME).is_file()


def _discover_run_dirs(root: Path) -> list[Path]:
    """Every run dir at or beneath ``root``.

    ``root`` may itself be a run dir (fixture/CLI convenience) or a tree
    containing many (a workspace's ``runs/`` dir, or a parent of
    several)."""
    found: list[Path] = []
    if _is_run_dir(root):
        found.append(root)
    for record in root.rglob(RUN_RECORD_NAME):
        run_dir = record.parent
        if run_dir != root:
            found.append(run_dir)
    return found


def collect_run(run_dir: Path, *, stale_after_s: float = 300.0,
                now: float | None = None) -> FleetRun:
    """Build one fleet-state row from a single run dir.

    Liveness is the reused ``probe_liveness`` (AC.FLEET.1) — this is the
    only liveness reader; no second probe is defined here."""
    run_dir = Path(run_dir)
    now = time.time() if now is None else now

    live = probe_liveness(run_dir, stale_after_s=stale_after_s)
    alive = bool(live.get("alive"))
    artifact_age_s = live.get("artifact_age_s")

    events = _read_run_record(run_dir / RUN_RECORD_NAME)
    stage = _stage_from_events(events)
    elapsed_s = _elapsed_from_events(events, alive=alive, now=now)

    summary = _read_json(run_dir / RUN_SUMMARY_NAME)
    objective = _objective_from_summary(summary)

    cost_usd, cost_source, exit_status = _cost_from_run_dir(run_dir)

    return FleetRun(
        run_dir=str(run_dir),
        workspace=_workspace_for(run_dir),
        objective=objective,
        stage=stage,
        elapsed_s=elapsed_s,
        alive=alive,
        artifact_age_s=artifact_age_s,
        cost_usd=cost_usd,
        cost_source=cost_source,
        exit_status=exit_status,
    )


def collect_fleet(roots: list[Path] | Path | str,
                  *, stale_after_s: float = 300.0) -> dict:
    """The production entry point (AC.FLEET.1/.2/.3).

    Discovers every run dir under ``roots`` and emits one fleet-state
    dict: ``{generated_at, generated_at_iso, run_count, runs: [...]}``.
    Runs are ordered newest-first by elapsed-start so the live feed reads
    top-down.  ``stale_after_s`` is the liveness staleness bound passed
    through to the reused probe."""
    if isinstance(roots, (str, Path)):
        roots = [Path(roots)]
    else:
        roots = [Path(r) for r in roots]

    now = time.time()
    seen: set[Path] = set()
    run_dirs: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        for rd in _discover_run_dirs(root):
            rd = rd.resolve()
            if rd not in seen:
                seen.add(rd)
                run_dirs.append(rd)

    runs = [collect_run(rd, stale_after_s=stale_after_s, now=now)
            for rd in run_dirs]
    # Live runs first, then most-recently-active; a stable name tiebreak
    # keeps output deterministic across globs.
    runs.sort(key=lambda r: (not r.alive,
                             -(r.artifact_age_s is None),
                             r.artifact_age_s if r.artifact_age_s is not None
                             else float("inf"),
                             r.run_dir))
    return {
        "generated_at": now,
        "generated_at_iso": time.strftime("%Y-%m-%dT%H:%M:%S",
                                          time.localtime(now)),
        "run_count": len(runs),
        "runs": [r.as_dict() for r in runs],
    }
