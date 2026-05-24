"""AC.TOKEN.S (OUTCOME-ALTITUDE) — Synthetic end-to-end session: a
fresh loam workspace, the cost-optimised-defaults SKILL is
discoverable in the workspace, the production merge entry-point runs
against a tmpfs settings.json with no pre-arranged state, the 4
keys land non-destructively (pre-existing user keys preserved),
and the structured diagnostic surfaces each key written.

Per ``docs/plans/drafts/token-defaults-optin-skill.md`` §4 AC.TOKEN.S
+ ``feedback_test_outcome_altitude_required`` — the test invokes the
production discovery path against a synthetic tmpfs workspace with NO
pre-arranged ``<workspace>/.claude/skills/`` state. The synthetic
workspace stages the canonical multi-plugin SKILL tree via real
``shutil.copytree`` from the on-disk plugin trees — NOT a mocked
file, NOT a stubbed symlinker. Settings.json is staged in a separate
tmpfs path; the production merge.apply is invoked via subprocess
against that path (no in-process mocks of the merge logic).

Mirrors the AC.COMPACT.S precedent at
``plugins/loam-skills/tests/test_AC_COMPACT_S_fresh_workspace_
discoverability.py`` exactly — same multi-plugin canonical-tree
staging, same production entry-point invocation; this test extends
the shape with the settings-merge synthetic end-to-end run.

RED-on-mutation: deleting the SKILL bundle, breaking the merge.py
contract, or moving the SKILL out of its canonical path all break
this test as required.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
PLUGINS_ROOT = REPO_ROOT / "plugins"
CANONICAL_DEV_SDLC_SKILLS = PLUGINS_ROOT / "dev-sdlc" / "skills"
CANONICAL_LOAM_SKILLS_SKILLS = PLUGINS_ROOT / "loam-skills" / "skills"
CANONICAL_COST_OPTIMISED = (
    CANONICAL_LOAM_SKILLS_SKILLS / "cost-optimised-defaults"
)
SKILL_MERGE_PY = CANONICAL_COST_OPTIMISED / "merge.py"


def _import_symlink_function():
    """Import the production `_symlink_plugin_skills` function per
    the AC.COMPACT.S / AC.SPDISC.S convention — pytest-launch-
    independent."""
    src_dir = REPO_ROOT / "framework" / "workspace-bootstrap" / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))
    from loam.workspace_bootstrap.adapters.first_run_scaffold import (
        _symlink_plugin_skills,
    )
    return _symlink_plugin_skills


def _stage_canonical_plugin_skills(workspace: Path) -> None:
    """Mirror the canonical multi-plugin SKILL tree into the synthetic
    workspace under <ws>/plugins/<name>/skills/. Real copytree of
    both plugins' `skills/` trees — no mocks, no stubs."""
    workspace_plugins = workspace / "plugins"
    workspace_plugins.mkdir(parents=True, exist_ok=True)
    if CANONICAL_DEV_SDLC_SKILLS.exists():
        shutil.copytree(
            CANONICAL_DEV_SDLC_SKILLS,
            workspace_plugins / "dev-sdlc" / "skills",
        )
    if CANONICAL_LOAM_SKILLS_SKILLS.exists():
        shutil.copytree(
            CANONICAL_LOAM_SKILLS_SKILLS,
            workspace_plugins / "loam-skills" / "skills",
        )


