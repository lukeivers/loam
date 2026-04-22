"""Reconcile-on-recovery drain worker (Amendment 1).

Activated by the supervisor when the memory sidecar transitions back
into ``normal``. Reads pending entries from the staging store in strict
FIFO order, forwards them to the sidecar via a caller-supplied
``forward`` callable, and deletes each entry only on confirmed landing.

Critical invariants (see research §Q4):

1. **FIFO preserved.** `id ASC` drain order matches staging order.
2. **Confirmed-landing delete.** Entries are removed only after the
   sidecar accepts the write. A crash between sidecar-accept and
   delete is tolerated by the client-side UUID: on re-attempt, the
   sidecar deduplicates on ``episode_uuid``.
3. **Drain failure never silently drops.** After
   ``MAX_FORWARD_ATTEMPTS`` the entry is moved to the poison table
   (preserved for user review) and the supervisor is signalled to
   open an escalation.
4. **Idempotent.** Calling ``DrainWorker.drain`` repeatedly is safe;
   every call reads the current pending set and drains what it can.

Error codes reserved to hands-off-lifecycle:
- ``-32096`` ``drain_poison_accumulation`` (raised on poison overflow)
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

from .staging import StagedEntry, StagingStore


MAX_FORWARD_ATTEMPTS = 3
DEFAULT_DRAIN_BATCH_SIZE = 100
DEFAULT_POISON_SOFT_CAP = 10


# ---- forward contract ------------------------------------------------


ForwardFn = Callable[[StagedEntry], Awaitable["ForwardResult"]]


@dataclass(frozen=True)
class ForwardResult:
    """Outcome of forwarding one entry to the sidecar."""

    ok: bool
    error: str | None = None
    episode_uuid: str | None = None  # the sidecar-confirmed UUID


# ---- drain report ---------------------------------------------------


@dataclass
class DrainReport:
    """Per-call drain report."""

    forwarded: int = 0
    poisoned: int = 0
    remaining: int = 0
    failures: int = 0
    poison_overflow: bool = False
    processed_ids: list[int] = field(default_factory=list)


# ---- drain worker ----------------------------------------------------


class DrainWorker:
    """Drains pending staged writes to the sidecar, one batch at a time.

    Construction decouples drain from the sidecar HTTP client; tests
    inject a fake ``forward`` to exercise FIFO / idempotence / poison
    behaviour without a live sidecar.
    """

    def __init__(
        self,
        staging: StagingStore,
        forward: ForwardFn,
        *,
        batch_size: int = DEFAULT_DRAIN_BATCH_SIZE,
        poison_soft_cap: int = DEFAULT_POISON_SOFT_CAP,
        escalation_sink: Callable[[str, dict[str, Any]], Awaitable[None]] | None = None,
    ) -> None:
        self._staging = staging
        self._forward = forward
        self._batch_size = int(batch_size)
        self._poison_soft_cap = int(poison_soft_cap)
        self._escalation = escalation_sink
        self._lock = asyncio.Lock()

    async def drain(self, *, max_entries: int | None = None) -> DrainReport:
        """Drain up to `max_entries` (or batch_size) pending entries.

        Returns a report; call again to continue. Safe to call
        repeatedly — the lock serialises concurrent drains.
        """
        report = DrainReport()
        limit = int(max_entries or self._batch_size)
        async with self._lock:
            pending = self._staging.list_pending(limit=limit)
            for entry in pending:
                result = await self._forward_one(entry)
                report.processed_ids.append(entry.id)
                if result.ok:
                    self._staging.mark_forwarded(entry.id)
                    report.forwarded += 1
                else:
                    report.failures += 1
                    new_attempts = self._staging.mark_failure(
                        entry.id, error=result.error or "unknown"
                    )
                    if new_attempts >= MAX_FORWARD_ATTEMPTS:
                        self._staging.move_to_poison(entry.id)
                        report.poisoned += 1
            report.remaining = self._staging.size()
            poison_count = self._staging.poison_size()
            if poison_count > self._poison_soft_cap:
                report.poison_overflow = True
                if self._escalation is not None:
                    await self._escalation(
                        "memory.drain.poison_accumulation",
                        {
                            "poison_count": poison_count,
                            "soft_cap": self._poison_soft_cap,
                        },
                    )
        return report

    async def drain_until_empty(
        self, *, max_iters: int = 1000
    ) -> DrainReport:
        """Drain repeatedly until staging is empty or a failure sets
        no-forward-progress (every entry in the last batch moved to
        poison or kept failing). Used on transition to `normal`."""
        total = DrainReport()
        for _ in range(int(max_iters)):
            r = await self.drain()
            total.forwarded += r.forwarded
            total.poisoned += r.poisoned
            total.failures += r.failures
            total.processed_ids.extend(r.processed_ids)
            total.remaining = r.remaining
            total.poison_overflow = total.poison_overflow or r.poison_overflow
            if r.remaining == 0:
                break
            if r.forwarded == 0 and r.poisoned == 0 and r.failures == 0:
                # Truly no progress (nothing even tried) — stop.
                break
        return total

    async def _forward_one(self, entry: StagedEntry) -> ForwardResult:
        try:
            return await self._forward(entry)
        except Exception as e:  # catch broadly — forward may raise any
            return ForwardResult(ok=False, error=f"{type(e).__name__}: {e}")
