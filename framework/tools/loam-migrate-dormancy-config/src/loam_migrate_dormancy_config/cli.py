"""CLI entry point for the dormancy config-file migration helper.

Console script ``loam-migrate-dormancy-config`` is registered in
``pyproject.toml``. Also runnable as
``python -m loam_migrate_dormancy_config``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .migrate import MigrationResult, migrate_dormancy_config


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="loam-migrate-dormancy-config",
        description=(
            "One-shot per-host migration: ~/.loam/degradation.sqlite → "
            "~/.loam/dormancy.sqlite (with WAL/SHM siblings) and "
            "~/.loam/degradation-config.yaml → "
            "~/.loam/dormancy-config.yaml. Idempotent (re-run is safe "
            "after success). Halts non-zero on conflict (both members "
            "of a file pair present)."
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

    - 0 on cases 1, 2, 3 (clean exit) for both files.
    - 2 if either file pair hits case 4 (conflict).
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    home = Path(args.home) if args.home is not None else None
    result: MigrationResult = migrate_dormancy_config(home=home)

    print(result.combined_message)

    if not result.is_clean:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
