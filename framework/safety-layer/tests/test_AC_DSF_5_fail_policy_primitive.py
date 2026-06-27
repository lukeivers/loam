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

"""AC.DSF.5 — per-gate fail-policy primitive (G15 keystone), unit surface.

The reusable fail-policy field a gate declares to control its on-fault
behaviour. Default ``FAIL_OPEN`` (preserves the sealed advisory
``D-SECHK.FAIL-OPEN`` convention with zero regression); a floor
destructive gate opts into ``FAIL_CLOSED`` so its hook, on its own
internal fault against a destructive candidate, DENIES rather than
falls open. A non-candidate (a read) fails OPEN even under a
fail-closed gate (read parity).
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path


_HOOKS_DIR = Path(__file__).resolve().parent.parent / "hooks"

# Import the stdlib-only sibling primitive exactly as a bare-script hook
# does: insert the hooks dir on sys.path and import under its real name
# (so it registers in sys.modules — required for the frozen dataclass).
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

import _fail_policy as FP  # noqa: E402


def test_default_fail_policy_is_fail_open() -> None:
    """A gate that declares nothing fails OPEN — the convention default,
    so no existing advisory guard regresses."""
    assert FP.DEFAULT_FAIL_POLICY is FP.FailPolicy.FAIL_OPEN


def test_resolve_fail_open_allows_on_fault() -> None:
    """FAIL_OPEN: on fault, ALLOW regardless of candidate-ness."""
    for candidate in (True, False):
        d = FP.resolve_fault(
            FP.FailPolicy.FAIL_OPEN, is_destructive_candidate=candidate
        )
        assert d.deny is False
        assert d.label == FP.LABEL_FAIL_OPEN


def test_resolve_fail_closed_denies_destructive_candidate() -> None:
    """FAIL_CLOSED + destructive candidate: DENY (the floor posture, G15)."""
    d = FP.resolve_fault(
        FP.FailPolicy.FAIL_CLOSED, is_destructive_candidate=True
    )
    assert d.deny is True
    assert d.label == FP.LABEL_DENY_FAIL_CLOSED


def test_resolve_fail_closed_non_candidate_fails_open() -> None:
    """FAIL_CLOSED + non-candidate (a read): ALLOW — a fail-closed gate
    must not block reads merely because its own check errored on an
    unrelated input (read parity with the floor gate's behaviour)."""
    d = FP.resolve_fault(
        FP.FailPolicy.FAIL_CLOSED, is_destructive_candidate=False
    )
    assert d.deny is False
    assert d.label == FP.LABEL_FAIL_OPEN_NON_CANDIDATE


def test_deny_payload_is_the_pretooluse_block_contract() -> None:
    """The emitted envelope is the exact PreToolUse deny contract Claude
    Code honours as a block (build-time keystone-verified, incl. bypass)."""
    payload = FP.deny_payload("because reasons")
    hso = payload["hookSpecificOutput"]
    assert hso["hookEventName"] == "PreToolUse"
    assert hso["permissionDecision"] == "deny"
    assert hso["permissionDecisionReason"] == "because reasons"


def test_apply_fault_policy_emits_deny_only_when_closed_and_candidate() -> None:
    """apply_fault_policy enacts the decision: it writes the deny envelope
    to ``out`` iff the resolved decision is DENY, and nothing otherwise."""
    # FAIL_CLOSED + candidate -> deny envelope on the stream.
    buf = io.StringIO()
    d = FP.apply_fault_policy(
        FP.FailPolicy.FAIL_CLOSED,
        is_destructive_candidate=True,
        deny_reason="blocked",
        out=buf,
    )
    assert d.deny is True
    emitted = json.loads(buf.getvalue())
    assert emitted["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert emitted["hookSpecificOutput"]["permissionDecisionReason"] == "blocked"

    # FAIL_OPEN + candidate -> nothing emitted (advisory convention).
    buf_open = io.StringIO()
    d_open = FP.apply_fault_policy(
        FP.FailPolicy.FAIL_OPEN,
        is_destructive_candidate=True,
        deny_reason="would-not-emit",
        out=buf_open,
    )
    assert d_open.deny is False
    assert buf_open.getvalue() == ""

    # FAIL_CLOSED + non-candidate -> nothing emitted (read parity).
    buf_read = io.StringIO()
    d_read = FP.apply_fault_policy(
        FP.FailPolicy.FAIL_CLOSED,
        is_destructive_candidate=False,
        deny_reason="would-not-emit",
        out=buf_read,
    )
    assert d_read.deny is False
    assert buf_read.getvalue() == ""
