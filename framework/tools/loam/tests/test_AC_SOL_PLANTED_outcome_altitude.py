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

"""★ AC.SOL-PLANTED.1 (outcome-altitude: true) — a REAL planted
"dark"-for-live divergence is CAUGHT at the real entry-point.

A doc is planted that CLAIMS a currently-live component is "dark"/
"unbuilt" (the literal shape of today's drift — loam-vnext-build-plan.md
§6 calling live FBM dark). The REAL audit entry-point — the `loam audit`
verb's production dispatch, with NO pre-arranged internal comparator
state — is invoked against it and CATCHES the divergence.

This test drives the production CLI dispatch path (`loam_cli.cli.main`
→ entry-point-discovered `audit` subcommand → `dispatch`), NOT the inner
status function. Per the AC it may NOT be satisfied by a unit test of
`classify_build_status` / `compare_claim` in isolation — those have
their own tests; THIS one proves the mechanism catches the exact same
shape automatically at the real verb entry-point.
"""

from __future__ import annotations

from pathlib import Path

import pytest

# The canonical loam repo root (4 parents up from this test file:
# tests/ → tools/loam → tools → framework → loam(repo)).
REPO_ROOT = Path(__file__).resolve().parents[4]


@pytest.fixture
def planted_dark_for_live_doc(tmp_path: Path) -> Path:
    """A FIXTURE doc (never a real canonical doc — plan halt-trigger 5)
    claiming a live component is dark, in the literal shape of today's
    drift."""
    doc = tmp_path / "stale-vnext-plan.md"
    doc.write_text(
        "# v-next build plan (planted fixture mirroring §6 drift)\n\n"
        "## §6 build status\n\n"
        "The episode store is built but not wired live.\n\n"
        "fbm-keep-pace-hook: dark\n"
        "fbm-episode-store: unbuilt\n",
        encoding="utf-8",
    )
    return doc


def test_AC_SOL_PLANTED_1_real_verb_catches_planted_dark_for_live(
    planted_dark_for_live_doc: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """outcome-altitude: drive the REAL `loam audit` production dispatch
    (the CLI entry point) against the planted divergence. It must CATCH
    it (non-zero exit) and report the doc claims dark while ground truth
    says live."""
    from loam_cli.cli import main

    # The production CLI dispatch — exactly what `loam audit ...` runs.
    # No pre-arranged comparator state: the record is derived fresh from
    # the real repo's ground truth inside the verb.
    rc = main(
        [
            "audit",
            "--repo-root",
            str(REPO_ROOT),
            "--doc",
            str(planted_dark_for_live_doc),
        ]
    )
    captured = capsys.readouterr().out

    # CAUGHT: non-zero exit (the verb surfaces; the gate arm would
    # HARD-BLOCK on the same finding).
    assert rc == 1, f"the real verb must catch the planted divergence; got rc={rc}"
    assert "DIVERGENCE" in captured
    # It reports the doc claims dark while ground truth says live.
    assert "fbm-episode-store" in captured or "fbm-keep-pace-hook" in captured
    assert "ground truth says" in captured
    # The live side is named (merged / wired), proving it read real refs +
    # config, not the doc's prose.
    assert ("merged" in captured) or ("wired" in captured)


def test_AC_SOL_PLANTED_1_real_verb_clean_on_accurate_doc(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """The complement at the real entry-point: an ACCURATE doc (claims
    agree with ground truth) passes clean (rc=0). Proves the catch is
    a real divergence detection, not a blanket reject."""
    from loam_cli.cli import main

    accurate = tmp_path / "accurate.md"
    accurate.write_text(
        "# accurate\n\nfbm-episode-store: merged\nfbm-keep-pace-hook: wired\n",
        encoding="utf-8",
    )
    rc = main(
        ["audit", "--repo-root", str(REPO_ROOT), "--doc", str(accurate)]
    )
    captured = capsys.readouterr().out
    assert rc == 0
    assert "CLEAN" in captured
