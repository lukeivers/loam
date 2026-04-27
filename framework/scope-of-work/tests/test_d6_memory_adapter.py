"""D6 — memory-mock retirement integration test.

Acceptance (brief D6):
- A `RealScopeSourceAdapter` wraps the primitive to match memory's
  existing `ScopeSource` protocol.
- `MemoryAPI` constructor accepts the adapter via a one-line change.
- An integration test creates a scope via the primitive, ingests memory
  under that scope_id, searches memory and finds the entry, and rejects
  an unknown scope_id with a clear error.
- No memory-side rewrite beyond the one wiring line.

Memory-system lives at ../memory-system. We load its modules under
aliased names to avoid colliding with our own `src` package on
sys.path. Running this against the live Graphiti+Kuzu+Anthropic+Ollama
stack is gated on `RUN_LIVE_MEMORY=1` (the live test imports the real
graphiti and requires Ollama to be up).
"""

from __future__ import annotations

import asyncio
import importlib.util
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from src.adapter import RealScopeSourceAdapter
from src.runtime import ScopeRuntime
from tests.conftest import make_spec


MEMORY_PATH = Path(__file__).resolve().parents[2] / "memory-system"
MEMORY_SRC = MEMORY_PATH / "src"


def _ensure_memory_third_party_on_path() -> None:
    """Memory's modules import graphiti_core; pull memory's venv
    site-packages onto sys.path so loading succeeds. This does not
    affect the primitive's own dependency footprint — the primitive
    itself never imports graphiti."""
    site = MEMORY_PATH / ".venv" / "lib" / "python3.13" / "site-packages"
    if site.is_dir() and str(site) not in sys.path:
        sys.path.append(str(site))


def _load_memory_modules() -> tuple[ModuleType, ModuleType]:
    """Load memory-system's src.memory and src.retention as `mem_*` aliases.

    Memory-system uses `from .config import section` etc., so we need to
    register the package + submodules under a fresh package name.
    """
    _ensure_memory_third_party_on_path()
    pkg_name = "mem_pkg"
    if pkg_name not in sys.modules:
        # Create a synthetic package rooted at memory-system/src/.
        pkg_spec = importlib.util.spec_from_file_location(
            pkg_name,
            MEMORY_SRC / "__init__.py",
            submodule_search_locations=[str(MEMORY_SRC)],
        )
        pkg = importlib.util.module_from_spec(pkg_spec)
        sys.modules[pkg_name] = pkg
        pkg_spec.loader.exec_module(pkg)

    def _load(submod: str) -> ModuleType:
        full = f"{pkg_name}.{submod}"
        if full in sys.modules:
            return sys.modules[full]
        spec = importlib.util.spec_from_file_location(
            full, MEMORY_SRC / f"{submod}.py"
        )
        m = importlib.util.module_from_spec(spec)
        sys.modules[full] = m
        spec.loader.exec_module(m)
        return m

    # Pre-load the modules memory.memory imports.
    _load("config")
    _load("ephemerality")
    _load("scope")
    _load("retention")
    _load("temporal")
    _load("observability")
    mem = _load("memory")
    ret = sys.modules[f"{pkg_name}.retention"]
    return mem, ret


# ---- minimal Graphiti stub --------------------------------------------


@dataclass
class _StubEpisode:
    uuid: str


@dataclass
class _StubAddResult:
    episode: _StubEpisode
    nodes: list = field(default_factory=list)
    edges: list = field(default_factory=list)


@dataclass
class _StubEdge:
    uuid: str
    fact: str
    source_node_uuid: str = "src"
    target_node_uuid: str = "tgt"
    valid_at: Any = None
    invalid_at: Any = None


class _StubTokenTracker:
    def get_usage(self):
        return {}


class _StubLLMClient:
    model = "stub-claude"
    token_tracker = _StubTokenTracker()


class _StubDriver:
    def __init__(self):
        self._episodes: list[dict] = []

    async def execute_query(self, cql: str, **kwargs):
        if "scope_id" in kwargs:
            sid = kwargs["scope_id"]
            rows = [
                {
                    "uuid": ep["uuid"],
                    "name": ep["name"],
                    "created_at": ep["created_at"],
                    "retention_class": ep.get("retention_class"),
                }
                for ep in self._episodes
                if ep["group_id"] == sid
            ]
            return rows, None, None
        return [], None, None


class _StubGraphiti:
    def __init__(self):
        self.driver = _StubDriver()
        self.llm_client = _StubLLMClient()
        self.ingested: list[dict] = []
        self.searches: list[dict] = []

    async def add_episode(
        self,
        *,
        name: str,
        episode_body: str,
        source_description: str,
        reference_time: datetime,
        source: Any,
        group_id: str,
    ) -> _StubAddResult:
        ep_uuid = f"ep-{len(self.ingested) + 1}"
        rec = {
            "uuid": ep_uuid,
            "name": name,
            "body": episode_body,
            "group_id": group_id,
            "created_at": reference_time.isoformat(),
        }
        self.ingested.append(rec)
        self.driver._episodes.append(rec)
        return _StubAddResult(episode=_StubEpisode(uuid=ep_uuid))

    async def search(
        self,
        *,
        query: str,
        center_node_uuid: str | None = None,
        group_ids: list[str] | None = None,
        num_results: int = 10,
        search_filter: Any = None,
    ) -> list[_StubEdge]:
        self.searches.append(
            {"query": query, "group_ids": group_ids, "num_results": num_results}
        )
        out: list[_StubEdge] = []
        for ep in self.ingested:
            if group_ids and ep["group_id"] not in group_ids:
                continue
            out.append(_StubEdge(uuid=f"edge-{ep['uuid']}", fact=ep["body"][:80]))
        return out[:num_results]


