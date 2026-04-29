"""Tests for AC.D-np.3 — `--render` produces a plan-doc end-to-end.

Per `docs/rebuild/plans/pos-amend-new-plan-orchestration.md`:

    Invoking ``loam amend new-plan <slug> --title "T" --ac-prefix AC.X.x
    --render`` writes BOTH the vars-file at
    ``<repo>/docs/rebuild/plans/<slug>.vars.yaml`` AND a rendered plan-doc
    at ``<repo>/docs/rebuild/plans/<slug>.md``. The rendered plan-doc
    carries every section heading from §1 through §14 verbatim, the
    ``TITLE`` substitution in heading-1, the ``AC_PREFIX`` substitution
    in §4's heading, and the §14 ``### Commit SHAs`` subsection scaffold.
"""

from __future__ import annotations

from pathlib import Path

from loam_cli.amend.commands import new_plan as new_plan_cmd


def test_AC_D_np_3_render_writes_both_files(tmp_path: Path) -> None:
    rc = new_plan_cmd.run(
        "example-slug",
        title="My Title",
        ac_prefix="AC.X.x",
        render=True,
        repo_root=tmp_path,
    )
    assert rc == 0
    vars_path = tmp_path / "docs" / "rebuild" / "plans" / "example-slug.vars.yaml"
    plan_path = tmp_path / "docs" / "rebuild" / "plans" / "example-slug.md"
    assert vars_path.is_file()
    assert plan_path.is_file()


def test_AC_D_np_3_rendered_plan_carries_every_section_heading(
    tmp_path: Path,
) -> None:
    rc = new_plan_cmd.run(
        "example-slug",
        title="My Title",
        ac_prefix="AC.X.x",
        render=True,
        repo_root=tmp_path,
    )
    assert rc == 0
    plan_path = tmp_path / "docs" / "rebuild" / "plans" / "example-slug.md"
    rendered = plan_path.read_text(encoding="utf-8")
    for heading in (
        "## 1. Summary / TLDR",
        "## 2. Spec-objective placement",
        "## 3. Three-lens analysis",
        "## 4. Acceptance criteria",
        "## 5. Behaviour-count check",
        "## 6. Hard constraints",
        "## 7. Out of scope",
        "## 8. Implementation order",
        "## 9. Impact / motivation",
        "## 10. Halt triggers",
        "## 11. Decisions",
        "## 12. Summary of named decisions",
        "## 13. Halt-and-surface",
        "## 14. Method-decision record",
        "## 15. References",
    ):
        assert heading in rendered, f"missing heading: {heading}"


def test_AC_D_np_3_rendered_plan_substitutes_title_in_heading_1(
    tmp_path: Path,
) -> None:
    rc = new_plan_cmd.run(
        "example-slug",
        title="My Special Title",
        ac_prefix="AC.X.x",
        render=True,
        repo_root=tmp_path,
    )
    assert rc == 0
    plan_path = tmp_path / "docs" / "rebuild" / "plans" / "example-slug.md"
    rendered = plan_path.read_text(encoding="utf-8")
    assert "# My Special Title — plan" in rendered


def test_AC_D_np_3_rendered_plan_substitutes_ac_prefix_in_section_4(
    tmp_path: Path,
) -> None:
    rc = new_plan_cmd.run(
        "example-slug",
        title="T",
        ac_prefix="AC.WIDGET.q",
        render=True,
        repo_root=tmp_path,
    )
    assert rc == 0
    plan_path = tmp_path / "docs" / "rebuild" / "plans" / "example-slug.md"
    rendered = plan_path.read_text(encoding="utf-8")
    assert "AC.WIDGET.q" in rendered
    assert "## 4. Acceptance criteria (AC.WIDGET.q" in rendered


def test_AC_D_np_3_rendered_plan_carries_section_14_commit_shas_scaffold(
    tmp_path: Path,
) -> None:
    rc = new_plan_cmd.run(
        "example-slug",
        title="T",
        ac_prefix="AC.X.x",
        render=True,
        repo_root=tmp_path,
    )
    assert rc == 0
    plan_path = tmp_path / "docs" / "rebuild" / "plans" / "example-slug.md"
    rendered = plan_path.read_text(encoding="utf-8")
    assert "### Commit SHAs" in rendered
    # AC.D-np.7 byte-identity asserts the §14 scaffold survives; this AC
    # only requires the subsection is present (so seal-automation has a
    # target to find).


def test_AC_D_np_3_rendered_plan_has_no_unmatched_placeholders(
    tmp_path: Path,
) -> None:
    rc = new_plan_cmd.run(
        "example-slug",
        title="T",
        ac_prefix="AC.X.x",
        render=True,
        repo_root=tmp_path,
    )
    assert rc == 0
    plan_path = tmp_path / "docs" / "rebuild" / "plans" / "example-slug.md"
    rendered = plan_path.read_text(encoding="utf-8")
    assert "{{" not in rendered, "rendered plan has unmatched {{ placeholders"