def _run_merge_subprocess(
    args: list[str],
    settings_path: Path,
) -> dict:
    """Invoke the production merge.py via subprocess; return parsed
    JSON output."""
    result = subprocess.run(
        [
            sys.executable,
            str(SKILL_MERGE_PY),
            "--settings-path",
            str(settings_path),
            *args,
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"AC.TOKEN.S: merge.py invocation failed; "
        f"returncode={result.returncode}, "
        f"stderr={result.stderr!r}, stdout={result.stdout!r}."
    )
    return json.loads(result.stdout)


def test_outcome_altitude_end_to_end_synthetic_session(
    tmp_path: Path,
) -> None:
    """AC.TOKEN.S — full end-to-end synthetic session.

    Stages:
    1. Stage a synthetic workspace (no pre-arranged .claude/skills/).
    2. Invoke the production _symlink_plugin_skills walk against it.
    3. Verify the cost-optimised-defaults SKILL is discoverable in
       the staged workspace via the production discovery path.
    4. Stage a synthetic settings.json with a pre-existing user key.
    5. Invoke the production merge.py `plan` subcommand via
       subprocess against the tmpfs settings.json; verify the
       diff is computed without writing.
    6. Invoke the production merge.py `apply` subcommand via
       subprocess against the tmpfs settings.json; verify the keys
       are written, the user's pre-existing key is preserved, and
       the structured diagnostic names each key written.
    """
    # --- Stage 1: synthetic workspace ---
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    # NO pre-arranged .claude/skills/ — discovery walk creates it.

    _stage_canonical_plugin_skills(workspace)

    # --- Stage 2: production discovery walk ---
    # `_symlink_plugin_skills` takes a single positional argument
    # (workspace_root) and creates `<workspace>/.claude/skills/`
    # internally as part of its walk. Returns a tuple of operator-
    # trace strings naming each SKILL it registered.
    symlink_plugin_skills = _import_symlink_function()
    written = symlink_plugin_skills(workspace)

    # --- Stage 3: SKILL is discoverable in the staged workspace ---
    claude_dir = workspace / ".claude"
    discovered_skill = (
        claude_dir
        / "skills"
        / "cost-optimised-defaults"
        / "SKILL.md"
    )
    assert discovered_skill.exists(), (
        f"AC.TOKEN.S: cost-optimised-defaults/SKILL.md must be "
        f"discoverable in the synthetic workspace via the production "
        f"`_symlink_plugin_skills` walk. Expected at "
        f"{discovered_skill}; not found. (This is the outcome-altitude "
        f"check: fresh workspace + production discovery = SKILL "
        f"reachable.)"
    )
    # And the merge.py helper landed too (symlinked alongside SKILL.md).
    discovered_merge = (
        claude_dir
        / "skills"
        / "cost-optimised-defaults"
        / "merge.py"
    )
    assert discovered_merge.exists(), (
        f"AC.TOKEN.S: merge.py must be discoverable in the staged "
        f"workspace alongside SKILL.md. Expected at "
        f"{discovered_merge}; not found."
    )

    # Operator-trace check: the symlinker's return tuple names the
    # registration so the operator sees the discovery on first run.
    assert any(
        "cost-optimised-defaults" in entry for entry in written
    ), (
        f"AC.TOKEN.S: `_symlink_plugin_skills` return tuple does not "
        f"include cost-optimised-defaults; got {written}. The "
        f"operator-trace surface MUST show the registration."
    )

    # --- Stage 4: synthetic settings.json with pre-existing user key ---
    settings_path = tmp_path / "settings.json"
    pre_existing = {
        "theme": "dark",
        "voice": {"enabled": True},
    }
    settings_path.write_text(
        json.dumps(pre_existing), encoding="utf-8"
    )

    # --- Stage 5: plan subcommand (read-only) ---
    plan_result = _run_merge_subprocess(["plan"], settings_path)
    assert plan_result["settings_path"] == str(settings_path)
    assert plan_result["settings_existed"] is True
    # Plan reports 3 entries (model + 2 env), all NEW.
    statuses = {e["key_path"]: e["status"] for e in plan_result["entries"]}
    assert statuses == {
        "model": "NEW",
        "env.MAX_THINKING_TOKENS": "NEW",
        "env.CLAUDE_AUTOCOMPACT_PCT_OVERRIDE": "NEW",
    }, (
        f"AC.TOKEN.S: plan must classify all 3 recommended keys as "
        f"NEW against a settings file with no recommended keys "
        f"present; got {statuses!r}."
    )
    # Plan is read-only — settings.json is byte-identical post-plan.
    post_plan = json.loads(settings_path.read_text(encoding="utf-8"))
    assert post_plan == pre_existing, (
        "AC.TOKEN.S: `plan` subcommand must be read-only; "
        "settings.json content must be byte-identical post-plan. "
        f"Pre: {pre_existing!r}; Post: {post_plan!r}."
    )

    # --- Stage 6: apply subcommand ---
    apply_result = _run_merge_subprocess(["apply"], settings_path)
    assert apply_result["no_changes"] is False
    assert set(apply_result["keys_written"]) == {
        "model",
        "env.MAX_THINKING_TOKENS",
        "env.CLAUDE_AUTOCOMPACT_PCT_OVERRIDE",
    }, (
        f"AC.TOKEN.S: apply diagnostic must report all 3 recommended "
        f"keys written; got {apply_result['keys_written']!r}."
    )
    assert apply_result["keys_preserved_due_to_conflict"] == []
    # Settings file post-apply: recommended keys merged, user keys
    # preserved.
    post_apply = json.loads(
        settings_path.read_text(encoding="utf-8")
    )
    assert post_apply["theme"] == "dark", (
        "AC.TOKEN.S: pre-existing user key `theme` must be preserved "
        f"post-apply; got {post_apply.get('theme')!r}."
    )
    assert post_apply["voice"] == {"enabled": True}, (
        "AC.TOKEN.S: pre-existing nested user key `voice` must be "
        f"preserved post-apply; got {post_apply.get('voice')!r}."
    )
    assert post_apply["model"] == "sonnet"
    assert post_apply["env"]["MAX_THINKING_TOKENS"] == "10000"
    assert (
        post_apply["env"]["CLAUDE_AUTOCOMPACT_PCT_OVERRIDE"] == "50"
    )
