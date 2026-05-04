"""AC.BANDS.1 — Banded AC schema (ConfidenceBand + Evidence + BandedAC).

- ConfidenceBand is a str enum with three values.
- Evidence is a Pydantic model with extra='forbid'.
- BandedAC is a Pydantic model with required ac_id + text + confidence
  + evidence; backing_files defaults to [].
- model_dump round-trips through dict shape (Cycle 1's RawACs.acs:
  list[dict] persistence layer).
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from loam_odd_extractor import (
    BandedAC,
    ConfidenceBand,
    Evidence,
)


def test_confidence_band_is_str_enum_with_three_values() -> None:
    """ConfidenceBand has exactly the three locked values."""
    assert ConfidenceBand.VERIFIED.value == "VERIFIED"
    assert ConfidenceBand.PLAUSIBLE.value == "PLAUSIBLE"
    assert ConfidenceBand.HYPOTHESISED.value == "HYPOTHESISED"
    assert len(ConfidenceBand) == 3
    # str-mixin: serializes verbatim.
    assert str(ConfidenceBand.VERIFIED.value) == "VERIFIED"


def test_evidence_extra_forbid() -> None:
    """Evidence rejects unknown keys at construction."""
    with pytest.raises(ValidationError):
        Evidence(
            kind="test",
            citations=["x"],
            repo_sha="abc",
            unknown_field="boom",  # type: ignore[call-arg]
        )


def test_banded_ac_extra_forbid() -> None:
    """BandedAC rejects unknown keys at construction."""
    with pytest.raises(ValidationError):
        BandedAC(
            ac_id="AC.X",
            text="x",
            confidence=ConfidenceBand.HYPOTHESISED,
            evidence=Evidence(kind="inference", rationale="x"),
            unknown_field="boom",  # type: ignore[call-arg]
        )


def test_banded_ac_required_fields() -> None:
    """ac_id, text, confidence, evidence are required."""
    with pytest.raises(ValidationError):
        BandedAC(text="x", confidence=ConfidenceBand.HYPOTHESISED)  # type: ignore[call-arg]


def test_banded_ac_ac_id_non_empty() -> None:
    """ac_id must be non-empty."""
    with pytest.raises(ValidationError):
        BandedAC(
            ac_id="",
            text="x",
            confidence=ConfidenceBand.HYPOTHESISED,
            evidence=Evidence(kind="inference", rationale="x"),
        )


def test_banded_ac_text_non_empty() -> None:
    """text must be non-empty."""
    with pytest.raises(ValidationError):
        BandedAC(
            ac_id="AC.X",
            text="",
            confidence=ConfidenceBand.HYPOTHESISED,
            evidence=Evidence(kind="inference", rationale="x"),
        )


def test_banded_ac_round_trip_via_model_dump() -> None:
    """model_dump produces a dict that round-trips through
    model_validate. This is the AC.BANDS.1 persistence-layer
    round-trip (RawACs.acs: list[dict] is the storage shape).
    """
    original = BandedAC(
        ac_id="AC.RT.1",
        text="round-trip AC",
        confidence=ConfidenceBand.VERIFIED,
        evidence=Evidence(
            kind="test",
            citations=["tests/test_x.py::test_y"],
            repo_sha="abc1234",
        ),
        backing_files=["app/x.py"],
    )
    dumped = original.model_dump()
    assert isinstance(dumped, dict)
    assert dumped["ac_id"] == "AC.RT.1"
    assert dumped["confidence"] == "VERIFIED"
    assert dumped["evidence"]["kind"] == "test"
    assert dumped["evidence"]["citations"] == ["tests/test_x.py::test_y"]
    assert dumped["evidence"]["repo_sha"] == "abc1234"
    assert dumped["backing_files"] == ["app/x.py"]

    restored = BandedAC.model_validate(dumped)
    assert restored == original


def test_banded_ac_round_trip_for_all_three_bands() -> None:
    """Each band variant survives the model_dump → model_validate cycle."""
    cases = [
        BandedAC(
            ac_id="AC.V",
            text="verified",
            confidence=ConfidenceBand.VERIFIED,
            evidence=Evidence(
                kind="test",
                citations=["t.py::test_v"],
                repo_sha="sha-v",
            ),
        ),
        BandedAC(
            ac_id="AC.P",
            text="plausible",
            confidence=ConfidenceBand.PLAUSIBLE,
            evidence=Evidence(
                kind="source",
                citations=["src.py:10"],
            ),
        ),
        BandedAC(
            ac_id="AC.H",
            text="hypothesised",
            confidence=ConfidenceBand.HYPOTHESISED,
            evidence=Evidence(
                kind="inference",
                rationale="LLM inferred this from the codebase shape.",
            ),
        ),
    ]
    for original in cases:
        dumped = original.model_dump()
        restored = BandedAC.model_validate(dumped)
        assert restored == original


def test_banded_ac_default_backing_files_empty() -> None:
    """backing_files defaults to []."""
    ac = BandedAC(
        ac_id="AC.X",
        text="x",
        confidence=ConfidenceBand.HYPOTHESISED,
        evidence=Evidence(
            kind="inference",
            rationale="inferred",
        ),
    )
    assert ac.backing_files == []
