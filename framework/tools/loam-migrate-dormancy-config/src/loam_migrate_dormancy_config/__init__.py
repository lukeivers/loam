"""loam-migrate-dormancy-config — per-host dormancy config-file migration helper.

One-shot helper relocating dormancy's config-files inside
``~/.loam/`` after the M1f graceful-degradation → dormancy rename:

- ``~/.loam/degradation.sqlite`` → ``~/.loam/dormancy.sqlite``
  (with WAL + SHM siblings).
- ``~/.loam/degradation-config.yaml`` → ``~/.loam/dormancy-config.yaml``.

Per-file four-case logic; idempotent; halts on conflict (both
members of a file pair present). See ``cli.py`` + the package
README for the per-file contract.
"""

from .migrate import (
    FilePairResult,
    FilePairStatus,
    MigrationResult,
    migrate_dormancy_config,
)

__all__ = [
    "FilePairResult",
    "FilePairStatus",
    "MigrationResult",
    "migrate_dormancy_config",
]
