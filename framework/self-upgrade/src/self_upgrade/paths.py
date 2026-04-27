"""Filesystem layout helpers.

pOS places all framework state under ``~/.pos``:

- ``~/.pos/framework/current``         — symlink to the live release
- ``~/.pos/framework/releases/<tag>/`` — unpacked release tree
- ``~/.pos/framework/staging/<tag>/``  — freshly unpacked, not yet live
- ``~/.pos/framework/history/<tag>*``  — pre/post probe files + reports
- ``~/.pos/framework/history/<tag>-pre/`` — pre-upgrade file-copy snaps
- ``~/.pos/upgrade-config.yaml``       — `auto_update_mode` + tunables

Substrate data files are **not** under ``framework/``:

- ``~/.pos/memory/*.kuzu``              — memory system
- ``~/.pos/scope_of_work.sqlite``       — scope-of-work
- ``~/.pos/objective_tracker.sqlite``   — objective-tracker
- ``~/.pos/orchestrator.sqlite``        — orchestrator local state
- ``~/.pos/degradation.sqlite``         — graceful-degradation
- ``~/.pos/observability.duckdb``       — observability aggregator

This module centralises resolution so tests can point the whole tree
at a ``tmp_path`` by overriding ``POS_BASE_DIR``.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_BASE_DIR = "~/.pos"


@dataclass(frozen=True)
class Paths:
    base: Path

    @classmethod
    def from_env(cls, base_dir: str | None = None) -> "Paths":
        raw = base_dir or os.environ.get("POS_BASE_DIR") or DEFAULT_BASE_DIR
        return cls(Path(os.path.expanduser(raw)).resolve())

    @property
    def framework(self) -> Path:
        return self.base / "framework"

    @property
    def current_link(self) -> Path:
        return self.framework / "current"

    @property
    def releases(self) -> Path:
        return self.framework / "releases"

    @property
    def staging(self) -> Path:
        return self.framework / "staging"

    @property
    def history(self) -> Path:
        return self.framework / "history"

    @property
    def upgrade_config(self) -> Path:
        return self.base / "upgrade-config.yaml"

    # Data substrate paths
    @property
    def memory_db(self) -> Path:
        return self.base / "memory"

    @property
    def scope_of_work_db(self) -> Path:
        return self.base / "scope_of_work.sqlite"

    @property
    def objective_tracker_db(self) -> Path:
        return self.base / "objective_tracker.sqlite"

    @property
    def orchestrator_db(self) -> Path:
        return self.base / "orchestrator.sqlite"

    @property
    def degradation_db(self) -> Path:
        return self.base / "degradation.sqlite"

    @property
    def aggregator_db(self) -> Path:
        return self.base / "observability.duckdb"

    def history_dir_pre(self, tag: str) -> Path:
        return self.history / f"{tag}-pre"

    def release_dir(self, tag: str) -> Path:
        return self.releases / tag

    def staging_dir(self, tag: str) -> Path:
        return self.staging / tag

    def conflicts_yaml(self, tag: str) -> Path:
        return self.history / f"{tag}-conflicts.yaml"

    def accepted_json(self, tag: str) -> Path:
        return self.history / f"{tag}-accepted.json"

    def rolled_back_json(self, tag: str) -> Path:
        return self.history / f"{tag}-rolled-back.json"

    def pre_probe_json(self, tag: str) -> Path:
        return self.history_dir_pre(tag) / "pre-probe.json"

    def post_probe_json(self, tag: str) -> Path:
        return self.history / f"{tag}-post-probe.json"

    def ensure_history(self, tag: str) -> None:
        self.history.mkdir(parents=True, exist_ok=True)
        self.history_dir_pre(tag).mkdir(parents=True, exist_ok=True)
