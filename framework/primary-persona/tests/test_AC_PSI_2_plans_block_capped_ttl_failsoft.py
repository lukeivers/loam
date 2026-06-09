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

"""AC.PSI.2 — the turn-start surface includes ONE concise plans block:
in-flight plans + their real build-state, one short line each, derived
live, TTL-cached, within a hard char cap, fail-soft (a derivation
failure yields no block, never a wedge or a wrong state).

Method is the builder's call; these tests pin the OUTCOME via the
test seams (injected derivation) plus the production composer
registration.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from loam.primary_persona.context_composer import TriggerKind
from loam.primary_persona.keep_pace.plans_state import (
    _PLANS_BLOCK_CHAR_CAP,
    render_plans_block,
)
from loam.primary_persona.session_start_emitter import build_session_composer


@dataclass(frozen=True)
class _Plan:
    project: str
    slug: str
    title: str
    doc_path: str
    build_state: str
    seal_evidence: tuple[str, ...]
    in_sealed_archive: bool


def _plan(slug: str, state: str, evidence: tuple[str, ...] = ()) -> _Plan:
    return _Plan(
        project="loam",
        slug=slug,
        title=slug.replace("-", " "),
        doc_path=f"docs/plans/{slug}.md",
        build_state=state,
        seal_evidence=evidence,
        in_sealed_archive=(state == "sealed"),
    )


def test_AC_PSI_2_one_concise_block_inflight_only() -> None:
    """In-flight plans (partial + pending) render one short line each;
    sealed plans are NOT in the ambient block (they are done — the
    in-flight signal is the point); partial leads pending."""
    derived = {
        "loam": (
            _plan("done-thing", "sealed", ("abc1234 chore(seals): done-thing",)),
            _plan("pending-thing", "no-build-evidence"),
            _plan(
                "inflight-thing",
                "partially-sealed",
                ("abc1234 chore(amend): inflight-thing manifest+apply",),
            ),
        )
    }
    block = render_plans_block(derive=lambda: derived)
    assert block.startswith("[plan-state]")
    assert "inflight thing" in block
    assert "partially built" in block
    assert "pending thing" in block
    assert "no build evidence" in block
    assert "done thing" not in block
    # Partial leads pending (the load-bearing in-flight signal first).
    assert block.index("inflight thing") < block.index("pending thing")
    # One line per plan: 1 header + 2 plan lines.
    assert len(block.splitlines()) == 3


def test_AC_PSI_2_hard_char_cap() -> None:
    """A huge in-flight set cannot bloat the turn: the block is hard-
    capped (the Slice-D anti-bloat contract)."""
    derived = {
        "loam": tuple(
            _plan(f"very-long-in-flight-plan-slug-number-{i}", "no-build-evidence")
            for i in range(200)
        )
    }
    block = render_plans_block(derive=lambda: derived)
    assert len(block) <= _PLANS_BLOCK_CHAR_CAP


def test_AC_PSI_2_failsoft_no_block_never_wrong() -> None:
    """A raising / empty / None derivation yields NO block — absent
    beats wrong, and the turn never wedges."""
    assert render_plans_block(derive=lambda: None) == ""
    assert render_plans_block(derive=lambda: {}) == ""

    def _boom() -> dict:
        raise RuntimeError("probe failure")

    assert render_plans_block(derive=_boom) == ""
    # All-sealed (nothing in flight) is also no block, not a header-only
    # stub.
    derived = {"loam": (_plan("done", "sealed"),)}
    assert render_plans_block(derive=lambda: derived) == ""


def test_AC_PSI_2_production_composer_registers_plans_block(
    tmp_path: Path,
) -> None:
    """The production composer registers exactly ONE plan-state turn
    contributor, additively alongside the existing turn blocks."""
    ws = tmp_path / "myws"
    ws.mkdir()
    composer = build_session_composer(
        ws,
        memory_client_factory=lambda _root: None,
        register_tracker=False,
    )
    names = [c.name for c in composer.contributors(trigger_kind=TriggerKind.turn)]
    assert names.count("plan-state") == 1, (
        f"exactly one plans block must register; turn contributors: {names}"
    )
