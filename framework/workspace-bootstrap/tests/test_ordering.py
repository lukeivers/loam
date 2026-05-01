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

"""B6–B9 — ordering engine."""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

import pytest

from loam.workspace_bootstrap import (
    BaseContribution,
    Bootstrapper,
    ContributionMetadata,
    IPC_BOOTSTRAP_NAME_COLLISION,
    IPC_BOOTSTRAP_ORDERING_CYCLE,
    IPC_BOOTSTRAP_UNKNOWN_REFERENCE,
    NameCollisionError,
    OrderingCycleError,
    Phase,
    UnknownReferenceError,
    load_manifest,
    topological_order,
)


# B6 — deterministic topological sort with alphabetical tie-breaking.


def test_B6_topological_sort_respects_after() -> None:
    triples = [
        ("b", ("a",), ()),
        ("a", (), ()),
        ("c", ("b",), ()),
    ]
    assert topological_order(triples, phase_label="test") == ["a", "b", "c"]


def test_B6_alphabetical_tie_breaking() -> None:
    """Independent nodes come out in alphabetical order."""
    triples = [("d", (), ()), ("a", (), ()), ("c", (), ()), ("b", (), ())]
    assert topological_order(triples, phase_label="test") == ["a", "b", "c", "d"]


def test_B6_before_declaration_resolved_as_reverse_edge() -> None:
    """`before=(y,)` means this runs before y → reverse edge."""
    triples = [
        ("x", (), ("y",)),  # x before y
        ("y", (), ()),
    ]
    assert topological_order(triples, phase_label="test") == ["x", "y"]


def test_B6_stable_given_equivalent_inputs() -> None:
    """Same inputs always produce the same output (reproducibility)."""
    triples = [
        ("primary_persona", ("observability_aggregator",), ()),
        ("observability_aggregator", (), ()),
        ("memory_system", ("observability_aggregator",), ()),
    ]
    for _ in range(5):
        assert topological_order(triples, phase_label="test") == [
            "observability_aggregator",
            "memory_system",
            "primary_persona",
        ]


# B7 — cycles raise -32084.


def test_B7_cycle_raises_32084() -> None:
    triples = [
        ("a", ("b",), ()),
        ("b", ("a",), ()),
    ]
    with pytest.raises(OrderingCycleError) as excinfo:
        topological_order(triples, phase_label="test")
    assert excinfo.value.code == IPC_BOOTSTRAP_ORDERING_CYCLE
    assert "a" in excinfo.value.message
    assert "b" in excinfo.value.message


def test_B7_three_node_cycle_surfaces_edges() -> None:
    triples = [
        ("a", ("c",), ()),
        ("b", ("a",), ()),
        ("c", ("b",), ()),
    ]
    with pytest.raises(OrderingCycleError) as excinfo:
        topological_order(triples, phase_label="test")
    assert excinfo.value.data.get("edges")


# B8 — unknown reference raises -32085.


def test_B8_unknown_after_raises_32085() -> None:
    triples = [("a", ("ghost",), ())]
    with pytest.raises(UnknownReferenceError) as excinfo:
        topological_order(triples, phase_label="test")
    assert excinfo.value.code == IPC_BOOTSTRAP_UNKNOWN_REFERENCE


def test_B8_unknown_before_raises_32085() -> None:
    triples = [("a", (), ("ghost",))]
    with pytest.raises(UnknownReferenceError):
        topological_order(triples, phase_label="test")


# B8 end-to-end: a manifest listing a contribution whose `after=`
# names something that is not in the manifest fails at the
# bootstrapper level too.


class _GhostyA(BaseContribution):
    metadata: ClassVar[ContributionMetadata] = ContributionMetadata(
        name="a",
        phase=Phase.before_orchestrator_start,
        after=("ghost",),
    )

    def contribute(self, host) -> None:
        return None


def test_B8_bootstrapper_unknown_reference_raises_32085(
    tmp_path: Path, write_manifest_fn
) -> None:
    adapter = tmp_path / "adapter.py"
    adapter.write_text(
        "from loam.workspace_bootstrap import BaseContribution, ContributionMetadata, Phase\n"
        "class A(BaseContribution):\n"
        "    metadata = ContributionMetadata(\n"
        "        name='a', phase=Phase.before_orchestrator_start, after=('ghost',)\n"
        "    )\n"
        "    def contribute(self, host): pass\n"
    )
    path = write_manifest_fn(
        tmp_path / "bootstrap.yaml",
        [{"name": "a", "path": "./adapter.py", "attr": "A"}],
    )
    with pytest.raises(UnknownReferenceError) as excinfo:
        bs = Bootstrapper(load_manifest(path))
        bs.resolve_and_order()
    assert excinfo.value.code == IPC_BOOTSTRAP_UNKNOWN_REFERENCE


