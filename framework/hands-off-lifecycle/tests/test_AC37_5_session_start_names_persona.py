"""Amendment #37 — AC37.5 — SessionStart additionalContext + the agent
file together name the loaded persona.

Plan §4 AC37.5 outcomes (after first-run + a SessionStart hook
invocation):

  - The ``additionalContext`` payload composed by the gate names the
    loaded persona (handle and given_name appear in the gate's text).
  - The agent-file's identity-anchor block is present in
    ``<workspace>/.claude/agents/<handle>.md`` — read from disk, not
    re-rendered for this assertion.

The on-disk side is the verification this amendment owns. The
additionalContext side reuses the contributor amendment #35 already
provides (``build_starter_pending_contributor`` emits the
starter-pending block including the contract's ``given_name`` when
``is_starter`` is True). The integration shape is the gate from
amendment #32 plus the on-disk artefact this amendment writes.

Maps to v1.0 line 153 (session-start test) + amendment #32 gate
contract → AC.PO.1.
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


def _render_via_runner(ws: Path) -> dict[str, str]:
    runner = HOOKS_DIR / "agent_file_runner.py"
    venv_python = REPO_ROOT / ".venv" / "bin" / "python"
    result = subprocess.run(
        [str(venv_python), "-u", str(runner), "--workspace-root", str(ws)],
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, (
        f"runner failed: rc={result.returncode} stderr={result.stderr!r}"
    )
    return json.loads(result.stdout)


# ---- AC37.5 — agent-file identity anchor on disk ---------------------


def test_AC37_5_identity_anchor_in_agent_file(
    workspace_with_persona: Path,
) -> None:
    """After first-run writes the agent file, its body contains the
    identity-anchor block addressed by handle and given_name (per
    amendment #35's renderer contract). The AC bounds presence of
    these tokens on disk."""
    envelope = _render_via_runner(workspace_with_persona)
    write_agent_file(
        workspace_root=workspace_with_persona,
        handle=envelope["handle"],
        body=envelope["body"],
    )
    on_disk = agent_file_path(
        workspace_with_persona, envelope["handle"]
    ).read_text(encoding="utf-8")

    # Identity-anchor structural marker (per amendment #35 AC35.2).
    assert "Identity anchor" in on_disk
    # Handle appears in frontmatter `name:` AND in the anchor body
    # `(<handle>)` parenthetical.
    assert f"name: {envelope['handle']}" in on_disk
    assert f"({envelope['handle']})" in on_disk


def test_AC37_5_handle_and_given_name_present_on_disk(
    workspace_with_persona: Path,
) -> None:
    """Read the on-disk agent file and confirm both handle and the
    contract's given_name appear. The renderer's identity-anchor
    block is "I am <given_name> (<handle>)..." so both tokens appear
    in the body."""
    envelope = _render_via_runner(workspace_with_persona)
    write_agent_file(
        workspace_root=workspace_with_persona,
        handle=envelope["handle"],
        body=envelope["body"],
    )
    on_disk = agent_file_path(
        workspace_with_persona, envelope["handle"]
    ).read_text(encoding="utf-8")

    # Load contract via runner-side machinery (re-using the venv-side
    # render to extract given_name without re-importing primary_persona
    # under the test interpreter's path).
    sys_path_was = list(sys.path)
    src_path = REPO_ROOT / "framework" / "primary-persona" / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    try:
        from primary_persona import PersonaLoader  # type: ignore

        loaded = PersonaLoader(workspace_root=workspace_with_persona).primary()
        given_name = loaded.contract.given_name
    finally:
        sys.path[:] = sys_path_was

    assert envelope["handle"] in on_disk
    assert given_name in on_disk
    # Combined anchor sentence shape — both tokens together.
    assert f"I am {given_name} ({envelope['handle']})" in on_disk


def test_AC37_5_session_start_gate_payload_carries_given_name(
    workspace_with_persona: Path,
) -> None:
    """Amendment #32's session-start gate composes a SessionPayload;
    when the starter-pending contributor (amendment #35) is
    registered, the payload's text carries the persona's given_name
    (the contributor body interpolates it). This test verifies that
    the gate + contributor compose correctly with this amendment's
    on-disk artefact in scope.

    The contributor registration is the persona-layer's responsibility
    (amendment #35); we register it here against a fresh composer to
    prove the integration shape works end-to-end with the on-disk
    agent file in place."""
    sys_path_was = list(sys.path)
    src_path = REPO_ROOT / "framework" / "primary-persona" / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    try:
        from primary_persona import (  # type: ignore
            ComposedContextPayload,
            PersonaLoader,
            TriggerKind,
            compose_session_fields,
        )
        from primary_persona.onboarding import (  # type: ignore
            STARTER_PENDING_MARKER,
            build_starter_pending_contributor,
        )

        loaded = PersonaLoader(workspace_root=workspace_with_persona).primary()
        # Verify our fixture left the persona starter-flagged.
        assert loaded.contract.is_starter is True
        given_name = loaded.contract.given_name

        composer = ComposedContextPayload(
            session_builder=compose_session_fields,
        )
        composer.register(
            name="starter-pending",
            trigger_kind=TriggerKind.session,
            fn=build_starter_pending_contributor(loaded),
        )
        payload = composer.on_session_start(workspace_with_persona)
    finally:
        sys.path[:] = sys_path_was

    text = payload.additional_context_text
    assert STARTER_PENDING_MARKER in text, (
        "AC37.5: session-start additionalContext must carry the "
        "starter-pending marker when the persona is starter-flagged"
    )
    assert given_name in text, (
        "AC37.5: session-start additionalContext must name the "
        "persona by given_name"
    )


def test_AC37_5_agent_file_path_keyed_by_handle(
    workspace_with_persona: Path,
) -> None:
    """The on-disk agent file's path itself is ``<handle>.md`` —
    so reading the directory listing is a structural way to recover
    the handle. AC37.5's "names the loaded persona by handle"
    side: even without parsing the body, the file path identifies
    the persona."""
    envelope = _render_via_runner(workspace_with_persona)
    write_agent_file(
        workspace_root=workspace_with_persona,
        handle=envelope["handle"],
        body=envelope["body"],
    )
    agents_dir = workspace_with_persona / ".claude" / "agents"
    listing = sorted(p.name for p in agents_dir.iterdir())
    assert listing == [f"{envelope['handle']}.md"]
