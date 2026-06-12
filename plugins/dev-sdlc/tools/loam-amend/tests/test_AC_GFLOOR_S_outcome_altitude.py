"""AC.GFLOOR.S ★ (outcome-altitude) — a foreign-fence guard breach
is BLOCKED at the introducing cycle's own seal.

Per ``docs/plans/seal-guard-sweep-floor.md`` §4: on a synthetic repo
via the production ``loam amend seal`` entry point (CLI main, no
pre-arranged internal state): an amendment whose fence is component
A but whose diff introduces a known breach of a sibling floor guard
is BLOCKED at its own seal with the guard-floor-breach diagnostic;
the identical amendment without the breach seals green.

This is the FIDRAFT F-SEAL-GUARD-SWEEP-FLOOR outcome: six real
breaches (currency cycle → primary-persona AC.alpha.8 + dev-sdlc
AC.PBRET.5, etc.) landed silently because the introducing cycle's
narrow fence never ran the sibling sweep — each bit the NEXT
innocent seal. The dominant real instances are repo-wide CONTENT
sweeps (banned-stem / marker sweeps), which is exactly the guard
shape modelled here.
"""

from __future__ import annotations

import textwrap

import pytest

from loam_amend.cli import main as cli_main

from test_seal import (
    _git,
    _write_manifest,
    sealed_repo,  # noqa: F401 — pytest fixture
)
from test_AC_GFLOOR_2_registry_targets_run import _write_registry

pytestmark = pytest.mark.outcome_altitude


_STEM = "FORBIDDEN" + "-STEM"  # split so the guard never flags itself


def _install_content_sweep_guard(repo) -> None:
    """A sibling repo-wide content sweep — the AC.PBRET.5 /
    AC.alpha.8 guard shape: git-grep the whole tracked tree for a
    banned stem, excluding the guard's own home."""
    guard = repo / "guards" / "test_AC_STEM_repo_wide_sweep.py"
    guard.parent.mkdir(parents=True, exist_ok=True)
    guard.write_text(
        textwrap.dedent(
            '''
            import subprocess
            from pathlib import Path

            STEM = "FORBIDDEN" + "-STEM"


            def test_no_banned_stem_anywhere_in_tracked_tree():
                repo = Path(__file__).resolve().parents[1]
                proc = subprocess.run(
                    ["git", "grep", "-l", STEM, "--", ".", ":!guards/"],
                    cwd=repo,
                    capture_output=True,
                    text=True,
                )
                offenders = [
                    ln for ln in proc.stdout.splitlines() if ln.strip()
                ]
                assert not offenders, (
                    "banned stem found in tracked tree: "
                    f"{offenders}"
                )
            '''
        ).lstrip(),
        encoding="utf-8",
    )
    _git(repo, "add", "--", "guards/test_AC_STEM_repo_wide_sweep.py")
    _git(repo, "commit", "-q", "-m", "fixture: sibling content-sweep guard")
    _write_registry(repo, ["guards/test_AC_STEM_*.py"])


def test_AC_GFLOOR_S_foreign_fence_breach_blocked_at_introducing_seal(
    sealed_repo, capsys
) -> None:
    repo = sealed_repo
    _install_content_sweep_guard(repo)

    manifest_path = _write_manifest(
        repo,
        components=["alpha"],
        number=940,
        slug="gfloor-oa",
        seal_description="gfloor outcome-altitude",
    )

    # The amendment: entirely inside alpha's own fence, but its
    # content breaches the sibling content-sweep guard.
    edit = repo / "framework" / "alpha" / "src" / "amendment.py"
    edit.write_text(f"# payload carries {_STEM} by mistake\n", encoding="utf-8")
    _git(repo, "add", "--", "framework/alpha/src/amendment.py")
    _git(repo, "commit", "-q", "-m", "feat(alpha): fixture amendment edit")
    amendment_sha = _git(repo, "rev-parse", "HEAD").stdout.strip()

    # Production entry point: the introducing cycle's own seal.
    rc = cli_main(["seal", str(manifest_path)])
    assert rc != 0
    out = capsys.readouterr().out
    assert "HALT: guard-floor-breach" in out
    assert "guards/test_AC_STEM_repo_wide_sweep.py" in out
    # BLOCKED: no seal commit was created.
    head = _git(repo, "rev-parse", "HEAD").stdout.strip()
    assert head == amendment_sha

    # The identical amendment WITHOUT the breach seals green: author
    # a corrective commit removing the stem, re-invoke the seal.
    edit.write_text("# payload, stem removed\n", encoding="utf-8")
    _git(repo, "add", "--", "framework/alpha/src/amendment.py")
    _git(repo, "commit", "-q", "-m", "fix(alpha): remove banned stem")

    rc2 = cli_main(["seal", str(manifest_path)])
    assert rc2 == 0
    body = _git(repo, "log", "-1", "--format=%B").stdout
    assert "chore(seals):" in body
    assert "sweep-class)" in body
