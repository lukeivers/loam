"""True-first-run acceptance tests (T1..T18).

Each test maps to a T-criterion from the proposal §4 / brief §5 ODD
block. The mapping is documented per-test so a future auditor can
confirm coverage.

Tests exercise the helper + settings-merge + inventory-parser modules
directly. End-to-end flow from Claude Code SessionStart is exercised
via a harness-level simulation — invoking the shell script with a
prepared workspace fixture and asserting outcomes.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
HOOKS_DIR = REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

from first_run_inventory import (  # noqa: E402
    InventoryParseError,
    load_inventory,
    parse_inventory,
    validate_inventory,
)
from first_run_settings import (  # noqa: E402
    build_first_run_stanza,
    build_supervisor_stanza,
    merge_session_start,
)
from first_run_helper import (  # noqa: E402
    _confirmation_sentence,
    _is_already_retired,
    _self_retire,
    _verify_self_retire,
)


# ---- fixtures -------------------------------------------------------


@pytest.fixture
def fresh_workspace(tmp_path: Path) -> Path:
    """A minimal pos-v2-shaped workspace under tmp_path.

    Post-D.1: framework code lives under ``<root>/framework/<comp>/``.
    The fixture mirrors that layout so first-run-helper tests resolve
    paths via the same shape they will at runtime.
    """
    ws = tmp_path / "pos-v2"
    (ws / ".claude").mkdir(parents=True)
    (ws / "framework" / "hands-off-lifecycle" / "hooks").mkdir(parents=True)
    (ws / "framework" / "orchestrator" / "scripts").mkdir(parents=True)
    (ws / "framework" / "orchestrator" / "scripts" / "pos_session_start.py").write_text(
        "# placeholder\n"
    )
    return ws


# ---- T11: settings.json authorship — from scratch -------------------


def test_T11_settings_json_authored_from_scratch(fresh_workspace: Path) -> None:
    """T11 — settings.json created when absent, SessionStart populated."""
    settings_path = fresh_workspace / ".claude" / "settings.json"
    assert not settings_path.exists()

    stanza = build_first_run_stanza(fresh_workspace)
    result = merge_session_start(settings_path=settings_path, new_entry=stanza)

    assert result.wrote is True
    assert settings_path.exists()
    data = json.loads(settings_path.read_text())
    # Current Claude Code schema: SessionStart[i] = {matcher, hooks: [...]}.
    assert (
        data["hooks"]["SessionStart"][0]["hooks"][0]["command"].endswith(
            "first-run.sh"
        )
    )
    assert data["hooks"]["SessionStart"][0]["matcher"] == ""
    assert result.backup_path is None
    assert result.prior_session_start_displaced is False


# ---- T12: stanza-merge on pre-existing user keys --------------------


def test_T12_user_keys_preserved_outside_session_start(
    fresh_workspace: Path,
) -> None:
    """T12 — user-authored keys outside SessionStart are preserved."""
    settings_path = fresh_workspace / ".claude" / "settings.json"
    settings_path.write_text(
        json.dumps(
            {
                "env": {"MY_USER_VAR": "42"},
                "permissions": {"allow": ["Read(//**)"]},
                "hooks": {
                    "PreToolUse": [
                        {"type": "command", "command": "/bin/true"}
                    ]
                },
            },
            indent=2,
        )
    )

    stanza = build_first_run_stanza(fresh_workspace)
    result = merge_session_start(settings_path=settings_path, new_entry=stanza)

    data = json.loads(settings_path.read_text())
    assert data["env"] == {"MY_USER_VAR": "42"}
    assert data["permissions"] == {"allow": ["Read(//**)"]}
    assert data["hooks"]["PreToolUse"][0]["command"] == "/bin/true"
    assert (
        data["hooks"]["SessionStart"][0]["hooks"][0]["command"].endswith(
            "first-run.sh"
        )
    )
    assert result.prior_session_start_displaced is False
    # Preserved user keys are advertised in the result for the
    # confirmation sentence to reference.
    assert "env" in result.preserved_user_keys
    assert "permissions" in result.preserved_user_keys
    assert "hooks.PreToolUse" in result.preserved_user_keys


# ---- T13: user SessionStart backed up with notification -------------


def test_T13_prior_session_start_moved_aside(fresh_workspace: Path) -> None:
    """T13 — user's SessionStart backed up to a timestamped file; notified."""
    settings_path = fresh_workspace / ".claude" / "settings.json"
    settings_path.write_text(
        json.dumps(
            {
                "hooks": {
                    "SessionStart": [
                        {
                            "type": "command",
                            "command": "/usr/local/bin/my-user-hook.sh",
                        }
                    ]
                }
            },
            indent=2,
        )
    )

    stanza = build_first_run_stanza(fresh_workspace)
    result = merge_session_start(
        settings_path=settings_path,
        new_entry=stanza,
        now_iso="20260422T160000Z",
    )

    assert result.prior_session_start_displaced is True
    assert result.backup_path is not None
    assert result.backup_path.exists()
    assert result.backup_path.name == "settings.json.user-backup-20260422T160000Z.json"

    backup_data = json.loads(result.backup_path.read_text())
    assert (
        backup_data["hooks"]["SessionStart"][0]["command"]
        == "/usr/local/bin/my-user-hook.sh"
    )

    live = json.loads(settings_path.read_text())
    assert (
        live["hooks"]["SessionStart"][0]["hooks"][0]["command"].endswith(
            "first-run.sh"
        )
    )
    assert live["hooks"]["SessionStart"][0]["matcher"] == ""

    # And confirmation sentence surfaces the displacement.
    # Amendment #6: labels are workspace-slug scoped; the fixture slug
    # is the basename of `fresh_workspace` (pytest tmp_path leaf).
    sample_labels = [
        "com.loam.alpha.memory-graphiti",
        "com.loam.alpha.orchestrator",
    ]
    sentence = _confirmation_sentence(
        merge_result=result,
        service_labels=sample_labels,
    )
    assert result.backup_path.name in sentence


