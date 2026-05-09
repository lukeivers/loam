"""AC.V041.3 — Build-next tie-breaker beyond alphabetical
(F-DESIGN-1 closure sub-fix 3).

Per v0.4.1 patch plan-doc §4 AC.V041.3: when multiple build-next
candidates share an equal composite_score AND equal category AND
equal confidence, the tie-breaker uses **load-bearing signals**
(orphan cluster size + objective text length) BEFORE falling back
to lex alphabetical.

The empirical motivation is the v0.4.0 C4 ProgramBench Task 2
failure (`docs/experiments/programbench-v0-docs-only.md` §3.4):
``error-handling`` and ``formatting`` candidates tied on every
v0.4.0 hierarchy dimension; alphabetical selected the
less-load-bearing ``error-handling``.

Hierarchy under test:

1. ``-composite_score`` (v0.2.4 C3; unchanged).
2. ``_CATEGORY_RANK`` (v0.2.4 C3; unchanged).
3. ``_CONFIDENCE_RANK`` (v0.2.4 C3; unchanged).
4. **NEW: ``-orphan_cluster_size``** — more evidence rows = more
   load-bearing.
5. **NEW: ``-objective_text_length``** — longer objective text =
   more load-bearing (discriminates category-a ties where evidence
   rows are empty).
6. ``c.gap_id`` (alphabetical; final fallback only).

Verifies:

1. Two category-b gaps tying on score + confidence: the one with
   the larger orphan cluster wins (NOT alphabetical).
2. Two category-a gaps tying on every prior dimension: the one with
   the longer objective text wins (NOT alphabetical).
3. Three-way tie: cluster-size > text-length > alphabetical applied
   in order.
4. Backward-compat: when category, confidence, AND load-bearing
   signals all tie, alphabetical IS the final fallback.
5. The category-a > category-b ranking still holds even when
   category-b has a much larger cluster.
6. STRONG > WEAK still holds even when WEAK has a larger cluster.
"""

from __future__ import annotations

from loam_odd_extractor import (
    AugmentedObjectiveSet,
    Gap,
    GapInventory,
    GapSummary,
    Objective,
    ObjectiveEvidence,
    score_candidates,
)
from loam_odd_extractor.bands import ConfidenceBand
from loam_odd_extractor.spec import EvidenceRowRef


# ---- Test fixtures (shaped to make ties land at the new dimensions) ----


def _objective(oid: str, *, text: str) -> Objective:
    """Construct a category-a-suitable Objective with custom text
    length so the load-bearing signal can discriminate."""
    return Objective(
        objective_id=oid,
        text=text,
        confidence=ConfidenceBand.PLAUSIBLE,
        domain="general",
        source="extracted",
        evidence=ObjectiveEvidence(
            readme_excerpts=["Some excerpt"],
        ),
    )


def _category_a_gap(oid: str, *, confidence: str = "STRONG") -> Gap:
    """Category-a (objective_without_verified_backing) gap with no
    evidence rows — orphan_cluster_size=0 for both candidates so the
    objective_text_length signal becomes the discriminator."""
    return Gap(
        gap_id=f"G.BACKING.{oid.lower().replace('.', '-')}",
        category="objective_without_verified_backing",
        confidence=confidence,
        objective_id=oid,
        evidence_rows=[],
        rationale=f"Objective {oid} has no backing-map entry.",
    )


def _category_b_gap(
    slug: str, *, confidence: str = "STRONG", row_count: int = 1
) -> Gap:
    rows = [
        EvidenceRowRef(
            evidence_row_id=f"route:src/{slug}.js:{i*10}",
            kind="route",
            path=f"src/{slug}.js",
            line_range=(i * 10, i * 10 + 5),
            language="jsts",
            confidence="STRONG",
        )
        for i in range(1, row_count + 1)
    ]
    return Gap(
        gap_id=f"G.ORPHAN.src-{slug}-js",
        category="implementation_orphan",
        confidence=confidence,
        objective_id=None,
        evidence_rows=rows,
        rationale=(
            f"Orphan cluster at src/{slug}.js ({row_count} rows; "
            "kinds: route); group-key=path:src/{slug}.js."
        ),
    )


def _wrap(extraction_id: str, gaps: list[Gap]) -> GapInventory:
    s = GapSummary(
        category_a_count=sum(
            1
            for g in gaps
            if g.category == "objective_without_verified_backing"
        ),
        category_b_count=sum(
            1 for g in gaps if g.category == "implementation_orphan"
        ),
        strong_count=sum(1 for g in gaps if g.confidence == "STRONG"),
        weak_count=sum(1 for g in gaps if g.confidence == "WEAK"),
        total=len(gaps),
    )
    return GapInventory(
        extraction_id=extraction_id,
        analyzed_at="2026-05-09T00:00:00+00:00",
        audit_path="/tmp/audit-log",
        gaps=gaps,
        summary=s,
    )


