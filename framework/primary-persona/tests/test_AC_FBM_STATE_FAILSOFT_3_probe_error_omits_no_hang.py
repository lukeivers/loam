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

"""AC-FBM-STATE-FAILSOFT-3 (Slice D — fail-soft guard) — a project whose
derivation raises is OMITTED from the block (the surviving projects still
render); an all-fail path returns ``""``. A status surface that is slow or wrong
is worse than absent — so a probe error degrades to nothing, never a hang or a
wrong/partial status.
"""

from __future__ import annotations

from loam_cli.audit.probe import Liveness
from loam_cli.audit.record import ComponentState, StateOfLoam

from loam.primary_persona.keep_pace.project_state import (
    build_project_state_contributor,
    render_project_state_block,
)


def _good_record(module: str) -> StateOfLoam:
    return StateOfLoam(
        head_sha="feedface0000",
        components=(
            ComponentState(
                name=module,
                liveness=Liveness.MERGED,
                kind="component",
                evidence="fixture",
            ),
        ),
    )


def test_raising_project_is_omitted_survivors_render() -> None:
    """One project's derivation raises; the other still renders — the block
    is the surviving project only, never a partial/wrong row for the failed
    one."""

    def _derive(name: str) -> StateOfLoam:
        if name == "broken":
            raise RuntimeError("simulated git-probe failure")
        return _good_record("alpha")

    block = render_project_state_block(
        names=("broken", "ok"), derive=_derive
    )
    assert block, "the surviving project must still render"
    assert "ok" in block.lower(), "the healthy project must be present"
    assert "alpha" in block.lower(), "the healthy project's module must be present"
    assert "broken" not in block.lower(), (
        f"the failing project must be OMITTED, not rendered partial; got:\n{block}"
    )


def test_all_fail_returns_empty_no_hang() -> None:
    """Every project's derivation raises => the block is ``""`` (no block,
    never a hang)."""

    def _derive(_name: str) -> StateOfLoam:
        raise RuntimeError("simulated total probe failure")

    block = render_project_state_block(
        names=("a", "b", "c"), derive=_derive
    )
    assert block == "", (
        f"an all-fail derivation must return an empty block; got:\n{block!r}"
    )


def test_contributor_is_fail_soft_to_empty_string() -> None:
    """The turn contributor returns ``str`` always — a raising derivation
    yields ``""`` (graceful-empty), never an exception that breaks the turn."""

    def _derive(_name: str) -> StateOfLoam:
        raise RuntimeError("boom")

    # The contributor renders via the registry path by default; here we drive
    # the render directly to assert the empty-string contract on total failure.
    out = render_project_state_block(names=("x",), derive=_derive)
    assert out == ""

    # And the contributor surface itself never raises (it returns str).
    fn = build_project_state_contributor(names=())
    result = fn({"prompt": "anything"})
    assert isinstance(result, str), "the contributor must always return a str"
