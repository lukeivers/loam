"""AC.OSS-M6.3 — `--methodology=tdd|bdd|adhoc` opt-out preserves
an internal ODD mirror.

Per plan §4 AC.OSS-M6.3: non-ODD methodologies write
`<project>/.dev-sdlc-odd-mirror.yaml` containing the plugin's
internal ODD representation.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from loam.plugins.dev_sdlc import api
from loam.plugins.dev_sdlc.errors import UnsupportedMethodologyError


def test_tdd_opt_out_writes_odd_mirror(tmp_path: Path) -> None:
    api.start_project(
        slug="tdd-proj", methodology="tdd", workspace_root=tmp_path
    )
    proj_root = tmp_path / "projects" / "tdd-proj"
    user_yaml = proj_root / ".dev-sdlc.yaml"
    odd_mirror = proj_root / ".dev-sdlc-odd-mirror.yaml"
    assert user_yaml.is_file()
    user = yaml.safe_load(user_yaml.read_text(encoding="utf-8"))
    assert user["methodology"] == "tdd"
    assert odd_mirror.is_file()
    mirror = yaml.safe_load(odd_mirror.read_text(encoding="utf-8"))
    assert mirror["slug"] == "tdd-proj"
    assert "stages" in mirror
    assert mirror["stages"] == [
        "research",
        "spec",
        "plan",
        "build",
        "review",
    ]
    assert "objective" in mirror


def test_bdd_opt_out_writes_odd_mirror(tmp_path: Path) -> None:
    api.start_project(
        slug="bdd-proj", methodology="bdd", workspace_root=tmp_path
    )
    proj_root = tmp_path / "projects" / "bdd-proj"
    assert (proj_root / ".dev-sdlc-odd-mirror.yaml").is_file()


def test_adhoc_opt_out_writes_odd_mirror(tmp_path: Path) -> None:
    api.start_project(
        slug="adhoc-proj",
        methodology="adhoc",
        workspace_root=tmp_path,
    )
    proj_root = tmp_path / "projects" / "adhoc-proj"
    assert (proj_root / ".dev-sdlc-odd-mirror.yaml").is_file()


def test_odd_methodology_does_not_write_mirror(tmp_path: Path) -> None:
    """ODD methodology has no mirror — the user-visible artefacts are
    already ODD-shaped."""
    api.start_project(
        slug="odd-proj", methodology="odd", workspace_root=tmp_path
    )
    proj_root = tmp_path / "projects" / "odd-proj"
    assert not (proj_root / ".dev-sdlc-odd-mirror.yaml").exists()


def test_unsupported_methodology_raises(tmp_path: Path) -> None:
    with pytest.raises(UnsupportedMethodologyError):
        api.start_project(
            slug="x",
            methodology="waterfall",
            workspace_root=tmp_path,
        )
