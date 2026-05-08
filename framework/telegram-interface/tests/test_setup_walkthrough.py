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

"""Setup walkthrough — TG1–TG6.

TG1: session-two offer fires with six numbered steps including time
     estimates.
TG2: decline writes declined-marker; never re-offered proactively.
TG3: success writes `status: done` marker; `should_offer` short-
     circuits.
TG4: `should_offer` detects plugin-available and emits; absent-plugin
     walkthrough starts at step 1.
TG5: prior settings preserved — access.json extra keys (pending,
     groups, dmPolicy) round-trip untouched.
TG6: step-level failure writes `status: failed` with `failed_at_step`;
     next session resumes from that step.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from loam.telegram_interface.allowlist import AccessFile, AuthorityClass
from loam.telegram_interface.setup_walkthrough import (
    STEP1,
    STEP2,
    STEP3,
    STEP4,
    STEPS,
    SetupMarker,
    SetupStatus,
    SetupWalkthrough,
    should_offer,
)


@pytest.mark.asyncio
async def test_tg1_offer_includes_six_steps_and_time_estimates(tmp_access: AccessFile, tmp_path: Path) -> None:
    """TG1 — opening offer covers the six-step framing; each user-
    visible step string includes an expected-time estimate."""
    emitted: list[str] = []

    async def emit(text: str) -> None:
        emitted.append(text)

    marker = SetupMarker(path=tmp_path / "telegram-setup-offered")
    w = SetupWalkthrough(marker=marker, access=tmp_access, emit=emit)
    await w.offer()

    assert len(emitted) == 1
    assert "six steps" in emitted[0]
    assert "5 minutes" in emitted[0]
    # The numbered user-visible step strings include a time estimate.
    for step_text in (STEP1, STEP2, STEP3, STEP4):
        assert "~" in step_text  # "~30 seconds" / "~2 minutes" / ...
    assert len(STEPS) == 6


@pytest.mark.asyncio
async def test_tg2_decline_writes_marker_and_does_not_reoffer(tmp_access: AccessFile, tmp_path: Path) -> None:
    """TG2 — decline writes the declined marker; should_offer
    returns False; the persona does not proactively raise setup
    again."""
    emitted: list[str] = []

    async def emit(text: str) -> None:
        emitted.append(text)

    marker = SetupMarker(path=tmp_path / "telegram-setup-offered")
    w = SetupWalkthrough(marker=marker, access=tmp_access, emit=emit)
    await w.decline()

    rec = marker.read()
    assert rec["status"] == SetupStatus.declined.value

    # Should-offer short-circuits.
    assert should_offer(marker=marker, access=tmp_access) is False


@pytest.mark.asyncio
async def test_tg3_success_writes_done_marker_and_self_retires(tmp_access: AccessFile, tmp_path: Path) -> None:
    """TG3 — on confirmed round-trip the walkthrough writes `status:
    done` and `should_offer` returns False."""
    emitted: list[str] = []
    written_tokens: list[str] = []
    pair_called_with: list[str] = []
    policy_set: list[bool] = []
    rtrip_called: list[bool] = []

    async def emit(text: str) -> None:
        emitted.append(text)

    async def write_token(token: str) -> None:
        written_tokens.append(token)

    async def pair_sender(code: str) -> str:
        pair_called_with.append(code)
        return "111111"

    async def set_policy() -> None:
        policy_set.append(True)

    async def rtrip() -> bool:
        rtrip_called.append(True)
        return True

    marker = SetupMarker(path=tmp_path / "telegram-setup-offered")
    w = SetupWalkthrough(
        marker=marker,
        access=tmp_access,
        emit=emit,
        write_token=write_token,
        pair_sender=pair_sender,
        set_allowlist_policy=set_policy,
        round_trip_verify=rtrip,
    )

    # Drive a happy-path through: offer → step1 → confirm-step1 →
    # step2-confirm(token) → step3-emit → step4-emit → step4-confirm(code).
    await w.offer()

    # Pretend the plugin was installed between step1 and confirm.
    import loam.telegram_interface.setup_walkthrough as sw
    orig = sw.plugin_installed
    sw.plugin_installed = lambda cache_dir=None: True
    try:
        await w.step1_emit()
        await w.step1_confirm()
        await w.step2_confirm("123456789:AAHdqTcv9876543210abcdef")
        await w.step4_emit()
        await w.step4_confirm("abc123")
    finally:
        sw.plugin_installed = orig

    assert written_tokens == ["123456789:AAHdqTcv9876543210abcdef"]
    assert pair_called_with == ["abc123"]
    assert policy_set == [True]
    assert rtrip_called == [True]

    rec = marker.read()
    assert rec["status"] == SetupStatus.done.value
    # self-retire: should_offer short-circuits on done.
    assert should_offer(marker=marker, access=tmp_access) is False


@pytest.mark.asyncio
async def test_tg4_already_configured_detection(tmp_access_with_owner: AccessFile, tmp_path: Path) -> None:
    """TG4 — when the plugin is already paired (allowFrom non-empty)
    the walkthrough never offers; marker is written with status:
    already_configured."""
    marker = SetupMarker(path=tmp_path / "telegram-setup-offered")
    assert should_offer(marker=marker, access=tmp_access_with_owner) is False

    rec = marker.read()
    assert rec["status"] == SetupStatus.already_configured.value


@pytest.mark.asyncio
async def test_tg5_prior_settings_preserved_through_setup(tmp_path: Path) -> None:
    """TG5 — writes through AccessFile preserve plugin-owned keys
    (dmPolicy, groups, pending) untouched. pos_identities is the
    only key we mutate."""
    path = tmp_path / "access.json"
    data = {
        "dmPolicy": "pairing",
        "allowFrom": [],
        "groups": {"-1001234": {"allowFrom": ["999"]}},
        "pending": {"abcdef": {"senderId": "777", "at": "2026-01-01T00:00Z"}},
    }
    path.write_text(json.dumps(data))

    a = AccessFile.load(path)
    a.add_identity(
        user_id="111111",
        display_name="Luke",
        relationship="owner",
        authority_class=AuthorityClass.OWNER,
    )
    a.save()

    reloaded = json.loads(path.read_text())
    assert reloaded["dmPolicy"] == "pairing"
    assert reloaded["groups"] == {"-1001234": {"allowFrom": ["999"]}}
    assert reloaded["pending"] == {"abcdef": {"senderId": "777", "at": "2026-01-01T00:00Z"}}
    assert "111111" in reloaded["pos_identities"]
    assert reloaded["allowFrom"] == ["111111"]


@pytest.mark.asyncio
async def test_tg6_step_failure_writes_marker_and_names_failed_step(tmp_access: AccessFile, tmp_path: Path) -> None:
    """TG6 — per-step failure surfaces a diagnostic and writes
    `status: failed` with the step number. Next session resumes from
    the failed step (the marker carries `failed_at_step`)."""
    emitted: list[str] = []

    async def emit(text: str) -> None:
        emitted.append(text)

    marker = SetupMarker(path=tmp_path / "telegram-setup-offered")
    w = SetupWalkthrough(marker=marker, access=tmp_access, emit=emit)

    # Try a token that doesn't match BotFather shape.
    await w.step2_confirm("not-a-token")

    rec = marker.read()
    assert rec["status"] == SetupStatus.failed.value
    assert rec["failed_at_step"] == 2
    # User-facing diagnostic — not a stack trace.
    assert any("BotFather" in msg for msg in emitted)
