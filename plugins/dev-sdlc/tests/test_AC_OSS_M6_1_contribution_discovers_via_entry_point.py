"""AC.OSS-M6.1 — Plugin discovers via workspace-bootstrap's
contribution protocol.

Per plan §4 AC.OSS-M6.1: a workspace whose `bootstrap.yaml` lists
`dev_sdlc` boots cleanly with the plugin's contribution running; a
workspace whose `bootstrap.yaml` does NOT list it boots cleanly
without the plugin loading.
"""

from __future__ import annotations

import importlib.metadata

from loam.plugins.dev_sdlc.contribution import (
    DevSdlcContribution,
    DevSdlcRuntime,
)


def test_entry_point_discoverable_in_bootstrap_contributions_group() -> None:
    """The plugin's pyproject.toml registers under
    `loam.bootstrap.contributions` and the entry-point resolves to
    `DevSdlcContribution`."""
    eps = importlib.metadata.entry_points(
        group="loam.bootstrap.contributions"
    )
    matches = [ep for ep in eps if ep.name == "dev_sdlc"]
    assert matches, (
        "expected entry-point 'dev_sdlc' in group "
        "'loam.bootstrap.contributions' (plugin's pyproject.toml "
        "must declare it)"
    )
    cls = matches[0].load()
    assert cls is DevSdlcContribution


def test_contribute_assigns_dev_sdlc_runtime_on_host() -> None:
    """Calling `DevSdlcContribution().contribute(host)` populates
    `host.dev_sdlc` with a `DevSdlcRuntime` instance carrying the
    workspace_root + composed runtimes."""

    class _StubHost:
        workspace_root = "<ws>"
        scope_runtime = object()
        objective_tracker = object()

    host = _StubHost()
    contrib = DevSdlcContribution()
    contrib.contribute(host)
    assert hasattr(host, "dev_sdlc")
    runtime = host.dev_sdlc
    assert isinstance(runtime, DevSdlcRuntime)
    assert runtime.workspace_root == "<ws>"
    assert runtime.scope_runtime is host.scope_runtime
    assert runtime.objective_tracker is host.objective_tracker


def test_contribution_metadata_phase_and_after_ordering() -> None:
    """Plugin's metadata declares
    `phase=after_orchestrator_ready` and orders after
    primary_persona, objective_tracker, scope_of_work — so the host
    surfaces it consumes are populated before contribute() runs."""
    md = DevSdlcContribution.metadata
    assert md.name == "dev_sdlc"
    assert md.phase.value == "after_orchestrator_ready"
    assert "primary_persona" in md.after
    assert "objective_tracker" in md.after
    assert "scope_of_work" in md.after
