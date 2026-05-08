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

"""Notification flow tests (v1.1 R13 + v1.2 R15 one-on-one channel)."""

from __future__ import annotations

import threading
import time


from loam.self_upgrade.notification import (
    ConfirmationDecision,
    InMemoryChannel,
    notify_accepted,
    notify_and_apply_with_cancel_window,
    notify_rolled_back,
    notify_rollback_failed,
    notify_upgrade_available,
    wait_for_confirmation,
)


def test_notify_upgrade_available_no_breaking() -> None:
    ch = InMemoryChannel()
    notify_upgrade_available(ch, "pos-v2-v0.2.0")
    assert len(ch.sent) == 1
    assert "pos-v2-v0.2.0" in ch.sent[0]
    assert "yes" in ch.sent[0]
    assert "no" in ch.sent[0]
    assert "Breaking changes" not in ch.sent[0]


def test_notify_upgrade_available_with_breaking() -> None:
    ch = InMemoryChannel()
    notify_upgrade_available(ch, "pos-v2-v0.2.0", breaking=["mem-v4"])
    assert "Breaking changes declared: mem-v4" in ch.sent[0]


def test_wait_for_confirmation_yes() -> None:
    ch = InMemoryChannel()

    def reply() -> None:
        time.sleep(0.05)
        ch.push_user_reply("yes")

    t = threading.Thread(target=reply)
    t.start()
    result = wait_for_confirmation(ch, timeout_s=2.0)
    t.join()
    assert result.decision is ConfirmationDecision.YES


def test_wait_for_confirmation_no() -> None:
    ch = InMemoryChannel()
    ch.push_user_reply("no")
    result = wait_for_confirmation(ch, timeout_s=1.0)
    assert result.decision is ConfirmationDecision.NO


def test_wait_for_confirmation_timeout() -> None:
    ch = InMemoryChannel()
    result = wait_for_confirmation(ch, timeout_s=0.3)
    assert result.decision is ConfirmationDecision.TIMEOUT


def test_wait_for_confirmation_ignores_unrecognised() -> None:
    ch = InMemoryChannel()

    def reply() -> None:
        time.sleep(0.05)
        ch.push_user_reply("maybe")
        time.sleep(0.1)
        ch.push_user_reply("yes")

    t = threading.Thread(target=reply)
    t.start()
    result = wait_for_confirmation(ch, timeout_s=3.0)
    t.join()
    assert result.decision is ConfirmationDecision.YES


def test_notify_and_apply_default_proceeds() -> None:
    ch = InMemoryChannel()
    result = notify_and_apply_with_cancel_window(ch, "pos-v2-v0.2.0", cancel_window_s=0.3)
    assert result.decision is ConfirmationDecision.YES
    assert any("cancel" in m for m in ch.sent)


def test_notify_and_apply_cancel_aborts() -> None:
    ch = InMemoryChannel()

    def reply() -> None:
        time.sleep(0.05)
        ch.push_user_reply("cancel")

    t = threading.Thread(target=reply)
    t.start()
    result = notify_and_apply_with_cancel_window(ch, "pos-v2-v0.2.0", cancel_window_s=2.0)
    t.join()
    assert result.decision is ConfirmationDecision.CANCEL


def test_notify_accepted_includes_summary() -> None:
    ch = InMemoryChannel()
    notify_accepted(
        ch,
        "pos-v2-v0.2.0",
        duration_s=38.4,
        clause_verdicts={
            "a": {"passed": True},
            "b": {"passed": True},
            "c": {"passed": True},
        },
    )
    assert len(ch.sent) == 1
    assert "accepted" in ch.sent[0]
    assert "38.4" in ch.sent[0]


def test_notify_rolled_back_includes_failing_clauses() -> None:
    ch = InMemoryChannel()
    notify_rolled_back(
        ch, "pos-v2-v0.2.0", failing=["c", "d"], report_path="/tmp/report.json"
    )
    assert "c" in ch.sent[0]
    assert "d" in ch.sent[0]
    assert "report.json" in ch.sent[0]


def test_notify_rollback_failed_tier1_tone() -> None:
    ch = InMemoryChannel()
    notify_rollback_failed(ch, "pos-v2-v0.2.0", "/tmp/fail.json")
    assert "UPGRADE FAILED" in ch.sent[0]
    assert "Manual recovery" in ch.sent[0]
