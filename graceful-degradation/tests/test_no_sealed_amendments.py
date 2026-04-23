"""Seal-enforcement retrofit for graceful-degradation.

The 2026-04-22 ODD audit surfaced that `graceful-degradation/tests/
SEAL_COMMIT` existed (holding `dab49dd`, the Amendment-3 landing SHA)
but no test consumed it — the "no sealed-component amendments"
constraint was advisory-only. This file closes that gap.

Pattern mirrors the cost-governance / reversibility-primitive /
self-correction retrofits introduced after commit `f94d602` pinned the
seal-test diff away from HEAD. The sidecar at tests/SEAL_COMMIT carries
the exact seal SHA; if absent or placeholder, _seal_commit() falls back
to HEAD so mid-build diffs still exercise the test.

BASELINE history:
  - dab49dd (Amendment-3 landing — the initial seal surface at retrofit).
  - Advanced to e8f704c when the delete-method-in-brief-dispatch-docs
    amendment (#18) opened. The amendment deletes graceful-
    degradation's historical `docs/rebuild/components/graceful-
    degradation/brief.md` dispatch doc (per ODD §2.5 + `scope-only-
    dispatch` / `research-before-plan` CDCs; briefs are dispatch-time
    artifacts, not committed canonical ones) and edits docs/odd-in-
    pos.md §7.4 accordingly. Multi-component amendment with six other
    brief-owning sealed components + hands-off-lifecycle. e8f704c is
    the pre-amendment tip (the `docs(future-ideas)` commit codifying
    the three new CDCs immediately before this amendment's code
    commit).

SEAL_COMMIT: populated at seal time per the existing amendment ritual.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
BASELINE = "e8f704c"

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
    assert "BASELINE = \"e8f704c\"" in source
    assert "SEAL_COMMIT_PATH" in source
    # Diff call must route through _seal_commit(), not hardcoded HEAD.
    assert "{BASELINE}..{seal}" in source, (
        "the diff call must route through _seal_commit()"
    )


def test_only_graceful_degradation_changed() -> None:
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
    # generated artifact alongside `graceful-degradation/`.
    # Amendment #18 (delete-method-in-brief-dispatch-docs) adds:
    #   - `docs/rebuild/components/graceful-degradation/` — the
    #     deleted brief.md lives under the component's doc dir.
    #   - `docs/rebuild/plans/` — plan-before-code paper trail.
    #   - `hands-off-lifecycle/` — cross-cutting seal counterpart
    #     (every amendment touches this).
    #   - `docs/odd-in-pos.md` — §7.4 rewrite (brief = dispatch-time,
    #     not committed canonical artifact).
    allowed_prefixes = (
        "graceful-degradation/",
        "data/",
        "docs/rebuild/components/graceful-degradation/",
        "docs/rebuild/plans/",
        "hands-off-lifecycle/",
    )
    allowed_files: set[str] = {"docs/odd-in-pos.md"}

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
