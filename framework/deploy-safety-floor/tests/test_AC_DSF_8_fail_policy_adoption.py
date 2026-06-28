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

"""AC.DSF.8 — the floor gate ADOPTS the shared fail-policy primitive.

Behaviour-preserving de-dup: the deploy-safety-floor gate sources its
fail-closed-on-fault behaviour from the shared safety-layer primitive
(``_fail_policy``) instead of its own ad-hoc enactment. This test proves:

* (structural) the gate declares ``FAIL_POLICY = FailPolicy.FAIL_CLOSED`` and
  binds the primitive's ``apply_fault_policy`` / ``emit_deny`` — the local
  ad-hoc ``_emit_deny`` enactment is GONE;
* (behavioural parity) the real PreToolUse hook entry-point, fed input that
  makes its own evaluation raise (a corrupt attestations file) for a
  destructive-prod candidate, STILL returns the same fail-closed deny — the
  observable behaviour the Sub-cycle A ``test_AC_DSF_7`` fault test asserts is
  unchanged, now routed through the shared primitive.

The structural import mirrors the safety-layer advisory-guard test: the
guard module is loaded by file path with both the floor's ``hooks`` dir and
the safety-layer ``hooks`` dir on ``sys.path`` (the primitive is a sibling of
the latter)."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType


_HOOKS_DIR = Path(__file__).resolve().parent.parent / "hooks"
_FAIL_POLICY_HOOKS = (
    Path(__file__).resolve().parents[2] / "safety-layer" / "hooks"
)

for _p in (_FAIL_POLICY_HOOKS, _HOOKS_DIR):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import _fail_policy as FP  # noqa: E402


HOOK = _HOOKS_DIR / "deploy_safety_floor_guard.py"

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


def _load_guard() -> ModuleType:
    """Import the floor guard module by path. Its top level inserts the
    sibling dirs on sys.path and binds ``FAIL_POLICY`` — no ``main()`` runs at
    import."""
    mod_name = "deploy_safety_floor_guard_under_test"
    spec = importlib.util.spec_from_file_location(mod_name, HOOK)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_floor_gate_declares_fail_closed_from_shared_primitive() -> None:
    """The floor gate declares FAIL_CLOSED — the floor destructive posture —
    via the shared primitive's enum."""
    guard = _load_guard()
    assert hasattr(guard, "FAIL_POLICY"), "floor gate must declare FAIL_POLICY"
    assert guard.FAIL_POLICY is FP.FailPolicy.FAIL_CLOSED


def test_floor_gate_routes_through_shared_primitive_not_local_dup() -> None:
    """The on-fault decision + deny-emit are sourced from the shared
    primitive; the local ad-hoc ``_emit_deny`` enactment is removed."""
    guard = _load_guard()
    # The duplicate enactment helper is gone.
    assert not hasattr(guard, "_emit_deny"), (
        "local _emit_deny duplicate must be removed — the deny envelope is "
        "emitted by the shared primitive"
    )
    # The gate binds the primitive's enactment functions (single source).
    assert guard.apply_fault_policy is FP.apply_fault_policy
    assert guard.emit_deny is FP.emit_deny


def _write_workspace(tmp_path: Path, *, attestations: str | None) -> Path:
    loam_dir = tmp_path / ".loam"
    loam_dir.mkdir(parents=True, exist_ok=True)
    (loam_dir / "environments.yaml").write_text(
        _PROD_ENV_CONFIG, encoding="utf-8"
    )
    if attestations is not None:
        (loam_dir / "attestations.yaml").write_text(
            attestations, encoding="utf-8"
        )
    return tmp_path


def _run_hook(workspace: Path, envelope: dict) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(envelope),
        cwd=str(workspace),
        capture_output=True,
        text=True,
        timeout=15,
    )
    return proc.returncode, proc.stdout


def test_real_entrypoint_still_fails_closed_after_adoption(tmp_path: Path) -> None:
    """Behavioural parity: the real entry-point on a corrupt-attestations
    fault against a destructive-prod candidate still returns the fail-closed
    deny — unchanged from pre-adoption, now routed through the primitive."""
    workspace = _write_workspace(
        tmp_path, attestations="attestations: [ this is ::: not valid yaml ]["
    )
    envelope = {
        "session_id": "dsf8-faultclosed",
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
    assert hso["hookEventName"] == "PreToolUse"
    assert hso["permissionDecision"] == "deny"
    assert "could not confirm this change is safe" in hso["permissionDecisionReason"]


def test_real_entrypoint_non_candidate_fault_still_fails_open(tmp_path: Path) -> None:
    """Read-parity preserved: a corrupt-attestations fault on a NON-candidate
    (a benign read command) fails OPEN — no deny payload — exactly as the
    FAIL_CLOSED primitive resolves a non-candidate."""
    workspace = _write_workspace(
        tmp_path, attestations="attestations: [ this is ::: not valid yaml ]["
    )
    envelope = {
        "session_id": "dsf8-faultopen",
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
    assert out.strip() == "", (
        "a non-candidate fault must fail OPEN (no deny) under the FAIL_CLOSED "
        "policy — read parity"
    )
