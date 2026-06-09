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

"""AC.CLG.4 — any internal guard error yields a PASS verdict
(fail-open), the guard adds no LLM/API call to the send path, and
every existing gate behaviour (AC.KP9.*) is preserved.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
KEEP_PACE_DIR = (
    REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks" / "keep_pace"
)
sys.path.insert(0, str(KEEP_PACE_DIR))

import claim_guard  # noqa: E402
from draft_gate import Verdict, gate  # noqa: E402


def test_AC_CLG_4_query_error_fails_open_to_pass(monkeypatch) -> None:
    """A raising ground-truth query (loam_cli absent, git wedged,
    anything) yields PASS — a guard error can NEVER block or flag a
    send."""

    def _boom(topic: str) -> dict:
        raise RuntimeError("ground truth unreachable")

    monkeypatch.setattr(claim_guard, "_default_query", _boom)
    draft = "The widget pipeline revamp isn't planned."
    result = gate(draft)
    assert result.verdict == Verdict.PASS
    assert not [r for r in result.reasons if r.layer == "CG"]


def test_AC_CLG_4_no_llm_or_api_in_the_send_path() -> None:
    """The guard's detection + verification are deterministic: the
    claim-guard module imports no LLM client, no Anthropic SDK, no API
    key surface (the feedback_no_anthropic_api_key hard rule, D4)."""
    source = (KEEP_PACE_DIR / "claim_guard.py").read_text(encoding="utf-8")
    for forbidden in ("anthropic", "ANTHROPIC_API_KEY", "claude_print"):
        assert forbidden not in source, (
            f"the send path must carry no LLM/API surface: {forbidden!r}"
        )


def test_AC_CLG_4_existing_gate_behaviour_preserved(monkeypatch) -> None:
    """AC.KP9.* spot-checks alongside the new layer (the full KP9
    suite is the sweep guard): Layer 1 still BLOCKs a jargon leak —
    even when the claim guard also fires (BLOCK beats FLAG); Layer C
    still FLAGs the seeded canon contradiction; clean drafts still
    PASS."""
    monkeypatch.setattr(
        claim_guard,
        "_default_query",
        lambda t: {"matches": [], "searched": ("x",), "unsearched": ("y",)},
    )
    # Layer 1 leak (a file path) + a work-state claim: BLOCK wins.
    leaky = "See framework/tools/loam/cli.py — the revamp isn't planned."
    assert gate(leaky).verdict == Verdict.BLOCK
    # Layer C seeded canon contradiction still FLAGs.
    canon = "In this scene Aaron settles in at his own pod and starts the run."
    result = gate(canon)
    assert result.verdict == Verdict.FLAG
    assert any(r.layer == "LC" for r in result.reasons)
    # A clean draft still passes.
    assert gate("Dinner at seven works for me.").verdict == Verdict.PASS
    # Fail-open on a non-string draft (the existing AC.KP9.4 contract).
    assert gate(None).verdict == Verdict.PASS  # type: ignore[arg-type]
