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

"""AC.BR.1 — interactive triage.

A real "report this" entry triggers a plain-language interview that
characterizes the issue before any bundle leaves DRAFTING. The interview's
answers become the user's own-words note in the assembled bundle.
"""

from __future__ import annotations

from loam.egress_consent.bug_report import (
    ReportInterview,
    assemble_report_bundle,
)
from loam.egress_consent.bundle import BundleState


def test_interview_answers_become_the_report_note() -> None:
    interview = ReportInterview(
        what_doing="saving my notes",
        expected="it would save",
        happened="it showed an error and closed",
    )
    bundle, _ = assemble_report_bundle(
        interview=interview, loam_version="1.0.1", os_name="Darwin"
    )
    note = bundle.item(bundle.items[0].item_id)
    text = note.exact_bytes.decode("utf-8")
    assert "saving my notes" in text
    assert "it would save" in text
    assert "it showed an error and closed" in text


def test_assembly_is_local_only_review_state_not_drafting_terminal() -> None:
    """After assembly the bundle is AWAITING_REVIEW — nothing has left yet."""
    interview = ReportInterview(
        what_doing="x", expected="y", happened="z"
    )
    bundle, _ = assemble_report_bundle(
        interview=interview, loam_version="1.0.1", os_name="Darwin"
    )
    # Assembled = ready for review, still a no-egress state.
    assert bundle.state == BundleState.AWAITING_REVIEW
    from loam.egress_consent.bundle import NO_EGRESS_STATES

    assert bundle.state in NO_EGRESS_STATES
