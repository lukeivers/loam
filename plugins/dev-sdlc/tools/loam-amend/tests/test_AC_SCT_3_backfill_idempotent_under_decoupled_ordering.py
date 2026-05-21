"""AC.SCT.3 — The §14 backfill is idempotent across the new
decoupled ordering: re-invoking the seal step (or running the
backfill alone) against a plan-doc that already carries the
``### Commit SHAs`` subsection produces NO additional commit
(no double-emit, no duplicate subsection).

Per docs/plans/amendment-141-seal-tool-section-14-backfill-decouple.md §4.

The pre-existing idempotence path lives at ``seal.py:1015-1024`` —
``git diff --cached --quiet`` after ``git add`` of the plan-doc
detects "nothing staged" (the helper found the subsection already
current) and SKIPS the commit step. Amendment #141's decouple keeps
that idempotence path intact: the ``backfill_committed`` flag
captures whether anything was actually staged; the commit step
wraps under ``if backfill_committed:``. This test guards that
invariant under the new ordering.
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
    (repo / ".gitignore").write_text("__pycache__/\n*.pyc\n", encoding="utf-8")
    (repo / "CLAUDE.md").write_text("# fixture\n", encoding="utf-8")
    _make_fake_component(repo, "alpha")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "fixture: initial sealed components")
    return repo


# ----------------------------------------------------------------------
# AC.SCT.3 — backfill idempotence under decoupled ordering
# ----------------------------------------------------------------------


def test_AC_SCT_3_backfill_helper_idempotent_no_double_emit(
    sealed_repo,
) -> None:
    """First seal invocation lands the seal commit + the §14 backfill
    commit (the happy-path case with clean dry-run). The second
    invocation of ``_backfill_plan_doc_shas`` against the already-
    populated plan-doc must report ``§14 SHAs already current.`` and
    NOT emit any additional commit.

    This test exercises the helper directly (which is what step (h)
    invokes) to isolate the idempotence path from any seal-cycle
    state. The seal-cycle re-invocation case is implicitly covered
    by the existing ``test_AC_LAS14R_S_smoke`` family + the seal-time
    dogfood at amendment #141's own seal.
    """
    repo = sealed_repo
    plan_path = repo / "docs" / "plans" / "amendment-982-sct3.md"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(
        textwrap.dedent(
            """
            # Amendment #982 — AC.SCT.3 fixture

            ## 1. Summary

            Fixture for AC.SCT.3 — preserves backfill idempotence
            under decoupled ordering.

            ## §14 — Method-decision register

            ### D-sct3.placeholder
            placeholder rationale.
            """
        ).lstrip(),
        encoding="utf-8",
    )
    _git(repo, "add", "--", str(plan_path.relative_to(repo)))
    _git(repo, "commit", "-q", "-m", "fixture: plan-doc for AC.SCT.3")

    manifest_path = _write_manifest(
        repo, components=["alpha"], number=982, slug="sct3"
    )
    _make_amendment_commit(repo, "alpha", payload="sct3")

    pre_seal_count = int(
        _git(repo, "rev-list", "--count", "HEAD").stdout.strip()
    )

    # First seal: clean happy path. Dry-run passes, §14 backfill fires.
    rc1 = cli_main(
        ["seal", "--plan-doc", str(plan_path), str(manifest_path)]
    )
    assert rc1 == 0, (
        f"AC.SCT.3 fixture precondition: first seal must succeed; "
        f"got rc={rc1}"
    )

    after_first_count = int(
        _git(repo, "rev-list", "--count", "HEAD").stdout.strip()
    )
    assert after_first_count == pre_seal_count + 2, (
        f"AC.SCT.3 fixture precondition: first seal must produce exactly "
        f"2 commits (seal + backfill); got {after_first_count - pre_seal_count}"
    )

    # Now invoke the backfill helper directly against the post-archive
    # plan-doc. It must be a no-op (helper finds §14 subsection
    # already current; no staged changes).
    from loam_amend.commands.seal import (
        _backfill_plan_doc_shas,
        _head_sha,
        _commit_subject,
    )

    sealed_plan_path = repo / "docs" / "plans" / "sealed" / plan_path.name
    assert sealed_plan_path.exists(), (
        "AC.SCT.3 precondition: plan-doc must be archived under sealed/"
    )

    # Capture amendment + seal SHAs from the recorded register (they
    # are at HEAD~1 and HEAD~2 — backfill is HEAD, seal is HEAD~1).
    seal_sha = _git(repo, "rev-parse", "HEAD~1").stdout.strip()
    seal_subject_text = _commit_subject(repo, seal_sha)
    amendment_sha = _git(repo, "rev-parse", "HEAD~2").stdout.strip()
    amendment_subject_text = _commit_subject(repo, amendment_sha)

    # Re-invoke the helper against the already-populated plan-doc.
    # If the rewrite is idempotent, the file on disk is unchanged and
    # ``git diff --cached --quiet`` would report nothing-staged.
    ck = _backfill_plan_doc_shas(
        plan_doc=sealed_plan_path,
        amendment_sha=amendment_sha,
        amendment_subject=amendment_subject_text,
        seal_sha=seal_sha,
        seal_subject=seal_subject_text,
    )
    assert ck is None, (
        f"AC.SCT.3 violation: backfill helper must succeed on idempotent "
        f"re-invocation; got failure checkpoint {ck}"
    )

    # No new file changes after the idempotent re-invocation.
    status = _git(repo, "status", "--porcelain").stdout
    assert status == "", (
        f"AC.SCT.3 violation: idempotent re-invocation must leave the "
        f"working tree clean (helper found the §14 subsection current); "
        f"got dirty paths: {status!r}"
    )

    # Plan-doc carries exactly ONE ### Commit SHAs subsection — no
    # duplicate emit.
    plan_text = sealed_plan_path.read_text(encoding="utf-8")
    assert plan_text.count("### Commit SHAs") == 1, (
        f"AC.SCT.3 violation: idempotent re-invocation must NOT duplicate "
        f"the ### Commit SHAs subsection; found "
        f"{plan_text.count('### Commit SHAs')} occurrences"
    )
