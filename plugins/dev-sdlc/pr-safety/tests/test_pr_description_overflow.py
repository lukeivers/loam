"""PR description body-overflow truncation — Surface #7."""

from __future__ import annotations

from pathlib import Path

from loam_odd_extractor.bands import BandedAC, ConfidenceBand, Evidence

from loam_pr_safety.installers.pr_template import (
    _PR_DESCRIPTION_CHAR_CEILING,
    render_pr_description,
)
from loam_pr_safety.spec import (
    GateAction,
    GateDecision,
    TouchedAC,
)


def _make_long_ac(idx: int, padding: int = 1500) -> BandedAC:
    """Build an AC with deliberately verbose text to force overflow."""
    big_text = (
        f"AC {idx} description with very long provenance — "
        + "x" * padding
    )
    return BandedAC(
        ac_id=f"AC.LONG.{idx}",
        text=big_text,
        confidence=ConfidenceBand.PLAUSIBLE,
        evidence=Evidence(
            kind="source",
            citations=[f"src/file{idx}.py:1-100"],
            repo_sha=None,
            rationale=None,
        ),
        backing_files=[f"src/file{idx}.py"],
    )


def test_overflow_triggers_truncation(tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / ".loam").mkdir()

    # 50 long ACs ×  ~1500 chars each = ~75000 chars; well over 60K.
    touched = [
        TouchedAC(
            ac=_make_long_ac(i),
            touch_kind="citation_line",
            touched_hunks=[],
        )
        for i in range(50)
    ]
    decision = GateDecision(
        action=GateAction.SURFACE_DECISION,
        requires_ratification=True,
        touched_acs=touched,
        novel=[],
        safety_profile="dev",
        reason="overflow test",
    )

    md = render_pr_description(
        decision, workspace_root=ws, repo_id="overflow-test"
    )

    # Truncation footer present.
    assert "(truncated;" in md
    assert "audit-log" in md
    # Total under ceiling (with footer accounted for).
    assert len(md) <= _PR_DESCRIPTION_CHAR_CEILING + 500


def test_under_ceiling_no_truncation(tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / ".loam").mkdir()

    touched = [
        TouchedAC(
            ac=BandedAC(
                ac_id="AC.SHORT.1",
                text="short ac",
                confidence=ConfidenceBand.PLAUSIBLE,
                evidence=Evidence(
                    kind="source",
                    citations=["a.py:1"],
                    repo_sha=None,
                    rationale=None,
                ),
                backing_files=["a.py"],
            ),
            touch_kind="citation_line",
            touched_hunks=[],
        )
    ]
    decision = GateDecision(
        action=GateAction.SURFACE_DECISION,
        requires_ratification=True,
        touched_acs=touched,
        novel=[],
        safety_profile="dev",
        reason="under-ceiling",
    )

    md = render_pr_description(
        decision, workspace_root=ws, repo_id="under"
    )
    assert "(truncated" not in md
    assert "AC.SHORT.1" in md


def test_overflow_truncation_is_deterministic(tmp_path: Path) -> None:
    """Same overflow input produces same output."""
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / ".loam").mkdir()

    touched = [
        TouchedAC(
            ac=_make_long_ac(i),
            touch_kind="citation_line",
            touched_hunks=[],
        )
        for i in range(50)
    ]
    decision = GateDecision(
        action=GateAction.SURFACE_DECISION,
        requires_ratification=True,
        touched_acs=touched,
        novel=[],
        safety_profile="dev",
        reason="determinism test",
    )

    md_a = render_pr_description(
        decision, workspace_root=ws, repo_id="det"
    )
    md_b = render_pr_description(
        decision, workspace_root=ws, repo_id="det"
    )
    assert md_a == md_b
