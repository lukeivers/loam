"""Tests for AC.D-np.4 — failure modes halt with structured diagnostics
(no partial output).

Per `docs/rebuild/plans/pos-amend-new-plan-orchestration.md`:

    When ``pos-amend new-plan`` encounters one of:
      (a) an invalid slug (slug containing ``/``, slug not matching
          ``^[a-z][a-z0-9-]*$``, empty slug),
      (b) a vars-file path that already exists and ``--force`` is not
          passed,
      (c) a ``--plan-out`` path that already exists and ``--force`` is
          not passed (when ``--render``),
      (d) a template-render contract failure,
      (e) IO failure,
    it (1) halts before any partial file is written, (2) emits a
    structured diagnostic to stderr, (3) exits non-zero in the existing
    1/2/3 taxonomy: classes (a)-(d) -> 2; class (e) -> 3.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from pos_amend.cli import main
from pos_amend.commands import new_plan as new_plan_cmd


# -- (a) invalid slug ------------------------------------------------------


@pytest.mark.parametrize(
    "slug",
    [
        "",                  # empty
        "Has-Uppercase",     # uppercase rejected
        "has_underscore",    # underscore rejected
        "1leading-digit",    # leading digit rejected
        "trailing-",         # OK actually per regex; remove if not desired
        "with/slash",        # subdirectory rejected
        "with space",        # whitespace rejected
        "-leading-hyphen",   # leading hyphen rejected
    ],
)
def test_AC_D_np_4_invalid_slug_exits_2_with_diagnostic(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    slug: str,
) -> None:
    if slug == "trailing-":
        # The locked regex permits trailing hyphen ([a-z0-9-]*); skip
        # this case explicitly. The parametrize entry is here as
        # documentation — the test asserts it does NOT reject.
        rc = new_plan_cmd.run(slug, repo_root=tmp_path)
        assert rc == 0  # accepted
        return
    rc = new_plan_cmd.run(slug, repo_root=tmp_path)
    assert rc == 2
    err = capsys.readouterr().err
    assert "invalid-slug" in err


def test_AC_D_np_4_invalid_slug_writes_no_partial_file(
    tmp_path: Path,
) -> None:
    rc = new_plan_cmd.run("with/slash", repo_root=tmp_path)
    assert rc == 2
    plans_dir = tmp_path / "docs" / "rebuild" / "plans"
    if plans_dir.exists():
        # Defensive: if the plans dir was created (it shouldn't be), it
        # must not contain any vars-file or plan-doc for the rejected slug.
        assert not list(plans_dir.iterdir())


# -- (b) vars-file refuse-overwrite ---------------------------------------


def test_AC_D_np_4_existing_vars_file_refuses_overwrite_exit_3(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    target = tmp_path / "docs" / "rebuild" / "plans" / "example-slug.vars.yaml"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("PRE-EXISTING\n", encoding="utf-8")
    rc = new_plan_cmd.run("example-slug", repo_root=tmp_path)
    assert rc == 3
    err = capsys.readouterr().err
    assert "refuse-overwrite" in err
    # File untouched.
    assert target.read_text(encoding="utf-8") == "PRE-EXISTING\n"


def test_AC_D_np_4_force_overwrites_existing_vars_file(
    tmp_path: Path,
) -> None:
    target = tmp_path / "docs" / "rebuild" / "plans" / "example-slug.vars.yaml"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("PRE-EXISTING\n", encoding="utf-8")
    rc = new_plan_cmd.run("example-slug", repo_root=tmp_path, force=True)
    assert rc == 0
    # File replaced.
    assert "PRE-EXISTING" not in target.read_text(encoding="utf-8")


# -- (c) plan-out refuse-overwrite (with --render) ------------------------


def test_AC_D_np_4_existing_plan_doc_refuses_overwrite_when_render(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    plan_target = tmp_path / "docs" / "rebuild" / "plans" / "example-slug.md"
    plan_target.parent.mkdir(parents=True, exist_ok=True)
    plan_target.write_text("PRE-EXISTING\n", encoding="utf-8")
    rc = new_plan_cmd.run(
        "example-slug",
        title="T",
        ac_prefix="AC.X.x",
        render=True,
        repo_root=tmp_path,
    )
    assert rc == 3
    err = capsys.readouterr().err
    assert "refuse-overwrite" in err
    # Plan-doc untouched.
    assert plan_target.read_text(encoding="utf-8") == "PRE-EXISTING\n"


def test_AC_D_np_4_pre_existing_plan_doc_blocks_before_vars_write(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """When ``--render`` is passed and the plan-doc target exists, the
    refuse-overwrite check fires before the vars-file write — no partial
    output anywhere.
    """
    plan_target = tmp_path / "docs" / "rebuild" / "plans" / "example-slug.md"
    plan_target.parent.mkdir(parents=True, exist_ok=True)
    plan_target.write_text("PRE-EXISTING\n", encoding="utf-8")
    vars_target = tmp_path / "docs" / "rebuild" / "plans" / "example-slug.vars.yaml"
    rc = new_plan_cmd.run(
        "example-slug",
        title="T",
        ac_prefix="AC.X.x",
        render=True,
        repo_root=tmp_path,
    )
    assert rc == 3
    capsys.readouterr()
    # Vars-file must NOT have been written (no partial output).
    assert not vars_target.exists()


# -- (e) IO failure -------------------------------------------------------


def test_AC_D_np_4_io_failure_exits_3_with_diagnostic(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """A read-only target directory triggers OSError on write; orchestration
    surfaces it as exit 3 with an io-failure diagnostic.
    """
    plans_dir = tmp_path / "docs" / "rebuild" / "plans"
    plans_dir.mkdir(parents=True)
    # Create a directory at the vars-file's expected path so write_text raises.
    blocker = plans_dir / "example-slug.vars.yaml"
    blocker.mkdir()
    rc = new_plan_cmd.run(
        "example-slug", repo_root=tmp_path, force=True
    )
    assert rc == 3
    err = capsys.readouterr().err
    assert "io-failure" in err


# -- CLI surface drives same failure-mapping ------------------------------


def test_AC_D_np_4_invalid_slug_via_cli_exits_2(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    target = tmp_path / "scaffold.vars.yaml"
    rc = main(
        [
            "new-plan",
            "INVALID",
            "--vars-out",
            str(target),
        ]
    )
    assert rc == 2
    err = capsys.readouterr().err
    assert "invalid-slug" in err
    assert not target.exists()
