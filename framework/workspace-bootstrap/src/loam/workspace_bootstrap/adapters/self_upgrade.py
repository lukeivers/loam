"""Adapter — self-upgrade (CLI availability probe).

Phase: after_orchestrator_ready.
Role (per Luke's ruling #3): verify the `pos` self-upgrade CLI is
installed and responsive. This is a readiness check, not a runtime
subscription — if the CLI is broken, the adapter fails-closed so a
workspace cannot silently lose its upgrade primitive.

Eve-inference #4 challenged: the proposal suggested `pos upgrade
--version`. Inspecting the sealed CLI shows `upgrade` is a subcommand
that requires positional `tag` + `--manifest` + `--staging-dir`; it
will not succeed on a bare `--version`. The `pos` parser has no
top-level `--version` either. The probe used here is `pos --help`,
which returns exit 0 when the CLI is importable and argparse-wired.
Workspaces can override via config.

Config (`self_upgrade.yaml` under host.config_dir):
    probe_cmd: list[str] (default: ["pos", "--help"])
    timeout_s: float (default: 5.0)
    required: bool (default: True) — when False, a missing/failing
        CLI is logged but does not fail-close.
"""

from __future__ import annotations

import subprocess
from typing import Any, ClassVar

import yaml

from ..errors import AdapterRaisedError
from ..spec import BaseContribution, ContributionMetadata, Phase


class SelfUpgradeContribution(BaseContribution):
    metadata: ClassVar[ContributionMetadata] = ContributionMetadata(
        name="self_upgrade",
        phase=Phase.after_orchestrator_ready,
    )

    def contribute(self, host) -> None:
        cfg_path = host.config_dir / "self_upgrade.yaml"
        cfg: dict[str, Any] = {}
        if cfg_path.exists():
            loaded = yaml.safe_load(cfg_path.read_text()) or {}
            if isinstance(loaded, dict):
                cfg = loaded

        probe_cmd = cfg.get("probe_cmd") or ["pos", "--help"]
        if not isinstance(probe_cmd, list) or not probe_cmd:
            raise AdapterRaisedError(
                "self_upgrade: probe_cmd must be a non-empty list",
                data={"probe_cmd": probe_cmd},
            )
        timeout = float(cfg.get("timeout_s") or 5.0)
        required = bool(cfg.get("required", True))

        try:
            result = subprocess.run(
                probe_cmd,
                capture_output=True,
                timeout=timeout,
                check=False,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            if required:
                raise AdapterRaisedError(
                    f"self_upgrade: probe {probe_cmd!r} failed: "
                    f"{type(e).__name__}: {e}",
                    data={"probe_cmd": probe_cmd, "error": str(e)},
                ) from e
            return

        if result.returncode != 0:
            if required:
                raise AdapterRaisedError(
                    f"self_upgrade: probe {probe_cmd!r} exited "
                    f"{result.returncode}; stderr: "
                    f"{result.stderr.decode(errors='replace')!r}",
                    data={
                        "probe_cmd": probe_cmd,
                        "exit_code": result.returncode,
                    },
                )
