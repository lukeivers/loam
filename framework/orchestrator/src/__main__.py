"""Run the orchestrator as a module: `python -m pos_orchestrator`.

Usage:
    python -m pos_orchestrator                    # defaults (~/.loam/)
    python -m pos_orchestrator --config cfg.yaml  # override paths

Workspace bootstrap (``~/.loam/bootstrap.py``) is loaded by the
workspace-bootstrap framework's ``WorkspaceBootstrapPyContribution``
adapter — not by this entry point. See
docs/rebuild/components/orchestrator-bootstrap-unification/proposal.md
(amendment #7). The ``--no-bootstrap`` flag that previously toggled the
direct loader call was removed because the adapter's default is
non-required and the flag no longer had a job.

Exit codes:
    0   clean SIGTERM/SIGINT shutdown
    1   crash inside the event loop
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from .config import OrchestratorConfig, load_config
from .orchestrator import Orchestrator


def _parse_args(argv: list[str]) -> argparse.Namespace:
    ap = argparse.ArgumentParser(prog="pos_orchestrator")
    ap.add_argument("--config", type=str, default=None)
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    ns = _parse_args(sys.argv[1:] if argv is None else argv)
    if ns.config:
        cfg = load_config(ns.config)
    else:
        cfg = OrchestratorConfig()
    orchestrator = Orchestrator(cfg)
    return asyncio.run(orchestrator.run())


if __name__ == "__main__":
    raise SystemExit(main())
