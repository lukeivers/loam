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

"""AC.CLP-MDLR.1-5 — model-ID extraction robust to upstream FORMATTING.

The v1 extractor matched Claude model IDs only when backtick-wrapped.
Anthropic reformatted the "Latest models comparison" table so the
Claude-API-ID row renders IDs as PLAIN text; the extractor under-detected
live models and a cosmetic backtick->plain edit faked add/remove deltas.

AC.CLP-MDLR.1 ★ (outcome-altitude): running the production extraction on
the REAL committed anthropic-models-overview snapshot detects the full
current-generation comparison-table lineup regardless of backtick
formatting (claude-fable-5, claude-opus-4-8, claude-sonnet-5,
claude-haiku-4-5-20251001).

AC.CLP-MDLR.2: a two-run refresh through production run_refresh, built
from the real before/after snippet (sonnet-5 backticked -> plain, table
otherwise identical), emits NO phantom add/remove for the reformatted model.

AC.CLP-MDLR.3: a model genuinely removed from the comparison table on the
second run is still named in model_delta.removed (the real signal survives).

AC.CLP-MDLR.4: claude-ids in incidental prose, Bedrock-style
anthropic.claude-* IDs, and Google-Cloud claude-*@date IDs are NOT captured.

AC.CLP-MDLR.5: a model present only as a backticked ID in prose (no table
row) is still detected — the structural change does not drop it.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

COMPONENT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = COMPONENT_ROOT.parents[2]
SRC = COMPONENT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from capability_refresh.models import extract_model_ids  # noqa: E402
from capability_refresh.refresh import run_refresh  # noqa: E402

# The real committed snapshot of the Anthropic models-overview page — the
# exact fetched content whose reformatting motivated this fix.
REAL_SNAPSHOT = (
    REPO_ROOT
    / "docs"
    / "capability-corpus"
    / ".refresh"
    / "snapshots"
    / "anthropic-models-overview.txt"
)


# ---------------------------------------------------------------------------
# AC.CLP-MDLR.1 ★ — outcome-altitude: real committed snapshot content
# ---------------------------------------------------------------------------

def test_AC_CLP_MDLR_1_real_snapshot_detects_current_lineup():
    """Running the production extractor on the REAL committed snapshot
    detects the current-generation comparison-table lineup regardless of
    which IDs happen to be backticked. This is the exact miss: the table's
    Claude-API-ID row has claude-fable-5 / claude-opus-4-8 /
    claude-haiku-4-5-20251001 in PLAIN text and only claude-sonnet-5
    backticked. AC.CLP-MDLR.1 ★ (outcome-altitude — real fetched content
    through the production extraction function)."""
    assert REAL_SNAPSHOT.is_file(), (
        f"real snapshot missing at {REAL_SNAPSHOT}"
    )
    ids = extract_model_ids(REAL_SNAPSHOT.read_text(encoding="utf-8"))
    for expected in (
        "claude-fable-5",
        "claude-opus-4-8",
        "claude-sonnet-5",
        "claude-haiku-4-5-20251001",
    ):
        assert expected in ids, (
            f"{expected!r} not detected from the real snapshot; got: {ids}"
        )


def test_AC_CLP_MDLR_1_real_snapshot_no_bedrock_or_gcloud_ids():
    """The real snapshot's Bedrock (anthropic.claude-*) and Google-Cloud
    (claude-*@date) ID rows must NOT pollute the lineup — the extractor
    returns only bare canonical claude-* IDs. AC.CLP-MDLR.1 / .4."""
    ids = extract_model_ids(REAL_SNAPSHOT.read_text(encoding="utf-8"))
    for got in ids:
        assert got.startswith("claude-"), f"non-canonical id captured: {got!r}"
        assert "@" not in got, f"Google-Cloud dated id captured: {got!r}"
        assert "anthropic." not in got, f"Bedrock id captured: {got!r}"


# ---------------------------------------------------------------------------
# Fixtures for the two-run / delta ACs — a real-shaped wide comparison table
# ---------------------------------------------------------------------------

# The comparison table with claude-sonnet-5 BACKTICKED (pre-reformat state).
TABLE_SONNET_BACKTICKED = """\
# Models overview

