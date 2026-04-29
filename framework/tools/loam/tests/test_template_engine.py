"""Tests for ``loam amend template`` (AC.D-tpl.1–AC.D-tpl.7).

Per the dispatch-prompt-template-extension plan:

- AC.D-tpl.1 — deterministic ``{{KEY}}`` substitution.
- AC.D-tpl.2 — required + optional variable contract.
- AC.D-tpl.3 — stdout default, ``--out`` opt-in with refuse-overwrite.
- AC.D-tpl.4 — ``list`` and ``validate`` introspection.
- AC.D-tpl.5 — every failure mode halts with a structured diagnostic.
- AC.D-tpl.6 — pre-existing loam amend behaviour byte-identical
  (covered by the rest of the test suite continuing to pass; this file
  adds an explicit sanity check that the bundled ``template`` import
  does not perturb the existing CLI surface).
- AC.D-tpl.7 — initial registry ships dispatch + plan families.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from loam_cli.amend.cli import main
from loam_cli.amend.commands import template as template_cmd
from loam_cli.amend.template_engine import (
    MissingRequiredVariable,
    TemplateMalformed,
    TemplateNotFound,
    UnrecognisedVariable,
    parse_template_text,
    render,
)


# ---------------------------------------------------------------------------
# Fixtures


@pytest.fixture
def tpl_root(tmp_path: Path) -> Path:
    """Create a tiny templates registry under ``tmp_path/templates/``."""
    root = tmp_path / "templates"
    (root / "famA").mkdir(parents=True)
    (root / "famB").mkdir(parents=True)
    (root / "famA" / "alpha.md").write_text(
        "---\n"
        "description: \"alpha template — exercises required + optional\"\n"
        "required:\n"
        "  - GREETING\n"
        "optional:\n"
        "  TARGET: world\n"
        "---\n"
        "{{GREETING}}, {{TARGET}}!\n",
        encoding="utf-8",
    )
    (root / "famA" / "beta.md").write_text(
        "---\n"
        "description: \"beta template — escape-syntax exercise\"\n"
        "required: []\n"
        "optional: {}\n"
        "---\n"
        "literal \\{{BRACES\\}} stay literal; no placeholders here.\n",
        encoding="utf-8",
    )
    (root / "famB" / "gamma.md").write_text(
        "---\n"
        "description: \"gamma template — different family\"\n"
        "required: [NAME]\n"
        "optional: {}\n"
        "---\n"
        "Hello {{NAME}}.\n",
        encoding="utf-8",
    )
    return root


@pytest.fixture
def malformed_root(tmp_path: Path) -> Path:
    root = tmp_path / "templates"
    (root / "bad").mkdir(parents=True)
    (root / "bad" / "no-frontmatter.md").write_text(
        "no yaml fence here\n", encoding="utf-8"
    )
    (root / "bad" / "broken-yaml.md").write_text(
        "---\n: [::\n---\nbody\n", encoding="utf-8"
    )
    (root / "bad" / "unmatched.md").write_text(
        "---\ndescription: \"unmatched braces\"\nrequired: []\noptional: {}\n"
        "---\ntext with stray {{ left over\n",
        encoding="utf-8",
    )
    (root / "bad" / "undeclared-placeholder.md").write_text(
        "---\ndescription: \"placeholder not in contract\"\nrequired: []\n"
        "optional: {}\n---\nHello {{UNDECLARED}}.\n",
        encoding="utf-8",
    )
    return root


# ---------------------------------------------------------------------------
# AC.D-tpl.1 — deterministic substitution


def test_AC_D_tpl_1_render_substitutes_placeholders_deterministically(
    tpl_root: Path,
) -> None:
    rc = main(
        [
            "template",
            "--templates-root",
            str(tpl_root),
            "render",
            "famA/alpha",
            "--var",
            "GREETING=hi",
            "--var",
            "TARGET=Luke",
        ]
    )
    assert rc == 0


def test_AC_D_tpl_1_render_byte_identical_across_invocations(
    tpl_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    main(
        [
            "template",
            "--templates-root",
            str(tpl_root),
            "render",
            "famA/alpha",
            "--var",
            "GREETING=hi",
        ]
    )
    out_first = capsys.readouterr().out
    main(
        [
            "template",
            "--templates-root",
            str(tpl_root),
            "render",
            "famA/alpha",
            "--var",
            "GREETING=hi",
        ]
    )
    out_second = capsys.readouterr().out
    assert out_first == out_second
    assert out_first == "hi, world!\n"


def test_AC_D_tpl_1_escape_preserves_literal_braces(
    tpl_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    rc = main(
        [
            "template",
            "--templates-root",
            str(tpl_root),
            "render",
            "famA/beta",
        ]
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert out == "literal {{BRACES}} stay literal; no placeholders here.\n"


# ---------------------------------------------------------------------------
# AC.D-tpl.2 — required + optional contract


def test_AC_D_tpl_2_missing_required_variable_halts(
    tpl_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    rc = main(
        [
            "template",
            "--templates-root",
            str(tpl_root),
            "render",
            "famA/alpha",
        ]
    )
    assert rc == 2
    err = capsys.readouterr().err
    assert "missing-required-variable" in err
    assert "GREETING" in err


def test_AC_D_tpl_2_optional_default_applied_when_unspecified(
    tpl_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    rc = main(
        [
            "template",
            "--templates-root",
            str(tpl_root),
            "render",
            "famA/alpha",
            "--var",
            "GREETING=hi",
        ]
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert out == "hi, world!\n"


def test_AC_D_tpl_2_unrecognised_variable_halts(
    tpl_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    rc = main(
        [
            "template",
            "--templates-root",
            str(tpl_root),
            "render",
            "famA/alpha",
            "--var",
            "GREETING=hi",
            "--var",
            "TYPO=oops",
        ]
    )
    assert rc == 2
    err = capsys.readouterr().err
    assert "unrecognised-variable" in err
    assert "TYPO" in err


def test_AC_D_tpl_2_required_optional_overlap_is_malformed() -> None:
    text = (
        "---\n"
        "description: \"bad\"\n"
        "required: [X]\n"
        "optional:\n  X: dup\n"
        "---\nbody {{X}}\n"
    )
    with pytest.raises(TemplateMalformed):
        parse_template_text(text, family="t", template_id="t")


# ---------------------------------------------------------------------------
# AC.D-tpl.3 — stdout default, --out opt-in, refuse-overwrite


def test_AC_D_tpl_3_default_render_to_stdout_writes_no_file(
    tpl_root: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    rc = main(
        [
            "template",
            "--templates-root",
            str(tpl_root),
            "render",
            "famA/alpha",
            "--var",
            "GREETING=hi",
        ]
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert out == "hi, world!\n"
    # No new files in tpl_root or tmp_path beyond the fixture tree.
    # Verify by checking nothing was written under tmp_path's top
    # level besides the templates dir.
    children = sorted(p.name for p in tmp_path.iterdir())
    assert children == ["templates"]


def test_AC_D_tpl_3_out_writes_file(tpl_root: Path, tmp_path: Path) -> None:
    target = tmp_path / "out" / "rendered.md"
    rc = main(
        [
            "template",
            "--templates-root",
            str(tpl_root),
            "render",
            "famA/alpha",
            "--var",
            "GREETING=hi",
            "--out",
            str(target),
        ]
    )
    assert rc == 0
    assert target.read_text(encoding="utf-8") == "hi, world!\n"


def test_AC_D_tpl_3_out_refuses_overwrite_without_force(
    tpl_root: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    target = tmp_path / "rendered.md"
    target.write_text("preexisting content\n", encoding="utf-8")
    rc = main(
        [
            "template",
            "--templates-root",
            str(tpl_root),
            "render",
            "famA/alpha",
            "--var",
            "GREETING=hi",
            "--out",
            str(target),
        ]
    )
    assert rc == 3
    err = capsys.readouterr().err
    assert "refuse-overwrite" in err
    assert target.read_text(encoding="utf-8") == "preexisting content\n"


def test_AC_D_tpl_3_out_force_overwrites(
    tpl_root: Path, tmp_path: Path
) -> None:
    target = tmp_path / "rendered.md"
    target.write_text("preexisting\n", encoding="utf-8")
    rc = main(
        [
            "template",
            "--templates-root",
            str(tpl_root),
            "render",
            "famA/alpha",
            "--var",
            "GREETING=hi",
            "--out",
            str(target),
            "--force",
        ]
    )
    assert rc == 0
    assert target.read_text(encoding="utf-8") == "hi, world!\n"


# ---------------------------------------------------------------------------
# AC.D-tpl.4 — list + validate introspection


def test_AC_D_tpl_4_list_enumerates_registered_templates(
    tpl_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    rc = main(
        [
            "template",
            "--templates-root",
            str(tpl_root),
            "list",
        ]
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert "famA/" in out
    assert "famB/" in out
    assert "alpha" in out
    assert "beta" in out
    assert "gamma" in out
    assert "alpha template" in out


def test_AC_D_tpl_4_validate_reports_required_optional_placeholders(
    tpl_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    rc = main(
        [
            "template",
            "--templates-root",
            str(tpl_root),
            "validate",
            "famA/alpha",
        ]
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert "required" in out and "GREETING" in out
    assert "optional" in out and "TARGET" in out


def test_AC_D_tpl_4_validate_malformed_template_exits_nonzero(
    malformed_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    rc = main(
        [
            "template",
            "--templates-root",
            str(malformed_root),
            "validate",
            "bad/no-frontmatter",
        ]
    )
    assert rc == 2
    err = capsys.readouterr().err
    assert "template-malformed" in err


# ---------------------------------------------------------------------------
# AC.D-tpl.5 — failure modes halt with structured diagnostics


def test_AC_D_tpl_5_unknown_template_id(
    tpl_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    rc = main(
        [
            "template",
            "--templates-root",
            str(tpl_root),
            "render",
            "famA/does-not-exist",
        ]
    )
    assert rc == 2
    err = capsys.readouterr().err
    assert "template-not-found" in err


def test_AC_D_tpl_5_malformed_frontmatter(
    malformed_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    rc = main(
        [
            "template",
            "--templates-root",
            str(malformed_root),
            "render",
            "bad/broken-yaml",
        ]
    )
    assert rc == 2
    err = capsys.readouterr().err
    assert "template-malformed" in err


def test_AC_D_tpl_5_unmatched_braces_in_body(
    malformed_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    rc = main(
        [
            "template",
            "--templates-root",
            str(malformed_root),
            "render",
            "bad/unmatched",
        ]
    )
    assert rc == 2
    err = capsys.readouterr().err
    assert "template-malformed" in err


def test_AC_D_tpl_5_undeclared_placeholder_treated_as_malformed(
    malformed_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # Body references {{UNDECLARED}}, but neither required nor optional
    # contains it. Rendering surfaces this as a malformed-template
    # diagnostic and does NOT silently emit the literal placeholder.
    rc = main(
        [
            "template",
            "--templates-root",
            str(malformed_root),
            "render",
            "bad/undeclared-placeholder",
        ]
    )
    assert rc == 2
    err = capsys.readouterr().err
    assert "template-malformed" in err
    assert "UNDECLARED" in err


def test_AC_D_tpl_5_no_partial_stdout_on_render_failure(
    tpl_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    rc = main(
        [
            "template",
            "--templates-root",
            str(tpl_root),
            "render",
            "famA/alpha",
            # No --var GREETING — required missing.
        ]
    )
    assert rc == 2
    captured = capsys.readouterr()
    # Stdout must be empty on render failure (halt before output).
    assert captured.out == ""
    assert "missing-required-variable" in captured.err


def test_AC_D_tpl_5_no_partial_file_on_render_failure(
    tpl_root: Path, tmp_path: Path
) -> None:
    target = tmp_path / "should-not-exist.md"
    rc = main(
        [
            "template",
            "--templates-root",
            str(tpl_root),
            "render",
            "famA/alpha",
            "--out",
            str(target),
            # No --var GREETING — render() raises before write.
        ]
    )
    assert rc == 2
    assert not target.exists()


def test_AC_D_tpl_5_malformed_var_flag(
    tpl_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    rc = main(
        [
            "template",
            "--templates-root",
            str(tpl_root),
            "render",
            "famA/alpha",
            "--var",
            "no-equals-sign",
        ]
    )
    assert rc == 2
    err = capsys.readouterr().err
    assert "KEY=VALUE" in err


def test_AC_D_tpl_5_vars_file_must_be_yaml_mapping(
    tpl_root: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    bad = tmp_path / "vars.yaml"
    bad.write_text("- a list, not a mapping\n", encoding="utf-8")
    rc = main(
        [
            "template",
            "--templates-root",
            str(tpl_root),
            "render",
            "famA/alpha",
            "--vars-file",
            str(bad),
        ]
    )
    assert rc == 2
    err = capsys.readouterr().err
    assert "mapping" in err


# ---------------------------------------------------------------------------
# AC.D-tpl.5 — engine-level unit checks (parse + render)


def test_engine_render_raises_missing_required() -> None:
    text = "---\nrequired: [X]\noptional: {}\n---\n{{X}}"
    tpl = parse_template_text(text, family="f", template_id="t")
    with pytest.raises(MissingRequiredVariable):
        render(tpl, {})


def test_engine_render_raises_unrecognised_variable() -> None:
    text = "---\nrequired: []\noptional: {}\n---\nbody"
    tpl = parse_template_text(text, family="f", template_id="t")
    with pytest.raises(UnrecognisedVariable):
        render(tpl, {"GHOST": "x"})


def test_engine_parse_raises_template_not_found(tmp_path: Path) -> None:
    from loam_cli.amend.template_engine import parse_template

    with pytest.raises(TemplateNotFound):
        parse_template(
            tmp_path / "nope.md", family="f", template_id="nope"
        )


# ---------------------------------------------------------------------------
# AC.D-tpl.6 — pre-existing loam amend behaviour byte-identical
#
# The existing test suite (test_cli, test_apply, test_seal, ...) already
# exercises every pre-existing surface; their continued green status IS
# the AC.D-tpl.6 evidence. This explicit check guards against the
# template module's import perturbing the existing CLI surface (regress
# example: an import-time side effect that mutates argparse defaults).


def test_AC_D_tpl_6_existing_help_lists_existing_subcommands(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit):
        main(["--help"])
    out = capsys.readouterr().out
    for sub in ("validate", "apply", "seal"):
        assert sub in out
    # New subcommand lands too — additive.
    assert "template" in out


def test_AC_D_tpl_6_console_script_still_resolves() -> None:
    # Post-M1g: the console script is ``loam`` (not ``pos-amend``);
    # the unified CLI registers ``--version`` at top level.
    result = subprocess.run(
        [sys.executable, "-m", "loam_cli", "--version"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "loam" in result.stdout


# ---------------------------------------------------------------------------
# AC.D-tpl.7 — initial registry ships dispatch + plan families


def _bundled_root() -> Path:
    return template_cmd.DEFAULT_TEMPLATES_ROOT


def test_AC_D_tpl_7_bundled_root_contains_dispatch_and_plan_families() -> None:
    root = _bundled_root()
    assert (root / "dispatch" / "sealed-component-build.md").is_file()
    assert (root / "plan" / "dev-discipline.md").is_file()


def test_AC_D_tpl_7_bundled_dispatch_template_validates(
    capsys: pytest.CaptureFixture[str],
) -> None:
    rc = main(["template", "validate", "dispatch/sealed-component-build"])
    assert rc == 0
    out = capsys.readouterr().out
    for name in ("COMPONENT", "AMENDMENT_NUMBER", "AC_PREFIX", "PLAN_PATH"):
        assert name in out


def test_AC_D_tpl_7_bundled_plan_template_validates(
    capsys: pytest.CaptureFixture[str],
) -> None:
    rc = main(["template", "validate", "plan/dev-discipline"])
    assert rc == 0
    out = capsys.readouterr().out
    for name in ("TITLE", "TLDR", "AC_PREFIX"):
        assert name in out


def test_AC_D_tpl_7_bundled_dispatch_renders_against_fixture_vars(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    vars_file = tmp_path / "vars.yaml"
    vars_file.write_text(
        "COMPONENT: example-component\n"
        "AMENDMENT_NUMBER: 99\n"
        "AC_PREFIX: AC.X.x\n"
        "PLAN_PATH: docs/rebuild/plans/example.md\n"
        "OBJECTIVE: \"Single-paragraph fixture objective.\"\n"
        "SCOPE_FENCE: \"path/to/component/\"\n"
        "WORKING_DIRECTORY: /tmp/fixture\n",
        encoding="utf-8",
    )
    rc = main(
        [
            "template",
            "render",
            "dispatch/sealed-component-build",
            "--vars-file",
            str(vars_file),
        ]
    )
    assert rc == 0
    out = capsys.readouterr().out
    # Fixture-renders contain every required variable substituted in:
    assert "example-component" in out
    assert "amendment #99" in out
    assert "AC.X.x" in out
    assert "docs/rebuild/plans/example.md" in out
    assert "Single-paragraph fixture objective." in out
    assert "path/to/component/" in out
    assert "/tmp/fixture" in out
    # No literal {{ left in the rendered output (defensive — escaped
    # braces decode at the end of render()).
    # The dispatch template has no \{{ escapes, so any {{ in stdout
    # would be a missed substitution.
    assert "{{" not in out


def test_AC_D_tpl_7_bundled_plan_renders_against_fixture_vars(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    vars_file = tmp_path / "vars.yaml"
    vars_file.write_text(
        "TITLE: example-plan\n"
        "TLDR: \"One paragraph.\"\n"
        "AC_PREFIX: AC.X.x\n"
        "SPEC_PLACEMENT: \"§2.5 framing.\"\n"
        "LENS_ANALYSIS: \"Three lenses.\"\n"
        "ACCEPTANCE_CRITERIA: \"AC list.\"\n"
        "BEHAVIOUR_COUNT: \"Behaviour table.\"\n"
        "HARD_CONSTRAINTS: \"Constraints.\"\n"
        "OUT_OF_SCOPE: \"Out of scope.\"\n"
        "IMPLEMENTATION_ORDER: \"Order.\"\n"
        "SECTION_9_HEADING: \"Impact / motivation\"\n"
        "SECTION_9_BODY: \"Body of section 9.\"\n"
        "HALT_TRIGGERS: \"Halts.\"\n"
        "DECISIONS_DETAIL: \"Detail.\"\n"
        "DECISIONS_SUMMARY: \"Summary.\"\n"
        "HALT_FINDINGS: \"Findings.\"\n",
        encoding="utf-8",
    )
    rc = main(
        [
            "template",
            "render",
            "plan/dev-discipline",
            "--vars-file",
            str(vars_file),
        ]
    )
    assert rc == 0
    out = capsys.readouterr().out
    assert "# example-plan — plan" in out
    assert "## 14. Method-decision record" in out
    # Every required-section heading appears (1..14):
    for section in (
        "## 1. Summary",
        "## 2. Spec-objective",
        "## 3. Three-lens",
        "## 4. Acceptance criteria",
        "## 5. Behaviour-count",
        "## 6. Hard constraints",
        "## 7. Out of scope",
        "## 8. Implementation order",
        "## 10. Halt triggers",
        "## 11. Decisions",
        "## 12. Summary of named decisions",
        "## 13. Halt-and-surface",
        "## 14. Method-decision",
    ):
        assert section in out
    assert "{{" not in out
