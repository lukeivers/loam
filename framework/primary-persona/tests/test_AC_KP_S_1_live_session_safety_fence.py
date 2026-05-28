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

"""AC.KP.S.1 — live-session-safety fence. The KP1 contributor is
fail-soft (a broken retrieval never breaks the turn — composes with
the chain's fail-open-whole-chain guarantee AC.KP0.4), and the
live-activation wiring is STAGED, not done (RF-6)."""

from __future__ import annotations

from pathlib import Path

from loam.primary_persona.keep_pace.retrieval import (
    RetrievalConfig,
    build_keep_pace_contributor,
)


def test_AC_KP_S_1_contributor_matches_chain_fn_contract() -> None:
    # The contributor shape is fn(envelope: dict) -> Optional[str] —
    # the KP0 chain's Contributor.fn contract.
    contributor = build_keep_pace_contributor()
    assert callable(contributor)
    # A well-formed empty envelope yields None (nothing to inject),
    # never raises.
    assert contributor({}) is None


def test_AC_KP_S_1_contributor_fail_soft_on_bad_envelope() -> None:
    contributor = build_keep_pace_contributor()
    # Garbage envelopes never raise — the turn proceeds.
    for bad in [None, [], "not-a-dict", {"prompt": 123}, {"keep_pace": "x"}]:
        result = contributor(bad)  # type: ignore[arg-type]
        assert result is None or isinstance(result, str)


def test_AC_KP_S_1_contributor_with_config_returns_str_or_none(
    tmp_path: Path,
) -> None:
    from _helpers_keep_pace import write_corpus

    memory_dir = tmp_path / "memory"
    write_corpus(memory_dir)
    cfg = RetrievalConfig(
        workspace_root=tmp_path,
        memory_dir=memory_dir,
        claude_homes=(),
        objectives_home=tmp_path / "empty-home",
    )
    contributor = build_keep_pace_contributor(cfg)
    out = contributor({"prompt": "continue the batch"})
    # A real cold-walk hit through the contributor surface.
    assert isinstance(out, str)
    assert "canon" in out.lower() or "litrpg" in out.lower()


def test_AC_KP_S_1_live_wiring_is_staged_not_done() -> None:
    # RF-6: the KP0 chain's contributors() list is still EMPTY — KP1's
    # registration is the GATED live step, not done in this cycle. The
    # live ~/.claude/settings.json activation is likewise staged.
    repo_root = Path(__file__).resolve().parents[3]
    ups = (
        repo_root
        / "framework"
        / "hands-off-lifecycle"
        / "hooks"
        / "keep_pace"
        / "user_prompt_submit.py"
    )
    src = ups.read_text(encoding="utf-8")
    # The contributors() surface still returns an empty list — KP1 is
    # NOT wired live here (proven via the import-target factory instead).
    assert "def contributors() -> list:" in src
    assert "return []" in src
