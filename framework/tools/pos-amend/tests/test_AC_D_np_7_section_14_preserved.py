"""Tests for AC.D-np.7 — skeleton's §14 scaffold preserved byte-identical
for ``pos-amend seal --plan-doc``.

Per `docs/rebuild/plans/pos-amend-new-plan-orchestration.md`:

    A plan-doc rendered from the post-extension skeleton can be the
    target of ``pos-amend seal --plan-doc <abs-path>`` exactly as a
    plan-doc rendered from the pre-extension skeleton was. The §14
    heading text (``## 14. Method-decision record (builder, post-build)``)
    and the ``### Commit SHAs`` subsection heading are byte-identical
    between pre- and post-extension renderings.

The pre-extension §14 block is captured here as a reference string;
the post-extension render must contain that block verbatim (the seal
machinery's heading-locator depends on it).
"""

from __future__ import annotations

from pathlib import Path

from pos_amend.cli import main


# Pre-extension §14 reference block. Captured from the
# pre-extension ``tools/pos-amend/templates/plan/dev-discipline.md``
# at the point this AC was authored. AC.D-np.7 enforces byte-identity:
# the post-extension render's §14 substring matches this reference.
PRE_EXTENSION_SECTION_14 = """## 14. Method-decision record (builder, post-build)

The plan §11 left D-build.x method choices to the builder within the
ACs' outcome bounds. This section is populated post-build.

### D-build.x — (placeholder for the build agent's method choices)

### Test breakdown

(placeholder)

### Backwards-compat verification

(placeholder)

### Commit SHAs

(placeholder; auto-filled by `pos-amend seal --plan-doc <ABSOLUTE PATH>` per the seal-automation extension. Pass an ABSOLUTE path to avoid the `Path.relative_to` crash documented at commit `75c4d73`. The amendment commit + seal commit + plan-SHA backfill commit each appear here on completion.)

### Commit SHAs

(populated by `pos-amend seal --plan-doc <this-file> ...` after build, or appended manually for dev-discipline plans)

### Dependents cleared to dispatch

(placeholder)"""


def _render_skeleton_against_minimal_vars(tmp_path: Path) -> str:
    vars_file = tmp_path / "vars.yaml"
    vars_file.write_text(
        "TITLE: t\n"
        "TLDR: t\n"
        "AC_PREFIX: AC.X.x\n"
        "SPEC_PLACEMENT: t\n"
        "LENS_ANALYSIS: t\n"
        "ACCEPTANCE_CRITERIA: t\n"
        "BEHAVIOUR_COUNT: t\n"
        "HARD_CONSTRAINTS: t\n"
        "OUT_OF_SCOPE: t\n"
        "IMPLEMENTATION_ORDER: t\n"
        "SECTION_9_HEADING: t\n"
        "SECTION_9_BODY: t\n"
        "HALT_TRIGGERS: t\n"
        "DECISIONS_DETAIL: t\n"
        "DECISIONS_SUMMARY: t\n"
        "HALT_FINDINGS: t\n",
        encoding="utf-8",
    )
    out = tmp_path / "rendered.md"
    rc = main(
        [
            "template",
            "render",
            "plan/dev-discipline",
            "--vars-file",
            str(vars_file),
            "--out",
            str(out),
        ]
    )
    assert rc == 0
    return out.read_text(encoding="utf-8")


def test_AC_D_np_7_section_14_block_byte_identical_to_pre_extension(
    tmp_path: Path,
) -> None:
    rendered = _render_skeleton_against_minimal_vars(tmp_path)
    assert PRE_EXTENSION_SECTION_14 in rendered, (
        "post-extension render diverges from pre-extension §14 block; "
        "seal-automation extension's --plan-doc heading-locator depends "
        "on byte-identity"
    )


def test_AC_D_np_7_section_14_heading_text_present_verbatim(
    tmp_path: Path,
) -> None:
    rendered = _render_skeleton_against_minimal_vars(tmp_path)
    assert "## 14. Method-decision record (builder, post-build)" in rendered


def test_AC_D_np_7_commit_shas_subsection_present_verbatim(
    tmp_path: Path,
) -> None:
    rendered = _render_skeleton_against_minimal_vars(tmp_path)
    assert "### Commit SHAs" in rendered
