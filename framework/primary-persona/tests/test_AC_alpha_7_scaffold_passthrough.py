"""AC.α.7 — Workspace scaffold lands the new template content
unchanged at default-handle path.

Per plan §4 AC.α.7, a workspace bootstrap run via
``run_first_run_scaffold`` against a tmpfs ``pos_root`` produces
``<workspace>/personas/<handle>/prompt.md`` whose body equals the
framework template's ``prompt.md`` body verbatim (modulo
line-endings). No source edit to ``workspace-bootstrap/`` is
required for this AC to pass — the scaffold's existing
copy-template-verbatim logic carries the post-α prompt.md content
through unchanged.

Mirrors L's AC.O.7 shape applied to the post-α template content;
the byte-equality check verifies that α's spine + new operational
rule land at the workspace's default persona path through the
existing scaffold.
"""

from __future__ import annotations

from pathlib import Path

import pytest


workspace_bootstrap = pytest.importorskip(
    "loam.workspace_bootstrap.adapters.first_run_scaffold"
)
run_first_run_scaffold = workspace_bootstrap.run_first_run_scaffold
DEFAULT_PERSONA_HANDLE = workspace_bootstrap.DEFAULT_PERSONA_HANDLE


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
TEMPLATE_PROMPT = (
    REPO_ROOT / "framework" / "primary-persona"
    / "templates" / "persona-template" / "prompt.md"
)


def _run_scaffold(tmp_path: Path):
    pos_root = tmp_path / "pos_root"
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    return run_first_run_scaffold(
        pos_root=pos_root,
        workspace_root=workspace,
        platform_override="macos",
        service_bootstrap=False,
        service_manager_dir_override=tmp_path / "agents",
    ), workspace


def test_AC_alpha_7_scaffolded_prompt_md_byte_equals_post_alpha_template(
    tmp_path: Path,
):
    """The scaffold produces a workspace prompt.md byte-equal to
    the framework template's post-α prompt.md."""
    _, workspace = _run_scaffold(tmp_path)
    workspace_prompt = (
        workspace / "workspace" / "personas" / DEFAULT_PERSONA_HANDLE
        / "prompt.md"
    ).read_text()
    template_body = TEMPLATE_PROMPT.read_text()
    assert workspace_prompt == template_body, (
        "scaffolded prompt.md drifted from post-α template body; "
        "α's spine + Lean on the corpus rule did not pass through "
        "the scaffold unchanged"
    )


def test_AC_alpha_7_scaffolded_prompt_md_carries_capability_leverage_spine(
    tmp_path: Path,
):
    """The scaffolded prompt.md carries the α-added Capability
    leverage spine section (as a redundant byte-content check on
    the scaffold pathway)."""
    _, workspace = _run_scaffold(tmp_path)
    workspace_prompt = (
        workspace / "workspace" / "personas" / DEFAULT_PERSONA_HANDLE
        / "prompt.md"
    ).read_text()
    assert "## Capability leverage spine" in workspace_prompt
    assert "### Lean on the corpus" in workspace_prompt