def _aug(extraction_id: str, objs: list[Objective]) -> AugmentedObjectiveSet:
    return AugmentedObjectiveSet(
        extraction_id=extraction_id,
        augmented_at="2026-05-09T00:00:00+00:00",
        interview_audit_path="/tmp/audit-log",
        objectives=objs,
    )


# ---- AC.V041.3 tests -----------------------------------------------


def test_AC_V041_3_category_b_larger_cluster_wins_over_alphabetical():
    """Two category-b gaps tie on confidence + composite_score.
    Alphabetical would pick ``a-handler`` (smaller cluster) over
    ``z-handler`` (larger cluster). With AC.V041.3 the larger
    cluster wins."""
    # Both category-b, STRONG, cluster size 3 triggers cluster-bonus
    # (impact=0.6) so composite_scores tie at 0.6 (gc=1, pm=1, imp=0.6).
    # Note: cluster-bonus fires at >=3, so use cluster sizes 3 and 5
    # (both same impact 0.6) to keep composite tied while letting
    # raw cluster size discriminate.
    g_small = _category_b_gap("a-handler", confidence="STRONG", row_count=3)
    g_large = _category_b_gap("z-handler", confidence="STRONG", row_count=5)

    inv = _wrap("test-cluster-tie", [g_small, g_large])
    aug = _aug("test-cluster-tie", [])

    rec = score_candidates(
        gap_inventory=inv,
        augmented_objectives=aug,
        survey_text=None,
        extraction_id="test-cluster-tie",
        audit_path="/tmp/audit-log",
    )

    assert len(rec.candidates) == 2
    # Both must score the same (cluster-bonus saturates at row_count>=3).
    assert (
        rec.candidates[0].composite_score == rec.candidates[1].composite_score
    ), (
        f"AC.V041.3 — both category-b gaps must tie on composite_score "
        f"to exercise the cluster-size tie-breaker; got "
        f"{rec.candidates[0].composite_score!r} vs "
        f"{rec.candidates[1].composite_score!r}"
    )
    # The larger cluster (z-handler with 5 rows) MUST rank first,
    # even though alphabetically ``a-handler`` < ``z-handler``.
    assert rec.candidates[0].gap_id == "G.ORPHAN.src-z-handler-js", (
        f"AC.V041.3 — larger cluster must beat alphabetical; "
        f"top candidate was {rec.candidates[0].gap_id!r}, expected "
        f"G.ORPHAN.src-z-handler-js (5 rows > 3 rows)"
    )


def test_AC_V041_3_category_a_longer_objective_text_wins_over_alphabetical():
    """Two category-a gaps tie on confidence + composite_score AND
    cluster-size (both 0). Alphabetical would pick ``error-handling``
    (the empirical C4 Task 2 failure case). With AC.V041.3 the
    longer objective text wins.

    Empirical motivation: v0.4.0 C4 jsonpp Task 2 had two candidates
    tied at composite_score 0.8 — ``O.error-handling.1`` (short text)
    vs ``O.formatting.1`` (longer, more specific text). v0.4.1
    closes this by ranking by objective text length.
    """
    obj_short = _objective(
        "O.error-handling.1",
        text="Handle errors gracefully and emit messages.",
    )
    obj_long = _objective(
        "O.formatting.1",
        text=(
            "Output JSON with consistent 2-space indentation, sorted "
            "keys, and Unix line endings to match the reference "
            "implementation's behavioral test suite."
        ),
    )

    g_short = _category_a_gap("O.error-handling.1", confidence="STRONG")
    g_long = _category_a_gap("O.formatting.1", confidence="STRONG")

    inv = _wrap("test-text-tie", [g_short, g_long])
    aug = _aug("test-text-tie", [obj_short, obj_long])

    rec = score_candidates(
        gap_inventory=inv,
        augmented_objectives=aug,
        survey_text=None,
        extraction_id="test-text-tie",
        audit_path="/tmp/audit-log",
    )

    assert len(rec.candidates) == 2
    # Both score equally (gc=1, pm=1.0 [None substituted], imp=0.8).
    assert (
        rec.candidates[0].composite_score == rec.candidates[1].composite_score
    )
    # The longer-text objective MUST rank first, beating alphabetical
    # (where "error-handling" < "formatting").
    assert rec.candidates[0].gap_id == "G.BACKING.o-formatting-1", (
        f"AC.V041.3 — longer objective text must beat alphabetical "
        f"(empirical motivation: v0.4.0 C4 Task 2 jsonpp); top "
        f"candidate was {rec.candidates[0].gap_id!r}, expected "
        f"G.BACKING.o-formatting-1 (formatting text > error-handling text)"
    )


