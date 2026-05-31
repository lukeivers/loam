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

"""AC.SOL-GATE.* — the audit gate detects + surfaces a claim-vs-reality
divergence, passes agreement clean, and composes on ALL_GATES.

  * AC.SOL-GATE.1 — divergence detected: a claimed status contradicting the
    derived record is caught + the specific claim + contradiction reported.
  * AC.SOL-GATE.2 — agreement passes clean (low false-positive).
  * AC.SOL-GATE.3 — the release-gate arm runs in the SAME ALL_GATES pass.
"""

from __future__ import annotations

from pathlib import Path

from loam_cli.audit.comparator import (
    ClaimedStatus,
    compare_claim,
    extract_claims_from_doc,
)
from loam_cli.audit.probe import Liveness
from loam_cli.audit.record import ComponentState, StateOfLoam
from loam_cli.release import gates


def _record() -> StateOfLoam:
    return StateOfLoam(
        head_sha="abc123",
        components=(
            ComponentState("fbm", Liveness.MERGED, "component", "seal merged"),
            ComponentState("widget", Liveness.DARK, "hook", "no hook in config"),
            ComponentState("maybe", Liveness.UNKNOWN, "component", "bogus sha"),
        ),
    )


def test_AC_SOL_GATE_1_divergence_detected_dark_for_live() -> None:
    """A doc claiming a LIVE component is DARK is caught; the divergence
    names the claim + the ground-truth contradiction."""
    d = compare_claim(
        ClaimedStatus(component="fbm", claim_token="dark", source="plan.md:6"),
        _record(),
    )
    assert d is not None
    assert d.component == "fbm"
    assert d.claimed == "dark"
    assert d.derived is Liveness.MERGED
    assert "ground truth says merged" in d.detail


def test_AC_SOL_GATE_1_divergence_detected_live_for_dark() -> None:
    """The reverse: a doc claiming a DARK component is LIVE is caught."""
    d = compare_claim(
        ClaimedStatus(component="widget", claim_token="live", source="x"),
        _record(),
    )
    assert d is not None
    assert d.derived is Liveness.DARK


def test_AC_SOL_GATE_2_agreement_passes_clean() -> None:
    """An accurate claim (matching the derived side) yields NO divergence
    — low false-positive."""
    assert (
        compare_claim(
            ClaimedStatus(component="fbm", claim_token="live", source="x"),
            _record(),
        )
        is None
    )
    assert (
        compare_claim(
            ClaimedStatus(component="widget", claim_token="dark", source="x"),
            _record(),
        )
        is None
    )


def test_AC_SOL_GATE_2_unknown_and_uncovered_never_false_flag() -> None:
    """Fail-safe: an UNKNOWN derived class never produces a divergence;
    a component the record does not cover never false-flags; an
    uninterpretable claim token never false-flags."""
    # UNKNOWN derived class → no divergence (indeterminate, not a false RED).
    assert (
        compare_claim(
            ClaimedStatus(component="maybe", claim_token="dark", source="x"),
            _record(),
        )
        is None
    )
    # Component not in the record → no divergence.
    assert (
        compare_claim(
            ClaimedStatus(component="nonexistent", claim_token="dark", source="x"),
            _record(),
        )
        is None
    )
    # Unrecognised claim token → no divergence (NL surface out of scope).
    assert (
        compare_claim(
            ClaimedStatus(component="fbm", claim_token="purple", source="x"),
            _record(),
        )
        is None
    )


def test_AC_SOL_GATE_structured_extraction_only() -> None:
    """Claim extraction is the BOUNDED structured-status surface (D4-A):
    `<component>: <status>` lines are extracted; free prose is not."""
    text = (
        "# Doc\n"
        "fbm: dark\n"
        "widget status: live\n"
        "Some free prose that rides fbm's existing hook chain.\n"
        "uncovered-thing: dark\n"
    )
    claims = extract_claims_from_doc(
        text, source="doc.md", components=frozenset({"fbm", "widget"})
    )
    names = {(c.component, c.claim_token) for c in claims}
    assert ("fbm", "dark") in names
    assert ("widget", "live") in names
    # Free-prose "rides existing X" is NOT extracted (out of scope, D4).
    assert all("prose" not in c.component for c in claims)
    # A component outside the covered set is filtered out.
    assert ("uncovered-thing", "dark") not in names


def test_AC_SOL_GATE_3_composes_in_all_gates(
    staged_repo: Path, fixture_version: str
) -> None:
    """The substrate-audit gate is part of ALL_GATES and runs in the SAME
    run_all pass — one report, no parallel CI (leverage-loam-first)."""
    assert gates.check_substrate_audit in gates.ALL_GATES
    # The boundary-respected gate (AC.BLOCK-ENFORCE.*, N1) appended a 9th.
    assert len(gates.ALL_GATES) == 9

    results = gates.run_all(staged_repo, fixture_version)
    names = [r.name for r in results]
    assert "substrate-audit" in names
    assert len(results) == 9
    # The staged fixture carries no diverging status doc → the gate passes.
    by_name = {r.name: r for r in results}
    assert by_name["substrate-audit"].ok is True


def test_AC_SOL_GATE_3_release_gate_hard_blocks_a_planted_divergence(
    fixture_version: str, tmp_path: Path
) -> None:
    """The release-gate arm HARD-BLOCKs (D3): plant a doc claiming a live
    component is dark, point check_substrate_audit at it (against the real
    repo's default record), and prove it returns RED + names the claim.

    The planted doc is a FIXTURE under tmp_path (plan halt-trigger 5: never
    mutate a real canonical doc); the `audited_docs` override threads its
    repo-relative path through the gate.
    """
    real_repo = Path(__file__).resolve().parents[4]
    # Place the planted doc UNDER the real repo (in a tmp-named docs file)
    # so the gate's `repo_root / rel` resolution reaches it, then clean up.
    planted = real_repo / "docs" / "_sol_planted_fixture.md"
    planted.write_text(
        "# Planted (fixture)\n\nfbm-episode-store: dark\n", encoding="utf-8"
    )
    try:
        res = gates.check_substrate_audit(
            real_repo,
            fixture_version,
            audited_docs=("docs/_sol_planted_fixture.md",),
        )
    finally:
        planted.unlink(missing_ok=True)
    assert res.ok is False, "a dark-for-live claim must HARD-BLOCK the gate"
    assert res.name == "substrate-audit"
    assert "fbm-episode-store" in res.message
    assert "DIVERGE" in res.message


def test_AC_SOL_GATE_2_release_gate_passes_agreement_clean(
    fixture_version: str,
) -> None:
    """The release-gate arm passes clean when an audited doc's claims AGREE
    with ground truth (low false-positive)."""
    real_repo = Path(__file__).resolve().parents[4]
    accurate = real_repo / "docs" / "_sol_accurate_fixture.md"
    accurate.write_text(
        "# Accurate (fixture)\n\nfbm-episode-store: merged\n", encoding="utf-8"
    )
    try:
        res = gates.check_substrate_audit(
            real_repo,
            fixture_version,
            audited_docs=("docs/_sol_accurate_fixture.md",),
        )
    finally:
        accurate.unlink(missing_ok=True)
    assert res.ok is True
