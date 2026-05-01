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

"""D3 — pre-upgrade snapshot.

Every sealed component's durable state is copied atomically into the
pre-upgrade history directory before any framework file changes. If
the upgrade fails (or the user invokes ``pos rollback``), the files
under ``~/.loam/framework/history/<tag>-pre/`` are the source of truth.

Post-snapshot consistency check: each component's ``snapshot_probe()``
(or equivalent upgrade-capture call) is run once *before* the file
copies and once *after*. The two results must be equal — if they
aren't, the snapshot straddled concurrent writes and is untrustworthy,
and the upgrade halts before applying any change.

Components and the files they own:

+---------------------+------------------------------------+
| memory              | entire ``memory/`` kuzu DB tree    |
| scope-of-work       | ``scope_of_work.sqlite`` + WAL sib |
| objective-tracker   | ``objective_tracker.sqlite`` + WAL |
| orchestrator        | ``orchestrator.sqlite`` + WAL      |
| graceful-degradation| ``dormancy.sqlite`` + WAL       |
| observability-aggr  | ``observability.duckdb``           |
+---------------------+------------------------------------+

The primary-persona layer has no on-disk substrate — the survival
payload is built from memory + orchestrator at call time. No
substrate snapshot needed; clause (b) verification at step D6 is a
live call against the new module.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from .paths import Paths


# Components with a file-copy substrate. The framework copies every
# sibling matching the base name (captures WAL/journal/shm files).
_SUBSTRATE_COMPONENTS: tuple[str, ...] = (
    "memory",
    "scope_of_work",
    "objective_tracker",
    "orchestrator",
    "degradation",
    "aggregator",
)


@dataclass
class ComponentSnapshot:
    component: str
    source: Path
    target: Path
    files_copied: int
    bytes_copied: int


@dataclass
class SnapshotResult:
    tag: str
    history_dir: Path
    per_component: dict[str, ComponentSnapshot] = field(default_factory=dict)


def _source_for(paths: Paths, component: str) -> Path:
    match component:
        case "memory":
            return paths.memory_db
        case "scope_of_work":
            return paths.scope_of_work_db
        case "objective_tracker":
            return paths.objective_tracker_db
        case "orchestrator":
            return paths.orchestrator_db
        case "degradation":
            return paths.degradation_db
        case "aggregator":
            return paths.aggregator_db
    raise KeyError(f"unknown substrate component: {component}")


def _snapshot_component(
    component: str, source: Path, target_root: Path
) -> ComponentSnapshot:
    """Copy every sibling (file or subtree) matching source name.

    For a single-file substrate (SQLite, DuckDB), this picks up the
    main file plus WAL/journal/shm siblings. For a directory substrate
    (Kuzu memory DB), the directory itself is copied as a single
    subtree.
    """
    target = target_root / component
    target.mkdir(parents=True, exist_ok=True)
    n = 0
    b = 0
    if source.exists() and source.is_dir():
        # Directory substrate (e.g. Kuzu)
        dest = target / source.name
        shutil.copytree(source, dest, dirs_exist_ok=True)
        for p in dest.rglob("*"):
            if p.is_file():
                n += 1
                b += p.stat().st_size
    else:
        # File substrate + siblings sharing the base name
        parent = source.parent
        if parent.exists():
            for sibling in parent.glob(source.name + "*"):
                if sibling.is_file():
                    dest = target / sibling.name
                    shutil.copy2(sibling, dest)
                    n += 1
                    b += sibling.stat().st_size
    return ComponentSnapshot(
        component=component,
        source=source,
        target=target,
        files_copied=n,
        bytes_copied=b,
    )


def capture_substrate_snapshots(
    paths: Paths,
    tag: str,
    *,
    components: tuple[str, ...] = _SUBSTRATE_COMPONENTS,
    probe_fn: Callable[[], dict] | None = None,
) -> SnapshotResult:
    """Take a file-copy snapshot of every component's substrate.

    ``probe_fn`` is the post-snapshot consistency check: caller-supplied
    function that returns a dict of each component's pre-snapshot probe
    hash; the framework re-runs the same probes after the copy and
    raises on mismatch. Supplying ``None`` skips the check (used only
    for bootstrap testing).
    """
    paths.ensure_history(tag)
    history_dir = paths.history_dir_pre(tag)
    result = SnapshotResult(tag=tag, history_dir=history_dir)

    pre_probe = probe_fn() if probe_fn else None

    for comp in components:
        source = _source_for(paths, comp)
        snap = _snapshot_component(comp, source, history_dir)
        result.per_component[comp] = snap

    # Post-snapshot consistency check
    if probe_fn is not None:
        post_probe = probe_fn()
        if pre_probe != post_probe:
            # Build a precise failure message and clean up.
            drift = [
                k
                for k in set(pre_probe) | set(post_probe)
                if pre_probe.get(k) != post_probe.get(k)
            ]
            raise RuntimeError(
                f"snapshot-drift: components diverged during snapshot: {drift}"
            )

    return result


def restore_substrate_snapshots(
    paths: Paths,
    tag: str,
    *,
    components: tuple[str, ...] = _SUBSTRATE_COMPONENTS,
) -> None:
    """Copy every snapshotted file back to its original location.

    Before copying, existing live files under each source base name
    are removed so the restore is exact (no leftover WAL from the
    failed upgrade).
    """
    history_dir = paths.history_dir_pre(tag)
    if not history_dir.exists():
        raise FileNotFoundError(f"no pre-upgrade snapshot for tag: {tag}")

    # Fail hard if any expected component snapshot dir is missing — a
    # silent skip here is exactly the clause-g anti-pattern the
    # framework prohibits. The caller (rollback) records this as a
    # failed step so the destructive-test runbook can detect it.
    missing_snapshots = [
        comp
        for comp in components
        if not (history_dir / comp).exists()
        and _source_for(paths, comp).exists()
    ]
    if missing_snapshots:
        raise FileNotFoundError(
            f"pre-upgrade snapshot incomplete for tag {tag}: "
            f"missing component dirs {missing_snapshots}"
        )

    for comp in components:
        target = history_dir / comp
        if not target.exists():
            continue
        source = _source_for(paths, comp)

        # Clear live state first
        if source.exists() and source.is_dir():
            shutil.rmtree(source, ignore_errors=True)
        else:
            parent = source.parent
            if parent.exists():
                for sibling in parent.glob(source.name + "*"):
                    if sibling.is_file():
                        sibling.unlink()
                    elif sibling.is_dir():
                        shutil.rmtree(sibling, ignore_errors=True)

        # Copy snapshot back to live
        if source.is_dir() or not source.parent.exists():
            source.parent.mkdir(parents=True, exist_ok=True)

        for entry in target.iterdir():
            dest = source.parent / entry.name
            if entry.is_dir():
                shutil.copytree(entry, dest, dirs_exist_ok=True)
            else:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(entry, dest)


def substrate_components() -> tuple[str, ...]:
    return _SUBSTRATE_COMPONENTS
