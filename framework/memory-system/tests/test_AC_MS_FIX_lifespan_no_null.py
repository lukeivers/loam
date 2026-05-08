"""Memory-sidecar-recovery — lifespan-leak fix + reference_time schema migration.

Three outcome-shaped tests covering AC.MS-FIX.1 / .2 / .3 from
``docs/plans/memory-sidecar-recovery.md`` §4:

  - AC.MS-FIX.1: lifespan no longer nulls ``service._graphiti`` on
    session close. After ``async with service.lifespan(server):``
    exits, ``service._graphiti`` is still populated and ``close()``
    was called exactly once.
  - AC.MS-FIX.2: ``ensure_reference_time_column`` adds the
    ``reference_time`` column to ``RelatesToNode_`` idempotently.
    Two calls in a row do not raise.
  - AC.MS-FIX.3: ``service._ensure_graphiti`` routes through
    ``prepare_graphiti(...)`` rather than calling
    ``build_indices_and_constraints()`` directly, so both schema
    migrations fire on every cold-start.

The first two tests use mock / in-process kuzu fixtures (no real
graphiti / Ollama / claude); the third asserts the wiring at the
function level by source-grep + a runtime exercise.
"""

from __future__ import annotations

import asyncio
import inspect
from pathlib import Path
from typing import Any

import pytest

from src import service
from src.retention import (
    ENSURE_REFERENCE_TIME_COLUMN_CQL,
    ensure_reference_time_column,
)


# ---- AC.MS-FIX.1 ----------------------------------------------------


