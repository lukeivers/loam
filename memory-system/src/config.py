"""Central configuration loader for memory-system.

Every deliverable (D5–D13) that has a runtime knob reads its values
from `config/memory.yml`. Workspaces override by editing that file or
pointing `POSV2_MEMORY_CONFIG` at a different path; both are allowed
per spec v1.1 R12 (per-prompt / workspace overridability).

Rationale: a single configuration surface keeps the framework
editable by a non-technical user, at the expense of one indirection
in code. The alternative (environment variables per knob) spreads
configuration across many surfaces and breaks v1.1 R4's "bundled
docs explain configuration" promise.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml


_DEFAULT_CONFIG_PATH = (
    Path(__file__).resolve().parent.parent / "config" / "memory.yml"
)


@lru_cache(maxsize=1)
def load_config(path: str | Path | None = None) -> dict[str, Any]:
    """Load and cache the memory-system config.

    Lookup order: explicit `path` arg -> `POSV2_MEMORY_CONFIG` env var
    -> default packaged path. An unreadable or invalid file raises;
    there is NO silent fallback (silent degradation is a v1.1 R11
    observability failure mode).
    """
    resolved = Path(path or os.environ.get("POSV2_MEMORY_CONFIG") or _DEFAULT_CONFIG_PATH)
    if not resolved.exists():
        raise FileNotFoundError(f"memory config not found: {resolved}")
    with resolved.open("rt", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict):
        raise ValueError(f"memory config root must be a mapping: {resolved}")
    return data


def reload_config() -> dict[str, Any]:
    """Drop the cache and re-read. Tests use this; runtime seldom does."""
    load_config.cache_clear()
    return load_config()


def section(name: str, cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    """Look up a top-level section by name, returning `{}` if absent."""
    cfg = cfg or load_config()
    value = cfg.get(name)
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"config section {name} must be a mapping, got {type(value).__name__}")
    return value
