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

"""AC.DSF.7 (OUTCOME-ALTITUDE) — the real floor PreToolUse hook entry-point.

Invoking the real floor PreToolUse hook entry-point with raw stdin and NO
pre-arranged fixture/state — a fabricated destructive command in an
``is_production: true`` context with no attestation record — returns a deny
decision whose message names the target and the destructive sub-action in
non-technical vocabulary; and the same entry-point, fed input that makes its
own evaluation raise (a corrupt attestations file), still returns deny
(fail-closed).

The hook is driven as a SEPARATE PROCESS over a real stdin pipe against a
real on-disk workspace — no internal function is stubbed, no decision is
pre-seeded. ``outcome-altitude: true``.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


HOOK = (
    Path(__file__).resolve().parent.parent
    / "hooks"
    / "deploy_safety_floor_guard.py"
)

_PROD_ENV_CONFIG = """\
environments:
  - name: prod
    id: 01J9ZPROD0000000000000001
    is_production: true
    tier: real-infra
    reversible: false
    gate: high
    security_profile: prod
    identities:
      hosts: [db.prod.internal]
active: prod
"""


def _write_workspace(tmp_path: Path, *, attestations: str | None) -> Path:
    loam_dir = tmp_path / ".loam"
    loam_dir.mkdir(parents=True, exist_ok=True)
    (loam_dir / "environments.yaml").write_text(_PROD_ENV_CONFIG, encoding="utf-8")
    if attestations is not None:
        (loam_dir / "attestations.yaml").write_text(attestations, encoding="utf-8")
    return tmp_path


def _run_hook(workspace: Path, envelope: dict) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(envelope),
        cwd=str(workspace),
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout


def test_real_entrypoint_denies_unattested_prod_destruction(tmp_path: Path) -> None:
    """No pre-arranged state: a real destructive command in an is_production
    context with no attestation record -> deny naming target + sub-action in
    plain words."""
    workspace = _write_workspace(tmp_path, attestations=None)
    envelope = {
        "session_id": "oa-1",
        "cwd": str(workspace),
        "permission_mode": "default",
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {
            "command": "psql -h db.prod.internal -c 'DROP DATABASE orders'"
        },
    }
    rc, out = _run_hook(workspace, envelope)
    assert rc == 0
    assert out.strip(), "the hook must emit a decision payload on stdout"
    payload = json.loads(out)
    hso = payload["hookSpecificOutput"]
    assert hso["hookEventName"] == "PreToolUse"
    assert hso["permissionDecision"] == "deny"
    reason = hso["permissionDecisionReason"]
    # Names the destructive sub-action in non-technical vocabulary.
    assert "delete an entire database" in reason
    # Names the target in plain words (not "is_production" / "prevent_destroy").
    assert "live production system" in reason
    assert "is_production" not in reason
    assert "prevent_destroy" not in reason


def test_real_entrypoint_fails_closed_when_evaluation_raises(tmp_path: Path) -> None:
    """The same entry-point, fed input that makes its own evaluation raise (a
    corrupt attestations file), still returns deny (fail-closed) — it does not
    fall open."""
    workspace = _write_workspace(
        tmp_path, attestations="attestations: [ this is ::: not valid yaml ]["
    )
    envelope = {
        "session_id": "oa-2",
        "cwd": str(workspace),
        "permission_mode": "default",
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {
            "command": "psql -h db.prod.internal -c 'DROP DATABASE orders'"
        },
    }
    rc, out = _run_hook(workspace, envelope)
    assert rc == 0
    assert out.strip(), "fail-closed must still emit a deny payload"
    payload = json.loads(out)
    hso = payload["hookSpecificOutput"]
    assert hso["permissionDecision"] == "deny"
    assert "could not confirm this change is safe" in hso["permissionDecisionReason"]


def test_real_entrypoint_allows_a_benign_read_command(tmp_path: Path) -> None:
    """Floor gate class is destructive-only: a non-destructive command in the
    same prod context is allowed (no deny payload)."""
    workspace = _write_workspace(tmp_path, attestations=None)
    envelope = {
        "session_id": "oa-3",
        "cwd": str(workspace),
        "permission_mode": "default",
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {
            "command": "psql -h db.prod.internal -c 'SELECT 1'"
        },
    }
    rc, out = _run_hook(workspace, envelope)
    assert rc == 0
    assert out.strip() == "", "a benign command must produce no deny payload"


def test_real_entrypoint_bypass_mode_still_returns_deny(tmp_path: Path) -> None:
    """The hook emits its deny decision regardless of permission_mode — the
    decision the entry-point returns does not depend on the mode (whether the
    harness HONORS deny under bypass is the deploy-tier-adjacent Sub-cycle B
    concern; the floor's job here is to RETURN deny)."""
    workspace = _write_workspace(tmp_path, attestations=None)
    envelope = {
        "session_id": "oa-4",
        "cwd": str(workspace),
        "permission_mode": "bypassPermissions",
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {
            "command": "psql -h db.prod.internal -c 'DROP DATABASE orders'"
        },
    }
    rc, out = _run_hook(workspace, envelope)
    assert rc == 0
    payload = json.loads(out)
    assert payload["hookSpecificOutput"]["permissionDecision"] == "deny"
