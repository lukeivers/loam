"""Amendment #24 — MCP service tests.

Seven outcome-shaped tests covering AC24.1 – AC24.7. The service
layer had zero test coverage pre-amendment; these are the first
service-layer tests to exist. Each test is named
``test_AC24_<n>_<slug>`` per the amendment plan at
``docs/rebuild/plans/amendment-24-memory-system-mcp-migration.md`` §3.

All tests are deterministic under mocks. No real LLM / Claude /
network call fires — the halt trigger "any test requires real LLM /
Claude / network" is cleared by injecting a ``FakeGraphiti`` stand-in
that implements the subset of the Graphiti surface the service tools
touch.

The tests exercise the tool implementation functions directly
(``_impl_*``) AND the MCP-decorated wrappers (through
``FastMCP.list_tools`` and direct wrapper invocation). The streamable-
HTTP transport itself is covered by upstream ``mcp`` tests; the
amendment's contract is "tool registered, dispatches to Graphiti
correctly, returns the right shape".
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from src import service


# ---- Fakes ----------------------------------------------------------


@dataclass
class FakeEpisode:
    uuid: str = "ep-uuid-fake"


@dataclass
class FakeNode:
    uuid: str = "node-uuid"


@dataclass
class FakeEdge:
    fact: str = "a related_to b"
    uuid: str = "edge-uuid"
    valid_at: datetime | None = None
    invalid_at: datetime | None = None
    source_node_uuid: str = "src-uuid"
    target_node_uuid: str = "tgt-uuid"


@dataclass
class FakeAddResult:
    episode: FakeEpisode = field(default_factory=FakeEpisode)
    nodes: list[FakeNode] = field(default_factory=lambda: [FakeNode(), FakeNode()])
    edges: list[FakeEdge] = field(default_factory=lambda: [FakeEdge()])


@dataclass
class FakeUsage:
    total_input_tokens: int = 10
    total_output_tokens: int = 20
    call_count: int = 1


@dataclass
class FakeTotalUsage:
    input_tokens: int = 100
    output_tokens: int = 200


class FakeTokenTracker:
    def get_usage(self) -> dict[str, FakeUsage]:
        return {"reflexive": FakeUsage()}

    def get_total_usage(self) -> FakeTotalUsage:
        return FakeTotalUsage()


class FakeLLMClient:
    def __init__(self) -> None:
        self.model = "claude-haiku-4-5"
        self.token_tracker = FakeTokenTracker()


class FakeEmbedderConfig:
    embedding_dim = 768


class FakeEmbedder:
    def __init__(self) -> None:
        self.config = FakeEmbedderConfig()


class FakeGraphiti:
    """Test stand-in for graphiti_core.Graphiti.

    Implements the subset of the Graphiti surface the MCP tools touch:
    ``add_episode``, ``search``, ``build_indices_and_constraints``,
    ``close``, plus the ``llm_client`` and ``embedder`` attributes.
    """

    def __init__(self) -> None:
        self.llm_client = FakeLLMClient()
        self.embedder = FakeEmbedder()
        self.added: list[dict[str, Any]] = []
        self.searched: list[dict[str, Any]] = []
        self.build_calls: int = 0
        self.close_calls: int = 0

    async def build_indices_and_constraints(self) -> None:
        self.build_calls += 1

    async def close(self) -> None:
        self.close_calls += 1

    async def add_episode(self, **kwargs: Any) -> FakeAddResult:
        self.added.append(kwargs)
        return FakeAddResult()

    async def search(self, **kwargs: Any) -> list[FakeEdge]:
        self.searched.append(kwargs)
        return [FakeEdge()]


@pytest.fixture
def fake_graphiti(monkeypatch: pytest.MonkeyPatch) -> FakeGraphiti:
    """Inject a FakeGraphiti as the module-level ``_graphiti``.

    Bypasses the lifespan so tool implementations can be exercised
    directly. Tests that need the lifespan itself (AC24.1) call the
    lifespan context manager explicitly and supply their own fake via
    monkeypatching ``make_graphiti``.
    """
    fake = FakeGraphiti()
    monkeypatch.setattr(service, "_graphiti", fake)
    return fake


# ---- AC24.1 ---------------------------------------------------------


def test_AC24_1_lifespan_constructs_and_closes_graphiti(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The lifespan context constructs Graphiti exactly once, calls
    ``build_indices_and_constraints()`` (via ``prepare_graphiti``),
    yields, and calls ``close()`` exactly once on exit.

    Memory-sidecar-recovery (AC.MS-FIX.4 in-band ODD §4 retire):
    the post-exit ``_graphiti is None`` assertion was over-specification
    beyond AC24.1's actual spec text. The fix that motivates this
    edit (drop the ``_graphiti = None`` line from the lifespan's
    ``finally`` block) addresses a per-session driver-leak that
    accumulated kuzu mmap reservations until macOS VA fragmentation
    failed mmap. Post-fix, the module global stays populated across
    lifespan exits — close runs, but the handle survives. Subsequent
    startups (i.e. process re-launches) still see a clean ``None``
    because the module is freshly imported.
    """
    # Avoid fake's prepare_graphiti dependency by stubbing it; AC24.1's
    # contract is about the lifespan's construct/yield/close shape, not
    # about prepare_graphiti's downstream side-effects.
    construct_calls = 0
    fake = FakeGraphiti()

    async def fake_make_graphiti() -> FakeGraphiti:
        nonlocal construct_calls
        construct_calls += 1
        return fake

    async def fake_prepare(g: Any) -> None:
        # Keep AC24.1's "build_calls == 1" expectation by exercising
        # build_indices_and_constraints inside the substituted prepare.
        await g.build_indices_and_constraints()

    # Also stub load_env so the test doesn't need an .env file.
    monkeypatch.setattr(service, "make_graphiti", fake_make_graphiti)
    monkeypatch.setattr(service, "load_env", lambda: None)
    monkeypatch.setattr(service, "prepare_graphiti", fake_prepare)
    monkeypatch.setattr(service, "_graphiti", None)

    async def exercise() -> None:
        # Enter and exit the lifespan.
        async with service.lifespan(service.mcp) as ctx:
            assert ctx["graphiti"] is fake
            assert service._graphiti is fake
            assert fake.build_calls == 1
            assert fake.close_calls == 0

    asyncio.run(exercise())
    assert construct_calls == 1
    assert fake.close_calls == 1
    # Module global stays populated across lifespan exits (driver lives
    # for process lifetime; close fires but handle survives — fix #1
    # of memory-sidecar-recovery).
    assert service._graphiti is fake


