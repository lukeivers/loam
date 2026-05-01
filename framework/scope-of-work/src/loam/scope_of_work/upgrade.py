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

"""D7 — Upgrade-fidelity test harness (v1.1 R1).

Brief D7 acceptance:
- A probe set of scope creations, transitions, and queries is captured
  pre-upgrade.
- The same probes are replayed post-upgrade.
- Output-equivalence is asserted; drift above a declared threshold
  fails the upgrade.
- SQLite database snapshot preserves physical reversibility alongside
  the semantic test.

The harness operates in two passes:

1. PRE-UPGRADE: capture the projection state of every scope as a
   "probe" — a dict of (scope_id, last_event_id, state, ledger,
   per-prompt-cost-row). Save to a JSON file. Take a SQLite snapshot
   alongside.

2. POST-UPGRADE: re-run the projector against the live event log; for
   every probe, compare the reconstructed projection against the
   captured one. Emit a `DriftReport` with per-scope deltas. Drift
   above the threshold fails.

Drift = number of fields whose post-upgrade value disagrees with the
pre-upgrade value. Threshold default 0 (any drift fails); callers can
relax for forward-compatible additions (e.g. a new optional field).
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .projection import project, projection_to_state_row
from .store import EventStore


@dataclass
class ProjectionProbe:
    scope_id: str
    last_event_id: int
    state_row: dict[str, Any]


@dataclass
class CapturedProbeSet:
    snapshot_db_path: str | None
    probes: list[ProjectionProbe] = field(default_factory=list)
    per_prompt_costs: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class DriftEntry:
    scope_id: str
    field: str
    pre: Any
    post: Any


@dataclass
class DriftReport:
    drifted: list[DriftEntry] = field(default_factory=list)
    missing_post: list[str] = field(default_factory=list)
    extra_post: list[str] = field(default_factory=list)

    @property
    def total_drift(self) -> int:
        return len(self.drifted) + len(self.missing_post) + len(self.extra_post)

    def as_json(self) -> str:
        return json.dumps(
            {
                "drifted": [asdict(d) for d in self.drifted],
                "missing_post": self.missing_post,
                "extra_post": self.extra_post,
                "total_drift": self.total_drift,
            },
            indent=2,
            default=str,
        )


def capture_pre_upgrade(
    store: EventStore,
    *,
    snapshot_to: str | Path | None = None,
) -> CapturedProbeSet:
    """Snapshot every scope's projection AND the SQLite file."""
    snap_path = None
    if snapshot_to is not None:
        snap_path = str(store.snapshot_to(snapshot_to))

    probes: list[ProjectionProbe] = []
    rows = store.list_states()
    for r in rows:
        sid = r["scope_id"]
        events = store.events_for(sid)
        proj = project(sid, events)
        probes.append(
            ProjectionProbe(
                scope_id=sid,
                last_event_id=proj.last_event_id,
                state_row=projection_to_state_row(proj),
            )
        )
    costs = store.per_prompt_costs()
    return CapturedProbeSet(
        snapshot_db_path=snap_path, probes=probes, per_prompt_costs=costs
    )


def replay_post_upgrade(
    store: EventStore, captured: CapturedProbeSet
) -> DriftReport:
    """Replay the projector on the live event log; compare to captured."""
    report = DriftReport()
    captured_ids = {p.scope_id for p in captured.probes}
    live_ids = {r["scope_id"] for r in store.list_states()}

    for sid in captured_ids - live_ids:
        report.missing_post.append(sid)
    for sid in live_ids - captured_ids:
        report.extra_post.append(sid)

    for probe in captured.probes:
        sid = probe.scope_id
        if sid not in live_ids:
            continue
        events = store.events_for(sid)
        new_proj = project(sid, events)
        new_row = projection_to_state_row(new_proj)
        # Compare every field; record disagreements.
        all_keys = set(probe.state_row.keys()) | set(new_row.keys())
        for k in sorted(all_keys):
            pre = probe.state_row.get(k)
            post = new_row.get(k)
            if pre != post:
                report.drifted.append(
                    DriftEntry(scope_id=sid, field=k, pre=pre, post=post)
                )

    return report


def assert_no_drift(
    report: DriftReport, *, threshold: int = 0
) -> None:
    """Raise if drift exceeds threshold. Used as the upgrade gate."""
    if report.total_drift > threshold:
        raise AssertionError(
            f"upgrade drift {report.total_drift} exceeds threshold "
            f"{threshold}; report:\n{report.as_json()}"
        )


def captured_to_json(c: CapturedProbeSet) -> str:
    return json.dumps(
        {
            "snapshot_db_path": c.snapshot_db_path,
            "probes": [asdict(p) for p in c.probes],
            "per_prompt_costs": c.per_prompt_costs,
        },
        indent=2,
        default=str,
    )


def captured_from_json(s: str) -> CapturedProbeSet:
    raw = json.loads(s)
    return CapturedProbeSet(
        snapshot_db_path=raw.get("snapshot_db_path"),
        probes=[ProjectionProbe(**p) for p in raw["probes"]],
        per_prompt_costs=raw.get("per_prompt_costs", []),
    )
