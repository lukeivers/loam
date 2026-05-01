"""Tests for AC.D-np.1 — `loam amend new-plan <slug>` scaffolds a vars-file
at the predictable path.

Per `docs/rebuild/plans/pos-amend-new-plan-orchestration.md`:

    Invoking ``loam amend new-plan <slug>`` (with no other flags) writes a
    YAML vars-file at ``<repo-root>/docs/rebuild/plans/<slug>.vars.yaml``.
    The file is a YAML mapping carrying one entry per required variable
    in the plan-doc skeleton's frontmatter contract (the 16 required vars
    per the research-doc inventory).

The scaffolded file must be well-formed YAML; ``yaml.safe_load`` against
it produces a dict whose keys cover every required variable. The vars-file
must successfully feed into ``loam amend template render plan/dev-discipline``
(AC.D-np.1 plus AC.D-np.5).
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from loam_amend.cli import main
from loam_amend.commands import new_plan as new_plan_cmd
from loam_amend.commands import template as template_cmd
from loam_amend.template_engine import parse_template


# Required variables per the plan-doc skeleton (locked at 16 per
# research §3 inventory). This list is the test contract; if the
# skeleton's `required:` list changes, this test breaks loudly so the
# operator notices.
REQUIRED_VARS = (
    "TITLE",
    "TLDR",
    "AC_PREFIX",
    "SPEC_PLACEMENT",
    "LENS_ANALYSIS",
    "ACCEPTANCE_CRITERIA",
    "BEHAVIOUR_COUNT",
    "HARD_CONSTRAINTS",
    "OUT_OF_SCOPE",
    "IMPLEMENTATION_ORDER",
    "SECTION_9_HEADING",
    "SECTION_9_BODY",
    "HALT_TRIGGERS",
    "DECISIONS_DETAIL",
    "DECISIONS_SUMMARY",
    "HALT_FINDINGS",
)


def test_AC_D_np_1_scaffolds_vars_file_at_predictable_path(
    tmp_path: Path,
) -> None:
    rc = new_plan_cmd.run("example-slug", repo_root=tmp_path)
    assert rc == 0
    expected = tmp_path / "docs" / "rebuild" / "plans" / "example-slug.vars.yaml"
    assert expected.is_file()


def test_AC_D_np_1_scaffolded_file_is_wellformed_yaml_mapping(
    tmp_path: Path,
) -> None:
    rc = new_plan_cmd.run("example-slug", repo_root=tmp_path)
    assert rc == 0
    target = tmp_path / "docs" / "rebuild" / "plans" / "example-slug.vars.yaml"
    loaded = yaml.safe_load(target.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)


def test_AC_D_np_1_every_required_var_present_as_key(tmp_path: Path) -> None:
    rc = new_plan_cmd.run("example-slug", repo_root=tmp_path)
    assert rc == 0
    target = tmp_path / "docs" / "rebuild" / "plans" / "example-slug.vars.yaml"
    loaded = yaml.safe_load(target.read_text(encoding="utf-8"))
    for name in REQUIRED_VARS:
        assert name in loaded, f"required var '{name}' missing from scaffold"


def test_AC_D_np_1_scaffolded_vars_render_skeleton_clean(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The scaffolded vars-file must successfully render the bundled
    ``plan/dev-discipline`` template — no missing required vars, no
    unrecognised vars.
    """
    rc = new_plan_cmd.run("example-slug", repo_root=tmp_path)
    assert rc == 0
    capsys.readouterr()  # discard stdout from new-plan
    vars_file = tmp_path / "docs" / "rebuild" / "plans" / "example-slug.vars.yaml"
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
    # Sanity: a few section headings appear.
    assert "## 1. Summary / TLDR" in out
    assert "## 14. Method-decision record" in out
    # No unmatched placeholders.
    assert "{{" not in out


def test_AC_D_np_1_invocation_via_cli_main_succeeds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Drive via the public ``loam amend new-plan <slug>`` CLI surface
    (rather than ``new_plan_cmd.run`` directly). ``--vars-out`` overrides
    the default repo-root resolution so this exercises the CLI argparse
    + dispatch wiring.
    """
    target = tmp_path / "scaffold.vars.yaml"
    rc = main(
        [
            "new-plan",
            "example-slug",
            "--vars-out",
            str(target),
        ]
    )
    assert rc == 0
    assert target.is_file()
    loaded = yaml.safe_load(target.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    for name in REQUIRED_VARS:
        assert name in loaded


def test_AC_D_np_1_scaffold_does_not_render_plan_doc_by_default(
    tmp_path: Path,
) -> None:
    """Without ``--render``, the orchestration writes only the vars-file
    (no plan-doc on disk). Captures the locked D-7 (``--render`` opt-in)
    behaviour at the AC.D-np.1 boundary.
    """
    rc = new_plan_cmd.run("example-slug", repo_root=tmp_path)
    assert rc == 0
    plan_path = tmp_path / "docs" / "rebuild" / "plans" / "example-slug.md"
    assert not plan_path.exists()
