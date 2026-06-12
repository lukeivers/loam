"""AC.STSP.S — outcome-altitude smoke: synthetic seal cycle on a
plugins-tree component runs the plugins-tree pytest before producing
the seal commit.

Per plan-doc ``amendment-138-loam-amend-seal-tool-hygiene-pair.md``
§4 (Scope A: F-SEAL-PLUGINS-TESTS-SKIPPED).

``outcome-altitude: true`` — invokes the production seal entry-point
against a fixture combining a plugins-tree component with a
plugins-tree ``seal_test:`` field. No mocking of ``_run_pytest`` —
the pytest invocation against the plugins-tree directory must
actually fire and pass for the seal to succeed.

Pre-amendment-#138 the seal would have silently skipped the
plugins-tree pytest (no ``framework/<comp>/tests/`` directory
existed); the seal commit would have been created without running
the component's tests. AC.STSP.S verifies that does NOT happen
post-amendment — when the component's test would fail, the seal
halts; when it would pass, the seal succeeds AND the pytest
invocation has been observed to run.
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


def _seed_plugins_component_failing(
    repo: Path, plugin: str, name: str
) -> None:
    """Seed a plugins-tree component whose component test FAILS.

    Used to prove the post-amendment seal step actually invokes the
    plugins-tree pytest (a pre-amendment seal would silently skip
    the missing framework/ tests dir, so the failure would not halt
    the seal). Post-amendment, the failing component test halts the
    seal at step (d).
    """
    base = repo / "plugins" / plugin / name
    (base / "src").mkdir(parents=True)
    (base / "tests").mkdir(parents=True)
    (base / "src" / "code.py").write_text(
        "def x():\n    return 1\n", encoding="utf-8"
    )
    (base / "tests" / "__init__.py").write_text("\n", encoding="utf-8")
    (base / "tests" / "SEAL_COMMIT").write_text(
        "0000000000000000000000000000000000000000\n", encoding="utf-8"
    )
    (base / "tests" / "test_no_sealed_amendments.py").write_text(
        textwrap.dedent(
            f"""
            allowed_prefixes = (
                "plugins/{plugin}/{name}/",
                "docs/plans/",
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
    (base / "tests" / "test_failing.py").write_text(
        textwrap.dedent(
            """
            def test_intentional_failure_to_prove_pytest_ran():
                assert False, (
                    "intentional failure: AC.STSP.S uses this test "
                    "to prove the seal step actually ran pytest "
                    "against the plugins-tree directory"
                )
            """
        ).lstrip(),
        encoding="utf-8",
    )


def _seed_plugins_component_passing(
    repo: Path, plugin: str, name: str
) -> None:
    """Seed a plugins-tree component whose component tests PASS."""
    base = repo / "plugins" / plugin / name
    (base / "src").mkdir(parents=True)
    (base / "tests").mkdir(parents=True)
    (base / "src" / "code.py").write_text(
        "def x():\n    return 1\n", encoding="utf-8"
    )
    (base / "tests" / "__init__.py").write_text("\n", encoding="utf-8")
    (base / "tests" / "SEAL_COMMIT").write_text(
        "0000000000000000000000000000000000000000\n", encoding="utf-8"
    )
    (base / "tests" / "test_no_sealed_amendments.py").write_text(
        textwrap.dedent(
            f"""
            allowed_prefixes = (
                "plugins/{plugin}/{name}/",
                "docs/plans/",
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
    (base / "tests" / "test_passing.py").write_text(
        textwrap.dedent(
            """
            def test_passes():
                assert True
            """
        ).lstrip(),
        encoding="utf-8",
    )


def _setup_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "workspace"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "loam amend test")
    (repo / ".gitignore").write_text(
        "__pycache__/\n*.pyc\n", encoding="utf-8"
    )
    (repo / "CLAUDE.md").write_text("# fixture\n", encoding="utf-8")
    return repo


def _write_manifest(repo: Path, plugin: str, name: str, number: int) -> Path:
    plans_dir = repo / "docs" / "plans"
    plans_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = plans_dir / f"amendment-{number}-stsp-s-fixture.manifest.yaml"
    baseline = _git(repo, "rev-parse", "HEAD").stdout.strip()
    manifest_path.write_text(
        textwrap.dedent(
            f"""
            schema_version: 1
            amendment:
              number: {number}
              slug: stsp-s-fixture
              title: "fixture for AC.STSP.S"
            baseline: {baseline}
            plan: docs/plans/amendment-{number}-stsp-s-fixture.md
            components:
              - name: {name}
                seal_test: plugins/{plugin}/{name}/tests/test_no_sealed_amendments.py
                sidecar: plugins/{plugin}/{name}/tests/SEAL_COMMIT
            seal_description: "stsp-s fixture"
            """
        ).lstrip(),
        encoding="utf-8",
    )
    _git(repo, "add", "--", str(manifest_path.relative_to(repo)))
    _git(repo, "commit", "-q", "-m", f"fixture: amendment-{number} manifest")
    return manifest_path


def _land_amendment_edit(repo: Path, plugin: str, name: str) -> None:
    target = repo / "plugins" / plugin / name / "src" / "amendment.py"
    target.write_text("# stsp-s\n", encoding="utf-8")
    _git(
        repo, "add", "--", str(target.relative_to(repo))
    )
    _git(repo, "commit", "-q", "-m", f"feat({name}): stsp-s amendment edit")


def test_AC_STSP_S_failing_plugins_test_halts_the_seal(
    tmp_path, monkeypatch
):
    """Plugins-tree component with an intentionally-failing
    component test halts the seal at step (d). Proves the plugins-
    tree pytest actually ran (pre-amendment-#138 it silently
    skipped, so the seal would have committed regardless)."""
    repo = _setup_repo(tmp_path)
    _seed_plugins_component_failing(repo, "demo", "comp-failing")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "fixture: failing plugins component")

    manifest_path = _write_manifest(repo, "demo", "comp-failing", 2003)
    _land_amendment_edit(repo, "demo", "comp-failing")
    monkeypatch.chdir(repo)

    rc = cli_main(["seal", str(manifest_path)])

    assert rc == 3, (
        "seal must halt with exit 3 when plugins-tree component test "
        "fails; pre-amendment-#138 would have exited 0 because the "
        "framework/<comp>/tests/ dir doesn't exist (silent skip)"
    )


def test_AC_STSP_S_passing_plugins_test_completes_the_seal(
    tmp_path, monkeypatch
):
    """Plugins-tree component with passing tests → seal commit lands.

    End-to-end: production cli_main(["seal", ...]) invocation against
    a plugins-tree fixture produces a seal commit only after pytest
    has run against ``plugins/<plugin>/<comp>/tests/`` and passed."""
    repo = _setup_repo(tmp_path)
    _seed_plugins_component_passing(repo, "demo", "comp-passing")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "fixture: passing plugins component")

    manifest_path = _write_manifest(repo, "demo", "comp-passing", 2004)
    _land_amendment_edit(repo, "demo", "comp-passing")
    monkeypatch.chdir(repo)

    pre_seal_sha = _git(repo, "rev-parse", "HEAD").stdout.strip()

    rc = cli_main(["seal", str(manifest_path)])
    assert rc == 0, "seal must succeed on the passing-plugins fixture"

    # Seal commit lands.
    post_seal_sha = _git(repo, "rev-parse", "HEAD").stdout.strip()
    assert post_seal_sha != pre_seal_sha, (
        "seal step must create a new commit on the passing path"
    )
    subject = _git(
        repo, "log", "-1", "--format=%s"
    ).stdout.strip()
    assert subject.startswith("chore(seals):"), (
        f"seal commit subject must start with 'chore(seals):' "
        f"(got: {subject})"
    )
