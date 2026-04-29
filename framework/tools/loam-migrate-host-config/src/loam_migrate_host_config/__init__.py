"""loam-migrate-host-config — per-host config dir migration helper.

One-shot helper relocating ``~/.pos/`` to ``~/.loam/``. Idempotent;
halts on conflict (both dirs present). See ``cli.py`` + the package
README for the four-case contract.
"""

from .migrate import (
    MigrationResult,
    MigrationStatus,
    migrate_host_config,
)

__all__ = [
    "MigrationResult",
    "MigrationStatus",
    "migrate_host_config",
]
