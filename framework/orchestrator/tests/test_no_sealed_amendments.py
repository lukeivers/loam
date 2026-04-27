"""B20 / B23 — orchestrator seal-diff test (amendment #7).

Mirror of workspace-bootstrap/tests/test_no_sealed_amendments.py.
Orchestrator historically shipped a ``SEAL_COMMIT`` sidecar without a
seal-diff test; amendment #7 (orchestrator-bootstrap-unification,
approved 2026-04-22) lands the test alongside the behaviour change so
the diff scope is enforceable from this point forward.

Seal-test pattern (B23): BASELINE constant names the pre-amendment tip;
SEAL_COMMIT is read from the sidecar sibling file so the diff runs
``BASELINE..SEAL_COMMIT`` — NOT ``..HEAD``. The HEAD-based variant was
the f94d602 defect fixed across the other sealed components; it must
not be introduced here.

BASELINE advances when a new amendment opens this sealed surface.
Initial value ``a5dbf8f`` — the pre-amendment tip (the seal commit for
amendment #6 / namespaced-labels-and-bootout) immediately before
amendment #7's first touch.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
# BASELINE history:
#   - a5dbf8f  at first orchestrator seal (amendment #7 —
#              orchestrator-bootstrap-unification opens the orchestrator's
#              sealed surface for the first time; the pre-amendment tip
#              is the amendment-#6 seal commit immediately preceding this
#              amendment's code commit).
#   - 7d462e3  when the linux-removal amendment (#10) opened. Per
#              docs/odd-methodology.md §2.5, Linux was never a named
#              supported-platform objective; the orchestrator-side
#              edits remove `ops/systemd/`, the systemd cases from
#              `test_d2_launchd_systemd.py` (renamed `test_d2_launchd.py`),
#              the linux branches in `pos_session_start.py`, and the
#              `launchd/systemd` comment in `orchestrator.py`. 7d462e3
#              is the pre-amendment tip — the graceful-degradation +
#              observability-aggregator retrofit chore commit
#              immediately before this amendment's code commit.
#   - a3bbdcd  when the orchestrator-bootstrap-unification AC1 removal
#              amendment (#12) opened. The 2026-04-22 audit flagged
#              AC1 in amendment #7's proposal as a method-in-acceptance
#              static-grep (asserts what the source looks like, not
#              what the system does), per ODD §2.5 / §8.2 rule 9.
#              AC2's poison-bomb runtime complement already covers the
#              same intent. Amendment #12 deletes the AC1 test, stubs
#              the AC1 slot in the proposal as "withdrawn", and ships
#              a plan doc under docs/rebuild/plans/. a3bbdcd is the
#              pre-amendment tip — the telegram-interface-framework-
#              integration seal commit immediately before amendment
#              #12's code commit. BASELINE re-pins here because the
#              intervening amendments (#8 memory-system, #9 telegram-
#              interface, #11 audit-closure) did not touch
#              orchestrator/ but did land paths outside this component's
#              allowed_prefixes — re-pinning narrows the diff to
#              amendment #12's own surface.
#   - e8f704c  when the delete-method-in-brief-dispatch-docs amendment
#              (#18) opened. The amendment deletes orchestrator's
#              historical `docs/rebuild/components/session-resilient-
#              orchestrator/brief.md` (session-resilient-orchestrator
#              is this component's doc-slug name; the brief served a
#              one-time dispatch-time purpose at build-time, the
#              canonical artifact set going forward per ODD §2.5 +
#              `scope-only-dispatch` / `research-before-plan` CDCs is
#              proposal + plan + shipped code + seal) and edits
#              docs/odd-in-pos.md §7.4 to name briefs as dispatch-time
#              artifacts rather than committed canonical ones. Multi-
#              component amendment with six other brief-owning sealed
#              components + hands-off-lifecycle. e8f704c is the pre-
#              amendment tip — the `docs(future-ideas)` commit
#              codifying the three new CDCs immediately before this
#              amendment's code commit.
#   - f1ff28b  when the S1 silent-except bundle amendment (#19) opened.
#              The 2026-04-22 audit + classifier run surfaced eight
#              `except Exception: pass | continue` branches with no
#              AC backing across safety-layer/src/kill.py,
#              safety-layer/src/controller.py, and
#              orchestrator/src/supervisor.py. Per ODD §8 rule 8 and
#              the audit-triage-by-severity CDC (bucket d — outright
#              violations in live operational paths), the fix is
#              required. The shutdown-catch CDC does NOT apply (none
#              of the eight are teardown methods). The amendment
#              replaces each silent catch with an observable-surface
#              emitter (OTel span + structured record field where
#              callers consume it). Two sites carry backwards-
#              compatible additive record extensions:
#              KillEventRecord.failed_scope_ids and
#              EscalationRecord.notification_failures. Multi-component
#              amendment touching safety-layer/, orchestrator/
#              (supervisor.py only), hands-off-lifecycle/ (BASELINE +
#              SEAL_COMMIT + cross-cutting allowed-set bump). f1ff28b
#              is the pre-amendment tip — the amendment-#18 seal
#              commit immediately before amendment #19's code commit.
BASELINE = "57d735fbcde275dc0462306cd53e4830792df894"

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


def test_B20_only_orchestrator_unification_surfaces_changed() -> None:
    """``git diff --name-only BASELINE..SEAL_COMMIT`` produces only
    paths under the allowed amendment surfaces.

    Amendment #7 is a multi-component amendment covering
    ``orchestrator/`` (primary surface), ``workspace-bootstrap/`` (adapter
    + integration-test edits for the ``require_bootstrap`` field
    removal), ``hands-off-lifecycle/`` (seal baseline advance), and the
    amendment's own proposal directory. ``data/`` is runtime spool.
    """
    seal = _seal_commit()
    out = subprocess.check_output(
        ["git", "diff", "--name-only", f"{BASELINE}..{seal}"],
        cwd=REPO_ROOT,
        text=True,
    )
    changed = [ln for ln in out.splitlines() if ln.strip()]

    # Amendment #10 (linux-removal) additions:
    #   - `self-upgrade/` — dead `systemd_user_restart` + /proc branch
    #     removed.
    #   - `memory-system/` — orphan systemd template removed.
    #   - `docs/rebuild/components/namespaced-labels-and-bootout/` —
    #     superseded-by marker on AC3.
    #   - `docs/rebuild/plans/` — the amendment's own plan file.
    #   - `first-run-inventory.yaml` — comment text scrub.
    # Amendment #18 (delete-method-in-brief-dispatch-docs) is a multi-
    # component amendment across seven brief-owning sealed components
    # plus hands-off-lifecycle. Adds:
    #   - `docs/rebuild/components/session-resilient-orchestrator/` —
    #     orchestrator's deleted brief.md lives under its doc-slug
    #     dir (session-resilient-orchestrator is the doc-slug name,
    #     distinct from the orchestrator/ code tree).
    #   - Six sibling doc dirs for the other brief-owning components:
    #     primary-persona-loader/, graceful-degradation/, observability-
    #     aggregator/, cost-governance/, scope-of-work/, objective-
    #     tracker/.
    #   - `cost-governance/`, `graceful-degradation/`, `observability-
    #     aggregator/` — the three sibling brief-owning sealed
    #     components whose seal-diff tests + SEAL_COMMIT sidecars are
    #     updated in lockstep.
    #   - `docs/odd-in-pos.md` (allowed_files) — §7.4 rewrite (brief =
    #     dispatch-time, not committed canonical artifact).
    # Amendment #19 (S1 silent-except bundle):
    #   - `safety-layer/` — the amendment's primary surface (sites 1–6:
    #     kill.py, controller.py, observability.py, events.py, +
    #     three new test files). orchestrator/ is a multi-component
    #     partner (sites 7, 8: supervisor.py); safety-layer/ admission
    #     here lets orchestrator's seal-diff walk the whole-repo diff
    #     at its new BASELINE..SEAL window without flagging the
    #     amendment-partner component's paths.
    #   - `docs/rebuild/plans/research/` flows through the existing
    #     `docs/rebuild/plans/` prefix entry (startswith).
    allowed_prefixes = (
        "framework/orchestrator/",
        "orchestrator/",
        "framework/hands-off-lifecycle/",
        "framework/workspace-bootstrap/",
        "framework/self-upgrade/",
        "framework/memory-system/",
        "docs/rebuild/components/orchestrator-bootstrap-unification/",
        "docs/rebuild/components/namespaced-labels-and-bootout/",
        "docs/rebuild/components/session-resilient-orchestrator/",
        "docs/rebuild/components/primary-persona-loader/",
        "docs/rebuild/components/graceful-degradation/",
        "docs/rebuild/components/observability-aggregator/",
        "docs/rebuild/components/cost-governance/",
        "docs/rebuild/components/scope-of-work/",
        "docs/rebuild/components/objective-tracker/",
        "docs/rebuild/plans/",
        "data/",
        "framework/cost-governance/",
        "framework/graceful-degradation/",
        "framework/observability-aggregator/",
        "framework/safety-layer/",
        "framework/reversibility-primitive/",
        "framework/self-correction/",
        "framework/telegram-interface/",
        "framework/tools/",
        "framework/primary-persona/",
        "cost-governance/",
        "framework/hands-off-lifecycle/canonical-dev/",
        "framework/objective-tracker/",
        "framework/scope-of-work/",
        "framework/workspace-sync/",
        "graceful-degradation/",
        "hands-off-lifecycle/",
        "memory-system/",
        "objective-tracker/",
        "observability-aggregator/",
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
        "framework/first-run-inventory.yaml",
        "docs/odd-in-pos.md",
        "CLAUDE.md",
        "docs/odd-methodology.md",
        "docs/rebuild/FUTURE_IDEAS.md",
        ".claude/settings.json",
        "first-run-inventory.yaml",
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
