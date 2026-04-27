"""D9 — Upgrade-fidelity test harness.

Tests that a framework upgrade preserves memory semantically.

Spec v1.1 R1 retired byte-identical equivalence for daily entries;
the replacement is semantic round-trip equivalence — the Luke-approved
probe set (Eve-in-lieu-of-Luke, 2026-04-18) runs pre-upgrade to
capture answers, re-runs post-upgrade, and a drift report compares
answers and fails the upgrade if drift exceeds a declared threshold.

A substrate-level snapshot of the Kuzu DB is taken pre-upgrade so
physical reversibility is preserved alongside the semantic test.

Harness shape:

  1. `snapshot(db_path, out_dir)` — freeze the current DB state by
     copying files to a timestamped directory.
  2. `run_probe_set(memory, probe_set)` — execute every probe query
     against the current memory, capturing answers as `ProbeResult`s.
  3. `compare(pre, post, thresholds)` — compute drift metrics, return
     `DriftReport` with per-query diffs and a pass/fail verdict.
  4. `run_upgrade_harness(memory_pre, memory_post, probe_set)` —
     orchestrates snapshot + pre-run + post-run + compare.

The harness is self-contained: it does not assume the upgrade
framework exists yet. When that framework lands, it wires in by
calling `snapshot()` pre-upgrade, the pOS upgrade commands, and then
`run_probe_set()` post-upgrade.
"""

from __future__ import annotations

import asyncio
import json
import shutil
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Awaitable, Callable

from .config import section


# ---- shapes ----------------------------------------------------------


@dataclass
class ProbeResult:
    query_id: str
    mode: str
    query: str
    passed: bool                       # pass/fail against declared labels
    recall: float                      # [0, 1]
    precision_at_5: float              # [0, 1]
    matched_expected: list[str]
    missed_expected: list[str]
    negative_hits: list[str]
    top_facts: list[str]               # top-5 fact strings (for diffing)
    result_count: int


@dataclass
class PerQueryDrift:
    query_id: str
    mode: str
    pre_pass: bool
    post_pass: bool
    verdict_flipped: bool
    recall_delta: float
    precision_delta: float
    top_fact_overlap: float            # Jaccard of top-5 fact sets


@dataclass
class DriftReport:
    pre_timestamp: str
    post_timestamp: str
    per_query: list[PerQueryDrift]
    verdict_flip_fraction: float
    mean_recall_delta: float
    mean_precision_delta: float
    over_tolerance_fraction: float     # how many per-query drifts exceed the per-query tolerance
    passed: bool
    thresholds: dict[str, float]
    notes: list[str] = field(default_factory=list)


# ---- probe set loader ------------------------------------------------


def load_probe_set(path: str | Path | None = None) -> dict[str, Any]:
    cfg = section("upgrade")
    p = Path(path or cfg.get("probe_set_path") or "./data/test_set.json")
    return json.loads(p.read_text())


# ---- scoring ---------------------------------------------------------


def score_one_probe(question: dict[str, Any], hits) -> ProbeResult:
    """Match the shape of scripts/eval_embeddings.py — intentional:
    the probe set scoring must agree with the evaluation scoring, or
    the upgrade harness and the spec acceptance test would measure
    different things.
    """
    facts = [(h.fact or "") for h in hits]
    facts_text = " ".join(f.lower() for f in facts)
    top5_facts = facts[:5]
    top5_text = " ".join(f.lower() for f in top5_facts)

    expected_all = (
        question.get("expected_facts")
        or question.get("expected_facts_all")
        or []
    )
    expected_any = question.get("expected_facts_any") or []
    negative = question.get("negative_facts") or []

    matched_all = [e for e in expected_all if e.lower() in facts_text]
    matched_any = [e for e in expected_any if e.lower() in facts_text]
    negative_hits = [n for n in negative if n.lower() in top5_text]

    if expected_all:
        recall = len(matched_all) / len(expected_all)
    elif expected_any:
        recall = 1.0 if matched_any else 0.0
    else:
        recall = 1.0

    top5_has_expected = any(
        e.lower() in top5_text for e in (expected_all + expected_any)
    )
    if top5_has_expected and not negative_hits:
        precision = 1.0
    elif top5_has_expected:
        precision = 0.5
    else:
        precision = 0.0

    passed = (recall >= 1.0) and not negative_hits

    return ProbeResult(
        query_id=question["id"],
        mode=question["mode"],
        query=question["question"],
        passed=passed,
        recall=recall,
        precision_at_5=precision,
        matched_expected=matched_all + matched_any,
        missed_expected=[e for e in expected_all if e.lower() not in facts_text],
        negative_hits=negative_hits,
        top_facts=top5_facts,
        result_count=len(hits),
    )