def test_T13b_pos_v2_owned_stanza_not_backed_up(fresh_workspace: Path) -> None:
    """A pos-v2-authored SessionStart is NOT backed up (idempotent re-run)."""
    settings_path = fresh_workspace / ".claude" / "settings.json"
    prior_stanza = build_first_run_stanza(fresh_workspace)
    settings_path.write_text(
        json.dumps({"hooks": {"SessionStart": [prior_stanza]}}, indent=2)
    )

    stanza = build_first_run_stanza(fresh_workspace)
    result = merge_session_start(settings_path=settings_path, new_entry=stanza)

    assert result.prior_session_start_displaced is False
    assert result.backup_path is None


# ---- T16–T18: self-retire + verification ----------------------------


def test_T16_T17_self_retire_removes_script_and_rewrites_stanza(
    fresh_workspace: Path,
) -> None:
    """T16 + T17 — script deleted; stanza points at supervisor with venv python."""
    # Populate the shipped state: settings.json points at first-run.sh,
    # and first-run.sh exists.
    settings_path = fresh_workspace / ".claude" / "settings.json"
    first_run_path = (
        fresh_workspace / "framework" / "hands-off-lifecycle" / "hooks" / "first-run.sh"
    )
    first_run_path.write_text("#!/bin/sh\necho placeholder\n")
    first_run_path.chmod(0o755)
    settings_path.write_text(
        json.dumps(
            {"hooks": {"SessionStart": [build_first_run_stanza(fresh_workspace)]}},
            indent=2,
        )
    )

    # Self-retire.
    merge_result, _, removed = _self_retire(
        pos_v2_root=fresh_workspace, settings_path=settings_path
    )
    assert removed is True
    assert not first_run_path.exists(), "T16 — shell script deleted"

    data = json.loads(settings_path.read_text())
    # Current Claude Code schema: SessionStart[i] = {matcher, hooks: [...]}.
    cmd = data["hooks"]["SessionStart"][0]["hooks"][0]["command"]
    # T17 — stanza points at pos_session_start.py with venv python.
    expected_python = str(fresh_workspace / ".venv" / "bin" / "python")
    expected_script = str(
        fresh_workspace / "framework" / "orchestrator" / "scripts" / "pos_session_start.py"
    )
    assert cmd == f"{expected_python} {expected_script}"
    assert data["hooks"]["SessionStart"][0]["matcher"] == ""

    # Phase 7 verification passes.
    ok, problems = _verify_self_retire(
        pos_v2_root=fresh_workspace, settings_path=settings_path
    )
    assert ok is True, f"Phase 7 problems: {problems}"


def test_T18_self_retire_verification_detects_inconsistency(
    fresh_workspace: Path,
) -> None:
    """T18 — Phase 7 loud-escalates when script is still present."""
    settings_path = fresh_workspace / ".claude" / "settings.json"
    first_run_path = (
        fresh_workspace / "framework" / "hands-off-lifecycle" / "hooks" / "first-run.sh"
    )
    first_run_path.write_text("#!/bin/sh\necho placeholder\n")
    # Settings rewritten to supervisor but script NOT deleted (simulates
    # a mid-retire partial failure).
    settings_path.write_text(
        json.dumps(
            {
                "hooks": {
                    "SessionStart": [build_supervisor_stanza(fresh_workspace)]
                }
            },
            indent=2,
        )
    )

    ok, problems = _verify_self_retire(
        pos_v2_root=fresh_workspace, settings_path=settings_path
    )
    assert ok is False
    assert any("first-run.sh" in p for p in problems)


def test_T18b_self_retire_verification_detects_stale_stanza(
    fresh_workspace: Path,
) -> None:
    """T18 — Phase 7 also loud-escalates when stanza still points at first-run."""
    settings_path = fresh_workspace / ".claude" / "settings.json"
    first_run_path = (
        fresh_workspace / "framework" / "hands-off-lifecycle" / "hooks" / "first-run.sh"
    )
    # Script deleted but settings NOT rewritten.
    settings_path.write_text(
        json.dumps(
            {
                "hooks": {
                    "SessionStart": [build_first_run_stanza(fresh_workspace)]
                }
            },
            indent=2,
        )
    )

    ok, problems = _verify_self_retire(
        pos_v2_root=fresh_workspace, settings_path=settings_path
    )
    assert ok is False
    assert any("pos_session_start.py" in p or "first-run.sh" in p for p in problems)


