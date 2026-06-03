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

"""★ AC-CAIRN-LIVE-3 (outcome-altitude: true) — the accuracy anchor.

Run the PRODUCTION per-project derivation (``derive_project_state("cairn")``)
against the LIVE ``/Users/lukeivers/cairn`` repo with NO pre-arranged
state. The returned record classifies Cairn's actually-built Layer-A
modules (verify / ledger / execute / pilot / cause) as BUILT (MERGED)
from ground truth — automatically reproducing the verdict the persona
got WRONG ("the engine isn't usable, verify/execute/ledger remain").

This drives the production registry entry point, no fixtures, no
pre-arranged state — it is the whole point of Slice C: prove the
generalization works on a SEPARATE repo before any lens-injection.

The test SKIPS (does not fail) if the live Cairn repo is absent (a fresh
clone / CI host without it) — the outcome-altitude assertion is about the
live repo when present, and an absent repo is an environment condition,
not a regression in the derivation.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from loam_cli.audit.cairn_state import DEFAULT_CAIRN_REPO_ROOT
from loam_cli.audit.probe import Liveness
from loam_cli.audit.registry import derive_project_state

# The five Layer-A modules the persona claimed "remain" / "isn't usable"
# but which exist on disk + landed via merged feature PRs.
_BUILT_MODULES = ("verify", "ledger", "execute", "pilot", "cause")


def _live_cairn_present() -> bool:
    return (DEFAULT_CAIRN_REPO_ROOT / ".git").exists() and (
        DEFAULT_CAIRN_REPO_ROOT / "src" / "cairn"
    ).is_dir()


@pytest.mark.skipif(
    not _live_cairn_present(),
    reason="live /Users/lukeivers/cairn repo not present on this host",
)
def test_live_cairn_derivation_classifies_built_modules_as_built() -> None:
    """outcome-altitude: the production derivation, run against the LIVE
    Cairn repo with no pre-arranged state, classifies the built modules
    as MERGED — reproducing the verdict the persona got WRONG."""
    # Production entry point. No fixtures, no overrides — the live repo's
    # ground truth is derived fresh inside the registry.
    record = derive_project_state("cairn")

    assert record is not None, "cairn must be a registered project"
    # head_sha was derived from the live repo's ref graph.
    assert record.head_sha != "UNKNOWN"

    for module in _BUILT_MODULES:
        row = record.by_name(module)
        assert row is not None, f"{module} missing from the derived record"
        assert row.liveness is Liveness.MERGED, (
            f"{module} must derive BUILT (merged) from ground truth — the "
            f"verdict the persona got WRONG; got {row.liveness.value}. "
            f"Evidence: {row.evidence}"
        )
        # The verdict carries ground-truth evidence (present modules +
        # introducing-commit ancestry), not a prose summary.
        assert "impl files" in row.evidence
        assert "ancestor of HEAD" in row.evidence


@pytest.mark.skipif(
    not _live_cairn_present(),
    reason="live /Users/lukeivers/cairn repo not present on this host",
)
def test_live_cairn_record_is_generated_fresh_not_persisted() -> None:
    """Two successive derivations return equivalent verdicts derived
    fresh from the same ground truth — there is no persisted prose
    source that could drift between them."""
    a = derive_project_state("cairn")
    b = derive_project_state("cairn")
    assert a is not None and b is not None
    assert a.head_sha == b.head_sha
    assert {r.name: r.liveness for r in a.components} == {
        r.name: r.liveness for r in b.components
    }
