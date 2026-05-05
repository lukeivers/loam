"""AC.PERSONA-PULL.2 — Persona pull-point contract (documentation-only).

Per v0.2.4 Cycle 3 sub-plan-doc §3 AC.PERSONA-PULL.2:

- No new SKILL.md (master plan §6.3 ruling).
- Documentation lives in module docstring + ``--help`` text +
  build-next.md closing line.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from loam_odd_extractor import (
    AugmentedObjectiveSet,
    GapInventory,
    save_recommendation,
    score_candidates,
)
from loam_odd_extractor import build_next as build_next_module


def test_module_docstring_names_persona_pullpoint():
    """The module docstring carries the invocation reference."""
    doc = build_next_module.__doc__ or ""
    assert "build-next" in doc
    assert "operator chooses" in doc.lower() or "informative" in doc.lower()


def test_cli_help_advertises_build_next_flag():
    """`loam odd-extract --help` text mentions --build-next + persona invocation."""
    import argparse
    from loam_odd_extractor.cli import build_odd_extract_subcommand

    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="subcommand")
    build_odd_extract_subcommand(sub)
    help_text = parser.format_help()
    # Find the odd-extract subparser's actions to assert flag presence.
    # argparse's format_help on the parent doesn't always include the
    # subparser's options; inspect the subparser directly.
    odd_action = None
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            odd_action = action.choices["odd-extract"]
            break
    assert odd_action is not None
    odd_help = odd_action.format_help()
    assert "--build-next" in odd_help
    assert "persona" in odd_help.lower() or "user-question-trigger" in odd_help.lower()


def test_build_next_md_closing_line_names_persona_invocation(tmp_path: Path):
    """The rendered markdown closes with the persona-invocation line."""
    fdir = (
        Path(__file__).parent / "fixtures" / "build-next" / "no-survey-context"
    )
    aug_p = yaml.safe_load((fdir / "augmented-objectives.yaml").read_text())
    aug_p.pop("schema_version", None)
    aug = AugmentedObjectiveSet.model_validate(aug_p)
    inv_p = yaml.safe_load((fdir / "gap-inventory.yaml").read_text())
    inv_p.pop("schema_version", None)
    inv = GapInventory.model_validate(inv_p)

    rec = score_candidates(
        gap_inventory=inv,
        augmented_objectives=aug,
        survey_text=None,
        extraction_id=inv.extraction_id,
        audit_path="/tmp/audit-log",
    )
    _, md_p, _ = save_recommendation(rec, tmp_path)
    md = md_p.read_text(encoding="utf-8")
    # Closing line carries the persona-invocation reference.
    assert "Persona invokes via" in md
    assert "loam odd-extract <repo> --build-next" in md
    assert "what should i build next" in md.lower()
    assert "informative" in md.lower()


def test_no_skill_md_added_for_build_next():
    """No skill file should be added at v0.2.4 per master plan §6.3."""
    # Search common SKILL.md locations.
    repo_root = Path(__file__).resolve().parents[4]
    suspicious = list(repo_root.rglob("**/build-next/SKILL.md"))
    suspicious += list(repo_root.rglob("**/build_next/SKILL.md"))
    suspicious += list(repo_root.rglob("**/what-should-i-build*"))
    assert suspicious == [], (
        f"AC.PERSONA-PULL.2 forbids new SKILL.md for build-next at "
        f"v0.2.4 per master plan §6.3. Found: {suspicious}"
    )
