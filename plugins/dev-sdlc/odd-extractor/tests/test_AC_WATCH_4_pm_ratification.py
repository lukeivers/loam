"""AC.WATCH.4 — PM ratification-queue mechanics.

Tests `enqueue_incremental_proposals`:

- One enqueue per domain-batch (NOT per-AC).
- Provenance string shape: `odd-extract:incremental:<id>:<domain>`.
- Idempotent duplicate-skip on re-enqueue against same PM queue.
- Question text format: header + one bullet per proposal.
- 25-AC truncation suffix.
- Empty proposal set → no enqueues.
"""

from __future__ import annotations

from pathlib import Path

from loam_odd_extractor.bands import ConfidenceBand
from loam_odd_extractor.diff_classifier import (
    EvidenceClassification,
    OrphanedAC,
    OutOfDateAC,
)
from loam_odd_extractor.incremental_ratify import (
    enqueue_incremental_proposals,
)
from loam_odd_extractor.proposals import generate_proposals

from _incremental_helpers import (  # type: ignore[import-not-found]
    StubPMRuntime,
    make_hypothesised_ac,
    make_plausible_ac,
    now_iso,
)


def _make_proposal_set(
    *,
    ids_by_domain: dict[str, list[str]],
    extraction_id: str = "test",
):
    out_of_date: list[OutOfDateAC] = []
    for domain, ids in ids_by_domain.items():
        for ac_id in ids:
            ac = make_plausible_ac(
                ac_id=ac_id,
                backing_files=[f"app/{domain}/x.rb"],
                citations=[f"app/{domain}/x.rb:1-10"],
            )
            out_of_date.append(
                OutOfDateAC(
                    ac=ac,
                    drift_kind="backing_file_changed",
                    affected_files=(f"app/{domain}/x.rb",),
                    from_sha=None,
                    to_sha="def4567890",
                )
            )
    classification = EvidenceClassification(
        out_of_date=tuple(out_of_date),
    )
    return generate_proposals(
        classification,
        extraction_id=extraction_id,
        prior_repo_sha=None,
        current_repo_sha="def4567890",
        generated_at=now_iso(),
    )


def test_one_enqueue_per_domain_batch(tmp_path: Path) -> None:
    pm = StubPMRuntime(tmp_path / "pm")
    pset = _make_proposal_set(
        ids_by_domain={
            "payment": ["AC.PAYMENT.1", "AC.PAYMENT.2"],
            "auth": ["AC.AUTH.1"],
        },
        extraction_id="test-id",
    )
    result = enqueue_incremental_proposals(
        proposal_set=pset,
        workspace_root=tmp_path,
        pm_runtime=pm,
        pm_handle="test-pm",
    )
    assert result.enqueued_count == 2
    assert set(result.enqueued_domains) == {"payment", "auth"}
    assert result.skipped_count == 0
    assert result.total_proposals == 3
    # Stub captured 2 calls (one per domain).
    assert len(pm.calls) == 2


def test_provenance_string_shape(tmp_path: Path) -> None:
    pm = StubPMRuntime(tmp_path / "pm")
    pset = _make_proposal_set(
        ids_by_domain={"payment": ["AC.PAYMENT.1"]},
        extraction_id="repo-abc12345",
    )
    enqueue_incremental_proposals(
        proposal_set=pset,
        workspace_root=tmp_path,
        pm_runtime=pm,
        pm_handle="test-pm",
    )
    _, prov = pm.calls[0]
    assert prov == "odd-extract:incremental:repo-abc12345:payment"


def test_idempotent_duplicate_skip(tmp_path: Path) -> None:
    """Re-running enqueue against the same PM queue → all domains
    are skipped."""
    pm = StubPMRuntime(tmp_path / "pm")
    pset = _make_proposal_set(
        ids_by_domain={
            "payment": ["AC.PAYMENT.1"],
            "auth": ["AC.AUTH.1"],
        },
        extraction_id="test-id",
    )
    # First run.
    r1 = enqueue_incremental_proposals(
        proposal_set=pset,
        workspace_root=tmp_path,
        pm_runtime=pm,
        pm_handle="test-pm",
    )
    assert r1.enqueued_count == 2
    # Second run: same proposal set → duplicate-skip.
    r2 = enqueue_incremental_proposals(
        proposal_set=pset,
        workspace_root=tmp_path,
        pm_runtime=pm,
        pm_handle="test-pm",
    )
    assert r2.enqueued_count == 0
    assert r2.skipped_count == 2
    assert set(r2.skipped_duplicates) == {"payment", "auth"}


