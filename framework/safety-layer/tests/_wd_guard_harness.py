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

"""Shared harness for the WD-discipline guard tests (AC.WDGUARD.*).

Every test drives the PRODUCTION hook script as a real `python
<script>` subprocess receiving a synthetic PreToolUse envelope on
stdin — no monkeypatching, no fakes, no module-level state. The git
repos the guard probes are REAL temporary repos built per-test, so the
canonical-identity detection runs against real `git remote` output.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
HOOK_SCRIPT = (
    REPO_ROOT / "framework" / "safety-layer" / "hooks" / "wd_discipline_guard.py"
)


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=True,
    )


def make_repo(root: Path, origin_url: str | None) -> Path:
    """Create a real git repo at *root* with an optional origin remote.

    `origin_url=None` -> no origin (mimics the derived vendored copy).
    """
    root.mkdir(parents=True, exist_ok=True)
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "t@t.test")
    _git(root, "config", "user.name", "t")
    if origin_url is not None:
        _git(root, "remote", "add", "origin", origin_url)
    return root


def write_source(repo: Path, rel: str, body: str = "x = 1\n") -> Path:
    """Materialize a file at repo-relative *rel* and return its abs path."""
    target = repo / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body, encoding="utf-8")
    return target


def envelope(
    *,
    cwd: str,
    file_path: str,
    tool_name: str = "Write",
    content: str = "x = 1\n",
) -> str:
    return json.dumps(
        {
            "cwd": cwd,
            "tool_name": tool_name,
            "tool_input": {"file_path": file_path, "content": content},
        }
    )


def invoke(env_json: str, extra_env: dict[str, str] | None = None) -> tuple[int, str, str]:
    """Run the production hook script as a subprocess; return (rc, out, err)."""
    import os

    run_env = dict(os.environ)
    # Neutralize any inherited toggle so the default path is exercised
    # unless a test explicitly sets one.
    run_env.pop("LOAM_SAFETY_HOOKS", None)
    run_env.pop("LOAM_WD_GUARD", None)
    if extra_env:
        run_env.update(extra_env)
    result = subprocess.run(
        [sys.executable, str(HOOK_SCRIPT)],
        input=env_json,
        capture_output=True,
        text=True,
        timeout=20,
        env=run_env,
    )
    return (result.returncode, result.stdout, result.stderr)


def is_deny(stdout: str) -> bool:
    """True iff the production deny shape is on stdout."""
    s = stdout.strip()
    if not s:
        return False
    try:
        payload = json.loads(s)
    except Exception:
        return False
    hso = payload.get("hookSpecificOutput", {})
    return hso.get("permissionDecision") == "deny"


def deny_reason(stdout: str) -> str:
    try:
        return json.loads(stdout.strip())["hookSpecificOutput"][
            "permissionDecisionReason"
        ]
    except Exception:
        return ""


# A canonical-loam origin URL the guard must accept.
CANONICAL_ORIGIN = "https://github.com/lukeivers/loam.git"
# A non-canonical origin (the derived pos3-workspace repo).
DERIVED_ORIGIN = "https://github.com/lukeivers/pos3-workspace.git"
