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

"""AC.LOCAL.1 — a LOCAL build produces an Acceptance record in the P0 shape,
judged by an independent check the builder did not control.

The outcome under test: the produced record carries every P0 field, and its
``met`` verdict is whatever the INDEPENDENT check returned — the producer
cannot fabricate it. A failing check yields an honest negative, never a retry.
(Any serialization satisfies this — the shape + producer-independence are the
load-bearing parts, not the encoding.)"""

from __future__ import annotations

import pytest

from loam.local_deploy_tier.acceptance import (
    Acceptance,
    CheckResult,
    produce_acceptance,
)


def test_record_carries_every_p0_field() -> None:
    """The record has id / statement / frozen / altitude / ladder + a verdict —
    the full P0 §2 shape, so a later gate can reference it and trace it up."""
    acc = produce_acceptance(
        id="AC.LOCAL.EXAMPLE",
        statement="the project builds and passes its own check locally",
        check=lambda: CheckResult(passed=True, detail="ok"),
        altitude=True,
    )
    assert acc.id == "AC.LOCAL.EXAMPLE"
    assert "builds" in acc.statement
    assert acc.frozen is True            # dispatched-build default: hash-pinned
    assert acc.altitude is True
    assert acc.ladder == ("AC.PO.1", "AC.PO.2")
    assert acc.check_fingerprint            # the criterion is pinned
    assert acc.met is True


def test_met_derives_from_the_check_not_a_self_report() -> None:
    """The verdict tracks the INDEPENDENT check: a passing check -> met; a
    failing check -> not met. The producer reads the check's result, it does
    not decide the verdict."""
    passed = produce_acceptance(
        id="AC.LOCAL.PASS",
        statement="green check",
        check=lambda: CheckResult(passed=True, detail="all green"),
    )
    failed = produce_acceptance(
        id="AC.LOCAL.FAIL",
        statement="red check",
        check=lambda: CheckResult(passed=False, detail="3 tests failed"),
    )
    assert passed.met is True
    assert failed.met is False


def test_failing_check_is_an_honest_negative_never_retried() -> None:
    """A definite 'not met, here is the evidence' is a complete result; the
    detail carries the plain-language reason and is NOT softened to a pass."""
    failed = produce_acceptance(
        id="AC.LOCAL.HONEST",
        statement="check that fails",
        check=lambda: CheckResult(passed=False, detail="migration did not apply"),
    )
    assert failed.met is False
    assert failed.is_honest_negative is True
    assert "migration did not apply" in failed.detail


def test_check_is_actually_invoked_once() -> None:
    """The producer RUNS the independent check (does not trust a passed-in
    boolean) — proven by the call counter the producer increments by running
    it."""
    calls = {"n": 0}

    def counting_check() -> CheckResult:
        calls["n"] += 1
        return CheckResult(passed=True, detail="ran")

    produce_acceptance(id="AC.LOCAL.RUN", statement="s", check=counting_check)
    assert calls["n"] == 1


def test_acceptance_cannot_be_constructed_with_a_self_reported_verdict() -> None:
    """A record minted OUTSIDE the producer (a hand-set ``met``) is refused —
    the only path to an Acceptance is through a real check run."""
    with pytest.raises(RuntimeError):
        Acceptance(
            id="AC.LOCAL.FAKE",
            statement="hand-set verdict",
            frozen=True,
            altitude=False,
            ladder=("AC.PO.1",),
            met=True,
            detail="I say it passed",
            check_fingerprint="deadbeef",
        )


def test_non_callable_check_is_refused_fail_closed() -> None:
    """A non-runnable check cannot produce an independent verdict, so the
    producer refuses rather than inventing a pass (fail-closed)."""
    with pytest.raises(TypeError):
        produce_acceptance(id="AC.LOCAL.X", statement="s", check="not callable")  # type: ignore[arg-type]