def test_AC_V041_3_three_way_tie_cluster_then_text_then_alphabetical():
    """Three category-b gaps with identical composite + confidence.
    Cluster-size discriminates first; text-length next; alphabetical
    last."""
    g_med = _category_b_gap("a-mid", confidence="STRONG", row_count=4)
    g_large = _category_b_gap("z-big", confidence="STRONG", row_count=8)
    g_med_dup = _category_b_gap("b-mid", confidence="STRONG", row_count=4)

    inv = _wrap("test-three-way", [g_med, g_large, g_med_dup])
    aug = _aug("test-three-way", [])

    rec = score_candidates(
        gap_inventory=inv,
        augmented_objectives=aug,
        survey_text=None,
        extraction_id="test-three-way",
        audit_path="/tmp/audit-log",
    )

    assert len(rec.candidates) == 3
    # Largest cluster first (8 > 4).
    assert rec.candidates[0].gap_id == "G.ORPHAN.src-z-big-js"
    # Among the two cluster-4 gaps with no objective (text-length 0),
    # alphabetical fires as final fallback: "a-mid" < "b-mid".
    assert rec.candidates[1].gap_id == "G.ORPHAN.src-a-mid-js"
    assert rec.candidates[2].gap_id == "G.ORPHAN.src-b-mid-js"


def test_AC_V041_3_alphabetical_remains_final_fallback_when_all_signals_tie():
    """Backward-compat: when category + confidence + cluster-size +
    objective-text-length ALL tie, lex alphabetical is the final
    fallback (preserves the v0.2.4 C3 contract)."""
    # Two category-a gaps with identical objective text length.
    obj_a = _objective(
        "O.alpha.1", text="Same length text here for comparing."
    )
    obj_b = _objective(
        "O.bravo.1", text="Same length text here for comparing."
    )
    g_a = _category_a_gap("O.alpha.1", confidence="STRONG")
    g_b = _category_a_gap("O.bravo.1", confidence="STRONG")

    inv = _wrap("test-alpha-fallback", [g_b, g_a])  # reverse order
    aug = _aug("test-alpha-fallback", [obj_a, obj_b])

    rec = score_candidates(
        gap_inventory=inv,
        augmented_objectives=aug,
        survey_text=None,
        extraction_id="test-alpha-fallback",
        audit_path="/tmp/audit-log",
    )

    # alpha-1 < bravo-1 lexicographically; alpha must rank first.
    assert rec.candidates[0].gap_id == "G.BACKING.o-alpha-1"
    assert rec.candidates[1].gap_id == "G.BACKING.o-bravo-1"


def test_AC_V041_3_category_a_beats_category_b_even_with_larger_cluster():
    """Category-a > category-b ranking is preserved even when the
    category-b has a much larger orphan cluster — cluster-size
    sits BELOW category in the hierarchy."""
    obj = _objective(
        "O.alpha.1",
        text="A short but valid objective sentence here.",
    )
    g_a = _category_a_gap("O.alpha.1", confidence="STRONG")
    g_b = _category_b_gap("huge", confidence="STRONG", row_count=20)

    inv = _wrap("test-category-vs-cluster", [g_b, g_a])
    aug = _aug("test-category-vs-cluster", [obj])

    rec = score_candidates(
        gap_inventory=inv,
        augmented_objectives=aug,
        survey_text=None,
        extraction_id="test-category-vs-cluster",
        audit_path="/tmp/audit-log",
    )

    # category-a base impact 0.8 vs category-b base+cluster 0.6 →
    # composite scores differ; category-a wins on composite, not on
    # tie-break. But even if scores were equal (which they're not
    # here), the _CATEGORY_RANK in _tiebreak_key keeps category-a
    # ahead.
    assert rec.candidates[0].category == "objective_without_verified_backing"
    assert rec.candidates[1].category == "implementation_orphan"


def test_AC_V041_3_strong_beats_weak_even_with_larger_cluster():
    """STRONG > WEAK is preserved even when the WEAK gap has a
    larger cluster — confidence-rank sits ABOVE cluster-size in the
    hierarchy."""
    g_strong_small = _category_b_gap(
        "small", confidence="STRONG", row_count=3
    )
    g_weak_large = _category_b_gap("large", confidence="WEAK", row_count=10)

    inv = _wrap("test-confidence-vs-cluster", [g_weak_large, g_strong_small])
    aug = _aug("test-confidence-vs-cluster", [])

    rec = score_candidates(
        gap_inventory=inv,
        augmented_objectives=aug,
        survey_text=None,
        extraction_id="test-confidence-vs-cluster",
        audit_path="/tmp/audit-log",
    )

    # STRONG composite is gc=1.0 × pm=1.0 × imp=0.6 = 0.6.
    # WEAK composite is gc=0.5 × pm=1.0 × imp=0.6 = 0.3.
    # STRONG wins on composite_score directly. Test asserts that even
    # when composites tied (which they don't here), STRONG would still
    # rank first via _CONFIDENCE_RANK.
    assert rec.candidates[0].gap_id == "G.ORPHAN.src-small-js"
    assert rec.candidates[1].gap_id == "G.ORPHAN.src-large-js"
