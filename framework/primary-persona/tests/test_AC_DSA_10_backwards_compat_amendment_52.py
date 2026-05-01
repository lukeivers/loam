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

"""AC.DSA.10 — backwards-compat with amendment #52 callers.

Existing callers of ``dispatch_with_scope`` that omit ``new_acs``
(i.e., every caller authored before this amendment) observe identical
behaviour to the pre-amendment wrapper. AC.A8.1 – AC.A8.S (amendment
#52) all remain green. The ``DispatchShape`` field is keyword-only
with a default of ``()`` so structural compatibility is preserved.
"""

from __future__ import annotations

import pytest

from loam.primary_persona import (
    DispatchOutcome,
    DispatchShape,
    dispatch_with_scope,
)

from ._helpers_a8 import (
    StubIPCClient,
    build_stub_ipc_client_factory,
    make_workspace,
    stub_agent_runner_ok,
)


@pytest.mark.asyncio
async def test_AC_DSA_10_call_without_new_acs_no_setup_phase(
    tmp_path, monkeypatch
) -> None:
    """Calling ``dispatch_with_scope`` without ``new_acs`` (or with
    the empty tuple) does NOT fire the setup phase, regardless of
    workspace mode. The dispatch behaves exactly as it did pre-#74."""
    workspace = make_workspace(tmp_path, ambient_objective="obj")

    # Force the workspace_mode reader to dev-mode — even there, the
    # empty new_acs gate must skip the setup phase entirely.
    import sys
    import types
    cls_mod = types.ModuleType("corpus_load_sentinel")
    cls_mod.workspace_mode = lambda _ws: "dev-mode"
    monkeypatch.setitem(sys.modules, "corpus_load_sentinel", cls_mod)

    # If setup ran, it would import active_scope_sentinel; install a
    # spy that asserts no call is made.
    write_calls: list = []
    ass_mod = types.ModuleType("active_scope_sentinel")

    class _SB:
        def __init__(self, **kw):
            pass

    def _w(*a, **kw):
        write_calls.append((a, kw))
        raise AssertionError("sentinel writer should not be invoked")

    ass_mod.ScopeBinding = _SB
    ass_mod.write_active_scope_sentinel = _w
    monkeypatch.setitem(sys.modules, "active_scope_sentinel", ass_mod)

    client = StubIPCClient()
    import loam.orchestrator.ipc as _ipc_mod

    monkeypatch.setattr(
        _ipc_mod, "IPCClient", build_stub_ipc_client_factory(client)
    )

    shape = DispatchShape(objective="research the foo")
    result = await dispatch_with_scope(
        shape,
        agent_runner=stub_agent_runner_ok,
        workspace_root=workspace,
    )
    assert isinstance(result, DispatchOutcome)
    assert write_calls == []  # the sentinel writer was never invoked.


def test_AC_DSA_10_dispatch_shape_signature_is_compatible() -> None:
    """An amendment-#52 caller building a DispatchShape with positional
    + keyword args (NOT supplying ``new_acs``) still works."""
    shape = DispatchShape(
        objective="x",
        constraints=("c1",),
        halt_conditions=("h1",),
        expected_duration_seconds=42.0,
        task_shape_category="moderate",
        reversibility_class="compensatable",
    )
    assert shape.new_acs == ()
    assert shape.objective == "x"
    assert shape.constraints == ("c1",)


def test_AC_DSA_10_dispatch_shape_can_construct_from_kwargs_only() -> None:
    """The new field's keyword-only default doesn't shift positional
    parameter order for any existing field."""
    # If ``new_acs`` had been inserted into the positional sequence,
    # this construction (positional objective + named-rest) would
    # have raised a TypeError under any prior ordering. It does not.
    shape = DispatchShape(
        "objective-text",
        ("c",),
        ("h",),
    )
    assert shape.objective == "objective-text"
    assert shape.constraints == ("c",)
    assert shape.halt_conditions == ("h",)
    assert shape.new_acs == ()
