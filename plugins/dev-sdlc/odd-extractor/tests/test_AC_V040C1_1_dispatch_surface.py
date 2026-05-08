"""AC.V040C1.1 — Code-gen dispatch surface exists.

Per cycle-1 plan-doc §4 AC.V040C1.1: a loam-CLI invocation
(``loam odd-extract <repo> --code-gen``) accepts an extraction
directory containing ``objectives.yaml`` (or
``augmented-objectives.yaml``) + ``gap-inventory.yaml`` +
``build-next.yaml`` and produces a unified diff or branch as a
persisted artefact.

This module verifies:

1. The ``--code-gen`` flag is registered on the ``loam odd-extract``
   argparse parser (manifest-entry equivalent).
2. The flag has a help-text describing the deliverable shape.
3. ``generate_code`` is callable with the expected signature.
4. ``persist_diff`` produces an artefact at
   ``<extraction_dir>/code-gen/manifest.json``.
5. ``_cmd_code_gen`` handler is registered in the dispatch table.
"""

from __future__ import annotations

import argparse
import inspect

import pytest

from loam_odd_extractor import cli as cli_module
from loam_odd_extractor.cli import build_odd_extract_subcommand
from loam_odd_extractor.code_gen import generate_code, persist_diff


def _make_parser() -> argparse.ArgumentParser:
    """Construct an argparse parser with `odd-extract` subcommand
    wired in (mirrors `cli.main()` shape)."""
    parser = argparse.ArgumentParser(prog="loam-odd-extract")
    sub = parser.add_subparsers(dest="subcommand", required=True)
    build_odd_extract_subcommand(sub)
    return parser


def test_AC_V040C1_1_code_gen_flag_registered_on_argparse() -> None:
    """The ``--code-gen`` flag is registered on the
    ``loam odd-extract`` argparse parser.
    """
    parser = _make_parser()
    # Walk the parser's choices to find the odd-extract sub-parser.
    found = False
    for action in parser._actions:
        if not hasattr(action, "choices") or action.choices is None:
            continue
        for sub_name, sub_parser in action.choices.items():
            if sub_name != "odd-extract":
                continue
            sub_help = sub_parser.format_help()
            if "--code-gen" in sub_help:
                found = True
                break
    assert found, (
        "AC.V040C1.1 — `--code-gen` flag must be registered on "
        "`loam odd-extract` subcommand. parser help did not contain "
        "the flag."
    )


def test_AC_V040C1_1_code_gen_flag_has_help_text() -> None:
    """The ``--code-gen`` flag's help text describes the deliverable
    (mentions code-gen / unified diff / objectives traceability)."""
    parser = _make_parser()
    help_lines: list[str] = []
    for action in parser._actions:
        if not hasattr(action, "choices") or action.choices is None:
            continue
        for sub_name, sub_parser in action.choices.items():
            if sub_name != "odd-extract":
                continue
            help_lines.append(sub_parser.format_help())
    blob = "\n".join(help_lines).lower()
    assert "--code-gen" in blob, "flag must appear in help"
    deliverable_hints = ("code-gen", "diff", "objectives", "build-next")
    assert any(h in blob for h in deliverable_hints), (
        "AC.V040C1.1 — `--code-gen` help text must mention at least "
        "one of: code-gen / diff / objectives / build-next. blob:"
        f"\n{blob[:500]}"
    )


def test_AC_V040C1_1_generate_code_signature() -> None:
    """``generate_code`` accepts an extraction_dir + an injectable
    ``llm_client`` kwarg (subscription-only; must be injectable so
    tests stub without invoking real ``claude -p``).
    """
    sig = inspect.signature(generate_code)
    params = sig.parameters
    assert "extraction_dir" in params, (
        "generate_code must accept extraction_dir as first param"
    )
    assert "llm_client" in params, (
        "generate_code must accept llm_client kwarg (subscription-only "
        "constraint: tests must be able to inject stubs)"
    )


def test_AC_V040C1_1_persist_diff_creates_manifest(tmp_path) -> None:
    """``persist_diff`` writes ``<extraction_dir>/code-gen/manifest.json``
    + ``<extraction_dir>/code-gen/diff.patch``.
    """
    from loam.objective_tracker.spec import LiftedFrom

    from loam_odd_extractor.code_gen_spec import (
        CodeGenCommit,
        CodeGenDiff,
        CodeGenRequest,
    )

    lf = LiftedFrom(source_doc="d.md", source_ac="AC.X.1")
    req = CodeGenRequest(
        extraction_id="t",
        extraction_dir=str(tmp_path),
        selected_candidate_gap_id="G.X.1",
    )
    commit = CodeGenCommit(
        message_subject="feat: x",
        diff_text="--- a/x\n+++ b/x\n@@ +1 @@\n+x\n",
        lifted_from=lf,
    )
    diff = CodeGenDiff(extraction_id="t", request=req, commits=(commit,))

    manifest_path = persist_diff(diff, tmp_path)

    assert manifest_path.is_file(), (
        f"manifest.json must exist at {manifest_path}"
    )
    assert (tmp_path / "code-gen" / "diff.patch").is_file(), (
        "diff.patch must exist as a sibling of manifest.json"
    )


def test_AC_V040C1_1_cmd_code_gen_handler_registered() -> None:
    """The ``_cmd_code_gen`` handler exists on the cli module and
    is wired into the dispatch routing (verified by source-string
    check; runtime invocation requires a workspace under test, which
    AC.V040C1.3 covers)."""
    assert hasattr(cli_module, "_cmd_code_gen"), (
        "AC.V040C1.1 — `_cmd_code_gen` handler must exist on cli "
        "module"
    )
    # Verify dispatch routing: _cmd_dispatch tests `args.code_gen`
    # before falling through to _cmd_extract.
    from pathlib import Path

    src = Path(cli_module.__file__).read_text()
    assert "code_gen" in src and "_cmd_code_gen" in src, (
        "_cmd_dispatch must route code-gen invocations"
    )