Claude Fable 5 (`claude-fable-5`) is the most capable model. Claude Mythos 5
(`claude-mythos-5`) shares its specs.

### Latest models comparison

| Feature           | Claude Fable 5 | Claude Opus 4.8 | Claude Sonnet 5   | Claude Haiku 4.5           |
| ----------------- | -------------- | --------------- | ----------------- | -------------------------- |
| **Description**   | Long agents    | Agentic coding  | Speed + intel     | Fastest                    |
| **Claude API ID** | claude-fable-5 | claude-opus-4-8 | `claude-sonnet-5` | claude-haiku-4-5-20251001  |
| **AWS Bedrock ID**| anthropic.claude-fable-53 | anthropic.claude-opus-4-83 | `anthropic.claude-sonnet-5`3 | anthropic.claude-haiku-4-5-20251001-v1:0 |
| **Google Cloud ID**| claude-fable-5 | claude-opus-4-8 | claude-sonnet-5\\@20260609 | claude-haiku-4-5\\@20251001 |
"""

# The SAME table with claude-sonnet-5 rendered PLAIN (post-reformat, the
# only change) — a pure formatting edit.
TABLE_SONNET_PLAIN = TABLE_SONNET_BACKTICKED.replace(
    "`claude-sonnet-5`", "claude-sonnet-5"
)

# The table with claude-sonnet-5 GENUINELY REMOVED from the ID row (deprecated).
TABLE_SONNET_REMOVED = """\
# Models overview

Claude Fable 5 (`claude-fable-5`) is the most capable model. Claude Mythos 5
(`claude-mythos-5`) shares its specs.

### Latest models comparison

| Feature           | Claude Fable 5 | Claude Opus 4.8 | Claude Haiku 4.5           |
| ----------------- | -------------- | --------------- | -------------------------- |
| **Description**   | Long agents    | Agentic coding  | Fastest                    |
| **Claude API ID** | claude-fable-5 | claude-opus-4-8 | claude-haiku-4-5-20251001  |
"""


@pytest.fixture
def wide_table_fixture(tmp_path):
    """Corpus with a model_parse:true watch source pointed at a file://
    upstream carrying a real-shaped wide comparison table."""
    repo = tmp_path / "repo"
    corpus = repo / "docs" / "capability-corpus"
    corpus.mkdir(parents=True)

    upstream = tmp_path / "models.md"
    upstream.write_text(TABLE_SONNET_BACKTICKED, encoding="utf-8")

    sources = corpus / "sources.yaml"
    sources.write_text(
        "schema_version: 1\n"
        "sources:\n"
        "  - id: model-tracker\n"
        "    kind: watch\n"
        "    model_parse: true\n"
        f"    url: file://{upstream}\n"
        "    cadence: high-velocity\n",
        encoding="utf-8",
    )
    return {"corpus": corpus, "upstream": upstream, "sources": sources}


# ---------------------------------------------------------------------------
# AC.CLP-MDLR.2 — a pure formatting change produces NO phantom delta
# ---------------------------------------------------------------------------

def test_AC_CLP_MDLR_2_no_phantom_delta_on_backtick_to_plain(wide_table_fixture):
    """Run 1: sonnet-5 backticked. Run 2: sonnet-5 plain (only change).
    The delta names no add and no removal — a cosmetic edit cannot fake a
    lineup change. Runs through the production run_refresh entry point."""
    run_refresh(wide_table_fixture["sources"])  # init at backticked state

    wide_table_fixture["upstream"].write_text(TABLE_SONNET_PLAIN, encoding="utf-8")
    report = run_refresh(wide_table_fixture["sources"])
    delta = report["sources"][0]["model_delta"]

    assert delta["removed"] == [], (
        f"phantom removal on a pure formatting change: {delta['removed']}"
    )
    assert delta["added"] == [], (
        f"phantom add on a pure formatting change: {delta['added']}"
    )


def test_AC_CLP_MDLR_2_sonnet_detected_in_both_formats():
    """claude-sonnet-5 is detected whether backticked or plain in the ID
    row — the direct extraction proof behind the no-phantom-delta result."""
    assert "claude-sonnet-5" in extract_model_ids(TABLE_SONNET_BACKTICKED)
    assert "claude-sonnet-5" in extract_model_ids(TABLE_SONNET_PLAIN)


# ---------------------------------------------------------------------------
# AC.CLP-MDLR.3 — a genuine removal still fires
# ---------------------------------------------------------------------------

def test_AC_CLP_MDLR_3_true_removal_still_detected(wide_table_fixture):
    """A model genuinely dropped from the comparison table's ID row is
    still named in model_delta.removed — the fix does not blunt the real
    signal the tracker exists to catch."""
    run_refresh(wide_table_fixture["sources"])  # init: sonnet-5 present

    wide_table_fixture["upstream"].write_text(TABLE_SONNET_REMOVED, encoding="utf-8")
    report = run_refresh(wide_table_fixture["sources"])
    delta = report["sources"][0]["model_delta"]

    assert "claude-sonnet-5" in delta["removed"], (
        f"true removal not detected; got removed={delta['removed']}"
    )
    assert delta["added"] == []


# ---------------------------------------------------------------------------
# AC.CLP-MDLR.4 — no over-capture from incidental prose / non-canonical rows
# ---------------------------------------------------------------------------

def test_AC_CLP_MDLR_4_incidental_prose_id_not_captured():
    """A plain-text claude-* token that appears only in incidental prose
    (not backticked, not in a Claude-API-ID row) is NOT added to the
    lineup — the fix is not a page-wide plain-text grep."""
    text = """\
