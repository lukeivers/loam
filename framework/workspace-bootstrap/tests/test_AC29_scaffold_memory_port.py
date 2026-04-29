"""Amendment #29 acceptance tests — workspace-bootstrap scaffold
propagates per-workspace memory-sidecar port.

AC29.2 — the first-run scaffold resolves a port value from the
workspace's ``memory.yaml`` and propagates it to the launchd plist's
``EnvironmentVariables`` (``GRAPHITI_SERVICE_PORT``) so the sidecar
process binds that port on service start.

AC29.3 — two scaffold invocations with distinct per-workspace
``memory.yaml`` port values produce two plists carrying the two
distinct port values. The port source is workspace-local (the
``~/.loam/memory.yaml`` under the workspace-associated pos_root), not
a host-global constant.
"""

from __future__ import annotations

from pathlib import Path

from workspace_bootstrap.adapters.first_run_scaffold import (
    run_first_run_scaffold,
    service_label,
)


# ---- test helpers ---------------------------------------------------


def _memory_yaml(port: int, host: str = "127.0.0.1") -> str:
    return (
        "launch: true\n"
        f"host: {host}\n"
        f"port: {port}\n"
        "health_path: /health\n"
        "startup_timeout_s: 30\n"
        "poll_interval_s: 0.5\n"
    )


def _scaffold_with_preseeded_memory_yaml(
    *,
    pos_root: Path,
    workspace_root: Path,
    agents_dir: Path,
    port: int,
) -> None:
    """Drive ``run_first_run_scaffold`` through the partial_recovery
    path so a pre-seeded ``memory.yaml`` is respected.

    The scaffold's normal fresh-run path writes the starter
    ``_MEMORY_YAML`` on top of an empty pos_root, so to exercise the
    "operator edited the port" case the test pre-seeds the yaml then
    invokes the scaffold with ``partial_recovery=True`` — the
    recovery path keeps existing files untouched, re-installs plists,
    and uses the on-disk yaml for the propagation read-back.
    """
    pos_root.mkdir(parents=True, exist_ok=True)
    # Seed memory.yaml AND bootstrap.yaml presence marker so partial
    # recovery semantics line up (the scaffold's detection heuristic
    # keys off the presence of ``bootstrap.yaml``; a seed of
    # ``memory.yaml`` under partial_recovery is then honoured).
    (pos_root / "memory.yaml").write_text(_memory_yaml(port))
    # Place a stub bootstrap.yaml so the scaffold's "already
    # scaffolded" check does not fire; under partial_recovery the
    # scaffold still installs plists and reads memory.yaml for
    # propagation.
    (pos_root / "bootstrap.yaml").write_text("contributions: []\n")
    run_first_run_scaffold(
        pos_root=pos_root,
        platform_override="macos",
        service_bootstrap=False,
        service_manager_dir_override=agents_dir,
        workspace_root=workspace_root,
        partial_recovery=True,
    )


def _read_plist_port(
    agents_dir: Path, workspace_root: Path
) -> tuple[str, str | None, str | None]:
    """Return (label, plist_text, env_port_str) for the memory-
    graphiti plist in ``agents_dir``. ``env_port_str`` is None if the
    plist does not contain a ``GRAPHITI_SERVICE_PORT`` key."""
    slug = workspace_root.name
    label = service_label("memory-graphiti", slug)
    path = agents_dir / f"{label}.plist"
    text = path.read_text()
    # Minimal XML sniff — the template has the form:
    # <key>GRAPHITI_SERVICE_PORT</key><string>NNNN</string>
    marker = "<key>GRAPHITI_SERVICE_PORT</key><string>"
    env_port: str | None = None
    idx = text.find(marker)
    if idx >= 0:
        start = idx + len(marker)
        end = text.find("</string>", start)
        if end > start:
            env_port = text[start:end]
    return label, text, env_port


# ---- AC29.2 ---------------------------------------------------------


def test_AC29_2_scaffold_propagates_memory_yaml_port_to_plist(
    tmp_path: Path,
) -> None:
    """Pre-seed a workspace's ``memory.yaml`` with ``port: 19876`` and
    invoke the scaffold. The emitted memory-graphiti plist carries
    ``GRAPHITI_SERVICE_PORT`` with value ``19876`` in its
    ``EnvironmentVariables`` dict."""
    workspace = tmp_path / "alpha-ws"
    workspace.mkdir()
    pos_root = tmp_path / "pos-alpha"
    agents = tmp_path / "LaunchAgents-alpha"

    _scaffold_with_preseeded_memory_yaml(
        pos_root=pos_root,
        workspace_root=workspace,
        agents_dir=agents,
        port=19876,
    )

    _label, plist_text, env_port = _read_plist_port(agents, workspace)
    assert env_port == "19876", (
        f"plist did not carry GRAPHITI_SERVICE_PORT=19876; "
        f"env_port={env_port!r} plist_text={plist_text!r}"
    )
    # LOAM_WORKSPACE_ROOT must also be present and point at this
    # workspace — AC29.5's plist-side wiring.
    assert f"<key>LOAM_WORKSPACE_ROOT</key><string>{workspace}</string>" in plist_text


# ---- AC29.3 ---------------------------------------------------------


def test_AC29_3_distinct_workspace_configs_produce_distinct_plist_ports(
    tmp_path: Path,
) -> None:
    """Two workspaces with distinct ``memory.yaml`` port values
    produce plists with distinct port values. Mutating one
    workspace's config does not affect the other's scaffold output —
    the port source is workspace-local (its own ``~/.loam/memory.yaml``),
    not a host-global sentinel."""
    # Workspace A.
    ws_a = tmp_path / "alpha-ws"
    ws_a.mkdir()
    pos_a = tmp_path / "pos-alpha"
    agents_a = tmp_path / "LaunchAgents-alpha"
    _scaffold_with_preseeded_memory_yaml(
        pos_root=pos_a,
        workspace_root=ws_a,
        agents_dir=agents_a,
        port=19876,
    )

    # Workspace B — disjoint pos_root + agents dir, different port.
    ws_b = tmp_path / "beta-ws"
    ws_b.mkdir()
    pos_b = tmp_path / "pos-beta"
    agents_b = tmp_path / "LaunchAgents-beta"
    _scaffold_with_preseeded_memory_yaml(
        pos_root=pos_b,
        workspace_root=ws_b,
        agents_dir=agents_b,
        port=19877,
    )

    _a_label, _a_text, port_a = _read_plist_port(agents_a, ws_a)
    _b_label, _b_text, port_b = _read_plist_port(agents_b, ws_b)

    assert port_a == "19876"
    assert port_b == "19877"
    assert port_a != port_b

    # Isolation: re-reading A after B's scaffold shows A's port
    # unchanged. No host-global state exists.
    _, _, port_a_again = _read_plist_port(agents_a, ws_a)
    assert port_a_again == "19876"
