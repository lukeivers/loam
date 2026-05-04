"""AC.LAE.1 — ``loam amend apply`` (non-dry-run) auto-commits the apply step.

Plan: ``docs/rebuild/plans/v0-1-2-loam-amend-ergonomics.md`` AC.LAE.1.
Per v0.1.2 item 6 (loam-amend ergonomics sweep).
"""

from __future__ import annotations

import os
import subprocess
import textwrap
from pathlib import Path

import yaml

from loam_amend.commands.apply import run as apply_run


def _git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout.strip()


def _seed_component(
    repo: Path, name: str, baseline_value: str = "0000000"
) -> None:
    """Seed a component under framework/<name>/ with seal-test + sidecar."""
    comp = repo / "framework" / name
    (comp / "src").mkdir(parents=True)
    (comp / "tests").mkdir(parents=True)
    (comp / "src" / "code.py").write_text(
        "def foo():\n    return 1\n", encoding="utf-8"
    )
    (comp / "tests" / "SEAL_COMMIT").write_text(
        f"{baseline_value}\n", encoding="utf-8"
    )
    (comp / "tests" / "test_no_sealed_amendments.py").write_text(
        textwrap.dedent(
            f'''
            BASELINE = "{baseline_value}"

            def test_x():
                allowed_prefixes = (
                    "framework/{name}/",
                )
                allowed_files: set[str] = set()
                assert True
            '''
        ).lstrip(),
        encoding="utf-8",
    )


def _author_manifest(
    repo: Path,
    *,
    baseline_sha: str,
    components: list[dict[str, str]],
    number: int = 99,
    slug: str = "ac-lae-1",
    seal_description: str | None = None,
) -> Path:
    manifest_path = repo / "manifest.yaml"
    manifest_doc: dict = {
        "schema_version": 1,
        "amendment": {
            "number": number,
            "slug": slug,
            "title": f"{slug} test",
        },
        "baseline": baseline_sha,
        "plan": f"docs/rebuild/plans/{slug}.md",
        "components": components,
    }
    if seal_description is not None:
        manifest_doc["seal_description"] = seal_description
    manifest_path.write_text(yaml.safe_dump(manifest_doc), encoding="utf-8")
    return manifest_path


def test_apply_creates_chore_amend_commit(scratch_repo: Path) -> None:
    """Successful non-dry-run apply with substantive changes auto-commits."""
    repo = scratch_repo
    _seed_component(repo, "alpha", baseline_value="aaaaaaa")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "seed alpha")
    baseline_sha = _git(repo, "rev-parse", "HEAD")

    # Edit code.py to make a substantive change requiring BASELINE+sidecar
    # bump from "aaaaaaa" → baseline_sha.
    (repo / "framework" / "alpha" / "src" / "code.py").write_text(
        "def foo():\n    return 2\n", encoding="utf-8"
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "edit alpha/src/code.py")

    pre_apply_sha = _git(repo, "rev-parse", "HEAD")
    manifest_path = _author_manifest(
        repo,
        baseline_sha=pre_apply_sha,
        components=[
            {
                "name": "alpha",
                "seal_test": "framework/alpha/tests/test_no_sealed_amendments.py",
                "sidecar": "framework/alpha/tests/SEAL_COMMIT",
            }
        ],
        slug="ac-lae-1-success",
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "manifest commit")

    pre_apply_head = _git(repo, "rev-parse", "HEAD")
    rc = apply_run(manifest_path, dry_run=False)
    assert rc == 0

    # HEAD should have advanced (auto-commit landed).
    post_apply_head = _git(repo, "rev-parse", "HEAD")
    assert post_apply_head != pre_apply_head, (
        "auto-commit should have advanced HEAD beyond pre-apply state"
    )

    # The new commit's subject should match the AC.LAE.1 shape.
    subject = _git(repo, "log", "-1", "--format=%s")
    assert subject.startswith("chore(amend): ac-lae-1-success apply"), (
        f"unexpected subject: {subject!r}"
    )
    assert " alpha BASELINE+sidecar bump to " in subject, (
        f"unexpected subject: {subject!r}"
    )

    # Working tree should be clean post-commit.
    porcelain = _git(repo, "status", "--porcelain")
    assert porcelain == "", f"working tree dirty post-apply: {porcelain!r}"


def test_idempotent_re_run_skips_commit(scratch_repo: Path) -> None:
    """Re-applying a manifest with no on-disk changes does NOT commit."""
    repo = scratch_repo
    _seed_component(repo, "beta", baseline_value="bbbbbbb")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "seed beta")
    baseline_sha = _git(repo, "rev-parse", "HEAD")

    # Touch a substantive edit so the first apply has work to do.
    (repo / "framework" / "beta" / "src" / "code.py").write_text(
        "def foo():\n    return 2\n", encoding="utf-8"
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "edit beta/src/code.py")
    pre_apply_sha = _git(repo, "rev-parse", "HEAD")

    manifest_path = _author_manifest(
        repo,
        baseline_sha=pre_apply_sha,
        components=[
            {
                "name": "beta",
                "seal_test": "framework/beta/tests/test_no_sealed_amendments.py",
                "sidecar": "framework/beta/tests/SEAL_COMMIT",
            }
        ],
        slug="ac-lae-1-idempotent",
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "manifest commit")

    # First apply should commit.
    pre1 = _git(repo, "rev-parse", "HEAD")
    rc1 = apply_run(manifest_path, dry_run=False)
    assert rc1 == 0
    post1 = _git(repo, "rev-parse", "HEAD")
    assert post1 != pre1

    # Second apply: nothing to bump, nothing to commit.
    rc2 = apply_run(manifest_path, dry_run=False)
    assert rc2 == 0
    post2 = _git(repo, "rev-parse", "HEAD")
    assert post2 == post1, (
        "idempotent re-run should NOT advance HEAD"
    )


