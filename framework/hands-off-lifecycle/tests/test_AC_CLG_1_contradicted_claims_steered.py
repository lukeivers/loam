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

"""AC.CLG.1 — a contradicted work-state claim (positive OR negative)
cannot pass silently: the model receives a model-facing steer naming
the claim AND the contradicting evidence before the draft is sent; the
steer is never rendered as user-facing text (it rides the gate's
AC.KP9.4 model-facing-only contract as a FLAG, and is never a BLOCK —
D2 ★ steer-not-block).

Detection grammar / verification order / steer wording are the
builder's call; these tests pin the outcome via an injected
ground-truth query (the test seam).
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
from claim_guard import check_claims  # noqa: E402
from draft_gate import Verdict, gate  # noqa: E402


def _ground_truth_with(matches: list[dict]) -> dict:
    return {
        "matches": matches,
        "searched": ("loam plan-docs + git apply/seal subjects",),
        "unsearched": ("scratch artefacts", "chat history"),
    }


_PARTIAL_MATCH = {
    "project": "loam",
    "slug": "widget-pipeline-revamp",
    "title": "widget pipeline revamp",
    "build_state": "partially-sealed",
    "seal_evidence": ("abc1234 chore(amend): widget-pipeline-revamp …",),
    "in_sealed_archive": False,
}

_PENDING_MATCH = {
    "project": "loam",
    "slug": "widget-pipeline-revamp",
    "title": "widget pipeline revamp",
    "build_state": "no-build-evidence",
    "seal_evidence": (),
    "in_sealed_archive": False,
}


def test_AC_CLG_1_negative_existence_claim_contradicted() -> None:
    """The 06-09 shape: 'X isn't planned' while X's plan + build
    evidence sit on file → a steer naming claim + evidence."""
    draft = "The widget pipeline revamp isn't planned at all."
    steers = check_claims(
        draft, query=lambda t: _ground_truth_with([_PARTIAL_MATCH])
    )
    assert len(steers) == 1
    s = steers[0]
    assert s.label == "claim-contradicts-stored-state"
    # The steer carries the claim …
    assert "isn't planned" in s.detail
    # … AND the contradicting evidence (identity + real state + commit).
    assert "widget pipeline revamp" in s.detail
    assert "partially-sealed" in s.detail
    assert "abc1234" in s.detail


def test_AC_CLG_1_negative_build_claim_contradicted_by_evidence() -> None:
    """'X was never built' while X carries seal evidence → steered;
    the same claim against a no-evidence plan is TRUE → no steer."""
    draft = "That widget pipeline revamp was never built."
    steered = check_claims(
        draft, query=lambda t: _ground_truth_with([_PARTIAL_MATCH])
    )
    assert len(steered) == 1
    assert "partially-sealed" in steered[0].detail

    true_negative = check_claims(
        draft, query=lambda t: _ground_truth_with([_PENDING_MATCH])
    )
    assert true_negative == [], (
        "a build-class negative that ground truth CONFIRMS must pass"
    )


def test_AC_CLG_1_positive_overclaim_contradicted() -> None:
    """'X is sealed' while ground truth shows the plan with ZERO build
    evidence → the over-claim is steered with the evidence."""
    draft = "Good news: the widget pipeline revamp is sealed."
    steers = check_claims(
        draft, query=lambda t: _ground_truth_with([_PENDING_MATCH])
    )
    assert len(steers) == 1
    assert "no-build-evidence" in steers[0].detail


def test_AC_CLG_1_steer_is_model_facing_flag_never_block(
    monkeypatch,
) -> None:
    """Through the production gate: the steer arrives as a FLAG-class
    model-facing reason (layer CG) — never a BLOCK (D2 steer-not-
    block), and only via the model-facing report artefact."""
    monkeypatch.setattr(
        claim_guard,
        "_default_query",
        lambda t: _ground_truth_with([_PARTIAL_MATCH]),
    )
    draft = "The widget pipeline revamp isn't planned."
    result = gate(draft)
    assert result.verdict == Verdict.FLAG, (
        f"a contradicted claim steers (FLAG), never blocks: {result.verdict}"
    )
    cg = [r for r in result.reasons if r.layer == "CG"]
    assert cg, "the steer must ride the gate's reason surface"
    report = result.model_facing_report()
    assert "widget pipeline revamp" in report
    assert report.startswith("[keep-pace draft-gate]"), (
        "the steer is a model-facing artefact (AC.KP9.4), not user text"
    )
