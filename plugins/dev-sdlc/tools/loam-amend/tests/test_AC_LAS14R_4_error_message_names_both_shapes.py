"""AC.LAS14R.4 — Failure-message text (when section-14 IS genuinely
missing) names BOTH accepted shapes (``## 14.`` AND ``## §14``).

Per docs/plans/amendment-136-loam-amend-seal-section-14-backfill-regex-widening.md §4.

Before this amendment the diagnostic said only ``"no '## 14.' heading"``,
which would mislead operators who used the canonical ``## §14`` shape
into thinking they used the wrong section number. The widened
diagnostic must name BOTH shapes so a recipient diagnosing a real
missing-section-14 condition has the correct mental model.
"""

from __future__ import annotations

import subprocess
import textwrap
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


def _make_amendment_commit(repo: Path, comp: str, payload: str) -> str:
    edit_path = repo / "framework" / comp / "src" / "amendment.py"
    edit_path.write_text(f"# {payload}\n", encoding="utf-8")
    _git(repo, "add", "--", f"framework/{comp}/src/amendment.py")
    _git(repo, "commit", "-m", f"feat({comp}): fixture amendment edit")
    return _git(repo, "rev-parse", "HEAD").stdout.strip()


@pytest.fixture
def sealed_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "workspace"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "loam amend test")
    (repo / ".gitignore").write_text(
        "__pycache__/\n*.pyc\n", encoding="utf-8"
    )
    (repo / "CLAUDE.md").write_text("# fixture\n", encoding="utf-8")
    _make_fake_component(repo, "alpha")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "fixture: initial sealed components")
    return repo


# ----------------------------------------------------------------------
# AC.LAS14R.4 — error message names BOTH shapes
# ----------------------------------------------------------------------


def test_AC_LAS14R_4_missing_section_14_error_names_both_shapes(
    sealed_repo, capsys
) -> None:
    """When a plan-doc has NEITHER ``## 14.`` NOR ``## §14`` (the
    section is genuinely missing), the failure-message text MUST
    name BOTH accepted shapes so the operator's mental model is
    correct."""
    repo = sealed_repo
    plan_path = (
        repo / "docs" / "plans" / "amendment-961-no-section-14.md"
    )
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    # Plan-doc with NO §14 (neither canonical nor legacy form)
    plan_path.write_text(
        "# Fixture plan doc — no §14\n\n## 1. Summary\n\nbody.\n",
        encoding="utf-8",
    )
    _git(repo, "add", "--", str(plan_path.relative_to(repo)))
    _git(repo, "commit", "-q", "-m", "fixture: plan-doc with no §14")

    manifest_path = _write_manifest(
        repo, components=["alpha"], number=961, slug="no-section-14"
    )
    _make_amendment_commit(repo, "alpha", payload="las14r4")

    rc = cli_main(
        ["seal", "--plan-doc", str(plan_path), str(manifest_path)]
    )
    assert rc != 0, "seal MUST fail when section-14 is genuinely missing"

    captured = capsys.readouterr()
    combined = captured.out + captured.err

    # The diagnostic must name BOTH the legacy and canonical shapes
    assert "## 14." in combined, (
        "AC.LAS14R.4: failure message MUST name the legacy '## 14.' "
        "shape so operators using the legacy form recognize the fault"
    )
    assert "## §14" in combined, (
        "AC.LAS14R.4: failure message MUST name the canonical "
        "'## §14' shape so operators using the canonical form "
        "recognize the fault (this is the regression the widening "
        "diagnostic prevents)"
    )
    # The structured klass token must still appear (preserved for
    # downstream tooling that greps for the failure category).
    assert "plan-doc-missing-section-14" in combined, (
        "AC.LAS14R.4: structured klass token must be preserved "
        "(downstream diagnostic consumers depend on this token)"
    )
