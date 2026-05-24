"""AC.COMPACT.S — OUTCOME-ALTITUDE: a fresh loam workspace produced
via the production `_symlink_plugin_skills` walk carries the
`strategic-compact` SKILL discoverable + invocable.

Per ``docs/plans/strategic-compact-skill-graduation.md`` §2 +
`feedback_test_outcome_altitude_required.md`: the test invokes the
production discovery path against a synthetic tmpfs workspace with
no pre-arranged `<workspace>/.claude/skills/` state. The synthetic
workspace stages the canonical multi-plugin SKILL tree (loam-
skills + dev-sdlc) via real shutil.copytree from the on-disk
plugin trees — NOT a mocked file, NOT a stubbed symlinker.

The test mirrors the AC.SPDISC.S shape from amendment #147
(start-project discoverability smoke at
`plugins/dev-sdlc/tests/test_AC_SPDISC_S_fresh_workspace_
discoverability.py`) — same multi-plugin canonical-tree staging,
same production entry-point invocation, same outcome-shape
assertion that the SKILL is reachable through the symlink as a
normal-file-resolution.

RED-on-mutation: reverting the SKILL move (deleting the
`plugins/loam-skills/skills/strategic-compact/` directory) leaves
the canonical tree without the staged SKILL; the test's copy step
then has nothing to copy and the outcome assertion fails — the
mutation breaks the test as required.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
PLUGINS_ROOT = REPO_ROOT / "plugins"
CANONICAL_DEV_SDLC_SKILLS = PLUGINS_ROOT / "dev-sdlc" / "skills"
CANONICAL_LOAM_SKILLS_SKILLS = PLUGINS_ROOT / "loam-skills" / "skills"
CANONICAL_STRATEGIC_COMPACT = (
    CANONICAL_LOAM_SKILLS_SKILLS / "strategic-compact"
)


def _import_symlink_function():
    """Import `_symlink_plugin_skills` per the AC.SPDISC.S /
    AC.SPDISC.DSCV convention — pytest-launch-independent."""
    src_dir = REPO_ROOT / "framework" / "workspace-bootstrap" / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))
    from loam.workspace_bootstrap.adapters.first_run_scaffold import (
        _symlink_plugin_skills,
    )
    return _symlink_plugin_skills


def _stage_canonical_plugin_skills(workspace: Path) -> None:
    """Mirror the canonical multi-plugin SKILL tree into the synthetic
    workspace. Real copytree of both plugins' `skills/` trees — no
    mocks, no stubs, no curated subset. Mirrors the AC.SPDISC.S
    stage-shape exactly so both smokes exercise the same canonical
    layout against the same production entry-point.
    """
    ws_plugins = workspace / "plugins"
    dest_dev = ws_plugins / "dev-sdlc" / "skills"
    dest_dev.mkdir(parents=True, exist_ok=True)
    for entry in CANONICAL_DEV_SDLC_SKILLS.iterdir():
        if not entry.is_dir():
            continue
        shutil.copytree(entry, dest_dev / entry.name)
    dest_loam = ws_plugins / "loam-skills" / "skills"
    dest_loam.mkdir(parents=True, exist_ok=True)
    for entry in CANONICAL_LOAM_SKILLS_SKILLS.iterdir():
        if not entry.is_dir():
            continue
        shutil.copytree(entry, dest_loam / entry.name)


def test_AC_COMPACT_S_fresh_workspace_smoke_strategic_compact_discoverable(
    tmp_path: Path,
) -> None:
    """OUTCOME-ALTITUDE end-to-end smoke: stage the canonical full
    multi-plugin SKILL tree into a synthetic workspace, invoke
    `_symlink_plugin_skills` with no pre-arranged `.claude/skills/`
    state, assert `<workspace>/.claude/skills/strategic-compact/
    SKILL.md` is reachable as a normal file (symlink-resolved).
    """
    # Tier-0 sanity: the canonical subdirectory-shape source MUST
    # exist for this smoke to be meaningful. If a future change
    # reverts the SKILL move, this assertion catches the regression
    # at staging-time before the outcome-altitude check (RED-on-
    # mutation discipline per `feedback_test_outcome_altitude_
    # required.md`).
    assert (CANONICAL_STRATEGIC_COMPACT / "SKILL.md").is_file(), (
        f"AC.COMPACT.S precondition failed: canonical SKILL.md not "
        f"found at {CANONICAL_STRATEGIC_COMPACT / 'SKILL.md'}. The "
        "subdirectory-shape SKILL must be present in the canonical "
        "tree for the auto-symlinker walk to discover it (the "
        "regression mode this AC closes)."
    )

    workspace = tmp_path / "fresh-workspace"
    workspace.mkdir()

    # Stage the canonical multi-plugin tree.
    _stage_canonical_plugin_skills(workspace)

    # Sanity precondition: the staged strategic-compact SKILL is
    # present in subdirectory shape (the discoverable layout).
    staged_skill_md = (
        workspace
        / "plugins"
        / "loam-skills"
        / "skills"
        / "strategic-compact"
        / "SKILL.md"
    )
    assert staged_skill_md.is_file(), (
        f"AC.COMPACT.S precondition failed: staged SKILL.md not at "
        f"{staged_skill_md}. The synthetic workspace must mirror the "
        "subdirectory shape (catches staging-time regression in the "
        "test setup)."
    )

    # Production entry-point invocation. No `.claude/skills/` state
    # pre-arranged. The symlinker creates it as part of its walk.
    symlink_fn = _import_symlink_function()
    written = symlink_fn(workspace)

    # Outcome assertion: the SKILL is reachable through the symlink
    # as a normal-file-resolution. This is the operator-visible
    # outcome — the SKILL must be discoverable + load-able via
    # Claude Code's filesystem walk against `<workspace>/.claude/
    # skills/`.
    skills_dir = workspace / ".claude" / "skills"
    strategic_compact_link = skills_dir / "strategic-compact"
    strategic_compact_skill = strategic_compact_link / "SKILL.md"

    assert strategic_compact_link.is_symlink(), (
        f"AC.COMPACT.S outcome failed: expected {strategic_compact_link} "
        "to be a symlink created by `_symlink_plugin_skills`; the "
        "production auto-symlinker MUST register strategic-compact "
        "for the graduation outcome to land."
    )
    assert strategic_compact_skill.is_file(), (
        f"AC.COMPACT.S outcome failed: {strategic_compact_skill} not "
        "reachable post-scaffold. The auto-symlink mechanism must "
        "make the strategic-compact SKILL discoverable in a fresh "
        "workspace; this is the operator-visible outcome the "
        "graduation requires."
    )

    # Operator-trace assertion: the symlinker's return tuple names
    # the registration (the line a debugger/log-trail consumer
    # would see).
    assert (
        "<workspace>/.claude/skills/strategic-compact" in written
    ), (
        f"AC.COMPACT.S trace failed: `_symlink_plugin_skills` return "
        f"tuple does not include strategic-compact; got {written}. "
        "The operator-trace surface MUST show the registration."
    )

    # Multi-plugin sanity: other loam-skills SKILLs + dev-sdlc SKILLs
    # are also discoverable (no cross-plugin starvation introduced
    # by the new SKILL). At least 10 plugin SKILLs should be
    # symlinked across the two contributing plugins (loam-skills
    # alone ships 20+ SKILLs at amendment time per the AC.LSK family;
    # multi-plugin regression would surface here).
    discovered_symlinks = [
        p.name for p in skills_dir.iterdir() if p.is_symlink()
    ]
    assert len(discovered_symlinks) >= 10, (
        "AC.COMPACT.S sanity: expected at least 10 plugin SKILLs "
        f"symlinked into {skills_dir}; got {len(discovered_symlinks)}: "
        f"{discovered_symlinks}. Multi-plugin walk regression would "
        "surface here."
    )

    # Body sanity — readable through the symlink, content matches
    # the canonical on-disk source byte-for-byte.
    body = strategic_compact_skill.read_text(encoding="utf-8")
    canonical_body = (
        CANONICAL_STRATEGIC_COMPACT / "SKILL.md"
    ).read_text(encoding="utf-8")
    assert body == canonical_body, (
        "AC.COMPACT.S: SKILL.md content reachable through the "
        "symlink must match the canonical on-disk source byte-for-"
        "byte (symlink resolves to the canonical file, not a copy "
        "or a stale snapshot)."
    )