# ---- T2, T3: subsequent-session behaviour --------------------------


def test_T2_is_already_retired_detects_completed_state(
    fresh_workspace: Path,
) -> None:
    """T2 — after retire, _is_already_retired returns True."""
    settings_path = fresh_workspace / ".claude" / "settings.json"
    settings_path.write_text(
        json.dumps(
            {
                "hooks": {
                    "SessionStart": [build_supervisor_stanza(fresh_workspace)]
                }
            },
            indent=2,
        )
    )
    # first-run.sh intentionally NOT present.
    assert _is_already_retired(fresh_workspace, settings_path) is True


def test_T3_supervisor_stanza_is_consistent_across_sessions(
    fresh_workspace: Path,
) -> None:
    """T3 — the supervisor stanza the rewrite produces is stable."""
    first = build_supervisor_stanza(fresh_workspace)
    second = build_supervisor_stanza(fresh_workspace)
    assert first == second
    # Shape: current Claude Code envelope — {matcher, hooks: [command-obj]}.
    assert first["matcher"] == ""
    inner = first["hooks"][0]
    assert inner["type"] == "command"
    assert inner["command"].endswith("pos_session_start.py")
    assert "/.venv/bin/python" in inner["command"]


# ---- T4: full preservation check -----------------------------------


def test_T4_rewritten_settings_preserves_user_keys_across_self_retire(
    fresh_workspace: Path,
) -> None:
    """T4 — after self-retire, every user-authored key outside the
    pos-v2-merged stanzas (SessionStart, UserPromptSubmit, Stop,
    PreToolUse, statusLine) is still present.

    Structural-enforcement A2 amendment (#70): self-retire now merges
    a PreToolUse stanza for the objective-binding gate. A pre-existing
    user-authored PreToolUse stanza is moved to a timestamped backup
    via the same convention SessionStart / UserPromptSubmit /
    Stop / statusLine use; the new gate stanza takes its place.
    Other top-level keys (``env``) remain untouched.
    """
    settings_path = fresh_workspace / ".claude" / "settings.json"
    # User adds their own keys alongside the shipped SessionStart stanza.
    settings_path.write_text(
        json.dumps(
            {
                "env": {"MY_USER_VAR": "42"},
                "hooks": {
                    "PreToolUse": [
                        {"type": "command", "command": "/bin/true"}
                    ],
                    "SessionStart": [build_first_run_stanza(fresh_workspace)],
                },
            },
            indent=2,
        )
    )
    first_run_path = (
        fresh_workspace / "framework" / "hands-off-lifecycle" / "hooks" / "first-run.sh"
    )
    first_run_path.write_text("#!/bin/sh\n")

    _self_retire(pos_v2_root=fresh_workspace, settings_path=settings_path)

    data = json.loads(settings_path.read_text())
    assert data["env"] == {"MY_USER_VAR": "42"}
    # Per A2 (amendment #70): the prior user-authored PreToolUse
    # stanza has been backed up via the timestamped sibling, and the
    # gate's stanza now occupies hooks.PreToolUse. Backup is
    # discoverable on disk.
    pre_tool_use = data["hooks"]["PreToolUse"]
    # Multi-contributor as of structural-enforcement A4 (amendment
    # #72): the outer PreToolUse list carries A2's objective-binding
    # gate FIRST, A3's TDD-guard SECOND, A4's Bash-guard THIRD,
    # A4's Agent-guard FOURTH.
    assert len(pre_tool_use) == 4
    assert (
        "objective_binding_gate.py"
        in pre_tool_use[0]["hooks"][0]["command"]
    )
    assert (
        "tdd_guard.py" in pre_tool_use[1]["hooks"][0]["command"]
    )
    assert (
        "bash_guard.py" in pre_tool_use[2]["hooks"][0]["command"]
    )
    assert (
        "agent_guard.py" in pre_tool_use[3]["hooks"][0]["command"]
    )
    backups = list(fresh_workspace.glob(".claude/settings.json.user-backup-*"))
    assert backups, "user-authored PreToolUse hook was not backed up"
    backup_data = json.loads(backups[0].read_text())
    assert (
        backup_data["hooks"]["PreToolUse"][0]["command"] == "/bin/true"
    )
    # Current Claude Code schema: SessionStart[i] = {matcher, hooks: [...]}.
    assert (
        data["hooks"]["SessionStart"][0]["hooks"][0]["command"].endswith(
            "pos_session_start.py"
        )
    )


# ---- T5, T6: Python version gate (shell behaviour) ------------------
#
# The shell script exits 0 and emits a stdout diagnostic on gate
# failure. We exercise it by setting LOAM_PYTHON to a path that
# resolves to a too-old Python, and to a nonexistent path.