# ---- probe runner ----------------------------------------------------


async def run_probe_set(
    memory,  # MemoryAPI-shaped; duck-typed to ease testing
    *,
    probe_set: dict[str, Any] | None = None,
    scope_ids: list[str] | None = None,
) -> list[ProbeResult]:
    """Run every question in the probe set and score it."""
    probe_set = probe_set or load_probe_set()
    out: list[ProbeResult] = []
    for q in probe_set["questions"]:
        at_time: datetime | None = None
        if q.get("reference_time"):
            at_time = datetime.fromisoformat(q["reference_time"])

        anchor_uuid = None
        if q["mode"] == "context_aware" and q.get("anchor_entity"):
            # Best-effort anchor lookup: first hit of a semantic search.
            anchor_hits = await memory.search(
                q["anchor_entity"],
                num_results=3,
                scope_ids=scope_ids,
            )
            if anchor_hits:
                anchor_uuid = anchor_hits[0].source_node_uuid

        hits = await memory.search(
            q["question"],
            scope_ids=scope_ids,
            anchor_node_uuid=anchor_uuid,
            at_time=at_time,
            num_results=10,
        )
        out.append(score_one_probe(q, hits))
    return out


# ---- drift comparison ------------------------------------------------


def _jaccard(a: list[str], b: list[str]) -> float:
    sa = set(s.lower() for s in a)
    sb = set(s.lower() for s in b)
    if not sa and not sb:
        return 1.0
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def compare(
    pre: list[ProbeResult],
    post: list[ProbeResult],
    *,
    thresholds: dict[str, float] | None = None,
    notes: list[str] | None = None,
) -> DriftReport:
    cfg = section("upgrade")
    t_in = thresholds or {}
    # Explicit None-check (not truthy-check) so an override of 0.0 is honoured.
    max_drift = t_in.get("max_drift_fraction")
    if max_drift is None:
        max_drift = cfg.get("max_drift_fraction", 0.10)
    per_query_tol = t_in.get("per_query_recall_tolerance")
    if per_query_tol is None:
        per_query_tol = cfg.get("per_query_recall_tolerance", 0.15)
    th = {
        "max_drift_fraction": float(max_drift),
        "per_query_recall_tolerance": float(per_query_tol),
    }

    by_id = {p.query_id: p for p in post}
    per_query: list[PerQueryDrift] = []
    flipped = 0
    over_tolerance = 0
    recall_deltas: list[float] = []
    precision_deltas: list[float] = []

    for p in pre:
        q = by_id.get(p.query_id)
        if q is None:
            per_query.append(PerQueryDrift(
                query_id=p.query_id,
                mode=p.mode,
                pre_pass=p.passed,
                post_pass=False,
                verdict_flipped=True,
                recall_delta=-p.recall,
                precision_delta=-p.precision_at_5,
                top_fact_overlap=0.0,
            ))
            flipped += 1
            over_tolerance += 1
            continue

        r_delta = q.recall - p.recall
        p_delta = q.precision_at_5 - p.precision_at_5
        overlap = _jaccard(p.top_facts, q.top_facts)
        flipped_here = p.passed != q.passed

        if flipped_here:
            flipped += 1
        if abs(r_delta) > th["per_query_recall_tolerance"]:
            over_tolerance += 1

        recall_deltas.append(r_delta)
        precision_deltas.append(p_delta)
        per_query.append(PerQueryDrift(
            query_id=p.query_id,
            mode=p.mode,
            pre_pass=p.passed,
            post_pass=q.passed,
            verdict_flipped=flipped_here,
            recall_delta=round(r_delta, 3),
            precision_delta=round(p_delta, 3),
            top_fact_overlap=round(overlap, 3),
        ))

    n = max(len(pre), 1)
    verdict_flip_fraction = flipped / n
    over_tolerance_fraction = over_tolerance / n
    drift_score = max(verdict_flip_fraction, over_tolerance_fraction)
    passed = drift_score <= th["max_drift_fraction"]

    return DriftReport(
        pre_timestamp=datetime.now(timezone.utc).isoformat(),
        post_timestamp=datetime.now(timezone.utc).isoformat(),
        per_query=per_query,
        verdict_flip_fraction=round(verdict_flip_fraction, 3),
        mean_recall_delta=round(
            sum(recall_deltas) / len(recall_deltas) if recall_deltas else 0.0, 3
        ),
        mean_precision_delta=round(
            sum(precision_deltas) / len(precision_deltas) if precision_deltas else 0.0, 3
        ),
        over_tolerance_fraction=round(over_tolerance_fraction, 3),
        passed=passed,
        thresholds=th,
        notes=notes or [],
    )


