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

"""AC.SSMR.1 — the ``probe_service_state`` docstring models the
``memory`` entry as file-based-store reachability under the v0.1.0
M-FBM pivot, NOT as a port-probed session-level service.

Under M-FBM (``file_memory.py`` D-Q.MFBM.6) memory is a file-based
episode dir with no daemon and no health port; the prior docstring
called it "session-level services" reached via an "HTTP health port".
This AC asserts the modelling language now reflects M-FBM: the
``memory`` entry is the file-based store (no service / no health
port for the file-based store), the TCP probe engages only when the
optional graphiti/M-GMP provider is installed, and the orchestrator
is still framed as a genuine UNIX-socket service.

Outcome-shape: any phrasing satisfying the modelling constraints
passes (method/wording is the builder's call). The wire-contract is
NOT touched here — that is AC.SSMR.3's preservation guard.
"""

from __future__ import annotations

from loam.primary_persona import session_start_gate as gate


def _doc() -> str:
    doc = gate.probe_service_state.__doc__
    assert doc is not None, "probe_service_state must carry a docstring"
    return doc.lower()


def test_AC_SSMR_1_docstring_models_memory_as_file_based_store() -> None:
    """The ``memory`` entry is modelled as the file-based store under
    M-FBM (file-based / M-FBM framing present)."""
    doc = _doc()
    assert "file-based" in doc, (
        "probe_service_state docstring must model the memory entry as "
        "the file-based memory store (M-FBM), not a service"
    )
    assert "m-fbm" in doc, (
        "docstring must reference the M-FBM pivot that makes memory "
        "file-based (the modelling correction's source)"
    )


def test_AC_SSMR_1_docstring_does_not_model_file_store_as_health_port_service() -> None:
    """The file-based store is NOT described as reached via an HTTP
    health port (the prior service-liveness mis-model is gone)."""
    doc = _doc()
    assert "http health port" not in doc, (
        "the file-based store must not be modelled as an HTTP "
        "health-port service (M-FBM: no memory daemon, no health port)"
    )
    # The docstring must say, in some phrasing, that there is no
    # memory daemon / no service / no health port for the file-based
    # store. Accept any of the equivalent phrasings (builder's call).
    assert ("no memory daemon" in doc) or ("not a service" in doc) or (
        "no health port" in doc
    ), (
        "docstring must state the file-based store has no daemon / is "
        "not a service / has no health port"
    )


def test_AC_SSMR_1_orchestrator_still_framed_as_socket_service() -> None:
    """The orchestrator entry — a genuine service — keeps its
    UNIX-socket-service framing (the reframe is memory-specific)."""
    doc = _doc()
    assert "orchestrator" in doc
    assert ("unix-socket" in doc) or ("socket" in doc and "service" in doc), (
        "the orchestrator must still be modelled as a genuine "
        "UNIX-socket service (the reframe is memory-entry-specific)"
    )
