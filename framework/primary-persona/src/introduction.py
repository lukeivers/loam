"""Introduction protocol (D7).

On successful authoring, the user is introduced to the new persona
BEFORE any message from that persona is delivered. The introduction
is dispatched ONLY to the user's current one-on-one channel
(terminal, Claude desktop, or personal Telegram thread) — never to
group channels (Luke's decision, brief §"Luke's decisions").

The new persona sits with `pending_introduction: true` and
`is_addressable: false` until the user's next non-retire message.
Retire instructions move the directory to `_retired/` and the flag
never flips True.

If zero one-on-one channels are reachable when authoring completes,
the introduction is queued and fires when one becomes active
(Eve's flagged inference in the brief — queue-and-fire).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Awaitable, Callable, Iterable, Protocol, Sequence

from . import observability as obs
from .contract import PersonaContract
from .creation_triggers import TriggerSignal
from .loader import LoadedPersona


# ---- channel protocol ----------------------------------------------


class ChannelKind(str, Enum):
    terminal = "terminal"
    claude_desktop = "claude_desktop"
    personal_telegram = "personal_telegram"


@dataclass(frozen=True)
class OneOnOneChannel:
    """A one-on-one user channel.

    The `send` callable takes the rendered introduction text and
    delivers it. Workspaces wire whatever transport they use; tests
    wire a fake that captures the payload.

    `is_group` is always False by construction — group channels are
    forbidden for introductions per Luke's decision. The field
    exists to make the invariant explicit in the type (a reviewer
    scanning the code sees it cannot be True here).
    """

    kind: ChannelKind
    name: str
    send: Callable[[str], Awaitable[None]]
    is_group: bool = False
    is_active: bool = True

    def __post_init__(self) -> None:
        if self.is_group:
            raise ValueError(
                "one-on-one channels cannot be group channels "
                "(Luke's decision, brief §intro protocol). "
                "Use a separate dispatcher for group announcements."
            )


# ---- outcome --------------------------------------------------------


class IntroductionOutcome(str, Enum):
    delivered = "delivered"
    queued_no_channel = "queued_no_channel"
    failed = "failed"


@dataclass(frozen=True)
class IntroductionRecord:
    handle: str
    given_name: str
    trigger_signal: str
    channel_used: str | None
    outcome: IntroductionOutcome
    delivered_at: str | None
    queued_at: str | None = None
    error: str | None = None


# ---- dispatcher -----------------------------------------------------


@dataclass
class IntroductionDispatcher:
    """Sends introductions and manages the addressable-flag transition.

    Usage:
        dispatcher = IntroductionDispatcher(
            channels=[terminal_channel, telegram_channel],
            workspace_root=Path("/workspaces/personal"),
        )
        record = await dispatcher.introduce(
            new_persona=authored_loaded_persona,
            trigger_signal=TriggerSignal.request_decline,
            retire_instruction="reply 'retire new_handle' to remove.",
        )

    `make_addressable` is called on the user's next non-retire message
    (hook wiring happens in session layer).
    `retire` on a pending persona moves it to `_retired/`.
    """

    channels: Sequence[OneOnOneChannel]
    workspace_root: Path
    queue_dir: Path | None = None
    # Captured introductions waiting for a channel to become active.
    _pending_queue: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        # Hard guard — if any channel claims to be a group, reject.
        for ch in self.channels:
            if ch.is_group:
                raise ValueError(
                    f"channel {ch.name!r} declares is_group=True; "
                    "introductions are one-on-one only."
                )
        if self.queue_dir is None:
            from workspace_bootstrap.workspace_paths import pos_subdir

            self.queue_dir = pos_subdir(self.workspace_root) / "intro_queue"
        self.queue_dir.mkdir(parents=True, exist_ok=True)

    async def introduce(
        self,
        *,
        new_persona: LoadedPersona,
        trigger_signal: TriggerSignal,
        retire_instruction: str | None = None,
    ) -> IntroductionRecord:
        """Dispatch the introduction to the first active one-on-one
        channel. Returns a record regardless of outcome."""
        text = self._render_introduction(
            new_persona=new_persona,
            trigger_signal=trigger_signal,
            retire_instruction=retire_instruction,
        )
        active_channels = [c for c in self.channels if c.is_active]

        if not active_channels:
            payload = {
                "handle": new_persona.handle,
                "given_name": new_persona.given_name,
                "trigger_signal": trigger_signal.value,
                "retire_instruction": retire_instruction,
                "text": text,
                "queued_at": datetime.now(timezone.utc).isoformat(),
            }
            self._pending_queue.append(payload)
            self._persist_queue_entry(payload)
            obs.introduction_event(
                new_handle=new_persona.handle,
                channel="<none>",
                outcome="queued_no_channel",
                reason="no active one-on-one channel",
            )
            return IntroductionRecord(
                handle=new_persona.handle,
                given_name=new_persona.given_name,
                trigger_signal=trigger_signal.value,
                channel_used=None,
                outcome=IntroductionOutcome.queued_no_channel,
                delivered_at=None,
                queued_at=payload["queued_at"],
            )

        # First active channel wins; by construction none is group.
        channel = active_channels[0]
        try:
            await channel.send(text)
        except Exception as e:  # noqa: BLE001 — surface the failure
            obs.introduction_event(
                new_handle=new_persona.handle,
                channel=channel.name,
                outcome="failed",
                reason=str(e),
            )
            return IntroductionRecord(
                handle=new_persona.handle,
                given_name=new_persona.given_name,
                trigger_signal=trigger_signal.value,
                channel_used=channel.name,
                outcome=IntroductionOutcome.failed,
                delivered_at=None,
                error=str(e),
            )

        obs.introduction_event(
            new_handle=new_persona.handle,
            channel=channel.name,
            outcome="delivered",
        )
        return IntroductionRecord(
            handle=new_persona.handle,
            given_name=new_persona.given_name,
            trigger_signal=trigger_signal.value,
            channel_used=channel.name,
            outcome=IntroductionOutcome.delivered,
            delivered_at=datetime.now(timezone.utc).isoformat(),
        )

    async def flush_queue(self) -> list[IntroductionRecord]:
        """Called when a channel becomes active. Tries to deliver any
        queued introductions; removes successful ones from the queue.
        """
        active_channels = [c for c in self.channels if c.is_active]
        if not active_channels:
            return []
        delivered: list[IntroductionRecord] = []
        remaining: list[dict[str, Any]] = []
        for payload in self._pending_queue:
            channel = active_channels[0]
            try:
                await channel.send(payload["text"])
                delivered.append(
                    IntroductionRecord(
                        handle=payload["handle"],
                        given_name=payload["given_name"],
                        trigger_signal=payload["trigger_signal"],
                        channel_used=channel.name,
                        outcome=IntroductionOutcome.delivered,
                        delivered_at=datetime.now(timezone.utc).isoformat(),
                        queued_at=payload.get("queued_at"),
                    )
                )
                self._clear_queue_entry(payload["handle"])
            except Exception:
                remaining.append(payload)
        self._pending_queue = remaining
        return delivered

    def make_addressable(self, handle: str) -> None:
        """Flip the is_addressable flag on the persona file.

        Called by the session layer when the user's next message is
        NOT a retire instruction. The loaded persona is re-read from
        disk; the contract is serialised back with the flags updated.
        """
        from workspace_bootstrap.workspace_paths import (
            personas_dir as _personas_dir,
        )

        persona_dir = _personas_dir(self.workspace_root) / handle
        contract_path = persona_dir / "contract.yaml"
        if not contract_path.exists():
            return
        # Load, mutate, write back.
        from .contract import load_contract

        contract = load_contract(contract_path)
        updated = contract.model_copy(
            update={"pending_introduction": False, "is_addressable": True}
        )
        contract_path.write_text(updated.to_yaml())

    # ---- rendering ------------------------------------------------

    def _render_introduction(
        self,
        *,
        new_persona: LoadedPersona,
        trigger_signal: TriggerSignal,
        retire_instruction: str | None,
    ) -> str:
        contract = new_persona.contract
        handles = ", ".join(contract.home_persona_for) or "—"
        taxonomy = ", ".join(contract.escalation_taxonomy.categories) or "—"
        retire = retire_instruction or (
            f'reply "retire {contract.handle}" and I will move them out of the '
            "active roster."
        )
        return (
            f"[Introduction] I've drafted a new specialist — {contract.given_name} "
            f"({contract.handle}). They'll handle: {handles}.\n"
            f"Trigger: {trigger_signal.value}.\n"
            f"Escalation categories: {taxonomy}.\n\n"
            f"If that doesn't sound right, {retire}"
        )

    def _persist_queue_entry(self, payload: dict[str, Any]) -> None:
        assert self.queue_dir is not None
        path = Path(self.queue_dir) / f"{payload['handle']}.json"
        path.write_text(json.dumps(payload, indent=2))

    def _clear_queue_entry(self, handle: str) -> None:
        assert self.queue_dir is not None
        path = Path(self.queue_dir) / f"{handle}.json"
        try:
            path.unlink()
        except FileNotFoundError:
            pass

    # ---- guard -----------------------------------------------------

    @staticmethod
    def assert_not_sent_before_addressable(
        persona: LoadedPersona, sender_handle: str
    ) -> None:
        """Runtime guard — raise if a message attempts to leave the
        system claiming to be from this persona before it is
        addressable.

        The session layer calls this before relaying any message that
        identifies `sender_handle`; if the persona's contract has
        `is_addressable=False`, the guard raises and the message is
        dropped.
        """
        if persona.handle != sender_handle:
            return
        if not persona.contract.is_addressable:
            raise RuntimeError(
                f"persona {persona.handle!r} is not addressable "
                f"(pending_introduction={persona.contract.pending_introduction}); "
                "no messages identifying this persona may be delivered until the "
                "introduction has been acknowledged."
            )
