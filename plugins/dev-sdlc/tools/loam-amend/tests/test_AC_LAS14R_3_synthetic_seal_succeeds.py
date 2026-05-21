"""AC.LAS14R.3 — Synthetic seal-cycle of a plan-doc whose §14 heading
is the canonical ``## §14 — Method-decision register`` shape
succeeds the auto-backfill; the ``### Commit SHAs`` subsection
appears under that heading; no ``plan-doc-missing-section-14``
checkpoint fires.

Per docs/plans/amendment-136-loam-amend-seal-section-14-backfill-regex-widening.md §4.

This is the integration-level proof: end-to-end ``loam amend seal
--plan-doc <p>`` against a fixture using the canonical heading
must succeed the full backfill — not just the regex match (which
is unit-tested by AC.LAS14R.1).
"""

from __future__ import annotations

import subprocess
import textwrap
from pathlib import Path

import pytest

from loam_amend.cli import main as cli_main


# ----------------------------------------------------------------------
# Fixture helpers — mirror the shape used by test_seal.py
# ----------------------------------------------------------------------


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )


def _make_fake_component(repo: Path, name: str) -> None:
    """Mirror of test_seal.py::_make_fake_component (post-D.1 layout)."""
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
    repo: Path,
    *,
    components: list[str],
    number: int,
    slug: str,
    seal_description: str | None = None,
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
    if seal_description is not None:
        lines.append(f'seal_description: "{seal_description}"')
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


def _write_plan_doc_with_canonical_section_14(plan_path: Path) -> None:
    """Write a plan-doc whose §14 heading is the canonical shape:
    ``## §14 — Method-decision register`` (§ prefix + em-dash sep).
    """
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(
        textwrap.dedent(
            """
            # Fixture plan doc (canonical heading shape)

            ## 1. Summary

            placeholder.

            ## §14 — Method-decision register

            ### D-las14r.1 — placeholder
            placeholder rationale.
            """
        ).lstrip(),
        encoding="utf-8",
    )


# ----------------------------------------------------------------------
# AC.LAS14R.3 — synthetic seal-cycle with canonical heading
# ----------------------------------------------------------------------


def test_AC_LAS14R_3_canonical_section_14_seal_succeeds(
    sealed_repo,
) -> None:
    """End-to-end ``loam amend seal --plan-doc <p>`` against a fixture
    plan-doc whose §14 heading is the canonical ``## §14 — ...``
    shape MUST succeed — the auto-backfill must locate the heading,
    append the ``### Commit SHAs`` subsection, and produce the
    deterministic follow-up commit. No ``plan-doc-missing-section-14``
    failure checkpoint may fire."""
    repo = sealed_repo
    plan_path = repo / "docs" / "plans" / "amendment-960-canonical-section-14.md"
    _write_plan_doc_with_canonical_section_14(plan_path)
    _git(repo, "add", "--", str(plan_path.relative_to(repo)))
    _git(repo, "commit", "-q", "-m", "fixture: plan-doc with canonical §14")

    manifest_path = _write_manifest(
        repo,
        components=["alpha"],
        number=960,
        slug="canonical-section-14",
        seal_description="canonical heading",
    )
    amendment_sha = _make_amendment_commit(repo, "alpha", payload="las14r3")

    rc = cli_main(
        ["seal", "--plan-doc", str(plan_path), str(manifest_path)]
    )
    assert rc == 0, (
        "AC.LAS14R.3 violation: seal-cycle MUST succeed on canonical "
        "## §14 heading shape; got non-zero exit code"
    )

    # AC.FBMT1.APS.1: plan-doc archives into docs/plans/sealed/ on
    # seal; the §14 backfill targets the post-archive location.
    sealed_plan_path = repo / "docs" / "plans" / "sealed" / plan_path.name
    assert sealed_plan_path.exists(), "plan-doc must archive to sealed/"

    plan_text = sealed_plan_path.read_text(encoding="utf-8")

    # The canonical heading must be preserved verbatim
    assert "## §14 — Method-decision register" in plan_text, (
        "AC.LAS14R.3: canonical heading must be preserved through the "
        "backfill rewrite"
    )

    # The Commit SHAs subsection must be appended
    assert "### Commit SHAs" in plan_text, (
        "AC.LAS14R.3: backfill must append ### Commit SHAs subsection"
    )
    assert amendment_sha in plan_text, (
        "AC.LAS14R.3: amendment SHA must appear in backfilled subsection"
    )

    # The Commit SHAs subsection MUST be positioned under §14 — not
    # at the top of the file or in some other section.
    s14_idx = plan_text.index("## §14")
    shas_idx = plan_text.index("### Commit SHAs")
    assert shas_idx > s14_idx, (
        "AC.LAS14R.3: ### Commit SHAs subsection must appear AFTER "
        "the ## §14 heading (positionally inside the section)"
    )

    # The follow-up commit must exist with the deterministic subject
    head_subject = _git(repo, "log", "-1", "--format=%s").stdout.strip()
    assert (
        head_subject
        == "docs(plans): record amendment #960 commit SHAs in method-decision register"
    ), (
        f"AC.LAS14R.3: follow-up commit subject mismatch: {head_subject!r}"
    )

    # Working tree clean
    status = _git(repo, "status", "--porcelain").stdout
    assert status == "", "working tree must be clean post-seal"
