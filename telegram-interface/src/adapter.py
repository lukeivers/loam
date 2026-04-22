"""`TelegramAdapter` — the component's public API.

Constructs a ``primary_persona.introduction.OneOnOneChannel`` with
``kind=ChannelKind.personal_telegram`` and an injected ``send``
callable routing through:

- MCP ``reply`` tool when the caller is in-session and the probe is
  green;
- Direct Bot API when the caller is out-of-session (``mcp_client`` is
  None) and the probe is green;
- Fallback (in-session stdout + ``~/.pos/attention.md``) with framing
  when the probe is red.

Inbound ``<channel source="telegram" …>`` events are handled by
``on_inbound`` — the adapter looks up the sender in the allowlist,
classifies the authority, and hands a shaped ``ChannelEvent`` to the
caller-supplied ``on_user_message`` handler.

Zero sealed-component amendments. ``OneOnOneChannel``'s ``send:
Callable`` injection is the entire surface this adapter consumes; the
sealed code itself is not touched.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

# Sealed import — no amendment, pure consumption.
from primary_persona.introduction import ChannelKind, OneOnOneChannel

from . import (
    IPC_TELEGRAM_ALLOWLIST_REJECTED,
    IPC_TELEGRAM_SEND_FAILED,
    IPC_TELEGRAM_UNAVAILABLE,
)
from . import observability as obs
from .allowlist import AccessFile, AuthorityClass, Identity
from .availability import AvailabilityProbe, FailureClass
from .bot_api import BotApiClient, BotApiError
from .confirmation import ConfirmationGate, ConfirmationOutcome
from .fallback import write_fallback
from .mcp_client import McpReplyClient


@dataclass
class ChannelEvent:
    """Normalised inbound event shape. The adapter emits these to the
    handler; persona input plumbing consumes them."""

    chat_id: str
    message_id: str | None
    user_id: str
    user_handle: str | None
    identity: Identity | None  # None = unauthorised
    authority_class: str | None  # None = unauthorised
    content: str
    attachment_file_id: str | None = None
    image_path: str | None = None
    received_at: str | None = None
    is_tier_ab_request: bool = False


OnUserMessageFn = Callable[[ChannelEvent], Awaitable[None]]
OwnerNotifyFn = Callable[[str], Awaitable[None]]
InSessionSendFn = Callable[[str], Awaitable[None]]


@dataclass
class TelegramAdapter:
    """See module docstring."""

    availability: AvailabilityProbe
    access: AccessFile
    bot_api: BotApiClient | None = None
    mcp_client: McpReplyClient | None = None
    confirmation: ConfirmationGate = field(default_factory=ConfirmationGate)
    in_session_send: InSessionSendFn | None = None
    on_user_message: OnUserMessageFn | None = None
    owner_notify: OwnerNotifyFn | None = None
    name: str = "telegram"
    # Active outbound chat_id (v1: owner DM). Resolved lazily from
    # allowlist. Callers may override (per-identity replies).
    _default_chat_id: str | None = None

    # ---- OneOnOneChannel construction ---------------------------------

    def build_channel(self) -> OneOnOneChannel:
        return OneOnOneChannel(
            kind=ChannelKind.personal_telegram,
            name=self.name,
            send=self._default_send,
            is_group=False,
            is_active=self.availability.current,
        )

    def default_chat_id(self) -> str | None:
        if self._default_chat_id is not None:
            return self._default_chat_id
        owner = self.access.owner()
        if owner is None:
            return None
        self._default_chat_id = owner.user_id
        return self._default_chat_id

    # ---- outbound -----------------------------------------------------

    async def _default_send(self, text: str) -> None:
        chat_id = self.default_chat_id()
        if chat_id is None:
            # No owner yet = no valid target. Route to fallback.
            await self._fallback(text=text, reason="no_allowlist_entry")
            return
        await self.send(text=text, chat_id=chat_id)

    async def send(
        self,
        *,
        text: str,
        chat_id: str,
        reply_to: str | None = None,
        identity: str | None = None,
    ) -> None:
        """Send `text` to `chat_id` via the most-preferred available
        transport. Loud-escalation on failure through the fallback
        layer — no silent drops."""
        if not self.availability.cached_available():
            await self._fallback(
                text=text,
                reason=(
                    self.availability.last_failure_class.value
                    if self.availability.last_failure_class
                    else "unavailable"
                ),
                identity=identity,
            )
            return

        # In-session (MCP) preferred when available; direct Bot API
        # otherwise. "Available" is decided by caller-injected clients:
        # the orchestrator passes only `bot_api`; an in-session dispatch
        # passes an `mcp_client` for the reply tool.
        try:
            if self.mcp_client is not None:
                await self.mcp_client.reply(
                    chat_id=chat_id, text=text, reply_to=reply_to
                )
                obs.outbound_sent(
                    path="mcp_reply",
                    chat_id=chat_id,
                    identity=identity,
                    bytes_sent=len(text.encode("utf-8")),
                )
                return
            if self.bot_api is not None:
                await self.bot_api.send_message(
                    chat_id=chat_id, text=text, reply_to=reply_to
                )
                return
            # No transport available — fallback.
            await self._fallback(text=text, reason="no_transport", identity=identity)
        except BotApiError as e:
            await self.availability.mark_failure(
                e.failure_class, detail=e.message
            )
            # Special-case 403: mark the identity blocked so subsequent
            # sends to them are suppressed until the owner clears.
            if e.failure_class == FailureClass.blocked_by_user:
                self.access.mark_blocked(chat_id)
                self.access.save()
            await self._fallback(
                text=text, reason=e.failure_class.value, identity=identity
            )
        except Exception as e:  # noqa: BLE001 — fallback must be robust
            await self.availability.mark_failure(
                FailureClass.api_unreachable, detail=str(e)
            )
            await self._fallback(
                text=text, reason="send_exception", identity=identity
            )

    async def _fallback(
        self, *, text: str, reason: str, identity: str | None = None
    ) -> None:
        await write_fallback(
            text=text,
            reason=reason,
            in_session_send=self.in_session_send,
            identity=identity,
        )

    # ---- inbound ------------------------------------------------------

    async def on_inbound(self, *, meta: dict[str, Any], content: str) -> None:
        """Handle a ``notifications/claude/channel`` event. Looks up
        the sender in the allowlist; drops (with observability) when
        the identity is not authorised. Otherwise forwards a
        ``ChannelEvent`` to the caller-supplied handler.
        """
        user_id = str(meta.get("user_id") or "")
        user_handle = meta.get("user")
        chat_id = str(meta.get("chat_id") or user_id)
        message_id = (
            str(meta.get("message_id")) if meta.get("message_id") else None
        )

        identity = self.access.lookup(user_id)

        # Confirmation-answer routing — before the allowlist check
        # yields the event to the persona, attempt to resolve any
        # pending confirmation for this identity.
        if identity is not None:
            if self.confirmation.pending_count() and self._maybe_resolve_confirmation(
                identity.user_id, content
            ):
                return

        if identity is None:
            # The plugin's own allowlist should have dropped this
            # before it reached us. If we see it, something is wrong
            # — log loudly and drop.
            obs.inbound_rejected(user_id=user_id, reason="not_in_pos_identities")
            return

        if identity.blocked_at:
            obs.inbound_rejected(user_id=user_id, reason="identity_blocked")
            return

        obs.inbound_received(
            chat_id=chat_id,
            user_id=user_id,
            identity=identity.display_name,
            authority_class=identity.authority_class,
            content_chars=len(content),
        )

        event = ChannelEvent(
            chat_id=chat_id,
            message_id=message_id,
            user_id=user_id,
            user_handle=user_handle,
            identity=identity,
            authority_class=identity.authority_class,
            content=content,
            attachment_file_id=meta.get("attachment_file_id"),
            image_path=meta.get("image_path"),
            received_at=meta.get("ts"),
        )
        if self.on_user_message is not None:
            await self.on_user_message(event)

    def _maybe_resolve_confirmation(self, identity_user_id: str, content: str) -> bool:
        """Attempt to resolve a pending confirmation from this
        identity's text. Returns True iff a pending confirmation was
        resolved by this message."""
        return self.confirmation.resolve_by_text(identity_user_id, content)

    # ---- Tier-A/B confirmation gate ----------------------------------

    async def request_tier_ab_confirmation(
        self,
        *,
        action_name: str,
        action_summary: str,
        identity: Identity,
    ) -> ConfirmationOutcome:
        """Ask the Telegram identity to confirm a Tier-A/B action.
        Non-owner identities auto-refuse; the owner is notified.
        """
        outcome = await self.confirmation.request(
            action_name=action_name,
            action_summary=action_summary,
            identity_user_id=identity.user_id,
            identity_display_name=identity.display_name,
            authority_class=identity.authority_class,
            send=lambda text: self.send(
                text=text, chat_id=identity.user_id, identity=identity.display_name
            ),
        )
        if outcome == ConfirmationOutcome.nonowner_refused:
            # Notify the owner that a non-owner tried a Tier-A/B action.
            await self._notify_owner_of_nonowner_refusal(
                identity=identity,
                action_name=action_name,
                action_summary=action_summary,
            )
        elif outcome == ConfirmationOutcome.timeout:
            await self._notify_owner_of_timeout(
                identity=identity, action_name=action_name
            )
        return outcome

    async def _notify_owner_of_nonowner_refusal(
        self, *, identity: Identity, action_name: str, action_summary: str
    ) -> None:
        owner = self.access.owner()
        if owner is None or self.owner_notify is None:
            return
        msg = (
            f"{identity.display_name} ({identity.relationship}) requested a "
            f"Tier-A/B action from Telegram — refused per reduced-bound authority.\n"
            f"Action: {action_name}\nDetail: {action_summary}"
        )
        await self.owner_notify(msg)

    async def _notify_owner_of_timeout(
        self, *, identity: Identity, action_name: str
    ) -> None:
        if self.owner_notify is None:
            return
        await self.owner_notify(
            f"Confirmation timed out for {action_name!r} from "
            f"{identity.display_name}. Request refused."
        )