def test_AC_MS_FIX_1_lifespan_does_not_null_graphiti_on_exit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The lifespan's ``finally`` block calls ``close()`` but does NOT
    set ``service._graphiti = None``. Post-fix, the module global stays
    populated across lifespan exits — the driver lives for the process
    lifetime.

    Pre-fix (the defect this test guards against): the ``finally``
    block set ``_graphiti = None``, defeating ``_ensure_graphiti()``'s
    idempotency guard. FastMCP routes the user lifespan to
    ``MCPServer.run``, which is invoked PER MCP session by
    ``StreamableHTTPSessionManager``. Each session close therefore
    nulled the global, the next session re-built the driver, opening
    another ``kuzu.Database`` against the same on-disk file. Kuzu's
    8 TiB virtual mmap reservation accumulated per session until macOS
    VA fragmentation failed mmap; the sidecar entered a permanent
    stuck state returning 503 forever.
    """

    class _FakeLLM:
        model = "fake"

    class _FakeEmbedder:
        class _Cfg:
            embedding_dim = 1
        config = _Cfg()

    class _FakeGraphiti:
        def __init__(self) -> None:
            self.llm_client = _FakeLLM()
            self.embedder = _FakeEmbedder()
            self.close_calls = 0
            self.build_calls = 0

        async def build_indices_and_constraints(self) -> None:
            self.build_calls += 1

        async def close(self) -> None:
            self.close_calls += 1

    fake = _FakeGraphiti()

    async def fake_make() -> Any:
        return fake

    async def fake_prepare(g: Any) -> None:
        await g.build_indices_and_constraints()

    monkeypatch.setattr(service, "make_graphiti", fake_make)
    monkeypatch.setattr(service, "load_env", lambda: None)
    monkeypatch.setattr(service, "prepare_graphiti", fake_prepare)
    monkeypatch.setattr(service, "_graphiti", None)

    async def exercise() -> None:
        async with service.lifespan(service.mcp) as ctx:
            assert ctx["graphiti"] is fake
            assert service._graphiti is fake
            assert fake.close_calls == 0
        # Post-exit invariant: close ran but module global stays
        # populated. Pre-fix, this would have been None (the leak).
        assert fake.close_calls == 1
        assert service._graphiti is fake

    asyncio.run(exercise())

    # Cross-session simulation: a second lifespan enter (the per-session
    # invocation FastMCP performs) should observe the populated global
    # and skip the rebuild. _ensure_graphiti's `if _graphiti is not
    # None: return` guard is what makes this work.
    construct_calls_2 = 0

    async def counted_make() -> Any:
        nonlocal construct_calls_2
        construct_calls_2 += 1
        return fake

    monkeypatch.setattr(service, "make_graphiti", counted_make)

    async def exercise_again() -> None:
        async with service.lifespan(service.mcp):
            assert service._graphiti is fake

    asyncio.run(exercise_again())
    assert construct_calls_2 == 0, (
        "second lifespan enter must not rebuild Graphiti — the "
        "_ensure_graphiti guard depends on _graphiti staying populated "
        "across lifespan exits"
    )
    assert fake.close_calls == 2, (
        "close still fires on each lifespan exit (the inner side-"
        "effects, if any, run every time)"
    )


# ---- AC.MS-FIX.2 ----------------------------------------------------


def test_AC_MS_FIX_2_reference_time_migration_idempotent(
    tmp_path: Path,
) -> None:
    """``ensure_reference_time_column`` adds the ``reference_time``
    column to ``RelatesToNode_`` and is safe to call repeatedly.

    Simulates the on-disk-DB-from-older-graphiti-core state by creating
    the ``RelatesToNode_`` table WITHOUT ``reference_time``, then calls
    the migration helper and asserts the column exists. A second call
    must not raise.
    """
    import kuzu

    db_path = str(tmp_path / "kuzu_db_test")
    # Small buffer pool so the test doesn't allocate gigabytes —
    # 32 MiB is plenty for the schema-only round-trip.
    db = kuzu.Database(db_path, buffer_pool_size=32 * 1024 * 1024)
    conn = kuzu.Connection(db)

    # Create RelatesToNode_ WITHOUT reference_time, simulating the
    # pre-graphiti-core-0.28.x schema.
    conn.execute(
        """
        CREATE NODE TABLE IF NOT EXISTS RelatesToNode_ (
            uuid STRING PRIMARY KEY,
            group_id STRING,
            created_at TIMESTAMP,
            name STRING,
            fact STRING
        )
        """
    )

    # Wrap the kuzu connection in a minimal async-driver shim so the
    # helper's `await driver.execute_query(...)` shape works.
    class _SyncDriverShim:
        def __init__(self, conn: Any) -> None:
            self._conn = conn

        async def execute_query(self, query: str) -> Any:
            return self._conn.execute(query)

    driver = _SyncDriverShim(conn)

    async def go() -> None:
        await ensure_reference_time_column(driver)
        # Idempotent: second call must not raise.
        await ensure_reference_time_column(driver)

    asyncio.run(go())

    # Verify the column exists by attempting an INSERT that uses it.
    # Kuzu raises a Binder exception if the column is missing.
    conn.execute(
        "CREATE (n:RelatesToNode_ {uuid: 't1', group_id: 'g', "
        "name: 'n', fact: 'f', reference_time: timestamp('2026-01-01')})"
    )
    rows = conn.execute(
        "MATCH (n:RelatesToNode_ {uuid: 't1'}) RETURN n.reference_time"
    )
    # Kuzu's QueryResult is iterable; pull the row out.
    row = list(rows)
    assert row, "expected one row for the inserted RelatesToNode_"


def test_AC_MS_FIX_2_migration_cql_targets_relates_to_node_reference_time() -> None:
    """The CQL constant names the right table + column + idempotency
    flag. Source-grep guard against accidental regression of the
    migration shape."""
    cql = ENSURE_REFERENCE_TIME_COLUMN_CQL.replace("\n", " ")
    assert "ALTER TABLE" in cql
    assert "RelatesToNode_" in cql
    assert "ADD IF NOT EXISTS" in cql
    assert "reference_time" in cql
    assert "TIMESTAMP" in cql


# ---- AC.MS-FIX.3 ----------------------------------------------------


def test_AC_MS_FIX_3_ensure_graphiti_routes_through_prepare_graphiti() -> None:
    """``service._ensure_graphiti``'s body calls ``prepare_graphiti``
    rather than ``build_indices_and_constraints()`` directly, so both
    schema migrations (retention_class + reference_time) fire on every
    cold-start.

    Source-grep + signature check: the function names ``prepare_graphiti``
    in its body and does NOT name ``build_indices_and_constraints``
    directly.
    """
    src = inspect.getsource(service._ensure_graphiti)
    assert "prepare_graphiti(" in src, (
        "_ensure_graphiti must route through prepare_graphiti so both "
        "schema migrations fire at sidecar startup"
    )

    # Strip the docstring to inspect only the executable body — the
    # docstring may reference build_indices_and_constraints in
    # historical narrative without that being a direct call.
    body_src = src.split('"""', 2)[-1] if src.count('"""') >= 2 else src
    # Negative: the executable body must NOT call
    # build_indices_and_constraints directly (the pre-fix shape).
    # prepare_graphiti owns that call internally.
    assert "build_indices_and_constraints" not in body_src, (
        "_ensure_graphiti's executable body must NOT call "
        "build_indices_and_constraints directly post-fix — "
        "prepare_graphiti owns the call"
    )


def test_AC_MS_FIX_3_ensure_graphiti_runtime_exercise(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Runtime check: a single ``_ensure_graphiti`` call invokes
    ``prepare_graphiti`` exactly once, and a second call (idempotent
    re-entry) is a no-op (does NOT call prepare again, per the
    ``if _graphiti is not None`` guard).
    """
    prepare_calls = 0

    class _FakeGraphiti:
        async def build_indices_and_constraints(self) -> None:
            return None

        async def close(self) -> None:
            return None

    fake = _FakeGraphiti()

    async def fake_make() -> Any:
        return fake

    async def fake_prepare(g: Any) -> None:
        nonlocal prepare_calls
        prepare_calls += 1

    monkeypatch.setattr(service, "make_graphiti", fake_make)
    monkeypatch.setattr(service, "load_env", lambda: None)
    monkeypatch.setattr(service, "prepare_graphiti", fake_prepare)
    monkeypatch.setattr(service, "_graphiti", None)

    async def go() -> None:
        await service._ensure_graphiti()
        await service._ensure_graphiti()  # idempotent re-entry

    asyncio.run(go())
    assert prepare_calls == 1, (
        "prepare_graphiti must fire exactly once across two "
        "_ensure_graphiti calls (idempotency guard)"
    )
