"""AC.SCT.2 — When the post-seal dry-run exits non-zero, the dry-run
diagnostic STILL emits AND the seal command's return code STILL
reflects the dry-run exit code (non-zero).

Per docs/plans/amendment-141-seal-tool-section-14-backfill-decouple.md §4.

This is the operator-visibility invariant: the decouple changes
step-(h) reachability, NOT step-(g) signal emission. The dry-run
diagnostic still prints to stdout/stderr at the failure point; the
seal command's final return code equals the dry-run's non-zero exit
code (typically 1 for MISSING_ADMISSION).

Pre-fix the dry-run failure returned immediately via the early
``return dry_rc`` at ``seal.py:969``; post-fix the dry-run exit code
is captured in a local ``dry_rc`` and surfaces via the final
``return dry_rc`` at the end of ``_finalize`` after step (h) has
fired. The contract: ``return dry_rc`` is preserved.
"""

from __future__ import annotations

import io
import subprocess
import sys
import textwrap
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import pytest

from loam_amend.cli import main as cli_main


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )


def _make_fake_component(repo: Path, name: str) -> None:
    comp_dir = repo / "framework" / name
    (comp_dir / "tests").mkdir(parents=True, exist_ok=True)
    (comp_dir / "src").mkdir(exist_ok=True)
    (comp_dir / "src" / "__init__.py").write_text("\n", encoding="utf-8")
    (comp_dir / "tests" / "__init__.py").write_text("\n", encoding="utf-8")
    (comp_dir / "tests" / "SEAL_COMMIT").write_text(
        "0000000000000000000000000000000000000000\n", encoding="utf-8"
    )
    seal_test = textwrap.dedent(
        f"""
        allowed_prefixes = (
            "framework/{name}/",
            "docs/plans/",
        )
        allowed_files = (
            "CLAUDE.md",
        )

        def test_seal_diff_ok():
            assert True
        """
    ).lstrip()
    (comp_dir / "tests" / "test_no_sealed_amendments.py").write_text(
        seal_test, encoding="utf-8"
    )
    (comp_dir / "tests" / "test_basic.py").write_text(
        "def test_component_ok():\n    assert True\n", encoding="utf-8"
    )


def _write_manifest(
    repo: Path, *, components: list[str], number: int, slug: str
) -> Path:
    plans_dir = repo / "docs" / "plans"
    plans_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = plans_dir / f"amendment-{number}-{slug}.manifest.yaml"
    baseline = _git(repo, "rev-parse", "HEAD").stdout.strip()
    lines = [
        "schema_version: 1",
        "amendment:",
        f"  number: {number}",
        f"  slug: {slug}",
        f'  title: "fixture amendment {number}"',
        f"baseline: {baseline}",
        f"plan: docs/plans/amendment-{number}-{slug}.md",
        "components:",
    ]
    for c in components:
        lines.append(f"  - name: {c}")
        lines.append(
            f"    seal_test: framework/{c}/tests/test_no_sealed_amendments.py"
        )
        lines.append(f"    sidecar: framework/{c}/tests/SEAL_COMMIT")
    manifest_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    _git(repo, "add", "--", str(manifest_path.relative_to(repo)))
    _git(repo, "commit", "-q", "-m", f"fixture: amendment-{number} manifest")
    return manifest_path


def _make_amendment_commit_with_orphan(
    repo: Path, comp: str, orphan_subpath: str, payload: str
) -> str:
    edit_path = repo / "framework" / comp / "src" / "amendment.py"
    edit_path.write_text(f"# {payload}\n", encoding="utf-8")
    orphan_path = repo / orphan_subpath
    orphan_path.parent.mkdir(parents=True, exist_ok=True)
    orphan_path.write_text(f"# orphan file: {payload}\n", encoding="utf-8")
    _git(repo, "add", "--", f"framework/{comp}/src/amendment.py", orphan_subpath)
    _git(repo, "commit", "-m", f"feat({comp}): fixture amendment edit + orphan")
    return _git(repo, "rev-parse", "HEAD").stdout.strip()


@pytest.fixture
def sealed_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "workspace"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "loam amend test")
    (repo / ".gitignore").write_text("__pycache__/\n*.pyc\n", encoding="utf-8")
    (repo / "CLAUDE.md").write_text("# fixture\n", encoding="utf-8")
    _make_fake_component(repo, "alpha")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "fixture: initial sealed components")
    return repo


# ----------------------------------------------------------------------
# AC.SCT.2 — dry-run failure surfaces via exit code + diagnostic
# ----------------------------------------------------------------------


def test_AC_SCT_2_dry_run_failure_surfaces_via_exit_code_and_diagnostic(
    sealed_repo, capsys
) -> None:
    """Same fixture shape as AC.SCT.1 (unadmitted orphan path forces
    dry-run failure). Asserts:
      1. The seal command's final exit code is non-zero AND equals the
         dry-run's exit code (1 for MISSING_ADMISSION).
      2. The dry-run diagnostic emits — captured stdout/stderr
         contains the ``post-seal-dry-run-failed`` ``klass:`` block
         from ``_emit_diagnostic``.
    """
    repo = sealed_repo
    plan_path = repo / "docs" / "plans" / "amendment-981-sct2.md"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(
        textwrap.dedent(
            """
            # Amendment #981 — AC.SCT.2 fixture

            ## 1. Summary

            Fixture for AC.SCT.2 — preserves dry-run signal emission
            and exit-code propagation under decouple.

            ## §14 — Method-decision register

            ### D-sct2.placeholder
            placeholder rationale.
            """
        ).lstrip(),
        encoding="utf-8",
    )
    _git(repo, "add", "--", str(plan_path.relative_to(repo)))
    _git(repo, "commit", "-q", "-m", "fixture: plan-doc for AC.SCT.2")

    manifest_path = _write_manifest(
        repo, components=["alpha"], number=981, slug="sct2"
    )
    _make_amendment_commit_with_orphan(
        repo,
        "alpha",
        orphan_subpath="unadmitted-dir/orphan.txt",
        payload="sct2",
    )

    rc = cli_main(
        ["seal", "--plan-doc", str(plan_path), str(manifest_path)]
    )

    captured = capsys.readouterr()

    # (1) Exit code: non-zero AND equals the dry-run's exit code.
    # apply.py:113 returns 1 for MISSING_ADMISSION; the seal command
    # must surface that exact value (not 3, not collapsed to a single
    # generic non-zero, not 0).
    assert rc == 1, (
        f"AC.SCT.2 violation: seal command's return code must equal "
        f"the dry-run's exit code (1 for MISSING_ADMISSION); got "
        f"rc={rc}. The decouple must preserve exit-code propagation."
    )

    # (2) Diagnostic must emit. The diagnostic is printed by
    # _emit_diagnostic with the klass tag.
    combined = captured.out + captured.err
    assert "post-seal-dry-run-failed" in combined, (
        f"AC.SCT.2 violation: ``post-seal-dry-run-failed`` klass tag "
        f"must appear in captured output (dry-run diagnostic). "
        f"Captured output (truncated to 800 chars):\n"
        f"{combined[:800]!r}"
    )

    # The dry-run analysis report itself emits MISSING_ADMISSION.
    assert "MISSING_ADMISSION" in combined, (
        f"AC.SCT.2 violation: the dry-run analysis report must emit "
        f"MISSING_ADMISSION for the unadmitted-path orphan file. "
        f"Captured output (truncated):\n{combined[:800]!r}"
    )
