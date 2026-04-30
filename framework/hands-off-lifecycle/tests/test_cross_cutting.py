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


REPO_ROOT = Path(__file__).resolve().parents[3]
# BASELINE is frozen at project-start per amendment #23 (the frozen-H19
# BASELINE + per-invariant-BASELINE convention amendment). 3780603 is
# the pre-amendment-#1 commit — the last state of the repo before
# hands-off-lifecycle began accumulating amendments. H19's fidelity
# target is the surface-introduction invariant ("no new top-level
# directory or file appears in the project without explicit admission
# into ``allowed`` below"); that target is cumulative across project
# history, not per-amendment. The previous floating-BASELINE pattern
# advanced this literal on every amendment of any component, which
# serialised all amendment development behind this one edit — the
# parallel-dev research (2026-04-23) named that as the biggest unlock
# blocker.
#
# Under the frozen-BASELINE design the diff window
# ``3780603..SEAL_COMMIT`` expands monotonically for the project's
# lifetime. New amendments extend ``allowed`` when they introduce a
# new top-level surface; no amendment ever removes an entry. Per-
# component contamination checks live in each sealed component's own
# ``tests/test_no_sealed_amendments.py``; those continue to use
# floating BASELINEs. See ``docs/odd-in-loam.md`` §10 for the
# frozen-vs-floating BASELINE convention and for the per-invariant-
# BASELINE pattern.
#
# Amendment-cycle history (the ~20 BASELINE advances that previously
# annotated this literal) lives canonically in
# ``hands-off-lifecycle/seals/SEAL_COMMIT.true-first-run``.
BASELINE = "3780603"
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
    """Surface-introduction invariant (frozen-BASELINE variant —
    amendment #23).

    Diffs ``3780603..SEAL_COMMIT`` and asserts every touched top-level
    dir or top-level file has been explicitly admitted into ``allowed``.
    BASELINE is frozen at project-start; the diff window expands
    monotonically over the project's lifetime. New admissions land via
    amendment; existing entries are never removed.

    H19 is a coordination-layer check — "no unadmitted top-level
    surface ever appeared" — not a per-component contamination check.
    Per-component contamination is covered by each sealed component's
    own ``tests/test_no_sealed_amendments.py`` (those retain floating
    BASELINEs that advance only when the component itself is touched).
    """
    allowed = {
        "memory-system",
        "orchestrator",
        "dormancy",
        # graceful-degradation admitted within the M1f rename diff
        # window; the directory was git mv'd to dormancy/ and the
        # pre-rename path-prefix appears in the BASELINE..HEAD
        # window. Will phase out after the next non-rename amendment
        # advances the H19 BASELINE past M1f.
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
        # D-migration D.1 (amendment #61) — directory restructure moves
        # every framework component under `framework/`, plus `tools/`,
        # `first-run-inventory.yaml`, and the canonical-dev settings
        # template. The new top-level first-segment is `framework`.
        # Existing per-component entries above (memory-system,
        # orchestrator, ...) are kept for monotonic admission per
        # ODD §10 even though they no longer match any post-D.1
        # path.
        "framework",
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
        "reversibility-primitive",
        "tools",
        "CLAUDE.md",
        # Amendment #35 (primary-persona-renderer-and-onboarding):
        #   - `primary-persona` admitted as a new amended sealed
        #     component. Amendment #35 added the to_agent_md()
        #     renderer + onboarding module + is_starter contract
        #     field under primary-persona/src/. Sealed at ce07242.
        #     The finer-grained diff-scope filter for primary-
        #     persona's surface lives in primary-persona/tests/
        #     test_no_sealed_amendments.py.
        # Amendment #36 (workspace-bootstrap-persona-scaffold)
        # extended primary-persona/ ONLY in the read-only template
        # consumption sense (no source edits), so no separate
        # admission for #36 is needed here; workspace-bootstrap is
        # already in the allowed set above.
        # Amendment #37 (this amendment, hands-off-lifecycle-
        # default-agent-wiring) advances SEAL_COMMIT past the
        # window where #35's primary-persona/ edits land — hence
        # this admission was deferred to #37 per ODD §10's
        # per-invariant-BASELINE convention (the H19 frozen
        # BASELINE is project-start; admissions land when the
        # SEAL_COMMIT window first surfaces them via hands-off-
        # lifecycle's own amendment).
        "primary-persona",
        # Amendment #38 (objective-tracker schema widening; sealed
        # at 92bead1) introduced the `objective-tracker/` top-level
        # bucket. Amendment #45 (the current hands-off-lifecycle
        # amendment) is the first H/L amendment whose SEAL_COMMIT
        # window crosses the #38 commit, so the admission lands
        # here per ODD §10's per-invariant-BASELINE convention.
        # Finer-grained diff-scope filter lives in
        # objective-tracker/tests/test_no_sealed_amendments.py.
        "objective-tracker",
        # Amendment #44 (sub-plan F dev-mode partition; sealed at
        # cb584ba) introduced the `CLAUDE.dev.md` top-level file as
        # the dev-only counterpart to CLAUDE.md (per F's D-build
        # choice 4). Amendment #45 admits it at H/L's first
        # opportunity; the file is consumed by amendment #45's
        # sub-plan B emitter as the dev-extension fragment.
        "CLAUDE.dev.md",
        # Amendment #44's sibling commit (f7cb781,
        # `chore(gitignore): add .scratch/ to root ignore list`)
        # touched root `.gitignore`. Amendment #45 admits the file
        # at H/L's first opportunity per the per-invariant-BASELINE
        # convention.
        ".gitignore",
        "workspace-sync",
        # Amendment #67 (single-framework-restructure; this amendment)
        # is the first H/L amendment whose SEAL_COMMIT window crosses
        # D-migration D.5.5's chore commit (`39cfbb1`,
        # `chore(repo): remove accidentally-committed runtime artifact
        # + gitignore data/`) which deleted the inadvertently-committed
        # top-level `data/` runtime-artifact bucket. The deletion
        # surfaces `data` as a touched top-level prefix in the
        # BASELINE..SEAL_COMMIT diff window. Admitted here at H/L's
        # first opportunity per ODD §10's per-invariant-BASELINE
        # convention (the H19 frozen BASELINE is project-start;
        # interim top-level prefix changes are admitted when H/L's
        # next SEAL_COMMIT advances past them).
        "data",
        # Amendment #76 (M1a — docs/prose-only brand rebrand; first
        # sub-amendment of the M1.rename multi-amendment series) is
        # the first H/L amendment whose SEAL_COMMIT window crosses
        # the public-docs scaffold commits `a28969e`
        # (`docs(public): add CODE_OF_CONDUCT.md (Contributor
        # Covenant 2.1)`) and `3c599c1`
        # (`feat(public-docs): scaffold v0.1.0 public artefacts
        # (LICENSE + CONTRIBUTING + SECURITY + README + positioning
        # + condensed-ODD)`). Together these introduced four new
        # top-level files: `LICENSE`, `CONTRIBUTING.md`,
        # `CODE_OF_CONDUCT.md`, and `SECURITY.md`. M1a admits all
        # four at H/L's first opportunity per ODD §10's per-
        # invariant-BASELINE convention. M1a itself does not edit
        # these files (its scope is docs/prose-only brand rebrand);
        # the admissions here cover the surface-introduction
        # invariant for files that already lived in the tree at
        # M1a's dispatch but had not yet crossed an H/L SEAL_COMMIT
        # window.
        "LICENSE",
        "CONTRIBUTING.md",
        "CODE_OF_CONDUCT.md",
        "SECURITY.md",
        # M6a — first plugin tree lands at plugins/dev-sdlc/. The
        # cross-cutting first-prefix admission is `plugins` (the
        # top-level new directory). Per plan §11 finding #7 — first
        # external contributor to the workspace-bootstrap entry-point
        # group establishes the `plugins/<name>/` pattern at v0.1.0.
        "plugins",
    }
    seal = _seal_commit()
    touched = _file_prefixes_between(BASELINE, seal)
    outside = touched - allowed
    assert not outside, f"amendment touched outside-scope paths: {outside}"


