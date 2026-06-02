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

"""AC.BR.2 — files/logs default-declined.

Any file or log candidate item defaults to ``declined``; it is included only
on an explicit per-item approve. Files NEVER default to "will send."
"""

from __future__ import annotations

from loam.egress_consent.bug_report import (
    CandidateFile,
    ReportInterview,
    assemble_report_bundle,
)
from loam.egress_consent.bundle import ItemDecision, ItemKind
from loam.egress_consent.review import apply_decision


def _assemble_with_files():
    interview = ReportInterview(what_doing="x", expected="y", happened="z")
    return assemble_report_bundle(
        interview=interview,
        loam_version="1.0.1",
        os_name="Darwin",
        candidate_files=(
            CandidateFile(
                plain_summary="The file you were working on",
                content=b"my document",
                is_log=False,
            ),
            CandidateFile(
                plain_summary="A recent activity log",
                content=b"log lines here",
                is_log=True,
            ),
        ),
    )


def test_every_file_and_log_defaults_to_declined() -> None:
    bundle, _ = _assemble_with_files()
    file_items = [
        it for it in bundle.items
        if it.kind in (ItemKind.file, ItemKind.log_line)
    ]
    assert file_items, "no file/log items assembled"
    for it in file_items:
        assert it.decision == ItemDecision.declined, (
            f"file/log item {it.plain_summary!r} did not default to declined"
        )


def test_file_included_only_after_explicit_approve() -> None:
    bundle, _ = _assemble_with_files()
    file_item = next(it for it in bundle.items if it.kind == ItemKind.file)
    # Declined by default -> not in the shippable set.
    assert file_item.item_id not in {it.item_id for it in bundle.shippable_items}
    # Explicit approve includes it.
    bundle = apply_decision(bundle, file_item.item_id, ItemDecision.approved)
    assert file_item.item_id in {it.item_id for it in bundle.shippable_items}
