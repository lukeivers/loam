"""Amendment #37 — AC37.2 — first-run writes ``.claude/agents/<handle>.md``
from the renderer.

Plan §4 AC37.2 outcomes (after first-run completes):

  - ``<workspace>/.claude/agents/<handle>.md`` exists.
  - Its content equals ``to_agent_md(loaded_contract,
    prompt_text=prompt.md)`` against the loaded contract.
  - Frontmatter ``name == handle``; ``description`` derived from the
    contract per amendment #35's renderer.

This AC verifies on-disk content equals the renderer's output. The
renderer's projection contract (frontmatter shape, identity-anchor
prose) is amendment #35 AC35.2's scope; here we measure that the
on-disk file *equals* whatever the renderer emits — i.e., the runner
+ writer compose without lossy transformation.

Maps to v1.0 line 153 → AC.PO.1 + AC.PO.2.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
HOOKS_DIR = REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

from agent_file_authoring import (  # noqa: E402
    agent_file_path,
    write_agent_file,
)


@pytest.fixture
def workspace_with_persona(tmp_path: Path) -> Path:
    """A tmpfs workspace with a workspace-bootstrap-style persona dir.

    Copies the framework persona template into ``personas/primary/`` and
    flips ``handle: primary`` + ``is_starter: true`` per amendment #36's
    scaffold contract. Subsequent tests render the agent file from this
    directory and compare to the renderer's output.
    """
    ws = tmp_path / "ws"
    ws.mkdir()
    # Materialise the same shape amendment #36's scaffold produces.
    template = REPO_ROOT / "framework" / "primary-persona" / "templates" / "persona-template"
    persona_dir = ws / "personas" / "primary"
    persona_dir.parent.mkdir(parents=True)
    shutil.copytree(template, persona_dir)
    # Mutate handle + is_starter the same way amendment #36's scaffold
    # does (yaml round-trip would be cleaner but stdlib-only sufficient
    # for the fixture: simple text replace on the well-known lines).
    contract_path = persona_dir / "contract.yaml"
    txt = contract_path.read_text()
    txt = txt.replace("handle: example-persona", "handle: primary")
    # is_starter is not in the template; appended at scaffold time.
    if "is_starter:" not in txt:
        txt += "\nis_starter: true\n"
    contract_path.write_text(txt)
    return ws


def _render_via_runner(ws: Path) -> dict[str, str]:
    """Invoke ``agent_file_runner.py`` under the repo's shared venv and
    return the parsed JSON envelope."""
    runner = HOOKS_DIR / "agent_file_runner.py"
    venv_python = REPO_ROOT / ".venv" / "bin" / "python"
    assert venv_python.exists(), (
        "test prerequisite: pos-v2 shared venv must exist for the "
        "runner to import primary_persona"
    )
    result = subprocess.run(
        [str(venv_python), "-u", str(runner), "--workspace-root", str(ws)],
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, (
        f"runner failed: rc={result.returncode} "
        f"stdout={result.stdout!r} stderr={result.stderr!r}"
    )
    return json.loads(result.stdout)


def _direct_render(ws: Path, handle: str) -> str:
    """Call the renderer directly — what the runner produces should
    equal this. Any discrepancy means the runner's load+render path
    is doing something the AC does not bound."""
    sys_path_was = list(sys.path)
    src_path = REPO_ROOT / "framework" / "primary-persona" / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    try:
        # Late imports — these resolve only when the shared venv (or
        # the test's editable install) provides pydantic / pyyaml.
        from primary_persona import PersonaLoader  # type: ignore
        from primary_persona.agent_md import to_agent_md  # type: ignore

        loader = PersonaLoader(workspace_root=ws)
        loaded = loader.load_one(handle)
        return to_agent_md(loaded.contract, prompt_text=loaded.prompt_text)
    finally:
        sys.path[:] = sys_path_was


# ---- AC37.2 — agent file written from renderer -----------------------


def test_AC37_2_agent_file_exists_after_write(workspace_with_persona: Path) -> None:
    """End-to-end: render via runner, write via the stdlib writer,
    assert ``.claude/agents/primary.md`` exists with the rendered
    content."""
    envelope = _render_via_runner(workspace_with_persona)
    handle = envelope["handle"]
    body = envelope["body"]
    assert handle == "primary"

    result = write_agent_file(
        workspace_root=workspace_with_persona, handle=handle, body=body
    )
    assert result.wrote is True
    assert result.reason == "written-new"

    target = agent_file_path(workspace_with_persona, handle)
    assert target.exists()
    assert target.read_text(encoding="utf-8") == body


def test_AC37_2_on_disk_content_equals_direct_renderer(
    workspace_with_persona: Path,
) -> None:
    """The on-disk agent file's bytes equal what ``to_agent_md(...)``
    emits against the loaded contract directly. Proves no lossy
    transformation between the runner subprocess and the on-disk
    write — AC37.2's headline outcome."""
    envelope = _render_via_runner(workspace_with_persona)
    write_agent_file(
        workspace_root=workspace_with_persona,
        handle=envelope["handle"],
        body=envelope["body"],
    )
    on_disk = agent_file_path(
        workspace_with_persona, envelope["handle"]
    ).read_text(encoding="utf-8")
    direct = _direct_render(workspace_with_persona, envelope["handle"])
    assert on_disk == direct, (
        "AC37.2: on-disk .claude/agents/<handle>.md must equal "
        "to_agent_md(loaded_contract) bytes"
    )


def test_AC37_2_frontmatter_name_matches_handle(
    workspace_with_persona: Path,
) -> None:
    """Frontmatter ``name`` field equals the resolved handle. The
    renderer's projection contract (AC35.2) is verified by amendment
    #35; this test verifies the on-disk file inherits that property.
    """
    envelope = _render_via_runner(workspace_with_persona)
    write_agent_file(
        workspace_root=workspace_with_persona,
        handle=envelope["handle"],
        body=envelope["body"],
    )
    on_disk = agent_file_path(
        workspace_with_persona, envelope["handle"]
    ).read_text(encoding="utf-8")
    # Frontmatter line.
    assert f"name: {envelope['handle']}" in on_disk
    assert "description: " in on_disk
    assert "model: inherit" in on_disk


def test_AC37_2_writer_creates_parent_dir(workspace_with_persona: Path) -> None:
    """The ``.claude/agents/`` directory does not pre-exist on a fresh
    clone; the writer creates it. AC37.2 implicit precondition (the
    file must be writable into a parent that may not yet exist)."""
    agents_dir = workspace_with_persona / ".claude" / "agents"
    assert not agents_dir.exists(), "fixture precondition"
    envelope = _render_via_runner(workspace_with_persona)
    result = write_agent_file(
        workspace_root=workspace_with_persona,
        handle=envelope["handle"],
        body=envelope["body"],
    )
    assert result.wrote is True
    assert agents_dir.is_dir()
