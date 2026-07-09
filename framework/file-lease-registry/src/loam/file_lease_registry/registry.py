# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""File-lease registry + admission throttle (WS-B1).

A lease is a set of file globs granted to one dispatch at grant time —
before any worktree exists — and released on terminal state (complete /
fail / artifact-probe-dead).  The registry refuses a grant whose globs
overlap a live lease (AC.LEASE.1), refuses a second dependency-manifest
touch while one is held (AC.LEASE.2), refuses grants beyond a concurrent
ceiling (AC.LEASE.3), and reaps leases whose holder is artifact-probe-
dead (AC.LEASE.4/5).  State is a single on-disk JSON file; grant /
release / reap are serialized so the overlap check and the write are
atomic (AC.LEASE.7).  Per-machine scope only — cross-operator collisions
are the CODEOWNERS + merge-queue's job, never a distributed lease store.
"""

from __future__ import annotations

import fcntl
import json
import os
import threading
import time
import uuid
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

from ._liveness import probe_liveness
from .overlap import globs_conflict

# The one reserved exclusive key for the dependency-manifest set: any
# dispatch touching it is single-writer regardless of its other globs.
DEPS_MANIFEST_KEY = "__deps_manifest__"

# Patterns that constitute the dependency-manifest set (one shared graph
# — a lockfile/package.json/schema change is not parallelisable).
DEFAULT_DEPS_PATTERNS: tuple[str, ...] = (
    "package.json",
    "**/package.json",
    "package-lock.json",
    "**/package-lock.json",
    "yarn.lock",
    "**/yarn.lock",
    "pnpm-lock.yaml",
    "**/pnpm-lock.yaml",
    "poetry.lock",
    "**/poetry.lock",
    "Cargo.lock",
    "**/Cargo.lock",
    "*.lock",
    "db/schema/**",
    "**/migrations/**",
)


@dataclass(frozen=True)
class Lease:
    """A granted claim over a set of globs for one dispatch."""

    lease_id: str
    dispatch_id: str
    globs: tuple[str, ...]
    deps_manifest: bool
    run_dir: str | None
    granted_at: float


@dataclass(frozen=True)
class LeaseRefusal:
    """A structured refusal returned (never raised) by ``grant_or_refuse``.

    ``kind`` is one of ``"overlap"``, ``"deps_manifest"``, ``"admission"``.
    ``holder_dispatch_id`` names the holding dispatch so the operator can
    decide (None for an admission-ceiling refusal, which names no holder).
    """

    kind: str
    message: str
    holder_dispatch_id: str | None = None


def _lease_from_dict(d: dict) -> Lease:
    return Lease(
        lease_id=d["lease_id"],
        dispatch_id=d["dispatch_id"],
        globs=tuple(d["globs"]),
        deps_manifest=bool(d["deps_manifest"]),
        run_dir=d.get("run_dir"),
        granted_at=float(d["granted_at"]),
    )


def _lease_to_dict(lease: Lease) -> dict:
    return {
        "lease_id": lease.lease_id,
        "dispatch_id": lease.dispatch_id,
        "globs": list(lease.globs),
        "deps_manifest": lease.deps_manifest,
        "run_dir": lease.run_dir,
        "granted_at": lease.granted_at,
    }


class LeaseRegistry:
    """On-disk, per-machine file-lease store with an admission throttle."""

    def __init__(
        self,
        store_path: str | os.PathLike[str],
        *,
        max_concurrent_leases: int = 8,
        deps_patterns: Iterable[str] = DEFAULT_DEPS_PATTERNS,
        startup_grace_s: float = 300.0,
        stale_after_s: float = 300.0,
        liveness: Callable[..., dict] = probe_liveness,
    ) -> None:
        self._store_path = Path(store_path)
        self._lock_path = Path(str(self._store_path) + ".lock")
        self._max = max_concurrent_leases
        self._deps_patterns = tuple(deps_patterns)
        self._startup_grace_s = startup_grace_s
        self._stale_after_s = stale_after_s
        self._liveness = liveness
        self._tlock = threading.Lock()
        self._store_path.parent.mkdir(parents=True, exist_ok=True)

    # -- critical section (atomic across threads AND processes) ---------

    @contextmanager
    def _critical(self) -> Generator[None, None, None]:
        with self._tlock:
            with open(self._lock_path, "w") as lf:
                fcntl.flock(lf, fcntl.LOCK_EX)
                try:
                    yield
                finally:
                    fcntl.flock(lf, fcntl.LOCK_UN)

    def _read(self) -> list[Lease]:
        if not self._store_path.exists():
            return []
        text = self._store_path.read_text() or '{"leases": []}'
        raw = json.loads(text)
        return [_lease_from_dict(r) for r in raw.get("leases", [])]

    def _write(self, leases: list[Lease]) -> None:
        tmp = self._store_path.with_suffix(self._store_path.suffix + ".tmp")
        tmp.write_text(
            json.dumps({"leases": [_lease_to_dict(l) for l in leases]}, indent=2)
        )
        os.replace(tmp, self._store_path)

    # -- classification helpers -----------------------------------------

    def _touches_deps(self, globs: tuple[str, ...]) -> bool:
        return any(
            globs_conflict(g, dp) for g in globs for dp in self._deps_patterns
        )

    @staticmethod
    def _overlaps(a: tuple[str, ...], b: tuple[str, ...]) -> bool:
        return any(globs_conflict(g1, g2) for g1 in a for g2 in b)

    # -- public surface (the production dispatch path for leases) -------

    def grant_or_refuse(
        self,
        dispatch_id: str,
        globs: Iterable[str],
        *,
        run_dir: str | os.PathLike[str] | None = None,
    ) -> Lease | LeaseRefusal:
        """Atomically grant a lease over *globs* to *dispatch_id*, or
        return a structured ``LeaseRefusal``.  Never raises on a domain
        refusal.
        """
        req = tuple(globs)
        with self._critical():
            leases = self._read()

            if len(leases) >= self._max:
                return LeaseRefusal(
                    kind="admission",
                    message=(
                        f"admission throttle: {len(leases)} active leases at "
                        f"ceiling {self._max}; release a lease before "
                        f"dispatching {dispatch_id!r}"
                    ),
                    holder_dispatch_id=None,
                )

            touches_deps = self._touches_deps(req)
            if touches_deps:
                for held in leases:
                    if held.deps_manifest:
                        return LeaseRefusal(
                            kind="deps_manifest",
                            message=(
                                f"dependency-manifest ({DEPS_MANIFEST_KEY}) is "
                                f"single-writer; held by dispatch "
                                f"{held.dispatch_id!r}"
                            ),
                            holder_dispatch_id=held.dispatch_id,
                        )

            for held in leases:
                if self._overlaps(req, held.globs):
                    return LeaseRefusal(
                        kind="overlap",
                        message=(
                            f"requested globs {list(req)} overlap the lease held "
                            f"by dispatch {held.dispatch_id!r} (holds "
                            f"{list(held.globs)})"
                        ),
                        holder_dispatch_id=held.dispatch_id,
                    )

            lease = Lease(
                lease_id=uuid.uuid4().hex,
                dispatch_id=dispatch_id,
                globs=req,
                deps_manifest=touches_deps,
                run_dir=str(run_dir) if run_dir is not None else None,
                granted_at=time.time(),
            )
            leases.append(lease)
            self._write(leases)
            return lease

    def release(self, dispatch_id: str) -> int:
        """Release every lease held by *dispatch_id*.  Returns the count
        released (terminal state: completion / failure).
        """
        with self._critical():
            leases = self._read()
            kept = [l for l in leases if l.dispatch_id != dispatch_id]
            released = len(leases) - len(kept)
            if released:
                self._write(kept)
            return released

    def reap(self) -> list[Lease]:
        """Release every lease whose holder is artifact-probe-dead (past
        the startup grace).  Returns the reaped leases.  Liveness is the
        shared ``probe_liveness`` reader — never a second hand-rolled one.
        """
        now = time.time()
        with self._critical():
            leases = self._read()
            reaped = [l for l in leases if self._is_dead(l, now)]
            if reaped:
                dead_ids = {l.lease_id for l in reaped}
                self._write([l for l in leases if l.lease_id not in dead_ids])
            return reaped

    def active_leases(self) -> list[Lease]:
        with self._critical():
            return self._read()

    # -- reap policy -----------------------------------------------------

    def _is_dead(self, lease: Lease, now: float) -> bool:
        # Startup grace: a just-granted lease that has not produced
        # artifacts yet is a live agent still spinning up, never reaped.
        if now - lease.granted_at <= self._startup_grace_s:
            return False
        # Past grace with no run dir ever recorded → nothing can ever
        # revive it; treat as dead.
        if lease.run_dir is None:
            return True
        state = self._liveness(Path(lease.run_dir), stale_after_s=self._stale_after_s)
        return not state.get("alive", False)
