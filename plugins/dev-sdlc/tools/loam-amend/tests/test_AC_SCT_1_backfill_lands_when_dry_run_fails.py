"""AC.SCT.1 — When ``--plan-doc <path>`` is supplied AND the seal
commit lands AND ``loam amend apply --dry-run`` exits non-zero, the
§14 SHA-backfill commit STILL lands as a follow-on commit.

Per docs/plans/amendment-141-seal-tool-section-14-backfill-decouple.md §4.

Pre-fix (canonical at `b46162f`): `_finalize` step (g) at
``seal.py:947-969`` early-returned on dry-run non-zero exit,
blocking step (h) §14 backfill (``seal.py:971-1086``) from firing.
Empirically: amendment #138's orphan-file dry-run failure forced
the operator to author manual backfill commit ``7d893b0``, defeating
amendment #136's no-manual-fallback promise.

Post-fix: the §14 backfill runs unconditionally on plan-doc
presence after a seal commit lands. The dry-run still emits its
diagnostic + drives the final exit code (AC.SCT.2); only step-(h)
reachability changes.

This test forces the dry-run to fail by including an unadmitted-path
file in the amendment commit (a path outside the component's
``allowed_prefixes`` and outside the manifest's ``universal_paths``).
That triggers ``MISSING_ADMISSION`` at dry-run analysis time, which
``apply --dry-run`` reports as exit code 1.
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
    """Mirror of test_AC_LAS14R_3::_make_fake_component."""
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
    """Amendment commit including the legitimate component edit + an
    unadmitted-path 'orphan' file. The orphan is at a path NOT covered
    by any of the component's ``allowed_prefixes`` / ``allowed_files``
    or the manifest's ``universal_paths`` — guarantees dry-run reports
    MISSING_ADMISSION + exits non-zero."""
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
# AC.SCT.1 — backfill commit lands even when post-seal dry-run fails
# ----------------------------------------------------------------------


def test_AC_SCT_1_backfill_lands_when_post_seal_dry_run_fails(
    sealed_repo,
) -> None:
    """End-to-end: amendment commit includes an unadmitted-path file
    (forces post-seal dry-run to exit non-zero); seal command runs;
    seal commit lands; the §14 SHA-backfill commit STILL lands at HEAD
    with the canonical ``docs(plans): record amendment #N commit SHAs
    in method-decision register`` subject."""
    repo = sealed_repo
    plan_path = repo / "docs" / "plans" / "amendment-980-sct1.md"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(
        textwrap.dedent(
            """
            # Amendment #980 — AC.SCT.1 fixture

            ## 1. Summary

            Fixture for AC.SCT.1 — decouples §14 backfill from
            post-seal dry-run failure.

            ## §14 — Method-decision register

            ### D-sct1.placeholder
            placeholder rationale.
            """
        ).lstrip(),
        encoding="utf-8",
    )
    _git(repo, "add", "--", str(plan_path.relative_to(repo)))
    _git(repo, "commit", "-q", "-m", "fixture: plan-doc for AC.SCT.1")

    manifest_path = _write_manifest(
        repo, components=["alpha"], number=980, slug="sct1"
    )
    # Orphan path: unadmitted top-level dir; dry-run will report
    # MISSING_ADMISSION on this path and exit 1.
    amendment_sha = _make_amendment_commit_with_orphan(
        repo,
        "alpha",
        orphan_subpath="unadmitted-dir/orphan.txt",
        payload="sct1",
    )

    pre_seal_count = int(
        _git(repo, "rev-list", "--count", "HEAD").stdout.strip()
    )

    # Single CLI invocation.
    rc = cli_main(
        ["seal", "--plan-doc", str(plan_path), str(manifest_path)]
    )

    # Per AC.SCT.2 (verified in its own test): rc equals the dry-run
    # non-zero exit code. Here we assert rc != 0 to confirm dry-run
    # failed, but the EXACT exit-code-equality check lives in AC.SCT.2.
    assert rc != 0, (
        "AC.SCT.1 fixture precondition: dry-run was expected to fail "
        f"(unadmitted orphan path), but seal command exited 0"
    )

    # AC.SCT.1: TWO new commits landed despite dry-run failure —
    # the seal commit AND the §14 backfill commit.
    post_seal_count = int(
        _git(repo, "rev-list", "--count", "HEAD").stdout.strip()
    )
    assert post_seal_count == pre_seal_count + 2, (
        f"AC.SCT.1 violation: expected exactly 2 new commits (seal + "
        f"§14 backfill) even with dry-run failure; got "
        f"{post_seal_count - pre_seal_count} new commits. "
        f"Pre-fix regression signature: only 1 new commit (the seal "
        f"alone, no backfill)."
    )

    # HEAD is the backfill follow-up commit.
    head_subject = _git(repo, "log", "-1", "--format=%s").stdout.strip()
    assert (
        head_subject
        == "docs(plans): record amendment #980 commit SHAs in method-decision register"
    ), (
        f"AC.SCT.1 violation: HEAD subject must match the canonical "
        f"backfill commit shape; got {head_subject!r}"
    )

    # HEAD~1 is the seal commit.
    seal_subject = _git(repo, "log", "-1", "--skip=1", "--format=%s").stdout.strip()
    assert seal_subject.startswith("chore(seals):"), (
        f"AC.SCT.1: HEAD~1 must be the seal commit; got {seal_subject!r}"
    )

    # Plan-doc on disk (post-archive) carries the ### Commit SHAs
    # subsection with the amendment SHA.
    sealed_plan_path = repo / "docs" / "plans" / "sealed" / plan_path.name
    assert sealed_plan_path.exists(), (
        "AC.SCT.1: plan-doc must archive to docs/plans/sealed/ on seal"
    )
    plan_text = sealed_plan_path.read_text(encoding="utf-8")
    assert "### Commit SHAs" in plan_text, (
        "AC.SCT.1: backfill must append ### Commit SHAs subsection"
    )
    assert amendment_sha in plan_text, (
        "AC.SCT.1: amendment SHA must appear in backfill subsection"
    )
