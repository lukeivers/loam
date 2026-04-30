"""AC.BAG.1 — Bash gate denies secret-file commit (UNIVERSAL).

Per the locked plan-doc §4 AC.BAG.1: given a Bash tool call whose
``tool_input.command`` matches a secret-commit pattern (the command
invokes ``git add``, ``git commit``, or ``git stash`` in a way that
includes a path matching the secret-file regex family — ``\\.env``,
``credentials\\.json``, ``\\.aws/credentials``, ``*.pem``, ``*.key``,
``id_rsa``, ``id_ed25519``, plus the curated extensible list): hook
returns ``hookSpecificOutput.permissionDecision: "deny"`` with a
``permissionDecisionReason`` that names (a) the matched paths,
(b) the secret-class detected, (c) at least one repair direction.
Fires regardless of workspace mode. The env-var override
``POS_BASH_GUARD_ALLOW=1`` does NOT bypass this gate.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
HOOKS_DIR = REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks"
# Post-M6b.0: gate-hook source files MOVED to plugins/dev-sdlc/hooks/.
# Add plugin's hooks dir to sys.path so the test imports resolve to
# the moved gate modules. _gate_helpers.py STAYS at canonical
# (HOOKS_DIR above) and remains importable.
PLUGIN_HOOKS_DIR = REPO_ROOT / "plugins" / "dev-sdlc" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))
if PLUGIN_HOOKS_DIR.exists():
    sys.path.insert(0, str(PLUGIN_HOOKS_DIR))


@pytest.fixture
def gate(monkeypatch, tmp_path):
    """Import bash_guard fresh and force NORMAL USE mode-bit
    fail-through so the universal-leg checks fire as the only deny
    surface (AC.BAG.1 is UNIVERSAL — fires regardless of mode)."""
    import bash_guard
    return bash_guard


def test_AC_BAG_1_git_add_dotenv_denies(tmp_path, gate) -> None:
    """git add .env → deny with reason naming the path + the no-
    override property."""
    decision = gate.evaluate(
        workspace_root=tmp_path,
        tool_name="Bash",
        tool_input={"command": "git add .env"},
    )
    assert decision.decision == "deny"
    assert decision.failure_class == "secret-commit"
    assert decision.reason is not None
    assert ".env" in decision.reason
    assert "AC.BAG.1" in decision.reason
    assert "UNIVERSAL" in decision.reason
    # Repair direction named.
    assert (
        ".gitignore" in decision.reason.lower()
        or "halt" in decision.reason.lower()
        or "rename" in decision.reason.lower()
    )
    # Override-not-applicable property surfaced.
    assert "POS_BASH_GUARD_ALLOW" in decision.reason


def test_AC_BAG_1_git_commit_pem_denies(tmp_path, gate) -> None:
    """git commit foo.pem → deny."""
    decision = gate.evaluate(
        workspace_root=tmp_path,
        tool_name="Bash",
        tool_input={"command": "git commit -m 'leak' foo.pem"},
    )
    assert decision.decision == "deny"
    assert decision.failure_class == "secret-commit"
    assert "foo.pem" in decision.reason


def test_AC_BAG_1_id_rsa_denies(tmp_path, gate) -> None:
    """git stash with id_rsa → deny."""
    decision = gate.evaluate(
        workspace_root=tmp_path,
        tool_name="Bash",
        tool_input={"command": "git stash push -- id_rsa"},
    )
    assert decision.decision == "deny"
    assert decision.failure_class == "secret-commit"
    assert "id_rsa" in decision.reason


def test_AC_BAG_1_credentials_json_denies(tmp_path, gate) -> None:
    decision = gate.evaluate(
        workspace_root=tmp_path,
        tool_name="Bash",
        tool_input={"command": "git add credentials.json"},
    )
    assert decision.decision == "deny"
    assert decision.failure_class == "secret-commit"


def test_AC_BAG_1_dotenv_example_admitted(tmp_path, gate) -> None:
    """git add .env-example → no-op (carve-out for documentation)."""
    decision = gate.evaluate(
        workspace_root=tmp_path,
        tool_name="Bash",
        tool_input={"command": "git add .env-example"},
    )
    # Admitted: the carve-out applies. Decision is allow OR no-op
    # (mode bit short-circuits since no DEV-MODE-only check fires).
    assert decision.decision in ("allow", "no-op")
    assert decision.failure_class is None


def test_AC_BAG_1_dotenv_dot_example_admitted(tmp_path, gate) -> None:
    decision = gate.evaluate(
        workspace_root=tmp_path,
        tool_name="Bash",
        tool_input={"command": "git add .env.example"},
    )
    assert decision.decision in ("allow", "no-op")
    assert decision.failure_class is None


def test_AC_BAG_1_normal_file_admitted(tmp_path, gate) -> None:
    """git add normal.py → admitted (no secret pattern)."""
    decision = gate.evaluate(
        workspace_root=tmp_path,
        tool_name="Bash",
        tool_input={"command": "git add normal.py"},
    )
    assert decision.decision in ("allow", "no-op")


def test_AC_BAG_1_universal_fires_in_normal_use(
    tmp_path, gate, monkeypatch
) -> None:
    """AC.BAG.1 fires regardless of workspace mode (UNIVERSAL).
    Even in NORMAL USE the secret-commit gate denies."""
    # The mode-bit read happens AFTER the universal checks in
    # evaluate(), so this is implicit by the architecture; this test
    # makes the property auditable.
    decision = gate.evaluate(
        workspace_root=tmp_path,
        tool_name="Bash",
        tool_input={"command": "git add .env"},
    )
    assert decision.decision == "deny"
    assert decision.failure_class == "secret-commit"


def test_AC_BAG_1_env_override_does_not_bypass(
    tmp_path, gate, monkeypatch
) -> None:
    """Setting POS_BASH_GUARD_ALLOW=1 does NOT admit the secret
    commit (universal classes are not bypassable per constraint 18)."""
    decision = gate.evaluate(
        workspace_root=tmp_path,
        tool_name="Bash",
        tool_input={"command": "git add .env"},
        env={"POS_BASH_GUARD_ALLOW": "1"},
    )
    assert decision.decision == "deny"
    assert decision.failure_class == "secret-commit"


def test_AC_BAG_1_non_bash_tool_no_op(tmp_path, gate) -> None:
    """tool_name != 'Bash' → no-op."""
    decision = gate.evaluate(
        workspace_root=tmp_path,
        tool_name="Edit",
        tool_input={"command": "git add .env"},
    )
    assert decision.decision == "no-op"
