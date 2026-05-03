# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""AC.D.2.1 + AC.D.2.2 + AC.D.2.3 — workspace-bootstrap scaffolds
workspace state under ``<workspace>/workspace/`` (with ``.claude/``
preserved at workspace root).

Verifies the post-D.2 scaffold writer outputs:

- AC.D.2.1: every workspace-state file lives under
  ``<fixture-ws>/workspace/<...>``. Pre-D.2 paths
  (``<fixture-ws>/.pos/``, ``<fixture-ws>/personas/``, etc.) are
  NOT created.

- AC.D.2.2: ``<fixture-ws>/.claude/`` lives at workspace root,
  preserving the D-Q.A4 lock (Claude Code expectation).

- AC.D.2.3: launchd plist EnvironmentVariables / WorkingDirectory /
  StandardOutPath / StandardErrorPath reference the new layout.

HC#4 binding: byte-content match (or substring match for templated
content) for each scaffolded workspace-state file. Pre-existing
default content (e.g. ``memory-worker.yaml`` retry-curve) MUST land
unchanged at the new location.

Backing AC: AC.D.2.1, AC.D.2.2, AC.D.2.3.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from loam.workspace_bootstrap.adapters.first_run_scaffold import (
    PREWARM_ADVISORY_FILENAME,
    WORKER_CONFIG_FILENAME,
    run_first_run_scaffold,
    service_label,
)
from loam.workspace_bootstrap.workspace_paths import (
    POS_SUBDIR,
    WORKSPACE_STATE_SUBDIR,
)


def _scaffold(tmp_path: Path) -> tuple[Path, Path, Path]:
    """Run the scaffold against a fresh fixture workspace; return
    ``(workspace, pos_root, agents_dir)``.
    """
    workspace = tmp_path / "ivers-corp-test-ws"
    workspace.mkdir()
    pos_root = tmp_path / "pos"
    agents = tmp_path / "LaunchAgents"
    run_first_run_scaffold(
        pos_root=pos_root,
        platform_override="macos",
        service_bootstrap=False,
        service_manager_dir_override=agents,
        workspace_root=workspace,
    )
    return workspace, pos_root, agents


def test_AC_D_2_1_pos_subdir_lands_under_workspace_state(tmp_path: Path) -> None:
    """``.pos/`` workspace-state lives under ``<ws>/workspace/.pos/``,
    NOT ``<ws>/.pos/``.
    """
    workspace, _pos_root, _agents = _scaffold(tmp_path)

    # Post-D.2 location.
    new_pos = workspace / WORKSPACE_STATE_SUBDIR / POS_SUBDIR
    assert new_pos.is_dir(), (
        f"AC.D.2.1: workspace-state .pos/ must live under "
        f"<ws>/workspace/.pos/, got missing: {new_pos}"
    )

    # Pre-D.2 location (must NOT be present).
    old_pos = workspace / POS_SUBDIR
    assert not old_pos.exists(), (
        f"AC.D.2.1: pre-D.2 <ws>/.pos/ must NOT be created post-D.2; "
        f"found: {old_pos}"
    )


def test_AC_D_2_1_personas_dir_lands_under_workspace_state(
    tmp_path: Path,
) -> None:
    """Persona directory lives under ``<ws>/workspace/personas/``."""
    workspace, _pos_root, _agents = _scaffold(tmp_path)

    new_personas = workspace / WORKSPACE_STATE_SUBDIR / "personas"
    assert new_personas.is_dir(), (
        f"AC.D.2.1: personas/ must live under <ws>/workspace/personas/, "
        f"got missing: {new_personas}"
    )

    # Pre-D.2 location (must NOT be present).
    old_personas = workspace / "personas"
    assert not old_personas.exists(), (
        f"AC.D.2.1: pre-D.2 <ws>/personas/ must NOT be created post-D.2; "
        f"found: {old_personas}"
    )


@pytest.mark.skip(
    reason=(
        "FBE.7 (v0.1.0 foldback): scaffold doesn't write .mcp.json at "
        "v0.1.0 (memory-graphiti retired from _SERVICE_KINDS); the path "
        "shape is preserved by mcp_json_writer's pure functions and "
        "M-GMP restores the scaffold-side write post-v0.1.0. See "
        "docs/rebuild/plans/v0-1-0-foldback-scope-expansion-fbe7.md."
    )
)
def test_AC_D_2_1_mcp_json_lands_under_workspace_state(tmp_path: Path) -> None:
    """``.mcp.json`` lives under ``<ws>/workspace/.mcp.json``."""
    workspace, _pos_root, _agents = _scaffold(tmp_path)

    new_mcp = workspace / WORKSPACE_STATE_SUBDIR / ".mcp.json"
    assert new_mcp.is_file(), (
        f"AC.D.2.1: .mcp.json must live under <ws>/workspace/, "
        f"got missing: {new_mcp}"
    )

    old_mcp = workspace / ".mcp.json"
    assert not old_mcp.exists(), (
        f"AC.D.2.1: pre-D.2 <ws>/.mcp.json must NOT be created post-D.2; "
        f"found: {old_mcp}"
    )


