"""AC.V025-C6.3 — Default `--workspace-root` resolves to the target
`<repo>` positional arg, not to `Path.cwd()`.

Per v0.2.5 corrective C6 (HARD-smoke F-DESIGN-3): pre-C6, running
`loam odd-extract /tmp/some-repo` from any CWD wrote artefacts to
`<cwd>/.loam/extractions/...`. When CWD was a loam tree (pos-v2),
this polluted the loam tree with another repo's extraction state.

Post-C6 the default is the resolved target `<repo>` positional arg;
artefacts land at `<repo>/.loam/extractions/<repo-id>/`. Existing
tests that pass `--workspace-root` explicitly remain unchanged in
behaviour (the explicit-arg path is preserved).

Two ACs verified here:

  1. Default-resolution unit test: invoke CLI without
     `--workspace-root` from a CWD different from `<repo>`; assert
     extraction lands under `<repo>/.loam/`, NOT `<cwd>/.loam/`.
  2. Help-text assertion: `--workspace-root` help text describes the
     new default ("default: target <repo> positional arg").
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from loam_odd_extractor.cli import (
    _resolve_workspace_root,
    build_odd_extract_subcommand,
    main as cli_main,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="loam-test")
    sub = parser.add_subparsers(dest="subcommand", required=True)
    build_odd_extract_subcommand(sub)
    return parser


def test_AC_V025_C6_3_resolve_helper_defaults_to_repo_path(
    tmp_path: Path,
) -> None:
    """`_resolve_workspace_root(None, repo_path)` returns the resolved
    repo_path (not cwd)."""
    repo = tmp_path / "target-repo"
    repo.mkdir()

    out = _resolve_workspace_root(None, repo)
    assert out == repo.expanduser().resolve(), (
        f"with arg=None, helper must default to repo_path; got {out}"
    )


def test_AC_V025_C6_3_resolve_helper_explicit_arg_wins(
    tmp_path: Path,
) -> None:
    """Explicit `--workspace-root` arg still wins over the repo
    default."""
    repo = tmp_path / "target-repo"
    repo.mkdir()
    explicit = tmp_path / "explicit-ws"
    explicit.mkdir()

    out = _resolve_workspace_root(explicit, repo)
    assert out == explicit.expanduser().resolve(), (
        f"with explicit arg, helper must use the arg, not repo_path; "
        f"got {out}"
    )


def test_AC_V025_C6_3_cli_default_lands_artefacts_under_repo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """End-to-end: invoke CLI without `--workspace-root` from a CWD
    different from `<repo>`; assert extraction lands under
    `<repo>/.loam/extractions/`, NOT `<cwd>/.loam/extractions/`.

    Uses dry-run (no --live) so no LLM is invoked; the four-stage
    workflow runs against a tiny synthesized fixture.
    """
    repo = tmp_path / "target-repo"
    repo.mkdir()
    (repo / "README.md").write_text("# target\n", encoding="utf-8")
    (repo / "package.json").write_text(
        '{"name":"target","version":"0.0.1"}\n', encoding="utf-8"
    )

    different_cwd = tmp_path / "different-cwd"
    different_cwd.mkdir()
    monkeypatch.chdir(different_cwd)

    rc = cli_main([str(repo)])
    assert rc == 0, f"CLI must exit 0 in dry-run; got rc={rc}"

    # Assert artefacts land under <repo>/.loam/, not <cwd>/.loam/.
    repo_loam = repo / ".loam" / "extractions"
    cwd_loam = different_cwd / ".loam" / "extractions"
    assert repo_loam.exists(), (
        f"extraction artefacts must land under <repo>/.loam/extractions/ "
        f"(C6.3 default-shift); not present at {repo_loam}"
    )
    assert not cwd_loam.exists(), (
        f"extraction artefacts must NOT land under <cwd>/.loam/extractions/ "
        f"(pre-C6 cwd-default behavior must be gone); present at "
        f"{cwd_loam}"
    )


def test_AC_V025_C6_3_help_text_describes_new_default() -> None:
    """`--workspace-root` argparse help text describes the new default
    (target `<repo>` positional)."""
    parser = _build_parser()
    # Get the odd-extract subparser.
    sub_actions = [
        a
        for a in parser._actions
        if isinstance(a, argparse._SubParsersAction)
    ]
    odd_extract_parser = sub_actions[0].choices["odd-extract"]
    help_text = odd_extract_parser.format_help()
    assert "target <repo>" in help_text, (
        f"--workspace-root help text must describe the new default "
        f"(target <repo> positional); got: {help_text!r}"
    )
