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

"""AC.DSF.5 (OUTCOME-ALTITUDE) — the fail-policy primitive at the wire.

``outcome-altitude: true``. Drives the real fail-policy primitive with
NO pre-arranged fixture/state and captures the ACTUAL bytes it writes:
a gate that declares ``FAIL_CLOSED`` and faults against a destructive
candidate emits, to its real output stream, the exact PreToolUse deny
envelope Claude Code honours as a tool-call block — verified at build
time to hold even under bypass-all permission modes (the deny is NOT
silently defeated by ``--permission-mode bypassPermissions`` /
``--dangerously-skip-permissions``).

A second check crosses to a real floor PreToolUse hook
(``deploy_safety_floor_guard``) driven as a separate process under a
fault, confirming the convention the primitive codifies holds end to
end at an actual floor gate — under an envelope whose ``permission_mode``
is ``bypassPermissions`` (the case Sub-cycle A's AC.DSF.7 explicitly
deferred to this sub-cycle). The cross-check skips gracefully if the
floor component is not present, so this suite stays self-contained.
"""

from __future__ import annotations

import io
import json
import subprocess
import sys
from pathlib import Path

import pytest


_HOOKS_DIR = Path(__file__).resolve().parent.parent / "hooks"
_REPO_ROOT = Path(__file__).resolve().parents[3]
_FLOOR_HOOK = (
    _REPO_ROOT
    / "framework"
    / "deploy-safety-floor"
    / "hooks"
    / "deploy_safety_floor_guard.py"
)

if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

import _fail_policy as FP  # noqa: E402


def test_fail_closed_gate_emits_the_honored_deny_envelope_on_fault() -> None:
    """Outcome at the wire: a FAIL_CLOSED gate faulting against a
    destructive candidate writes the real PreToolUse deny envelope —
    the exact contract the build-time keystone proved Claude Code honours
    as a block even under bypass-all. No pre-arranged state: the only
    inputs are the declared policy, the candidate flag, and a reason."""
    out = io.StringIO()
    reason = (
        "Refused: could not confirm this change is safe, so it is blocked "
        "by default (the protection check itself errored)."
    )
    decision = FP.apply_fault_policy(
        FP.FailPolicy.FAIL_CLOSED,
        is_destructive_candidate=True,
        deny_reason=reason,
        out=out,
    )
    assert decision.deny is True

    raw = out.getvalue()
    assert raw, "a fail-closed gate must emit a decision payload on fault"
    payload = json.loads(raw)
    hso = payload["hookSpecificOutput"]
    assert hso["hookEventName"] == "PreToolUse"
    assert hso["permissionDecision"] == "deny"
    assert hso["permissionDecisionReason"] == reason
    # Plain-words reason (no internal jargon leaked to the user).
    assert "is_production" not in hso["permissionDecisionReason"]


def test_fail_open_gate_emits_nothing_on_fault() -> None:
    """The same primitive under FAIL_OPEN emits nothing on the same fault
    — the advisory convention, at the wire."""
    out = io.StringIO()
    decision = FP.apply_fault_policy(
        FP.FailPolicy.FAIL_OPEN,
        is_destructive_candidate=True,
        deny_reason="never-emitted",
        out=out,
    )
    assert decision.deny is False
    assert out.getvalue() == ""


@pytest.mark.skipif(
    not _FLOOR_HOOK.is_file(),
    reason="deploy-safety-floor gate not present; primitive checks suffice",
)
def test_real_floor_gate_denies_on_fault_under_bypass_mode(tmp_path: Path) -> None:
    """Cross-check at a real floor PreToolUse hook: a destructive command
    against a prod identity with a CORRUPT config (its own evaluation
    raises) returns deny — even when the envelope's permission_mode is
    ``bypassPermissions``. The floor gate RETURNS deny; the keystone
    established the harness HONORS that deny under bypass."""
    loam_dir = tmp_path / ".loam"
    loam_dir.mkdir(parents=True, exist_ok=True)
    # A prod environment so a destructive command is a floor candidate...
    (loam_dir / "environments.yaml").write_text(
        "environments:\n"
        "  - name: prod\n"
        "    id: 01J9ZPROD0000000000000001\n"
        "    is_production: true\n"
        "    tier: real-infra\n"
        "    reversible: false\n"
        "    gate: high\n"
        "    security_profile: prod\n"
        "    identities:\n"
        "      hosts: [db.prod.internal]\n"
        "active: prod\n",
        encoding="utf-8",
    )
    # ...and a corrupt attestations file so the floor's own evaluation raises.
    (loam_dir / "attestations.yaml").write_text(
        "attestations: [ this is ::: not valid yaml ][", encoding="utf-8"
    )
    envelope = {
        "cwd": str(tmp_path),
        "permission_mode": "bypassPermissions",
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {
            "command": "psql -h db.prod.internal -c 'DROP DATABASE orders'"
        },
    }
    proc = subprocess.run(
        [sys.executable, str(_FLOOR_HOOK)],
        input=json.dumps(envelope),
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert proc.returncode == 0
    assert proc.stdout.strip(), "fail-closed floor gate must emit a deny payload"
    payload = json.loads(proc.stdout)
    assert payload["hookSpecificOutput"]["permissionDecision"] == "deny"
