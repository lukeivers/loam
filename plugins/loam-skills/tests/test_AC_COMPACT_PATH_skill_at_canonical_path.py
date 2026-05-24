"""AC.COMPACT.PATH — strategic-compact SKILL exists at canonical
subdirectory path.

Per ``docs/plans/strategic-compact-skill-graduation.md`` §2: the
SKILL file lives at the discoverable subdirectory shape required
by `_symlink_plugin_skills` (per-directory walk; flat-file shapes
are silently undiscovered per the start-project regression closed
at amendment #147).

This is the structural existence + shape AC. Outcome-altitude
discoverability is AC.COMPACT.S.
"""

from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SKILL_DIR = (
    REPO_ROOT
    / "plugins"
    / "loam-skills"
    / "skills"
    / "strategic-compact"
)
SKILL_MD = SKILL_DIR / "SKILL.md"


def test_AC_COMPACT_PATH_skill_md_at_canonical_subdirectory_path() -> None:
    """The SKILL.md exists at the canonical subdirectory path the
    auto-symlinker (`_symlink_plugin_skills`) walks for discovery.

    The subdirectory shape is the discoverable contract enforced by
    `framework/workspace-bootstrap/src/loam/workspace_bootstrap/
    adapters/first_run_scaffold.py` lines 1262-1267 (per-directory
    walk; flat-file shapes explicitly skipped). Flat-file
    `plugins/loam-skills/skills/strategic-compact.md` would be
    silently undiscovered (the regression that prompted amendment
    #147 for start-project).
    """
    assert SKILL_DIR.is_dir(), (
        f"AC.COMPACT.PATH: expected SKILL directory at {SKILL_DIR}; "
        "the subdirectory shape is the discoverable contract enforced "
        "by `_symlink_plugin_skills` per-directory walk."
    )
    assert SKILL_MD.is_file(), (
        f"AC.COMPACT.PATH: expected SKILL.md file at {SKILL_MD}; "
        "the file must be a regular readable file inside the "
        "subdirectory-shape package."
    )


def test_AC_COMPACT_PATH_no_flat_file_predecessor() -> None:
    """Defensive: no flat-file predecessor at the silent-undiscoverable
    path. If a future change reintroduces the flat-file shape, this
    test catches it before the silent regression ships.
    """
    flat_path = (
        REPO_ROOT
        / "plugins"
        / "loam-skills"
        / "skills"
        / "strategic-compact.md"
    )
    assert not flat_path.exists(), (
        f"AC.COMPACT.PATH: flat-file path {flat_path} must NOT exist; "
        "flat-file shapes are silently undiscovered by "
        "`_symlink_plugin_skills` (per the start-project regression "
        "closed at amendment #147)."
    )
