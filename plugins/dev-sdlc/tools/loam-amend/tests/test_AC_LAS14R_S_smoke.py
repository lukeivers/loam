"""AC.LAS14R.S — Outcome-altitude smoke: end-to-end
``loam amend seal --plan-doc <p>`` against a fixture plan-doc using
the canonical ``## §14 — Method-decision register`` heading
produces a clean seal commit AND a ``### Commit SHAs`` follow-up
commit, both deterministic, with NO manual operator intervention.

Per docs/plans/amendment-136-loam-amend-seal-section-14-backfill-regex-widening.md §4.

This is the outcome-altitude AC for this amendment (per
feedback_test_outcome_altitude_required). The test invokes the
production CLI entry-point against a no-pre-arranged-state fixture
and verifies the WHOLE-CYCLE outcome — not just any single internal
step. The fixture is built minimally; no pre-canned ### Commit SHAs
subsection exists, no manual operator follow-up commits, no manual
edits between seal-invocation and assertion.

If the regex widening is incorrect, this smoke fails — the seal-step
would either (a) abort with ``plan-doc-missing-section-14`` (the
production failure observed in amendments #128–#134) OR (b) succeed
the seal but leave the auto-backfill silently un-run (which would
fail the follow-up commit assertion).
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
    """Cold-state repo: no pre-canned plan-doc content, no manual
    backfill, no operator-edited follow-up. Mirrors the production
    state at amendment-author time."""
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
# AC.LAS14R.S — outcome-altitude smoke
# outcome-altitude: true
# ----------------------------------------------------------------------


def test_AC_LAS14R_S_canonical_heading_end_to_end_no_manual_intervention(
    sealed_repo,
) -> None:
    """End-to-end smoke: a fixture plan-doc whose §14 heading is the
    canonical ``## §14 — Method-decision register`` shape feeds into
    a single ``loam amend seal --plan-doc <p>`` invocation, and the
    invocation produces:

      1. A deterministic seal commit (``chore(seals): ...``).
      2. A deterministic backfill follow-up commit
         (``docs(plans): record amendment #N commit SHAs ...``).
      3. The plan-doc carries the ``### Commit SHAs`` subsection
         positioned under the ``## §14`` heading.
      4. The working tree is clean.

    NO manual operator intervention. NO ``plan-doc-missing-section-14``
    checkpoint fires. This is the bar the production seal-flow MUST
    meet on every cycle that uses the canonical heading shape.
    """
    repo = sealed_repo

    # COLD-STATE plan-doc — minimum viable canonical-shape fixture.
    # No ### Commit SHAs subsection (the backfill creates it).
    plan_path = repo / "docs" / "plans" / "amendment-970-smoke.md"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(
        textwrap.dedent(
            """
            # Amendment #970 — outcome-altitude smoke fixture

            ## 1. Summary

            Cold-state plan-doc used by the AC.LAS14R.S smoke test.
            The §14 heading uses the canonical convention (§ prefix +
            em-dash separator). The smoke test verifies that
            ``loam amend seal --plan-doc <this-file>`` succeeds
            end-to-end with no manual operator intervention.

            ## §14 — Method-decision register

            ### D-las14r.smoke — placeholder
            placeholder rationale for the smoke fixture.
            """
        ).lstrip(),
        encoding="utf-8",
    )
    _git(repo, "add", "--", str(plan_path.relative_to(repo)))
    _git(repo, "commit", "-q", "-m", "fixture: smoke plan-doc (canonical §14)")

    manifest_path = _write_manifest(
        repo,
        components=["alpha"],
        number=970,
        slug="smoke",
    )
    amendment_sha = _make_amendment_commit(repo, "alpha", payload="las14rS")

    # Snapshot commit-count pre-seal so we can verify exactly two
    # new commits land (the seal commit + the follow-up backfill).
    pre_seal_count = int(
        _git(repo, "rev-list", "--count", "HEAD").stdout.strip()
    )

    # === The smoke: a SINGLE CLI invocation, no manual steps ===
    rc = cli_main(
        ["seal", "--plan-doc", str(plan_path), str(manifest_path)]
    )
    assert rc == 0, (
        "AC.LAS14R.S violation: end-to-end seal MUST succeed on a "
        "fixture plan-doc using the canonical ## §14 heading shape. "
        f"Got non-zero exit code {rc}."
    )

    # (1) + (2) — exactly two new commits: seal + backfill
    post_seal_count = int(
        _git(repo, "rev-list", "--count", "HEAD").stdout.strip()
    )
    assert post_seal_count == pre_seal_count + 2, (
        f"AC.LAS14R.S: expected exactly 2 new commits (seal + backfill); "
        f"got {post_seal_count - pre_seal_count}. If only 1 commit landed, "
        f"the §14 auto-backfill failed silently — the production "
        f"regression this amendment fixes."
    )

    # HEAD is the backfill follow-up commit
    head_subject = _git(repo, "log", "-1", "--format=%s").stdout.strip()
    assert (
        head_subject
        == "docs(plans): record amendment #970 commit SHAs in method-decision register"
    ), (
        f"AC.LAS14R.S: HEAD subject must be the deterministic backfill "
        f"commit; got {head_subject!r}"
    )

    # HEAD~1 is the seal commit
    seal_subject = _git(repo, "log", "-1", "--skip=1", "--format=%s").stdout.strip()
    assert seal_subject.startswith("chore(seals):"), (
        f"AC.LAS14R.S: HEAD~1 must be the seal commit; got {seal_subject!r}"
    )

    # (3) — plan-doc carries ### Commit SHAs under ## §14
    # (post-archive location per amendment #134 T1.4)
    sealed_plan_path = repo / "docs" / "plans" / "sealed" / plan_path.name
    assert sealed_plan_path.exists(), (
        "AC.LAS14R.S: plan-doc must archive to docs/plans/sealed/ on seal"
    )
    plan_text = sealed_plan_path.read_text(encoding="utf-8")
    s14_idx = plan_text.index("## §14 — Method-decision register")
    shas_idx = plan_text.index("### Commit SHAs")
    assert shas_idx > s14_idx, (
        "AC.LAS14R.S: ### Commit SHAs subsection must be positioned "
        "under the ## §14 heading (post-archive plan-doc)"
    )
    assert amendment_sha in plan_text, (
        "AC.LAS14R.S: amendment SHA must appear in the backfill subsection"
    )

    # (4) working tree clean
    status = _git(repo, "status", "--porcelain").stdout
    assert status == "", (
        f"AC.LAS14R.S: working tree must be clean post-seal; got: {status!r}"
    )
