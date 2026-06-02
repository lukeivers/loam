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

"""Guard: a caught secret never survives into a bundle, payload, or local file.

Defence-in-depth over AC.BR.3 — once the floor redacts a secret at assembly,
the original must not reappear in: the assembled item bytes, the released gate
payload, or the local-fallback file on disk.
"""

from __future__ import annotations

from loam.egress_consent.bug_report import (
    ReportInterview,
    assemble_report_bundle,
    take_local_fallback,
)

SECRET = b"sk-ant-LEAKTEST1234567890abcdEFGH"


def test_secret_absent_from_assembled_bundle() -> None:
    interview = ReportInterview(
        what_doing="x",
        expected="key is " + SECRET.decode(),
        happened="error",
    )
    bundle, matched = assemble_report_bundle(
        interview=interview, loam_version="1.0.1", os_name="Darwin"
    )
    assert "anthropic-api-key" in matched
    for it in bundle.items:
        assert SECRET not in it.exact_bytes


def test_secret_absent_from_local_fallback_file(tmp_path) -> None:
    interview = ReportInterview(
        what_doing="x",
        expected="key is " + SECRET.decode(),
        happened="error",
    )
    bundle, _ = assemble_report_bundle(
        interview=interview, loam_version="1.0.1", os_name="Darwin"
    )
    out = tmp_path / "r.txt"
    take_local_fallback(bundle, out_path=out)
    assert SECRET not in out.read_bytes()
