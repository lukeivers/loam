"""AC.WATCH.5 — Domain-batched AC surfacing.

Tests `infer_domain` + `group_by_domain`:

- AC ID prefix path (primary): `AC.<DOMAIN>.<n>` → lowercased domain.
- Loam-internal blocklist: AC.OREK.* / AC.WATCH.* / etc. → fall through.
- File-path-prefix fallback: longest common prefix → last segment.
- `_uncategorised` fallback when neither path produces a domain.
- Determinism: `group_by_domain` produces sorted-key OrderedDict.
"""

from __future__ import annotations

from collections import OrderedDict

from loam_odd_extractor.bands import BandedAC, ConfidenceBand, Evidence
from loam_odd_extractor.domain_batching import (
    LOAM_INTERNAL_AC_NAMESPACES,
    group_by_domain,
    infer_domain,
)
from loam_odd_extractor.proposals import IncrementalProposal


def _make_ac(
    *,
    ac_id: str,
    citations: list[str] | None = None,
    backing_files: list[str] | None = None,
    band: ConfidenceBand = ConfidenceBand.PLAUSIBLE,
) -> BandedAC:
    if band is ConfidenceBand.VERIFIED:
        ev = Evidence(
            kind="test",
            citations=citations or ["tests/t.py::test_x"],
            repo_sha="abc12345",
        )
    elif band is ConfidenceBand.PLAUSIBLE:
        ev = Evidence(
            kind="source",
            citations=citations or ["app/x.rb:1-10"],
        )
    else:
        ev = Evidence(
            kind="inference",
            citations=citations or [],
            rationale="hypothesised",
        )
    return BandedAC(
        ac_id=ac_id,
        text="placeholder",
        confidence=band,
        evidence=ev,
        backing_files=backing_files or [],
    )


def _make_proposal(ac: BandedAC) -> IncrementalProposal:
    return IncrementalProposal(
        ac=ac,
        current_evidence=ac.evidence,
        proposed_new_evidence=ac.evidence,
        confidence_band=ac.confidence,
        drift_kind="backing_file_changed",
        affected_files=tuple(ac.backing_files) or (),
    )


# ---- AC ID prefix path (primary) -----------------------------------


def test_ac_id_prefix_path_simple_domain() -> None:
    ac = _make_ac(ac_id="AC.PAYMENT.1")
    assert infer_domain(ac) == "payment"


def test_ac_id_prefix_path_compound_domain() -> None:
    ac = _make_ac(ac_id="AC.PAYMENT_GATEWAY.3")
    assert infer_domain(ac) == "payment_gateway"


def test_ac_id_prefix_uppercase_normalised() -> None:
    ac = _make_ac(ac_id="AC.RAILS.7")
    assert infer_domain(ac) == "rails"


# ---- Loam-internal blocklist ---------------------------------------


def test_loam_internal_namespace_blocklist_falls_through() -> None:
    """AC IDs in the loam-internal blocklist do NOT surface as
    domain. Fall through to file-path-prefix."""
    ac = _make_ac(
        ac_id="AC.OREK.1",
        backing_files=["plugins/dev-sdlc/odd-extractor/src/x.py"],
    )
    # Falls through to file-path-prefix; "src" is the last segment
    # of the common prefix (filename has dot, so last directory used).
    domain = infer_domain(ac)
    assert domain != "orek"
    assert domain  # non-empty


def test_loam_internal_blocklist_contains_known_namespaces() -> None:
    """Blocklist includes known loam-internal AC namespaces."""
    expected = {"OREK", "BANDS", "WATCH", "PRSG", "DPS1", "DPS2"}
    assert expected.issubset(LOAM_INTERNAL_AC_NAMESPACES)


def test_blocklisted_with_no_files_falls_to_uncategorised() -> None:
    """Blocklisted AC ID + empty backing files + empty citations →
    `_uncategorised`."""
    ac = _make_ac(
        ac_id="AC.WATCH.99",
        backing_files=[],
        citations=[],
    )
    # Note: PLAUSIBLE band requires non-empty citations, so we use
    # HYPOTHESISED here for the empty-citations case.
    ac = _make_ac(
        ac_id="AC.WATCH.99",
        backing_files=[],
        citations=[],
        band=ConfidenceBand.HYPOTHESISED,
    )
    assert infer_domain(ac) == "_uncategorised"


# ---- File-path-prefix fallback -------------------------------------


def test_file_path_prefix_fallback_with_common_directory() -> None:
    """Backing-files share `app/payment/` prefix → domain `payment`."""
    ac = _make_ac(
        ac_id="WATCH-001",  # non-conformant ID
        backing_files=[
            "app/payment/charge.rb",
            "app/payment/refund.rb",
        ],
        # Citations consistent with backing-files prefix so the
        # common-prefix is `app/payment` not just `app`.
        citations=[
            "app/payment/charge.rb:1-10",
            "app/payment/refund.rb:1-10",
        ],
    )
    assert infer_domain(ac) == "payment"