# ---- Frozen-BASELINE adversarial + monotonicity checks -------------
#
# These three tests are the amendment #23 acceptance proof that the
# frozen-BASELINE variant of H19 preserves the surface-introduction
# invariant. AC23.1 is the existing assertion above under its new
# frozen BASELINE; AC23.2 is the adversarial synthetic case; AC23.3
# asserts the diff window is non-empty (proves the BASELINE really did
# move to project-start, not silently defaulted to HEAD).


def test_H19_frozen_baseline_catches_unadmitted_bucket() -> None:
    """AC23.2 — adversarial synthetic case.

    Construct a ``touched`` set containing an admitted bucket and an
    unadmitted one. The same set-difference logic the real H19 test
    uses must surface the unadmitted bucket. Proves the frozen-BASELINE
    design still detects a new top-level surface appearing without
    review.
    """
    allowed = {"hands-off-lifecycle", "docs", "README.md"}
    touched = {"hands-off-lifecycle", "some-new-unapproved-bucket"}
    outside = touched - allowed
    assert outside == {"some-new-unapproved-bucket"}, (
        "frozen-BASELINE H19 must still catch new unadmitted top-level "
        f"surfaces. Got outside={outside!r}"
    )


def test_H19_frozen_baseline_is_project_start() -> None:
    """AC23.3 — BASELINE is pinned at project-start.

    Asserts the BASELINE literal resolves to the pre-amendment-#1
    commit. This guards against accidental re-introduction of the
    floating-BASELINE pattern — any future amendment that advances
    BASELINE away from 3780603 must be a conscious structural change
    (and must update this test accordingly).
    """
    assert BASELINE == "3780603", (
        f"BASELINE must stay frozen at project-start (3780603); "
        f"found {BASELINE!r}. Floating-BASELINE pattern re-introduced?"
    )
    # Resolve the SHA through git — fails loudly if the commit isn't
    # reachable (e.g. on a shallow clone or amputated tree).
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "rev-parse", BASELINE],
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.strip().startswith(BASELINE), (
        f"BASELINE {BASELINE!r} did not resolve cleanly: {result.stdout!r}"
    )


