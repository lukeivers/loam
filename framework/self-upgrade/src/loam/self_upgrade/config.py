"""Workspace upgrade config — ``~/.loam/upgrade-config.yaml``.

Schema (all keys optional; defaults below):

.. code-block:: yaml

    auto_update_mode: require_confirmation   # or notify_and_apply
    drain_timeout_seconds: 30
    sigterm_timeout_seconds: 30
    orchestrator_boot_timeout_seconds: 60
    cancel_window_seconds: 60                # notify_and_apply only
    confirmation_timeout_hours: 24           # require_confirmation only
    launchd_label: com.pos.orchestrator
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field


class AutoUpdateMode(str, Enum):
    REQUIRE_CONFIRMATION = "require_confirmation"
    NOTIFY_AND_APPLY = "notify_and_apply"


class UpgradeConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    auto_update_mode: AutoUpdateMode = AutoUpdateMode.REQUIRE_CONFIRMATION
    drain_timeout_seconds: float = 30.0
    sigterm_timeout_seconds: float = 30.0
    orchestrator_boot_timeout_seconds: float = 60.0
    cancel_window_seconds: float = 60.0
    confirmation_timeout_hours: float = 24.0
    launchd_label: str = "com.pos.orchestrator"

    @classmethod
    def load_or_default(cls, path: str | Path) -> "UpgradeConfig":
        p = Path(path)
        if not p.exists():
            return cls()
        raw = yaml.safe_load(p.read_text()) or {}
        return cls.model_validate(raw)

    def save(self, path: str | Path) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            yaml.safe_dump(
                self.model_dump(mode="json"),
                default_flow_style=False,
                sort_keys=False,
            )
        )