def test_file_path_prefix_uses_citation_paths() -> None:
    """Citations contribute to the path-prefix fallback even when
    backing_files is empty."""
    ac = _make_ac(
        ac_id="WATCH-002",
        backing_files=[],
        citations=[
            "app/auth/login.rb:1-5",
            "app/auth/logout.rb:1-5",
        ],
    )
    assert infer_domain(ac) == "auth"


def test_file_path_prefix_uses_citation_with_test_separator() -> None:
    """Citations of shape `<file>::<test>` contribute file-path."""
    ac = _make_ac(
        ac_id="WATCH-002b",
        backing_files=["app/auth/login.rb"],
        citations=["app/auth/login.rb::test_login"],
    )
    assert infer_domain(ac) == "auth"


def test_file_path_prefix_strips_filename() -> None:
    """A single path like `app/payment/charge.rb` skips the filename
    (which contains a dot) and uses the directory `payment`."""
    ac = _make_ac(
        ac_id="WATCH-003",
        backing_files=["app/payment/charge.rb"],
        citations=["app/payment/charge.rb:1-10"],
    )
    assert infer_domain(ac) == "payment"


def test_file_path_prefix_no_common_prefix_uncategorised() -> None:
    """Backing-files with no common prefix beyond root → falls back
    to `_uncategorised` (no shared directory)."""
    ac = _make_ac(
        ac_id="WATCH-004",
        backing_files=[
            "app/payment/charge.rb",
            "lib/util.rb",
        ],
        # Citations that share no prefix with backing.
        citations=[
            "app/payment/charge.rb:1-5",
            "lib/util.rb:1-5",
        ],
    )
    # Common prefix is empty (no shared first segment); falls
    # through to _uncategorised.
    assert infer_domain(ac) == "_uncategorised"


# ---- _uncategorised fallback ---------------------------------------


def test_uncategorised_for_no_files_no_citations() -> None:
    """Empty backing_files + empty citations + non-conformant AC ID →
    `_uncategorised`."""
    ac = _make_ac(
        ac_id="WATCH-005",
        backing_files=[],
        citations=[],
        band=ConfidenceBand.HYPOTHESISED,
    )
    assert infer_domain(ac) == "_uncategorised"


# ---- group_by_domain determinism -----------------------------------


def test_group_by_domain_returns_sorted_ordered_dict() -> None:
    """Per AC.WATCH.5: deterministic output (sorted keys; insertion-
    order preserved within values)."""
    proposals = [
        _make_proposal(_make_ac(ac_id="AC.PAYMENT.1")),
        _make_proposal(_make_ac(ac_id="AC.AUTH.1")),
        _make_proposal(_make_ac(ac_id="AC.PAYMENT.2")),
    ]
    grouped = group_by_domain(proposals)
    assert isinstance(grouped, OrderedDict)
    keys = list(grouped.keys())
    assert keys == sorted(keys)
    assert keys == ["auth", "payment"]
    assert len(grouped["payment"]) == 2
    assert len(grouped["auth"]) == 1
    # Insertion order within each value list preserved:
    payment_ids = [p.ac_id for p in grouped["payment"]]
    assert payment_ids == ["AC.PAYMENT.1", "AC.PAYMENT.2"]


def test_group_by_domain_is_pure() -> None:
    """Same input → byte-identical output across calls."""
    proposals = [
        _make_proposal(_make_ac(ac_id="AC.PAYMENT.1")),
        _make_proposal(_make_ac(ac_id="AC.AUTH.1")),
    ]
    g1 = group_by_domain(proposals)
    g2 = group_by_domain(proposals)
    assert list(g1.keys()) == list(g2.keys())
    assert [
        p.ac_id for p in g1["payment"]
    ] == [p.ac_id for p in g2["payment"]]


def test_group_by_domain_handles_empty_input() -> None:
    """Empty proposal list → empty OrderedDict."""
    grouped = group_by_domain([])
    assert isinstance(grouped, OrderedDict)
    assert len(grouped) == 0


# ---- Mixed input ---------------------------------------------------


def test_mixed_paths_all_three_buckets() -> None:
    """Input mixing AC ID prefix + file-path fallback +
    `_uncategorised` produces three domains."""
    proposals = [
        _make_proposal(_make_ac(ac_id="AC.PAYMENT.1")),
        _make_proposal(
            _make_ac(
                ac_id="WATCH-006",  # non-conformant
                backing_files=["app/auth/x.rb"],
                citations=["app/auth/x.rb:1-5"],
            )
        ),
        _make_proposal(
            _make_ac(
                ac_id="WATCH-007",
                backing_files=[],
                citations=[],
                band=ConfidenceBand.HYPOTHESISED,
            )
        ),
    ]
    grouped = group_by_domain(proposals)
    assert set(grouped.keys()) == {"payment", "auth", "_uncategorised"}
    assert len(grouped["payment"]) == 1
    assert len(grouped["auth"]) == 1
    assert len(grouped["_uncategorised"]) == 1
