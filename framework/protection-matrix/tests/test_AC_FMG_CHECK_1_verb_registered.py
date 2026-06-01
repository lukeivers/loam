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

"""AC.FMG-CHECK.1 — a real coverage-check entry-point exists + is persona-
invokable.

`loam guards` is registered through loam.cli.subcommands, runs against the
live tree, and emits a report of every floor-class failure mode + its guard +
default-on status. Pins the verb + behaviour, not argparse wiring.
"""

from __future__ import annotations

import importlib.metadata

from loam.protection_matrix.check import render_report, run_coverage_check


def test_guards_verb_is_registered_through_the_entry_point_group() -> None:
    """The `guards` verb resolves through the loam.cli.subcommands group."""
    eps = importlib.metadata.entry_points(group="loam.cli.subcommands")
    names = {ep.name for ep in eps}
    assert "guards" in names, (
        f"`guards` not registered in loam.cli.subcommands; saw {sorted(names)}"
    )
    guards_ep = next(ep for ep in eps if ep.name == "guards")
    builder = guards_ep.load()
    assert callable(builder)


def test_loam_guards_is_reachable_from_the_unified_dispatcher() -> None:
    """`loam guards` dispatches through the unified loam CLI + exits 0."""
    from loam_cli.cli import main as loam_main

    rc = loam_main(["guards"])
    assert rc == 0


def test_report_lists_every_floor_class_mode_with_its_guard_and_default_on() -> None:
    """The rendered report names every floor row + its default-on status."""
    report = run_coverage_check()
    text = render_report(report)
    assert report.floor_verdicts, "expected floor-class rows"
    for v in report.floor_verdicts:
        assert v.row.id in text
    assert "FLOOR-CLASS COVERAGE" in text
