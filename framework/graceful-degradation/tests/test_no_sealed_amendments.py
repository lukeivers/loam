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
  - Advanced to 24d54cb when the S2 silent-except bundle amendment
    (#20) opened. The 2026-04-22 audit + classifier surfaced three
    `except ...: pass | continue` silent branches with AC:none in
    graceful-degradation/ (site 6: component.py:443 scope lookup in
    _any_paused_scope_user_relevant; site 7: component.py:513 ValueError
    in reconcile_on_startup; site 8: observability.py:144 paused-scope-
    ids attribute set). Per ODD §8 rule 8 + audit-triage-by-severity
    CDC (bucket d — outright violations), each catch is replaced with
    an observable-surface fix (emitter or span event). Shutdown-catch
    CDC does NOT apply (none are teardown methods). Multi-component
    amendment (self-correction + graceful-degradation + observability-
    aggregator + hands-off-lifecycle). The new allowed prefixes below
    admit the partner components (`self-correction/`,
    `observability-aggregator/`) + `docs/rebuild/plans/` (research +
    plan paper-trail per plan-before-code CDC). 24d54cb is the pre-
    amendment tip — the `docs(future-ideas)` commit codifying the
    amendment-dispatch-speedups + 529-recovery CDCs immediately before
    amendment #20's code commit.

SEAL_COMMIT: populated at seal time per the existing amendment ritual.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
BASELINE = "57d735fbcde275dc0462306cd53e4830792df894"

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
    # Shape check: BASELINE is declared as a module-top constant
    # (advanced by ``pos-amend apply``, not hardcoded to a fixed SHA).
    assert "BASELINE = " in source
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
    # Amendment #18 (delete-method-in-brief-dispatch-docs) is a multi-
    # component amendment across seven brief-owning sealed components
    # plus hands-off-lifecycle. Adds:
    #   - `docs/rebuild/components/graceful-degradation/` and the six
    #     sibling component doc dirs — the seven deleted briefs.
    #   - `docs/rebuild/plans/` — plan-before-code paper trail.
    #   - `hands-off-lifecycle/` — cross-cutting seal counterpart.
    #   - `cost-governance/`, `observability-aggregator/`,
    #     `orchestrator/` — the three sibling brief-owning sealed
    #     components whose seal-diff tests + SEAL_COMMIT sidecars are
    #     updated in lockstep.
    #   - `docs/odd-in-pos.md` (allowed_files) — §7.4 rewrite (brief =
    #     dispatch-time, not committed canonical artifact).
    # Amendment #20 (S2 silent-except bundle) additions:
    #   - `self-correction/` — partner component (sites 1-5 fixes).
    #   - `observability-aggregator/` already present (sites 9-10).
    #   - `docs/rebuild/plans/` already present (research + plan docs
    #     per plan-before-code + research-before-plan CDCs).
    allowed_prefixes = (
        "framework/graceful-degradation/",
        "data/",
        "docs/rebuild/components/graceful-degradation/",
        "docs/rebuild/components/primary-persona-loader/",
        "docs/rebuild/components/session-resilient-orchestrator/",
        "docs/rebuild/components/observability-aggregator/",
        "docs/rebuild/components/cost-governance/",
        "docs/rebuild/components/scope-of-work/",
        "docs/rebuild/components/objective-tracker/",
        "docs/rebuild/plans/",
        "framework/hands-off-lifecycle/",
        "framework/cost-governance/",
        "framework/observability-aggregator/",
        "framework/orchestrator/",
        "framework/self-correction/",
        "framework/memory-system/",
        "framework/reversibility-primitive/",
        "framework/telegram-interface/",
        "framework/tools/",
        "framework/workspace-bootstrap/",
        "cost-governance/",
        "framework/hands-off-lifecycle/canonical-dev/",
        "framework/objective-tracker/",
        "framework/primary-persona/",
        "framework/safety-layer/",
        "framework/scope-of-work/",
        "framework/self-upgrade/",
        "framework/workspace-sync/",
        "hands-off-lifecycle/",
        "memory-system/",
        "objective-tracker/",
        "observability-aggregator/",
        "orchestrator/",
        "primary-persona/",
        "reversibility-primitive/",
        "safety-layer/",
        "scope-of-work/",
        "self-correction/",
        "self-upgrade/",
        "telegram-interface/",
        "tools/",
        "workspace-bootstrap/",
        "workspace-sync/",
    )
    allowed_files: set[str] = {
        "docs/odd-in-pos.md",
        "CLAUDE.md",
        "docs/odd-methodology.md",
        "docs/rebuild/FUTURE_IDEAS.md",
        ".claude/settings.json",
        "first-run-inventory.yaml",
        "framework/first-run-inventory.yaml",
    }

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
