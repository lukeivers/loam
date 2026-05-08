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

"""User notification via the primary-persona one-on-one channel.

Per v1.1 R13 + v1.2 R15: all user-facing notifications go through the
primary persona's one-on-one channel (Luke's Telegram thread with Eve
in the canonical stack). The framework itself is persona-less (rule
7): it does not speak to the user directly. Instead it emits
notifications to a pluggable ``NotificationChannel`` which in
production is bound to the primary persona's IPC channel.

Two ``auto_update_mode`` values shape behaviour:

- ``require_confirmation`` — notify "Upgrade <tag> available — reply
  'yes' to proceed or 'no' to skip"; block until a yes/no response
  (24 h default timeout → deferred).
- ``notify_and_apply`` — notify "Upgrading to <tag> in 60 s — reply
  'cancel' to abort"; proceed after the window unless cancelled.

The ``NotificationChannel`` protocol is duck-typed for testability.
Production implementations wire it to the orchestrator's primary-
persona notification surface; tests supply an in-memory stub.
"""

from __future__ import annotations

import queue
import time
from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class NotificationChannel(Protocol):
    """Minimal send + receive interface the framework talks to.

    The production implementation is the primary-persona IPC channel;
    the framework deliberately avoids any knowledge of which transport
    it sits on. Whatever the channel is, it must be one-on-one with
    the user — never a group chat (v1.1 R13).
    """

    def send(self, message: str) -> None: ...

    def recv(self, timeout_s: float) -> str | None:
        """Block up to timeout_s for a user response; None on timeout."""


class ConfirmationDecision(str, Enum):
    YES = "yes"
    NO = "no"
    CANCEL = "cancel"
    TIMEOUT = "timeout"


@dataclass
class NotificationOutcome:
    decision: ConfirmationDecision
    raw_response: str | None = None
    elapsed_s: float = 0.0


def _normalise(raw: str | None) -> ConfirmationDecision | None:
    if raw is None:
        return None
    r = raw.strip().lower()
    if r in ("yes", "y", "proceed", "go"):
        return ConfirmationDecision.YES
    if r in ("no", "n", "skip", "defer"):
        return ConfirmationDecision.NO
    if r in ("cancel", "abort", "stop"):
        return ConfirmationDecision.CANCEL
    return None


def notify_upgrade_available(
    channel: NotificationChannel, tag: str, breaking: list[str] | None = None
) -> None:
    parts = [f"Upgrade {tag} available."]
    if breaking:
        parts.append(f"Breaking changes declared: {', '.join(breaking)}.")
    parts.append("Reply 'yes' to proceed or 'no' to skip.")
    channel.send(" ".join(parts))


def wait_for_confirmation(
    channel: NotificationChannel, timeout_s: float
) -> NotificationOutcome:
    """Block for a yes/no response.

    ``timeout_s`` is the window (default 24 h per brief / Eve's
    inference). Unrecognised responses are ignored — the caller is
    expected to provide a yes/no, and silence elapses into TIMEOUT.
    """
    start = time.monotonic()
    deadline = start + timeout_s
    last_raw: str | None = None
    while time.monotonic() < deadline:
        remaining = deadline - time.monotonic()
        raw = channel.recv(timeout_s=min(remaining, 60.0))
        last_raw = raw if raw is not None else last_raw
        decision = _normalise(raw)
        if decision in (ConfirmationDecision.YES, ConfirmationDecision.NO):
            return NotificationOutcome(
                decision=decision,
                raw_response=raw,
                elapsed_s=time.monotonic() - start,
            )
    return NotificationOutcome(
        decision=ConfirmationDecision.TIMEOUT,
        raw_response=last_raw,
        elapsed_s=time.monotonic() - start,
    )


def notify_and_apply_with_cancel_window(
    channel: NotificationChannel, tag: str, cancel_window_s: float
) -> NotificationOutcome:
    """Send the notify_and_apply prompt; wait cancel_window_s for a
    'cancel' response. Returns YES on timeout (apply proceeds), CANCEL
    if the user replied 'cancel'."""
    channel.send(
        f"Upgrading to {tag} in {int(cancel_window_s)} s — reply 'cancel' to abort."
    )
    start = time.monotonic()
    deadline = start + cancel_window_s
    last_raw: str | None = None
    while time.monotonic() < deadline:
        remaining = deadline - time.monotonic()
        raw = channel.recv(timeout_s=min(remaining, 5.0))
        last_raw = raw if raw is not None else last_raw
        decision = _normalise(raw)
        if decision is ConfirmationDecision.CANCEL:
            return NotificationOutcome(
                decision=ConfirmationDecision.CANCEL,
                raw_response=raw,
                elapsed_s=time.monotonic() - start,
            )
    return NotificationOutcome(
        decision=ConfirmationDecision.YES,
        raw_response=last_raw,
        elapsed_s=time.monotonic() - start,
    )


def notify_accepted(
    channel: NotificationChannel, tag: str, duration_s: float, clause_verdicts: dict
) -> None:
    passed = [c for c, r in clause_verdicts.items() if r.get("passed")]
    summary = f"clauses OK: {', '.join(sorted(passed))}"
    channel.send(
        f"Upgrade {tag} accepted in {duration_s:.1f}s — {summary}."
    )


def notify_rolled_back(
    channel: NotificationChannel, tag: str, failing: list[str], report_path: str
) -> None:
    channel.send(
        f"Upgrade {tag} rejected and rolled back. "
        f"Failing clauses: {', '.join(failing)}. "
        f"Report: {report_path}"
    )


def notify_rollback_failed(
    channel: NotificationChannel, tag: str, report_path: str
) -> None:
    """Tier 1 — manual recovery required."""
    channel.send(
        f"UPGRADE FAILED AND ROLLBACK FAILED. System in undefined state. "
        f"Details: {report_path}. Manual recovery required."
    )


# ---- test stub ----------------------------------------------------


class InMemoryChannel:
    """Simple FIFO channel for tests. Threaded send/recv mirrors the
    wire protocol without actually going over it."""

    def __init__(self) -> None:
        self.sent: list[str] = []
        self._inbox: queue.Queue[str] = queue.Queue()

    def send(self, message: str) -> None:
        self.sent.append(message)

    def recv(self, timeout_s: float) -> str | None:
        try:
            return self._inbox.get(timeout=timeout_s)
        except queue.Empty:
            return None

    def push_user_reply(self, reply: str) -> None:
        self._inbox.put(reply)
