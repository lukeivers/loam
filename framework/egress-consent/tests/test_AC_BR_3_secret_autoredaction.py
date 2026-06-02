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

"""AC.BR.3 — secret auto-redaction pre-review.

Candidate item bytes matching the safety-layer secret-pattern floor are
redacted during assembly, BEFORE the review surface is rendered — the user is
never shown, and can never accidentally ship, a secret loam caught. Composes
the sealed ``CONTENT_PATTERNS`` floor (Lens 1).
"""

from __future__ import annotations

from loam.egress_consent.bug_report import (
    CandidateFile,
    ReportInterview,
    assemble_report_bundle,
)
from loam.egress_consent.redaction import SECRET_PLACEHOLDER, redact_secrets


def test_redact_secrets_catches_a_real_floor_pattern() -> None:
    # An Anthropic API key shape — a CONTENT_PATTERNS floor member.
    raw = b"here is my key sk-ant-abcdefghij1234567890ABCD and more text"
    clean, matched = redact_secrets(raw)
    assert "anthropic-api-key" in matched
    assert b"sk-ant-abcdefghij1234567890ABCD" not in clean
    assert SECRET_PLACEHOLDER.encode("utf-8") in clean


def test_secret_in_a_candidate_is_gone_before_the_user_sees_it() -> None:
    interview = ReportInterview(
        what_doing="testing",
        # The user pasted a secret into their description.
        expected="it works with sk-ant-SECRETSECRETSECRET1234567 set",
        happened="error",
    )
    bundle, matched = assemble_report_bundle(
        interview=interview,
        loam_version="1.0.1",
        os_name="Darwin",
        candidate_files=(
            CandidateFile(
                plain_summary="A log",
                content=b"AKIAIOSFODNN7EXAMPLE was in the log",
                is_log=True,
            ),
        ),
    )
    # The note no longer carries the pasted secret.
    note = bundle.items[0]
    assert b"sk-ant-SECRETSECRETSECRET1234567" not in note.exact_bytes
    # The log candidate's AWS-key shape is gone from its bytes too.
    log_item = next(it for it in bundle.items if it.plain_summary == "A log")
    assert b"AKIAIOSFODNN7EXAMPLE" not in log_item.exact_bytes
    # The floor reported at least the two patterns it caught.
    assert "anthropic-api-key" in matched
    assert "aws-access-key" in matched