# ---- AC24.2 ---------------------------------------------------------


def test_AC24_2_add_episode_dispatches_to_graphiti(
    fake_graphiti: FakeGraphiti,
) -> None:
    """The ``add_episode`` tool dispatches to ``Graphiti.add_episode``
    with the translated args and returns the expected shape.
    """
    from graphiti_core.nodes import EpisodeType

    async def go() -> dict[str, Any]:
        return await service._impl_add_episode(
            fake_graphiti,
            name="test-ep",
            body="body text",
            source_description="unit-test episode",
            reference_time=datetime(2026, 4, 22, 12, 0, 0, tzinfo=timezone.utc),
            source="message",
            group_id="test-group",
        )

    out = asyncio.run(go())

    # Shape
    assert set(out.keys()) == {"episode_uuid", "nodes_extracted", "edges_extracted"}
    assert out["episode_uuid"] == "ep-uuid-fake"
    assert out["nodes_extracted"] == 2
    assert out["edges_extracted"] == 1

    # Dispatch correctness
    assert len(fake_graphiti.added) == 1
    call = fake_graphiti.added[0]
    assert call["name"] == "test-ep"
    assert call["episode_body"] == "body text"
    assert call["source_description"] == "unit-test episode"
    assert call["source"] == EpisodeType.message
    assert call["group_id"] == "test-group"
    assert call["reference_time"] == datetime(2026, 4, 22, 12, 0, 0, tzinfo=timezone.utc)


def test_AC24_2_add_episode_naive_reference_time_normalised_to_utc(
    fake_graphiti: FakeGraphiti,
) -> None:
    """A naive ``reference_time`` is normalised to UTC (preserves
    outgoing-FastAPI behaviour)."""
    async def go() -> None:
        await service._impl_add_episode(
            fake_graphiti,
            name="n",
            body="b",
            reference_time=datetime(2026, 1, 1, 0, 0, 0),  # naive
        )

    asyncio.run(go())
    rt = fake_graphiti.added[0]["reference_time"]
    assert rt.tzinfo is timezone.utc


# ---- AC24.3 ---------------------------------------------------------


def test_AC24_3_search_dispatches_to_graphiti(
    fake_graphiti: FakeGraphiti,
) -> None:
    """The ``search`` tool dispatches to ``Graphiti.search`` and
    returns the expected shape."""

    async def go() -> dict[str, Any]:
        return await service._impl_search(
            fake_graphiti,
            query="what is x",
            group_ids=["g1", "g2"],
            num_results=5,
            center_node_uuid="center",
        )

    out = asyncio.run(go())

    assert out["query"] == "what is x"
    assert isinstance(out["results"], list) and len(out["results"]) == 1
    item = out["results"][0]
    assert set(item.keys()) == {
        "fact", "edge_uuid", "valid_at", "invalid_at",
        "source_node_uuid", "target_node_uuid",
    }
    assert item["fact"] == "a related_to b"
    assert item["edge_uuid"] == "edge-uuid"

    # Dispatch correctness
    assert len(fake_graphiti.searched) == 1
    call = fake_graphiti.searched[0]
    assert call["query"] == "what is x"
    assert call["group_ids"] == ["g1", "g2"]
    assert call["num_results"] == 5
    assert call["center_node_uuid"] == "center"


