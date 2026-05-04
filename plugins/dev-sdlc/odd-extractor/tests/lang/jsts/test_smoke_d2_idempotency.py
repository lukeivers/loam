"""Smoke D2 (idempotency variant).

Per plan-doc §6 D2:

- 5 extractions against the JsTs fixture produce byte-identical
  artefacts (modulo timestamps).
- Cycle-4a-specific: per-grammar idempotency — TS/JS/TSX file
  extracted twice produces byte-identical per-file results.
- Multi-grammar parser caches don't introduce non-determinism.
"""

from __future__ import annotations

from pathlib import Path

from loam_odd_extractor.lang.jsts import extract_jsts_acs


def test_extract_is_byte_identical_across_runs(
    jsts_playwright_app_repo: Path,
) -> None:
    """5 extractions produce identical AC dicts (modulo created_at)."""
    runs = [
        extract_jsts_acs(repo=jsts_playwright_app_repo)
        for _ in range(5)
    ]

    def _normalise(raw):
        return {
            "acs": raw.acs,
            "unhandled_paths": [str(p) for p in raw.unhandled_paths],
            "per_slice_costs": raw.per_slice_costs,
        }

    first = _normalise(runs[0])
    for r in runs[1:]:
        assert _normalise(r) == first, (
            "extraction is non-deterministic; D2 idempotency variant "
            "broken"
        )


def test_acs_sorted_lexicographically(
    jsts_playwright_app_repo: Path,
) -> None:
    """RawACs.acs is sorted by ac_id (per Surface #9 inheritance)."""
    raw = extract_jsts_acs(repo=jsts_playwright_app_repo)
    ac_ids = [ac.get("ac_id", "") for ac in raw.acs]
    assert ac_ids == sorted(ac_ids), (
        "AC list not sorted by ac_id; idempotency at risk"
    )


def test_per_slice_idempotency(
    jsts_playwright_app_repo: Path,
) -> None:
    """The same input slice produces the same output across two
    adapter invocations.
    """
    from loam_odd_extractor.lang.jsts.adapter import JsTsAdapter
    from loam_odd_extractor.spec import AnalysisPlan, Slice

    files = sorted(
        list(jsts_playwright_app_repo.rglob("*.js"))
        + list(jsts_playwright_app_repo.rglob("*.mjs"))
        + list(jsts_playwright_app_repo.rglob("*.cjs"))
        + list(jsts_playwright_app_repo.rglob("*.ts"))
        + list(jsts_playwright_app_repo.rglob("*.tsx"))
        + list(jsts_playwright_app_repo.rglob("*.html"))
    )
    plan = AnalysisPlan(
        extraction_id="t",
        slices=[
            Slice(
                slice_id="jsts-root",
                adapter_name="jsts",
                paths=files,
            )
        ],
        unhandled_paths=[],
        created_at="2026-05-04T00:00:00+00:00",
    )
    adapter = JsTsAdapter()
    raw1 = adapter.extract(jsts_playwright_app_repo, plan)
    raw2 = adapter.extract(jsts_playwright_app_repo, plan)
    assert raw1.acs == raw2.acs
    assert raw1.unhandled_paths == raw2.unhandled_paths


def test_multi_grammar_parser_cache_is_deterministic(
    jsts_playwright_app_repo: Path,
) -> None:
    """The per-grammar parser cache keeps separate parsers for JS,
    TS, and TSX. Two extractions hitting all three grammars must
    return byte-identical results.
    """
    raw1 = extract_jsts_acs(repo=jsts_playwright_app_repo)
    raw2 = extract_jsts_acs(repo=jsts_playwright_app_repo)
    assert raw1.acs == raw2.acs
