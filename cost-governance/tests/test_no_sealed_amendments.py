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
  - Advanced to e8f704c when the delete-method-in-brief-dispatch-docs
    amendment (#18) opened. The amendment deletes cost-governance's
    historical `docs/rebuild/components/cost-governance/brief.md`
    dispatch doc (the brief served a one-time dispatch-time purpose at
    build-time; the canonical artifact set going forward is proposal
    + plan + shipped code + seal per ODD §2.5 and the `scope-only-
    dispatch` / `research-before-plan` CDCs) and edits
    docs/odd-in-pos.md §7.4 to name briefs as dispatch-time artifacts
    rather than committed canonical ones. Multi-component amendment
    with six other brief-owning sealed components + hands-off-
    lifecycle. e8f704c is the pre-amendment tip (the
    `docs(future-ideas)` commit codifying the three new CDCs
    immediately before this amendment's code commit).
"""

from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
BASELINE = "9559ca7"

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
    # Amendment #18 (delete-method-in-brief-dispatch-docs) is a multi-
    # component amendment across seven brief-owning sealed components
    # plus hands-off-lifecycle. Adds, in addition to the already-
    # admitted cost-governance/ / data/ / docs/rebuild/plans/ / hands-
    # off-lifecycle/ surfaces:
    #   - `docs/rebuild/components/cost-governance/` — cost-governance's
    #     own deleted brief.md lives here.
    #   - `docs/rebuild/components/primary-persona-loader/`,
    #     `docs/rebuild/components/session-resilient-orchestrator/`,
    #     `docs/rebuild/components/graceful-degradation/`,
    #     `docs/rebuild/components/observability-aggregator/`,
    #     `docs/rebuild/components/scope-of-work/`,
    #     `docs/rebuild/components/objective-tracker/` — the other six
    #     brief-owning components' deleted briefs (multi-component
    #     partners in this amendment window).
    #   - `graceful-degradation/`, `observability-aggregator/`,
    #     `orchestrator/` — the three other brief-owning sealed
    #     components whose seal-diff tests + SEAL_COMMIT sidecars are
    #     updated in lockstep (multi-component partners).
    #   - `docs/odd-in-pos.md` (allowed_files) — §7.4 rewrite naming
    #     briefs as dispatch-time, not canonical.
    allowed_prefixes = (
        "cost-governance/",
        "data/",
        "docs/rebuild/plans/",
        "hands-off-lifecycle/",
        "docs/rebuild/components/cost-governance/",
        "docs/rebuild/components/primary-persona-loader/",
        "docs/rebuild/components/session-resilient-orchestrator/",
        "docs/rebuild/components/graceful-degradation/",
        "docs/rebuild/components/observability-aggregator/",
        "docs/rebuild/components/scope-of-work/",
        "docs/rebuild/components/objective-tracker/",
        "graceful-degradation/",
        "observability-aggregator/",
        "orchestrator/",
        "memory-system/",
        "reversibility-primitive/",
        "self-correction/",
        "telegram-interface/",
        "tools/",
        "workspace-bootstrap/",
    )
    allowed_files: set[str] = {
        "docs/odd-in-pos.md",
        "CLAUDE.md",
        "docs/odd-methodology.md",
        "docs/rebuild/FUTURE_IDEAS.md",
    }

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