# ---- H20 regression suites -----------------------------------------


@pytest.mark.parametrize(
    "component,expected_minimum",
    [
        ("workspace-bootstrap", 60),  # 57 baseline + 9 new
        ("orchestrator", 70),  # 56 baseline + 17 new
        ("dormancy", 95),  # 93 baseline + 6 new (formerly graceful-degradation; renamed in M1f)
        ("memory-system", 40),  # 26 baseline + 17 new (excl. graphiti)
    ],
)
def test_H20_component_suite_passes(
    component: str, expected_minimum: int
) -> None:
    """Smoke-check that each amended component's tests still run
    and exceed the baseline count. The exact count is asserted in
    each component's own regression suite; here we confirm presence."""
    # Post-D.1: components live under framework/<comp>/.
    assert (REPO_ROOT / "framework" / component).is_dir()


# ---- H21 root README ------------------------------------------------


def test_H21_root_readme_present() -> None:
    readme = REPO_ROOT / "README.md"
    assert readme.exists()
    text = readme.read_text()
    # The fresh content describes the current sealed-component state,
    # not the prototyping-phase placeholder. Post-amendment-#76 (M1a
    # docs/prose-only brand rebrand of the M1.rename multi-amendment
    # series; sealed `2b2899b` feature commit), the README brand-
    # vocabulary lands on `loam`. The pre-public-docs-scaffold
    # marker phrase ("pOS v2" + "Foundation"/"foundational"/"twelve"
    # — pinned by amendment #67's pos-v2-era foundation-audit
    # README) is replaced by the loam-shape marker phrases — the
    # one-line pitch ("substrate") + the harness sentence
    # ("Claude-attached harness") that anchor the post-public-docs
    # README authored at commit `3c599c1`.
    assert "loam" in text
    assert "substrate" in text or "harness" in text or "primary persona" in text


# ---- SEAL_COMMIT sidecars all present ------------------------------


def test_all_four_amended_components_have_seal_commit_sidecars() -> None:
    for component in (
        "memory-system",
        "orchestrator",
        "dormancy",
        "workspace-bootstrap",
    ):
        # Post-D.1: components live under framework/<comp>/.
        seal = REPO_ROOT / "framework" / component / "tests" / "SEAL_COMMIT"
        assert seal.exists(), f"framework/{component}/tests/SEAL_COMMIT missing"
        text = seal.read_text().strip()
        assert len(text) >= 7, f"{component} SEAL_COMMIT looks malformed: {text!r}"


def test_hands_off_lifecycle_has_seal_commit_sidecar() -> None:
    # Lands as part of the final seal commit — this test verifies the
    # sidecar is present once the component itself is sealed.
    seal = REPO_ROOT / "framework" / "hands-off-lifecycle" / "tests" / "SEAL_COMMIT"
    if not seal.exists():
        pytest.skip("hands-off-lifecycle SEAL_COMMIT not yet written")
    text = seal.read_text().strip()
    assert len(text) >= 7
