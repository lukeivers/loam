"""AC.GFLOOR.7 — docs truthful.

Per ``docs/plans/seal-guard-sweep-floor.md`` §4: the loam CLI README
``loam amend`` section and the dev-sdlc amendment-cycle convention
describe the GUARD-SWEEP FLOOR; no live doc still claims
``--scoped-sweep`` exists.
"""

from __future__ import annotations

from pathlib import Path

from loam_amend.paths import find_repo_root


def _repo_root() -> Path:
    return find_repo_root(Path(__file__).parent)


def test_AC_GFLOOR_7_loam_readme_describes_floor_no_scoped_sweep() -> None:
    readme = _repo_root() / "framework" / "tools" / "loam" / "README.md"
    text = readme.read_text(encoding="utf-8")
    assert "GUARD-SWEEP FLOOR" in text
    assert "guard-floor.yaml" in text
    assert "--scoped-sweep" not in text, (
        "the loam README still documents the removed --scoped-sweep "
        "flag (AC.GFLOOR.4 removed it; D-GFLOOR.3)"
    )


def test_AC_GFLOOR_7_loam_amend_cycle_skill_describes_floor() -> None:
    skill = (
        _repo_root()
        / "plugins"
        / "dev-sdlc"
        / "skills"
        / "loam-amend-cycle"
        / "SKILL.md"
    )
    text = skill.read_text(encoding="utf-8")
    assert "GUARD-SWEEP FLOOR" in text
    assert "--scoped-sweep" not in text


def test_AC_GFLOOR_7_amendment_cycle_convention_describes_floor() -> None:
    convention = (
        _repo_root()
        / "plugins"
        / "dev-sdlc"
        / "docs"
        / "conventions"
        / "amendment-cycle.md"
    )
    text = convention.read_text(encoding="utf-8")
    assert "GUARD-SWEEP FLOOR" in text
    assert "guard-floor.yaml" in text
    assert "--scoped-sweep" not in text
