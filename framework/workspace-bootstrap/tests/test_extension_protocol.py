"""B18, B19 — Phase 4+ extension-protocol acid test.

B18: a synthetic Phase 4 contribution registers with ONE manifest
line, ONE entry-point declaration (or path-form equivalent), and
ZERO change to workspace-bootstrap's source.

The test is constructed so the synthetic contribution lives entirely
outside workspace-bootstrap's package tree — it is a workspace-local
path entry OR a module entry declared in the test's own fake package.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

from loam.workspace_bootstrap import (
    Bootstrapper,
    ContributionMetadata,
    IPC_BOOTSTRAP_ORDERING_CYCLE,
    OrderingCycleError,
    Phase,
    load_manifest,
)


@pytest.mark.asyncio
async def test_B18_synthetic_phase4_contribution_enables_with_one_manifest_line(
    tmp_path: Path,
) -> None:
    """The acid test. A Phase 4+ contribution:

      - is defined in a workspace-local file (its own "package");
      - declares metadata `{name, phase, after=("self_correction",)}`;
      - is enabled by ONE new line in bootstrap.yaml;
      - bootstrap's code DOES NOT CHANGE to admit it.
    """
    # Minimal workspace — no orchestrator; just tests the extension
    # protocol end-to-end on contribution discovery + ordering + run.
    contribution_file = tmp_path / "synthetic_b18_adapter.py"
    contribution_file.write_text(
        "from loam.workspace_bootstrap import BaseContribution, ContributionMetadata, Phase\n"
        "OBSERVED = []\n"
        "class OnboardingContribution(BaseContribution):\n"
        "    metadata = ContributionMetadata(\n"
        "        name='synthetic_b18_phase4',\n"
        "        phase=Phase.after_orchestrator_ready,\n"
        "    )\n"
        "    def contribute(self, host):\n"
        "        OBSERVED.append(('synthetic_b18_phase4', id(host)))\n"
    )
    # Manifest has ONE line for the new contribution (a path-form
    # entry is one list item — a single manifest line).
    manifest = {
        "version": 1,
        "workspace_root": str(tmp_path),
        "contributions": [
            {
                "name": "synthetic_b18_phase4",
                "path": "./synthetic_b18_adapter.py",
                "attr": "OnboardingContribution",
            }
        ],
    }
    manifest_path = tmp_path / "bootstrap.yaml"
    manifest_path.write_text(yaml.safe_dump(manifest))

    bs = Bootstrapper(load_manifest(manifest_path))
    try:
        await bs.start()
        # Verify the synthetic contribution ran by looking at the
        # sys.modules entry for the path-form file.
        wanted_hash = abs(hash(str(contribution_file.resolve())))
        mod_key = f"_pos_workspace_bootstrap_path_{wanted_hash}"
        assert mod_key in sys.modules
        mod = sys.modules[mod_key]
        assert len(mod.OBSERVED) == 1
        assert mod.OBSERVED[0][0] == "synthetic_b18_phase4"
    finally:
        await bs.shutdown()


@pytest.mark.asyncio
async def test_B18_synthetic_contribution_orders_against_foundational(
    tmp_path: Path,
) -> None:
    """A Phase 4+ contribution declaring `after=("self_correction",)`
    runs after self_correction, without bootstrap source changes."""
    contribution_file = tmp_path / "synthetic_b18_adapter.py"
    contribution_file.write_text(
        "from loam.workspace_bootstrap import BaseContribution, ContributionMetadata, Phase\n"
        "RECORD = []\n"
        "class OnboardingContribution(BaseContribution):\n"
        "    metadata = ContributionMetadata(\n"
        "        name='synthetic_b18_phase4',\n"
        "        phase=Phase.after_orchestrator_ready,\n"
        "        after=('self_correction',),\n"
        "    )\n"
        "    def contribute(self, host):\n"
        "        # Verify self_correction_controller was populated earlier.\n"
        "        RECORD.append(host.self_correction_controller)\n"
    )

    # Full workspace so self_correction is available.
    import tempfile, uuid

    (tmp_path / "config").mkdir()
    (tmp_path / ".pos").mkdir()
    sock = Path(tempfile.gettempdir()) / f"pos-{uuid.uuid4().hex[:12]}.sock"
    (tmp_path / "config" / "orchestrator.yaml").write_text(
        yaml.safe_dump(
            {
                "root_dir": str(tmp_path / ".pos"),
                "socket_path": str(sock),
                "heartbeat_interval_seconds": 0.05,
                "sigterm_grace_seconds": 1.0,
            }
        )
    )
    (tmp_path / "config" / "memory.yaml").write_text(
        yaml.safe_dump({"launch": False})
    )
    (tmp_path / "config" / "self_upgrade.yaml").write_text(
        yaml.safe_dump({"required": False})
    )
    (tmp_path / "config" / "workspace_bootstrap_py.yaml").write_text(
        yaml.safe_dump({"bootstrap_path": str(tmp_path / "no.py"), "required": False})
    )

    contributions = [
        "observability_aggregator",
        "scope_of_work",
        "objective_tracker",
        "primary_persona",
        "graceful_degradation",
        "cost_governance",
        "reversibility_primitive",
        "safety_layer",
        "self_correction",
        {
            "name": "synthetic_b18_phase4",
            "path": "./synthetic_b18_adapter.py",
            "attr": "OnboardingContribution",
        },
    ]
    manifest = {
        "version": 1,
        "workspace_root": str(tmp_path),
        "config_dir": str(tmp_path / "config"),
        "contributions": contributions,
    }
    manifest_path = tmp_path / "bootstrap.yaml"
    manifest_path.write_text(yaml.safe_dump(manifest))

    bs = Bootstrapper(load_manifest(manifest_path))
    try:
        await bs.start()
        wanted_hash = abs(hash(str(contribution_file.resolve())))
        mod = sys.modules[f"_pos_workspace_bootstrap_path_{wanted_hash}"]
        assert len(mod.RECORD) == 1
        assert mod.RECORD[0] is bs.host.self_correction_controller
    finally:
        await bs.shutdown()


@pytest.mark.asyncio
async def test_B19_cyclic_synthetic_contribution_raises_32084(tmp_path: Path) -> None:
    """B19: a synthetic contribution declaring a cycle trips
    OrderingCycleError (-32084)."""
    contribution_file = tmp_path / "synthetic_b18_adapter.py"
    contribution_file.write_text(
        "from loam.workspace_bootstrap import BaseContribution, ContributionMetadata, Phase\n"
        "class A(BaseContribution):\n"
        "    metadata = ContributionMetadata(\n"
        "        name='a', phase=Phase.after_orchestrator_ready,\n"
        "        after=('b',), before=('b',)\n"
        "    )\n"
        "    def contribute(self, host): pass\n"
        "class B(BaseContribution):\n"
        "    metadata = ContributionMetadata(\n"
        "        name='b', phase=Phase.after_orchestrator_ready,\n"
        "    )\n"
        "    def contribute(self, host): pass\n"
    )
    manifest = {
        "version": 1,
        "workspace_root": str(tmp_path),
        "contributions": [
            {"name": "a", "path": "./synthetic_b18_adapter.py", "attr": "A"},
            {"name": "b", "path": "./synthetic_b18_adapter.py", "attr": "B"},
        ],
    }
    manifest_path = tmp_path / "bootstrap.yaml"
    manifest_path.write_text(yaml.safe_dump(manifest))
    bs = Bootstrapper(load_manifest(manifest_path))
    with pytest.raises(OrderingCycleError) as excinfo:
        bs.resolve_and_order()
    assert excinfo.value.code == IPC_BOOTSTRAP_ORDERING_CYCLE


def test_B18_bootstrap_source_unchanged_diff_check() -> None:
    """B18 companion: verify bootstrap's source tree does NOT name
    the synthetic Phase 4+ contribution this test fixture defines.
    The extension protocol must not require bootstrap source changes
    to admit new contributions.

    We scan workspace_bootstrap/src for the synthetic sentinel
    ``synthetic_b18_phase4`` (this test's deliberately-fake Phase 4+
    contribution name) — if bootstrap's source names this exact
    sentinel, the framework is failing the extension-protocol
    contract.

    Sub-plan E (amendment #42) AC-precision update: the prior
    sentinel was the bare word ``"onboarding"`` which collides with
    the legitimate ``primary_persona.onboarding`` module path that
    bootstrap's tracker_seed adapter imports from (sub-plan A's
    ``read_dev_intent`` reader). The substring check was overly
    broad — flagging an import path rather than a Phase 4+
    contribution registration. The deliberately-fake sentinel
    ``synthetic_b18_phase4`` cannot collide with any real module
    path; the AC outcome (bootstrap source untouched by Phase 4+
    contributions) is preserved.
    """
    src_root = Path(__file__).resolve().parent.parent / "src"
    sentinel = "synthetic_b18_phase4"
    for py_file in src_root.rglob("*.py"):
        contents = py_file.read_text()
        # Allow mentions in tests only. `src/` must not name the
        # synthetic.
        assert sentinel not in contents.lower(), (
            f"{py_file} mentions {sentinel!r} — a Phase 4+ "
            "contribution name that bootstrap should not know about."
        )


# ---- B25 — framework-internal phase set ------------------------------
#
# B25 (amendment #17) is the complementary criterion to B18. Where B18
# governs the external-extension protocol (Phase 4+ contributions
# register via the public extension surface with zero change to
# bootstrap's source), B25 names the framework-internal phase surface:
# every Phase enum value is claimed by at least one framework-internal
# adapter in workspace_bootstrap.adapters, and external contributions
# consume the enum rather than extend it. When a bootstrap amendment
# widens the enum (Amendment #4 added first_run_scaffold), the
# widening has explicit audit-trail affordance via this criterion.


def test_B25_framework_internal_phases_match_bootstrap_source_adapters() -> None:
    """B25 — the Phase enum values are the framework-internal phase set.

    Every Phase enum member has at least one framework-internal adapter
    (a module in ``workspace_bootstrap.adapters``) whose contribution
    class declares ``phase=Phase.<value>`` in its ContributionMetadata.
    Conversely, every framework-internal adapter's declared phase is a
    valid Phase enum member. The two sets are equal.

    Outcome-shaped — no source-grep. The test discovers adapters
    dynamically via ``pkgutil.iter_modules`` on the adapters package,
    inspects each module's ``Contribution`` subclasses, and reads the
    ``metadata.phase`` attribute off the runtime metadata. If a future
    bootstrap amendment adds a Phase enum value, this test fails until
    a framework-internal adapter lands using it (failure message names
    the orphan). If a future amendment removes an adapter without
    removing the enum value, same failure mode.
    """
    import importlib
    import pkgutil

    from loam.workspace_bootstrap import Phase
    from loam.workspace_bootstrap import adapters as adapters_pkg
    from loam.workspace_bootstrap.spec import BaseContribution, ContributionMetadata

    phases_declared_by_adapters: set[Phase] = set()
    per_adapter_phase: dict[str, Phase] = {}

    for module_info in pkgutil.iter_modules(adapters_pkg.__path__):
        mod_name = module_info.name
        # Skip helper / private modules that do not ship contributions.
        if mod_name.startswith("_"):
            continue
        mod = importlib.import_module(
            f"{adapters_pkg.__name__}.{mod_name}"
        )
        # Collect classes in this adapter module that are subclasses of
        # BaseContribution defined here (not re-imported from spec). The
        # phase-bearing metadata lives on BaseContribution subclasses.
        for attr_name in dir(mod):
            obj = getattr(mod, attr_name)
            if not isinstance(obj, type):
                continue
            if obj is BaseContribution:
                continue
            if not issubclass(obj, BaseContribution):
                continue
            # Only count classes defined in this module (ignore any
            # re-export).
            if getattr(obj, "__module__", None) != mod.__name__:
                continue
            md = getattr(obj, "metadata", None)
            if not isinstance(md, ContributionMetadata):
                continue
            phases_declared_by_adapters.add(md.phase)
            per_adapter_phase[f"{mod_name}.{obj.__name__}"] = md.phase

    # Every Phase value has at least one framework-internal adapter.
    unused_phases = set(Phase) - phases_declared_by_adapters
    assert not unused_phases, (
        f"Phase enum values without any framework-internal adapter: "
        f"{sorted(p.value for p in unused_phases)}. Every Phase member "
        "must be claimed by at least one adapter in "
        "workspace_bootstrap.adapters; add an adapter using the phase "
        "or remove the orphaned enum value."
    )
    # Every adapter's phase is a valid Phase member (tautological given
    # ContributionMetadata's schema, but stated explicitly).
    invalid = {n: p for n, p in per_adapter_phase.items() if p not in Phase}
    assert not invalid, (
        f"Adapters declaring non-enum phase values: {invalid}"
    )

    # Amendment #4 anchor: first_run_scaffold is claimed by exactly the
    # FirstRunScaffoldContribution. This pins the #4 phase's
    # single-purpose status in the criterion so a future regression
    # (orphaning the phase, or adding a second framework-internal
    # claimant) surfaces at test time.
    first_run_claimants = [
        n for n, p in per_adapter_phase.items()
        if p is Phase.first_run_scaffold
    ]
    assert first_run_claimants == ["first_run_scaffold.FirstRunScaffoldContribution"], (
        "Phase.first_run_scaffold must be claimed by exactly the "
        "FirstRunScaffoldContribution adapter (Amendment #4 anchor). "
        f"Got: {first_run_claimants}"
    )
