"""CLI entry point for the migration helper.

Console script ``loam-migrate-host-config`` is registered in
``pyproject.toml``. Also runnable as ``python -m loam_migrate_host_config``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .migrate import MigrationStatus, migrate_host_config


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="loam-migrate-host-config",
        description=(
            "One-shot per-host migration: ~/.pos/ → ~/.loam/. "
            "Idempotent (re-run is safe after success). "
            "Halts non-zero on conflict (both dirs present)."
        ),
    )
    parser.add_argument(
        "--home",
        default=None,
        help=(
            "Override the home directory the helper migrates under. "
            "Default: the calling process's $HOME (Path.home()). "
            "Test/override hook only."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point. Returns the process exit code.

    - 0 on cases 1, 2, 3 (clean exit).
    - 2 on case 4 (conflict; user must resolve manually).
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    home = Path(args.home) if args.home is not None else None
    result = migrate_host_config(home=home)

    print(result.message)

    if result.status is MigrationStatus.CONFLICT:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
