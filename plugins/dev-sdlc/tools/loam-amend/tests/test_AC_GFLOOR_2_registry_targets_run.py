"""AC.GFLOOR.2 — registry-driven sweep-class floor.

Per ``docs/plans/seal-guard-sweep-floor.md`` §4: when the repo
carries ``docs/plans/guard-floor.yaml``, every registry pattern is
resolved against tracked files at seal time and every resolved
target runs as part of the floor; a red floor target halts the seal
before the seal commit is created.

(The fence-class red-halts case lives at
``test_seal.py::test_AC_GFLOOR_2_floor_red_halts_before_commit``;
this file covers the registry/sweep-class leg.)
"""

from __future__ import annotations

from pathlib import Path

from loam_amend.cli import main as cli_main

from test_seal import (
    _git,
    _make_amendment_commit,
    _write_manifest,
    sealed_repo,  # noqa: F401 — pytest fixture
)


def _write_registry(repo: Path, patterns: list[str]) -> None:
    reg = repo / "docs" / "plans" / "guard-floor.yaml"
    reg.parent.mkdir(parents=True, exist_ok=True)
    lines = ["schema_version: 1", "patterns:"]
    for p in patterns:
        lines.append(f'  - pattern: "{p}"')
        lines.append('    guard_class: "fixture guard class"')
    reg.write_text("\n".join(lines) + "\n", encoding="utf-8")
    _git(repo, "add", "--", "docs/plans/guard-floor.yaml")
    _git(repo, "commit", "-q", "-m", "fixture: guard-floor registry")


def _write_sweep_guard(repo: Path, *, passing: bool) -> None:
    guard = repo / "guards" / "test_AC_FAKE_sweep_guard.py"
    guard.parent.mkdir(parents=True, exist_ok=True)
    if passing:
        body = "def test_sweep_guard_ok():\n    assert True\n"
    else:
        body = (
            "def test_sweep_guard_breached():\n"
            "    assert False, 'fixture-injected sweep-class breach'\n"
        )
    guard.write_text(body, encoding="utf-8")
    _git(repo, "add", "--", "guards/test_AC_FAKE_sweep_guard.py")
    _git(
        repo,
        "commit",
        "-q",
        "-m",
        f"fixture: sweep guard ({'green' if passing else 'red'})",
    )


def test_AC_GFLOOR_2_registry_targets_run_at_seal(sealed_repo) -> None:
    """A registry pattern's resolved target runs at seal: the floor
    summary counts it as a sweep-class member."""
    repo = sealed_repo
    _write_sweep_guard(repo, passing=True)
    _write_registry(repo, ["guards/test_AC_FAKE_*.py"])

    manifest_path = _write_manifest(
        repo,
        components=["alpha"],
        number=931,
        slug="gfloor-2-green",
        seal_description="gfloor-2 green",
    )
    _make_amendment_commit(repo, "alpha", payload="gfloor2a")

    rc = cli_main(["seal", str(manifest_path)])
    assert rc == 0
    body = _git(repo, "log", "-1", "--format=%B").stdout
    # sealed_repo carries alpha + beta fence tests; +1 sweep-class.
    assert "guard floor 3 targets green (2 fence + 1 sweep-class)" in body


def test_AC_GFLOOR_2_red_sweep_target_halts_before_commit(
    sealed_repo, capsys
) -> None:
    """A red sweep-class target blocks the seal commit — the breach
    is caught at the introducing cycle."""
    repo = sealed_repo
    _write_sweep_guard(repo, passing=False)
    _write_registry(repo, ["guards/test_AC_FAKE_*.py"])

    manifest_path = _write_manifest(
        repo,
        components=["alpha"],
        number=932,
        slug="gfloor-2-red",
        seal_description="gfloor-2 red",
    )
    amendment_sha = _make_amendment_commit(repo, "alpha", payload="gfloor2b")

    rc = cli_main(["seal", str(manifest_path)])
    assert rc != 0
    out = capsys.readouterr().out
    assert "HALT: guard-floor-breach" in out
    # No seal commit: HEAD is still the amendment commit.
    head = _git(repo, "rev-parse", "HEAD").stdout.strip()
    assert head == amendment_sha
