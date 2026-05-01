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

"""D4 — pre-upgrade probe run (coordinator).

Calls each sealed component's existing upgrade-fidelity surface and
aggregates every result into a single JSON-serialisable record. The
framework is explicitly **duck-typed** — each probe adapter below
accepts whatever the sealed component returns and normalises it to a
plain dict. If a component is not configured (no DB on disk, not
installed), the adapter returns a descriptive skip record; the upgrade
still proceeds because the absent component can't drift.

Component surfaces consumed (all unchanged — no seal amendment):

- memory-system: ``memory_system.upgrade.snapshot`` + ``run_probe_set``
  — but per the brief, the pre-upgrade call collects only the hash of
  the current DB state (the full probe run is memory's own harness).
  The framework's check in D6 calls ``memory.upgrade.compare()`` post-
  upgrade.
- scope-of-work: ``scope_of_work.upgrade.capture_pre_upgrade(store)``
- objective-tracker: ``objective_tracker.upgrade.capture_pre_upgrade``
- orchestrator: ``orchestrator.local_state.LocalStateStore.snapshot_probe()``
- dormancy: ``dormancy.state.DegradationStore.snapshot_probe()``
- primary-persona: ``primary_persona.compaction.build_survival_payload``
  — requires a loaded persona + runtime, so the pre-probe records only
  "loader importable" and we run the full payload check post-upgrade.
- observability-aggregator: framework-owned probe set
  (``aggregator_probes.run_aggregator_probes``).
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .aggregator_probes import (
    AggregatorProbeResult,
    aggregator_probe_hash,
    run_aggregator_probes,
)
from .paths import Paths


@dataclass
class ProbeRecord:
    """One component's probe output. ``status`` is 'ok' | 'skipped' |
    'error'; ``detail`` carries the reason when not ok."""

    component: str
    status: str
    payload: Any = None
    detail: str | None = None


@dataclass
class ProbeBundle:
    tag: str
    records: dict[str, ProbeRecord] = field(default_factory=dict)

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "tag": self.tag,
            "records": {k: asdict(v) for k, v in self.records.items()},
        }

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_json_dict(), indent=2, default=str))


# ---- memory --------------------------------------------------------


def _probe_memory(paths: Paths) -> ProbeRecord:
    """Record a hash of the memory DB file tree.

    The memory system owns its semantic probe — we do not rerun it at
    pre-upgrade time because it requires a fully-booted MemoryAPI.
    Instead the framework records the substrate hash which, combined
    with the post-upgrade ``memory.upgrade.compare()`` call, is
    sufficient for the clause-(c) check.
    """
    db_root = paths.memory_db
    if not db_root.exists():
        return ProbeRecord(
            component="memory",
            status="skipped",
            detail=f"memory db not present at {db_root}",
        )
    h = _hash_tree(db_root)
    return ProbeRecord(
        component="memory",
        status="ok",
        payload={"substrate_hash": h, "path": str(db_root)},
    )


# ---- scope-of-work -------------------------------------------------


def _probe_scope_of_work(paths: Paths) -> ProbeRecord:
    db = paths.scope_of_work_db
    if not db.exists():
        return ProbeRecord(
            component="scope_of_work",
            status="skipped",
            detail=f"scope_of_work db not present at {db}",
        )
    try:
        from loam.scope_of_work.store import EventStore  # type: ignore
        from loam.scope_of_work.upgrade import capture_pre_upgrade  # type: ignore
    except Exception as exc:
        return ProbeRecord(
            component="scope_of_work",
            status="error",
            detail=f"import failed: {type(exc).__name__}: {exc}",
        )
    try:
        store = EventStore(str(db))
        captured = capture_pre_upgrade(store)
        return ProbeRecord(
            component="scope_of_work",
            status="ok",
            payload={
                "snapshot_db_path": captured.snapshot_db_path,
                "probe_count": len(captured.probes),
                "per_prompt_costs_count": len(captured.per_prompt_costs),
                "probe_state_hash": _hash_obj(
                    [p.state_row for p in captured.probes]
                ),
            },
        )
    except Exception as exc:
        return ProbeRecord(
            component="scope_of_work",
            status="error",
            detail=f"capture failed: {type(exc).__name__}: {exc}",
        )


# ---- objective-tracker ---------------------------------------------


def _probe_objective_tracker(paths: Paths) -> ProbeRecord:
    db = paths.objective_tracker_db
    if not db.exists():
        return ProbeRecord(
            component="objective_tracker",
            status="skipped",
            detail=f"objective_tracker db not present at {db}",
        )
    try:
        from loam.objective_tracker.store import EventStore  # type: ignore
        from loam.objective_tracker.upgrade import capture_pre_upgrade  # type: ignore
    except Exception as exc:
        return ProbeRecord(
            component="objective_tracker",
            status="error",
            detail=f"import failed: {type(exc).__name__}: {exc}",
        )
    try:
        store = EventStore(str(db))
        captured = capture_pre_upgrade(store)
        return ProbeRecord(
            component="objective_tracker",
            status="ok",
            payload={
                "snapshot_db_path": captured.snapshot_db_path,
                "probe_count": len(captured.probes),
                "bindings_count": len(captured.bindings),
                "probe_state_hash": _hash_obj(
                    [p.state_row for p in captured.probes]
                ),
            },
        )
    except Exception as exc:
        return ProbeRecord(
            component="objective_tracker",
            status="error",
            detail=f"capture failed: {type(exc).__name__}: {exc}",
        )


# ---- orchestrator --------------------------------------------------


def _probe_orchestrator(paths: Paths) -> ProbeRecord:
    db = paths.orchestrator_db
    if not db.exists():
        return ProbeRecord(
            component="orchestrator",
            status="skipped",
            detail=f"orchestrator db not present at {db}",
        )
    try:
        from loam.orchestrator.local_state import LocalStateStore  # type: ignore
    except Exception as exc:
        return ProbeRecord(
            component="orchestrator",
            status="error",
            detail=f"import failed: {type(exc).__name__}: {exc}",
        )
    try:
        store = LocalStateStore(str(db))
        return ProbeRecord(
            component="orchestrator",
            status="ok",
            payload=store.snapshot_probe(),
        )
    except Exception as exc:
        return ProbeRecord(
            component="orchestrator",
            status="error",
            detail=f"snapshot_probe failed: {type(exc).__name__}: {exc}",
        )


# ---- dormancy ------------------------------------------


def _probe_degradation(paths: Paths) -> ProbeRecord:
    db = paths.degradation_db
    if not db.exists():
        return ProbeRecord(
            component="degradation",
            status="skipped",
            detail=f"degradation db not present at {db}",
        )
    try:
        from loam.dormancy.state import DegradationStore  # type: ignore
    except Exception as exc:
        return ProbeRecord(
            component="degradation",
            status="error",
            detail=f"import failed: {type(exc).__name__}: {exc}",
        )
    try:
        store = DegradationStore(str(db))
        return ProbeRecord(
            component="degradation",
            status="ok",
            payload=store.snapshot_probe(),
        )
    except Exception as exc:
        return ProbeRecord(
            component="degradation",
            status="error",
            detail=f"snapshot_probe failed: {type(exc).__name__}: {exc}",
        )


# ---- primary-persona -----------------------------------------------


def _probe_primary_persona() -> ProbeRecord:
    """Pre-probe only confirms the compaction module is importable.

    The full ``build_survival_payload`` call at clause (b) verify-time
    needs a runtime + persona which are not available at pre-upgrade
    snapshot time.
    """
    try:
        from loam.primary_persona.compaction import SURVIVAL_LIST  # type: ignore

        return ProbeRecord(
            component="primary_persona",
            status="ok",
            payload={"survival_list": list(SURVIVAL_LIST)},
        )
    except Exception as exc:
        return ProbeRecord(
            component="primary_persona",
            status="error",
            detail=f"import failed: {type(exc).__name__}: {exc}",
        )


# ---- aggregator (framework-owned probe) ----------------------------


def _probe_aggregator(paths: Paths) -> ProbeRecord:
    db = paths.aggregator_db
    # If .duckdb absent, check for a .sqlite fallback alongside
    if not db.exists():
        alt = db.with_suffix(".sqlite")
        if alt.exists():
            db = alt
        else:
            return ProbeRecord(
                component="aggregator",
                status="skipped",
                detail=f"aggregator db not present at {db}",
            )
    try:
        result = run_aggregator_probes(db)
        return ProbeRecord(
            component="aggregator",
            status="ok",
            payload={
                "probe_set_version": result.probe_set_version,
                "substrate": result.substrate,
                "queries": result.queries,
                "hash": aggregator_probe_hash(result),
            },
        )
    except Exception as exc:
        return ProbeRecord(
            component="aggregator",
            status="error",
            detail=f"probe failed: {type(exc).__name__}: {exc}",
        )


# ---- coordinator ---------------------------------------------------


def collect_pre_probe(paths: Paths, tag: str) -> ProbeBundle:
    """Run every component's pre-upgrade probe. Never raises on a
    single component failure — the record carries status='error' and
    the D6 clause check decides whether the upgrade proceeds."""
    bundle = ProbeBundle(tag=tag)
    bundle.records["memory"] = _probe_memory(paths)
    bundle.records["scope_of_work"] = _probe_scope_of_work(paths)
    bundle.records["objective_tracker"] = _probe_objective_tracker(paths)
    bundle.records["orchestrator"] = _probe_orchestrator(paths)
    bundle.records["degradation"] = _probe_degradation(paths)
    bundle.records["primary_persona"] = _probe_primary_persona()
    bundle.records["aggregator"] = _probe_aggregator(paths)
    return bundle


def post_upgrade_probe_hashes(paths: Paths) -> dict[str, str]:
    """A fast, hash-only probe used as the D3 consistency check.

    Pre-snapshot and post-snapshot calls must produce identical
    results. If they don't, the snapshot straddled a concurrent write
    and is not trustworthy — the upgrade halts before touching files.
    """
    out: dict[str, str] = {}
    for comp, fn in (
        ("memory", lambda: _hash_tree(paths.memory_db)),
        ("scope_of_work", lambda: _hash_file(paths.scope_of_work_db)),
        (
            "objective_tracker",
            lambda: _hash_file(paths.objective_tracker_db),
        ),
        ("orchestrator", lambda: _hash_file(paths.orchestrator_db)),
        ("degradation", lambda: _hash_file(paths.degradation_db)),
        ("aggregator", lambda: _hash_file(paths.aggregator_db)),
    ):
        try:
            out[comp] = fn()
        except FileNotFoundError:
            out[comp] = "absent"
    return out


# ---- hashing helpers -----------------------------------------------


def _hash_file(p: Path) -> str:
    if not p.exists():
        return "absent"
    import hashlib

    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _hash_tree(p: Path) -> str:
    """Stable hash over a directory tree — sorted rel-paths + file shas."""
    if not p.exists():
        return "absent"
    import hashlib

    h = hashlib.sha256()
    if p.is_file():
        return _hash_file(p)
    entries = sorted(p.rglob("*"))
    for entry in entries:
        if entry.is_file():
            rel = entry.relative_to(p).as_posix().encode()
            h.update(rel + b"\0")
            h.update(_hash_file(entry).encode() + b"\0")
    return h.hexdigest()


def _hash_obj(o: Any) -> str:
    import hashlib

    body = json.dumps(o, sort_keys=True, default=str).encode()
    return hashlib.sha256(body).hexdigest()
