"""OrchestratorConfig — user-home paths, intervals, thresholds.

Defaults follow the brief:
  - ~/.loam/                 — root configuration / state dir
  - ~/.loam/orchestrator.sqlite
  - ~/.loam/orchestrator.sock    (0600)
  - ~/.loam/bootstrap.py         (optional; loaded by the
                                  workspace-bootstrap framework's
                                  WorkspaceBootstrapPyContribution
                                  adapter, not by the orchestrator
                                  itself — amendment #7)
  - ~/.loam/precompact.flag      (written by session's PreCompact hook)

Every path is configurable via OrchestratorConfig(...). YAML loader
provided for convenience (`load_config(path)`).

All intervals are seconds.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

import yaml

_DEFAULT_ROOT = Path.home() / ".loam"


@dataclass(frozen=True)
class OrchestratorConfig:
    """Runtime configuration for the orchestrator process."""

    # Storage roots --------------------------------------------------
    root_dir: Path = _DEFAULT_ROOT
    local_sqlite_path: Path | None = None
    socket_path: Path | None = None
    bootstrap_path: Path | None = None
    precompact_flag_dir: Path | None = None

    # Phase 1 store paths (consumed via public APIs) -----------------
    scope_of_work_db: Path | None = None
    objective_tracker_db: Path | None = None
    pending_extension_dir: Path | None = None

    # Timing --------------------------------------------------------
    heartbeat_interval_seconds: float = 5.0
    sigterm_grace_seconds: float = 10.0
    awareness_pull_timeout_ms: int = 100
    launchd_throttle_seconds: int = 30

    # IPC ------------------------------------------------------------
    socket_mode: int = 0o600

    # Workspace label (OTel attribute) -------------------------------
    workspace_label: str = "pos-v2"

    def __post_init__(self) -> None:
        # Resolve dependent defaults against root_dir. Because the
        # dataclass is frozen, object.__setattr__ is used.
        root = Path(self.root_dir)
        object.__setattr__(self, "root_dir", root)
        if self.local_sqlite_path is None:
            object.__setattr__(
                self, "local_sqlite_path", root / "orchestrator.sqlite"
            )
        if self.socket_path is None:
            object.__setattr__(self, "socket_path", root / "orchestrator.sock")
        if self.bootstrap_path is None:
            object.__setattr__(self, "bootstrap_path", root / "bootstrap.py")
        if self.precompact_flag_dir is None:
            object.__setattr__(self, "precompact_flag_dir", root)
        if self.scope_of_work_db is None:
            object.__setattr__(
                self, "scope_of_work_db", root / "scope_of_work.sqlite"
            )
        if self.objective_tracker_db is None:
            object.__setattr__(
                self, "objective_tracker_db", root / "objective_tracker.sqlite"
            )
        if self.pending_extension_dir is None:
            object.__setattr__(
                self,
                "pending_extension_dir",
                root / "pending_extensions",
            )

    # -- path helpers ------------------------------------------------

    def ensure_dirs(self) -> None:
        """Create the root + subdirs needed for first start."""
        self.root_dir.mkdir(parents=True, exist_ok=True)
        assert self.pending_extension_dir is not None
        self.pending_extension_dir.mkdir(parents=True, exist_ok=True)


def load_config(path: str | Path) -> OrchestratorConfig:
    """Load config from a YAML file. Keys are all OrchestratorConfig
    field names; unknown keys raise ValueError."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"config not found: {path}")
    data: dict[str, Any] = yaml.safe_load(path.read_text()) or {}
    # Coerce path-like fields.
    path_fields = {
        "root_dir",
        "local_sqlite_path",
        "socket_path",
        "bootstrap_path",
        "precompact_flag_dir",
        "scope_of_work_db",
        "objective_tracker_db",
        "pending_extension_dir",
    }
    for k in list(data.keys()):
        if k in path_fields and data[k] is not None:
            data[k] = Path(os.path.expanduser(data[k]))
    valid = {f.name for f in OrchestratorConfig.__dataclass_fields__.values()}
    unknown = set(data.keys()) - valid
    if unknown:
        raise ValueError(f"unknown config keys: {sorted(unknown)}")
    return OrchestratorConfig(**data)


def with_overrides(base: OrchestratorConfig, **kwargs: Any) -> OrchestratorConfig:
    """Test helper — swap named fields without mutating the dataclass."""
    return replace(base, **kwargs)
