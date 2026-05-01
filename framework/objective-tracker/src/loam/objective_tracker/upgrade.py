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

"""D8 — Upgrade-fidelity harness (v1.1 R1).

Semantic round-trip: capture the projection state of every objective
(plus the scope-objective binding sidecar) pre-upgrade, replay the
projector post-upgrade, assert equivalence. Drift above a declared
threshold fails the upgrade.

SQLite snapshot preserves physical reversibility alongside the semantic
test — the pattern mirrors scope-of-work's D7 harness.

Drift = number of state-row fields whose post-upgrade value disagrees
with the pre-upgrade value, plus missing / extra objective ids, plus
binding-row mismatches.
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
    objective_id: str
    last_event_id: int
    state_row: dict[str, Any]


@dataclass
class BindingProbe:
    scope_id: str
    objective_id: str
    bound_event_id: int


@dataclass
class CapturedProbeSet:
    snapshot_db_path: str | None
    probes: list[ProjectionProbe] = field(default_factory=list)
    bindings: list[BindingProbe] = field(default_factory=list)


@dataclass
class DriftEntry:
    subject: str
    subject_kind: str
    field: str
    pre: Any
    post: Any


@dataclass
class DriftReport:
    drifted: list[DriftEntry] = field(default_factory=list)
    missing_post: list[str] = field(default_factory=list)
    extra_post: list[str] = field(default_factory=list)
    binding_missing_post: list[str] = field(default_factory=list)
    binding_extra_post: list[str] = field(default_factory=list)

    @property
    def total_drift(self) -> int:
        return (
            len(self.drifted)
            + len(self.missing_post)
            + len(self.extra_post)
            + len(self.binding_missing_post)
            + len(self.binding_extra_post)
        )

    def as_json(self) -> str:
        return json.dumps(
            {
                "drifted": [asdict(d) for d in self.drifted],
                "missing_post": self.missing_post,
                "extra_post": self.extra_post,
                "binding_missing_post": self.binding_missing_post,
                "binding_extra_post": self.binding_extra_post,
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
    snap_path = None
    if snapshot_to is not None:
        snap_path = str(store.snapshot_to(snapshot_to))

    probes: list[ProjectionProbe] = []
    for r in store.list_states():
        oid = r["objective_id"]
        proj = project(oid, store.events_for(oid))
        probes.append(
            ProjectionProbe(
                objective_id=oid,
                last_event_id=proj.last_event_id,
                state_row=projection_to_state_row(proj),
            )
        )
    bindings = [
        BindingProbe(
            scope_id=b["scope_id"],
            objective_id=b["objective_id"],
            bound_event_id=b["bound_event_id"],
        )
        for b in store.list_bindings()
    ]
    return CapturedProbeSet(
        snapshot_db_path=snap_path, probes=probes, bindings=bindings
    )


def replay_post_upgrade(
    store: EventStore, captured: CapturedProbeSet
) -> DriftReport:
    report = DriftReport()
    captured_ids = {p.objective_id for p in captured.probes}
    live_ids = {r["objective_id"] for r in store.list_states()}

    for oid in captured_ids - live_ids:
        report.missing_post.append(oid)
    for oid in live_ids - captured_ids:
        report.extra_post.append(oid)

    for probe in captured.probes:
        oid = probe.objective_id
        if oid not in live_ids:
            continue
        new_proj = project(oid, store.events_for(oid))
        new_row = projection_to_state_row(new_proj)
        all_keys = set(probe.state_row.keys()) | set(new_row.keys())
        for k in sorted(all_keys):
            pre = probe.state_row.get(k)
            post = new_row.get(k)
            if pre != post:
                report.drifted.append(
                    DriftEntry(
                        subject=oid,
                        subject_kind="objective",
                        field=k,
                        pre=pre,
                        post=post,
                    )
                )

    captured_scopes = {b.scope_id for b in captured.bindings}
    live_bindings = {b["scope_id"]: b for b in store.list_bindings()}
    live_scope_ids = set(live_bindings.keys())

    for s in captured_scopes - live_scope_ids:
        report.binding_missing_post.append(s)
    for s in live_scope_ids - captured_scopes:
        report.binding_extra_post.append(s)

    for bprobe in captured.bindings:
        live = live_bindings.get(bprobe.scope_id)
        if live is None:
            continue
        if live["objective_id"] != bprobe.objective_id:
            report.drifted.append(
                DriftEntry(
                    subject=bprobe.scope_id,
                    subject_kind="binding",
                    field="objective_id",
                    pre=bprobe.objective_id,
                    post=live["objective_id"],
                )
            )

    return report


def assert_no_drift(
    report: DriftReport, *, threshold: int = 0
) -> None:
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
            "bindings": [asdict(b) for b in c.bindings],
        },
        indent=2,
        default=str,
    )


def captured_from_json(s: str) -> CapturedProbeSet:
    raw = json.loads(s)
    return CapturedProbeSet(
        snapshot_db_path=raw.get("snapshot_db_path"),
        probes=[ProjectionProbe(**p) for p in raw["probes"]],
        bindings=[BindingProbe(**b) for b in raw.get("bindings", [])],
    )
