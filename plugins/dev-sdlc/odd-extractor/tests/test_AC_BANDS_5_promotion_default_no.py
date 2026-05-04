"""AC.BANDS.5 — PLAUSIBLE→VERIFIED requires explicit_yes=True per
Decision I; silent promotion refused.

- promote() factory rejects PLAUSIBLE→VERIFIED without explicit_yes.
- promote() factory accepts PLAUSIBLE→VERIFIED with explicit_yes=True.
- promote() factory accepts other promotions (HYPOTHESISED→PLAUSIBLE,
  HYPOTHESISED→VERIFIED) without explicit_yes.
- demote() factory accepts demotions without explicit_yes (asymmetric).
- apply_ratification_action also rejects PLAUSIBLE→VERIFIED without
  explicit_yes (defense in depth — even if a caller bypasses the
  factory and constructs a raw RatificationAction).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from loam_odd_extractor import (
    BandedAC,
    ConfidenceBand,
    Evidence,
    RatificationAction,
    RatificationRefusedError,
    apply_ratification_action,
    demote,
    promote,
)


# ---- factory-level enforcement ------------------------------------


def test_promote_plausible_to_verified_without_explicit_yes_refused() -> None:
    """The default-no path raises RatificationRefusedError."""
    with pytest.raises(RatificationRefusedError) as excinfo:
        promote(
            ac_id="AC.X",
            from_band=ConfidenceBand.PLAUSIBLE,
            to_band=ConfidenceBand.VERIFIED,
            # explicit_yes omitted → default False
        )
    assert "explicit_yes" in str(excinfo.value)
    assert "Decision I" in str(excinfo.value)


def test_promote_plausible_to_verified_with_explicit_yes_succeeds() -> None:
    action = promote(
        ac_id="AC.X",
        from_band=ConfidenceBand.PLAUSIBLE,
        to_band=ConfidenceBand.VERIFIED,
        explicit_yes=True,
    )
    assert action.kind == "promote"
    assert action.explicit_yes is True
    assert action.from_band is ConfidenceBand.PLAUSIBLE
    assert action.to_band is ConfidenceBand.VERIFIED


def test_promote_hypothesised_to_plausible_no_explicit_yes_needed() -> None:
    action = promote(
        ac_id="AC.X",
        from_band=ConfidenceBand.HYPOTHESISED,
        to_band=ConfidenceBand.PLAUSIBLE,
    )
    assert action.kind == "promote"
    assert action.explicit_yes is False


def test_promote_hypothesised_to_verified_no_explicit_yes_needed() -> None:
    """The asymmetric rule applies only to PLAUSIBLE→VERIFIED."""
    action = promote(
        ac_id="AC.X",
        from_band=ConfidenceBand.HYPOTHESISED,
        to_band=ConfidenceBand.VERIFIED,
    )
    assert action.kind == "promote"
    assert action.explicit_yes is False


def test_promote_rejects_same_band() -> None:
    """promote(X→X) raises (no movement)."""
    with pytest.raises(RatificationRefusedError):
        promote(
            ac_id="AC.X",
            from_band=ConfidenceBand.PLAUSIBLE,
            to_band=ConfidenceBand.PLAUSIBLE,
        )


def test_promote_rejects_downward_movement() -> None:
    """promote(VERIFIED→PLAUSIBLE) raises — that's a demotion."""
    with pytest.raises(RatificationRefusedError):
        promote(
            ac_id="AC.X",
            from_band=ConfidenceBand.VERIFIED,
            to_band=ConfidenceBand.PLAUSIBLE,
        )


def test_demote_no_explicit_yes_needed() -> None:
    """Demotion is asymmetric — no explicit_yes."""
    action = demote(
        ac_id="AC.X",
        from_band=ConfidenceBand.VERIFIED,
        to_band=ConfidenceBand.PLAUSIBLE,
    )
    assert action.kind == "demote"


def test_demote_rejects_same_band() -> None:
    with pytest.raises(RatificationRefusedError):
        demote(
            ac_id="AC.X",
            from_band=ConfidenceBand.VERIFIED,
            to_band=ConfidenceBand.VERIFIED,
        )


def test_demote_rejects_upward_movement() -> None:
    with pytest.raises(RatificationRefusedError):
        demote(
            ac_id="AC.X",
            from_band=ConfidenceBand.PLAUSIBLE,
            to_band=ConfidenceBand.VERIFIED,
        )


def test_promote_empty_ac_id_refused() -> None:
    with pytest.raises(RatificationRefusedError):
        promote(
            ac_id="",
            from_band=ConfidenceBand.HYPOTHESISED,
            to_band=ConfidenceBand.PLAUSIBLE,
        )


# ---- apply-level defense-in-depth ---------------------------------


def test_apply_rejects_plausible_to_verified_without_explicit_yes(
    tmp_path: Path,
) -> None:
    """A caller that bypasses the factory and constructs
    RatificationAction(...) directly with PLAUSIBLE→VERIFIED +
    explicit_yes=False is still rejected at apply time.
    """
    direct_action = RatificationAction(
        kind="promote",
        ac_id="AC.X",
        from_band=ConfidenceBand.PLAUSIBLE,
        to_band=ConfidenceBand.VERIFIED,
        explicit_yes=False,  # bypassed factory
    )
    workspace_root = tmp_path / "ws"
    workspace_root.mkdir()
    banded_acs = [
        BandedAC(
            ac_id="AC.X",
            text="x",
            confidence=ConfidenceBand.PLAUSIBLE,
            evidence=Evidence(
                kind="source",
                citations=["src.py:1"],
            ),
        )
    ]
    with pytest.raises(RatificationRefusedError):
        apply_ratification_action(
            direct_action,
            banded_acs=banded_acs,
            workspace_root=workspace_root,
            repo_id="test-repo",
        )
