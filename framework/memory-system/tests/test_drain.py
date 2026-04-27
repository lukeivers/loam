"""Drain worker tests (Amendment 1 — hands-off-lifecycle).

Covers H-criteria from proposal §5.3:

    H12 — drain forwards FIFO; entries clear only on confirmed landing
    H14 — drain failure → supervisor escalation path (via escalation_sink)

Also covers: poison-pill flow (entries that fail MAX_FORWARD_ATTEMPTS
move to poison rather than being silently dropped), idempotent replay
via client UUID, and drain-until-empty convergence.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from src.drain import (
    DEFAULT_POISON_SOFT_CAP,
    DrainWorker,
    ForwardResult,
    MAX_FORWARD_ATTEMPTS,
)
from src.staging import StagedEntry, StagingStore


@pytest.fixture
def db(tmp_path: Path) -> StagingStore:
    return StagingStore(tmp_path / "staging.sqlite")


# ---- H12 — FIFO drain + confirmed-landing delete --------------------


@pytest.mark.asyncio
async def test_H12_drain_forwards_in_FIFO_order(db: StagingStore) -> None:
    seen: list[str] = []

    async def forward(entry: StagedEntry) -> ForwardResult:
        seen.append(entry.payload["name"])
        return ForwardResult(ok=True, episode_uuid=entry.episode_uuid)

    for name in ("a", "b", "c"):
        db.stage({"name": name, "body": "b", "group_id": "s"})
    worker = DrainWorker(db, forward)
    report = await worker.drain()
    assert seen == ["a", "b", "c"]
    assert report.forwarded == 3
    assert db.size() == 0


@pytest.mark.asyncio
async def test_H12_entry_cleared_only_on_confirmed_landing(db: StagingStore) -> None:
    async def forward_fails(entry: StagedEntry) -> ForwardResult:
        return ForwardResult(ok=False, error="sidecar rejected")

    e = db.stage({"name": "x", "body": "b", "group_id": "s"})
    worker = DrainWorker(db, forward_fails)
    await worker.drain()
    # Entry is still present; attempts incremented.
    assert db.size() == 1
    pending = db.list_pending()
    assert pending[0].id == e.id
    assert pending[0].forward_attempts == 1


@pytest.mark.asyncio
async def test_H12_drain_resumes_from_partial_success(db: StagingStore) -> None:
    # First call succeeds, next two fail — FIFO preserved on re-drain.
    call_count = {"n": 0}

    async def forward(entry: StagedEntry) -> ForwardResult:
        call_count["n"] += 1
        ok = call_count["n"] <= 1
        return ForwardResult(ok=ok, error=None if ok else "boom")

    db.stage({"name": "a", "body": "b", "group_id": "s"})
    db.stage({"name": "b", "body": "b", "group_id": "s"})
    db.stage({"name": "c", "body": "b", "group_id": "s"})
    worker = DrainWorker(db, forward)
    report = await worker.drain()
    assert report.forwarded == 1
    # Remaining should be b and c in FIFO order.
    pending = db.list_pending()
    assert [p.payload["name"] for p in pending] == ["b", "c"]


# ---- H14 — drain failure surfaces via escalation sink ---------------


@pytest.mark.asyncio
async def test_H14_poison_accumulation_triggers_escalation(db: StagingStore) -> None:
    escalations: list[tuple[str, dict[str, Any]]] = []

    async def escalation_sink(cls: str, data: dict[str, Any]) -> None:
        escalations.append((cls, data))

    async def always_fail(entry: StagedEntry) -> ForwardResult:
        return ForwardResult(ok=False, error="rejected")

    # Soft cap of 1 so two poisoned entries triggers overflow.
    worker = DrainWorker(
        db,
        always_fail,
        poison_soft_cap=1,
        escalation_sink=escalation_sink,
    )
    for i in range(2):
        db.stage(
            {"name": f"bad-{i}", "body": "b", "group_id": "s"},
            episode_uuid=f"uid-{i}",
        )
    # Three drain iterations: attempt 1, 2, 3 → move to poison.
    for _ in range(MAX_FORWARD_ATTEMPTS):
        await worker.drain()
    assert db.size() == 0
    assert db.poison_size() == 2
    # Escalation fired on poison overflow.
    assert any(cls == "memory.drain.poison_accumulation" for cls, _ in escalations)


# ---- idempotent replay via client UUID ------------------------------


@pytest.mark.asyncio
async def test_client_uuid_preserved_through_drain(db: StagingStore) -> None:
    seen_uuids: list[str] = []

    async def forward(entry: StagedEntry) -> ForwardResult:
        seen_uuids.append(entry.episode_uuid)
        return ForwardResult(ok=True, episode_uuid=entry.episode_uuid)

    db.stage(
        {"name": "x", "body": "b", "group_id": "s"}, episode_uuid="client-uuid-A"
    )
    worker = DrainWorker(db, forward)
    await worker.drain()
    assert seen_uuids == ["client-uuid-A"]


# ---- drain-until-empty convergence ----------------------------------


@pytest.mark.asyncio
async def test_drain_until_empty_drains_everything(db: StagingStore) -> None:
    async def forward(entry: StagedEntry) -> ForwardResult:
        return ForwardResult(ok=True, episode_uuid=entry.episode_uuid)

    for i in range(250):
        db.stage({"name": f"n{i}", "body": "b", "group_id": "s"})
    worker = DrainWorker(db, forward, batch_size=100)
    report = await worker.drain_until_empty()
    assert report.forwarded == 250
    assert db.size() == 0


@pytest.mark.asyncio
async def test_drain_until_empty_stops_on_no_progress(db: StagingStore) -> None:
    async def forward_fails(entry: StagedEntry) -> ForwardResult:
        return ForwardResult(ok=False, error="boom")

    # One entry; never succeeds. drain_until_empty must stop rather
    # than loop forever.
    db.stage({"name": "x", "body": "b", "group_id": "s"})
    worker = DrainWorker(db, forward_fails)
    report = await worker.drain_until_empty(max_iters=5)
    # Expect: 3 attempts → poison → remaining=0 → loop exits.
    assert db.size() == 0
    assert db.poison_size() == 1
    assert report.poisoned == 1


# ---- forward callable exceptions never kill the drain --------------


@pytest.mark.asyncio
async def test_forward_raising_exception_is_caught_as_failure(
    db: StagingStore,
) -> None:
    async def forward_raises(entry: StagedEntry) -> ForwardResult:
        raise RuntimeError("connection reset")

    db.stage({"name": "x", "body": "b", "group_id": "s"})
    worker = DrainWorker(db, forward_raises)
    report = await worker.drain()
    assert report.failures == 1
    # Entry still present; attempts=1.
    pending = db.list_pending()
    assert pending[0].forward_attempts == 1
