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

"""AC.CLP-CUR.3 — a recurring refresh exists that, unattended, projects
Class A entries from their canonical upstream sources on the locked
cadence classes and emits a structured delta.

Verified here at the PRODUCTION entry-point altitude: the same
``python -m capability_refresh`` command the cadence binding (cloud
routine / launchd fallback) invokes, run as a subprocess with no
pre-arranged refresh state. The cadence-binding artefacts themselves
(routine spec + launchd plists + one-command activation) are inspected
as files — activation of the LIVE binding is owner-gated (plan
section-status; dispatcher gate 2026-06-11)."""

from __future__ import annotations

import json
import os
import plistlib
import subprocess
import sys
from pathlib import Path

COMPONENT_ROOT = Path(__file__).resolve().parents[1]
SRC = COMPONENT_ROOT / "src"


def _run_cli(args, cwd):
    env = dict(os.environ)
    env["PYTHONPATH"] = str(SRC) + os.pathsep + env.get("PYTHONPATH", "")
    return subprocess.run(
        [sys.executable, "-m", "capability_refresh"] + args,
        cwd=str(cwd), env=env, capture_output=True, text=True, timeout=120,
    )


def test_AC_CLP_CUR_3_production_cli_runs_full_cycle(fixture_repo):
    """One full cycle through the production CLI: fetch -> project ->
    snapshot -> stamp -> structured delta on disk."""
    corpus = fixture_repo["corpus"]
    res = _run_cli(["--sources", str(fixture_repo["sources"])], cwd=fixture_repo["repo"])
    assert res.returncode == 0, res.stderr + res.stdout

    snap = corpus / ".refresh" / "snapshots" / "widget.txt"
    assert snap.is_file(), "snapshot not initialised by the production CLI"
    last_run = corpus / ".refresh" / "last-run.json"
    assert last_run.is_file(), "structured delta not emitted"
    report = json.loads(last_run.read_text())
    assert report["sources"][0]["id"] == "widget"
    assert report["sources"][0]["status"] == "initialized"

    entry_text = fixture_repo["entry"].read_text()
    assert "source_status: current" in entry_text
    assert "file://" in entry_text, (
        "seed internal: source_url not replaced by the real upstream URL "
        "on first re-projection (D-CUR.3)"
    )


def test_AC_CLP_CUR_3_cadence_class_filter(fixture_repo):
    """A long-form source is NOT fetched by a high-velocity run — the
    locked cadence classes select, as data."""
    corpus = fixture_repo["corpus"]
    weekly_upstream = fixture_repo["upstream"].parent / "weekly.md"
    weekly_upstream.write_text("Weekly long-form content.\n", encoding="utf-8")
    fixture_repo["sources"].write_text(
        fixture_repo["sources"].read_text()
        + "  - id: weekly\n"
          "    kind: watch\n"
          f"    url: file://{weekly_upstream}\n"
          "    cadence: long-form\n",
        encoding="utf-8",
    )
    res = _run_cli(
        ["--sources", str(fixture_repo["sources"]), "--cadence-class", "high-velocity"],
        cwd=fixture_repo["repo"],
    )
    assert res.returncode == 0, res.stderr
    assert (corpus / ".refresh" / "snapshots" / "widget.txt").is_file()
    assert not (corpus / ".refresh" / "snapshots" / "weekly.txt").exists(), (
        "long-form source fetched during a high-velocity cadence run"
    )
    report = json.loads((corpus / ".refresh" / "last-run.json").read_text())
    assert [s["id"] for s in report["sources"]] == ["widget"]


def test_AC_CLP_CUR_3_unchanged_second_cycle_is_clean(fixture_repo):
    """Two cycles against an unchanged upstream: second run reports
    'unchanged', no pending-deltas, fresh stamp."""
    _run_cli(["--sources", str(fixture_repo["sources"])], cwd=fixture_repo["repo"])
    res = _run_cli(["--sources", str(fixture_repo["sources"])], cwd=fixture_repo["repo"])
    assert res.returncode == 0
    report = json.loads(
        (fixture_repo["corpus"] / ".refresh" / "last-run.json").read_text()
    )
    assert report["sources"][0]["status"] == "unchanged"
    assert not (fixture_repo["corpus"] / "pending-deltas").exists()


def test_AC_CLP_CUR_3_cadence_binding_artefacts_ship_in_component():
    """The unattended cadence binding ships: routine spec (primary,
    activation owner-gated) + launchd plists (fallback) + a documented
    one-command activation. The schedules encode the locked classes
    (high-velocity ~daily, long-form ~weekly)."""
    cadence = COMPONENT_ROOT / "cadence"
    spec = cadence / "routine-spec.md"
    activation = cadence / "ACTIVATION.md"
    assert spec.is_file(), "cloud-routine spec missing"
    assert activation.is_file(), "activation doc missing"
    spec_text = spec.read_text()
    assert "high-velocity" in spec_text and "long-form" in spec_text
    assert "/schedule" in spec_text

    daily = cadence / "launchd" / "com.loam.capability-refresh-daily.plist"
    weekly = cadence / "launchd" / "com.loam.capability-refresh-weekly.plist"
    for p in (daily, weekly):
        assert p.is_file(), f"launchd fallback plist missing: {p.name}"
        with p.open("rb") as fh:
            plist = plistlib.load(fh)
        assert "StartCalendarInterval" in plist
        joined = " ".join(plist["ProgramArguments"])
        assert "capability_refresh" in joined or "capability-refresh" in joined
    with daily.open("rb") as fh:
        assert "Weekday" not in plistlib.load(fh)["StartCalendarInterval"]
    with weekly.open("rb") as fh:
        assert "Weekday" in plistlib.load(fh)["StartCalendarInterval"]
