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

"""RealScopeSourceAdapter — bridges the primitive into memory-system.

Memory's `ScopeSource` protocol (memory-system/src/scope.py):

    def get_scope(self, scope_id: str) -> ScopeRecord | None
    def register_scope(self, scope_id: str, **metadata) -> ScopeRecord
    def list_scopes(self) -> list[ScopeRecord]

`ScopeRecord` carries: scope_id, name, created_at, description?, metadata.

The adapter exposes the same shape backed by the real ScopeRuntime.
`register_scope` is a no-op delegate that *queries* the runtime — the
real primitive does NOT auto-create scopes. Per memory's mock docstring:
"the real primitive will reject unknown scopes instead of auto-
registering."

This file is the 10-line adapter the brief calls for; the wrapping is
unavoidably a few lines longer because we have to hand back the
ScopeRecord shape memory expects, but the heart is the three method
shims.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import Any

from .runtime import ScopeRuntime


# Memory uses a ScopeRecord dataclass; we mirror its shape so callers do
# not import memory's module from here (avoids a cyclic dep).
@dataclass
class ScopeRecord:
    scope_id: str
    name: str
    created_at: str
    description: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


def _to_record(proj) -> ScopeRecord:
    return ScopeRecord(
        scope_id=proj.scope_id,
        name=proj.owner_persona or proj.scope_id,
        created_at=proj.last_transition_at or "",
        description=proj.goal,
        metadata={
            "state": proj.state.value,
            "reversibility_class": proj.reversibility_class.value,
        },
    )


class RealScopeSourceAdapter:
    """Wraps a ScopeRuntime to satisfy memory's ScopeSource protocol.

    The 10-line core is `get_scope` + `list_scopes` + `register_scope`'s
    rejection branch.
    """

    def __init__(self, runtime: ScopeRuntime) -> None:
        self._rt = runtime

    def get_scope(self, scope_id: str) -> ScopeRecord | None:
        proj = self._rt.get(scope_id)
        return _to_record(proj) if proj else None

    def register_scope(self, scope_id: str, **metadata: Any) -> ScopeRecord:
        # The real primitive rejects unknown scopes (memory's
        # MockScopeSource ensure() docstring already documents this).
        existing = self.get_scope(scope_id)
        if existing is not None:
            return existing
        raise KeyError(
            f"unknown scope_id {scope_id!r}: scopes must be created via "
            "ScopeRuntime.create() before memory ingest"
        )

    def list_scopes(self) -> list[ScopeRecord]:
        return [_to_record(p) for p in self._rt.list()]
