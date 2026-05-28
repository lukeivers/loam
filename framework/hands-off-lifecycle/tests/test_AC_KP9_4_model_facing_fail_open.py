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

"""AC.KP9.4 — gate feedback model-facing only; fail-open.

The gate's block/flag reason is emitted MODEL-FACING (the report is for
the model / hook stderr), never as a user-visible "your reply was
blocked by the register judge" message (that would itself be a
mechanism leak). On gate error/timeout the draft PASSES (fail-open) — a
broken gate must NEVER block a send.

Method is the builder's call (ODD §1.1): fail-open is proven by feeding
the gate a draft type that would crash naive code (a non-string) and by
asserting a deliberately-raising constraint set still yields PASS; the
model-facing-only contract is proven by asserting the report is a
distinct artefact the contributor returns to the chain (not user-render)
and that the PASS path emits nothing.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
KEEP_PACE_DIR = (
    REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks" / "keep_pace"
)
sys.path.insert(0, str(KEEP_PACE_DIR))

from draft_gate import (  # noqa: E402
    Verdict,
    build_draft_gate_contributor,
    gate,
)


def test_AC_KP9_4_fail_open_on_non_string_draft() -> None:
    """A non-string draft must not crash the gate — it fails open (PASS)
    so a malformed draft never blocks a send."""
    result = gate(None)  # type: ignore[arg-type]
    assert result.passed()
    assert result.verdict == Verdict.PASS


def test_AC_KP9_4_fail_open_on_raising_constraint_set() -> None:
    """A constraint set that raises mid-check fails open (PASS) — the
    gate's own bug can never block a send."""

    class _Boom:
        # A "constraint tuple" whose iteration raises.
        def __iter__(self):
            raise RuntimeError("deliberate constraint-set crash")

    result = gate("Aaron settles in at his own pod.", constraints=_Boom())  # type: ignore[arg-type]
    assert result.passed(), "a raising constraint set must fail open to PASS"


def test_AC_KP9_4_block_report_is_model_facing_artefact() -> None:
    """The block reason is a MODEL-FACING report artefact — it carries
    the internal layer/label tagging the user never sees, and it is only
    available via the explicit model_facing_report() accessor (not a
    user-render path)."""
    result = gate("The fix is in retrieval.py.")
    assert result.blocked()
    report = result.model_facing_report()
    assert report  # model gets a report
    assert "[keep-pace draft-gate]" in report  # internal tagging, model-only
    assert "L1" in report


def test_AC_KP9_4_pass_emits_no_report() -> None:
    """A clean draft passes and carries NO reasons — nothing to surface
    to the model, nothing to the user."""
    result = gate("Done — your fiction batch is queued.")
    assert result.passed()
    assert result.model_facing_report() == ""
    assert result.reasons == []


def test_AC_KP9_4_contributor_returns_none_on_pass() -> None:
    """On PASS the chain contributor returns None (silent) — no user
    message, no model noise. The block/flag report is the ONLY non-None
    return, and it is the model-facing report (chain surfaces it to the
    model, not the user)."""
    contributor = build_draft_gate_contributor()
    clean = {
        "tool_name": "reply",
        "tool_input": {"message": "Your batch is queued and running."},
    }
    assert contributor(clean) is None

    leaky = {
        "tool_name": "reply",
        "tool_input": {"message": "see §14 of the roadmap"},
    }
    report = contributor(leaky)
    assert report is not None
    assert "[keep-pace draft-gate]" in report


def test_AC_KP9_4_contributor_fail_soft_on_garbage_envelope() -> None:
    """A garbage envelope yields None (fail-soft) — the contributor
    never raises into the chain (composes with AC.KP0.4 fail-open)."""
    contributor = build_draft_gate_contributor()
    assert contributor(None) is None  # type: ignore[arg-type]
    assert contributor({"tool_name": 123, "tool_input": "not-a-dict"}) is None