# Notes

An earlier draft mentioned claude-opus-3-legacy in passing, and a future
claude-experimental-9 was speculated about. Neither is a real listed model.

### Latest models comparison

| Feature           | Claude Opus 4.8 |
| ----------------- | --------------- |
| **Claude API ID** | claude-opus-4-8 |
"""
    ids = extract_model_ids(text)
    assert ids == ["claude-opus-4-8"], (
        f"incidental-prose ids polluted the lineup: {ids}"
    )


def test_AC_CLP_MDLR_4_bedrock_and_gcloud_rows_not_captured():
    """Bedrock (anthropic.claude-*) and Google-Cloud (claude-*@date) ID
    rows are excluded — only the Claude-API-ID row is authoritative."""
    text = """\
### Latest models comparison

| Feature             | Claude Sonnet 5              |
| ------------------- | ---------------------------- |
| **Claude API ID**   | claude-sonnet-5              |
| **AWS Bedrock ID**  | anthropic.claude-sonnet-5    |
| **Google Cloud ID** | claude-sonnet-5\\@20260609    |
"""
    ids = extract_model_ids(text)
    assert ids == ["claude-sonnet-5"], (
        f"non-canonical ID rows leaked into the lineup: {ids}"
    )


# ---------------------------------------------------------------------------
# AC.CLP-MDLR.5 — prose-only backticked model preserved (no false removal)
# ---------------------------------------------------------------------------

def test_AC_CLP_MDLR_5_prose_only_backticked_model_preserved():
    """A model present ONLY as a backticked ID in prose (no table row) is
    still detected, so the switch to structural table parsing does not drop
    it and fire a false removal. claude-mythos-5 has no table row in the
    fixture yet must survive."""
    ids = extract_model_ids(TABLE_SONNET_BACKTICKED)
    assert "claude-mythos-5" in ids, (
        f"prose-only backticked model dropped: {ids}"
    )
    # It is also present when the table reformats — the union is stable.
    assert "claude-mythos-5" in extract_model_ids(TABLE_SONNET_PLAIN)
