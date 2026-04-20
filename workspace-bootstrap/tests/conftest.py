"""Shared test fixtures for workspace-bootstrap."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import pytest
import yaml


def write_manifest(path: Path, contributions: list, **extras: Any) -> Path:
    """Write a bootstrap.yaml at `path` with the given contributions list."""
    payload: dict[str, Any] = {
        "version": 1,
        "contributions": contributions,
    }
    payload.update(extras)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(payload))
    return path


@pytest.fixture
def write_manifest_fn() -> Callable[..., Path]:
    return write_manifest


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    """Standard test workspace with config/ and data/ subdirs."""
    (tmp_path / "config").mkdir(parents=True, exist_ok=True)
    (tmp_path / "data").mkdir(parents=True, exist_ok=True)
    return tmp_path