def test_AC_D_2_1_tracker_db_lands_under_workspace_state(tmp_path: Path) -> None:
    """``objective_tracker.sqlite`` lives under
    ``<ws>/workspace/objective_tracker.sqlite``.
    """
    workspace, _pos_root, _agents = _scaffold(tmp_path)

    new_tracker = workspace / WORKSPACE_STATE_SUBDIR / "objective_tracker.sqlite"
    # The tracker DB is seeded only on a workspace classified as user
    # or pos-v2-dev with a value-prop doc; the fresh fixture has no
    # value-prop doc so seeding skips. Test both presence (when
    # seeding lands) and the path-shape contract (location, not
    # existence).
    if new_tracker.exists():
        # Seeded — verify it landed at the new location.
        assert new_tracker.is_file()

    old_tracker = workspace / "objective_tracker.sqlite"
    assert not old_tracker.exists(), (
        f"AC.D.2.1: pre-D.2 <ws>/objective_tracker.sqlite must NOT be "
        f"created post-D.2; found: {old_tracker}"
    )


def test_AC_D_2_2_claude_dir_at_workspace_root_NOT_under_state(
    tmp_path: Path,
) -> None:
    """D-Q.A4 lock: ``<ws>/.claude/`` lives at workspace root, NOT
    under ``<ws>/workspace/``. Claude Code's discovery looks at
    ``<ws>/.claude/``.
    """
    workspace, _pos_root, _agents = _scaffold(tmp_path)

    # The scaffold doesn't currently create ``.claude/`` itself
    # (that's the operator's `claude` invocation), but the
    # workspace-bootstrap-scaffolded ``.gitignore`` MUST permit
    # ``.claude/`` at workspace root — verified via the gitignore
    # body assertion below.
    gitignore = workspace / ".gitignore"
    assert gitignore.is_file(), "AC.D.2.1: <ws>/.gitignore must be scaffolded"
    body = gitignore.read_text(encoding="utf-8")
    assert "!.claude" in body, (
        "AC.D.2.2: <ws>/.gitignore must opt ``.claude/`` back in (D-Q.A4 "
        f"lock — Claude Code expects .claude/ at workspace root). Got: {body!r}"
    )

    # Defence: ``.claude/`` location is NOT inside workspace/.
    bad_claude = workspace / WORKSPACE_STATE_SUBDIR / ".claude"
    assert not bad_claude.exists(), (
        f"AC.D.2.2: ``.claude/`` must NOT be scaffolded under "
        f"<ws>/workspace/; found: {bad_claude}"
    )


def test_AC_D_2_3_orchestrator_plist_uses_new_layout(tmp_path: Path) -> None:
    """Orchestrator plist's WorkingDirectory + StandardOutPath /
    StandardErrorPath reference ``<ws>/workspace/...`` post-D.2.
    """
    workspace, _pos_root, agents = _scaffold(tmp_path)

    label = service_label("orchestrator", workspace.name)
    plist = agents / f"{label}.plist"
    assert plist.exists(), f"orchestrator plist missing: {plist}"
    text = plist.read_text(encoding="utf-8")

    # WorkingDirectory now points at <ws>/workspace/ so cwd-relative
    # writes land in the workspace-state tree.
    assert (
        f"<key>WorkingDirectory</key><string>{workspace}/workspace</string>"
        in text
    ), f"AC.D.2.3: WorkingDirectory must be <ws>/workspace/; got plist:\n{text}"

    # Log paths now under <ws>/workspace/.
    assert (
        f"<key>StandardOutPath</key><string>{workspace}/workspace/orchestrator.out.log</string>"
        in text
    ), f"AC.D.2.3: orchestrator stdout log under <ws>/workspace/; got:\n{text}"
    assert (
        f"<key>StandardErrorPath</key><string>{workspace}/workspace/orchestrator.err.log</string>"
        in text
    ), f"AC.D.2.3: orchestrator stderr log under <ws>/workspace/; got:\n{text}"


def test_AC_D_2_3_memory_write_worker_plist_uses_new_layout(
    tmp_path: Path,
) -> None:
    """Memory-write-worker plist's log paths + WorkingDirectory point
    at ``<ws>/workspace/``.
    """
    workspace, _pos_root, agents = _scaffold(tmp_path)

    label = service_label("memory-write-worker", workspace.name)
    plist = agents / f"{label}.plist"
    assert plist.exists(), f"worker plist missing: {plist}"
    text = plist.read_text(encoding="utf-8")

    assert (
        f"<key>WorkingDirectory</key><string>{workspace}/workspace</string>"
        in text
    )
    assert (
        f"<key>StandardOutPath</key><string>{workspace}/workspace/memory-write-worker.out.log</string>"
        in text
    )
    assert (
        f"<key>StandardErrorPath</key><string>{workspace}/workspace/memory-write-worker.err.log</string>"
        in text
    )


