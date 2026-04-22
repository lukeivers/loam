"""Seal-enforcement retrofit for observability-aggregator.

The 2026-04-22 ODD audit surfaced that observability-aggregator was the
only Phase-2+ sealed component with neither a SEAL_COMMIT sidecar nor a
seal-enforcement test — the sealing ritual at 2026-04-19 11:24 missed
both artifacts. This file (plus the new tests/SEAL_COMMIT sidecar)
closes that gap.

Pattern mirrors the cost-governance / reversibility-primitive /
self-correction retrofits. The sidecar at tests/SEAL_COMMIT carries the
exact seal SHA; if absent or placeholder, _seal_commit() falls back to
HEAD so mid-build diffs still exercise the test.

BASELINE: a0906c1 (observability-aggregator D9 docs — the final build
    commit, tipped immediately before the 11:24 seal per STATE.md).
SEAL_COMMIT: a0906c1 (same — retrofit diffs the seal against itself,
    producing an empty diff that trivially passes. Future amendments
    bump both BASELINE and SEAL_COMMIT to the new amendment's landing
    SHA per the existing amendment ritual).
"""

from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
BASELINE = "a0906c1"

SEAL_COMMIT_PATH = Path(__file__).parent / "SEAL_COMMIT"


def _seal_commit() -> str:
    """Resolve SEAL_COMMIT from sidecar file, else HEAD."""
    if SEAL_COMMIT_PATH.exists():
        txt = SEAL_COMMIT_PATH.read_text().strip()
        if txt and txt != "HEAD":
            return txt
    return "HEAD"


def test_seal_commit_pinning_pattern() -> None:
    """The test file exposes BASELINE + SEAL_COMMIT_PATH and does not
    diff against ..HEAD literally. Post-seal, tests/SEAL_COMMIT contains
    the SHA.
    """
    source = Path(__file__).read_text()
    assert "BASELINE = \"a0906c1\"" in source
    assert "SEAL_COMMIT_PATH" in source
    # Diff call must route through _seal_commit(), not hardcoded HEAD.
    assert "{BASELINE}..{seal}" in source, (
        "the diff call must route through _seal_commit()"
    )


def test_only_observability_aggregator_changed() -> None:
    """No sealed-component surface moved between BASELINE and seal."""
    seal = _seal_commit()
    out = subprocess.check_output(
        ["git", "diff", "--name-only", f"{BASELINE}..{seal}"],
        cwd=REPO_ROOT,
        text=True,
    )
    changed = [ln for ln in out.splitlines() if ln.strip()]

    # `data/` is runtime test-output (observability spans.jsonl etc.),
    # not source. It is not a sealed-component amendment — treat as
    # generated artifact alongside `observability-aggregator/`.
    allowed_prefixes = ("observability-aggregator/", "data/")
    allowed_files: set[str] = set()

    offending = []
    for path in changed:
        if any(path.startswith(p) for p in allowed_prefixes):
            continue
        if path in allowed_files:
            continue
        offending.append(path)
    assert offending == [], (
        f"Sealed-component paths modified: {offending}. "
        "Halt-signal condition."
    )
