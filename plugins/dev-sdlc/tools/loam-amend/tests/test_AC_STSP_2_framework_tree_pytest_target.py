"""AC.STSP.2 — manifest with framework-tree ``seal_test:`` → pytest
invocation runs against ``framework/<comp>/tests/`` (unchanged behavior).

Per plan-doc ``amendment-138-loam-amend-seal-tool-hygiene-pair.md``
§4 (Scope A: F-SEAL-PLUGINS-TESTS-SKIPPED).

Regression-guard: amendment #138's switch from hardcoded
``framework/<comp>/tests/`` to schema-driven ``Path(seal_test).parent``
must NOT regress framework-tree components — these were the only
shape working pre-amendment-#138; they must continue working.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from loam_amend.cli import main as cli_main

from test_seal import (
    _git,
    _make_amendment_commit,
    _write_manifest,
    sealed_repo,  # noqa: F401 — pytest fixture
)


def test_AC_STSP_2_framework_tree_seal_test_invokes_framework_tests_dir(
    sealed_repo, monkeypatch
):
    """When manifest's ``seal_test:`` is framework/<comp>/tests/<test>.py,
    the per-component pytest invocation targets framework/<comp>/tests/
    (the pre-amendment-#138 behavior, preserved post-amendment)."""
    repo = sealed_repo
    monkeypatch.chdir(repo)
    manifest_path = _write_manifest(
        repo,
        components=["alpha"],
        number=2002,
        slug="stsp2-fixture",
        seal_description="stsp2 fixture",
    )
    _make_amendment_commit(repo, "alpha", payload="stsp2")

    captured_targets: list[Path] = []
    from loam_amend.commands import seal as seal_mod

    real_run_pytest = seal_mod._run_pytest

    def _capture(repo_root, target, *, env=None):
        captured_targets.append(Path(target))
        return real_run_pytest(repo_root, target, env=env)

    with patch.object(seal_mod, "_run_pytest", side_effect=_capture):
        rc = cli_main(["seal", "--scoped-sweep", str(manifest_path)])

    assert rc == 0, "seal must succeed on the framework-tree fixture"
    assert captured_targets, "_run_pytest must be invoked for the component"
    first = captured_targets[0].resolve()
    expected = (repo / "framework" / "alpha" / "tests").resolve()
    assert first == expected, (
        f"step (d) pytest target must be framework/alpha/tests/ "
        f"(got {first}, expected {expected})"
    )