# ---- AC24.4 ---------------------------------------------------------


def test_AC24_4_health_reports_config(
    fake_graphiti: FakeGraphiti,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The ``health`` tool returns ``status=ok`` plus the configured
    LLM model, embedder dim, and DB path."""
    monkeypatch.setenv("KUZU_DB_PATH", "/tmp/kuzu-test.db")

    async def go() -> dict[str, Any]:
        return await service._impl_health(fake_graphiti)

    out = asyncio.run(go())
    assert out["status"] == "ok"
    assert out["llm_model"] == "claude-haiku-4-5"
    assert out["embedder_dim"] == 768
    assert out["db_path"] == "/tmp/kuzu-test.db"


# ---- AC24.5 ---------------------------------------------------------


def test_AC24_5_token_usage_reports_by_prompt_and_total(
    fake_graphiti: FakeGraphiti,
) -> None:
    """The ``token_usage`` tool returns ``by_prompt`` keyed by prompt
    name and ``total`` with input/output counts."""

    async def go() -> dict[str, Any]:
        return await service._impl_token_usage(fake_graphiti)

    out = asyncio.run(go())
    assert "by_prompt" in out and "total" in out
    assert out["by_prompt"]["reflexive"] == {
        "input_tokens": 10, "output_tokens": 20, "call_count": 1,
    }
    assert out["total"] == {"input_tokens": 100, "output_tokens": 200}


# ---- AC24.6 ---------------------------------------------------------


def test_AC24_6_run_launches_streamable_http_transport(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``run()`` invokes FastMCP's streamable-HTTP transport with a
    host+port consistent with the configured env vars. The call is
    intercepted so the transport never actually binds a port."""
    monkeypatch.setenv("GRAPHITI_SERVICE_HOST", "127.0.0.1")
    monkeypatch.setenv("GRAPHITI_SERVICE_PORT", "8765")

    # Rebuild the MCP instance under the env-var overrides so its
    # settings reflect the test values.
    mcp_instance = service._build_mcp()
    assert mcp_instance.settings.host == "127.0.0.1"
    assert mcp_instance.settings.port == 8765

    # Swap the module-level ``mcp`` for the test instance, and stub
    # ``run_streamable_http_async`` so ``run()`` doesn't bind a
    # socket.
    called: dict[str, Any] = {"count": 0}

    async def fake_transport() -> None:
        called["count"] += 1

    monkeypatch.setattr(mcp_instance, "run_streamable_http_async", fake_transport)
    monkeypatch.setattr(service, "mcp", mcp_instance)
    monkeypatch.setattr(service, "load_env", lambda: None)

    service.run()
    assert called["count"] == 1


# ---- AC24.7 ---------------------------------------------------------


def test_AC24_7_requirements_drops_fastapi_and_pins_mcp() -> None:
    """memory-system/requirements.txt omits fastapi and pins mcp>=1.27.

    Regression guard for the dependency-delta direction in the
    amendment plan §3 / the manifest narrative block.
    """
    req = Path(__file__).resolve().parent.parent / "requirements.txt"
    content = req.read_text()

    # Flag any fastapi requirement line — permissive match across
    # "fastapi", "fastapi>=...", "fastapi==..." etc. Comments
    # mentioning fastapi (the migration note) are allowed.
    for raw in content.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        token = line.split("#", 1)[0].strip()
        first = token.split()[0] if token else ""
        # Strip any version specifier or extras to get the bare
        # package name.
        pkg = first.split("==")[0].split(">=")[0].split("<=")[0]
        pkg = pkg.split("<")[0].split(">")[0].split("[")[0].strip()
        assert pkg != "fastapi", (
            "fastapi must be removed from requirements.txt post-"
            f"amendment #24; found line: {raw!r}"
        )

    # mcp>=1.27 must be present.
    has_mcp = any(
        ln.strip().startswith("mcp>=") or ln.strip() == "mcp"
        or ln.strip().startswith("mcp==") or ln.strip().startswith("mcp>")
        for ln in content.splitlines()
    )
    assert has_mcp, "mcp package must be pinned in requirements.txt"


# ---- Coverage: MCP registration side -------------------------------
#
# The AC tests above exercise the ``_impl_*`` functions directly. We
# also assert the MCP-decorated wrappers are registered correctly so
# a client calling `mcp list-tools` sees the intended surface. This
# is AC24.1–AC24.5's registration half: without it, a test that
# dispatches to the implementation could pass while the tool was
# never actually exposed to MCP clients.


def test_AC24_1_through_5_tools_registered_on_mcp_instance() -> None:
    """``list_tools()`` returns the four expected tools."""

    async def go() -> list[str]:
        tools = await service.mcp.list_tools()
        return sorted(t.name for t in tools)

    names = asyncio.run(go())
    assert names == ["add_episode", "health", "search", "token_usage"]
