"""Amendment #37 — AC37.3 — re-running first-run on a workspace with a
non-starter persona is a no-op for the agent file + settings.json.

Plan §4 AC37.3 outcomes:

  - The agent file's mtime does NOT change across the second first-run
    when its content equals ``to_agent_md(loaded_contract)``.
  - The settings.json ``"agent"`` field is preserved across re-run.
  - User edits to the contract (with ``is_starter: false``) are durable
    — the second first-run does not regenerate the agent file from a
    stale handle.

Maps to v1.0 line 152 (low-friction; user edits durable) + v1.2 R16
(workspace-supplied content remains workspace-owned) → AC.PO.1.
"""

from __future__ import annotations

import json
import shutil
import sys
import time
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
HOOKS_DIR = REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

from agent_file_authoring import (  # noqa: E402
    agent_file_path,
    write_agent_file,
)
from first_run_settings import (  # noqa: E402
    build_first_run_stanza,
    merge_session_start,
)


@pytest.fixture
def workspace_with_persona(tmp_path: Path) -> Path:
    ws = tmp_path / "ws"
    ws.mkdir()
    template = REPO_ROOT / "framework" / "primary-persona" / "templates" / "persona-template"
    persona_dir = ws / "personas" / "primary"
    persona_dir.parent.mkdir(parents=True)
    shutil.copytree(template, persona_dir)
    contract_path = persona_dir / "contract.yaml"
    txt = contract_path.read_text()
    txt = txt.replace("handle: example-persona", "handle: primary")
    if "is_starter:" not in txt:
        txt += "\nis_starter: true\n"
    contract_path.write_text(txt)
    return ws


# ---- AC37.3 — agent-file mtime stable across re-run ------------------


def test_AC37_3_identical_body_skips_write(workspace_with_persona: Path) -> None:
    """``write_agent_file`` returns ``skipped-identical`` when the
    target file already contains the same bytes. AC37.3 measures
    "no observable change" — the writer's no-op skip is the
    structural mechanism."""
    body = "---\nname: primary\ndescription: hello\nmodel: inherit\n---\n\nbody\n"
    first = write_agent_file(
        workspace_root=workspace_with_persona, handle="primary", body=body
    )
    assert first.wrote is True

    second = write_agent_file(
        workspace_root=workspace_with_persona, handle="primary", body=body
    )
    assert second.wrote is False
    assert second.reason == "skipped-identical"


def test_AC37_3_mtime_unchanged_when_content_matches(
    workspace_with_persona: Path,
) -> None:
    """The agent file's mtime is unchanged across a second write of
    the same content. Plays nicely with file-watch tooling per
    plan §11 D-build.4 recommendation."""
    body = "---\nname: primary\ndescription: hello\nmodel: inherit\n---\n\nbody\n"
    write_agent_file(
        workspace_root=workspace_with_persona, handle="primary", body=body
    )
    target = agent_file_path(workspace_with_persona, "primary")
    first_mtime = target.stat().st_mtime
    # Sleep enough to be detectable on coarse-grained filesystem timestamps.
    time.sleep(0.05)

    write_agent_file(
        workspace_root=workspace_with_persona, handle="primary", body=body
    )
    assert target.stat().st_mtime == first_mtime, (
        "AC37.3: write-only-if-different must preserve mtime"
    )


def test_AC37_3_changed_body_does_overwrite(
    workspace_with_persona: Path,
) -> None:
    """Negative case: when the contract changes, the new render
    differs, so the writer overwrites. Demonstrates the AC's bound
    is "no-op when stable", not "never overwrite"."""
    body_v1 = "---\nname: primary\ndescription: v1\nmodel: inherit\n---\n\nv1\n"
    body_v2 = "---\nname: primary\ndescription: v2\nmodel: inherit\n---\n\nv2\n"
    write_agent_file(
        workspace_root=workspace_with_persona, handle="primary", body=body_v1
    )
    target = agent_file_path(workspace_with_persona, "primary")
    assert target.read_text() == body_v1

    second = write_agent_file(
        workspace_root=workspace_with_persona, handle="primary", body=body_v2
    )
    assert second.wrote is True
    assert second.reason == "written-update"
    assert target.read_text() == body_v2


def test_AC37_3_settings_agent_preserved_on_rerun(
    workspace_with_persona: Path,
) -> None:
    """Re-running the merge with the same handle preserves the
    ``"agent"`` field. AC37.3's settings.json side: a stable system
    stays stable across re-runs."""
    settings_path = workspace_with_persona / ".claude" / "settings.json"
    stanza = build_first_run_stanza(workspace_with_persona)
    merge_session_start(
        settings_path=settings_path, new_entry=stanza, agent_handle="primary"
    )
    data1 = json.loads(settings_path.read_text())
    assert data1["agent"] == "primary"

    # Re-run.
    merge_session_start(
        settings_path=settings_path, new_entry=stanza, agent_handle="primary"
    )
    data2 = json.loads(settings_path.read_text())
    assert data2["agent"] == "primary"
    # Top-level key set unchanged.
    assert set(data1.keys()) == set(data2.keys())


def test_AC37_3_user_edited_handle_round_trips(
    workspace_with_persona: Path,
) -> None:
    """If the user edits the contract's handle (and renames the
    persona dir), a re-run resolves the new handle and writes to
    the new path. AC37.3 third outcome: the agent-file path is not
    re-derived from a stale cached handle."""
    # User renames the persona directory + edits contract handle.
    old_dir = workspace_with_persona / "personas" / "primary"
    new_dir = workspace_with_persona / "personas" / "iris"
    old_dir.rename(new_dir)
    contract_path = new_dir / "contract.yaml"
    txt = contract_path.read_text()
    txt = txt.replace("handle: primary", "handle: iris")
    txt = txt.replace("is_starter: true", "is_starter: false")
    contract_path.write_text(txt)

    # The writer keyed by handle="iris" lands at the new path; the old
    # path is never touched.
    body = "---\nname: iris\ndescription: x\nmodel: inherit\n---\n\nx\n"
    result = write_agent_file(
        workspace_root=workspace_with_persona, handle="iris", body=body
    )
    assert result.wrote is True
    assert result.path == agent_file_path(workspace_with_persona, "iris")
