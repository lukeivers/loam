"""Adapter — telegram-interface framework integration (amendment #9).

Phase: after_orchestrator_ready. Dependencies: after primary_persona
(owner of ``OneOnOneChannel`` / ``ChannelKind.personal_telegram``) and
after safety_layer (gate chain established before the adapter wires
its own channel surface).

Role: construct a ``TelegramAdapter`` from telegram-interface's public
surface (``AvailabilityProbe``, ``AccessFile.load``, ``BotApiClient``,
``TelegramAdapter``), build its ``OneOnOneChannel``, and expose both
on the host — so pos-v2 workspaces compose Telegram as the thirteenth
foundational adapter without user intervention. Zero sealed-component
edits; every symbol consumed is already exported by
``telegram-interface`` at ``cdfb3f3``.

Fail-closed direction (proposal §2): degraded-alive at default. When
``~/.loam/telegram.yaml`` is absent, or the bot token is not
configured, or the allowlist file is missing, the adapter STILL
composes — ``is_active=False`` on the channel, ``send`` routes through
the component's fallback. The adapter only raises
``AdapterRaisedError`` when ``~/.loam/telegram.yaml`` contains
``required: true`` AND credentials are absent.

Config (``~/.loam/telegram.yaml``, all fields optional):

    required: bool        # default False; true → fail-close boot if creds absent
    env_path: str         # override ~/.claude/channels/telegram/.env location
    access_path: str      # override ~/.claude/channels/telegram/access.json
    default_tier: int     # dormancy-config default
    probe_interval_s: int # availability-probe cadence override (unused by default

The credential source of truth remains
``~/.claude/channels/telegram/.env`` (per proposal §5 #5). The
framework adapter does NOT relocate the token into ``~/.loam/``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, ClassVar

import yaml

from ..errors import AdapterRaisedError
from ..spec import BaseContribution, ContributionMetadata, Phase


class TelegramInterfaceContribution(BaseContribution):
    metadata: ClassVar[ContributionMetadata] = ContributionMetadata(
        name="telegram_interface",
        phase=Phase.after_orchestrator_ready,
        after=("primary_persona", "safety_layer"),
        required=False,
    )

    def contribute(self, host: Any) -> None:
        from loam.telegram_interface import (
            IPC_TELEGRAM_SETUP_FAILED,
            IPC_TELEGRAM_TOKEN_INVALID,
        )
        from loam.telegram_interface.adapter import TelegramAdapter
        from loam.telegram_interface.allowlist import AccessFile
        from loam.telegram_interface.availability import (
            AvailabilityProbe,
            FailureClass,
            ProbeResult,
            token_configured,
        )

        cfg_path = host.config_dir / "telegram.yaml"
        cfg: dict[str, Any] = {}
        if cfg_path.exists():
            loaded = yaml.safe_load(cfg_path.read_text()) or {}
            if isinstance(loaded, dict):
                cfg = loaded

        required = bool(cfg.get("required", False))

        env_path_raw = cfg.get("env_path")
        env_path = (
            Path(str(env_path_raw)).expanduser() if env_path_raw else None
        )

        access_path_raw = cfg.get("access_path")
        access_path = (
            Path(str(access_path_raw)).expanduser()
            if access_path_raw
            else None
        )

        # Credential presence is decided by the telegram-interface
        # component's own ``token_configured`` helper — single source
        # of truth for the TELEGRAM_BOT_TOKEN env var + .env file
        # reader. Under required=True, missing credentials raise
        # AdapterRaisedError wrapping the component's own code; under
        # required=False (default) the adapter continues and the probe
        # simply reports the token-missing failure class.
        have_token = token_configured(env_path=env_path)

        if required and not have_token:
            raise AdapterRaisedError(
                "telegram_interface: required=true but TELEGRAM_BOT_TOKEN "
                "is not configured (set in ~/.claude/channels/telegram/.env "
                "or the TELEGRAM_BOT_TOKEN env var, or flip required=false "
                "in ~/.loam/telegram.yaml)",
                data={
                    "code": IPC_TELEGRAM_TOKEN_INVALID,
                    "env_path": str(env_path) if env_path else None,
                    "required": True,
                },
            )

        # Deterministic, non-network probe. ``token_configured`` already
        # checked filesystem + env; the getme probe would otherwise hit
        # api.telegram.org at boot — which AC3/AC6 forbid (proposal §7
        # halt trigger "AC6 requires network I/O at boot"). We wire a
        # no-network probe that surfaces the token state as its
        # ProbeResult, letting the adapter compose with ``is_active``
        # reflecting the credential-present-but-unverified state.
        async def _no_network_getme() -> ProbeResult:
            if not have_token:
                return ProbeResult(
                    available=False,
                    failure_class=FailureClass.token_missing,
                    detail="TELEGRAM_BOT_TOKEN not set",
                )
            # Token present, but we have not verified it against the
            # Bot API. Treat as unavailable-until-probed so
            # cached_available() at send-time routes to fallback; the
            # component's own background probe will flip this to
            # available on first successful getMe. This keeps boot
            # deterministic (no network) and preserves the
            # degraded-alive default shape (adapter composes, channel
            # exists, is_active is False until the real probe runs).
            return ProbeResult(
                available=False,
                failure_class=FailureClass.plugin_not_connected,
                detail="boot-time probe skipped; awaiting background probe",
            )

        availability = AvailabilityProbe(
            getme_probe=_no_network_getme,
            mcp_tool_probe=None,
            env_path=env_path,
        )

        access = AccessFile.load(path=access_path)

        # If required=True and the allowlist has no owner identity,
        # the adapter cannot deliver messages to anyone — fail-close
        # per proposal AC6 (IPC_TELEGRAM_SETUP_FAILED).
        if required and access.owner() is None:
            raise AdapterRaisedError(
                "telegram_interface: required=true but no owner identity "
                "exists in the access allowlist; run the setup walkthrough "
                "or flip required=false in ~/.loam/telegram.yaml",
                data={
                    "code": IPC_TELEGRAM_SETUP_FAILED,
                    "access_path": str(access.path),
                    "required": True,
                },
            )

        adapter = TelegramAdapter(
            availability=availability,
            access=access,
            bot_api=None,
            mcp_client=None,
        )
        channel = adapter.build_channel()

        host.telegram_adapter = adapter
        host.telegram_channel = channel
        host.channel_registry["telegram"] = channel
