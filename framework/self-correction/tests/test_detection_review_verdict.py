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

"""CR4 — review-verdict IPC trigger (ruling #1)."""

from __future__ import annotations

from loam.self_correction import (
    TriggerSource,
    build_trigger_from_review_verdict,
)


def test_CR4_fail_verdict_fires_trigger() -> None:
    tr = build_trigger_from_review_verdict(
        scope_id="scope-build-99",
        verdict="fail",
        reasons=["spec not satisfied", "missing test"],
        reporter="nora",
    )
    assert tr is not None
    assert tr.source == TriggerSource.review_verdict
    assert tr.reporter == "nora"
    assert tr.scope_id == "scope-build-99"
    assert tr.failure_class_hint == "review_verdict_fail"
    assert tr.raw_payload["verdict"] == "fail"
    assert tr.raw_payload["reasons"] == ["spec not satisfied", "missing test"]


def test_CR4_pass_verdict_does_not_fire() -> None:
    tr = build_trigger_from_review_verdict(
        scope_id="scope-99",
        verdict="pass",
        reasons=[],
        reporter="nora",
    )
    assert tr is None


def test_CR4_unknown_verdict_does_not_fire() -> None:
    tr = build_trigger_from_review_verdict(
        scope_id="scope-99",
        verdict="abstain",
        reasons=[],
        reporter="nora",
    )
    assert tr is None
