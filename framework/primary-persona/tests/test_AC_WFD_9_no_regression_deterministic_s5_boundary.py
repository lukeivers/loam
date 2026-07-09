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

"""AC.WFD.9 — no regression; deterministic-only; S5 boundary held.

The discipline adds NO LLM/API call to any write or read path; the
classifier is deterministic; a classifier error fails open (fact-typed
write, the turn never breaks); and no offline extraction / consolidation
engine is introduced (the S5 boundary — this stage produces the typed
facts S5 will later consume). The named regression suites (VOL / RSR / SUP
/ DLG / KP / FBM ...) are run by the seal's full-suite sweep.
"""

from __future__ import annotations

import inspect
from datetime import datetime, timezone
from pathlib import Path

from loam.primary_persona import file_memory as fm
from loam.primary_persona.file_memory import (
    EPISTEMIC_FACT,
    FileMemoryStore,
    classify_epistemic_type,
)


def test_AC_WFD_9_classifier_is_deterministic() -> None:
    samples = [
        "the design is elegant",
        "we merged the PR and the CI passed",
        "Luke said it was annoying on 2026-06-14",
        "",
    ]
    for s in samples:
        assert classify_epistemic_type(s) == classify_epistemic_type(s)


def test_AC_WFD_9_no_llm_or_api_on_the_classifier() -> None:
    # Deterministic + stdlib-only: the classifier source must not reach for
    # an LLM / subscription client / API key (no claude -p on the write
    # path — the cost ruling + subscription-only doctrine).
    src = inspect.getsource(classify_epistemic_type)
    src += inspect.getsource(fm._has_durable_fact_signal)
    for forbidden in ("claude_print", "anthropic", "openai", "requests", "urllib", "api_key"):
        assert forbidden not in src, (
            f"the classifier must be deterministic — found {forbidden!r}"
        )


def test_AC_WFD_9_fail_open_error_routes_to_fact_and_write_completes(
    tmp_path: Path, monkeypatch
) -> None:
    store = FileMemoryStore(memory_dir=tmp_path / "store")

    def _boom(_t: str) -> bool:  # noqa: ANN001
        raise RuntimeError("classifier fault")

    monkeypatch.setattr(fm, "_has_durable_fact_signal", _boom)
    # A body that WOULD otherwise be tagged non-fact.
    res = store.write_episode(
        name="turn/err",
        body="the design is elegant",
        source_description="session capture",
        reference_time=datetime.now(timezone.utc),
        source="message",
        group_id="pos3",
    )
    p = Path(res["path"])
    assert p.exists(), "a classifier fault must not break the write"
    front, _ = fm._split_frontmatter(p.read_text(encoding="utf-8"))
    assert front.get("epistemic") == EPISTEMIC_FACT, (
        "a classifier fault must route to fact (never suppress)"
    )


def test_AC_WFD_9_s5_boundary_no_extraction_engine() -> None:
    # This stage codes NO offline extraction / consolidation engine (no
    # bulk rule-mining, no significance judgment). It exposes only a
    # write-time classifier + a tag reader; no ``extract``/``consolidate``/
    # ``mine`` surface leaks into file_memory as part of this stage.
    public = {n for n in dir(fm) if not n.startswith("_")}
    for banned in ("extract_rules", "consolidate_rules", "mine_facts", "derive_rules"):
        assert banned not in public, (
            f"the S5 boundary is breached — {banned!r} belongs to a later stage"
        )