# ---- substrate snapshot ---------------------------------------------


def snapshot(
    db_path: str | Path,
    *,
    out_dir: str | Path | None = None,
    tag: str | None = None,
) -> Path:
    """Copy the Kuzu DB file (and its WAL siblings) to a timestamped
    subdirectory. Used pre-upgrade to preserve physical reversibility.
    """
    cfg = section("upgrade")
    target = Path(out_dir or cfg.get("snapshot_dir") or "./data/snapshots")
    target.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    label = tag or "pre-upgrade"
    snap = target / f"{label}-{ts}"
    snap.mkdir(parents=True, exist_ok=True)

    db = Path(db_path)
    # Copy the main file, the WAL, and any lock / aux files Kuzu writes
    # under the same base name.
    for sibling in db.parent.glob(db.name + "*"):
        dest = snap / sibling.name
        if sibling.is_file():
            shutil.copy2(sibling, dest)
        elif sibling.is_dir():
            shutil.copytree(sibling, dest, dirs_exist_ok=True)
    return snap


def restore(snapshot_dir: str | Path, db_path: str | Path) -> None:
    """Restore a prior snapshot — copy files back into db_path's slot."""
    snap = Path(snapshot_dir)
    db = Path(db_path)
    # Wipe current state first.
    for sibling in db.parent.glob(db.name + "*"):
        if sibling.is_file():
            sibling.unlink()
        elif sibling.is_dir():
            shutil.rmtree(sibling, ignore_errors=True)
    # Copy snap contents back.
    for source in snap.iterdir():
        dest = db.parent / source.name
        if source.is_file():
            shutil.copy2(source, dest)
        elif source.is_dir():
            shutil.copytree(source, dest, dirs_exist_ok=True)


# ---- full orchestrator ----------------------------------------------


async def run_upgrade_harness(
    *,
    pre_factory: Callable[[], Awaitable[Any]],
    post_factory: Callable[[], Awaitable[Any]],
    probe_set: dict[str, Any] | None = None,
    db_path: str | Path | None = None,
    scope_ids: list[str] | None = None,
) -> tuple[DriftReport, Path | None]:
    """Run the full harness: snapshot, pre-probe, simulated upgrade
    (caller-provided `post_factory` builds a new memory instance
    post-upgrade), compare.

    `pre_factory` / `post_factory` return a MemoryAPI-shaped object.
    The harness never decides how the upgrade itself runs — that's the
    self-upgrade framework's job. It only verifies equivalence.
    """
    probe_set = probe_set or load_probe_set()
    snap_dir = snapshot(db_path) if db_path else None

    pre_memory = await pre_factory()
    pre_results = await run_probe_set(pre_memory, probe_set=probe_set, scope_ids=scope_ids)

    post_memory = await post_factory()
    post_results = await run_probe_set(post_memory, probe_set=probe_set, scope_ids=scope_ids)

    report = compare(pre_results, post_results)
    return report, snap_dir


# ---- serialisation ---------------------------------------------------


def drift_report_to_dict(report: DriftReport) -> dict[str, Any]:
    return asdict(report)
