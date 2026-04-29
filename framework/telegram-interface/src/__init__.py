"""Telegram interface — adapter-pattern consumer of the Claude MCP Telegram
plugin. Exposes a `TelegramAdapter` that constructs a
`primary_persona.introduction.OneOnOneChannel` with
`kind=ChannelKind.personal_telegram` and an injected `send` callable
routing through the plugin's `reply` tool (in-session) or the direct
Bot API (out-of-session), with loud-escalation fallback to
`~/.loam/attention.md` on outage.

No sealed-component amendments. `ChannelKind.personal_telegram`
already exists on the sealed enum; this package supplies the
`send` callable at the injection point the sealed dataclass documents.

Error-code range `-32100..-32109` reserved to this component.
"""

from __future__ import annotations

# Error codes — JSON-RPC/ApplicationError range reserved to this component.
# Scanned 2026-04-22 against the pos-v2 tree; no prior allocation in this
# range. Aligned with the orchestrator's -32000..-32099 application-error
# convention (orchestrator/src/ipc.py lines 14-17). The next decade
# extends the allocation cleanly without collision.
IPC_TELEGRAM_UNAVAILABLE = -32100
IPC_TELEGRAM_SEND_FAILED = -32101
IPC_TELEGRAM_TOKEN_INVALID = -32102  # 401 from the Bot API
IPC_TELEGRAM_BLOCKED_BY_USER = -32103  # 403
IPC_TELEGRAM_RATE_LIMITED = -32104  # 429
IPC_TELEGRAM_ALLOWLIST_REJECTED = -32105
IPC_TELEGRAM_CONFIRMATION_TIMEOUT = -32106
IPC_TELEGRAM_CONFIRMATION_REFUSED = -32107
IPC_TELEGRAM_SETUP_FAILED = -32108
IPC_TELEGRAM_NONOWNER_TIER_A_REFUSED = -32109


__all__ = [
    "IPC_TELEGRAM_UNAVAILABLE",
    "IPC_TELEGRAM_SEND_FAILED",
    "IPC_TELEGRAM_TOKEN_INVALID",
    "IPC_TELEGRAM_BLOCKED_BY_USER",
    "IPC_TELEGRAM_RATE_LIMITED",
    "IPC_TELEGRAM_ALLOWLIST_REJECTED",
    "IPC_TELEGRAM_CONFIRMATION_TIMEOUT",
    "IPC_TELEGRAM_CONFIRMATION_REFUSED",
    "IPC_TELEGRAM_SETUP_FAILED",
    "IPC_TELEGRAM_NONOWNER_TIER_A_REFUSED",
]
