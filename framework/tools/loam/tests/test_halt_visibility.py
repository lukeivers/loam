"""Regression test for AC.PA-hv (halt visibility on stdout).

Halt diagnostics emitted by ``loam amend seal`` and ``loam amend
new-plan`` must reach stdout so they remain visible in contexts
where stderr is dropped (e.g. some Bash-tool eval-wrapper
invocations). The ``HALT:`` prefix is the scannable contract;
the line MUST appear on stdout for those halt sites.

Note: ``loam amend template render`` is exempt by AC.D-tpl.5 — the
template-render halt path is forbidden from contaminating
stdout because callers redirect stdout with ``>`` to capture
rendered template output. Template halts emit to stderr only.

This module exercises:

- ``seal._emit_diagnostic`` — dirty-working-tree halt (rc=3)
- ``new_plan._emit_diagnostic`` — invalid-slug halt (rc=2)

Per ``docs/rebuild/plans/pos-amend-halt-visibility.md`` AC.PA-hv.5.
"""

from __future__ import annotations

import io
import subprocess
import sys
import textwrap
from contextlib import redirect_stdout
from pathlib import Path

from loam_cli.amend.cli import main as cli_main


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )


def _make_minimal_repo_with_dirty_tree(tmp_path: Path) -> Path:
    """Build a tiny git repo with a manifest, a sealed component, an
    amendment commit, and an unrelated dirty file in the tree.
    """
    repo = tmp_path / "workspace"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "loam amend halt test")
    (repo / ".gitignore").write_text("__pycache__/\n*.pyc\n", encoding="utf-8")
    (repo / "CLAUDE.md").write_text("# fixture\n", encoding="utf-8")

    # Fixture sealed component "alpha".
    comp_dir = repo / "alpha"
    (comp_dir / "tests").mkdir(parents=True, exist_ok=True)
    (comp_dir / "src").mkdir(exist_ok=True)
    (comp_dir / "src" / "__init__.py").write_text("\n", encoding="utf-8")
    (comp_dir / "tests" / "__init__.py").write_text("\n", encoding="utf-8")
    (comp_dir / "tests" / "SEAL_COMMIT").write_text(
        "0000000000000000000000000000000000000000\n", encoding="utf-8"
    )
    (comp_dir / "tests" / "test_no_sealed_amendments.py").write_text(
        textwrap.dedent(
            """
            allowed_prefixes = (
                "alpha/",
                "docs/rebuild/plans/",
            )
            allowed_files = (
                "CLAUDE.md",
            )

            def test_seal_diff_ok():
                assert True
            """
        ).lstrip(),
        encoding="utf-8",
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "fixture: initial")

    # Manifest pinned to current HEAD as baseline.
    plans_dir = repo / "docs" / "rebuild" / "plans"
    plans_dir.mkdir(parents=True, exist_ok=True)
    head_sha = _git(repo, "rev-parse", "HEAD").stdout.strip()
    manifest_path = plans_dir / "amendment-999-halt-vis.manifest.yaml"
    manifest_path.write_text(
        textwrap.dedent(
            f"""
            schema_version: 1
            amendment:
              number: 999
              slug: halt-vis
              title: "fixture amendment 999"
            baseline: {head_sha}
            plan: docs/rebuild/plans/amendment-999-halt-vis.md
            components:
              - name: alpha
                seal_test: alpha/tests/test_no_sealed_amendments.py
                sidecar: alpha/tests/SEAL_COMMIT
            """
        ).lstrip(),
        encoding="utf-8",
    )
    _git(repo, "add", "--", "docs/rebuild/plans/amendment-999-halt-vis.manifest.yaml")
    _git(repo, "commit", "-q", "-m", "fixture: manifest")

    # Land a fake amendment commit under alpha so apply --dry-run
    # post-seal would have something to validate against.
    (comp_dir / "src" / "amendment.py").write_text("# edit\n", encoding="utf-8")
    _git(repo, "add", "--", "alpha/src/amendment.py")
    _git(repo, "commit", "-q", "-m", "feat(alpha): fixture edit")

    # Inject an unrelated dirty path — this is what trips the
    # dirty-working-tree halt.
    (repo / "scratch_unrelated.txt").write_text("dirt\n", encoding="utf-8")
    return repo


def test_AC_PA_hv_seal_dirty_tree_halt_visible_on_stdout(
    tmp_path, monkeypatch, capsys
) -> None:
    """``loam amend seal`` with a dirty tree must emit a
    ``HALT: dirty-working-tree`` line on stdout (and exit non-zero).

    Captures stdout via pytest's capsys; intentionally does NOT
    inspect stderr — the contract is "stdout is sufficient."
    """
    repo = _make_minimal_repo_with_dirty_tree(tmp_path)
    monkeypatch.chdir(repo)
    rc = cli_main([
        "seal",
        str(
            repo
            / "docs"
            / "rebuild"
            / "plans"
            / "amendment-999-halt-vis.manifest.yaml"
        ),
    ])
    captured = capsys.readouterr()
    assert rc != 0, f"expected non-zero rc on dirty-tree halt, got {rc}"
    assert "HALT:" in captured.out, (
        "halt prefix must appear on stdout; "
        f"stdout={captured.out!r} stderr={captured.err!r}"
    )
    assert "dirty-working-tree" in captured.out, (
        "halt class must appear on stdout; "
        f"stdout={captured.out!r}"
    )


def test_AC_PA_hv_new_plan_invalid_slug_halt_visible_on_stdout(
    capsys,
) -> None:
    """``loam amend new-plan`` with an invalid slug must emit a
    ``HALT: invalid-slug`` line on stdout."""
    rc = cli_main(["new-plan", "Bad-Slug-With-Caps"])
    captured = capsys.readouterr()
    assert rc == 2, f"expected rc=2 on invalid slug, got {rc}"
    assert "HALT:" in captured.out, (
        f"halt prefix must appear on stdout; stdout={captured.out!r}"
    )
    assert "invalid-slug" in captured.out, (
        f"halt class must appear on stdout; stdout={captured.out!r}"
    )


def test_AC_PA_hv_template_halt_remains_stderr_only(capsys) -> None:
    """``loam amend template render`` halt path is exempt from the
    stdout-HALT contract (AC.D-tpl.5 forbids stdout contamination
    because callers pipe rendered output via ``>``). Halt class
    must still appear on stderr; stdout must be empty.

    This is a regression-guard: a future "make all halts stdout-
    visible" sweep would silently violate AC.D-tpl.5. The exemption
    is documented in template._emit_diagnostic's docstring."""
    rc = cli_main([
        "template",
        "render",
        "plan/dev-discipline",
    ])
    captured = capsys.readouterr()
    assert rc == 2, f"expected rc=2 on missing-required-variable, got {rc}"
    assert captured.out == "", (
        "AC.D-tpl.5 — template-render halt must NOT touch stdout; "
        f"got stdout={captured.out!r}"
    )
    assert "missing-required-variable" in captured.err, (
        f"halt class must appear on stderr; stderr={captured.err!r}"
    )
