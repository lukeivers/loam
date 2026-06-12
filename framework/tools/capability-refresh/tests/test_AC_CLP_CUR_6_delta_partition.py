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

"""AC.CLP-CUR.6 — the D-CUR.4 partition: a delta that adds a new
capability claim, removes one, or touches a ``[user-intent phrasings]``
overlay does NOT land automatically (pending-delta for review); body
re-projections of existing entries DO land automatically.

Fixture per the AC's named verification: one upstream containing one
body change + one new claim + one removal; observe the partition."""

from __future__ import annotations

import json

from tests.conftest import UPSTREAM_V2

from capability_refresh.refresh import run_refresh


def _two_runs(fixture_repo):
    run_refresh(fixture_repo["sources"])  # initialise snapshot at v1
    fixture_repo["upstream"].write_text(UPSTREAM_V2, encoding="utf-8")
    return run_refresh(fixture_repo["sources"])  # the delta run


def test_AC_CLP_CUR_6_body_reprojection_auto_lands(fixture_repo):
    report = _two_runs(fixture_repo)
    rec = report["sources"][0]
    entry_text = fixture_repo["entry"].read_text()

    landed = [i for i in rec["auto_landed"] if i["kind"] == "reprojection"]
    assert len(landed) == 1, f"expected exactly one auto-landed re-projection: {rec}"
    assert "accepts four inputs" in entry_text, "same-statement update did not land"
    assert "accepts three inputs" not in entry_text, "superseded statement retained"


def test_AC_CLP_CUR_6_new_claim_and_removal_surface_not_land(fixture_repo):
    report = _two_runs(fixture_repo)
    rec = report["sources"][0]
    entry_text = fixture_repo["entry"].read_text()

    kinds = sorted(i["kind"] for i in rec["review"])
    assert "new-claim" in kinds and "removal" in kinds, f"partition wrong: {kinds}"
    # the new claim did NOT enter the corpus
    assert "SSH" not in entry_text, "new capability claim auto-landed (floor breach)"
    # the removed claim was NOT auto-deleted
    assert "keeps a log of every invocation" in entry_text, (
        "removal auto-landed (floor breach)"
    )

    pending = rec["pending_delta"]
    assert pending, "review-class delta did not surface a pending-delta file"
    pending_text = open(pending, encoding="utf-8").read()
    assert "new-claim" in pending_text and "SSH" in pending_text
    assert "removal" in pending_text and "keeps a log" in pending_text


def test_AC_CLP_CUR_6_overlay_touch_never_auto_lands(fixture_repo):
    """An upstream same-statement update whose superseded text lives only
    in the curated overlay is review-class — the overlay is never
    auto-edited."""
    # seed an upstream statement whose text exists verbatim ONLY in the
    # curated overlay section of the entry
    fixture_repo["upstream"].write_text(
        fixture_repo["upstream"].read_text() + '"run the widget tool"\n',
        encoding="utf-8",
    )
    run_refresh(fixture_repo["sources"])
    fixture_repo["upstream"].write_text(
        fixture_repo["upstream"].read_text().replace(
            '"run the widget tool"\n',
            '"run the widget tool right now"\n',
        ),
        encoding="utf-8",
    )
    report = run_refresh(fixture_repo["sources"])
    rec = report["sources"][0]

    overlay_items = [i for i in rec["review"] if i["kind"] == "overlay-touch"]
    assert overlay_items, f"overlay touch not surfaced as review-class: {rec}"
    overlay = fixture_repo["entry"].read_text().split("## [user-intent phrasings]")[1]
    assert '- "run the widget tool"' in overlay, "curated overlay was auto-edited"


def test_AC_CLP_CUR_6_curated_divergence_demotes_to_review(fixture_repo):
    """A same-statement update whose superseded text is no longer
    verbatim in the entry (curated drift) is surfaced, never guessed."""
    entry = fixture_repo["entry"]
    entry.write_text(
        entry.read_text().replace(
            "The widget tool accepts three inputs and returns one output.",
            "The widget tool takes a trio of inputs (curated rewording).",
        ),
        encoding="utf-8",
    )
    report = _two_runs(fixture_repo)
    rec = report["sources"][0]
    diverged = [i for i in rec["review"] if i["kind"] == "curated-divergence"]
    assert diverged, f"curated divergence not surfaced: {rec}"
    assert not rec["auto_landed"]
    assert "(curated rewording)" in entry.read_text(), "curated body was clobbered"


def test_AC_CLP_CUR_6_watch_source_deltas_are_all_review(fixture_repo, tmp_path):
    """A watch source (e.g. the changelog) has no projection target —
    every delta it produces is review-class by construction."""
    watch_upstream = tmp_path / "changelog.md"
    watch_upstream.write_text("## 1.0.0\n- first feature\n", encoding="utf-8")
    fixture_repo["sources"].write_text(
        "schema_version: 1\n"
        "sources:\n"
        "  - id: changelog\n"
        "    kind: watch\n"
        f"    url: file://{watch_upstream}\n"
        "    cadence: high-velocity\n",
        encoding="utf-8",
    )
    run_refresh(fixture_repo["sources"])
    watch_upstream.write_text(
        "## 1.1.0\n- a brand new capability\n## 1.0.0\n- first feature\n",
        encoding="utf-8",
    )
    report = run_refresh(fixture_repo["sources"])
    rec = report["sources"][0]
    assert rec["review"], "watch-source delta produced no review items"
    assert not rec["auto_landed"], "watch source auto-landed a delta"
    assert rec["pending_delta"] and "brand new capability" in open(
        rec["pending_delta"], encoding="utf-8"
    ).read()
