"""D5 — creation-trigger detector.

Acceptance (brief D5):
- Five signal types detectable from observable events.
- Threshold rubric with concrete numbers, tunable per workspace.
- Threshold crossed → judgment LLM call; output yes | no | defer.
- `yes` → triggers authoring pipeline (tested in D6 integration).
- `no` → rejection recorded.
- `defer` → re-check scheduled after delay.
"""

from __future__ import annotations

import time

import pytest

from src.creation_triggers import (
    CreationTrigger,
    CreationTriggerDetector,
    JudgmentResult,
    JudgmentVerdict,
    ThresholdRubric,
    TriggerSignal,
)


# ---- rubric + signal types ------------------------------------------


def test_defaults_cover_all_five_signals():
    d = ThresholdRubric.defaults()
    assert set(d.keys()) == set(TriggerSignal)


def test_defaults_have_concrete_numbers():
    d = ThresholdRubric.defaults()
    for r in d.values():
        assert r.min_count > 0
        assert r.window_seconds > 0


def test_rubric_tunable_per_workspace():
    d = ThresholdRubric.defaults()
    d[TriggerSignal.request_decline] = ThresholdRubric(
        signal=TriggerSignal.request_decline,
        min_count=1,
        window_seconds=60.0,
    )
    detector = CreationTriggerDetector(rubrics=d)
    detector.observe(
        CreationTrigger(
            signal=TriggerSignal.request_decline,
            domain="cooking",
            observed_at=time.time(),
        )
    )
    assert detector.threshold_crossed(TriggerSignal.request_decline, "cooking")


# ---- window counting -------------------------------------------------


def test_observations_outside_window_not_counted():
    detector = CreationTriggerDetector()
    # 8 days ago on a 7-day window; not counted.
    detector.observe(
        CreationTrigger(
            signal=TriggerSignal.request_decline,
            domain="law",
            observed_at=time.time() - 8 * 86_400,
        )
    )
    assert (
        detector.count_in_window(TriggerSignal.request_decline, "law") == 0
    )


def test_observations_in_window_counted():
    detector = CreationTriggerDetector()
    now = time.time()
    for _ in range(3):
        detector.observe(
            CreationTrigger(
                signal=TriggerSignal.request_decline,
                domain="law",
                observed_at=now - 60,
            )
        )
    assert detector.count_in_window(TriggerSignal.request_decline, "law") == 3


def test_same_signal_different_domains_bucketed_separately():
    detector = CreationTriggerDetector()
    now = time.time()
    for domain in ("law", "law", "finance"):
        detector.observe(
            CreationTrigger(
                signal=TriggerSignal.request_decline,
                domain=domain,
                observed_at=now,
            )
        )
    assert detector.count_in_window(TriggerSignal.request_decline, "law") == 2
    assert detector.count_in_window(TriggerSignal.request_decline, "finance") == 1


# ---- threshold-crossed ----------------------------------------------


def test_threshold_not_crossed_below_min_count():
    detector = CreationTriggerDetector()
    now = time.time()
    # default for request_decline is 3
    for _ in range(2):
        detector.observe(
            CreationTrigger(
                signal=TriggerSignal.request_decline,
                domain="law",
                observed_at=now,
            )
        )
    assert not detector.threshold_crossed(
        TriggerSignal.request_decline, "law", now=now
    )


def test_threshold_crossed_at_min_count():
    detector = CreationTriggerDetector()
    now = time.time()
    for _ in range(3):
        detector.observe(
            CreationTrigger(
                signal=TriggerSignal.request_decline,
                domain="law",
                observed_at=now,
            )
        )
    assert detector.threshold_crossed(
        TriggerSignal.request_decline, "law", now=now
    )


def test_explicit_user_mention_fires_on_first_observation():
    # Default min_count for explicit_user_mention is 1.
    detector = CreationTriggerDetector()
    detector.observe(
        CreationTrigger(
            signal=TriggerSignal.explicit_user_mention,
            domain="scotch",
            observed_at=time.time(),
            note='User said "wish I had someone for scotch"',
        )
    )
    assert detector.threshold_crossed(
        TriggerSignal.explicit_user_mention, "scotch"
    )


# ---- evaluate: yes / no / defer verdicts ---------------------------


@pytest.mark.asyncio
async def test_evaluate_returns_none_below_threshold():
    async def never_called(*args):
        raise AssertionError("judgment should not run below threshold")

    detector = CreationTriggerDetector(judgment_fn=never_called)
    detector.observe(
        CreationTrigger(
            signal=TriggerSignal.request_decline,
            domain="law",
            observed_at=time.time(),
        )
    )
    result = await detector.evaluate(TriggerSignal.request_decline, "law")
    assert result is None


@pytest.mark.asyncio
async def test_evaluate_returns_none_without_judgment_fn():
    detector = CreationTriggerDetector(judgment_fn=None)
    now = time.time()
    for _ in range(3):
        detector.observe(
            CreationTrigger(
                signal=TriggerSignal.request_decline,
                domain="law",
                observed_at=now,
            )
        )
    result = await detector.evaluate(
        TriggerSignal.request_decline, "law", now=now
    )
    assert result is None


@pytest.mark.asyncio
async def test_evaluate_calls_judgment_when_threshold_crossed():
    async def judge(signal, domain, recent):
        return JudgmentResult(
            verdict=JudgmentVerdict.yes,
            rationale=f"authoring needed for {domain}",
        )

    detector = CreationTriggerDetector(judgment_fn=judge)
    now = time.time()
    for _ in range(3):
        detector.observe(
            CreationTrigger(
                signal=TriggerSignal.request_decline,
                domain="law",
                observed_at=now,
            )
        )
    result = await detector.evaluate(
        TriggerSignal.request_decline, "law", now=now
    )
    assert result is not None
    assert result.verdict == JudgmentVerdict.yes


@pytest.mark.asyncio
async def test_no_verdict_recorded_as_rejection():
    async def judge(s, d, r):
        return JudgmentResult(verdict=JudgmentVerdict.no, rationale="not useful")

    detector = CreationTriggerDetector(judgment_fn=judge)
    now = time.time()
    for _ in range(3):
        detector.observe(
            CreationTrigger(
                signal=TriggerSignal.request_decline,
                domain="law",
                observed_at=now,
            )
        )
    await detector.evaluate(TriggerSignal.request_decline, "law", now=now)
    rejections = detector.rejections()
    assert len(rejections) == 1
    assert rejections[0]["rationale"] == "not useful"


@pytest.mark.asyncio
async def test_defer_verdict_suppresses_re_evaluation_within_window():
    calls = {"n": 0}

    async def judge(s, d, r):
        calls["n"] += 1
        return JudgmentResult(
            verdict=JudgmentVerdict.defer,
            rationale="check back later",
            defer_seconds=100.0,
        )

    detector = CreationTriggerDetector(judgment_fn=judge)
    now = time.time()
    for _ in range(3):
        detector.observe(
            CreationTrigger(
                signal=TriggerSignal.request_decline,
                domain="law",
                observed_at=now,
            )
        )
    first = await detector.evaluate(TriggerSignal.request_decline, "law", now=now)
    assert first.verdict == JudgmentVerdict.defer
    # Within the defer window — evaluate must NOT call the judgment again.
    second = await detector.evaluate(
        TriggerSignal.request_decline, "law", now=now + 50
    )
    assert second is None
    assert calls["n"] == 1

    # After the defer window, evaluate calls the judgment again.
    third = await detector.evaluate(
        TriggerSignal.request_decline, "law", now=now + 200
    )
    assert third is not None
    assert calls["n"] == 2
