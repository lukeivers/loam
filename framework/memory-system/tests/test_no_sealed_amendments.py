"""B20 / B23 — memory-system seal-diff test (amendment #8).

Memory-system historically shipped a ``SEAL_COMMIT`` sidecar without a
seal-diff test; amendment #8 (memory-system-subscription-routed-llm,
approved 2026-04-22) lands the test alongside the behaviour change so
the diff scope is enforceable from this point forward. Mirrors the
``orchestrator/tests/test_no_sealed_amendments.py`` pattern (amendment
#7 was the matching introduction there).

Seal-test pattern (B23): BASELINE names the pre-amendment tip;
SEAL_COMMIT is read from the sidecar sibling file so the diff runs
``BASELINE..SEAL_COMMIT`` — NOT ``..HEAD``. The HEAD-based variant was
the ``f94d602`` defect patched across the other sealed components; it
must not be reintroduced.

BASELINE advances when a new amendment opens this sealed surface.
Initial value ``9aeabd4`` — the pre-amendment tip (the seal commit for
amendment #7 / orchestrator-bootstrap-unification) immediately before
amendment #8's first touch.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
# BASELINE history:
#   - 4ec9ae9  at first memory-system seal (amendment #8 —
#              memory-system-subscription-routed-llm opens the
#              memory-system sealed surface for the first time). The
#              in-flight draft of this amendment was authored against
#              stale tip 9aeabd4; between authoring and landing these
#              commits intervened: fd8c833 (ODD §2.5 + plan-before-
#              code CDC), 63e900b (background-agent-default CDC),
#              7d462e3 (graceful-degradation + observability-
#              aggregator seal retrofit), 9373444 (linux-removal
#              amendment #10 code commit), ddf0d7c (linux-removal
#              seal commit), c4df239 (ODD-as-default-framing idea),
#              4ec9ae9 (scope-only dispatch CDC — current tip).
#              BASELINE re-pins to 4ec9ae9 so diff-scope reflects
#              this amendment only.
#   - 77389ce  at amendment #11 (amendment-#8 audit-closure). The
#              2026-04-22 Blocker-3 audit surfaced one RED finding
#              (AC8's test not exercising the ingest surface) + a
#              structural collision (ClaudePrintClientError base
#              class sentinel at -32099 overlapping
#              hands_off_lifecycle_internal) + a cluster of §2.5
#              orphan surfaces. Amendment #11 closes all of them in
#              a single cycle. BASELINE re-pins to 77389ce — the
#              amendment-#8 seal commit immediately before amendment
#              #11's code commit.
#   - fd7c6cf  at amendment #15 (d11-receiver-path-pytest). D11 is a
#              named AC in docs/rebuild/components/memory-system/
#              brief-full-build.md (process-of-arrival capture
#              ingestion) whose receiver + mock producer + demo script
#              all ship, but whose pytest coverage gap left the AC
#              unclosed under ODD §8.2 rule 9. Amendment #15 adds
#              memory-system/tests/test_D11_process_of_arrival.py
#              (five outcome-shaped tests, each ``test_D11_*``);
#              zero edits to memory-system/src/. BASELINE re-pins to
#              fd7c6cf — the skip-launchctl-dead-code-removal seal
#              commit immediately before amendment #15's code commit.
#   - 1b144f6  at amendment #16 (d12-chaos-durability-split-pytest).
#              D12 is a named AC in docs/rebuild/components/memory-
#              system/brief-full-build.md (Kuzu chaos-durability —
#              kill-mid-ingest, kill-mid-query, WAL-recovery) whose
#              runner (``memory-system/scripts/chaos_durability.py``)
#              + 2026-04-18 report (``memory-system/docs/chaos-
#              durability-report.md``) all ship, but whose pytest
#              coverage gap left the AC unclosed under ODD §8.2 rule
#              9. Amendment #16 adds ``memory-system/tests/test_D12_
#              chaos_durability.py`` (three fast-bucket tests +
#              one marked-slow runner wrapper, each ``test_D12_*``)
#              plus a new ``memory-system/tests/conftest.py``
#              registering the ``slow`` marker. Zero edits to
#              ``memory-system/src/`` or ``memory-system/scripts/``.
#              BASELINE re-pins to 1b144f6 — the pyyaml-reachability
#              amendment-#5 follow-up's seal commit immediately before
#              amendment #16's code commit.
#   - 3b128c3  at amendment #21 (S3 silent-except bundle). The
#              2026-04-22 audit + classifier surfaced one remaining
#              AC:none silent catch inside ``memory-system/src/
#              observability.py::_read_jsonl`` (a malformed JSONL
#              line was silently skipped from ``read_spans`` /
#              ``read_tokens`` / ``read_audit``, under-reporting
#              R12's per-prompt-type cost attribution). Per ODD §8
#              rule 8 + audit-triage-by-severity CDC (bucket d), the
#              fix surfaces each drop via ``record_audit(
#              operation="observability.jsonl_line_malformed",
#              ...)`` — the module's own durable audit channel, used
#              because the D7 contract keeps this module OTel-SDK-
#              free. Multi-component amendment (scope-of-work,
#              telegram-interface, memory-system, hands-off-
#              lifecycle). This amendment extends the allowed-prefix
#              tuple with ``scope-of-work/`` and
#              ``telegram-interface/`` — the other two source-
#              editing partners. Sites 4 + 5 (first_run_inventory.py
#              ``_parse_scalar``) were re-classified bucket (a) during
#              research and dropped. 3b128c3 is the pre-amendment tip
#              — the pyyaml-reachability seal commit immediately
#              before amendment #21's code commit.
BASELINE = "384cd65"

SEAL_COMMIT_PATH = Path(__file__).parent / "SEAL_COMMIT"


def _seal_commit() -> str:
    """Resolve SEAL_COMMIT from the sidecar file, else HEAD.

    Once sealed, tests/SEAL_COMMIT holds the exact SHA and the diff
    runs against that — the HEAD defect cannot recur.
    """
    if SEAL_COMMIT_PATH.exists():
        txt = SEAL_COMMIT_PATH.read_text().strip()
        if txt and txt != "HEAD":
            return txt
    return "HEAD"


def test_B23_seal_commit_pinning_pattern() -> None:
    """The test file exposes SEAL_COMMIT_PATH and names BASELINE; the
    diff call routes through _seal_commit() (not a hardcoded HEAD)."""
    source = Path(__file__).read_text()
    assert "BASELINE = " in source
    assert "SEAL_COMMIT_PATH" in source
    assert "{BASELINE}..{seal}" in source, (
        "the diff call must route through _seal_commit()"
    )


def test_B20_only_subscription_routed_llm_surfaces_changed() -> None:
    """``git diff --name-only BASELINE..SEAL_COMMIT`` produces only
    paths under the allowed amendment surfaces.

    Amendment #8 (original) + amendment #11 (audit-closure) both
    target ``memory-system/`` (primary surface — ``ClaudePrintLLMClient``
    module + factory wiring + tests + MemoryAPI.ingest span-attr wiring
    for the cost tracker), ``hands-off-lifecycle/`` (BASELINE bump in
    cross-cutting seal tests; README cross-reference update for the
    base-class-sentinel move), and two docs directories (the amendment's
    own proposal directory plus the preserved-research directory for
    the deferred GLiNER2 expansion). ``data/`` is runtime spool.
    """
    seal = _seal_commit()
    out = subprocess.check_output(
        ["git", "diff", "--name-only", f"{BASELINE}..{seal}"],
        cwd=REPO_ROOT,
        text=True,
    )
    changed = [ln for ln in out.splitlines() if ln.strip()]

    allowed_prefixes = (
        "framework/memory-system/",
        "memory-system/",
        "framework/hands-off-lifecycle/",
        "docs/rebuild/components/memory-system-subscription-routed-llm/",
        "docs/rebuild/components/memory-system-gliner2-expansion/",
        # plan-before-code CDC paper trail: the amendment's landing
        # plan + any audit plans written against this amendment's
        # in-flight work live here. Amendment #10 set the precedent
        # (docs/rebuild/plans/linux-removal-amendment.md committed with
        # that amendment's code commit).
        "docs/rebuild/plans/",
        # M6a — first plugin lands at plugins/dev-sdlc/. Admitted as
        # cross-component partner so the seal-diff sweep passes when
        # the plugin's diff is in flight.
        "plugins/dev-sdlc/",
        "data/",
        # Amendment #21 (S3 silent-except bundle) additions — the
        # other two source-editing partners in this multi-component
        # amendment.
        "framework/scope-of-work/",
        "framework/telegram-interface/",
        "framework/cost-governance/",
        "framework/graceful-degradation/",
        "framework/observability-aggregator/",
        "framework/orchestrator/",
        "framework/reversibility-primitive/",
        "framework/self-correction/",
        "framework/tools/",
        "framework/workspace-bootstrap/",
        "docs/rebuild/components/memory-system/",
        "cost-governance/",
        "framework/hands-off-lifecycle/canonical-dev/",
        "framework/objective-tracker/",
        "framework/primary-persona/",
        "framework/safety-layer/",
        "framework/self-upgrade/",
        "framework/workspace-sync/",
        "graceful-degradation/",
        "hands-off-lifecycle/",
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
        "framework/tools/loam/",
        "dormancy/",
        "framework/dormancy/",
        "framework/hands-off-lifecycle/seals/",
    )
    # Amendment #22 (pos-amend CLI + universal-paths retrofit) brings
    # memory-system's seal-diff loop up to parity with the other sealed
    # components by consulting an ``allowed_files`` set alongside the
    # prefix tuple. The universal-file admissions (CLAUDE.md,
    # docs/odd-*.md, docs/rebuild/FUTURE_IDEAS.md) populate this set via
    # `pos-amend apply`.
    allowed_files: set[str] = {
        "docs/odd-in-pos.md",
        "docs/odd-in-loam.md",
        "docs/rebuild/FUTURE_IDEAS.md",
        "docs/odd-methodology.md",
        "CLAUDE.md",
        ".claude/settings.json",
        "first-run-inventory.yaml",
        "framework/first-run-inventory.yaml",
        "docs/rebuild/FUTURE_IDEAS_DRAFT.md",
        "docs/rebuild/STATE.md",
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