# ---- HC#4 byte-content match assertions ----------------------------------


def test_HC4_memory_worker_yaml_byte_content_match(tmp_path: Path) -> None:
    """HC#4: the scaffolded ``memory-worker.yaml`` carries the
    documented retry-curve defaults at the post-D.2 location with
    byte-stable content.
    """
    workspace, _pos_root, _agents = _scaffold(tmp_path)

    cfg = workspace / WORKSPACE_STATE_SUBDIR / POS_SUBDIR / WORKER_CONFIG_FILENAME
    assert cfg.is_file(), f"HC#4: memory-worker.yaml missing at {cfg}"
    text = cfg.read_text(encoding="utf-8")

    # Substring assertions covering the AC.J retry-curve contract.
    assert "max_retries: 5" in text
    assert "backoff_initial_s: 2.0" in text
    assert "backoff_max_s: 60.0" in text
    assert "poll_interval_s: 1.0" in text
    assert "tmp_cleanup_age_s: 3600.0" in text


def test_HC4_ollama_prewarm_advisory_byte_content_match(tmp_path: Path) -> None:
    """HC#4: ``ollama-prewarm-recommended.txt`` carries the AC.J.1
    OLLAMA_KEEP_ALIVE recommendation at the post-D.2 location.
    """
    workspace, _pos_root, _agents = _scaffold(tmp_path)

    advisory = (
        workspace
        / WORKSPACE_STATE_SUBDIR
        / POS_SUBDIR
        / PREWARM_ADVISORY_FILENAME
    )
    assert advisory.is_file(), (
        f"HC#4: ollama-prewarm-recommended.txt missing at {advisory}"
    )
    text = advisory.read_text(encoding="utf-8")

    # AC.J.1 D-5 lock — exact recommendation.
    assert "OLLAMA_KEEP_ALIVE=24h" in text
    # The advisory's operator-side commands.
    assert "launchctl setenv" in text
    assert "brew services restart ollama" in text


def test_HC4_persona_contract_byte_content_match(tmp_path: Path) -> None:
    """HC#4: the scaffolded persona ``contract.yaml`` carries the
    handle + ``is_starter: true`` at the post-D.2 location.
    """
    workspace, _pos_root, _agents = _scaffold(tmp_path)

    personas = workspace / WORKSPACE_STATE_SUBDIR / "personas"
    # The scaffold installs exactly one persona on a fresh workspace.
    persona_dirs = [p for p in personas.iterdir() if p.is_dir()]
    assert len(persona_dirs) >= 1, (
        f"HC#4: at least one persona must be scaffolded; got "
        f"{persona_dirs}"
    )
    contract = persona_dirs[0] / "contract.yaml"
    assert contract.is_file(), f"HC#4: contract.yaml missing at {contract}"
    text = contract.read_text(encoding="utf-8")

    handle = persona_dirs[0].name
    assert f"handle: {handle}" in text
    assert "is_starter: true" in text


@pytest.mark.skip(
    reason=(
        "FBE.7 (v0.1.0 foldback): scaffold doesn't write .mcp.json at "
        "v0.1.0 (memory-graphiti retired from _SERVICE_KINDS); the byte "
        "content shape is preserved by mcp_json_writer's pure functions "
        "and M-GMP restores the scaffold-side write post-v0.1.0. See "
        "docs/rebuild/plans/v0-1-0-foldback-scope-expansion-fbe7.md."
    )
)
def test_HC4_mcp_json_byte_content_match(tmp_path: Path) -> None:
    """HC#4: ``.mcp.json`` carries a memory-graphiti server registration
    at the post-D.2 location.
    """
    workspace, _pos_root, _agents = _scaffold(tmp_path)

    mcp = workspace / WORKSPACE_STATE_SUBDIR / ".mcp.json"
    assert mcp.is_file(), f"HC#4: .mcp.json missing at {mcp}"
    text = mcp.read_text(encoding="utf-8")
    assert "memory-graphiti" in text, (
        "HC#4: .mcp.json must register memory-graphiti server; "
        f"got: {text!r}"
    )


def test_AC_D_2_1_workspace_gitignore_scaffolded(tmp_path: Path) -> None:
    """The scaffold writes ``<ws>/.gitignore`` declaring framework/
    as the only tracked subtree (D.2-build.E e1).
    """
    workspace, _pos_root, _agents = _scaffold(tmp_path)

    gitignore = workspace / ".gitignore"
    assert gitignore.is_file(), (
        f"AC.D.2.1: <ws>/.gitignore must be scaffolded at {gitignore}"
    )
    body = gitignore.read_text(encoding="utf-8")
    # Default-deny everything.
    assert body.splitlines()[0] == "*" or "*\n" in body or "\n*\n" in body
    # framework/ tracked.
    assert "!framework" in body
    # .claude/ tracked at workspace root (D-Q.A4 lock).
    assert "!.claude" in body
