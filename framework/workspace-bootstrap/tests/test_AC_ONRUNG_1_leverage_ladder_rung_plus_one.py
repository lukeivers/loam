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

"""AC.ONRUNG.1 — the leverage ladder read computes EXACTLY rung+1, never rung+2.

Owner ruling (Luke 13401 + 13403): loam reads where the distilled request sits on
a leverage ladder (doc -> template -> workflow -> system; spreadsheet ->
reusable-formula -> dashboard -> pipeline; one-off-task -> recurring-helper ->
automation) and the one-rung ask targets EXACTLY rung+1 — a doc may ask about a
TEMPLATE, never a WORKFLOW/SYSTEM (that would be two+ rungs). An unmatched request
falls to the generic deliverable ladder so rung+1 is always well-defined.
"""

from __future__ import annotations

from loam.workspace_bootstrap.translate_in_intake import _read_leverage_ladder


def test_AC_ONRUNG_1_doc_request_steps_to_template_not_workflow():
    read = _read_leverage_ladder("writing listing descriptions for properties")
    assert read.rung == "doc"
    assert read.next_rung == "template"  # EXACTLY rung+1
    assert read.next_rung not in ("workflow", "system")  # never rung+2+


def test_AC_ONRUNG_1_a_request_already_at_template_steps_to_workflow():
    read = _read_leverage_ladder("a reusable template for my client letters")
    assert read.rung == "template"
    assert read.next_rung == "workflow"  # the immediate next rung, not "system"


def test_AC_ONRUNG_1_spreadsheet_request_steps_to_reusable_formula():
    read = _read_leverage_ladder("reconciliation spreadsheet for the month-end")
    assert read.rung == "spreadsheet"
    assert read.next_rung == "reusable-formula"
    assert read.next_rung not in ("dashboard", "pipeline")


def test_AC_ONRUNG_1_unmatched_request_uses_generic_one_off_to_recurring():
    read = _read_leverage_ladder("calling clients back about their files")
    assert read.rung == "one-off-task"
    assert read.next_rung == "recurring-helper"  # generic ladder rung+1


def test_AC_ONRUNG_1_top_rung_request_has_no_next_rung():
    # A request that already names the TOP of its ladder has nothing one-rung-up.
    read = _read_leverage_ladder("a full document generator system")
    assert read.rung == "system"
    assert read.next_rung == ""  # no rung+2 to invent
    assert read.next_phrase == ""


def test_AC_ONRUNG_1_next_phrase_is_user_facing_and_never_two_rungs_up():
    # The user-facing phrase for a doc's rung+1 names a template, never a workflow.
    read = _read_leverage_ladder("drafting policyholder letters")
    assert "template" in read.next_phrase.lower()
    assert "workflow" not in read.next_phrase.lower()
    assert "system" not in read.next_phrase.lower()