def test_multi_component_subject_shape(scratch_repo: Path) -> None:
    """Multi-component manifest produces ``<a>+<b>`` in the subject."""
    repo = scratch_repo
    _seed_component(repo, "gamma", baseline_value="ggggggg")
    _seed_component(repo, "delta", baseline_value="ddddddd")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "seed gamma + delta")

    # Substantive edit on both.
    (repo / "framework" / "gamma" / "src" / "code.py").write_text(
        "def foo():\n    return 2\n", encoding="utf-8"
    )
    (repo / "framework" / "delta" / "src" / "code.py").write_text(
        "def foo():\n    return 2\n", encoding="utf-8"
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "edit gamma + delta")
    baseline = _git(repo, "rev-parse", "HEAD")

    manifest_path = _author_manifest(
        repo,
        baseline_sha=baseline,
        components=[
            {
                "name": "gamma",
                "seal_test": "framework/gamma/tests/test_no_sealed_amendments.py",
                "sidecar": "framework/gamma/tests/SEAL_COMMIT",
            },
            {
                "name": "delta",
                "seal_test": "framework/delta/tests/test_no_sealed_amendments.py",
                "sidecar": "framework/delta/tests/SEAL_COMMIT",
            },
        ],
        slug="ac-lae-1-multi",
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "manifest")

    rc = apply_run(manifest_path, dry_run=False)
    assert rc == 0
    subject = _git(repo, "log", "-1", "--format=%s")
    assert "gamma+delta BASELINE+sidecar bump" in subject, (
        f"unexpected multi-component subject: {subject!r}"
    )


def test_co_authored_by_trailer_under_claude_env(
    scratch_repo: Path, monkeypatch
) -> None:
    """Co-Authored-By trailer appears when CLAUDECODE env var is set."""
    repo = scratch_repo
    _seed_component(repo, "epsilon", baseline_value="eeeeeee")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "seed epsilon")

    (repo / "framework" / "epsilon" / "src" / "code.py").write_text(
        "def foo():\n    return 2\n", encoding="utf-8"
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "edit epsilon")
    baseline = _git(repo, "rev-parse", "HEAD")

    manifest_path = _author_manifest(
        repo,
        baseline_sha=baseline,
        components=[
            {
                "name": "epsilon",
                "seal_test": "framework/epsilon/tests/test_no_sealed_amendments.py",
                "sidecar": "framework/epsilon/tests/SEAL_COMMIT",
            }
        ],
        slug="ac-lae-1-coauth",
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "manifest")

    # Force the Claude-env detection true; clear other vars to avoid
    # spurious detection from the test runner env.
    monkeypatch.setenv("CLAUDECODE", "1")
    monkeypatch.delenv("CLAUDE_CODE_SDK", raising=False)
    monkeypatch.delenv("CLAUDE_AGENT_RUN", raising=False)

    rc = apply_run(manifest_path, dry_run=False)
    assert rc == 0
    body = _git(repo, "log", "-1", "--format=%B")
    assert "Co-Authored-By: Claude Opus 4.7" in body, (
        f"trailer missing under CLAUDECODE=1: {body!r}"
    )


def test_co_authored_by_trailer_absent_without_env(
    scratch_repo: Path, monkeypatch
) -> None:
    """Co-Authored-By trailer is omitted when no Claude env vars set."""
    repo = scratch_repo
    _seed_component(repo, "zeta", baseline_value="zzzzzzz")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "seed zeta")

    (repo / "framework" / "zeta" / "src" / "code.py").write_text(
        "def foo():\n    return 2\n", encoding="utf-8"
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "edit zeta")
    baseline = _git(repo, "rev-parse", "HEAD")

    manifest_path = _author_manifest(
        repo,
        baseline_sha=baseline,
        components=[
            {
                "name": "zeta",
                "seal_test": "framework/zeta/tests/test_no_sealed_amendments.py",
                "sidecar": "framework/zeta/tests/SEAL_COMMIT",
            }
        ],
        slug="ac-lae-1-no-coauth",
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "manifest")

    monkeypatch.delenv("CLAUDECODE", raising=False)
    monkeypatch.delenv("CLAUDE_CODE_SDK", raising=False)
    monkeypatch.delenv("CLAUDE_AGENT_RUN", raising=False)

    rc = apply_run(manifest_path, dry_run=False)
    assert rc == 0
    body = _git(repo, "log", "-1", "--format=%B")
    assert "Co-Authored-By:" not in body, (
        f"trailer should be absent without env: {body!r}"
    )
