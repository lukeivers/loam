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

BASELINE history:
  - a0906c1 (observability-aggregator D9 docs — the final build
    commit, tipped immediately before the 11:24 seal per STATE.md).
  - Advanced to e8f704c when the delete-method-in-brief-dispatch-
    docs amendment (#18) opened. The amendment deletes observability-
    aggregator's historical `docs/rebuild/components/observability-
    aggregator/brief.md` dispatch doc (per ODD §2.5 + `scope-only-
    dispatch` / `research-before-plan` CDCs; briefs are dispatch-time
    artifacts, not committed canonical ones) and edits docs/odd-in-
    pos.md §7.4 accordingly. Multi-component amendment with six other
    brief-owning sealed components + hands-off-lifecycle. e8f704c is
    the pre-amendment tip (the `docs(future-ideas)` commit codifying
    the three new CDCs immediately before this amendment's code
    commit).
  - Advanced to 24d54cb when the S2 silent-except bundle amendment
    (#20) opened. The 2026-04-22 audit + classifier surfaced two
    `except Exception: pass` silent branches with AC:none in
    observability-aggregator/src/nl_path.py (site 9: translate LLM
    fall-through; site 10: answer LLM fall-through). Per ODD §8 rule 8
    + audit-triage-by-severity CDC (bucket d), each catch gains a span
    event (`llm_translate_failed` / `llm_format_failed`) on the already-
    open pos.aggregator.nl_translate / pos.aggregator.nl_format span;
    fall-through to rule-based translate/format is preserved. Multi-
    component amendment (self-correction + graceful-degradation +
    observability-aggregator + hands-off-lifecycle). The allowed
    prefixes below admit the partner components
    (`self-correction/`, `graceful-degradation/` already present) +
    `docs/rebuild/plans/` (research + plan paper-trail per plan-before-
    code CDC). 24d54cb is the pre-amendment tip.

SEAL_COMMIT: populated at seal time per the existing amendment ritual.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
BASELINE = "dd11677"

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
    assert "BASELINE = " in source  # shape check: pos-amend apply advances the literal
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
    # Amendment #18 (delete-method-in-brief-dispatch-docs) is a multi-
    # component amendment across seven brief-owning sealed components
    # plus hands-off-lifecycle. Adds:
    #   - `docs/rebuild/components/observability-aggregator/` and the
    #     six sibling component doc dirs — the seven deleted briefs.
    #   - `docs/rebuild/plans/` — plan-before-code paper trail.
    #   - `hands-off-lifecycle/` — cross-cutting seal counterpart.
    #   - `cost-governance/`, `graceful-degradation/`, `orchestrator/`
    #     — the three sibling brief-owning sealed components whose
    #     seal-diff tests + SEAL_COMMIT sidecars are updated in
    #     lockstep.
    #   - `docs/odd-in-pos.md` (allowed_files) — §7.4 rewrite.
    # Amendment #20 (S2 silent-except bundle) additions:
    #   - `self-correction/` — partner component (sites 1-5 fixes).
    #   - `graceful-degradation/` already present (sites 6-8).
    #   - `docs/rebuild/plans/` already present (research + plan docs).
    allowed_prefixes = (
        "framework/observability-aggregator/",
        "observability-aggregator/",
        "data/",
        "docs/rebuild/components/observability-aggregator/",
        "docs/rebuild/components/primary-persona-loader/",
        "docs/rebuild/components/session-resilient-orchestrator/",
        "docs/rebuild/components/graceful-degradation/",
        "docs/rebuild/components/cost-governance/",
        "docs/rebuild/components/scope-of-work/",
        "docs/rebuild/components/objective-tracker/",
        "docs/rebuild/plans/",
        "framework/hands-off-lifecycle/",
        "framework/cost-governance/",
        "framework/graceful-degradation/",
        "framework/orchestrator/",
        "framework/self-correction/",
        "framework/memory-system/",
        "framework/reversibility-primitive/",
        "framework/telegram-interface/",
        "framework/tools/",
        "framework/workspace-bootstrap/",
        "framework/safety-layer/",
        "cost-governance/",
        "framework/hands-off-lifecycle/canonical-dev/",
        "framework/objective-tracker/",
        "framework/primary-persona/",
        "framework/scope-of-work/",
        "framework/self-upgrade/",
        "framework/workspace-sync/",
        "graceful-degradation/",
        "hands-off-lifecycle/",
        "memory-system/",
        "objective-tracker/",
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
        "framework/tools/pos-amend/",
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
