"""Tests for AC.NTU.4 — memory-doc skeleton template + ``loam amend new-memory``
orchestration.

Per ``docs/plans/v0-7-0-non-tech-user-surface.md`` AC.NTU.4:

    (a) template file at canonical path; (b) CLI verb registered +
    invokes the renderer; (c) integration test: `loam amend new-memory
    test-rule` produces a syntactically-valid memory file at the expected
    path; the file's frontmatter parses + carries the required fields.
    Reuses the existing template-engine surface (no new engine code).

This test exercises the full slug → vars-file → render path against the
canonical templates root (``plugins/dev-sdlc/templates/memory-doc/SKELETON.md``).
"""

from __future__ import annotations

from pathlib import Path

import yaml

from loam_amend.commands import new_memory as new_memory_cmd


# ---------------------------------------------------------------------------
# (a) Template file at canonical path


def test_AC_NTU_4_template_exists_at_canonical_path() -> None:
    """The memory-doc/SKELETON.md template ships at the conventional
    plugins/dev-sdlc/templates/<family>/<id>.md location.
    """
    repo_root = Path(__file__).resolve().parents[5]
    template_path = (
        repo_root
        / "plugins"
        / "dev-sdlc"
        / "templates"
        / "memory-doc"
        / "SKELETON.md"
    )
    assert template_path.is_file(), (
        f"memory-doc template missing at {template_path}"
    )


def test_AC_NTU_4_template_frontmatter_parses_with_required_fields() -> None:
    """The template's frontmatter declares the 4 required + 7 optional
    vars per the AC's ``required + 7 optional vars`` shape.
    """
    from loam_amend.template_engine import parse_template

    repo_root = Path(__file__).resolve().parents[5]
    template_path = (
        repo_root
        / "plugins"
        / "dev-sdlc"
        / "templates"
        / "memory-doc"
        / "SKELETON.md"
    )
    parsed = parse_template(
        template_path, family="memory-doc", template_id="SKELETON"
    )
    # The 4 required body vars per the SKELETON contract.
    assert "NAME" in parsed.required
    assert "DESCRIPTION" in parsed.required
    assert "DEFINITION_BODY" in parsed.required
    assert "HOW_TO_APPLY_BODY" in parsed.required
    # Optional vars present with defaults (non-exhaustive sample).
    assert "TYPE" in parsed.optional_defaults
    assert "STATUS" in parsed.optional_defaults
    assert "COMPOSES_WITH" in parsed.optional_defaults


# ---------------------------------------------------------------------------
# (b) CLI verb registered


def test_AC_NTU_4_cli_verb_registered_in_attach_subparsers() -> None:
    """``loam amend new-memory`` registers via attach_subparsers and
    parses without error.
    """
    import argparse

    from loam_amend.cli import attach_subparsers

    parser = argparse.ArgumentParser(prog="loam amend test-harness")
    attach_subparsers(parser)
    # Should not raise on a well-formed invocation.
    args = parser.parse_args(["new-memory", "example_slug"])
    assert args.command == "new-memory"
    assert args.slug == "example_slug"


def test_AC_NTU_4_cli_dispatch_routes_to_new_memory_run(tmp_path: Path) -> None:
    """The dispatch() function routes ``new-memory`` to
    new_memory_cmd.run via the shared dispatch path.
    """
    import argparse

    from loam_amend.cli import attach_subparsers, dispatch

    parser = argparse.ArgumentParser(prog="loam amend test-harness")
    attach_subparsers(parser)
    args = parser.parse_args(
        [
            "new-memory",
            "test_dispatch",
            "--memory-dir",
            str(tmp_path / "mem"),
            "--vars-out",
            str(tmp_path / "out.vars.yaml"),
        ]
    )
    rc = dispatch(args)
    assert rc == 0
    assert (tmp_path / "out.vars.yaml").is_file()


# ---------------------------------------------------------------------------
# (c) Integration probe — full new-memory --render → memory file


