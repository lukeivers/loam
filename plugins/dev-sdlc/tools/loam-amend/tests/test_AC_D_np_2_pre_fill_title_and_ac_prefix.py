"""Tests for AC.D-np.2 — `--title` and `--ac-prefix` pre-fill the
corresponding vars in the scaffolded vars-file.

Per `docs/rebuild/plans/pos-amend-new-plan-orchestration.md`:

    Invoking ``loam amend new-plan <slug> --title "Some Title"
    --ac-prefix AC.X.x`` writes a vars-file whose ``TITLE`` value equals
    ``"Some Title"`` and whose ``AC_PREFIX`` value equals ``"AC.X.x"``.
    Other variables retain their default-stubbed values. ``--title`` and
    ``--ac-prefix`` are independently optional.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from loam_amend.commands import new_plan as new_plan_cmd


def _scaffold(tmp_path: Path, **kwargs) -> dict:
    rc = new_plan_cmd.run("example-slug", repo_root=tmp_path, **kwargs)
    assert rc == 0
    target = tmp_path / "docs" / "rebuild" / "plans" / "example-slug.vars.yaml"
    return yaml.safe_load(target.read_text(encoding="utf-8"))


def test_AC_D_np_2_both_flags_pre_fill_corresponding_vars(
    tmp_path: Path,
) -> None:
    loaded = _scaffold(tmp_path, title="Some Title", ac_prefix="AC.X.x")
    assert loaded["TITLE"] == "Some Title"
    assert loaded["AC_PREFIX"] == "AC.X.x"


def test_AC_D_np_2_only_title_flag_pre_fills_only_title(
    tmp_path: Path,
) -> None:
    loaded = _scaffold(tmp_path, title="Only Title")
    assert loaded["TITLE"] == "Only Title"
    # AC_PREFIX is default-stubbed (empty string per scaffold).
    assert loaded["AC_PREFIX"] == ""


def test_AC_D_np_2_only_ac_prefix_flag_pre_fills_only_ac_prefix(
    tmp_path: Path,
) -> None:
    loaded = _scaffold(tmp_path, ac_prefix="AC.Y.y")
    assert loaded["AC_PREFIX"] == "AC.Y.y"
    assert loaded["TITLE"] == ""


def test_AC_D_np_2_neither_flag_pre_fills_neither(tmp_path: Path) -> None:
    loaded = _scaffold(tmp_path)
    assert loaded["TITLE"] == ""
    assert loaded["AC_PREFIX"] == ""


def test_AC_D_np_2_title_with_special_chars_round_trips_through_yaml(
    tmp_path: Path,
) -> None:
    """A title with embedded double-quotes / backslashes survives the
    YAML round-trip — the scaffold escapes them at write-time so
    ``yaml.safe_load`` reproduces the original string.
    """
    title = 'Has "quotes" and \\backslash'
    loaded = _scaffold(tmp_path, title=title)
    assert loaded["TITLE"] == title
