"""Run the orchestrator as a module: `python -m pos_orchestrator`.

Usage:
    python -m pos_orchestrator                    # defaults (~/.pos/)
    python -m pos_orchestrator --config cfg.yaml  # override paths
    python -m pos_orchestrator --no-bootstrap     # dev/test only

Exit codes:
    0   clean SIGTERM/SIGINT shutdown
    1   crash inside the event loop
    2   workspace bootstrap missing
    3   workspace bootstrap errored
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from .config import OrchestratorConfig, load_config, with_overrides
from .orchestrator import Orchestrator


def _parse_args(argv: list[str]) -> argparse.Namespace:
    ap = argparse.ArgumentParser(prog="pos_orchestrator")
    ap.add_argument("--config", type=str, default=None)
    ap.add_argument(
        "--no-bootstrap",
        action="store_true",
        help="Do not require ~/.pos/bootstrap.py (dev/test only).",
    )
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    ns = _parse_args(sys.argv[1:] if argv is None else argv)
    if ns.config:
        cfg = load_config(ns.config)
    else:
        cfg = OrchestratorConfig()
    if ns.no_bootstrap:
        cfg = with_overrides(cfg, require_bootstrap=False)
    orchestrator = Orchestrator(cfg)
    return asyncio.run(orchestrator.run())


if __name__ == "__main__":
    raise SystemExit(main())
