"""Shared fixtures for loam-mode tests."""

from __future__ import annotations

from pathlib import Path

import pytest


# Post-M6b.0: this conftest lives at
# plugins/dev-sdlc/tools/loam-mode/tests/conftest.py (5 levels deep
# from workspace root). Pre-M6b.0 it lived at
# framework/tools/loam-mode/tests/conftest.py (4 levels deep).
REPO_ROOT = Path(__file__).resolve().parents[5]
REAL_MANIFEST = REPO_ROOT / "plugins" / "dev-sdlc" / "dev-mode-manifest.yaml"


@pytest.fixture
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture
def real_manifest_path() -> Path:
    return REAL_MANIFEST
