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

from workspace_bootstrap import (
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
    contribution_file = tmp_path / "onboarding_adapter.py"
    contribution_file.write_text(
        "from workspace_bootstrap import BaseContribution, ContributionMetadata, Phase\n"
        "OBSERVED = []\n"
        "class OnboardingContribution(BaseContribution):\n"
        "    metadata = ContributionMetadata(\n"
        "        name='onboarding',\n"
        "        phase=Phase.after_orchestrator_ready,\n"
        "    )\n"
        "    def contribute(self, host):\n"
        "        OBSERVED.append(('onboarding', id(host)))\n"
    )
    # Manifest has ONE line for the new contribution (a path-form
    # entry is one list item — a single manifest line).
    manifest = {
        "version": 1,
        "workspace_root": str(tmp_path),
        "contributions": [
            {
                "name": "onboarding",
                "path": "./onboarding_adapter.py",
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
        assert mod.OBSERVED[0][0] == "onboarding"
    finally:
        await bs.shutdown()


@pytest.mark.asyncio
async def test_B18_synthetic_contribution_orders_against_foundational(
    tmp_path: Path,
) -> None:
    """A Phase 4+ contribution declaring `after=("self_correction",)`
    runs after self_correction, without bootstrap source changes."""
    contribution_file = tmp_path / "onboarding_adapter.py"
    contribution_file.write_text(
        "from workspace_bootstrap import BaseContribution, ContributionMetadata, Phase\n"
        "RECORD = []\n"
        "class OnboardingContribution(BaseContribution):\n"
        "    metadata = ContributionMetadata(\n"
        "        name='onboarding',\n"
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
            "name": "onboarding",
            "path": "./onboarding_adapter.py",
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
    contribution_file = tmp_path / "onboarding_adapter.py"
    contribution_file.write_text(
        "from workspace_bootstrap import BaseContribution, ContributionMetadata, Phase\n"
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
            {"name": "a", "path": "./onboarding_adapter.py", "attr": "A"},
            {"name": "b", "path": "./onboarding_adapter.py", "attr": "B"},
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
    'onboarding' or any Phase 4+ synthetic contribution. The extension
    protocol must not require bootstrap source changes to admit new
    contributions.

    We scan workspace_bootstrap/src for the word 'onboarding' — if
    bootstrap's source names a future contribution, the framework is
    failing the extension-protocol contract.
    """
    src_root = Path(__file__).resolve().parent.parent / "src"
    for py_file in src_root.rglob("*.py"):
        contents = py_file.read_text()
        # Allow mentions in tests only. `src/` must not name the
        # synthetic.
        assert "onboarding" not in contents.lower(), (
            f"{py_file} mentions 'onboarding' — a Phase 4+ contribution "
            "name that bootstrap should not know about."
        )