async def _no_op_apply_plan(driver, *, episode_uuid, plan):
    return None


@pytest.fixture
async def memory_with_real_scopes(tmp_path, monkeypatch):
    db = tmp_path / "scope.db"
    rt = ScopeRuntime(db_path=db, pending_extension_dir=tmp_path / "pending")
    mem_module, ret_module = _load_memory_modules()
    monkeypatch.setattr(ret_module, "apply_plan", _no_op_apply_plan)

    stub_graphiti = _StubGraphiti()
    adapter = RealScopeSourceAdapter(rt)
    api = mem_module.MemoryAPI(stub_graphiti, scope_source=adapter)
    yield api, rt, stub_graphiti
    rt.close()


# ---- adapter-shape tests ---------------------------------------------


async def test_adapter_register_unknown_scope_raises(tmp_path):
    rt = ScopeRuntime(db_path=tmp_path / "s.db", pending_extension_dir=tmp_path / "p")
    adapter = RealScopeSourceAdapter(rt)
    with pytest.raises(KeyError) as excinfo:
        adapter.register_scope("does-not-exist")
    assert "scopes must be created" in str(excinfo.value)
    rt.close()


async def test_adapter_get_scope_returns_record_for_real_scope(tmp_path):
    rt = ScopeRuntime(db_path=tmp_path / "s.db", pending_extension_dir=tmp_path / "p")
    proj = await rt.create(make_spec(goal="anchored", owner_persona="eve"))
    adapter = RealScopeSourceAdapter(rt)
    rec = adapter.get_scope(proj.scope_id)
    assert rec is not None
    assert rec.scope_id == proj.scope_id
    assert rec.description == "anchored"
    rt.close()


async def test_adapter_list_scopes_returns_all(tmp_path):
    rt = ScopeRuntime(db_path=tmp_path / "s.db", pending_extension_dir=tmp_path / "p")
    a = await rt.create(make_spec(goal="a"))
    b = await rt.create(make_spec(goal="b"))
    adapter = RealScopeSourceAdapter(rt)
    ids = {r.scope_id for r in adapter.list_scopes()}
    assert ids == {a.scope_id, b.scope_id}
    rt.close()


# ---- end-to-end memory wiring (stub Graphiti) ------------------------


async def test_memory_ingest_under_real_scope_id(memory_with_real_scopes):
    api, rt, stub = memory_with_real_scopes
    proj = await rt.create(make_spec(goal="research engagement"))
    sid = proj.scope_id

    result = await api.ingest(
        body="Renji Okamoto presented the Tideglass migration plan.",
        name="meeting-2027-05-30",
        scope_id=sid,
    )
    assert result.episode_uuid is not None
    assert stub.ingested[-1]["group_id"] == sid


async def test_memory_search_filters_by_real_scope_id(memory_with_real_scopes):
    api, rt, stub = memory_with_real_scopes
    a = await rt.create(make_spec(goal="halcyon"))
    b = await rt.create(make_spec(goal="rookery"))

    await api.ingest(body="Halcyon Cartography migrated.", name="h1", scope_id=a.scope_id)
    await api.ingest(body="Rookery Holdings reporting reorg.", name="r1", scope_id=b.scope_id)

    hits = await api.search("Halcyon", scope_ids=[a.scope_id])
    assert len(hits) >= 1
    assert stub.searches[-1]["group_ids"] == [a.scope_id]


async def test_memory_ingest_unknown_scope_id_rejects(memory_with_real_scopes):
    api, rt, stub = memory_with_real_scopes
    with pytest.raises(KeyError) as excinfo:
        await api.ingest(body="orphan", name="x", scope_id="bogus-scope")
    assert "bogus-scope" in str(excinfo.value)


# ---- live integration (opt-in) ---------------------------------------


@pytest.mark.skipif(
    os.environ.get("RUN_LIVE_MEMORY") != "1",
    reason="set RUN_LIVE_MEMORY=1 to run the live Graphiti integration",
)
async def test_live_memory_round_trip(tmp_path):
    """Optional live integration. See module docstring."""
    mem_module, _ = _load_memory_modules()
    factory_spec = importlib.util.spec_from_file_location(
        "mem_pkg.factory", MEMORY_SRC / "factory.py"
    )
    factory = importlib.util.module_from_spec(factory_spec)
    sys.modules["mem_pkg.factory"] = factory
    factory_spec.loader.exec_module(factory)

    factory.load_env()
    db = tmp_path / "scope.db"
    rt = ScopeRuntime(db_path=db, pending_extension_dir=tmp_path / "pending")
    proj = await rt.create(make_spec(goal="d6 live integration"))
    adapter = RealScopeSourceAdapter(rt)

    g = await factory.make_graphiti(db_path=str(tmp_path / "kuzu_d6"))
    await g.build_indices_and_constraints()
    api = mem_module.MemoryAPI(g, scope_source=adapter)

    body = (
        "On 2027-08-25 Ines Saralegui kicked off the Tideglass engagement "
        "with Anders Vrelich at a budget of 110,000 GBP."
    )
    res = await api.ingest(body=body, name="live-d6", scope_id=proj.scope_id)
    assert res.episode_uuid is not None

    hits = await api.search("Tideglass", scope_ids=[proj.scope_id])
    assert any("Tideglass" in h.fact or "Ines" in h.fact for h in hits)

    with pytest.raises(KeyError):
        await api.ingest(body="orphan", name="orphan", scope_id="not-a-real-scope")

    await g.close()
    rt.close()