def test_partial_duplicate_skip(tmp_path: Path) -> None:
    """One domain pre-existing in queue + one new → 1 enqueue + 1
    skip."""
    pm = StubPMRuntime(tmp_path / "pm")
    # Seed PM with a payment domain proposal.
    pset_seed = _make_proposal_set(
        ids_by_domain={"payment": ["AC.PAYMENT.1"]},
        extraction_id="test-id",
    )
    enqueue_incremental_proposals(
        proposal_set=pset_seed,
        workspace_root=tmp_path,
        pm_runtime=pm,
        pm_handle="test-pm",
    )
    # Now enqueue a set with both payment + auth.
    pset_full = _make_proposal_set(
        ids_by_domain={
            "payment": ["AC.PAYMENT.1"],
            "auth": ["AC.AUTH.1"],
        },
        extraction_id="test-id",
    )
    result = enqueue_incremental_proposals(
        proposal_set=pset_full,
        workspace_root=tmp_path,
        pm_runtime=pm,
        pm_handle="test-pm",
    )
    assert result.enqueued_count == 1
    assert result.skipped_count == 1
    assert result.enqueued_domains == ("auth",)
    assert result.skipped_duplicates == ("payment",)


def test_question_text_format(tmp_path: Path) -> None:
    """Question text has header + one bullet per proposal +
    decision-options trailer."""
    pm = StubPMRuntime(tmp_path / "pm")
    pset = _make_proposal_set(
        ids_by_domain={
            "payment": ["AC.PAYMENT.1", "AC.PAYMENT.2"],
        },
        extraction_id="test-id",
    )
    enqueue_incremental_proposals(
        proposal_set=pset,
        workspace_root=tmp_path,
        pm_runtime=pm,
        pm_handle="test-pm",
    )
    qtext, _ = pm.calls[0]
    assert "Domain 'payment'" in qtext
    assert "AC.PAYMENT.1" in qtext
    assert "AC.PAYMENT.2" in qtext
    assert "ratify-all" in qtext
    assert "PLAUSIBLE→VERIFIED" in qtext


def test_question_text_truncates_at_25_acs(tmp_path: Path) -> None:
    """30 ACs in one domain → first 25 enumerated + truncation
    suffix."""
    pm = StubPMRuntime(tmp_path / "pm")
    pset = _make_proposal_set(
        ids_by_domain={
            "payment": [f"AC.PAYMENT.{i}" for i in range(30)],
        },
        extraction_id="test-id",
    )
    enqueue_incremental_proposals(
        proposal_set=pset,
        workspace_root=tmp_path,
        pm_runtime=pm,
        pm_handle="test-pm",
    )
    qtext, _ = pm.calls[0]
    # AC IDs sorted lexicographically; first 25 visible.
    visible_ids = [
        f"AC.PAYMENT.{i}"
        for i in sorted([str(i) for i in range(30)])[:25]
    ]
    for vid in visible_ids:
        assert vid in qtext
    assert "(and " in qtext
    assert "more" in qtext


def test_empty_proposal_set_no_enqueue(tmp_path: Path) -> None:
    pm = StubPMRuntime(tmp_path / "pm")
    classification = EvidenceClassification()
    pset = generate_proposals(
        classification,
        extraction_id="test-id",
        prior_repo_sha=None,
        current_repo_sha="def4567890",
        generated_at=now_iso(),
    )
    result = enqueue_incremental_proposals(
        proposal_set=pset,
        workspace_root=tmp_path,
        pm_runtime=pm,
        pm_handle="test-pm",
    )
    assert result.enqueued_count == 0
    assert result.skipped_count == 0
    assert result.total_proposals == 0
    assert pm.calls == []


def test_orphan_proposal_in_question_text(tmp_path: Path) -> None:
    """Orphaned ACs render with `→ orphaned` suffix in question
    text."""
    pm = StubPMRuntime(tmp_path / "pm")
    orphan_ac = make_hypothesised_ac(
        ac_id="AC.LEGACY.1",
        backing_files=["app/legacy/old.rb"],
    )
    classification = EvidenceClassification(
        orphaned=(
            OrphanedAC(
                ac=orphan_ac,
                missing_files=("app/legacy/old.rb",),
            ),
        ),
    )
    pset = generate_proposals(
        classification,
        extraction_id="test-id",
        prior_repo_sha=None,
        current_repo_sha="def4567890",
        generated_at=now_iso(),
    )
    enqueue_incremental_proposals(
        proposal_set=pset,
        workspace_root=tmp_path,
        pm_runtime=pm,
        pm_handle="test-pm",
    )
    assert len(pm.calls) == 1
    qtext, prov = pm.calls[0]
    assert "→ orphaned" in qtext
    assert "AC.LEGACY.1" in qtext
    assert "file deleted" in qtext
    assert prov == "odd-extract:incremental:test-id:legacy"
