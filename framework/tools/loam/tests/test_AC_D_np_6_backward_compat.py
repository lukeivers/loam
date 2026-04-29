"""Tests for AC.D-np.6 — pre-existing loam amend behaviour byte-identical.

Per `docs/rebuild/plans/pos-amend-new-plan-orchestration.md`:

    The full pre-extension ``tools/loam/tests/`` suite passes against
    the post-extension tree without modification. ``loam amend validate``,
    ``loam amend apply [--dry-run]``, ``loam amend seal``, ``loam amend
    template list|render|validate`` exit-code semantics, output formats,
    and side effects are byte-identical. The ``new-plan`` subcommand is
    purely additive — no existing subcommand sees behaviour change. No
    new third-party dependency on ``tools/loam/pyproject.toml``.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from loam_cli.amend.cli import main


def test_AC_D_np_6_help_lists_existing_subcommands_plus_new_plan(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``--help`` enumerates every pre-existing subcommand alongside the
    new ``new-plan``. No pre-existing subcommand was renamed or removed.
    """
    with pytest.raises(SystemExit):
        main(["--help"])
    out = capsys.readouterr().out
    for sub in ("validate", "apply", "seal", "template", "new-plan"):
        assert sub in out


def test_AC_D_np_6_console_script_still_resolves() -> None:
    # Post-M1g: the unified ``loam`` CLI registers ``--version`` at
    # the top-level dispatcher (the ``amend`` subparser does not
    # carry its own ``--version``; this is the post-rename functional
    # equivalent of the pre-rename ``loam amend --version`` surface).
    result = subprocess.run(
        [sys.executable, "-m", "loam_cli", "--version"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "loam" in result.stdout


def test_AC_D_np_6_template_render_pre_existing_dispatch_template_still_renders(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The pre-existing dispatch template (``dispatch/sealed-component-build``)
    is unaffected by the plan-skeleton extension. Renders cleanly against
    the same fixture shape used by AC.D-tpl.7.
    """
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
    assert "example-component" in out
    assert "amendment #99" in out


def test_AC_D_np_6_template_list_includes_plan_dev_discipline(
    capsys: pytest.CaptureFixture[str],
) -> None:
    rc = main(["template", "list"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "plan/" in out
    assert "dev-discipline" in out
    assert "dispatch/" in out
    assert "sealed-component-build" in out


def test_AC_D_np_6_pyproject_no_new_dependency_introduced() -> None:
    """The plan-extension build does not introduce any new third-party
    dependency. The existing dependency list is exactly ``PyYAML>=6``.
    """
    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    contents = pyproject.read_text(encoding="utf-8")
    # Locate the dependencies = [...] line.
    assert 'dependencies = ["PyYAML>=6"]' in contents, (
        "pyproject.toml dependency list changed; AC.D-np.6 disallows new "
        "dependencies. Update only if the change is owner-approved."
    )


def test_AC_D_np_6_existing_template_engine_module_unchanged_at_api_surface() -> None:
    """The template engine's public surface (``parse_template_text``,
    ``render``, ``discover_templates``, ``ParsedTemplate``, error
    classes) remains importable. Sanity check guarding against accidental
    deletion or rename.
    """
    from loam_cli.amend.template_engine import (  # noqa: F401
        MissingRequiredVariable,
        ParsedTemplate,
        TemplateError,
        TemplateMalformed,
        TemplateNotFound,
        UnrecognisedVariable,
        discover_templates,
        parse_template,
        parse_template_text,
        render,
    )
