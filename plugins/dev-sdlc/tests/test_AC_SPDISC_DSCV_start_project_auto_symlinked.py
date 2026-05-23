"""AC.SPDISC.DSCV — `start-project` SKILL is auto-discoverable via
`_symlink_plugin_skills` post-promotion to subdirectory shape.

**OUTCOME-ALTITUDE** per `feedback_test_outcome_altitude_required`:
invokes the production entry-point `_symlink_plugin_skills(workspace)`
against a synthetic tmpfs workspace with NO pre-arranged
`<workspace>/.claude/skills/` state. The synthetic workspace stages
the canonical plugin SKILL by copying the actual on-disk
`plugins/dev-sdlc/skills/start-project/SKILL.md` content into the
tmpfs plugin tree — NOT a mocked file, NOT a stubbed symlinker.

RED-on-mutation: temporarily reverting the `git mv` would leave the
canonical tree with a flat-file `start-project.md` and no
`start-project/SKILL.md`; the test's copy step would then either
copy the flat-file into a subdirectory shape (still GREEN — testing
the symlinker against staged data) OR fail to find the source file
(RED). To prevent the first case from masking a real regression, the
test sources the staged file from the canonical layout
`plugins/dev-sdlc/skills/start-project/SKILL.md` directly: if the
canonical tree doesn't have the subdirectory shape, the test fails
at the file-not-found step.

Closes the gap AC.OSS-M6.9's text always required ("discoverable +
invocable") but the original test never delivered (file-existence
+ frontmatter + manual reader-fall-through simulation only).

Ladder: AC.SPDISC.DSCV (outcome-altitude) → AC.OSS-M6.9
("discoverable + invocable" contract from v0.1.0) → AC.LAYERED.2
(the auto-symlinker mechanism) → AC.PO.1 (translation-burden
reduction: the SKILL becomes intent-routable from the user's first
click).
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
CANONICAL_SKILL_DIR = (
    REPO_ROOT
    / "plugins"
    / "dev-sdlc"
    / "skills"
    / "start-project"
)
CANONICAL_SKILL_MD = CANONICAL_SKILL_DIR / "SKILL.md"


def _import_symlink_function():
    """Import `_symlink_plugin_skills` from its canonical location.

    The function lives at
    `framework/workspace-bootstrap/src/loam/workspace_bootstrap/adapters/first_run_scaffold.py`.
    Add the package's `src` dir to sys.path if needed so the import
    succeeds in tree-walking test invocations regardless of how
    pytest is launched (component-local or top-level).
    """
    src_dir = REPO_ROOT / "framework" / "workspace-bootstrap" / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))
    from loam.workspace_bootstrap.adapters.first_run_scaffold import (
        _symlink_plugin_skills,
    )
    return _symlink_plugin_skills


def test_AC_SPDISC_DSCV_start_project_symlinked_into_workspace_skills(
    tmp_path: Path,
) -> None:
    """OUTCOME-ALTITUDE: invoke `_symlink_plugin_skills` against a
    synthetic workspace and assert the start-project SKILL is
    discoverable at `<workspace>/.claude/skills/start-project/SKILL.md`.

    No mock; no stub; no pre-arranged `.claude/skills/` state. The
    workspace's plugins/ tree stages the canonical start-project
    SKILL package via real shutil.copytree from the canonical loam
    on-disk source — exercising the production walk-and-symlink path
    end-to-end.
    """
    # Tier-0 sanity: the canonical subdirectory-shape source MUST
    # exist for this test to be meaningful. If A-PROMOTE-START-PROJECT
    # is reverted (git mv undone), this assertion catches it.
    assert CANONICAL_SKILL_MD.is_file(), (
        f"canonical SKILL.md not found at {CANONICAL_SKILL_MD}; "
        "A-PROMOTE-START-PROJECT requires the subdirectory-shape "
        "SKILL be present in the canonical tree. The flat-shape "
        "predecessor at plugins/dev-sdlc/skills/start-project.md is "
        "not Anthropic-discoverable (per-directory walk only)."
    )

    # Build a synthetic workspace mirroring the canonical layout.
    workspace = tmp_path / "ws"
    workspace.mkdir()
    plugin_skills = workspace / "plugins" / "dev-sdlc" / "skills"
    plugin_skills.mkdir(parents=True)
    # Real copytree from the canonical on-disk source — not a mocked
    # file, not a stubbed frontmatter. The synthetic workspace's
    # plugin tree carries an exact replica of the production SKILL.
    shutil.copytree(
        CANONICAL_SKILL_DIR,
        plugin_skills / "start-project",
    )

    # Invoke the production entry-point — no pre-arranged
    # `<workspace>/.claude/skills/` state. The function creates the
    # `.claude/skills/` directory and the symlink as part of its
    # walk.
    symlink_fn = _import_symlink_function()
    written = symlink_fn(workspace)

    # Outcome assertions — the SKILL is reachable at the
    # Anthropic-discoverable path through the symlinker's work.
    skills_dir = workspace / ".claude" / "skills"
    start_project_link = skills_dir / "start-project"
    start_project_skill = start_project_link / "SKILL.md"

    assert start_project_link.is_symlink(), (
        f"expected {start_project_link} to be a symlink created by "
        "_symlink_plugin_skills; the production auto-symlinker MUST "
        "register start-project for AC.SPDISC.DSCV (outcome-altitude)."
    )
    assert start_project_skill.is_file(), (
        f"expected {start_project_skill} to resolve through the "
        "symlink to a readable SKILL.md; the resolved file IS the "
        "discoverability outcome the test asserts."
    )
    # The function's return tuple records the symlink registration.
    assert "<workspace>/.claude/skills/start-project" in written, (
        f"expected `_symlink_plugin_skills` return tuple to record "
        f"the start-project registration; got {written}."
    )

    # Body sanity — readable through the symlink, content matches
    # the canonical source.
    body = start_project_skill.read_text(encoding="utf-8")
    canonical_body = CANONICAL_SKILL_MD.read_text(encoding="utf-8")
    assert body == canonical_body, (
        "SKILL.md content reachable through the symlink must match "
        "the canonical on-disk source byte-for-byte."
    )