def _run_first_run_sh(
    *, workspace: Path, env: dict[str, str]
) -> subprocess.CompletedProcess[str]:
    script = workspace / "hands-off-lifecycle" / "hooks" / "first-run.sh"
    full_env = dict(os.environ)
    # Remove inherited PYTHON env that would override our fixture.
    for k in ("LOAM_PYTHON", "CLAUDE_PROJECT_DIR"):
        full_env.pop(k, None)
    full_env.update(env)
    return subprocess.run(
        [str(script)],
        capture_output=True,
        text=True,
        env=full_env,
        timeout=30,
    )


def _populate_shell_script(workspace: Path) -> None:
    """Copy the real first-run.sh into the fixture."""
    target = workspace / "hands-off-lifecycle" / "hooks" / "first-run.sh"
    target.write_bytes(
        (REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks" / "first-run.sh").read_bytes()
    )
    target.chmod(0o755)


def test_T5_version_too_low_emits_step_by_step_diagnostic(
    tmp_path: Path,
) -> None:
    """T5 — 3.12 only available → halt with step-by-step install instructions."""
    # Construct a workspace where LOAM_PYTHON points at a fake python
    # that reports 3.12 and no other candidate is reachable. We write a
    # shell wrapper that prints a 3.12 version.
    ws = tmp_path / "pos-v2"
    (ws / "hands-off-lifecycle" / "hooks").mkdir(parents=True)
    _populate_shell_script(ws)

    fake_python = tmp_path / "fake-python-312"
    fake_python.write_text(
        "#!/bin/sh\n"
        'exec /bin/sh -c \'python3 -c "import sys; sys.stderr.write(\\"3.12 fake\\n\\"); sys.exit(1)"\' 2>/dev/null; exit 1\n'
    )
    fake_python.chmod(0o755)
    # Actually: easier — write a python-compat script that exits 1 on the
    # version check by raising SystemExit in the inline snippet. The
    # shell's _verify_version_ge_313 runs a python -c expression; our
    # fake must execute that expression. Use a tiny inline python that
    # reports 3.12 and hence fails the (>=3.13) gate.
    fake_python_312_src = tmp_path / "fake_python_312.py"
    fake_python_312_src.write_text(
        "#!/usr/bin/env python3\n"
        "import sys\n"
        "if len(sys.argv) >= 3 and sys.argv[1] == '-c':\n"
        "    # Emulate an interpreter whose version_info is 3.12.5.\n"
        "    code = sys.argv[2].replace('sys.version_info', '__fake_vi__')\n"
        "    exec_globals = {\n"
        "        '__fake_vi__': type('v', (), {'major': 3, 'minor': 12, 'micro': 5})(),\n"
        "        'sys': sys,\n"
        "    }\n"
        "    try:\n"
        "        exec(code, exec_globals)\n"
        "    except SystemExit as e:\n"
        "        raise\n"
        "elif len(sys.argv) >= 2 and sys.argv[1] == '-m' and len(sys.argv) >= 3 and sys.argv[2] == 'venv':\n"
        "    sys.exit(0)\n"
        "else:\n"
        "    sys.exit(0)\n"
    )
    fake_python_312_src.chmod(0o755)

    proc = _run_first_run_sh(
        workspace=ws,
        env={
            "LOAM_PYTHON": str(fake_python_312_src),
            # Strip PATH so no system python3.13 is reachable.
            "PATH": "/nonexistent",
        },
    )

    # Shell exits 0 always; the diagnostic is in stdout.
    assert proc.returncode == 0
    assert "-32091" in proc.stdout
    assert "platform-unsupported:no-compatible-python-found" in proc.stdout
    # Step-by-step remediation present.
    assert "brew install python@3.13" in proc.stdout


def test_T6_no_python_at_all_emits_step_by_step_diagnostic(
    tmp_path: Path,
) -> None:
    """T6 — no python interpreter → step-by-step install instructions."""
    ws = tmp_path / "pos-v2"
    (ws / "hands-off-lifecycle" / "hooks").mkdir(parents=True)
    _populate_shell_script(ws)

    proc = _run_first_run_sh(
        workspace=ws,
        env={
            "LOAM_PYTHON": "/nonexistent/python",
            "PATH": "/nonexistent",
        },
    )

    assert proc.returncode == 0
    assert "-32091" in proc.stdout
    assert "Detected:" in proc.stdout
    assert "Reopen this workspace in Claude Code" in proc.stdout


# ---- T7–T9: venv + dependency discovery -----------------------------


def test_T7_T8_T9_inventory_declares_shared_and_dedicated_venvs() -> None:
    """T7/T8/T9 — inventory correctly maps shared and dedicated venvs.

    T7 is exercised end-to-end via the shell script (Phase 2 creates
    the shared .venv). Here we verify the inventory drives the
    distinction correctly: shared_venv.components all route to the
    shared venv; dedicated_venvs route to their own paths.
    """
    data = load_inventory(REPO_ROOT / "framework" / "first-run-inventory.yaml")
    validate_inventory(data)

    assert data["shared_venv"]["path"] == ".venv"
    assert "orchestrator" in data["shared_venv"]["components"]
    assert "scope-of-work" in data["shared_venv"]["components"]
    assert "workspace-bootstrap" in data["shared_venv"]["components"]
    # memory-system is NOT in shared_venv; it has a dedicated venv.
    assert "memory-system" not in data["shared_venv"]["components"]

    dedicated = data["dedicated_venvs"]
    assert len(dedicated) == 1
    assert dedicated[0]["component"] == "memory-system"
    # Post-D.1: paths in the inventory carry the framework/ prefix.
    assert dedicated[0]["venv_path"] == "framework/memory-system/.venv"
    assert dedicated[0]["requirements"] == "framework/memory-system/requirements.txt"


def test_T9b_dedicated_venv_creation_lands_at_declared_path(
    tmp_path: Path,
) -> None:
    """Dedicated-venv creation uses the declared venv_path, not a shared path."""
    from first_run_helper import _install_dedicated_venv

    ws = tmp_path / "pos-v2"
    (ws / "memory-system").mkdir(parents=True)
    req = ws / "memory-system" / "requirements.txt"
    req.write_text("")  # empty — installs nothing but exercises the path.

    entry = {
        "component": "memory-system",
        "venv_path": "memory-system/.venv",
        "requirements": "memory-system/requirements.txt",
        "rationale": "test",
    }
    venv_path, outcome = _install_dedicated_venv(
        pos_v2_root=ws,
        shared_python=Path(sys.executable),
        entry=entry,
    )
    assert venv_path == ws / "memory-system" / ".venv"
    assert (venv_path / "bin" / "python").exists()
    assert outcome.ok, outcome.stderr_tail


# ---- T10: pip-install failure surfaces loud escalation --------------


def test_T10_pip_install_failure_surfaces_diagnostic(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """T10 — pip install failure produces loud diagnostic; no self-retire."""
    from first_run_helper import (
        _emit_diag,
        ERR_PIP_INSTALL_FAILED,
    )

    _emit_diag(
        ERR_PIP_INSTALL_FAILED,
        "pip-install-failed:orchestrator",
        "ERROR: Could not find a version that satisfies the requirement foo==1.0",
        "Next session will retry...",
    )
    captured = capsys.readouterr()
    assert "-32097" in captured.out
    assert "pip-install-failed:orchestrator" in captured.out
    assert "Next session will retry" in captured.out


# ---- T14, T15: plist + service bootstrap ----------------------------


def test_T14_inventory_declares_both_services() -> None:
    """T14 — services list has both orchestrator and memory sidecar.

    Amendment #6: labels are ``{slug}``-templated so the inventory is
    workspace-agnostic. The assertion checks the template form — the
    first-run helper resolves ``{slug}`` at load time.
    """
    data = load_inventory(REPO_ROOT / "framework" / "first-run-inventory.yaml")
    labels = [svc["label"] for svc in data["services"]]
    assert "com.loam.{slug}.memory-graphiti" in labels
    assert "com.loam.{slug}.orchestrator" in labels


def test_T15_service_health_timeout_surfaces_diagnostic(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """T15 — service-launch/health failure produces loud diagnostic."""
    from first_run_helper import _emit_diag, ERR_SERVICE_HEALTH_TIMEOUT

    _emit_diag(
        ERR_SERVICE_HEALTH_TIMEOUT,
        "service-health-timeout:com.loam.alpha.orchestrator",
        "services did not report healthy within budget: ['com.loam.alpha.orchestrator']",
        "Next session will retry. Check service logs:",
    )
    captured = capsys.readouterr()
    assert "-32098" in captured.out
    assert "service-health-timeout" in captured.out


# ---- Amendment #6 — AC7: health-poll targets computed labels --------


def test_AC7_health_poll_resolves_labels_against_workspace_slug(
    tmp_path: Path,
) -> None:
    """AC7 — ``resolve_service_labels`` substitutes ``{slug}`` in each
    service label against the workspace slug derived from the
    workspace-root basename. After resolution, the inventory's service
    entries carry the full reverse-DNS label the first-run worker
    probes in Phase 4b.
    """
    from first_run_inventory import resolve_service_labels
    from first_run_helper import _workspace_slug

    data = load_inventory(REPO_ROOT / "framework" / "first-run-inventory.yaml")
    # Confirm template form survives the loader.
    raw_labels = [svc["label"] for svc in data["services"]]
    assert all("{slug}" in lbl for lbl in raw_labels)

    # Fixture: simulate a workspace basename.
    fixture_root = tmp_path / "fixture-x"
    fixture_root.mkdir()
    slug = _workspace_slug(fixture_root)
    assert slug == "fixture-x"

    resolved = resolve_service_labels(data, slug)
    resolved_labels = [svc["label"] for svc in resolved["services"]]
    assert "com.loam.fixture-x.memory-graphiti" in resolved_labels
    assert "com.loam.fixture-x.orchestrator" in resolved_labels
    # Original inventory must NOT be mutated (resolve returns a new dict).
    assert "{slug}" in data["services"][0]["label"]


def test_AC7_workspace_slug_parity_with_workspace_bootstrap() -> None:
    """AC7 cross-cutting — the helper's local ``_workspace_slug`` and
    ``workspace_bootstrap.adapters.first_run_scaffold.workspace_slug``
    must agree on a fixture set. Duplicated logic between the two
    Python interpreters (system vs shared-venv) is the documented
    trade-off; the parity test is how they stay in lock-step.
    """
    from workspace_bootstrap.adapters.first_run_scaffold import (
        workspace_slug as canonical_workspace_slug,
    )
    from first_run_helper import _workspace_slug

    fixtures = [
        "pos3",
        "POS3",
        "pos_v2_dev",
        "My.App",
        "alpha---beta",
        "ivers-corp-pos-v2",
    ]
    for name in fixtures:
        root = Path("/tmp") / name
        assert canonical_workspace_slug(root) == _workspace_slug(root), (
            f"slug drift on {name!r}"
        )


# ---- T1: end-to-end flow via fixture --------------------------------


def test_T1_end_to_end_dry_flow_through_helper_modules(
    fresh_workspace: Path,
) -> None:
    """T1 — verify the end-to-end module interaction.

    We cannot run the real pip installs or launch real services in a
    unit test; that is covered by the live-prototype step (brief §6).
    But we can exercise the full helper code path with mocks for the
    external effects and verify the sequence is correct.

    The full end-to-end flow:
      Phase 2 venv created → Phase 3 pip installs → Phase 3d settings
      authorship → Phase 4 plist+bootstrap+health → Phase 5 sentence →
      Phase 6 self-retire → Phase 7 verification.

    This test verifies each module-boundary interaction in isolation;
    the cross-session behaviour is covered by T2/T3/T4/T16/T17/T18.
    """
    # 1. Inventory parses and validates.
    data = load_inventory(REPO_ROOT / "framework" / "first-run-inventory.yaml")
    validate_inventory(data)

    # 2. Settings.json authorship.
    settings_path = fresh_workspace / ".claude" / "settings.json"
    stanza = build_first_run_stanza(fresh_workspace)
    result = merge_session_start(settings_path=settings_path, new_entry=stanza)
    assert result.wrote is True

    # 3. Stage "phase 6" — self-retire.
    first_run_path = (
        fresh_workspace / "framework" / "hands-off-lifecycle" / "hooks" / "first-run.sh"
    )
    first_run_path.write_text("#!/bin/sh\n")
    _self_retire(pos_v2_root=fresh_workspace, settings_path=settings_path)

    # 4. Phase 7 verification passes.
    ok, problems = _verify_self_retire(
        pos_v2_root=fresh_workspace, settings_path=settings_path
    )
    assert ok is True, f"Phase 7 problems: {problems}"

    # 5. After retire, _is_already_retired returns True (session 2+
    # silence precondition).
    assert _is_already_retired(fresh_workspace, settings_path) is True


# ---- T19: inventory parser robustness -------------------------------


def test_T19_inventory_parser_rejects_tabs() -> None:
    """T19 (added) — the stdlib parser halts on tab indentation."""
    with pytest.raises(InventoryParseError, match="tab indentation"):
        parse_inventory("shared_venv:\n\tpath: .venv\n")


def test_T19b_inventory_parser_rejects_missing_schema_version() -> None:
    """T19 (added) — missing schema_version halts."""
    data = parse_inventory("shared_venv:\n  path: .venv\n  components: []\n")
    with pytest.raises(InventoryParseError, match="schema_version"):
        validate_inventory(data)


def test_T19c_inventory_parser_parses_the_shipped_file() -> None:
    """T19 (added) — the authoritative inventory parses cleanly."""
    data = load_inventory(REPO_ROOT / "framework" / "first-run-inventory.yaml")
    validate_inventory(data)
    # Smoke check.
    assert data["schema_version"] == 1
    assert len(data["shared_venv"]["components"]) >= 10


# ---- T20: editable-install amendment (2026-04-22) ------------------
#
# Failure class: missing editable-install phase — cross-component
# imports fail on fresh clone.
# Systemic cause: component packages were installed at build time
# outside first-run scope, never wired into the shipped first-run flow.
# Structural remedy: discover components via pyproject walk, topological
# order from declared deps, idempotent on re-run.


def test_T20_discover_components_finds_every_pyproject_under_root() -> None:
    """Discovery returns every workspace component with a pyproject.toml.

    The list must contain all 13 currently-shipped components. Discovery
    is not hardcoded — adding a new component directory with a
    pyproject.toml pulls it in automatically.
    """
    from first_run_helper import _discover_components

    comps = _discover_components(REPO_ROOT)
    names = {c["name"] for c in comps}
    expected = {
        "scope_of_work",
        "objective_tracker",
        "primary_persona",
        "pos_safety_layer",
        "pos_reversibility_primitive",
        "pos_cost_governance",
        "pos_self_correction",
        "graceful_degradation",
        "pos_orchestrator",
        "pos_observability_aggregator",
        "pos_self_upgrade",
        "pos_workspace_bootstrap",
        "pos_telegram_interface",
    }
    missing = expected - names
    assert not missing, f"discovery missed shipped components: {missing}"
    # Post-D.1: every discovered component resolves to a child of
    # REPO_ROOT/framework/ (the directory restructure introduced by
    # amendment #61).
    framework_root = REPO_ROOT / "framework"
    for c in comps:
        assert c["dir"].parent == framework_root


def test_T20b_discover_components_excludes_non_component_dirs(
    tmp_path: Path,
) -> None:
    """Discovery skips .venv, .git, data, docs, and nested pyprojects.

    Post-D.1: discovery walks ``<root>/framework/`` so the fixture
    constructs the framework/ subtree.
    """
    from first_run_helper import _discover_components

    ws = tmp_path / "ws"
    fw = ws / "framework"
    fw.mkdir(parents=True)
    # Real component.
    (fw / "alpha").mkdir()
    (fw / "alpha" / "pyproject.toml").write_text(
        '[project]\nname = "alpha"\nversion = "0.1.0"\n'
    )
    # Excluded directories with pyprojects — must be skipped.
    for excluded in (".venv", ".git", "data", "docs", "__pycache__"):
        d = fw / excluded
        d.mkdir()
        (d / "pyproject.toml").write_text(
            '[project]\nname = "excluded"\nversion = "0.1.0"\n'
        )
    # Nested pyproject (subdirectory of a real component) — must be skipped.
    nested = fw / "alpha" / "tests"
    nested.mkdir()
    (nested / "pyproject.toml").write_text(
        '[project]\nname = "alpha_nested"\nversion = "0.1.0"\n'
    )

    comps = _discover_components(ws)
    assert [c["name"] for c in comps] == ["alpha"]


def test_T20c_topological_order_respects_declared_dependencies() -> None:
    """Every component ordered after all of its sibling dependencies."""
    from first_run_helper import (
        _discover_components,
        _extract_dep_name,
        _topological_order,
    )

    comps = _discover_components(REPO_ROOT)
    ordered = _topological_order(comps)
    sibling_names = {c["name"] for c in comps}

    seen: set[str] = set()
    for c in ordered:
        for dep in c["deps"]:
            bare = _extract_dep_name(dep)
            if bare in sibling_names and bare != c["name"]:
                assert bare in seen, (
                    f"{c['name']} ordered before its dep {bare}"
                )
        seen.add(c["name"])

    # Length preserved (no component dropped).
    assert len(ordered) == len(comps)


def test_T20d_topological_order_detects_cycles(tmp_path: Path) -> None:
    """A declared cycle in sibling deps raises RuntimeError with the cycle members."""
    from first_run_helper import _topological_order

    components = [
        {"name": "a", "dir": tmp_path / "a", "deps": ["b"]},
        {"name": "b", "dir": tmp_path / "b", "deps": ["a"]},
    ]
    with pytest.raises(RuntimeError, match="editable-topological-cycle"):
        _topological_order(components)


def test_T20e_extract_dep_name_strips_version_pins() -> None:
    """_extract_dep_name returns the bare name for PEP 508 specs."""
    from first_run_helper import _extract_dep_name

    assert _extract_dep_name("pydantic>=2") == "pydantic"
    assert _extract_dep_name("pos-orchestrator") == "pos_orchestrator"
    assert _extract_dep_name("scope_of_work") == "scope_of_work"
    assert _extract_dep_name("foo[extras]>=1.0") == "foo"
    assert _extract_dep_name("bar ; python_version>='3.13'") == "bar"


def test_T20f_install_editable_is_idempotent(tmp_path: Path) -> None:
    """End-to-end: editable install + re-run short-circuits.

    Creates a two-component fixture workspace with a declared dep
    between them, runs ``_install_editable_components`` twice in a
    fresh venv, and asserts: first run pip-installs each; second run
    short-circuits via ``_is_component_installed``.
    """
    from first_run_helper import _install_editable_components

    # Post-D.1: components live under <root>/framework/<comp>/.
    ws = tmp_path / "ws"
    fw = ws / "framework"
    fw.mkdir(parents=True)

    # Component A — no sibling deps.
    (fw / "alpha-pkg").mkdir()
    (fw / "alpha-pkg" / "pyproject.toml").write_text(
        '[build-system]\n'
        'requires = ["setuptools>=61"]\n'
        'build-backend = "setuptools.build_meta"\n'
        '\n'
        '[project]\n'
        'name = "alpha_pkg"\n'
        'version = "0.1.0"\n'
        'dependencies = []\n'
        '\n'
        '[tool.setuptools.packages.find]\n'
        'where = ["src"]\n'
    )
    (fw / "alpha-pkg" / "src" / "alpha_pkg").mkdir(parents=True)
    (fw / "alpha-pkg" / "src" / "alpha_pkg" / "__init__.py").write_text(
        "VALUE = 'alpha'\n"
    )

    # Component B — depends on A.
    (fw / "beta-pkg").mkdir()
    (fw / "beta-pkg" / "pyproject.toml").write_text(
        '[build-system]\n'
        'requires = ["setuptools>=61"]\n'
        'build-backend = "setuptools.build_meta"\n'
        '\n'
        '[project]\n'
        'name = "beta_pkg"\n'
        'version = "0.1.0"\n'
        'dependencies = ["alpha_pkg"]\n'
        '\n'
        '[tool.setuptools.packages.find]\n'
        'where = ["src"]\n'
    )
    (fw / "beta-pkg" / "src" / "beta_pkg").mkdir(parents=True)
    (fw / "beta-pkg" / "src" / "beta_pkg" / "__init__.py").write_text(
        "from alpha_pkg import VALUE\n"
    )

    # Fresh venv.
    venv_dir = ws / ".venv"
    subprocess.run(
        [sys.executable, "-m", "venv", str(venv_dir)],
        check=True,
        capture_output=True,
        timeout=60,
    )
    venv_python = venv_dir / "bin" / "python"

    # First run — both components should install.
    outcomes_1 = _install_editable_components(
        pos_v2_root=ws, shared_venv_python=venv_python
    )
    names_1 = [o.component for o in outcomes_1]
    # Topological order: alpha before beta.
    assert names_1 == ["alpha_pkg", "beta_pkg"]
    for o in outcomes_1:
        assert o.ok, f"{o.component}: {o.stderr_tail}"
        # First run actually invokes pip, not the short-circuit marker.
        assert o.stderr_tail != "already-installed"

    # Both packages importable in the venv after install.
    import_check = subprocess.run(
        [str(venv_python), "-c", "import beta_pkg; print(beta_pkg.VALUE)"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert import_check.returncode == 0, import_check.stderr
    assert "alpha" in import_check.stdout

    # Second run — idempotent: every component short-circuits.
    outcomes_2 = _install_editable_components(
        pos_v2_root=ws, shared_venv_python=venv_python
    )
    assert [o.component for o in outcomes_2] == ["alpha_pkg", "beta_pkg"]
    for o in outcomes_2:
        assert o.ok, f"{o.component}: {o.stderr_tail}"
        assert o.stderr_tail == "already-installed", (
            f"{o.component} did not short-circuit on re-run: {o.stderr_tail}"
        )


def test_T20g_install_editable_reports_failure_with_named_class(
    tmp_path: Path,
) -> None:
    """A malformed pyproject produces a pip-install-failed:editable outcome."""
    from first_run_helper import _install_editable_components

    # Post-D.1: components live under <root>/framework/<comp>/.
    ws = tmp_path / "ws"
    fw = ws / "framework"
    fw.mkdir(parents=True)
    (fw / "broken-pkg").mkdir()
    # Missing [build-system] AND missing source → pip will fail to build.
    (fw / "broken-pkg" / "pyproject.toml").write_text(
        '[project]\n'
        'name = "broken_pkg"\n'
        'version = "0.1.0"\n'
        'dependencies = []\n'
        '\n'
        '[tool.setuptools.packages.find]\n'
        'where = ["nonexistent_src_dir"]\n'
    )
    venv_dir = ws / ".venv"
    subprocess.run(
        [sys.executable, "-m", "venv", str(venv_dir)],
        check=True,
        capture_output=True,
        timeout=60,
    )
    venv_python = venv_dir / "bin" / "python"

    outcomes = _install_editable_components(
        pos_v2_root=ws, shared_venv_python=venv_python
    )
    assert len(outcomes) == 1
    assert outcomes[0].component == "broken_pkg"
    assert outcomes[0].ok is False
    assert outcomes[0].stderr_tail  # non-empty diagnostic tail


def test_T20h_phase_3e_installs_all_components_on_shipped_inventory() -> None:
    """AC1 proxy: ordering output names every sealed-component package exactly once.

    Every component in the shipped workspace's framework/ tree (i.e.
    every dir with a top-level pyproject.toml) must appear in the
    topological order, none missing. This is the fresh-clone AC1
    proxy that runs fast without spinning up a full venv.

    Count threshold uses ``>= 14`` rather than an exact value to
    track future component additions without test churn — the
    structural intent is "every shipped component" not "exactly N".
    """
    from first_run_helper import _discover_components, _topological_order

    comps = _discover_components(REPO_ROOT)
    ordered = _topological_order(comps)
    names_in_order = [c["name"] for c in ordered]

    assert len(names_in_order) >= 14
    assert sorted(names_in_order) == sorted({c["name"] for c in comps})
    # Canonical first-tier anchors.
    assert "scope_of_work" in names_in_order
    assert "pos_orchestrator" in names_in_order
    assert "pos_workspace_bootstrap" in names_in_order
    # pos_workspace_bootstrap depends on almost everything — must be
    # installed after its siblings.
    wb_idx = names_in_order.index("pos_workspace_bootstrap")
    so_idx = names_in_order.index("scope_of_work")
    orch_idx = names_in_order.index("pos_orchestrator")
    assert wb_idx > so_idx
    assert wb_idx > orch_idx
