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

"""Extra explicit-confirmation gate for Telegram-originated Tier-A/B actions.

Ruling 2026-04-22 (Q4): in-session identical requests retain existing
safety-gate discipline; Telegram adds a second gate — a reply from
Eve names the action, asks yes/no, the user must answer from Telegram
before execution. Default timeout is 30 minutes (Eve's inference #2 —
challenged below, confirmed held for v1).

Inference-challenge note (Eve's #2): 30 minutes. A shorter window (5
min) forces the owner to be at the phone actively, which defeats the
"reach me when I'm not at my desk" purpose. A longer window (60+ min)
lets a stale request linger past the point where the owner would have
forgotten what they asked for. 30 minutes sits in the middle of the
"user-glance-at-phone" cadence. Holding as-is.

Non-owner identities cannot request Tier-A/B actions at all — the
``classify`` function returns ``NONOWNER_REFUSED`` in that case and
no confirmation is issued; the owner is notified of the refused
request via their own primary channel.
"""

from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Awaitable, Callable

from . import observability as obs


DEFAULT_CONFIRMATION_TIMEOUT_S = 30 * 60  # 30 minutes


class ConfirmationOutcome(str, Enum):
    approved = "approved"
    refused = "refused"
    timeout = "timeout"
    nonowner_refused = "nonowner_refused"


@dataclass
class ConfirmationRequest:
    request_id: str
    action_name: str
    action_summary: str
    identity_user_id: str
    identity_display_name: str
    authority_class: str
    issued_at: float
    timeout_s: float = DEFAULT_CONFIRMATION_TIMEOUT_S
    future: asyncio.Future[ConfirmationOutcome] = field(
        default_factory=lambda: asyncio.get_event_loop().create_future()
    )


@dataclass
class ConfirmationGate:
    """State machine for the extra-confirmation gate.

    Usage (adapter calls):
        outcome = await gate.request(
            action_name="publish_blog_post",
            action_summary="post draft to medium.com public feed",
            identity=some_identity,
            send=lambda text: mcp.reply(chat_id=..., text=text),
        )

    Inbound handler calls ``gate.resolve(request_id, 'yes')`` (or
    'no'). Unparsed inbound text ``gate.resolve_by_text(identity, text)``
    attempts a best-effort regex over the most recent pending request
    for that identity.
    """

    timeout_s: float = DEFAULT_CONFIRMATION_TIMEOUT_S
    clock: Callable[[], float] = time.monotonic
    _pending: dict[str, ConfirmationRequest] = field(default_factory=dict)

    def is_tier_ab(self, action_name: str) -> bool:
        """Caller supplies the Tier-A/B classification. This module
        does not reimplement the safety layer's tier logic; it accepts
        a boolean or string from the caller. Present for test
        ergonomics.
        """
        return True

    async def request(
        self,
        *,
        action_name: str,
        action_summary: str,
        identity_user_id: str,
        identity_display_name: str,
        authority_class: str,
        send: Callable[[str], Awaitable[None]],
        timeout_s: float | None = None,
    ) -> ConfirmationOutcome:
        # Non-owner identity: refuse immediately, no prompt to user.
        from .allowlist import AuthorityClass

        if authority_class != AuthorityClass.OWNER:
            obs.confirmation_flow(
                action=action_name,
                identity=identity_user_id,
                outcome="nonowner_refused",
            )
            return ConfirmationOutcome.nonowner_refused

        request_id = uuid.uuid4().hex[:8]
        effective_timeout = timeout_s if timeout_s is not None else self.timeout_s
        req = ConfirmationRequest(
            request_id=request_id,
            action_name=action_name,
            action_summary=action_summary,
            identity_user_id=identity_user_id,
            identity_display_name=identity_display_name,
            authority_class=authority_class,
            issued_at=self.clock(),
            timeout_s=effective_timeout,
        )
        self._pending[request_id] = req

        prompt = (
            f"Telegram-originated request — extra confirmation required.\n"
            f"Action: {action_name}\n"
            f"Detail: {action_summary}\n"
            f"Reply `yes {request_id}` to approve or `no {request_id}` to refuse.\n"
            f"Times out in {int(effective_timeout // 60)} minutes."
        )
        await send(prompt)

        started = self.clock()
        try:
            outcome = await asyncio.wait_for(req.future, timeout=effective_timeout)
        except asyncio.TimeoutError:
            outcome = ConfirmationOutcome.timeout
        finally:
            self._pending.pop(request_id, None)

        obs.confirmation_flow(
            action=action_name,
            identity=identity_user_id,
            outcome=outcome.value,
            elapsed_s=self.clock() - started,
        )
        return outcome

    def resolve(self, request_id: str, answer: str) -> bool:
        req = self._pending.get(request_id)
        if req is None:
            return False
        decision = answer.strip().lower()
        if decision in {"yes", "y", "approve", "ok", "confirm"}:
            req.future.set_result(ConfirmationOutcome.approved)
            return True
        if decision in {"no", "n", "refuse", "deny", "cancel"}:
            req.future.set_result(ConfirmationOutcome.refused)
            return True
        return False

    def resolve_by_text(self, identity_user_id: str, text: str) -> bool:
        """Best-effort text-match resolver. Accepts:
          yes <request_id> / no <request_id>
          yes / no (routed to most recent pending request for this identity)
        """
        import re

        norm = text.strip().lower()
        # Explicit form first.
        m = re.match(r"^(yes|y|no|n)\s+([a-f0-9]{8})\b", norm)
        if m:
            return self.resolve(m.group(2), m.group(1))
        # Bare yes/no — pick the most-recently-issued request for this identity.
        m2 = re.match(r"^(yes|y|no|n)\b", norm)
        if m2:
            candidates = [
                r
                for r in self._pending.values()
                if r.identity_user_id == identity_user_id
            ]
            if not candidates:
                return False
            latest = max(candidates, key=lambda r: r.issued_at)
            return self.resolve(latest.request_id, m2.group(1))
        return False

    def pending_count(self) -> int:
        return len(self._pending)