def test_AC_NTU_4_render_produces_syntactically_valid_memory_file(
    tmp_path: Path,
) -> None:
    """End-to-end: ``loam amend new-memory test_rule --render`` produces
    a memory file at <memory_dir>/feedback_test_rule.md whose
    frontmatter parses + carries the required fields.

    This is the AC's named integration probe.
    """
    memory_dir = tmp_path / "mem"
    rc = new_memory_cmd.run(
        "test_rule",
        name="Test rule — AC.NTU.4 probe",
        description="Demonstrates new-memory orchestration.",
        memory_dir=memory_dir,
        render=True,
        repo_root=tmp_path,
    )
    assert rc == 0

    memory_file = memory_dir / "feedback_test_rule.md"
    assert memory_file.is_file(), f"memory-doc not produced at {memory_file}"

    text = memory_file.read_text(encoding="utf-8")
    # The frontmatter is the SECOND `---` block (the template's own
    # frontmatter is consumed at parse time; the rendered body opens
    # with the memory-doc's own ``---\nname: ...\n---`` block).
    # Parse the frontmatter directly.
    import re

    fm_match = re.match(r"\A---\s*\n(?P<fm>.*?)\n---\s*\n", text, re.DOTALL)
    assert fm_match is not None, (
        f"rendered memory-doc missing frontmatter; got: {text[:200]}"
    )
    fm = yaml.safe_load(fm_match.group("fm"))
    assert isinstance(fm, dict)
    assert fm.get("name") == "Test rule — AC.NTU.4 probe"
    assert fm.get("description") == "Demonstrates new-memory orchestration."
    assert fm.get("type") == "feedback"
    # Body sections present.
    assert "## Why" in text
    assert "## How to apply" in text
    assert "## Composes with" in text


def test_AC_NTU_4_default_path_lands_at_docs_memory(tmp_path: Path) -> None:
    """Without ``--memory-dir`` override, the default destination is
    ``<repo>/docs/memory/feedback_<slug>.md``.
    """
    rc = new_memory_cmd.run(
        "test_default",
        name="X",
        description="Y",
        render=True,
        repo_root=tmp_path,
    )
    assert rc == 0
    expected = tmp_path / "docs" / "memory" / "feedback_test_default.md"
    assert expected.is_file()


def test_AC_NTU_4_invalid_slug_halts_with_exit_2(tmp_path: Path) -> None:
    """Invalid slug (uppercase, hyphen-only-no-underscore allowed?)
    short-circuits at slug validation with exit 2.
    """
    # Hyphens are NOT permitted in memory-doc slugs (snake_case for the
    # feedback_*.md naming); validate enforces this.
    rc = new_memory_cmd.run(
        "Bad-Slug",
        repo_root=tmp_path,
    )
    assert rc == 2


def test_AC_NTU_4_refuse_overwrite_without_force(tmp_path: Path) -> None:
    """Refuse-overwrite on existing vars-file unless --force."""
    memory_dir = tmp_path / "mem"
    memory_dir.mkdir()
    (memory_dir / "feedback_existing.vars.yaml").write_text("preexisting\n")
    rc = new_memory_cmd.run(
        "existing",
        memory_dir=memory_dir,
        repo_root=tmp_path,
    )
    assert rc == 3
    # With --force, succeeds.
    rc2 = new_memory_cmd.run(
        "existing",
        memory_dir=memory_dir,
        force=True,
        repo_root=tmp_path,
    )
    assert rc2 == 0


def test_AC_NTU_4_pre_fill_name_and_description(tmp_path: Path) -> None:
    """``--name`` + ``--description`` flags pre-fill the corresponding
    vars in the scaffolded vars-file (mirrors AC.D-np.2 shape).
    """
    rc = new_memory_cmd.run(
        "prefill_test",
        name="Pre-filled Name",
        description="Pre-filled Description",
        memory_dir=tmp_path / "mem",
        repo_root=tmp_path,
    )
    assert rc == 0
    vars_file = tmp_path / "mem" / "feedback_prefill_test.vars.yaml"
    loaded = yaml.safe_load(vars_file.read_text(encoding="utf-8"))
    assert loaded["NAME"] == "Pre-filled Name"
    assert loaded["DESCRIPTION"] == "Pre-filled Description"
