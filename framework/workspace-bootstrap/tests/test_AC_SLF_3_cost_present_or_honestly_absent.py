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

"""AC.SLF.3 — per-run cost/usage is honestly present-or-absent.

Plan: docs/plans/subloam-driver-fix.md  (§3 AC.SLF.3, decision D-COST)

The interactive driver emits NO machine result envelope (verified
2026-05-15, retired-benchmark-harness step-0 driver smoke §3,
archived on the pos3 side — no result JSON, no
usage fields, no /cost output for a subscription session). D-COST
therefore resolves AC.SLF.3 to **present-or-honestly-absent**, NOT
"a cost number always exists". The capture method (chosen here): the
driver issues an in-session ``/cost`` query after the loop settles and
parses the printed USD figure. This test pins the OUTCOME:

  - a real ``$N.NN`` printed on a /cost line -> a real figure,
    source "cost-command";
  - no parseable figure -> ``cost_usd is None`` and source "absent";
  - the figure is NEVER estimated/inferred/fabricated, and an
    unrelated ``$`` elsewhere in the transcript is NOT picked up as
    the session cost.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parents[3]
        / "framework"
        / "tools"
        / "subloam-driver"
        / "src"
    ),
)

from subloam_driver.driver import _parse_cost  # noqa: E402


def test_AC_SLF_3_real_cost_line_yields_real_figure() -> None:
    """A genuine /cost echo line -> the real figure, source tagged
    as coming from the cost command (not derived)."""
    transcript = (
        "⏺ done.\n"
        "❯ /cost\n"
        "Total cost:            $0.4213\n"
        "Total duration (API):  1m 2s\n"
    )
    cost, source = _parse_cost(transcript)
    assert cost == 0.4213
    assert source == "cost-command"


def test_AC_SLF_3_cost_line_with_trailing_detail() -> None:
    transcript = "Total cost: $1.07 (charged to subscription)\n"
    cost, source = _parse_cost(transcript)
    assert cost == 1.07
    assert source == "cost-command"


def test_AC_SLF_3_no_cost_figure_is_honest_absence() -> None:
    """The step-0-observed reality: a subscription session whose
    /cost surfaces NO USD figure. Absence is recorded as absent —
    NOT a zero, NOT an estimate, NOT a fabricated number."""
    transcript = (
        "❯ /cost\n"
        "You're on the Max plan; per-session USD is not shown.\n"
        "⏺ ok\n"
    )
    cost, source = _parse_cost(transcript)
    assert cost is None
    assert source == "absent"


def test_AC_SLF_3_empty_transcript_is_absent() -> None:
    cost, source = _parse_cost("")
    assert cost is None
    assert source == "absent"


def test_AC_SLF_3_unrelated_dollar_is_not_taken_as_cost() -> None:
    """A ``$`` that appears in model/shell output unrelated to cost
    must NOT be misread as the session cost — only a line that is
    about cost AND carries a figure counts. This is the
    never-fabricate guard: better honest-absent than a wrong number
    scraped from arbitrary transcript text."""
    transcript = (
        "⏺ Here is the script:\n"
        "FILE: run.sh\n"
        'echo "price is $9.99"\n'
        "tool_result: ok\n"
    )
    cost, source = _parse_cost(transcript)
    assert cost is None
    assert source == "absent"


def test_AC_SLF_3_driver_result_default_is_honest_absent() -> None:
    """A DriverResult constructed without a captured cost defaults to
    honest absence, never 0.0-as-if-real."""
    from subloam_driver import DriverResult

    r = DriverResult(
        transcript="",
        effective_turns=0,
        genuine_turns=0,
        file_blocks=(),
        exit_status=0,
        spawn_argv=(),
        spawn_env_config_dir="",
        workspace_root=Path("/tmp/x"),
    )
    assert r.cost_usd is None
    assert r.cost_source == "absent"
