"""AC.SPDISC.COLLAT — collateral references to `start-project` reflect
the post-promotion subdirectory shape across all sites the plan-author
surfaced.

Per amendment-A-PROMOTE-START-PROJECT plan-doc §4 AC.SPDISC.COLLAT
(merged with the DSDLC-LIST EXPECTED_SKILLS update per plan §11):
five sites + the EXPECTED_SKILLS list need updates so the corpus
no longer hard-codes or describes the v0.1.0 flat-shape as
real-tree truth.

Sites covered:
  (a) plugins/dev-sdlc/README.md — names the subdirectory shape
      path.
  (b) docs/design/layered-skill-architecture.md — flat-shape example
      no longer cites `start-project.md` as real-tree truth.
  (c) plugins/dev-sdlc/tests/test_AC_SKILLS_DSDLC1_7_*.py docstring
      — no longer claims "flat-file start-project.md shipped with
      v0.1.0".
  (d) plugins/dev-sdlc/tests/test_AC_SKILLS_DSDLC2_7_*.py docstring
      — same. Plus EXPECTED_SKILLS admits `start-project` as the
      16th SKILL (per plan §11; necessary for exact-equality test).
  (e) framework/workspace-bootstrap/tests/test_AC_LAYERED_2_*.py
      docstring — no longer claims the real-tree has the flat-shape;
      historical-context wording.

RED-on-mutation: reverting any single edit flips the matching
assertion.

Ladder: AC.SPDISC.COLLAT → AC.SPDISC.MV (the relocation that makes
these collateral references stale) → AC.PO.1 (translation-burden:
operator-readable docs reflect reality so readers don't form a
wrong mental model of the on-disk layout).
"""

from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent

DEV_SDLC_README = REPO_ROOT / "plugins" / "dev-sdlc" / "README.md"
LAYERED_DESIGN_DOC = (
    REPO_ROOT / "docs" / "design" / "layered-skill-architecture.md"
)
DSDLC1_TEST = (
    REPO_ROOT
    / "plugins"
    / "dev-sdlc"
    / "tests"
    / "test_AC_SKILLS_DSDLC1_7_all_six_skills_discovered.py"
)
DSDLC2_TEST = (
    REPO_ROOT
    / "plugins"
    / "dev-sdlc"
    / "tests"
    / "test_AC_SKILLS_DSDLC2_7_all_twelve_skills_discovered.py"
)
LAYERED_TEST = (
    REPO_ROOT
    / "framework"
    / "workspace-bootstrap"
    / "tests"
    / "test_AC_LAYERED_2_skill_symlink_registration.py"
)


def test_AC_SPDISC_COLLAT_a_dev_sdlc_readme_names_subdirectory_shape() -> None:
    """(a) plugins/dev-sdlc/README.md names the subdirectory-shape
    path `plugins/dev-sdlc/skills/start-project/SKILL.md`."""
    body = DEV_SDLC_README.read_text(encoding="utf-8")
    assert "plugins/dev-sdlc/skills/start-project/SKILL.md" in body, (
        f"AC.SPDISC.COLLAT (a) requires {DEV_SDLC_README} to name "
        "the subdirectory-shape path; pre-amendment it cited the "
        "flat-shape `start-project.md` path."
    )


def test_AC_SPDISC_COLLAT_b_layered_design_doc_no_realtree_flat_example() -> None:
    """(b) docs/design/layered-skill-architecture.md no longer cites
    `plugins/dev-sdlc/skills/start-project.md` as the canonical
    real-tree flat-shape example. The flat-shape skip-contract is
    still discussed (the design doc is documenting the layer's
    out-of-fence scope) but with a hypothetical example, not a
    false real-tree claim."""
    body = LAYERED_DESIGN_DOC.read_text(encoding="utf-8")
    # The pre-amendment phrasing "(e.g., plugins/dev-sdlc/skills/
    # start-project.md)" must be gone.
    assert "plugins/dev-sdlc/skills/start-project.md" not in body, (
        f"AC.SPDISC.COLLAT (b) requires {LAYERED_DESIGN_DOC} to no "
        "longer cite the flat-shape `start-project.md` path as a "
        "real-tree example (no canonical flat-shape SKILL exists "
        "post-A-PROMOTE-START-PROJECT)."
    )


def test_AC_SPDISC_COLLAT_c_dsdlc1_docstring_no_flat_shape_claim() -> None:
    """(c) DSDLC1.7 test docstring no longer claims "in addition to
    the flat-file `start-project.md` shipped with v0.1.0 of the
    plugin"."""
    body = DSDLC1_TEST.read_text(encoding="utf-8")
    assert (
        "flat-file `start-project.md` shipped with v0.1.0 of the plugin"
        not in body
    ), (
        f"AC.SPDISC.COLLAT (c) requires {DSDLC1_TEST} docstring to "
        "no longer claim the flat-file shape as v0.1.0 truth (post-"
        "A-PROMOTE-START-PROJECT the SKILL ships as subdirectory)."
    )


def test_AC_SPDISC_COLLAT_d_dsdlc2_docstring_no_flat_shape_claim() -> None:
    """(d) DSDLC2.7 test docstring no longer claims "in addition to
    the flat-file `start-project.md` shipped with v0.1.0"."""
    body = DSDLC2_TEST.read_text(encoding="utf-8")
    assert (
        "in addition to the flat-file `start-project.md`" not in body
    ), (
        f"AC.SPDISC.COLLAT (d) requires {DSDLC2_TEST} docstring to "
        "no longer claim the flat-file shape (post-promotion the "
        "SKILL is subdirectory + listed in EXPECTED_SKILLS)."
    )


def test_AC_SPDISC_COLLAT_d_dsdlc2_expected_skills_admits_start_project() -> None:
    """(d-cont) DSDLC2.7 EXPECTED_SKILLS includes `start-project`.

    Per plan §11: the test asserts exact-equality between discovered
    SKILLs and EXPECTED_SKILLS. Post-promotion the discovered set
    grows by 1; the expected list MUST grow in lockstep or the test
    fails on the orphan."""
    # Import EXPECTED_SKILLS from the actual test module so we assert
    # against the live value (Tier-0 verification against the actual
    # symbol the production assertion uses).
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "_dsdlc2_for_collat_check", DSDLC2_TEST
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    expected = module.EXPECTED_SKILLS
    assert "start-project" in expected, (
        f"AC.SPDISC.COLLAT (d-cont) requires `start-project` in "
        f"DSDLC2.7 EXPECTED_SKILLS; got {expected}."
    )


def test_AC_SPDISC_COLLAT_e_layered_test_no_realtree_flat_claim() -> None:
    """(e) AC.LAYERED.2 test docstring no longer claims the
    real-tree has the flat-shape; historical-context wording per
    plan §10 D-SPDISC.LAYERED-2-TEST-COMMENT."""
    body = LAYERED_TEST.read_text(encoding="utf-8")
    # Pre-amendment exact wording: "Mirrors plugins/dev-sdlc/skills/
    # start-project.md (real-tree shape that exists today)".
    assert "real-tree shape that exists today" not in body, (
        f"AC.SPDISC.COLLAT (e) requires {LAYERED_TEST} docstring to "
        "no longer claim the flat-shape exists in the real tree today "
        "(it doesn't, post-A-PROMOTE-START-PROJECT)."
    )
