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

"""AC.BR.4 — friendly destination + always-available local fallback.

The default destination carries no technical jargon to the user; the
local-only fallback is always offered and lands a real on-disk artefact the
user controls.
"""

from __future__ import annotations

from loam.self_correction.recovery_surface import find_internal_vocabulary

from loam.egress_consent.bug_report import (
    FRIENDLY_INTAKE_NAME,
    ReportInterview,
    assemble_report_bundle,
    take_local_fallback,
)


def test_friendly_destination_carries_no_technical_jargon() -> None:
    name = FRIENDLY_INTAKE_NAME
    lowered = name.lower()
    for jargon in ("github", "issue", "repo", "pull request", "endpoint", "url"):
        assert jargon not in lowered, f"destination name leaks jargon: {jargon}"
    # And it is plain-language clean per the shared vocab probe.
    assert find_internal_vocabulary(name) == ()


def test_local_fallback_writes_a_real_file_with_zero_egress(tmp_path) -> None:
    interview = ReportInterview(
        what_doing="x", expected="y", happened="it broke"
    )
    bundle, _ = assemble_report_bundle(
        interview=interview, loam_version="1.0.1", os_name="Darwin"
    )
    out = tmp_path / "loam-report.txt"
    outcome = take_local_fallback(bundle, out_path=out)
    assert outcome.egress_occurred is False
    assert outcome.local_path == out
    assert out.is_file()
    body = out.read_text(encoding="utf-8")
    assert "nothing was sent" in body
    assert "it broke" in body


def test_local_fallback_is_a_terminal_no_egress_state(tmp_path) -> None:
    from loam.egress_consent.bundle import NO_EGRESS_STATES

    interview = ReportInterview(what_doing="x", expected="y", happened="z")
    bundle, _ = assemble_report_bundle(
        interview=interview, loam_version="1.0.1", os_name="Darwin"
    )
    outcome = take_local_fallback(bundle, out_path=tmp_path / "r.txt")
    assert outcome.bundle.state in NO_EGRESS_STATES
