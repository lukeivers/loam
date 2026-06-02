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

"""AC.BR-S.1 — outcome-altitude (outcome-altitude: true).

A real "loam broke" entry at the production entry-point (``run_bug_report``),
NO pre-arranged state: interview -> assemble -> review (one item declined) ->
local-fallback chosen -> assert a REAL report file on disk AND zero egress;
then a second run choosing "send" -> assert the approved set (minus the
declined item) posts through the REAL gate.

No stub: ``run_bug_report`` is the production entry-point the ``loam report``
verb drives; the RecordingTransport is the real send sink and observes exactly
what left.
"""

from __future__ import annotations

from loam.egress_consent.bug_report import (
    CandidateFile,
    ReportInterview,
    run_bug_report,
)
from loam.egress_consent.bundle import ItemDecision


def _interview() -> ReportInterview:
    return ReportInterview(
        what_doing="writing a chapter",
        expected="my work would save",
        happened="loam closed with an error",
    )


def test_local_fallback_run_writes_file_and_zero_egress(tmp_path, transport) -> None:
    out = tmp_path / "loam-report.txt"
    outcome = run_bug_report(
        interview=_interview(),
        loam_version="1.0.1",
        os_name="Darwin",
        candidate_files=(
            CandidateFile(
                plain_summary="The file you were working on",
                content=b"my chapter draft",
                is_log=False,
            ),
        ),
        # The file defaults to declined; the user keeps it declined.
        decisions=(),
        choice="local",
        out_path=out,
        transport=transport,
    )
    # A REAL artefact on disk.
    assert out.is_file()
    assert outcome.local_path == out
    assert outcome.egress_occurred is False
    # ZERO egress — the transport was never called.
    assert transport.sends == []
    body = out.read_text(encoding="utf-8")
    assert "loam closed with an error" in body


def test_send_run_posts_approved_set_minus_declined_through_gate(
    tmp_path, transport
) -> None:
    # The user declines item 1 (the note) by its position on the review list —
    # the number they actually see. No pre-arranged state, no pre-known ids:
    # run_bug_report assembles internally and the user refers to the position.
    outcome = run_bug_report(
        interview=_interview(),
        loam_version="1.0.1",
        os_name="Darwin",
        candidate_files=(
            CandidateFile(
                plain_summary="The file you were working on",
                content=b"PRIVATE-DRAFT-CONTENT",
                is_log=False,
            ),
        ),
        decisions=((1, ItemDecision.declined),),  # decline the note by position
        choice="send",
        transport=transport,
    )
    assert outcome.egress_occurred is True
    assert outcome.released is not None
    assert outcome.released.state.value == "RELEASED"

    # The approved set posted through the gate; the declined note + the
    # default-declined file are NOT in the payload.
    payload = transport.last_payload_bytes
    assert b"1.0.1" in payload  # approved version (item 2)
    assert b"Darwin" in payload  # approved OS (item 3)
    assert b"PRIVATE-DRAFT-CONTENT" not in payload  # default-declined file
    # The declined note's text (the user's words) is not present.
    assert b"writing a chapter" not in payload
