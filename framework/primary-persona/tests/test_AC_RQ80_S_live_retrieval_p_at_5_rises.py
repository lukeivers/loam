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

"""AC.RQ80.S ★ (outcome-altitude:true, #80) — the REAL Slice-F P@5 metric over
the PRODUCTION ``rank()`` against the LIVE FBM store + corpus, NO pre-arranged
state, computes an ACTUAL P@5 number and asserts it is STRICTLY GREATER THAN the
pre-fix baseline of 0.0 — the two levers (anchor-flood cap + omnibus length-norm)
move the genuinely-relevant focused rule into the top-5.

This drives the same production ``rank()`` the live turn injects, over the live
machine's episode store + feedback corpus, with relevance labels authored on
GENUINE topical relevance to known durable corpus rules (the same honest probe
set the sealed ``fbm-retrieval-relevance-metric-p-at-5`` floor test uses, where
the measured baseline was 0.0). A STUB-class test (mocked ``rank`` / hand-fed hit
lists) does NOT satisfy this AC; the P@5 here is COMPUTED from real retrieval
over real data.

Skips cleanly if the live store/corpus is absent (CI without the machine's
memory dir) — the outcome-altitude guarantee is about the LIVE path.

Plan: docs/plans/fbm-retrieval-quality-anchor-cap-omnibus-norm.md §AC.RQ80.S.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from loam.primary_persona.keep_pace.retrieval import RetrievalConfig, rank
from loam.primary_persona.keep_pace.retrieval_metric import Probe, precision_at_k


# The live workspace whose FBM store + auto-memory corpus this metric measures.
_LIVE_WORKSPACE_ROOT = Path("/Users/lukeivers/pos3")
_LIVE_GROUP = "pos3"

# The pre-fix baseline the sealed metric measured (recorded in the
# fbm-retrieval-relevance-metric-p-at-5 seal + this cycle's plan §14): live
# P@5 = 0.0. This AC asserts the fix moves the measured value STRICTLY ABOVE it.
_PRE_FIX_BASELINE = 0.0


def _live_config() -> RetrievalConfig | None:
    """Resolve the LIVE RetrievalConfig the way the production live wiring does;
    ``None`` if the live store is absent."""
    from loam.primary_persona.file_memory import memory_dir_for_workspace

    claude_home = Path.home() / ".claude"
    slug = "-" + str(_LIVE_WORKSPACE_ROOT).strip("/").replace("/", "-")
    mem = claude_home / "projects" / slug / "memory"
    episode_dir = memory_dir_for_workspace(_LIVE_WORKSPACE_ROOT)
    if not mem.is_dir() or not episode_dir.exists():
        return None
    return RetrievalConfig(
        workspace_root=_LIVE_WORKSPACE_ROOT,
        memory_dir=mem,
        claude_homes=(claude_home,),
        objectives_home=claude_home,
        episode_memory_dir=episode_dir,
        episode_group_ids=(_LIVE_GROUP,),
        top_n=5,
    )


# The SAME honest probe set the sealed metric floor test uses — relevance
# authored on GENUINE topical relevance to known durable corpus rules, decided
# on topic, NOT from ranker output.
_LIVE_PROBES = [
    Probe.from_labels(
        "what should I do when Telegram is down and the MCP is unreachable",
        ["Telegram outage self-heal keep working confident path"],
    ),
    Probe.from_labels(
        "can we use the Anthropic API key for an LLM call",
        ["NO Anthropic API key subscription-only claude"],
    ),
    Probe.from_labels(
        "how should background agents be used for long research work",
        ["Background agents by default"],
    ),
]


def test_AC_RQ80_S_live_retrieval_p_at_5_rises_above_baseline() -> None:
    """Outcome-altitude: the real metric over the live production retrieval
    computes an actual P@5 STRICTLY GREATER THAN the pre-fix 0.0 baseline."""
    config = _live_config()
    if config is None:
        pytest.skip(
            "live FBM store/corpus absent — outcome-altitude needs the real "
            "store on disk"
        )

    report = precision_at_k(_LIVE_PROBES, config, k=5)

    # The metric machinery ran end-to-end over the LIVE production path.
    assert report.k == 5
    assert report.num_probes == len(_LIVE_PROBES)
    assert 0.0 <= report.mean <= 1.0

    # Non-vacuous: the production path surfaced a real ranked top-5 per probe.
    for probe in _LIVE_PROBES:
        hits = rank(prompt=probe.query, config=config)
        assert hits, (
            "the live production retrieval must surface ranked hits for the "
            f"probe {probe.query!r}; an empty result would mean the metric is "
            "not exercising the live path"
        )

    # Deterministic on the live path — a second run reproduces the report.
    assert precision_at_k(_LIVE_PROBES, config, k=5) == report

    # THE HEADLINE: live P@5 rose STRICTLY above the pre-fix 0.0 baseline — at
    # least one genuinely-relevant focused rule now lands in the top-5 (it was
    # crowded out at rank ~12-14 before the two levers).
    assert report.mean > _PRE_FIX_BASELINE, (
        f"live P@5 {report.mean} did not rise above the pre-fix baseline "
        f"{_PRE_FIX_BASELINE}; the anchor-cap + omnibus length-norm levers must "
        f"move the focused rule into the top-5; per_probe={report.per_probe}"
    )
