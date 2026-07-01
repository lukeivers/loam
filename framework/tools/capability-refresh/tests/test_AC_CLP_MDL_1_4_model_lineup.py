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

"""AC.CLP-MDL.1-4 — model-lineup tracking extension.

AC.CLP-MDL.1: after a run that includes a model_parse:true watch source,
``.refresh/snapshots/<id>.txt`` contains the fetched content AND
``.refresh/model-lineup/<id>.json`` exists with a non-empty ``ids`` list.

AC.CLP-MDL.2 ★ (outcome-altitude): given a prior run whose model lineup
was {claude-opus-4-8, claude-sonnet-4-6} and a current upstream that adds
claude-sonnet-5, the tool emits a delta whose ``model_delta.added``
names ``["claude-sonnet-5"]``.  This is the exact real-world miss that
motivated the extension (Sonnet 5 shipped; the owner reported it manually;
the automated refresh never surfaced it).

AC.CLP-MDL.3: regression — existing fixture_repo (no model_parse sources)
runs with no model_delta field in the per-source record and no
``.refresh/model-lineup/`` directory created.

AC.CLP-MDL.4: ``cadence/routine-spec.md`` mentions model-data pull + delta
in both the daily and weekly routine prompt blocks.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

COMPONENT_ROOT = Path(__file__).resolve().parents[1]
SRC = COMPONENT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from capability_refresh.refresh import run_refresh  # noqa: E402


# ---------------------------------------------------------------------------
# Fixture — a minimal corpus with a model_parse:true watch source
# ---------------------------------------------------------------------------

# Minimal Markdown representing a model-overview page with two model IDs
# in backtick form — the v1 state (prior run).
MODELS_V1_MD = """\
# Models overview

| Claude API ID | `claude-opus-4-8` |
| Claude API ID | `claude-sonnet-4-6` |

Pricing and availability subject to change.
"""

# v2 state: same models plus the newly-shipped claude-sonnet-5.
MODELS_V2_MD = """\
# Models overview

| Claude API ID | `claude-opus-4-8` |
| Claude API ID | `claude-sonnet-4-6` |
| Claude API ID | `claude-sonnet-5` |

