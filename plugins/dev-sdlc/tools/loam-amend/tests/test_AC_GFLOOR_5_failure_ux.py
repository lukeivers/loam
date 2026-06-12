"""AC.GFLOOR.5 — floor-failure UX (D-GFLOOR.2).

Per ``docs/plans/seal-guard-sweep-floor.md`` §4: a floor breach
emits a HALT diagnostic that names (a) the breached guard target,
(b) the pytest failure output, (c) the introducing diff window
``<baseline>..<amendment-sha>`` with an explicit statement that this
cycle's diff is the introducing diff, and (d) a ready-to-run
inspection command.
"""

from __future__ import annotations

from loam_amend.cli import main as cli_main
from loam_amend.manifest import load_manifest

from test_seal import (
    _git,
    _make_amendment_commit,
    _write_manifest,
    sealed_repo,  # noqa: F401 — pytest fixture
)
from test_AC_GFLOOR_2_registry_targets_run import (
    _write_registry,
    _write_sweep_guard,
)


def test_AC_GFLOOR_5_breach_diagnostic_names_guard_window_and_command(
    sealed_repo, capsys
) -> None:
    repo = sealed_repo
    _write_sweep_guard(repo, passing=False)
    _write_registry(repo, ["guards/test_AC_FAKE_*.py"])

    manifest_path = _write_manifest(
        repo,
        components=["alpha"],
        number=937,
        slug="gfloor-5-ux",
        seal_description="gfloor-5 ux",
    )
    amendment_sha = _make_amendment_commit(repo, "alpha", payload="gfloor5")
    baseline = load_manifest(manifest_path).baseline

    rc = cli_main(["seal", str(manifest_path)])
    assert rc != 0
    out = capsys.readouterr().out

    # (a) breached guard target named.
    assert "HALT: guard-floor-breach" in out
    assert "guards/test_AC_FAKE_sweep_guard.py" in out
    # (b) pytest failure output present.
    assert "fixture-injected sweep-class breach" in out
    # (c) introducing window + the introducing-cycle statement.
    assert f"{baseline}..{amendment_sha[:7]}" in out
    assert "introducing" in out
    # (d) ready-to-run inspection command.
    assert f"git diff {baseline}..{amendment_sha[:7]} --stat" in out
