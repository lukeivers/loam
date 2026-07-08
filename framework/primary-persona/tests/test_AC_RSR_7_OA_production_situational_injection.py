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

"""AC.RSR.7 (OUTCOME-ALTITUDE) — situational behavioral injection,
end-to-end, no pre-arranged state.

Over the production ``retrieve()`` entry-point invoked with no
pre-arranged retrieval state, against a SEEDED rules store: a turn whose
situation matches surfaces the rule's directive in the labeled rules
block; a turn whose situation does not match surfaces no rule; the topical
fact recall on both turns is intact — proving the store recalls behavioral
prompts SITUATIONALLY through the real entry-point. The additive
``{situation -> rules fired}`` telemetry lands too.
"""

from __future__ import annotations

import json
from pathlib import Path

from loam.primary_persona import rules_store as rs
from loam.primary_persona.keep_pace.retrieval import RetrievalConfig, retrieve

from _helpers_keep_pace import write_corpus


def _cfg(tmp_path: Path, corpus: Path, store: Path, telemetry_dir) -> RetrievalConfig:
    return RetrievalConfig(
        workspace_root=tmp_path,
        memory_dir=corpus,
        claude_homes=(),
        objectives_home=tmp_path / "no-obj",
        rules_memory_dir=store,
        telemetry_dir=telemetry_dir,
    )


def _read_situational_records(telemetry_dir: Path) -> list[dict]:
    out: list[dict] = []
    for f in sorted(telemetry_dir.glob("*.jsonl")):
        for line in f.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            if rec.get("kind") == "situational-recall":
                out.append(rec)
    return out


def test_AC_RSR_7_OA_situational_injection_end_to_end(tmp_path: Path) -> None:
    corpus = tmp_path / "memory"
    write_corpus(corpus)
    store = tmp_path / "store"
    store.mkdir()
    # Seed the starter rule set — the store is populated only here (cold
    # start; no injected index, no pre-arranged ranking state).
    written = rs.seed_starter_rules(store)
    assert written, "seed did not populate the store"
    telemetry_dir = tmp_path / "tel"

    # A turn whose SITUATION matches a seeded rule (dispatching) AND whose
    # topic hits the corpus (litrpg canon / production pipeline).
    matching_prompt = (
        "dispatch a background agent to run the litrpg canon "
        "production pipeline"
    )
    block_match = retrieve(
        prompt=matching_prompt,
        config=_cfg(tmp_path, corpus, store, telemetry_dir),
    )
    assert "[behavioral-rules]" in block_match
    assert "Dispatch briefs carry scope only" in block_match
    # Fact recall is intact on the same turn.
    assert "[keep-pace]" in block_match
    assert "LitRPG canon" in block_match

    # A turn whose topic hits the SAME corpus but whose situation does NOT
    # match any seeded rule.
    nonmatching_prompt = "tell me about the litrpg canon production pipeline"
    block_nomatch = retrieve(
        prompt=nonmatching_prompt,
        config=_cfg(tmp_path, corpus, store, telemetry_dir),
    )
    assert "[behavioral-rules]" not in block_nomatch, (
        "a rule surfaced on a non-matching situation (always-on failure)"
    )
    # Fact recall is intact on the non-matching turn too.
    assert "[keep-pace]" in block_nomatch
    assert "LitRPG canon" in block_nomatch

    # The additive situational telemetry recorded both turns: one with a
    # rule injected, one with an empty situation.
    records = _read_situational_records(telemetry_dir)
    assert len(records) == 2
    injected_counts = sorted(r["counts"]["n_injected"] for r in records)
    assert injected_counts == [0, 1]
    fired = next(r for r in records if r["counts"]["n_injected"] == 1)
    assert "dispatching-subagent" in fired["situation"]
