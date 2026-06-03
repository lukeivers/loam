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

"""AC.WVS-MR.2 (Slice E) — no fabricated project row; per-project +
whole-read fail-soft.

A project whose derivation returns ``None`` (unregistered / no spec)
produces NO bucket — never a fabricated row; survivors still render. A
per-project derivation that RAISES omits that project, survivors stay. A
registry-absent / all-fail read yields zero buckets +
``project_states_unknown=True``, and the snapshot + surface still return
(the existing AC.WVS-AGG.2 never-break-the-snapshot contract extended to
the multi-repo read).

Plan: docs/plans/fbm-multi-repo-work-visibility.md §5.
"""

from __future__ import annotations

from pathlib import Path

from loam.primary_persona.work_visibility import (
    ProjectStateSummary,
    build_snapshot,
    render_surface,
)
from loam.primary_persona.work_visibility import _read_project_states

from _helpers_d40 import FakeTrackerClient


def test_AC_WVS_MR_2_reader_raises_marks_unknown_still_renders(
    tmp_path: Path,
) -> None:
    """A project_state_reader that raises → zero buckets, unknown=True,
    snapshot still returns and surface still renders."""

    def _boom() -> tuple[ProjectStateSummary, ...]:
        raise RuntimeError("registry read failed")

    snapshot = build_snapshot(
        tmp_path,
        tracker_factory=lambda: FakeTrackerClient(query_result=()),
        project_state_reader=_boom,
    )
    assert snapshot.project_states == ()
    assert snapshot.project_states_unknown is True
    text = render_surface(snapshot)
    assert text  # never breaks the surface


def test_AC_WVS_MR_2_none_derivation_yields_no_row(tmp_path: Path) -> None:
    """A registered name whose derivation returns None yields NO bucket
    (never a fabricated row); a registered name that derives a record DOES
    appear. Drives the production registry read path with injected
    name/derive seams."""
    # Build a record-shaped fake for the present project.
    from loam_cli.audit.record import StateOfLoam, ComponentState
    from loam_cli.audit.probe import Liveness

    present = StateOfLoam(
        head_sha="abc123def",
        components=(
            ComponentState(name="m1", liveness=Liveness.MERGED, kind="component", evidence="merged"),
            ComponentState(name="m2", liveness=Liveness.MERGED, kind="component", evidence="merged"),
        ),
    )

    def _derive(name: str):
        # "ghost" is registered-name-shaped but has no spec → None (no row).
        return present if name == "real" else None

    # Patch the production registry seam the reader uses.
    import loam_cli.audit.registry as registry_mod

    orig_names = registry_mod.registered_project_names
    orig_derive = registry_mod.derive_project_state
    try:
        registry_mod.registered_project_names = lambda: ("real", "ghost")
        registry_mod.derive_project_state = _derive
        read = _read_project_states(None)
    finally:
        registry_mod.registered_project_names = orig_names
        registry_mod.derive_project_state = orig_derive

    names = {p.name for p in read.summaries}
    assert names == {"real"}  # ghost (None) produced NO row
    assert read.unknown is False
    real = next(p for p in read.summaries if p.name == "real")
    assert real.built == 2 and real.total == 2


def test_AC_WVS_MR_2_per_project_raise_omits_survivors_stay(
    tmp_path: Path,
) -> None:
    """A per-project derivation that RAISES omits that project; the
    surviving project still summarizes."""
    from loam_cli.audit.record import StateOfLoam, ComponentState
    from loam_cli.audit.probe import Liveness

    good = StateOfLoam(
        head_sha="deadbeef0",
        components=(ComponentState(name="x", liveness=Liveness.BUILT, kind="component", evidence="built"),),
    )

    def _derive(name: str):
        if name == "boom":
            raise RuntimeError("probe failed for boom")
        return good

    import loam_cli.audit.registry as registry_mod

    orig_names = registry_mod.registered_project_names
    orig_derive = registry_mod.derive_project_state
    try:
        registry_mod.registered_project_names = lambda: ("good", "boom")
        registry_mod.derive_project_state = _derive
        read = _read_project_states(None)
    finally:
        registry_mod.registered_project_names = orig_names
        registry_mod.derive_project_state = orig_derive

    names = {p.name for p in read.summaries}
    assert names == {"good"}  # boom omitted, good survives
    assert read.unknown is False


def test_AC_WVS_MR_2_default_on_never_breaks_existing_surface(
    tmp_path: Path,
) -> None:
    """The multi-repo read is default-on; even against a real registry the
    work-state surface + the existing fail-soft contract are intact (the
    snapshot still returns, no exception propagates)."""
    snapshot = build_snapshot(
        tmp_path,
        tracker_factory=lambda: FakeTrackerClient(query_result=()),
    )
    # The work-state half is unaffected; the project-state half either
    # populated (live registry) or marked unknown — never an exception.
    text = render_surface(snapshot)
    assert text
