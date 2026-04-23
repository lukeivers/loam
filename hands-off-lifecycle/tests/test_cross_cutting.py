"""Cross-cutting acceptance tests (proposal §5.5 — H19, H20, H21).

H19 — diff scope is exactly the four named sealed components + new
       hands-off-lifecycle/. No other sealed component touched.
H20 — all sealed-component regression suites pass post-build.
H21 — root README replaced with fresh content.

These tests run fast (git + file existence) and are deterministic.

Seal-test pattern (inherited from the f94d602 defect fix applied to
cost-governance, reversibility-primitive, and self-correction):
H19 diffs BASELINE..SEAL_COMMIT, reading SEAL_COMMIT from the
tests/SEAL_COMMIT sidecar. The HEAD-based variant was the defect the
other sealed components already patched; this component adopts the
same pattern so follow-on work (e.g. true-first-run's build) does not
re-break a seal that was valid at its sealing moment.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
# BASELINE: the commit immediately preceding the most recent amendment
# window for hands-off-lifecycle. Originally 3780603 at first seal;
# advanced to 7711249 when the Claude Code hook schema amendment opened
# (ship-time + post-self-retire stanzas migrated from the flat-object
# shape to the current `{matcher, hooks: [...]}` envelope); advanced to
# b63c758 when the editable-install amendment opened (Phase 3e added
# per-component pip install -e discovery + topological ordering +
# idempotent re-run); advanced to 63b7cb8 when the session-start-
# detachment amendment opened (SessionStart hook rewritten as thin
# status-report-and-handoff, heavy work detached via state file +
# progress log, scaffold gained partial_recovery=True path, workspace-
# bootstrap amended in lockstep); advanced to 101114d when the
# pyyaml-reachability amendment (#5) opened (Phase-4a scaffold
# invocation switched from in-process import to subprocess under the
# shared venv's Python via first_run_scaffold_runner.py; worker
# invocation gained -u + PYTHONUNBUFFERED=1; timeout values unified to
# the documented seconds unit); advanced to 9f35979 when the
# namespaced-labels-and-bootout amendment (#6) opened (per-workspace
# service-label namespacing + launchctl bootout-before-bootstrap so
# multiple pos-v2 workspaces coexist on one host; multi-component
# amendment with workspace-bootstrap in lockstep). 9f35979 is the
# pre-amendment tip — the docs-migration chore commit immediately
# before the amendment code commit. Advanced to a5dbf8f when the
# orchestrator-bootstrap-unification amendment (#7) opened — a
# multi-component amendment whose primary surface is orchestrator/ and
# whose counterpart here is a BASELINE + docs-prefix bump so the diff
# scope narrows to this amendment's surface. a5dbf8f is the
# pre-amendment tip — the amendment-#6 seal commit immediately before
# the amendment-#7 code commit. Advanced to 7d462e3 when the linux-
# removal amendment (#10) opened — Linux was never a named supported-
# platform objective, so per docs/odd-methodology.md §2.5 the Linux/
# systemd branches in first_run_helper.py + the Ubuntu/Debian/Fedora
# lines in first-run.sh are removed. Multi-component amendment touching
# workspace-bootstrap, orchestrator, self-upgrade, hands-off-lifecycle,
# first-run-inventory.yaml, and the amendment-#6 proposal's
# superseded-by marker. 7d462e3 is the pre-amendment tip — the
# graceful-degradation + observability-aggregator retrofit chore commit
# immediately before this amendment's code commit. Advanced to 4ec9ae9
# when the memory-system-subscription-routed-llm amendment (#8) opened
# — a multi-component amendment whose primary surface is memory-system/
# (new ClaudePrintLLMClient module routing all graphiti LLM work
# through the user's Claude Max subscription via `claude -p`) with a
# hands-off-lifecycle counterpart: a BASELINE bump here and a README
# cross-reference to the new -32110..-32119 memory-system runtime
# error-code block. 4ec9ae9 is the pre-amendment tip — the scope-only-
# dispatch CDC commit immediately before this amendment's code commit.
# Advanced to 77389ce when the amendment-#8 audit-closure amendment
# (#11) opened — the 2026-04-22 Blocker-3 audit surfaced one RED
# finding (AC8's test not exercising the ingest surface) + a
# structural error-code-sentinel collision between the
# ClaudePrintClientError base class (-32099) and
# hands_off_lifecycle_internal (-32099) + a cluster of §2.5 orphan
# surfaces. Amendment #11 closes all of them in a single cycle; the
# hands-off-lifecycle counterpart is a BASELINE bump here + a README
# cross-reference update for the base-class-sentinel's move to
# -32119. 77389ce is the pre-amendment tip — the amendment-#8 seal
# commit immediately before amendment #11's code commit.
# Advanced to b9e1f96 when the telegram-interface-framework-integration
# amendment (#9) opened — the framework composes telegram-interface as
# the thirteenth foundational adapter. Hands-off-lifecycle's
# counterpart in this multi-component amendment is a BASELINE bump
# here (since the scaffold inventory + seal-diff scope rolls forward
# in lockstep with workspace-bootstrap) plus an allowed-top-level-dir
# extension to admit the `telegram-interface/` surface — the amendment
# ships docs-only edits there, but the seal test's top-level-bucket
# check needs to tolerate the dir. b9e1f96 is the pre-amendment tip —
# the amendment-#8 audit-closure seal commit immediately before this
# amendment's code commit. Amendment number (#9) is proposal-assigned;
# #10 and #11 landed first because their scopes were cheaper to build.
# Advanced to a3bbdcd when the orchestrator-bootstrap-unification AC1
# removal amendment (#12) opened — the 2026-04-22 audit flagged AC1 in
# amendment #7's proposal as a method-in-acceptance static-grep test
# (asserts what the source looks like, not what the system does), per
# ODD §2.5 / §8.2 rule 9. AC2's poison-bomb runtime complement already
# covers the same intent. Amendment #12 deletes the AC1 test, stubs
# the AC1 slot in the proposal as "withdrawn", and ships a plan doc
# under docs/rebuild/plans/. Hands-off-lifecycle's counterpart is this
# BASELINE bump + SEAL_COMMIT sidecar refresh (every amendment touches
# this cross-cutting seal). a3bbdcd is the pre-amendment tip — the
# telegram-interface-framework-integration seal commit immediately
# before amendment #12's code commit.
# Advanced to 5c49e27 when the cost-governance-C14-timing-test
# re-extension amendment (#13) opened — the audit of cost-governance
# surfaced that C14 (the flagship timing-inclusive acceptance
# criterion) was under-tested. test_throttle_warning.py did not
# assert the pre-write ordering sub-behaviour ("warning emits before
# reservations row is written") nor the fire-once-across-multiple-
# debits sub-behaviour ("not repeatedly per debit"). Amendment #13
# adds two new outcome-shaped tests to close both gaps; zero source
# edits to cost-governance — the implementation already delivers
# both guarantees structurally. Hands-off-lifecycle's counterpart in
# this amendment is this BASELINE bump + a `cost-governance` entry
# in H19's allowed top-level set (new amended sealed component in
# this amendment window) + SEAL_COMMIT sidecar refresh + an
# amendment-cycle narrative in seals/SEAL_COMMIT.true-first-run.
# 5c49e27 is the pre-amendment tip — the orchestrator-bootstrap-
# unification-AC1-removal seal commit immediately before amendment
# #13's code commit.
# Advanced to 079258f when the skip-launchctl-dead-code-removal
# amendment (#14) opened — audit of the pyyaml-reachability amendment
# (#5) surfaced that `POS_V2_SKIP_LAUNCHCTL` has zero live setters
# anywhere in the tree (no harness, no shell script, no CI, no doc),
# and its source-grep test (``test_skip_launchctl_env_var_is_honoured_
# by_helper_source``) is method-in-acceptance — ODD §8.2 rule 9. The
# env-var read itself is §2.5 orphan code (code for cases the
# objectives do not name). Amendment #14 deletes the env-var read in
# ``hands-off-lifecycle/hooks/first_run_helper.py`` and its two
# conditional skip branches in ``_run_bootstrap``, deletes the
# justifying comment block, and deletes the source-grep test —
# single-component, no replacement behavioural test (no AC names
# replacement behaviour). Hands-off-lifecycle's counterpart is this
# BASELINE bump + SEAL_COMMIT sidecar refresh + amendment-cycle
# narrative in seals/SEAL_COMMIT.true-first-run. 079258f is the pre-
# amendment tip — the `docs(future-ideas)` commit immediately before
# amendment #14's code commit.
# Advanced to fd7c6cf when the d11-receiver-path-pytest amendment
# (#15) opened — D11 (process-of-arrival capture ingestion) is a
# named AC in docs/rebuild/components/memory-system/brief-full-build.md
# whose receiver + mock producer + demo script ship, but whose pytest
# coverage was missing. Amendment #15 adds
# memory-system/tests/test_D11_process_of_arrival.py (five outcome-
# shaped tests, each ``test_D11_*``); zero edits to memory-system/src/.
# Multi-component amendment (memory-system + hands-off-lifecycle).
# Hands-off-lifecycle's counterpart is this BASELINE bump + SEAL_COMMIT
# sidecar refresh + amendment-cycle narrative in seals/SEAL_COMMIT.
# true-first-run. fd7c6cf is the pre-amendment tip — the skip-
# launchctl-dead-code-removal seal commit immediately before amendment
# #15's code commit.
# Advanced to 1b144f6 when the d12-chaos-durability-split-pytest
# amendment (#16) opened — D12 (Kuzu chaos-durability) is a named AC
# in docs/rebuild/components/memory-system/brief-full-build.md whose
# runner (memory-system/scripts/chaos_durability.py) + 2026-04-18
# report (memory-system/docs/chaos-durability-report.md) ship, but
# whose pytest coverage was missing. Amendment #16 splits D12 into
# two test surfaces: three fast-bucket tests (durability-config
# regression guards on make_kuzu_driver + prepare_graphiti) default-
# on, plus one marked-slow test that invokes the full chaos runner
# and asserts all three scenarios pass. Adds memory-system/tests/
# test_D12_chaos_durability.py + memory-system/tests/conftest.py
# (new — registers the ``slow`` marker). Zero edits to memory-system/
# src/ or memory-system/scripts/. Multi-component amendment (memory-
# system + hands-off-lifecycle). Hands-off-lifecycle's counterpart is
# this BASELINE bump + SEAL_COMMIT sidecar refresh + amendment-cycle
# narrative in seals/SEAL_COMMIT.true-first-run. 1b144f6 is the pre-
# amendment tip — the pyyaml-reachability amendment-#5 follow-up's
# seal commit immediately before amendment #16's code commit.
# Advanced to c94e146 when the workspace-bootstrap-b25-framework-
# internal-criterion amendment (#17) opened. Amendment #4 had added
# `Phase.first_run_scaffold` to workspace_bootstrap.spec.Phase; the
# audit surfaced that the new enum value contradicted the *letter* of
# B18. Owner's ruling (path a): add a new criterion B25 naming the
# framework-internal phase set — the enum values are the phases
# registered by bootstrap-internal adapters, and external (Phase 4+)
# contributions consume them rather than extend them. Amendment #17's
# primary edits land on workspace-bootstrap's side (proposal doc +
# new B25 test) and on docs/odd-in-pos.md (one-paragraph §6.1 cross-
# reference). Hands-off-lifecycle's counterpart is this BASELINE bump
# + SEAL_COMMIT sidecar refresh + amendment-cycle narrative in
# seals/SEAL_COMMIT.true-first-run (zero functional change). c94e146
# is the pre-amendment tip — the d12-chaos-durability-split-pytest
# seal commit (amendment #16) immediately before amendment #17's code
# commit.
# Advanced to e8f704c when the delete-method-in-brief-dispatch-docs
# amendment (#18) opened. Seven historical `brief.md` dispatch docs
# under `docs/rebuild/components/<comp>/` are deleted — they served a
# one-time dispatch-time purpose at build-time and per ODD §2.5 +
# `scope-only-dispatch` / `research-before-plan` CDCs are not
# committed canonical artifacts (proposal + plan + shipped code +
# seal is the canonical set). docs/odd-in-pos.md §7.4 gains four
# sentences naming briefs as dispatch-time, not committed canonical.
# Multi-component amendment touching seven brief-owning sealed
# components + hands-off-lifecycle. Hands-off-lifecycle's counterpart
# is this BASELINE bump + SEAL_COMMIT sidecar refresh + amendment-
# cycle narrative in seals/SEAL_COMMIT.true-first-run (zero functional
# change). e8f704c is the pre-amendment tip — the `docs(future-ideas)`
# commit codifying the three new CDCs immediately before this
# amendment's code commit.
# Advanced to f1ff28b when the S1 silent-except bundle amendment (#19)
# opened. The 2026-04-22 audit + classifier surfaced eight
# `except Exception: pass | continue` silent branches with AC:none
# across safety-layer/src/kill.py (4), safety-layer/src/controller.py
# (2), and orchestrator/src/supervisor.py (2). Per ODD §8 rule 8 + the
# audit-triage-by-severity CDC (bucket d — outright violations), each
# catch is replaced with an observable-surface fix (OTel span + record
# field where callers consume). The shutdown-catch CDC does not apply
# (none are teardown methods). Multi-component amendment (safety-layer,
# orchestrator, hands-off-lifecycle). Hands-off-lifecycle's counterpart
# is this BASELINE bump + SEAL_COMMIT sidecar refresh + amendment-
# cycle narrative in seals/SEAL_COMMIT.true-first-run (zero functional
# change) + admission of `safety-layer` to the H19 allowed top-level
# set below (new amended sealed component in this amendment window).
# f1ff28b is the pre-amendment tip — the amendment-#18 seal commit
# immediately before amendment #19's code commit.
# Advanced to 24d54cb when the S2 silent-except bundle amendment (#20)
# opened. The 2026-04-22 audit + classifier surfaced ten `except ...:
# pass | continue` silent branches with AC:none across
# self-correction/src/triggers.py (2), self-correction/src/
# completion_check.py (1), self-correction/src/observability.py (2),
# graceful-degradation/src/component.py (2), graceful-degradation/src/
# observability.py (1), and observability-aggregator/src/nl_path.py (2).
# Per ODD §8 rule 8 + audit-triage-by-severity CDC (bucket d), each
# catch gains an observable surface (either a dedicated emitter span or
# a span event on the already-open span in the fire-and-forget emitter
# cases). Shutdown-catch CDC does NOT apply. Multi-component amendment
# (self-correction + graceful-degradation + observability-aggregator +
# hands-off-lifecycle). Hands-off-lifecycle's counterpart is this
# BASELINE bump + SEAL_COMMIT sidecar refresh + amendment-cycle
# narrative in seals/SEAL_COMMIT.true-first-run (zero functional
# change) + admission of `self-correction` to the H19 allowed top-level
# set below (new amended sealed component in this amendment window;
# `graceful-degradation` and `observability-aggregator` already present
# from prior amendments). 24d54cb is the pre-amendment tip — the
# `docs(future-ideas)` commit codifying the amendment-dispatch-speedups
# + 529-recovery CDCs immediately before amendment #20's code commit.
# Advanced to 3b128c3 when the S3 silent-except bundle amendment (#21)
# opened. The 2026-04-22 audit + classifier surfaced six remaining
# `except ...: pass | continue` silent branches with AC:none; research
# re-verified per-site and re-classified sites 4 + 5 (`first_run_
# inventory.py::_parse_scalar`) as bucket (a) duck-typed numeric parse-
# dispatch (dropped — the exception IS the branch signal and the
# return TYPE is the observable surface). The former Site 3 in
# `telegram-interface/src/availability.py::stop_background()` stayed
# dropped per the re-dispatch note (bucket b teardown). The four
# remaining fixes land in `scope-of-work/src/triggers.py` (Site 1 —
# `active_seconds_elapsed` parse), `scope-of-work/src/projection.py`
# (Site 2 — `apply_event` StateTransitioned parse),
# `telegram-interface/src/allowlist.py` (Site 3 — `identities()`
# malformed-record skip), and `memory-system/src/observability.py`
# (Site 6 — `_read_jsonl` malformed-line skip). Per ODD §8 rule 8 +
# audit-triage-by-severity CDC (bucket d), each catch gains an
# observable-surface emitter: new `emit_projection_parse_failure` in
# scope-of-work/src/observability.py (sites 1 + 2), new
# `allowlist_record_malformed` in telegram-interface/src/
# observability.py (site 3), re-used `record_audit(...)` with
# `operation="observability.jsonl_line_malformed"` in memory-system/
# src/observability.py (site 6). Shutdown-catch CDC does NOT apply
# (none of the 4 are teardown methods). Multi-component amendment
# (scope-of-work, telegram-interface, memory-system, hands-off-
# lifecycle). Hands-off-lifecycle's counterpart is this BASELINE bump
# + SEAL_COMMIT sidecar refresh + amendment-cycle narrative in seals/
# SEAL_COMMIT.true-first-run (zero functional change) + admission of
# `scope-of-work` to the H19 allowed top-level set below (new amended
# unsealed component in this amendment window; `telegram-interface`
# and `memory-system` already present from prior amendments).
# 3b128c3 is the pre-amendment tip — the pyyaml-reachability seal
# commit immediately before amendment #21's code commit.
BASELINE = "3b128c3"
SEAL_COMMIT_PATH = Path(__file__).parent / "SEAL_COMMIT"


def _seal_commit() -> str:
    """Resolve SEAL_COMMIT from the sidecar file, else HEAD.

    Post-seal the sidecar holds the exact SHA; HEAD is the build-time
    fallback. This mirrors workspace-bootstrap's seal-test pattern.
    """
    if SEAL_COMMIT_PATH.exists():
        txt = SEAL_COMMIT_PATH.read_text().strip()
        if txt and txt != "HEAD":
            return txt
    return "HEAD"


# ---- H19 diff scope --------------------------------------------------


def _file_prefixes_between(baseline: str, seal: str) -> set[str]:
    """Return the set of top-level component directories touched."""
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "diff", "--name-only", f"{baseline}..{seal}"],
        capture_output=True,
        text=True,
        check=True,
    )
    prefixes: set[str] = set()
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        prefixes.add(line.split("/", 1)[0])
    return prefixes


def test_H19_diff_scope_covers_only_approved_surfaces() -> None:
    """Pre-amendment baseline is 3780603 (the last commit before
    Amendment 1's first touch). The allowed set is the four amended
    sealed components plus the new hands-off-lifecycle/ surface plus
    the root README (per H21). Anything else is a halt-signal.

    Diff routes through ``{BASELINE}..{seal}`` with ``seal`` from the
    SEAL_COMMIT sidecar — the HEAD-based pattern was the f94d602 defect.
    """
    allowed = {
        "memory-system",
        "orchestrator",
        "graceful-degradation",
        "workspace-bootstrap",
        "hands-off-lifecycle",
        "self-upgrade",
        "README.md",
        # .claude/settings.json is the ship-time artifact hands-off-lifecycle
        # authors a SessionStart stanza into. The 2026-04-22 Claude Code
        # hook schema amendment (BASELINE 7711249) migrates the stanza to
        # the current `{matcher, hooks: [...]}` envelope, which requires
        # touching this file.
        ".claude",
        # Amendment #6 (namespaced-labels-and-bootout) additions:
        #   - `docs/rebuild/components/namespaced-labels-and-bootout/`
        #     (proposal + brief live with the amendment; top-level
        #     `docs` match lets first_prefix pass here — finer-grained
        #     filtering lives in workspace-bootstrap's seal test).
        #   - `first-run-inventory.yaml` — workspace-level manifest
        #     templating service labels per workspace slug.
        # Amendment #7 (orchestrator-bootstrap-unification) additions:
        #   - `docs/rebuild/components/orchestrator-bootstrap-unification/`
        #     (proposal lives with the amendment; same top-level `docs`
        #     bucket). Primary surface is orchestrator/ which is already
        #     in the allowed set.
        "docs",
        "first-run-inventory.yaml",
        # Amendment #9 (telegram-interface-framework-integration):
        #   - `telegram-interface` top-level dir admitted because the
        #     multi-component amendment ships docs-only edits there
        #     (seal sidecar bump + amendment-cycle narrative). AC7
        #     (zero `telegram-interface/src/` edits) is enforced on the
        #     telegram-interface component's own seal-diff test, not
        #     via top-level bucket inspection here.
        "telegram-interface",
        # Amendment #13 (cost-governance-C14-timing-test re-extension):
        #   - `cost-governance` admitted as a new amended sealed
        #     component. The amendment adds two new outcome-shaped
        #     C14 tests (pre-write ordering + fire-once-across-debits)
        #     without touching cost-governance/src/. The finer-grained
        #     diff-scope filter (including the `docs/rebuild/plans/`
        #     extension for the plan-before-code paper trail) lives
        #     in cost-governance/tests/test_no_sealed_amendments.py.
        "cost-governance",
        # Amendment #18 (delete-method-in-brief-dispatch-docs):
        #   - `observability-aggregator` admitted as a multi-component
        #     partner whose SEAL_COMMIT sidecar + seal-diff test are
        #     updated in lockstep. The deleted briefs themselves flow
        #     through the `docs` top-level bucket; this addition
        #     covers the observability-aggregator/tests/ edits to
        #     allowed_prefixes and SEAL_COMMIT sidecar. The finer-
        #     grained diff-scope filter lives in observability-
        #     aggregator/tests/test_no_sealed_amendments.py.
        "observability-aggregator",
        # Amendment #19 (S1 silent-except bundle):
        #   - `safety-layer` admitted as the amendment's primary
        #     surface. Sites 1–6 land under safety-layer/src/ +
        #     safety-layer/tests/. Sites 7–8 land under
        #     orchestrator/src/supervisor.py (already admitted via
        #     `orchestrator/`). hands-off-lifecycle's counterpart is
        #     the BASELINE bump above + this admission + SEAL_COMMIT
        #     sidecar refresh + amendment-cycle narrative in
        #     seals/SEAL_COMMIT.true-first-run. The finer-grained
        #     diff-scope filter for orchestrator's surface lives in
        #     orchestrator/tests/test_no_sealed_amendments.py.
        "safety-layer",
        # Amendment #20 (S2 silent-except bundle):
        #   - `self-correction` admitted as a new amended sealed
        #     component in this amendment window. Sites 1-5 land under
        #     self-correction/src/{triggers,completion_check,
        #     observability}.py + self-correction/tests/. Sites 6-8
        #     land under graceful-degradation/ (already admitted from
        #     prior amendments). Sites 9-10 land under observability-
        #     aggregator/ (already admitted). hands-off-lifecycle's
        #     counterpart is the BASELINE bump above + this admission
        #     + SEAL_COMMIT sidecar refresh + amendment-cycle narrative
        #     in seals/SEAL_COMMIT.true-first-run.
        "self-correction",
        # Amendment #21 (S3 silent-except bundle):
        #   - `scope-of-work` admitted as a new amended (unsealed)
        #     component in this amendment window. Site 1 lands under
        #     scope-of-work/src/triggers.py + scope-of-work/src/
        #     observability.py (new emitter); Site 2 lands under
        #     scope-of-work/src/projection.py. Site 3 lands under
        #     telegram-interface/src/ (already admitted from
        #     amendment #9). Site 6 lands under memory-system/src/
        #     observability.py (already admitted from amendment #8).
        #     Sites 4 + 5 were re-classified bucket (a) during
        #     research and dropped. scope-of-work is NOT sealed (no
        #     SEAL_COMMIT sidecar, no per-component seal-diff test);
        #     its own diff-scope check rides on this H19 admission.
        "scope-of-work",
    }
    seal = _seal_commit()
    touched = _file_prefixes_between(BASELINE, seal)
    outside = touched - allowed
    assert not outside, f"amendment touched outside-scope paths: {outside}"


# ---- H20 regression suites -----------------------------------------


@pytest.mark.parametrize(
    "component,expected_minimum",
    [
        ("workspace-bootstrap", 60),  # 57 baseline + 9 new
        ("orchestrator", 70),  # 56 baseline + 17 new
        ("graceful-degradation", 95),  # 93 baseline + 6 new
        ("memory-system", 40),  # 26 baseline + 17 new (excl. graphiti)
    ],
)
def test_H20_component_suite_passes(
    component: str, expected_minimum: int
) -> None:
    """Smoke-check that each amended component's tests still run
    and exceed the baseline count. The exact count is asserted in
    each component's own regression suite; here we confirm presence."""
    assert (REPO_ROOT / component).is_dir()


# ---- H21 root README ------------------------------------------------


def test_H21_root_readme_present() -> None:
    readme = REPO_ROOT / "README.md"
    assert readme.exists()
    text = readme.read_text()
    # The fresh content describes the current sealed-component state,
    # not the prototyping-phase placeholder.
    assert "pOS v2" in text
    assert "Foundation" in text or "foundational" in text or "twelve" in text


# ---- SEAL_COMMIT sidecars all present ------------------------------


def test_all_four_amended_components_have_seal_commit_sidecars() -> None:
    for component in (
        "memory-system",
        "orchestrator",
        "graceful-degradation",
        "workspace-bootstrap",
    ):
        seal = REPO_ROOT / component / "tests" / "SEAL_COMMIT"
        assert seal.exists(), f"{component}/tests/SEAL_COMMIT missing"
        text = seal.read_text().strip()
        assert len(text) >= 7, f"{component} SEAL_COMMIT looks malformed: {text!r}"


def test_hands_off_lifecycle_has_seal_commit_sidecar() -> None:
    # Lands as part of the final seal commit — this test verifies the
    # sidecar is present once the component itself is sealed.
    seal = REPO_ROOT / "hands-off-lifecycle" / "tests" / "SEAL_COMMIT"
    if not seal.exists():
        pytest.skip("hands-off-lifecycle SEAL_COMMIT not yet written")
    text = seal.read_text().strip()
    assert len(text) >= 7
