"""AC.SCT.S — Outcome-altitude smoke: synthetic seal cycle with a
plan-doc + manifest + INTENTIONAL orphan file (so the post-seal
dry-run fails) → seal commit lands, dry-run diagnostic emits non-
zero, §14 backfill commit lands as a separate follow-on commit, the
post-seal HEAD's plan-doc carries the ``### Commit SHAs`` subsection
naming both the amendment commit and the seal commit SHAs.

Per docs/plans/amendment-141-seal-tool-section-14-backfill-decouple.md §4.

outcome-altitude: true — calls the production seal entry-point
(``cli_main(["seal", ...])``) against a no-pre-arranged-state
fixture. The fixture's only pre-arrangement is the orphan file
included in the amendment commit (the trigger for dry-run failure),
which is the empirical condition this amendment is designed to
survive.

This is the load-bearing outcome-altitude probe for amendment #141.
If it fails, the decouple does not deliver its promise — the
operator would still see #138's manual-backfill workflow.
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


def _make_amendment_commit_with_orphan(
    repo: Path, comp: str, orphan_subpath: str, payload: str
) -> str:
    edit_path = repo / "framework" / comp / "src" / "amendment.py"
    edit_path.write_text(f"# {payload}\n", encoding="utf-8")
    orphan_path = repo / orphan_subpath
    orphan_path.parent.mkdir(parents=True, exist_ok=True)
    orphan_path.write_text(f"# orphan: {payload}\n", encoding="utf-8")
    _git(repo, "add", "--", f"framework/{comp}/src/amendment.py", orphan_subpath)
    _git(repo, "commit", "-m", f"feat({comp}): fixture amendment edit + orphan")
    return _git(repo, "rev-parse", "HEAD").stdout.strip()


@pytest.fixture
def sealed_repo(tmp_path: Path) -> Path:
    """Cold-state repo, mirroring the production state at amendment-
    author time. No pre-canned ### Commit SHAs subsection, no manual
    backfill, no operator-edited follow-up — outcome-altitude
    discipline."""
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
# AC.SCT.S — outcome-altitude smoke
# outcome-altitude: true
# ----------------------------------------------------------------------


def test_AC_SCT_S_dry_run_fails_but_backfill_lands_end_to_end(
    sealed_repo, capsys
) -> None:
    """End-to-end smoke: a single ``loam amend seal --plan-doc <p>``
    invocation against a fixture whose amendment commit includes an
    unadmitted-path orphan file produces:

      1. A deterministic seal commit (``chore(seals): ...``) at HEAD~1.
      2. A deterministic §14 backfill follow-up commit
         (``docs(plans): record amendment #N commit SHAs ...``) at HEAD.
      3. The post-seal HEAD's plan-doc on disk (in
         ``docs/plans/sealed/``) carries the ``### Commit SHAs``
         subsection positioned under the ``## §14`` heading.
      4. The dry-run diagnostic emits to stdout/stderr
         (``post-seal-dry-run-failed`` klass).
      5. The seal command's final exit code equals the dry-run's exit
         code (1 for MISSING_ADMISSION).

    NO manual operator intervention. NO manual §14 backfill commit
    needed.

    Pre-fix regression signature: only ONE new commit (the seal
    alone, with no backfill); operator forced to author a manual
    ``docs(plans): record amendment #N commit SHAs ...`` commit by
    hand (the #138 ``7d893b0`` workaround that this amendment
    retires).
    """
    repo = sealed_repo

    # COLD-STATE plan-doc — minimum viable canonical-shape fixture.
    plan_path = repo / "docs" / "plans" / "amendment-983-sct-smoke.md"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(
        textwrap.dedent(
            """
            # Amendment #983 — AC.SCT.S outcome-altitude smoke fixture

            ## 1. Summary

            Cold-state plan-doc used by the AC.SCT.S smoke test.
            The §14 heading uses the canonical convention. The smoke
            verifies the decoupled-backfill end-to-end against a
            fixture whose post-seal dry-run is forced to fail by an
            unadmitted-path orphan file included in the amendment
            commit.

            ## §14 — Method-decision register

            ### D-sct.smoke — placeholder
            placeholder rationale for the smoke fixture.
            """
        ).lstrip(),
        encoding="utf-8",
    )
    _git(repo, "add", "--", str(plan_path.relative_to(repo)))
    _git(repo, "commit", "-q", "-m", "fixture: smoke plan-doc (canonical §14)")

    manifest_path = _write_manifest(
        repo, components=["alpha"], number=983, slug="sct-smoke"
    )
    # Orphan path forces dry-run MISSING_ADMISSION exit 1.
    amendment_sha = _make_amendment_commit_with_orphan(
        repo,
        "alpha",
        orphan_subpath="unadmitted-dir/orphan.txt",
        payload="sct-smoke",
    )

    pre_seal_count = int(
        _git(repo, "rev-list", "--count", "HEAD").stdout.strip()
    )

    # === The smoke: a SINGLE CLI invocation, no manual steps ===
    rc = cli_main(
        ["seal", "--plan-doc", str(plan_path), str(manifest_path)]
    )

    captured = capsys.readouterr()

    # (5) Exit code equals dry-run's exit code (1 for MISSING_ADMISSION).
    assert rc == 1, (
        f"AC.SCT.S violation: seal command's final exit code must equal "
        f"the dry-run's non-zero exit code (1 for MISSING_ADMISSION); "
        f"got rc={rc}. The decouple must preserve exit-code propagation."
    )

    # (1) + (2) — exactly two new commits land despite dry-run failure
    # (the seal commit + the §14 backfill commit). Pre-fix would
    # produce only ONE new commit (seal alone).
    post_seal_count = int(
        _git(repo, "rev-list", "--count", "HEAD").stdout.strip()
    )
    assert post_seal_count == pre_seal_count + 2, (
        f"AC.SCT.S violation: expected exactly 2 new commits (seal + "
        f"§14 backfill) even when post-seal dry-run fails; got "
        f"{post_seal_count - pre_seal_count}. "
        f"Pre-fix regression signature: only 1 new commit (the seal "
        f"alone, no backfill) — this is the #138 manual-backfill "
        f"workflow this amendment retires."
    )

    # HEAD is the §14 backfill follow-up commit.
    head_subject = _git(repo, "log", "-1", "--format=%s").stdout.strip()
    assert (
        head_subject
        == "docs(plans): record amendment #983 commit SHAs in method-decision register"
    ), (
        f"AC.SCT.S violation: HEAD subject must be the deterministic "
        f"backfill commit; got {head_subject!r}"
    )

    # HEAD~1 is the seal commit.
    seal_subject = _git(
        repo, "log", "-1", "--skip=1", "--format=%s"
    ).stdout.strip()
    assert seal_subject.startswith("chore(seals):"), (
        f"AC.SCT.S violation: HEAD~1 must be the seal commit; got "
        f"{seal_subject!r}"
    )
    seal_sha = _git(repo, "rev-parse", "HEAD~1").stdout.strip()

    # (3) — plan-doc carries ### Commit SHAs under ## §14 (post-archive).
    sealed_plan_path = repo / "docs" / "plans" / "sealed" / plan_path.name
    assert sealed_plan_path.exists(), (
        "AC.SCT.S: plan-doc must archive to docs/plans/sealed/ on seal"
    )
    plan_text = sealed_plan_path.read_text(encoding="utf-8")
    s14_idx = plan_text.index("## §14 — Method-decision register")
    shas_idx = plan_text.index("### Commit SHAs")
    assert shas_idx > s14_idx, (
        "AC.SCT.S: ### Commit SHAs subsection must be positioned "
        "under the ## §14 heading (post-archive plan-doc)"
    )
    assert amendment_sha in plan_text, (
        "AC.SCT.S: amendment SHA must appear in the backfill subsection"
    )
    assert seal_sha in plan_text, (
        "AC.SCT.S: seal SHA must appear in the backfill subsection"
    )

    # (4) — dry-run diagnostic emits.
    combined = captured.out + captured.err
    assert "post-seal-dry-run-failed" in combined, (
        f"AC.SCT.S violation: ``post-seal-dry-run-failed`` klass must "
        f"emit in captured output (dry-run diagnostic). Captured "
        f"(truncated to 800 chars):\n{combined[:800]!r}"
    )

    # Working tree clean.
    status = _git(repo, "status", "--porcelain").stdout
    assert status == "", (
        f"AC.SCT.S: working tree must be clean post-seal; got: {status!r}"
    )
