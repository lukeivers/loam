"""Shared fixtures for loam-mode tests."""

from __future__ import annotations

from pathlib import Path

import pytest


# Post-D.1: this conftest lives at framework/tools/loam-mode/tests/conftest.py
# (4 levels deep from workspace root, not 3).
REPO_ROOT = Path(__file__).resolve().parents[4]
REAL_MANIFEST = REPO_ROOT / "docs" / "rebuild" / "dev-mode-manifest.yaml"


@pytest.fixture
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture
def real_manifest_path() -> Path:
    return REAL_MANIFEST
