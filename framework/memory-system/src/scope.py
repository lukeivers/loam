"""D6 — Scope-of-work mapper.

Every memory entry is attributed to the scope-of-work it was produced
within or about. Retrieval can be filtered by scope, and a scope's
memory slice is enumerable.

**Status (2026-04-18):** the real scope-of-work primitive landed at
`pos-v2/scope-of-work/`. Production wiring uses
`scope_of_work.adapter.RealScopeSourceAdapter(runtime)` injected into
the `MemoryAPI` constructor. The `MockScopeSource` below is preserved
as a test-only fixture for memory-system tests that exercise this
module in isolation; new code should not use it.

The interface the adapter satisfies is `ScopeSource` — a small protocol:

    get_scope(scope_id) -> ScopeRecord | None
    register_scope(scope_id, metadata) -> ScopeRecord
    list_scopes() -> list[ScopeRecord]

Graphiti's `group_id` is the physical carrier of scope attribution
inside Kuzu; we use scope_id == group_id for memory writes, so scope
filtering is native ("retrieve within scope S" -> `group_ids=[S]`).

The mock persists to `data/scope_registry.json`; the real primitive
backs scopes by a SQLite WAL event log (see
`scope-of-work/src/store.py`).
"""

from __future__ import annotations

import json
import os
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from .config import section


@dataclass
class ScopeRecord:
    scope_id: str
    name: str
    created_at: str
    description: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class ScopeSource(Protocol):
    """The minimal contract memory needs from the scope primitive.

    The real scope-of-work runtime will implement this plus everything
    else it owns (goals, budgets, reversibility class, etc.). Memory
    only cares about the identity and enumeration surface.
    """

    def get_scope(self, scope_id: str) -> ScopeRecord | None: ...
    def register_scope(self, scope_id: str, **metadata: Any) -> ScopeRecord: ...
    def list_scopes(self) -> list[ScopeRecord]: ...


class MockScopeSource:
    """Mock implementation backing onto a JSON file.

    When the scope primitive lands, this whole class is replaced by the
    primitive's adapter; `MemoryAPI` takes a ScopeSource by injection,
    so the change is one line at wiring time.
    """

    def __init__(self, registry_path: str | Path | None = None) -> None:
        cfg = section("scope")
        mock_cfg = cfg.get("mock") or {}
        self._default_scope_id: str = mock_cfg.get("default_scope_id", "pos-v2:default")
        self._auto_register: bool = bool(mock_cfg.get("auto_register", True))
        self._registry_path = Path(
            registry_path
            or os.environ.get("POSV2_SCOPE_REGISTRY")
            or "./data/scope_registry.json"
        )
        self._lock = threading.Lock()
        self._scopes: dict[str, ScopeRecord] = {}
        self._load()

    # --- persistence ---

    def _load(self) -> None:
        if not self._registry_path.exists():
            return
        try:
            raw = json.loads(self._registry_path.read_text())
        except (json.JSONDecodeError, OSError):
            return
        for entry in raw.get("scopes", []):
            rec = ScopeRecord(**entry)
            self._scopes[rec.scope_id] = rec

    def _flush(self) -> None:
        self._registry_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"scopes": [asdict(r) for r in self._scopes.values()]}
        tmp = self._registry_path.with_suffix(self._registry_path.suffix + ".tmp")
        tmp.write_text(json.dumps(payload, indent=2, default=str))
        tmp.replace(self._registry_path)

    # --- API ---

    def get_scope(self, scope_id: str) -> ScopeRecord | None:
        with self._lock:
            return self._scopes.get(scope_id)

    def register_scope(
        self,
        scope_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        **metadata: Any,
    ) -> ScopeRecord:
        with self._lock:
            existing = self._scopes.get(scope_id)
            if existing is not None:
                return existing
            rec = ScopeRecord(
                scope_id=scope_id,
                name=name or scope_id,
                created_at=datetime.now(timezone.utc).isoformat(),
                description=description,
                metadata=dict(metadata),
            )
            self._scopes[rec.scope_id] = rec
            self._flush()
            return rec

    def list_scopes(self) -> list[ScopeRecord]:
        with self._lock:
            return list(self._scopes.values())

    # --- mock-specific helpers ---

    @property
    def default_scope_id(self) -> str:
        return self._default_scope_id

    def ensure(self, scope_id: str | None) -> ScopeRecord:
        """Return a ScopeRecord, auto-registering if configured to do so.

        Callers use this at ingest time to coerce an arbitrary scope_id
        into a registered record (or fall back to the default scope).
        This is the MOCK-ONLY behaviour; the real primitive will reject
        unknown scopes instead of auto-registering.
        """
        if scope_id is None:
            scope_id = self._default_scope_id
        existing = self.get_scope(scope_id)
        if existing is not None:
            return existing
        if self._auto_register:
            return self.register_scope(scope_id, name=scope_id)
        raise KeyError(f"unknown scope_id {scope_id!r} (auto_register disabled)")


def default_scope_source() -> MockScopeSource:
    """Module-level factory; tests or callers may inject their own."""
    return MockScopeSource()
