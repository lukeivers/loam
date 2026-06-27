# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""AC.SBB.1 — secrets-never-committed at the commit/push boundary.

The secret-pattern guard is EXTENDED (strictly additively) with a
staged-diff scan: a ``git commit`` / ``git push`` boundary command
triggers a scan of the content the boundary would publish (the staged
diff for commit, the unpushed range for push) for credential shapes. A
secret embedded in a file's CONTENT — not just a literal on the command
line — is blocked at the boundary, with no secret value echoed, and the
block fires for the artifact loam BUILDS (any repo under ``cwd``), not
only loam's own repository.

Driven at the REAL entry-point: the hook runs as a separate process over
a real stdin pipe against a real on-disk git repository — no internal
function is stubbed.

The additive constraint (plan §8 HALT): the existing inbound-paste
CONTENT/FILE paths and the guard's fail-OPEN fault policy
(``D-SECHK.FAIL-OPEN``) are unchanged — covered by
``test_AC_SBB_1_additive_no_regression_of_fail_open`` plus the
pre-existing ``test_AC_SECHK_4_fail_open`` suite.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


HOOK = (
    Path(__file__).resolve().parent.parent
    / "hooks"
    / "secret_pattern_guard.py"
)

# Canonical AWS example access key — matches the sealed ``aws-access-key``
# CONTENT pattern (AKIA + 16 chars). Not a live credential.
AWS_KEY = "AKIAIOSFODNN7EXAMPLE"


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )


def _init_repo(repo: Path) -> None:
    repo.mkdir(parents=True, exist_ok=True)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "t@example.com")
    _git(repo, "config", "user.name", "t")
    # Ensure a default branch name exists for the @{upstream} path.
    _git(repo, "checkout", "-q", "-B", "main")


def _run_hook(cwd: Path, envelope: dict) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(envelope),
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout


def _commit_envelope(cwd: Path) -> dict:
    return {
        "session_id": "sbb1",
        "cwd": str(cwd),
        "permission_mode": "default",
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": "git commit -m 'add config'"},
    }


def test_staged_file_secret_blocked_at_commit_boundary(tmp_path: Path) -> None:
    """A secret embedded in a STAGED FILE (not the command line) is denied
    at the ``git commit`` boundary, in a repo that is NOT loam's own."""
    repo = tmp_path / "built-artifact"
    _init_repo(repo)
    (repo / "settings.py").write_text(
        f'AWS_ACCESS_KEY_ID = "{AWS_KEY}"\n', encoding="utf-8"
    )
    _git(repo, "add", "settings.py")  # staged, not yet committed

    rc, out = _run_hook(repo, _commit_envelope(repo))
    assert rc == 0
    assert out.strip(), "a staged-diff secret must produce a deny payload"
    payload = json.loads(out)
    hso = payload["hookSpecificOutput"]
    assert hso["hookEventName"] == "PreToolUse"
    assert hso["permissionDecision"] == "deny"
    reason = hso["permissionDecisionReason"]
    assert "AC.SBB.1" in reason
    assert "commit/push boundary" in reason


def test_secret_value_never_echoed(tmp_path: Path) -> None:
    """The deny reason carries only a redacted token shape — the full
    secret is never echoed into the reply / brief / log."""
    repo = tmp_path / "artifact"
    _init_repo(repo)
    (repo / ".env").write_text(f"AWS_ACCESS_KEY_ID={AWS_KEY}\n", encoding="utf-8")
    _git(repo, "add", "-f", ".env")

    rc, out = _run_hook(repo, _commit_envelope(repo))
    assert rc == 0
    payload = json.loads(out)
    assert payload["hookSpecificOutput"]["permissionDecision"] == "deny"
    # The full credential MUST NOT appear anywhere in the emitted payload.
    assert AWS_KEY not in out


def test_clean_staged_commit_passes_silently(tmp_path: Path) -> None:
    """A commit whose staged diff carries no credential passes silently
    (no deny payload)."""
    repo = tmp_path / "clean"
    _init_repo(repo)
    (repo / "app.py").write_text("print('hello')\n", encoding="utf-8")
    _git(repo, "add", "app.py")

    rc, out = _run_hook(repo, _commit_envelope(repo))
    assert rc == 0
    assert out.strip() == "", "a clean staged diff must produce no deny payload"


def test_push_boundary_scans_unpushed_commits(tmp_path: Path) -> None:
    """A ``git push`` boundary scans the unpushed commit range: a secret
    already committed (no longer in the staged diff) but not yet pushed is
    still caught."""
    repo = tmp_path / "topush"
    _init_repo(repo)
    (repo / "deploy.cfg").write_text(
        f"key = {AWS_KEY}\n", encoding="utf-8"
    )
    _git(repo, "add", "deploy.cfg")
    _git(repo, "commit", "-q", "-m", "add deploy cfg")  # committed, unpushed

    envelope = {
        "session_id": "sbb1-push",
        "cwd": str(repo),
        "permission_mode": "default",
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": "git push origin main"},
    }
    rc, out = _run_hook(repo, envelope)
    assert rc == 0
    assert out.strip(), "an unpushed-commit secret must be denied at push"
    payload = json.loads(out)
    assert payload["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert AWS_KEY not in out


def test_non_boundary_command_does_not_scan_diff(tmp_path: Path) -> None:
    """A non-commit/push Bash command does NOT trigger the staged-diff scan
    even when the repo has a staged secret — the boundary scan is scoped to
    the publish boundary (a ``git status`` is not a publish)."""
    repo = tmp_path / "noscan"
    _init_repo(repo)
    (repo / "secret.py").write_text(
        f'KEY = "{AWS_KEY}"\n', encoding="utf-8"
    )
    _git(repo, "add", "secret.py")

    envelope = {
        "session_id": "sbb1-noscan",
        "cwd": str(repo),
        "permission_mode": "default",
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": "git status"},
    }
    rc, out = _run_hook(repo, envelope)
    assert rc == 0
    assert out.strip() == "", "git status must not trigger the diff scan"


def test_additive_no_regression_of_fail_open(tmp_path: Path) -> None:
    """Additive constraint (plan §8 HALT): a commit boundary command in a
    directory that is NOT a git repo (the ``git`` read fails) does NOT
    block — the staged-diff scan fails SOFT, preserving the guard's
    ``D-SECHK.FAIL-OPEN`` fault policy. The existing inbound-paste path is
    untouched."""
    not_a_repo = tmp_path / "plain-dir"
    not_a_repo.mkdir()
    rc, out = _run_hook(not_a_repo, _commit_envelope(not_a_repo))
    assert rc == 0
    assert out.strip() == "", (
        "a git-read failure must fail OPEN (no deny), not regress to a block"
    )


def test_command_line_secret_still_blocked_unchanged(tmp_path: Path) -> None:
    """Regression anchor: the pre-existing CONTENT path (a secret literal on
    the Bash command line) still denies, unchanged by the additive
    staged-diff branch."""
    repo = tmp_path / "cli"
    _init_repo(repo)
    envelope = {
        "session_id": "sbb1-cli",
        "cwd": str(repo),
        "permission_mode": "default",
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": f"echo {AWS_KEY} > /tmp/x"},
    }
    rc, out = _run_hook(repo, envelope)
    assert rc == 0
    payload = json.loads(out)
    assert payload["hookSpecificOutput"]["permissionDecision"] == "deny"
    # The pre-existing CONTENT class fires (AC.SECHK.1), not the new path.
    assert "AC.SECHK.1" in payload["hookSpecificOutput"]["permissionDecisionReason"]


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-q"]))
