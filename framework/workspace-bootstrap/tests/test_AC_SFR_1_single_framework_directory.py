"""AC.SFR.1 — `pos-new-workspace --from <canonical>` produces a
single-level framework directory.

Single-framework restructure (amendment #67). After the restructure
landed, `pos-new-workspace` clones canonical's `framework-only`
synthetic branch (rather than the default `pos-v2` branch). The
synthetic branch's tree promotes canonical's `framework/<entry>` to
root + carries top-level docs verbatim, so the resulting workspace
has shape `<new-ws>/framework/<comp>/` for every sealed component
(no `framework/framework/<comp>/` doubling).

Test surface verifies:

- Single-level shape: `<new-ws>/framework/<comp>/` exists for the
  fixture's components (e.g. workspace-sync, workspace-bootstrap).
- No doubling: `<new-ws>/framework/framework/` MUST NOT exist.
- Top-level docs land under `<new-ws>/framework/`: framework-only
  carries CLAUDE.md / docs/ etc. at the synthetic-branch root.
- HC#4 byte-content match: `<new-ws>/framework/CLAUDE.md` byte-equals
  canonical's pos-v2 `CLAUDE.md`.
- Workspace's `<new-ws>/framework/` tracks `framework-only` as the
  checked-out branch (so subsequent `pos-sync` runs against the
  synthetic branch — AC.SFR.4 binding).
- Failure mode: when canonical does not publish `framework-only`, the
  bootstrap fails with a structured CloneFailedError.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from loam.workspace_bootstrap.adapters import tracker_seed
from loam.workspace_bootstrap.new_workspace import (
    CloneFailedError,
    bootstrap_new_workspace,
)


def _stub_tracker_seed_runner(**_kwargs):
    return tracker_seed.TrackerSeedResult(
        seeded=False,
        reason="skipped_test_stub",
        classification="user",
        root_id=None,
        descendants_seeded=(),
        value_prop_source=None,
    )


def _git_show(repo: Path, ref_with_path: str) -> str:
    return subprocess.run(  # noqa: S603
        ["git", "show", ref_with_path],
        cwd=str(repo),
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def test_AC_SFR_1_single_level_framework_directory(
    tmp_path: Path,
    make_fixture_canonical,
) -> None:
    """The bootstrap produces `<new-ws>/framework/<comp>/` (no doubling).

    AC.SFR.1: when canonical publishes a `framework-only` branch (the
    fixture does so by default), `pos-new-workspace` clones that branch
    into `<new-ws>/framework/`. Components live at single level
    (`<new-ws>/framework/workspace-sync/...` rather than
    `<new-ws>/framework/framework/workspace-sync/...`), and top-level
    docs (CLAUDE.md, docs/) live under `<new-ws>/framework/`.
    """
    canonical = make_fixture_canonical(tmp_path / "canonical")
    new_ws = tmp_path / "new-ws"
    agents = tmp_path / "LaunchAgents"

    bootstrap_new_workspace(
        new_ws_path=new_ws,
        canonical_source=str(canonical),
        service_manager_dir_override=agents,
        tracker_seed_runner=_stub_tracker_seed_runner,
    )

    framework = new_ws / "framework"

    # AC.SFR.1: components at single level.
    assert (framework / "workspace-sync").is_dir()
    assert (framework / "workspace-bootstrap").is_dir()

    # AC.SFR.1: no doubling. The failure class the restructure
    # eliminates.
    assert not (framework / "framework").exists(), (
        f"AC.SFR.1: doubling failure class re-introduced; "
        f"<new-ws>/framework/framework/ at "
        f"{framework / 'framework'}"
    )

    # AC.SFR.1: top-level docs at <new-ws>/framework/<doc>.
    assert (framework / "CLAUDE.md").exists()
    assert (framework / "docs" / "odd-methodology.md").exists()


def test_AC_SFR_1_byte_content_match_against_pos_v2(
    tmp_path: Path,
    make_fixture_canonical,
) -> None:
    """HC#4 binding — `<new-ws>/framework/CLAUDE.md` byte-equals
    canonical's `pos-v2` `CLAUDE.md`. The synthesis carries content
    verbatim; the bootstrap clones it verbatim; HC#4 holds end-to-end.
    """
    canonical = make_fixture_canonical(tmp_path / "canonical")
    new_ws = tmp_path / "new-ws"

    bootstrap_new_workspace(
        new_ws_path=new_ws,
        canonical_source=str(canonical),
        service_manager_dir_override=tmp_path / "LaunchAgents",
        tracker_seed_runner=_stub_tracker_seed_runner,
    )

    canonical_claude = _git_show(canonical, "pos-v2:CLAUDE.md")
    workspace_claude = (new_ws / "framework" / "CLAUDE.md").read_text()
    assert canonical_claude == workspace_claude

    canonical_odd = _git_show(canonical, "pos-v2:docs/odd-methodology.md")
    workspace_odd = (
        new_ws / "framework" / "docs" / "odd-methodology.md"
    ).read_text()
    assert canonical_odd == workspace_odd


def test_AC_SFR_1_workspace_tracks_framework_only_branch(
    tmp_path: Path,
    make_fixture_canonical,
) -> None:
    """AC.SFR.1: the workspace's `<new-ws>/framework/.git/` tracks
    `framework-only` as origin. AC.SFR.4 composition binding:
    subsequent `pos-sync` operates against the synthetic branch.
    """
    canonical = make_fixture_canonical(tmp_path / "canonical")
    new_ws = tmp_path / "new-ws"

    bootstrap_new_workspace(
        new_ws_path=new_ws,
        canonical_source=str(canonical),
        service_manager_dir_override=tmp_path / "LaunchAgents",
        tracker_seed_runner=_stub_tracker_seed_runner,
    )

    framework = new_ws / "framework"

    head_branch = subprocess.run(  # noqa: S603
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=str(framework),
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert head_branch == "framework-only"

    # And origin's HEAD on the workspace's clone tracks origin/
    # framework-only.
    upstream = subprocess.run(  # noqa: S603
        [
            "git",
            "rev-parse",
            "--abbrev-ref",
            "--symbolic-full-name",
            "@{u}",
        ],
        cwd=str(framework),
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert upstream == "origin/framework-only"


def test_AC_SFR_1_failure_when_framework_only_absent(
    tmp_path: Path,
) -> None:
    """When canonical does not publish `framework-only`, the bootstrap
    fails with CloneFailedError naming the missing branch.

    The fixture is constructed with publish_framework_only=False so the
    canonical exposes only the default `pos-v2` branch. The clone with
    `--branch framework-only` fails non-zero; the bootstrap surfaces a
    structured error rather than silently producing a broken workspace.
    """
    from .conftest import _make_fixture_canonical

    canonical = _make_fixture_canonical(
        tmp_path / "canonical-no-fo",
        publish_framework_only=False,
    )
    new_ws = tmp_path / "new-ws"

    with pytest.raises(CloneFailedError) as excinfo:
        bootstrap_new_workspace(
            new_ws_path=new_ws,
            canonical_source=str(canonical),
            service_manager_dir_override=tmp_path / "LaunchAgents",
            tracker_seed_runner=_stub_tracker_seed_runner,
        )
    msg = str(excinfo.value)
    assert "framework-only" in msg
