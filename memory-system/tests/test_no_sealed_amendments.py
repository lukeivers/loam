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


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
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
BASELINE = "77389ce"

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
        "memory-system/",
        "hands-off-lifecycle/",
        "docs/rebuild/components/memory-system-subscription-routed-llm/",
        "docs/rebuild/components/memory-system-gliner2-expansion/",
        # plan-before-code CDC paper trail: the amendment's landing
        # plan + any audit plans written against this amendment's
        # in-flight work live here. Amendment #10 set the precedent
        # (docs/rebuild/plans/linux-removal-amendment.md committed with
        # that amendment's code commit).
        "docs/rebuild/plans/",
        "data/",
    )

    offending = []
    for path in changed:
        if any(path.startswith(p) for p in allowed_prefixes):
            continue
        offending.append(path)
    assert offending == [], (
        f"Sealed-component paths modified: {offending}. "
        "Halt-signal condition."
    )
