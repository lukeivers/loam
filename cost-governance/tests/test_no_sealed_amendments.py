"""C23: git diff against the pre-amendment baseline shows only
cost-governance/ changes (plus the allowed plan-doc path). Zero
deltas to any sealed component.

Structural remedy 2026-04-20: originally pinned to cost-governance's
own seal commit as an inline constant (fixed on commit `f94d602`
after the HEAD-based scope broke when self-correction landed).
Retrofitted 2026-04-21 to the sidecar-file pattern self-correction
and workspace-bootstrap use — cleaner ritual, no post-seal test
amendment required. SEAL_COMMIT_PATH reads from tests/SEAL_COMMIT;
falls back to HEAD when absent/placeholder so builds on an
unfinished seal still exercise the test. Post-seal, tests/SEAL_COMMIT
carries the exact SHA and the diff is deterministic.

BASELINE history:
  - f657f8c (reversibility-primitive seal — the original anchor).
  - Advanced to 5c49e27 when amendment #13 (cost-governance-C14-
    timing-test re-extension) opened. The previous anchor was
    acceptable while cost-governance had never been amended since
    its original seal (so the `f657f8c..04951b6` diff naturally
    narrowed to `cost-governance/` only). Amendment #13 bumps the
    sidecar SEAL_COMMIT to the new amendment commit; if BASELINE
    remained at f657f8c the diff window would widen to include every
    unrelated sealed-component amendment between 04951b6 and the
    new SHA. Advancing BASELINE to 5c49e27 (the orchestrator-
    bootstrap-unification-AC1-removal seal — the pre-amendment-#13
    tip) narrows the diff window to just this amendment's touches.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
BASELINE = "5c49e27"

SEAL_COMMIT_PATH = Path(__file__).parent / "SEAL_COMMIT"


def _seal_commit() -> str:
    """Resolve SEAL_COMMIT from sidecar file, else HEAD."""
    if SEAL_COMMIT_PATH.exists():
        txt = SEAL_COMMIT_PATH.read_text().strip()
        if txt and txt != "HEAD":
            return txt
    return "HEAD"


def test_C23_only_cost_governance_changed() -> None:
    seal = _seal_commit()
    out = subprocess.check_output(
        ["git", "diff", "--name-only", f"{BASELINE}..{seal}"],
        cwd=REPO_ROOT,
        text=True,
    )
    changed = [ln for ln in out.splitlines() if ln.strip()]

    # `data/` is runtime test-output (observability spans.jsonl etc.),
    # not source. It is not a sealed-component amendment — treat as
    # generated artifact alongside `cost-governance/`.
    # `docs/rebuild/plans/` admits the plan-before-code paper trail
    # introduced by the plan-before-code CDC (first codified at fd8c833;
    # amendment #10 set the precedent of committing plan files with
    # the amendment's code commit — same pattern as memory-system's
    # and orchestrator's seal tests).
    # `hands-off-lifecycle/` admits the cross-cutting seal counterpart
    # every amendment touches (BASELINE bump + allowed-set extension
    # + SEAL_COMMIT sidecar refresh + amendment-cycle narrative).
    # Amendment #13 is the first cost-governance amendment to include
    # the cross-cutting seal counterpart in the diff window — earlier
    # cost-governance state never included any post-first-seal edits.
    allowed_prefixes = (
        "cost-governance/",
        "data/",
        "docs/rebuild/plans/",
        "hands-off-lifecycle/",
    )
    allowed_files: set[str] = set()  # no workspace-wide touches needed

    offending = []
    for path in changed:
        if any(path.startswith(p) for p in allowed_prefixes):
            continue
        if path in allowed_files:
            continue
        offending.append(path)
    assert offending == [], (
        f"Sealed-component paths modified: {offending}. Halt-signal condition."
    )
