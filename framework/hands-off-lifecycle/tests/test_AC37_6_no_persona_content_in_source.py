"""Amendment #37 — AC37.6 — no persona content shipped from
``hands-off-lifecycle/``.

Plan §4 AC37.6 outcomes:

  - Source under ``hands-off-lifecycle/hooks/`` does not contain
    persona prose. The agent-file body is composed at write time by
    calling amendment #35's ``to_agent_md(contract)``; the contract
    is read from ``<workspace>/personas/<handle>/contract.yaml``.
  - A test-fixture contract whose prose fields are unique sentinel
    strings produces an agent-file containing those sentinels —
    proving the prose came from the contract, not from a constant
    in ``hands-off-lifecycle/`` source.

Maps to v1.2 R16 framework-not-content → AC.PO.2 (toolkit purity).
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml


REPO_ROOT = Path(__file__).resolve().parents[3]
HOOKS_DIR = REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

from agent_file_authoring import (  # noqa: E402
    agent_file_path,
    write_agent_file,
)


# ---- AC37.6 — sentinel-prose test ------------------------------------


def test_AC37_6_sentinel_prose_flows_through_renderer(tmp_path: Path) -> None:
    """Inject sentinel strings into the contract; after the runner
    renders, the on-disk agent file carries those sentinels — proving
    the prose came from the workspace's contract, not from a hands-
    off-lifecycle/ source constant.

    Mutation strategy: YAML round-trip on the contract dict, NOT
    fragile substring replacement. Per ODD §8.2.10 the test asserts
    the OUTCOME (contract prose flows through renderer) without
    coupling to specific template substrings, so template prose
    changes (e.g. amendment #50's archetype rewrite) do not break
    this test."""
    SENTINEL_GIVEN_NAME = "ZorkBlatherSentinel42"
    SENTINEL_RESPONSIBILITY = (
        "Sentinel prose marker for AC37.6: handle banana coordination."
    )

    ws = tmp_path / "ws"
    ws.mkdir()
    template = REPO_ROOT / "framework" / "primary-persona" / "templates" / "persona-template"
    persona_dir = ws / "personas" / "primary"
    persona_dir.parent.mkdir(parents=True)
    shutil.copytree(template, persona_dir)
    contract_path = persona_dir / "contract.yaml"
    contract = yaml.safe_load(contract_path.read_text())
    contract["handle"] = "primary"
    contract["given_name"] = SENTINEL_GIVEN_NAME
    contract.setdefault("responsibilities", {})
    contract["responsibilities"]["single_point_of_contact"] = SENTINEL_RESPONSIBILITY
    contract["is_starter"] = True
    contract_path.write_text(yaml.safe_dump(contract, sort_keys=False))

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
    envelope = json.loads(result.stdout)
    write_agent_file(
        workspace_root=ws,
        handle=envelope["handle"],
        body=envelope["body"],
    )
    on_disk = agent_file_path(ws, envelope["handle"]).read_text(encoding="utf-8")

    # Both sentinels appear in the rendered file → the prose came
    # from the workspace's contract, not from a constant in source.
    assert SENTINEL_GIVEN_NAME in on_disk, (
        "AC37.6: the contract's given_name sentinel must appear on disk"
    )
    assert SENTINEL_RESPONSIBILITY[: len(SENTINEL_RESPONSIBILITY) // 2] in on_disk, (
        "AC37.6: the contract's responsibility sentinel must appear on disk"
    )


# ---- AC37.6 — no persona-prose constants in source -------------------


def test_AC37_6_hooks_source_has_no_persona_prose() -> None:
    """Scan ``hands-off-lifecycle/hooks/`` source for persona-prose
    sentinel patterns. A persona-prose constant in source would mean
    the framework ships content (R16 violation). Specifically check:
      * no occurrence of the framework persona-template's example
        prose (would mean it leaked into source)
      * no hardcoded ``given_name`` / ``handle`` literals beyond
        ``"primary"`` (the default-handle constant) — and the default
        lives in workspace-bootstrap, not here.
    """
    forbidden_sentinels: list[str] = [
        # The framework template's example prose — must never appear in
        # hands-off-lifecycle/ source. (It legitimately lives in
        # primary-persona/templates/persona-template/.)
        "Describe, in one sentence, what this persona is the sole contact for.",
        # The framework template's example given_name — same logic.
        "given_name: Example",
        # An identity-anchor sentence shape from the renderer — would
        # indicate hands-off-lifecycle/ duplicated the renderer.
        "I am Example (example-persona)",
    ]
    for py_file in sorted(HOOKS_DIR.glob("*.py")):
        text = py_file.read_text(encoding="utf-8")
        for sentinel in forbidden_sentinels:
            assert sentinel not in text, (
                f"AC37.6: persona-prose sentinel {sentinel!r} appears in "
                f"{py_file.name} — the framework must not ship content"
            )


def test_AC37_6_renderer_not_re_implemented_in_hooks() -> None:
    """The agent-file body MUST come from amendment #35's renderer.
    A re-implementation in hands-off-lifecycle/ would defeat the
    framework-not-content boundary. Structural check: no source file
    in hands-off-lifecycle/hooks/ defines a function whose name
    matches ``to_agent_md`` (the renderer's own name) — only imports
    or subprocess invocations."""
    for py_file in sorted(HOOKS_DIR.glob("*.py")):
        text = py_file.read_text(encoding="utf-8")
        # Imports of to_agent_md from primary_persona are fine; a local
        # `def to_agent_md(...)` is a violation.
        assert "def to_agent_md" not in text, (
            f"AC37.6: hands-off-lifecycle must not re-implement "
            f"to_agent_md (found a local definition in {py_file.name})"
        )


def test_AC37_6_agent_file_authoring_module_is_renderer_free() -> None:
    """The new agent_file_authoring module should be an on-disk write
    primitive — no persona-prose, no rendering. Pure I/O."""
    text = (HOOKS_DIR / "agent_file_authoring.py").read_text(encoding="utf-8")
    # Must NOT import from primary_persona — the writer is stdlib-only.
    assert "primary_persona" not in text, (
        "agent_file_authoring.py must remain stdlib-only — no "
        "primary_persona import"
    )
    # Must NOT contain persona-prose.
    assert "Persona prompt" not in text
    assert "Identity anchor" not in text
