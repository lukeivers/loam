"""Adapter — orchestrator's existing `~/.loam/bootstrap.py` escape hatch.

Phase: after_orchestrator_ready (per Eve-inference #6 — the
workspace-authored hook sees a fully-wired orchestrator at this
phase; pre-orchestrator-start would be too early).

Role (per proposal §2 / brief §1): invoke the orchestrator's sealed
`load_and_register(bootstrap_path, orchestrator)` as a late-phase
contribution. Preserves the fail-closed posture the orchestrator
already ships with — on `BootstrapMissing`, this adapter re-raises
that exception (wrapped by the framework as -32086).

Config (`workspace_bootstrap_py.yaml` under host.config_dir):
    bootstrap_path: str (default: `~/.loam/bootstrap.py`)
    required: bool (default: False) — when False, a missing file is
        logged but does not fail-close. The default is False because
        most test workspaces do not ship a bootstrap.py; production
        workspaces set `required: True`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, ClassVar

import yaml

from ..errors import AdapterRaisedError
from ..spec import BaseContribution, ContributionMetadata, Phase


class WorkspaceBootstrapPyContribution(BaseContribution):
    metadata: ClassVar[ContributionMetadata] = ContributionMetadata(
        name="workspace_bootstrap_py",
        phase=Phase.after_orchestrator_ready,
        after=("self_correction",),
    )

    def contribute(self, host) -> None:
        from pos_orchestrator.bootstrap import load_and_register
        from pos_orchestrator.errors import BootstrapError, BootstrapMissing

        cfg_path = host.config_dir / "workspace_bootstrap_py.yaml"
        cfg: dict[str, Any] = {}
        if cfg_path.exists():
            loaded = yaml.safe_load(cfg_path.read_text()) or {}
            if isinstance(loaded, dict):
                cfg = loaded

        raw_path = cfg.get("bootstrap_path")
        if raw_path:
            bootstrap_path = Path(str(raw_path)).expanduser()
        else:
            bootstrap_path = Path.home() / ".loam" / "bootstrap.py"

        required = bool(cfg.get("required", False))
        orch = host.require("orchestrator")

        try:
            load_and_register(bootstrap_path, orch)
        except BootstrapMissing as e:
            if required:
                raise AdapterRaisedError(
                    f"workspace_bootstrap_py: {e}",
                    data={"path": str(bootstrap_path), "required": True},
                ) from e
            # Non-required → treat as successful no-op.
            return
        except BootstrapError as e:
            raise AdapterRaisedError(
                f"workspace_bootstrap_py: {e}",
                data={"path": str(bootstrap_path)},
            ) from e
