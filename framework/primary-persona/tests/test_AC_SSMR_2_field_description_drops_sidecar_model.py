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

"""AC.SSMR.2 — the ``SessionPayload.service_state`` Pydantic ``Field``
description no longer models the ``memory`` entry as a "sidecar" /
session-level service; the ``orchestrator`` entry's genuine-service
framing is preserved.

Under the v0.1.0 M-FBM pivot memory is a file-based store, not a
sidecar service. The prior Field description read "Service-state
fields for the memory sidecar, orchestrator, and any other
session-level services" — mis-modelling the file-based store as a
sidecar service. This AC asserts the description models the memory
entry as file-based-store reachability while keeping the orchestrator
framed as a service.

Outcome-shape: any description satisfying the constraints passes
(wording is the builder's call).
"""

from __future__ import annotations

from loam.primary_persona.context_composer import SessionPayload


def _field_description() -> str:
    field = SessionPayload.model_fields["service_state"]
    desc = field.description
    assert desc, "service_state Field must carry a description"
    return desc.lower()


def test_AC_SSMR_2_description_drops_memory_sidecar_mismodel() -> None:
    """The description no longer calls the memory entry a "sidecar"."""
    desc = _field_description()
    assert "sidecar" not in desc, (
        "the service_state Field description must not model the "
        "file-based memory store as a 'sidecar' (M-FBM: file-based "
        "store, no sidecar service)"
    )


def test_AC_SSMR_2_description_models_memory_as_file_based_store() -> None:
    """The description models the memory entry as the file-based store
    under M-FBM."""
    desc = _field_description()
    assert "file-based" in desc, (
        "the description must model the memory entry as the "
        "file-based memory store (M-FBM)"
    )


def test_AC_SSMR_2_description_keeps_orchestrator_service_framing() -> None:
    """The orchestrator entry — a genuine service — keeps its service
    framing (the reframe is memory-entry-specific)."""
    desc = _field_description()
    assert "orchestrator" in desc and "service" in desc, (
        "the orchestrator entry must still be modelled as a genuine "
        "service (the reframe is memory-entry-specific, not a blanket "
        "de-service of the whole field)"
    )
