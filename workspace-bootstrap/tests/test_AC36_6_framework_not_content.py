"""Amendment #36 — AC36.6 — Framework-not-content invariant preserved.

Plan §4 AC36.6 outcomes:

- The scaffold does not embed persona prose in its source — the
  persona directory is materialised by *copying* from the
  framework's persona template
  (``primary-persona/templates/persona-template/``).
- The scaffold's only mutations on the copy are: rename to the
  resolved handle, set ``is_starter: true``, replace the
  placeholder ``handle`` field.
- A known sentinel string from the template appears in the
  scaffolded output (provenance evidence).
- ``workspace-bootstrap/src/`` source carries no persona-prose
  constants.

Maps to v1.2 R16 framework-not-content
(``docs/rebuild/spec/pos-v2-objectives-spec.md`` §348–356) →
AC.PO.2 (toolkit purity).
"""

from __future__ import annotations

from pathlib import Path

from workspace_bootstrap.adapters.first_run_scaffold import (
    DEFAULT_PERSONA_HANDLE,
    _resolve_persona_template_dir,
    run_first_run_scaffold,
)

_WB_SRC_ROOT = (
    Path(__file__).resolve().parent.parent / "src" / "workspace_bootstrap"
)


def _scaffold_fresh(tmp_path: Path) -> Path:
    workspace = tmp_path / "ws-fnc"
    workspace.mkdir()
    pos_root = tmp_path / ".pos"
    agents = tmp_path / "LaunchAgents"
    run_first_run_scaffold(
        pos_root=pos_root,
        platform_override="macos",
        service_bootstrap=False,
        service_manager_dir_override=agents,
        workspace_root=workspace,
    )
    return workspace


def test_AC36_6_template_sentinels_appear_in_scaffold_output(
    tmp_path: Path,
) -> None:
    """A unique sentinel sentence in the persona-template files
    appears in the scaffolded output — proving the prose came from
    the template, not from scaffold source."""
    template_dir = _resolve_persona_template_dir()
    template_prompt = (template_dir / "prompt.md").read_text()

    # Pick a sentinel sentence that is template-specific and unlikely
    # to be re-derived by accident anywhere else.
    sentinel = (
        'This file is free prose. pOS does not parse it.'
    )
    assert sentinel in template_prompt, (
        "test fixture: chosen sentinel must exist in the framework "
        f"persona-template prompt.md; not found in {template_dir / 'prompt.md'}"
    )

    workspace = _scaffold_fresh(tmp_path)
    scaffolded_prompt = (
        workspace
        / "personas"
        / DEFAULT_PERSONA_HANDLE
        / "prompt.md"
    ).read_text()

    assert sentinel in scaffolded_prompt, (
        "scaffolded prompt.md does not carry the framework template's "
        "sentinel sentence — provenance broken."
    )


def test_AC36_6_workspace_bootstrap_src_has_no_persona_prose_constants() -> None:
    """``workspace-bootstrap/src/`` source must not carry literal
    persona-contract prose (the template's sentinel sentences). The
    scaffold's only legitimate persona-prose handling is the
    *copy-from-template* operation."""
    template_dir = _resolve_persona_template_dir()
    # Sentinel phrases that must NOT appear hard-coded in the
    # scaffold source. Each is a distinctive snippet from the
    # framework template.
    forbidden_sentinels = [
        "This file is free prose. pOS does not parse it.",
        "Describe, in one sentence, what this persona is the sole",
        "Two to four sentences grounded in the real-world role",
    ]

    for src_file in _WB_SRC_ROOT.rglob("*.py"):
        text = src_file.read_text()
        for sentinel in forbidden_sentinels:
            assert sentinel not in text, (
                f"{src_file} contains persona-prose sentinel {sentinel!r} — "
                "framework-not-content invariant broken; the scaffold "
                "must copy from primary-persona/templates/, not embed "
                "prose constants."
            )


def test_AC36_6_scaffold_only_mutates_handle_and_is_starter(
    tmp_path: Path,
) -> None:
    """Diff between template ``contract.yaml`` and scaffolded
    ``contract.yaml`` is limited to the ``handle`` and
    ``is_starter`` fields — no other persona-prose fields are
    touched by the scaffold."""
    import yaml

    template_dir = _resolve_persona_template_dir()
    template_contract = yaml.safe_load(
        (template_dir / "contract.yaml").read_text()
    )

    workspace = _scaffold_fresh(tmp_path)
    scaffolded_contract = yaml.safe_load(
        (
            workspace
            / "personas"
            / DEFAULT_PERSONA_HANDLE
            / "contract.yaml"
        ).read_text()
    )

    # Mutations the scaffold is permitted to make.
    assert scaffolded_contract["handle"] == DEFAULT_PERSONA_HANDLE
    assert scaffolded_contract["is_starter"] is True

    # Every other field is byte-identical to the template.
    for key, value in template_contract.items():
        if key in ("handle", "is_starter"):
            continue
        assert scaffolded_contract.get(key) == value, (
            f"scaffold mutated unexpected field {key!r}: "
            f"template={value!r} scaffold={scaffolded_contract.get(key)!r}"
        )

    # No new fields were added beyond is_starter (template carries
    # everything else; is_starter is the only addition).
    template_keys = set(template_contract.keys())
    scaffold_keys = set(scaffolded_contract.keys())
    new_keys = scaffold_keys - template_keys
    assert new_keys.issubset({"is_starter"}), (
        f"scaffold added unexpected keys: {new_keys - {'is_starter'}}"
    )


def test_AC36_6_prompt_md_byte_identical_to_template(tmp_path: Path) -> None:
    """The ``prompt.md`` in the scaffolded persona dir is byte-
    identical to the template's ``prompt.md``. The scaffold does not
    rewrite prompt prose."""
    template_dir = _resolve_persona_template_dir()
    template_prompt = (template_dir / "prompt.md").read_bytes()

    workspace = _scaffold_fresh(tmp_path)
    scaffolded_prompt = (
        workspace
        / "personas"
        / DEFAULT_PERSONA_HANDLE
        / "prompt.md"
    ).read_bytes()

    assert scaffolded_prompt == template_prompt
