"""AC.MFBM.5 — Persona's memory-system MCP-client wiring retires
from runtime.

Plan ref: ``oss-v0-1-0-publish-memory-pivot.md`` §5 AC.MFBM.5.

Verification (per plan): grep the synthetic v0.1.0 tree for runtime
instantiation of ``MemoryClient`` outside of dev-only test fixtures:
zero hits.

Implementation under test: the production memory-client factory in
``session_start_emitter._default_memory_client_factory`` returns
``None`` post-M-FBM; ``build_session_composer`` registers the
file-based contributor in that path. The legacy
``mcp_memory_client.build_live_mcp_memory_client`` stays on disk
(M-GMP relocates it) but is no longer reachable from the production
runtime path.
"""

from __future__ import annotations

from pathlib import Path

from loam.primary_persona.session_start_emitter import (
    _default_memory_client_factory,
    build_session_composer,
)


def test_AC_MFBM_5_default_factory_returns_none(tmp_path: Path) -> None:
    """Production-default memory-client factory returns ``None`` post-
    M-FBM; the file-based contributor takes over via the dedicated
    branch in ``build_session_composer``."""
    assert _default_memory_client_factory(tmp_path) is None


def test_AC_MFBM_5_composer_registers_file_based_contributor(
    tmp_path: Path,
) -> None:
    """When the production factory returns None, the file-based
    contributor IS registered (not absent — a registered empty-state
    contributor is the M-FBM graceful-empty contract)."""
    composer = build_session_composer(tmp_path)
    # ``_contributors`` is a list of ``RegisteredContributor`` (post-
    # session-start-context-load-gate composer shape). Test by name.
    names = [c.name for c in composer._contributors]  # type: ignore[attr-defined]
    assert "memory-retrieval" in names


def test_AC_MFBM_5_no_mcp_import_in_session_start_factory_branch() -> None:
    """The default factory's source code does not import
    ``mcp_memory_client``. M-FBM (AC.MFBM.5) retires the runtime
    MCP path."""
    import inspect
    from loam.primary_persona import session_start_emitter as sse

    source = inspect.getsource(sse._default_memory_client_factory)
    assert "mcp_memory_client" not in source
    assert "build_live_mcp_memory_client" not in source


def test_AC_MFBM_5_memory_provider_protocol_is_importable() -> None:
    """The MemoryProvider Protocol stub authored at M-FBM is
    importable from the package surface; M-GMP implements graphiti's
    provider against it."""
    from loam.primary_persona import MemoryProvider

    # Protocol-shape: methods are abstract via ellipsis in a Protocol;
    # the test asserts the names are present.
    assert hasattr(MemoryProvider, "add_episode")
    assert hasattr(MemoryProvider, "search")
    assert hasattr(MemoryProvider, "health")