Pricing and availability subject to change.
"""


@pytest.fixture
def model_fixture(tmp_path):
    """Minimal corpus with a model_parse:true watch source (file:// upstream)."""
    repo = tmp_path / "repo"
    corpus = repo / "docs" / "capability-corpus"
    corpus.mkdir(parents=True)

    models_upstream = tmp_path / "models.md"
    models_upstream.write_text(MODELS_V1_MD, encoding="utf-8")

    sources = corpus / "sources.yaml"
    sources.write_text(
        "schema_version: 1\n"
        "sources:\n"
        "  - id: model-tracker\n"
        "    kind: watch\n"
        "    model_parse: true\n"
        f"    url: file://{models_upstream}\n"
        "    cadence: high-velocity\n",
        encoding="utf-8",
    )
    return {
        "repo": repo,
        "corpus": corpus,
        "upstream": models_upstream,
        "sources": sources,
    }


# ---------------------------------------------------------------------------
# AC.CLP-MDL.1 — corpus contains content + machine-derivable artifact
# ---------------------------------------------------------------------------

def test_AC_CLP_MDL_1_snapshot_and_lineup_artifact_created(model_fixture):
    """After a run with a model_parse:true source, the snapshot exists and
    the model-lineup artifact exists with a non-empty ids list."""
    corpus = model_fixture["corpus"]
    run_refresh(model_fixture["sources"])

    snap = corpus / ".refresh" / "snapshots" / "model-tracker.txt"
    assert snap.is_file(), "snapshot not created for model_parse watch source"
    assert snap.read_text(encoding="utf-8").strip(), "snapshot is empty"

    lineup = corpus / ".refresh" / "model-lineup" / "model-tracker.json"
    assert lineup.is_file(), "model-lineup artifact not created"
    data = json.loads(lineup.read_text(encoding="utf-8"))
    assert isinstance(data.get("ids"), list), "'ids' key missing or not a list"
    assert data["ids"], "ids list is empty after a run with model IDs in upstream"


def test_AC_CLP_MDL_1_extracted_ids_match_upstream(model_fixture):
    """The ids in the lineup artifact match the backtick-quoted IDs in
    the upstream Markdown exactly."""
    run_refresh(model_fixture["sources"])
    lineup = model_fixture["corpus"] / ".refresh" / "model-lineup" / "model-tracker.json"
    data = json.loads(lineup.read_text(encoding="utf-8"))
    assert data["ids"] == ["claude-opus-4-8", "claude-sonnet-4-6"], (
        f"extracted IDs differ from upstream: {data['ids']}"
    )


# ---------------------------------------------------------------------------
# AC.CLP-MDL.2 ★ — outcome-altitude delta test (the exact real-world miss)
# ---------------------------------------------------------------------------

def test_AC_CLP_MDL_2_delta_names_new_model_on_second_run(model_fixture):
    """Two-run fixture:
      Run 1: upstream has {claude-opus-4-8, claude-sonnet-4-6}.
      Run 2: upstream adds claude-sonnet-5.
    The run-2 report's model_delta.added names claude-sonnet-5.

    This is the exact real-world miss: Sonnet 5 shipped; the automated
    refresh never caught it; the owner reported it manually.
    AC.CLP-MDL.2 ★ (outcome-altitude — runs through production run_refresh).
    """
    # Run 1: initialise lineup at v1 (opus-4-8 + sonnet-4-6).
    report1 = run_refresh(model_fixture["sources"])
    rec1 = report1["sources"][0]
    assert rec1["model_delta"]["no_prior"] is True, (
        "first run should report no_prior=True"
    )

    # Run 2: upstream advances to v2 (adds claude-sonnet-5).
    model_fixture["upstream"].write_text(MODELS_V2_MD, encoding="utf-8")
    report2 = run_refresh(model_fixture["sources"])
    rec2 = report2["sources"][0]

    delta = rec2.get("model_delta")
    assert delta is not None, "model_delta missing from second-run report"
    assert delta["no_prior"] is False, "second run should have a prior lineup"
    assert delta["added"] == ["claude-sonnet-5"], (
        f"delta did not name claude-sonnet-5 as added; got: {delta['added']}"
    )
    assert delta["removed"] == [], (
        f"delta incorrectly reports removals: {delta['removed']}"
    )


def test_AC_CLP_MDL_2_removal_detected(model_fixture):
    """A model removed from the upstream is named in model_delta.removed."""
    # Initialise with v2 (has sonnet-5).
    model_fixture["upstream"].write_text(MODELS_V2_MD, encoding="utf-8")
    run_refresh(model_fixture["sources"])

    # v3: remove sonnet-5 (deprecated / withdrawn).
    model_fixture["upstream"].write_text(MODELS_V1_MD, encoding="utf-8")
    report = run_refresh(model_fixture["sources"])
    delta = report["sources"][0]["model_delta"]
    assert delta["removed"] == ["claude-sonnet-5"], (
        f"removed model not detected; got: {delta['removed']}"
    )
    assert delta["added"] == []


def test_AC_CLP_MDL_2_unchanged_lineup_emits_empty_delta(model_fixture):
    """When the upstream lineup does not change, added and removed are both
    empty and no_prior is False."""
    run_refresh(model_fixture["sources"])  # init
    report = run_refresh(model_fixture["sources"])  # second run, same upstream
    delta = report["sources"][0]["model_delta"]
    assert delta["added"] == [] and delta["removed"] == [], (
        f"unchanged lineup produced a non-empty delta: {delta}"
    )
    assert delta["no_prior"] is False


# ---------------------------------------------------------------------------
# AC.CLP-MDL.3 — regression: existing sources run unchanged
# ---------------------------------------------------------------------------

def test_AC_CLP_MDL_3_existing_sources_produce_no_model_delta(fixture_repo):
    """The existing fixture_repo (no model_parse sources) runs with
    no model_delta in the per-source record and no model-lineup directory."""
    corpus = fixture_repo["corpus"]
    report = run_refresh(fixture_repo["sources"])

    for rec in report["sources"]:
        assert rec.get("model_delta") is None, (
            f"source {rec['id']!r} has unexpected model_delta: {rec['model_delta']}"
        )

    lineup_dir = corpus / ".refresh" / "model-lineup"
    assert not lineup_dir.exists(), (
        "model-lineup directory created for non-model_parse sources"
    )


def test_AC_CLP_MDL_3_model_parse_flag_rejected_on_entry_kind(tmp_path):
    """model_parse:true on a kind:entry source is a manifest error."""
    from capability_refresh.sources import SourceManifestError, load_sources

    repo = tmp_path / "repo"
    corpus = repo / "docs" / "capability-corpus"
    (corpus / "claude-code").mkdir(parents=True)
    entry = corpus / "claude-code" / "widget.md"
    entry.write_text("# Widget\n## Source\n```\nsource_url: x\n```\n", encoding="utf-8")

    bad_sources = corpus / "sources.yaml"
    bad_sources.write_text(
        "schema_version: 1\n"
        "sources:\n"
        "  - id: bad\n"
        "    kind: entry\n"
        "    entry: claude-code/widget.md\n"
        "    url: https://example.com/\n"
        "    cadence: high-velocity\n"
        "    model_parse: true\n",
        encoding="utf-8",
    )
    with pytest.raises(SourceManifestError, match="model_parse"):
        load_sources(bad_sources)


# ---------------------------------------------------------------------------
# AC.CLP-MDL.4 — routine-spec.md mentions model-data pull + delta
# ---------------------------------------------------------------------------

def test_AC_CLP_MDL_4_routine_spec_names_model_data():
    """cadence/routine-spec.md's daily prompt block mentions the model-data
    pull and delta step."""
    spec = COMPONENT_ROOT / "cadence" / "routine-spec.md"
    assert spec.is_file(), "routine-spec.md missing"
    text = spec.read_text(encoding="utf-8")
    # Both "model" references should appear — the daily step explanation
    # and the weekly note.
    assert "model" in text.lower(), (
        "routine-spec.md does not mention model-data pull"
    )
    assert "model-delta" in text or "model_delta" in text or "model lineup" in text.lower(), (
        "routine-spec.md does not mention the model-delta output"
    )
