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

"""AC.CLP-CUR.5 — each Class A entry carries a fresh ``source_fetch_ts``,
and an entry whose source fetch fails is marked STALE rather than
silently retained as current."""

from __future__ import annotations

import datetime as dt
import re

from capability_refresh.refresh import run_refresh


def _source_block(entry_path):
    return entry_path.read_text(encoding="utf-8").split("## Source", 1)[1]


def test_AC_CLP_CUR_5_fresh_fetch_ts_stamped(fixture_repo):
    start = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    run_refresh(fixture_repo["sources"])
    block = _source_block(fixture_repo["entry"])
    m = re.search(r"source_fetch_ts:\s*(\S+)", block)
    assert m, "source_fetch_ts line missing after refresh"
    stamped = dt.datetime.fromisoformat(m.group(1).replace("Z", "+00:00"))
    assert stamped >= start, f"stale timestamp retained: {m.group(1)}"
    assert "source_status: current" in block


def test_AC_CLP_CUR_5_fetch_failure_marks_stale_not_silently_current(fixture_repo):
    """Simulated fetch failure: the entry is marked stale; the body and
    the last good timestamp are retained untouched."""
    run_refresh(fixture_repo["sources"])
    good_block = _source_block(fixture_repo["entry"])
    good_ts = re.search(r"source_fetch_ts:\s*(\S+)", good_block).group(1)
    body_before = fixture_repo["entry"].read_text().split("## Source")[0]

    fixture_repo["upstream"].unlink()  # upstream goes away -> fetch fails
    report = run_refresh(fixture_repo["sources"])

    assert report["sources"][0]["status"] == "fetch-failed"
    block = _source_block(fixture_repo["entry"])
    assert "source_status: stale (fetch failed" in block, (
        "entry silently retained as current after a failed fetch"
    )
    assert f"source_fetch_ts: {good_ts}" in block, (
        "last good fetch timestamp must be retained on failure"
    )
    assert fixture_repo["entry"].read_text().split("## Source")[0] == body_before, (
        "entry body must be untouched on a failed fetch"
    )


def test_AC_CLP_CUR_5_recovery_clears_stale(fixture_repo, tmp_path):
    """A later successful fetch returns the entry to ``current``."""
    run_refresh(fixture_repo["sources"])
    saved = fixture_repo["upstream"].read_text()
    fixture_repo["upstream"].unlink()
    run_refresh(fixture_repo["sources"])
    assert "source_status: stale" in _source_block(fixture_repo["entry"])

    fixture_repo["upstream"].write_text(saved, encoding="utf-8")
    run_refresh(fixture_repo["sources"])
    block = _source_block(fixture_repo["entry"])
    assert "source_status: current" in block
    assert "stale" not in block
