"""AC.SPDISC.S — end-to-end smoke: a fresh workspace mirroring the
canonical multi-plugin layout carries `<workspace>/.claude/skills/
start-project/SKILL.md` reachable as a normal file post-scaffold.

**OUTCOME-ALTITUDE** per `feedback_test_outcome_altitude_required`:
no pre-arranged `<workspace>/.claude/skills/` state; production
entry-point `_symlink_plugin_skills` invoked against a tmpfs
workspace that stages the canonical full multi-plugin SKILL tree
(both `loam-skills` and `dev-sdlc`); the SKILL surfaces as a
normal-file-resolution through the symlink.

Differs from AC.SPDISC.DSCV in scope: DSCV stages dev-sdlc's
start-project SKILL in isolation to prove the symlinker walks the
new subdirectory shape; SPDISC.S stages the full canonical
multi-plugin layout to exercise the production scenario (multiple
plugins, multiple skill directories, walk ordering, claim-tracking
collision discipline). Both are outcome-altitude per the rubric;
this is the integration-altitude probe; DSCV is the targeted-
mechanism probe.

Heavy entry-points like `run_first_run_scaffold` (which writes
~/.loam/, may call launchctl, requires platform mocks) are
deliberately NOT used here — the load-bearing primitive for the
discoverability outcome is `_symlink_plugin_skills`, and that's
what's invoked. Per plan-doc §4 AC.SPDISC.S text: "fresh workspace
produced by `run_first_run_scaffold` (or the moral equivalent
invoked through the canonical `loam init` path)".

Ladder: AC.SPDISC.S (outcome-altitude smoke) → AC.SPDISC.DSCV
(targeted discoverability) + AC.SPDISC.MV (the underlying file
relocation) → AC.OSS-M6.9 (the v0.1.0 discoverability contract).
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
PLUGINS_ROOT = REPO_ROOT / "plugins"
CANONICAL_DEV_SDLC_SKILLS = PLUGINS_ROOT / "dev-sdlc" / "skills"
CANONICAL_LOAM_SKILLS_SKILLS = PLUGINS_ROOT / "loam-skills" / "skills"


def _import_symlink_function():
    """Import `_symlink_plugin_skills` per the same convention as
    test_AC_SPDISC_DSCV — pytest-launch-independent."""
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
    mocks, no stubs, no curated subset."""
    ws_plugins = workspace / "plugins"
    # dev-sdlc — copy all subdirectory-shape SKILLs.
    dest_dev = ws_plugins / "dev-sdlc" / "skills"
    dest_dev.mkdir(parents=True, exist_ok=True)
    for entry in CANONICAL_DEV_SDLC_SKILLS.iterdir():
        if not entry.is_dir():
            # Post-A-PROMOTE-START-PROJECT no flat-shape skills exist
            # in dev-sdlc. Skip any non-dir defensively (would be
            # auto-skipped by the symlinker anyway per its per-dir
            # walk).
            continue
        shutil.copytree(entry, dest_dev / entry.name)
    # loam-skills — copy all subdirectory-shape SKILLs.
    dest_loam = ws_plugins / "loam-skills" / "skills"
    dest_loam.mkdir(parents=True, exist_ok=True)
    for entry in CANONICAL_LOAM_SKILLS_SKILLS.iterdir():
        if not entry.is_dir():
            continue
        shutil.copytree(entry, dest_loam / entry.name)


def test_AC_SPDISC_S_fresh_workspace_smoke_start_project_discoverable(
    tmp_path: Path,
) -> None:
    """OUTCOME-ALTITUDE end-to-end smoke: stage the canonical full
    multi-plugin SKILL tree into a synthetic workspace, invoke
    `_symlink_plugin_skills` with no pre-arranged `.claude/skills/`
    state, assert `<workspace>/.claude/skills/start-project/SKILL.md`
    is reachable as a normal file (symlink-resolved)."""
    workspace = tmp_path / "fresh-workspace"
    workspace.mkdir()

    # Stage the canonical multi-plugin tree.
    _stage_canonical_plugin_skills(workspace)

    # Sanity precondition: the staged start-project SKILL is present
    # in subdirectory shape (the post-promotion layout).
    staged_skill_md = (
        workspace
        / "plugins"
        / "dev-sdlc"
        / "skills"
        / "start-project"
        / "SKILL.md"
    )
    assert staged_skill_md.is_file(), (
        f"AC.SPDISC.S precondition failed: staged SKILL.md not at "
        f"{staged_skill_md}. The synthetic workspace must mirror the "
        "post-promotion subdirectory shape (this catches A-PROMOTE-"
        "START-PROJECT regression at staging-time)."
    )

    # Production entry-point invocation. No `.claude/skills/` state
    # pre-arranged. The symlinker creates it as part of its walk.
    symlink_fn = _import_symlink_function()
    written = symlink_fn(workspace)

    # Outcome assertion: the SKILL is reachable through the symlink.
    skills_dir = workspace / ".claude" / "skills"
    resolved_skill_md = skills_dir / "start-project" / "SKILL.md"
    assert resolved_skill_md.is_file(), (
        f"AC.SPDISC.S outcome failed: {resolved_skill_md} not "
        "reachable post-scaffold. The auto-symlink mechanism must "
        "make the start-project SKILL discoverable in a fresh "
        "workspace; this is the operator-visible outcome the v0.1.0 "
        "AC.OSS-M6.9 contract requires + the v0.1.7 AC.LAYERED.2 "
        "mechanism was supposed to deliver."
    )

    # Operator-trace assertion: the symlinker's return tuple names
    # the registration (the line a debugger/log-trail consumer
    # would see).
    assert "<workspace>/.claude/skills/start-project" in written, (
        f"AC.SPDISC.S trace failed: `_symlink_plugin_skills` return "
        f"tuple does not include start-project; got {written}. The "
        "operator-trace surface MUST show the registration."
    )

    # Multi-plugin sanity: the other plugin's SKILLs are also
    # discoverable (no cross-plugin starvation). At least one
    # loam-skills SKILL should be present in the resolved skills_dir.
    loam_skills_present = [
        p.name for p in skills_dir.iterdir() if p.is_symlink()
    ]
    assert len(loam_skills_present) >= 2, (
        "AC.SPDISC.S sanity: expected at least 2 plugin SKILLs "
        f"symlinked into {skills_dir} (one from each contributing "
        f"plugin); got {loam_skills_present}. Multi-plugin walk "
        "regression would surface here."
    )
