"""AC.BANDS.2 — Per-band evidence requirements (model_validator).

- VERIFIED requires evidence.kind='test' + repo_sha non-null +
  citations non-empty.
- PLAUSIBLE requires evidence.kind='source' + citations non-empty.
- HYPOTHESISED requires evidence.kind='inference' + rationale
  non-empty (and non-whitespace-only).
- Each rejection raises pydantic.ValidationError with a message
  naming the offending condition.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from loam_odd_extractor import BandedAC, ConfidenceBand, Evidence


# ---- VERIFIED ------------------------------------------------------


def test_verified_happy_path() -> None:
    """All required VERIFIED fields present → constructs cleanly."""
    ac = BandedAC(
        ac_id="AC.V.1",
        text="verified AC",
        confidence=ConfidenceBand.VERIFIED,
        evidence=Evidence(
            kind="test",
            citations=["t.py::test_x"],
            repo_sha="abc1234",
        ),
    )
    assert ac.confidence is ConfidenceBand.VERIFIED


def test_verified_rejects_wrong_evidence_kind() -> None:
    """VERIFIED + evidence.kind != 'test' raises."""
    with pytest.raises(ValidationError) as excinfo:
        BandedAC(
            ac_id="AC.V.bad",
            text="x",
            confidence=ConfidenceBand.VERIFIED,
            evidence=Evidence(
                kind="source",
                citations=["src.py:1"],
            ),
        )
    assert "VERIFIED" in str(excinfo.value)
    assert "test" in str(excinfo.value)


def test_verified_rejects_missing_repo_sha() -> None:
    """VERIFIED without repo_sha raises."""
    with pytest.raises(ValidationError) as excinfo:
        BandedAC(
            ac_id="AC.V.bad",
            text="x",
            confidence=ConfidenceBand.VERIFIED,
            evidence=Evidence(
                kind="test",
                citations=["t.py::test_x"],
                repo_sha=None,
            ),
        )
    assert "repo_sha" in str(excinfo.value)


def test_verified_rejects_empty_citations() -> None:
    """VERIFIED with empty citations raises."""
    with pytest.raises(ValidationError) as excinfo:
        BandedAC(
            ac_id="AC.V.bad",
            text="x",
            confidence=ConfidenceBand.VERIFIED,
            evidence=Evidence(
                kind="test",
                citations=[],
                repo_sha="abc",
            ),
        )
    assert "citations" in str(excinfo.value)


# ---- PLAUSIBLE -----------------------------------------------------


def test_plausible_happy_path() -> None:
    ac = BandedAC(
        ac_id="AC.P.1",
        text="plausible AC",
        confidence=ConfidenceBand.PLAUSIBLE,
        evidence=Evidence(
            kind="source",
            citations=["src.py:10-20"],
        ),
    )
    assert ac.confidence is ConfidenceBand.PLAUSIBLE


def test_plausible_rejects_wrong_evidence_kind() -> None:
    with pytest.raises(ValidationError) as excinfo:
        BandedAC(
            ac_id="AC.P.bad",
            text="x",
            confidence=ConfidenceBand.PLAUSIBLE,
            evidence=Evidence(
                kind="inference",
                rationale="x",
            ),
        )
    assert "PLAUSIBLE" in str(excinfo.value)
    assert "source" in str(excinfo.value)


def test_plausible_rejects_empty_citations() -> None:
    with pytest.raises(ValidationError) as excinfo:
        BandedAC(
            ac_id="AC.P.bad",
            text="x",
            confidence=ConfidenceBand.PLAUSIBLE,
            evidence=Evidence(
                kind="source",
                citations=[],
            ),
        )
    assert "citations" in str(excinfo.value)


# ---- HYPOTHESISED --------------------------------------------------


def test_hypothesised_happy_path() -> None:
    """HYPOTHESISED with non-empty rationale + no citations is valid."""
    ac = BandedAC(
        ac_id="AC.H.1",
        text="hypothesised AC",
        confidence=ConfidenceBand.HYPOTHESISED,
        evidence=Evidence(
            kind="inference",
            citations=[],
            rationale="LLM inferred from comments + missing retry code.",
        ),
    )
    assert ac.confidence is ConfidenceBand.HYPOTHESISED


def test_hypothesised_rejects_wrong_evidence_kind() -> None:
    with pytest.raises(ValidationError) as excinfo:
        BandedAC(
            ac_id="AC.H.bad",
            text="x",
            confidence=ConfidenceBand.HYPOTHESISED,
            evidence=Evidence(
                kind="test",
                citations=["t.py::x"],
                repo_sha="abc",
            ),
        )
    assert "HYPOTHESISED" in str(excinfo.value)
    assert "inference" in str(excinfo.value)


def test_hypothesised_rejects_missing_rationale() -> None:
    with pytest.raises(ValidationError) as excinfo:
        BandedAC(
            ac_id="AC.H.bad",
            text="x",
            confidence=ConfidenceBand.HYPOTHESISED,
            evidence=Evidence(
                kind="inference",
                rationale=None,
            ),
        )
    assert "rationale" in str(excinfo.value)


def test_hypothesised_rejects_whitespace_rationale() -> None:
    """Whitespace-only rationale is treated as empty."""
    with pytest.raises(ValidationError) as excinfo:
        BandedAC(
            ac_id="AC.H.bad",
            text="x",
            confidence=ConfidenceBand.HYPOTHESISED,
            evidence=Evidence(
                kind="inference",
                rationale="   \n  ",
            ),
        )
    assert "rationale" in str(excinfo.value)
