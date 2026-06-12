"""AC.HYG.S — outcome-altitude shared smoke: ONE synthetic seal
cycle exercising BOTH amendment-#138 fixes together.

Per plan-doc ``amendment-138-loam-amend-seal-tool-hygiene-pair.md``
§4 (shared smoke covering Scope A + Scope B interaction).

``outcome-altitude: true`` — single end-to-end test invokes the
production seal entry-point against a fixture combining the
plugins-tree manifest AC.STSP.S uses with the clean-tree AC.DTCO.S
inverse. Asserts:

- the seal completes successfully (exit 0),
- the plugins-tree pytest ran (Scope A — verified by the test
  passing, which proves pytest invoked the plugins-tree directory
  and saw a passing test),
- the plan-doc archives to ``docs/plans/sealed/`` (Scope B — the
  archive step runs AFTER the dirty-tree gate passes, against a
  clean tree),
- a seal commit lands.

The merged-amendment interaction risk this smoke catches: if the
reorder (Scope B) accidentally broke the plugins-tree pytest
invocation (Scope A) — e.g., by passing the wrong path argument
or breaking the loop ordering — the smoke would fail with either
a missing pytest call or a wrong-target call.
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


def _seed_plugins_component(repo: Path, plugin: str, name: str) -> None:
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


def test_AC_HYG_S_merged_amendment_end_to_end_seal_cycle(tmp_path, monkeypatch):
    """One synthetic seal cycle exercising BOTH fixes:

    - plugins-tree component → Scope A's pytest invocation must
      run plugins/<plugin>/<comp>/tests/,
    - clean working tree → Scope B's dirty-tree gate passes, then
      the archive step moves plan-doc + manifest into sealed/,
    - seal commit lands.
    """
    repo = tmp_path / "workspace"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "loam amend test")
    (repo / ".gitignore").write_text(
        "__pycache__/\n*.pyc\n", encoding="utf-8"
    )
    (repo / "CLAUDE.md").write_text("# fixture\n", encoding="utf-8")
    _seed_plugins_component(repo, "demo", "hyg-comp")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "fixture: initial plugins component")

    # Plan-doc.
    plan_path = repo / "docs" / "plans" / "hyg-s-fixture.md"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(
        "# Fixture plan doc\n\n## §14. Method-decision register\n\n"
        "placeholder.\n",
        encoding="utf-8",
    )
    _git(repo, "add", "--", "docs/plans/hyg-s-fixture.md")
    _git(repo, "commit", "-q", "-m", "fixture: plan-doc")

    # Manifest pointing at plugins-tree seal_test.
    plans_dir = repo / "docs" / "plans"
    manifest_path = plans_dir / "amendment-2007-hyg-s-fixture.manifest.yaml"
    baseline = _git(repo, "rev-parse", "HEAD").stdout.strip()
    manifest_path.write_text(
        textwrap.dedent(
            f"""
            schema_version: 1
            amendment:
              number: 2007
              slug: hyg-s-fixture
              title: "fixture for AC.HYG.S"
            baseline: {baseline}
            plan: docs/plans/hyg-s-fixture.md
            components:
              - name: hyg-comp
                seal_test: plugins/demo/hyg-comp/tests/test_no_sealed_amendments.py
                sidecar: plugins/demo/hyg-comp/tests/SEAL_COMMIT
            seal_description: "hyg-s shared smoke"
            """
        ).lstrip(),
        encoding="utf-8",
    )
    _git(repo, "add", "--", str(manifest_path.relative_to(repo)))
    _git(repo, "commit", "-q", "-m", "fixture: hyg-s manifest")

    # Amendment edit + commit.
    edit_path = repo / "plugins" / "demo" / "hyg-comp" / "src" / "amendment.py"
    edit_path.write_text("# hyg-s\n", encoding="utf-8")
    _git(repo, "add", "--", str(edit_path.relative_to(repo)))
    _git(repo, "commit", "-q", "-m", "feat(hyg-comp): hyg-s amendment edit")
    amendment_sha = _git(repo, "rev-parse", "HEAD").stdout.strip()

    monkeypatch.chdir(repo)

    rc = cli_main(
        ["seal", "--plan-doc", str(plan_path),
         str(manifest_path)]
    )

    # (1) Seal succeeded.
    assert rc == 0, (
        f"AC.HYG.S shared smoke: seal must succeed on the merged-fix "
        f"fixture (plugins-tree component + clean tree); got {rc}"
    )

    # (2) Seal commit landed. The post-seal §14 backfill creates an
    # additional ``docs(plans): record amendment #N ...`` commit on
    # top of the seal commit; the seal commit itself is one of the
    # most-recent commits. Walk the recent log to locate it.
    post_seal_sha = _git(repo, "rev-parse", "HEAD").stdout.strip()
    assert post_seal_sha != amendment_sha, (
        "seal step must create new commits beyond amendment"
    )
    log_subjects = _git(
        repo, "log", "-5", "--format=%s"
    ).stdout.strip().splitlines()
    seal_subjects = [s for s in log_subjects if s.startswith("chore(seals):")]
    assert seal_subjects, (
        f"AC.HYG.S: expected a 'chore(seals): ...' commit in the last "
        f"5 commits; got log subjects:\n{log_subjects}"
    )

    # (3) Plan-doc + manifest moved to sealed/ (Scope B archive after
    # gate; gate passed because tree was clean).
    sealed_plan = repo / "docs" / "plans" / "sealed" / plan_path.name
    sealed_manifest = (
        repo / "docs" / "plans" / "sealed" / manifest_path.name
    )
    assert sealed_plan.exists(), (
        "AC.HYG.S: plan-doc must be archived to docs/plans/sealed/ "
        "on successful seal (Scope B archive runs after the gate)"
    )
    assert sealed_manifest.exists(), (
        "AC.HYG.S: manifest must be archived to docs/plans/sealed/ "
        "on successful seal"
    )
    assert not plan_path.exists()
    assert not manifest_path.exists()

    # (4) Sidecar advanced to amendment SHA (proves seal flow ran
    # through to the commit step — which is only reachable if both
    # Scope A's pytest invocation against plugins/demo/hyg-comp/tests/
    # passed AND Scope B's gate passed against the clean tree).
    sidecar = (
        repo / "plugins" / "demo" / "hyg-comp" / "tests" / "SEAL_COMMIT"
    ).read_text().strip()
    assert sidecar == amendment_sha, (
        f"sidecar must advance to amendment SHA after merged-fix "
        f"seal; got {sidecar}, expected {amendment_sha}"
    )