# B4 — name collision raises -32083.


def test_B4_name_collision_raises_32083(tmp_path: Path, write_manifest_fn) -> None:
    adapter = tmp_path / "adapter.py"
    adapter.write_text(
        "from loam.workspace_bootstrap import BaseContribution, ContributionMetadata, Phase\n"
        "class A(BaseContribution):\n"
        "    metadata = ContributionMetadata(name='dup', phase=Phase.before_orchestrator_start)\n"
        "    def contribute(self, host): pass\n"
        "class B(BaseContribution):\n"
        "    metadata = ContributionMetadata(name='dup', phase=Phase.before_orchestrator_start)\n"
        "    def contribute(self, host): pass\n"
    )
    path = write_manifest_fn(
        tmp_path / "bootstrap.yaml",
        [
            {"name": "first", "path": "./adapter.py", "attr": "A"},
            {"name": "second", "path": "./adapter.py", "attr": "B"},
        ],
    )
    with pytest.raises(NameCollisionError) as excinfo:
        bs = Bootstrapper(load_manifest(path))
        bs.resolve_and_order()
    assert excinfo.value.code == IPC_BOOTSTRAP_NAME_COLLISION
    assert "dup" in excinfo.value.message


# B9 — phase ordering is respected.


def test_B9_phase_ordering_preserved(tmp_path: Path, write_manifest_fn) -> None:
    """A later-phase item NEVER runs before an earlier-phase item."""
    adapter = tmp_path / "adapter.py"
    adapter.write_text(
        "from loam.workspace_bootstrap import BaseContribution, ContributionMetadata, Phase\n"
        "RUN_LOG = []\n"
        "class EarlyA(BaseContribution):\n"
        "    metadata = ContributionMetadata(name='early_a', phase=Phase.before_orchestrator_start)\n"
        "    def contribute(self, host):\n"
        "        RUN_LOG.append('early_a')\n"
        "class WrapA(BaseContribution):\n"
        "    metadata = ContributionMetadata(name='wrap_a', phase=Phase.wrap_activate_scope)\n"
        "    def contribute(self, host):\n"
        "        RUN_LOG.append('wrap_a')\n"
        "class AfterA(BaseContribution):\n"
        "    metadata = ContributionMetadata(name='after_a', phase=Phase.after_orchestrator_ready)\n"
        "    def contribute(self, host):\n"
        "        RUN_LOG.append('after_a')\n"
    )
    path = write_manifest_fn(
        tmp_path / "bootstrap.yaml",
        [
            {"name": "after_a", "path": "./adapter.py", "attr": "AfterA"},
            {"name": "wrap_a", "path": "./adapter.py", "attr": "WrapA"},
            {"name": "early_a", "path": "./adapter.py", "attr": "EarlyA"},
        ],
    )
    bs = Bootstrapper(load_manifest(path))
    bs.resolve_and_order()
    # Verify ordering by phase. Use phase-name indexing so adding new
    # phases (e.g. first_run_scaffold) doesn't invalidate the assertion
    # about these three specific phases.
    from loam.workspace_bootstrap import Phase

    ordered = bs._ordered_by_phase
    assert ordered[Phase.before_orchestrator_start][0].name == "early_a"
    assert ordered[Phase.wrap_activate_scope][0].name == "wrap_a"
    assert ordered[Phase.after_orchestrator_ready][0].name == "after_a"


def test_B9_after_ref_pointing_at_later_phase_refused(
    tmp_path: Path, write_manifest_fn
) -> None:
    """A before-phase adapter declaring after=(wrap_item,) is illegal."""
    adapter = tmp_path / "adapter.py"
    adapter.write_text(
        "from loam.workspace_bootstrap import BaseContribution, ContributionMetadata, Phase\n"
        "class E(BaseContribution):\n"
        "    metadata = ContributionMetadata(\n"
        "        name='early', phase=Phase.before_orchestrator_start,\n"
        "        after=('wrap_me',)\n"
        "    )\n"
        "    def contribute(self, host): pass\n"
        "class W(BaseContribution):\n"
        "    metadata = ContributionMetadata(\n"
        "        name='wrap_me', phase=Phase.wrap_activate_scope\n"
        "    )\n"
        "    def contribute(self, host): pass\n"
    )
    path = write_manifest_fn(
        tmp_path / "bootstrap.yaml",
        [
            {"name": "early", "path": "./adapter.py", "attr": "E"},
            {"name": "wrap_me", "path": "./adapter.py", "attr": "W"},
        ],
    )
    with pytest.raises(UnknownReferenceError):
        bs = Bootstrapper(load_manifest(path))
        bs.resolve_and_order()
