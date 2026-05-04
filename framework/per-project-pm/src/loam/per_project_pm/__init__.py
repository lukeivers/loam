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

"""Per-project PM persona for loam.

Workspace-scoped project-manager persona. Holds project-domain
decision/ratification state + state-of-world snapshot; surfaces
decisions needing user attention; auto-loads (lazy on-demand) when
persona begins work in workspace.

Public API:

  - :class:`PMRuntime` — workspace-state-anchored PM runtime.
  - :class:`PMContract` — Pydantic model of an authored PM.
  - :class:`DecisionSurfacingPolicy` — policy knobs on the contract.
  - :class:`StateOfWorld` — read snapshot of PM state.
  - :class:`SurfacedQuestion` — return value of ``surface_next_question``
    (and one element of the tuple returned by
    ``surface_next_questions_batch``).
  - :class:`RecordedResponse` (Cycle 4) — return value of
    ``record_response``.
  - :class:`PMNotFoundError`, :class:`PMStateCorruptedError`,
    :class:`PendingResponseError` (Cycle 4) — named exception classes.
  - :class:`PerProjectPMContribution` — workspace-bootstrap contribution.
  - :class:`PerProjectPMRuntime` — host-published runtime factory.

See ``docs/design.md`` for PM/M-FBM boundary articulation + the
Cycle 4 one-question-at-a-time flow + audit-block-on-telegram SKILL
composition.

v0.1.7 Cycle 4 lands the deferred Cycle 2 surfaces:
``record_response()``, ``surface_next_questions_batch()``,
``require_owner_response``-blocking enforcement (on the batch API),
``onboarding_mode`` enforcement (forces 1 per batch), and
``PendingResponseError``.
"""

from __future__ import annotations

from loam.per_project_pm.contract import (
    DecisionSurfacingPolicy,
    PMContract,
)
from loam.per_project_pm.contribution import (
    PerProjectPMContribution,
    PerProjectPMRuntime,
)
from loam.per_project_pm.errors import (
    PendingResponseError,
    PMNotFoundError,
    PMStateCorruptedError,
)
from loam.per_project_pm.runtime import PMRuntime
from loam.per_project_pm.state import (
    RecordedResponse,
    StateOfWorld,
    SurfacedQuestion,
)


__all__ = [
    "DecisionSurfacingPolicy",
    "PMContract",
    "PendingResponseError",
    "PMNotFoundError",
    "PMStateCorruptedError",
    "PMRuntime",
    "PerProjectPMContribution",
    "PerProjectPMRuntime",
    "RecordedResponse",
    "StateOfWorld",
    "SurfacedQuestion",
]
