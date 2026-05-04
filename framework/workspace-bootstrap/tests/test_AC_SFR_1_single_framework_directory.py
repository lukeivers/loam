# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""AC.SFR.1 — `pos-new-workspace --from <canonical>` clones canonical's
default branch (``main``) into ``<new-ws>/framework/``.

Single-framework restructure (amendment #67) + OSS dev-architecture
migration (2026-05-04). Post-migration the bootstrap targets
canonical's ``main`` branch directly (no synthesis layer). Canonical
carries ``framework/<comp>/`` paths + top-level docs at root, so the
clone-into ``<new-ws>/framework/`` produces:

- ``<new-ws>/framework/framework/<comp>/`` (DOUBLED component shape;
  FBE.2c.5 binding) — components live one level deeper than the
  workspace's framework/ root because canonical already prefixes
  them with ``framework/``.
- ``<new-ws>/framework/<doc>`` (single-level) — top-level docs
  (CLAUDE.md, docs/) live at one level under workspace's framework/
  because they were never under ``framework/`` in canonical.

The historical "single level" / "no doubling" framing in this file's
name + the test function name is preserved as a documentation
artifact (rename = scope creep per FBE.2c sub-plan §9). Binding AC
family is AC.FBE.2c.* + AC.WBM2M.*; see file-level docstring for the
shape-evolution narrative.

Test surface verifies:

- Doubled component-leaf shape: `<new-ws>/framework/framework/<comp>/`
  exists for the fixture's components.
- Top-level docs at `<new-ws>/framework/<doc>` (single-level).
- HC#4 byte-content match: `<new-ws>/framework/CLAUDE.md` byte-equals
  canonical's `main` `CLAUDE.md`.
- Workspace's `<new-ws>/framework/` tracks `main` as the checked-out
  branch (so subsequent `pos-sync` runs against canonical's main).

The pre-migration "framework-only absent" failure-mode test was
DELETED with the OSS dev-architecture migration: with `main` as
canonical's default branch, the equivalent failure mode (canonical
doesn't publish `main`) cannot occur for any real clone (git refuses
to clone a repo with no default branch).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from loam.workspace_bootstrap.adapters import tracker_seed
from loam.workspace_bootstrap.new_workspace import (
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
    """The bootstrap produces `<new-ws>/framework/framework/<comp>/`
    (doubled component shape, post-FBE.2b/FBE.2c).

    Function name preserved as a documentation artifact (the original
    AC.SFR.1 named "single level"; FBE.2b/FBE.2c shifted the contract
    to "doubled-component shape, single-level top-level docs").
    Binding AC family post-migration is AC.FBE.2c.* + AC.WBM2M.*.

    Post-migration contract: ``pos-new-workspace`` clones canonical's
    ``main`` branch into ``<new-ws>/framework/``. Components live
    DOUBLED at ``<new-ws>/framework/framework/<comp>/`` because
    canonical's ``framework/<comp>/`` prefix is preserved verbatim by
    the clone. Top-level docs (CLAUDE.md, docs/) live SINGLE-LEVEL at
    ``<new-ws>/framework/<doc>`` because they were never under
    ``framework/`` in canonical.
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

    # AC.FBE.2c.3: components at DOUBLED location (canonical's
    # framework/<comp>/ prefix is preserved verbatim by the clone).
    assert (framework / "framework" / "workspace-sync").is_dir()
    assert (framework / "framework" / "workspace-bootstrap").is_dir()

    # AC.FBE.2c.3: doubling REQUIRED for component leaves to land.
    # Canonical carries `framework/<comp>/` paths; the clone-into
    # `<new-ws>/framework/` lands them at `<new-ws>/framework/
    # framework/<comp>/`.
    assert (framework / "framework").is_dir(), (
        f"AC.FBE.2c.3: doubled-component shape required; "
        f"<new-ws>/framework/framework/ MUST exist at "
        f"{framework / 'framework'} for component leaves to land "
        f"(canonical's framework/ prefix preserved verbatim)"
    )

    # AC.FBE.2c.3: top-level docs at <new-ws>/framework/<doc>
    # (single-level — they were never under framework/ in canonical
    # so the clone doesn't double-prefix them).
    assert (framework / "CLAUDE.md").exists()
    assert (framework / "docs" / "odd-methodology.md").exists()


def test_AC_SFR_1_byte_content_match_against_main(
    tmp_path: Path,
    make_fixture_canonical,
) -> None:
    """HC#4 binding — `<new-ws>/framework/CLAUDE.md` byte-equals
    canonical's `main` `CLAUDE.md`. The bootstrap clones content
    verbatim; HC#4 holds end-to-end.
    """
    canonical = make_fixture_canonical(tmp_path / "canonical")
    new_ws = tmp_path / "new-ws"

    bootstrap_new_workspace(
        new_ws_path=new_ws,
        canonical_source=str(canonical),
        service_manager_dir_override=tmp_path / "LaunchAgents",
        tracker_seed_runner=_stub_tracker_seed_runner,
    )

    canonical_claude = _git_show(canonical, "main:CLAUDE.md")
    workspace_claude = (new_ws / "framework" / "CLAUDE.md").read_text()
    assert canonical_claude == workspace_claude

    canonical_odd = _git_show(canonical, "main:docs/odd-methodology.md")
    workspace_odd = (
        new_ws / "framework" / "docs" / "odd-methodology.md"
    ).read_text()
    assert canonical_odd == workspace_odd


def test_AC_SFR_1_workspace_tracks_main_branch(
    tmp_path: Path,
    make_fixture_canonical,
) -> None:
    """AC.SFR.1 + AC.WBM2M.2: the workspace's `<new-ws>/framework/.git/`
    tracks `main` as origin. AC.SFR.4 composition binding: subsequent
    `pos-sync` operates against canonical's main.
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
    assert head_branch == "main"

    # And origin's HEAD on the workspace's clone tracks origin/main.
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
    assert upstream == "origin/main"
