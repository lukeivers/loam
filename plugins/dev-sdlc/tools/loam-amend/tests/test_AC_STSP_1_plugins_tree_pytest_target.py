"""AC.STSP.1 — manifest with plugins-tree ``seal_test:`` → pytest
invocation runs against ``plugins/<plugin>/<comp>/tests/``.

Per plan-doc ``amendment-138-loam-amend-seal-tool-hygiene-pair.md``
§4 (Scope A: F-SEAL-PLUGINS-TESTS-SKIPPED).

The pre-amendment-#138 seal step hardcoded the per-component pytest
target as ``framework/<comp>/tests/`` (line 796 in canonical
HEAD ``30fd65d``). Plugins-tree components silently skipped because
``framework/<comp>/tests/`` did not exist. Post-amendment, the
manifest's mandatory ``seal_test:`` field's parent directory is the
pytest target — both framework- and plugins-located components run.

Mechanism-level test (mocks ``_run_pytest`` to capture invocation
target). AC.STSP.S covers the outcome-altitude smoke via the
production seal entry-point.
"""

from __future__ import annotations

import subprocess
import textwrap
from pathlib import Path
from unittest.mock import patch

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


def _seed_plugins_component(repo: Path, plugin: str, name: str) -> None:
    """Seed a plugins-tree component at ``plugins/<plugin>/<name>/``."""
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
    (base / "tests" / "test_basic.py").write_text(
        textwrap.dedent(
            """
            def test_component_ok():
                assert True
            """
        ).lstrip(),
        encoding="utf-8",
    )


@pytest.fixture
def plugins_repo(tmp_path: Path) -> Path:
    """Workspace with a plugins-tree component."""
    repo = tmp_path / "workspace"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "loam amend test")
    (repo / ".gitignore").write_text(
        "__pycache__/\n*.pyc\n", encoding="utf-8"
    )
    (repo / "CLAUDE.md").write_text("# fixture\n", encoding="utf-8")
    _seed_plugins_component(repo, "demo", "comp-x")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "fixture: initial plugins component")
    return repo


def _write_plugins_manifest(repo: Path, plugin: str, name: str) -> Path:
    plans_dir = repo / "docs" / "plans"
    plans_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = plans_dir / "amendment-2001-stsp1-fixture.manifest.yaml"
    baseline = _git(repo, "rev-parse", "HEAD").stdout.strip()
    manifest_path.write_text(
        textwrap.dedent(
            f"""
            schema_version: 1
            amendment:
              number: 2001
              slug: stsp1-fixture
              title: "fixture for AC.STSP.1"
            baseline: {baseline}
            plan: docs/plans/amendment-2001-stsp1-fixture.md
            components:
              - name: {name}
                seal_test: plugins/{plugin}/{name}/tests/test_no_sealed_amendments.py
                sidecar: plugins/{plugin}/{name}/tests/SEAL_COMMIT
            seal_description: "stsp1 fixture"
            """
        ).lstrip(),
        encoding="utf-8",
    )
    _git(repo, "add", "--", str(manifest_path.relative_to(repo)))
    _git(repo, "commit", "-q", "-m", "fixture: stsp1 manifest")
    return manifest_path


def _land_amendment_commit(repo: Path, plugin: str, name: str) -> None:
    target = repo / "plugins" / plugin / name / "src" / "amendment.py"
    target.write_text("# stsp1\n", encoding="utf-8")
    _git(
        repo, "add", "--", str(target.relative_to(repo))
    )
    _git(repo, "commit", "-q", "-m", f"feat({name}): stsp1 amendment edit")


def test_AC_STSP_1_plugins_tree_seal_test_invokes_plugins_tests_dir(
    plugins_repo, monkeypatch
):
    """When manifest's ``seal_test:`` is plugins/<plugin>/<comp>/tests/<test>.py,
    the per-component pytest invocation targets plugins/<plugin>/<comp>/tests/."""
    repo = plugins_repo
    manifest_path = _write_plugins_manifest(repo, "demo", "comp-x")
    _land_amendment_commit(repo, "demo", "comp-x")
    monkeypatch.chdir(repo)

    captured_targets: list[Path] = []

    real_run_pytest = None
    from loam_amend.commands import seal as seal_mod

    real_run_pytest = seal_mod._run_pytest

    def _capture(repo_root, target, *, env=None):
        captured_targets.append(Path(target))
        return real_run_pytest(repo_root, target, env=env)

    with patch.object(seal_mod, "_run_pytest", side_effect=_capture):
        rc = cli_main(["seal", "--scoped-sweep", str(manifest_path)])

    assert rc == 0, "seal must succeed on the plugins-tree fixture"
    # Step (d) target — first invocation per the loop in _finalize step (d).
    # Resolve symlinks (macOS /private/var prefix) before comparing.
    assert captured_targets, "_run_pytest must be invoked for the component"
    first = captured_targets[0].resolve()
    expected = (repo / "plugins" / "demo" / "comp-x" / "tests").resolve()
    assert first == expected, (
        f"step (d) pytest target must be plugins/demo/comp-x/tests/ "
        f"(got {first}, expected {expected})"
    )
