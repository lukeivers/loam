"""loam-migrate-launchd-labels — per-host launchd label migration helper.

One-shot per-host helper that bootouts pre-M1c
``com.pos-v2.<slug>.<kind>`` launchd labels and renames the plist
files aside (to ``<base>.label-rebrand-disabled.bak``). Lands per
M1c sub-amendment of the M1.rename multi-amendment series. See the
package README for the full contract.

Sibling to ``loam-migrate-host-config`` (M1b's per-host config dir
helper). Distinct surface; same single-purpose-helper pattern.
"""

from .migrate import (
    BootoutResult,
    MigrationOutcome,
    MigrationResult,
    migrate_launchd_labels,
)

__all__ = [
    "BootoutResult",
    "MigrationOutcome",
    "MigrationResult",
    "migrate_launchd_labels",
]
