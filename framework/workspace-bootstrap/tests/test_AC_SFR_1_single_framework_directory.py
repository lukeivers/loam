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
framework-only branch into `<new-ws>/framework/`.

Single-framework restructure (amendment #67). After the restructure
landed, `pos-new-workspace` clones canonical's `framework-only`
synthetic branch (rather than the default `pos-v2` branch).

**Shape evolution:** Pre-FBE.2b (amendment #109) the synth pipeline
stripped the `framework/` prefix on shipped paths, so the framework-
only branch carried bare-component paths (`workspace-sync/...`,
`tools/loam/...`) at root; cloning into `<new-ws>/framework/`
produced single-level shape `<new-ws>/framework/<comp>/`. Post-
FBE.2b the synth preserves canonical's `framework/<comp>/` shape
verbatim on shipped paths, so cloning into `<new-ws>/framework/`
produces `<new-ws>/framework/framework/<comp>/` (DOUBLED). Post-
FBE.2c (amendment #111) commits to the doubled-component contract
in this test; top-level docs (CLAUDE.md, docs/) stay single-level
because they were never under `framework/` in pos-v2.

The historical "single level" / "no doubling" framing in this
file's name + the test function name is preserved as a documentation
artifact (rename = scope creep per FBE.2c sub-plan §9). Per
AC.FBE.2c.3 the test body asserts the post-FBE.2b/FBE.2c contract;
binding AC family is `AC.FBE.2c.*`.

Test surface verifies:

- Doubled component-leaf shape: `<new-ws>/framework/framework/<comp>/`
  exists for the fixture's components (e.g. workspace-sync,
  workspace-bootstrap) — AC.FBE.2c.3.
- Top-level docs land under `<new-ws>/framework/<doc>` (single-level):
  framework-only carries CLAUDE.md / docs/ at the synthetic-branch
  root because they were never under `framework/` in pos-v2.
- HC#4 byte-content match: `<new-ws>/framework/CLAUDE.md` byte-equals
  canonical's pos-v2 `CLAUDE.md` (top-level doc; single-level).
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
    """The bootstrap produces `<new-ws>/framework/framework/<comp>/`
    (doubled component shape, post-FBE.2b/FBE.2c).

    Function name preserved as a documentation artifact (the original
    AC.SFR.1 named "single level"; FBE.2b/FBE.2c shifted the contract
    to "doubled-component shape, single-level top-level docs").
    Binding AC family post-FBE.2c is `AC.FBE.2c.*`; see file-level
    docstring for the shape-evolution narrative.

    Post-FBE.2b/FBE.2c contract: when canonical publishes a
    `framework-only` branch (the fixture does so by default),
    `pos-new-workspace` clones that branch into `<new-ws>/framework/`.
    Components live DOUBLED at `<new-ws>/framework/framework/<comp>/`
    because the synth preserves the `framework/` prefix on component
    leaves (FBE.2b synth contract). Top-level docs (CLAUDE.md, docs/)
    live SINGLE-LEVEL at `<new-ws>/framework/<doc>` because they were
    never under `framework/` in pos-v2.
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

    # AC.FBE.2c.3: components at DOUBLED location post-FBE.2b synth.
    assert (framework / "framework" / "workspace-sync").is_dir()
    assert (framework / "framework" / "workspace-bootstrap").is_dir()

    # AC.FBE.2c.3: doubling REQUIRED for component leaves to land
    # (post-FBE.2b synth contract). Pre-FBE.2b this assertion was
    # `assert not (...).exists()`; FBE.2c flipped it to commit to the
    # post-FBE.2b shape. See FBE.2b sub-plan §1 + FBE.2c sub-plan §1
    # for the synth-shape narrative.
    assert (framework / "framework").is_dir(), (
        f"AC.FBE.2c.3: post-FBE.2b doubled-component shape required; "
        f"<new-ws>/framework/framework/ MUST exist at "
        f"{framework / 'framework'} for component leaves to land "
        f"(synth preserves canonical's framework/ prefix verbatim)"
    )

    # AC.FBE.2c.3: top-level docs at <new-ws>/framework/<doc>
    # (single-level — they were never under framework/ in pos-v2 so
    # the synth doesn't double-prefix them).
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
