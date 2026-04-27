"""Session-two Telegram setup walkthrough.

Step-by-step-when-impossible. Six numbered steps, each with an
expected-time estimate. The user-handleable steps are numbered;
system-handleable steps are silent.

Self-retire on success — ``~/.pos/telegram-setup-offered`` with
``status: done`` is the marker that short-circuits the "offer setup"
code path. The ``should_offer`` gate reads this marker every time;
when the marker exists with ``status: done`` or ``status: declined``
the walkthrough never offers again (the ``declined`` state requires
an explicit ``status: deferred`` + re-offer on ask-only path per the
G2 Q1 ruling).

Failure at any step writes a ``status: failed`` marker with the step
number; the next session resumes from the failed step rather than
starting over.

Eve's inference #5 (decline-marker filename pattern): kept as
``~/.pos/telegram-setup-offered-declined``. Challenge note: could be
folded into the single ``~/.pos/telegram-setup-offered`` marker with
``status: declined`` inside — and that's what this module does; the
separate file is redundant. Collapsed to a single marker file.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Awaitable, Callable

from . import IPC_TELEGRAM_SETUP_FAILED
from . import observability as obs
from .allowlist import AccessFile, AuthorityClass
from .availability import plugin_installed, token_configured


DEFAULT_MARKER_PATH = Path("~/.pos/telegram-setup-offered").expanduser()


class SetupStatus(str, Enum):
    not_started = "not_started"
    offered = "offered"
    deferred = "deferred"
    in_progress = "in_progress"
    failed = "failed"
    done = "done"
    declined = "declined"  # "stop offering telegram setup"
    already_configured = "already_configured"


@dataclass
class SetupMarker:
    path: Path = DEFAULT_MARKER_PATH

    def read(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"status": SetupStatus.not_started.value}
        try:
            return json.loads(self.path.read_text())
        except (json.JSONDecodeError, OSError):
            return {"status": SetupStatus.not_started.value}

    def write(self, *, status: SetupStatus, **kwargs: Any) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "status": status.value,
            "last_updated_at": datetime.now(timezone.utc).isoformat(),
            **kwargs,
        }
        self.path.write_text(json.dumps(payload, indent=2))


def should_offer(
    *, marker: SetupMarker | None = None, access: AccessFile | None = None
) -> bool:
    """Gate for the "offer setup" code path. Self-retire means:
    returns False when the marker says ``done`` / ``declined`` /
    ``already_configured``, or when ``access.json`` already has a
    non-empty ``allowFrom`` (the power-user pre-configured case).
    """
    m = marker or SetupMarker()
    rec = m.read()
    status = rec.get("status")
    if status in {
        SetupStatus.done.value,
        SetupStatus.declined.value,
        SetupStatus.already_configured.value,
    }:
        return False

    # If access.json is already configured, write the
    # already-configured marker and short-circuit.
    a = access or AccessFile.load()
    if a.allow_from:
        m.write(status=SetupStatus.already_configured)
        return False

    # Deferred: offer again only on explicit user ask (G2 Q1 ruling).
    # The caller is the primary persona whose prompt hook reads the
    # marker; the "ask-only path" is implemented there. From this
    # function's perspective: do not proactively offer again.
    if status == SetupStatus.deferred.value:
        return False

    return True


# ---- user-facing strings -------------------------------------------

STEP1 = """\
Step 1 (user, ~30 seconds).
Install the plugin. In your terminal, in this Claude Code session, run:
   /plugin install telegram@claude-plugins-official
   /reload-plugins
Reply "done" when the plugin is installed.
"""

STEP2 = """\
Step 2 (user, ~2 minutes).
Create a bot with Telegram's BotFather.
   (a) Open Telegram and go to: https://t.me/BotFather
   (b) Send BotFather: /newbot
   (c) Give it a display name (anything — e.g. "Eve").
   (d) Give it a unique username ending in "bot" — e.g. @your_eve_bot.
   (e) BotFather replies with a token that looks like 123456789:AAH...
       Copy the whole token including the number and colon.
Paste the token here when you have it.
"""

STEP3 = """\
Step 3 (user, ~30 seconds).
Exit this session and start a new one with the channel flag:
   Ctrl+D to exit
   Then: claude --channels plugin:telegram@claude-plugins-official
I will pick up in step 4 on your next session start.
"""

STEP4 = """\
Step 4 (user, ~1 minute).
DM your bot from Telegram. Any message — "hello" is fine.
The bot replies with a 6-character pairing code. Send me that code.
"""

OPENING_OFFER = """\
Eve: Telegram setup is the next thing that makes pos-v2 fully useful — \
it becomes the default channel so I can reach you when you're not at \
your desk. This takes about 5 minutes, in six steps (two are silent on \
my side). Want to walk through it now, or defer?

Privacy note: messages you send via Telegram pass through Telegram's \
servers and through Claude. Same privacy posture as chatting with me \
in this terminal, plus Telegram's side of the pipe. If you want anything \
kept strictly off Telegram — health, finances, private names — say so \
and I'll keep it in-session.
"""


# ---- walkthrough orchestrator --------------------------------------


@dataclass
class WalkthroughStep:
    number: int
    label: str
    expected_time_s: float


STEPS: list[WalkthroughStep] = [
    WalkthroughStep(1, "install_plugin", 30),
    WalkthroughStep(2, "create_bot_token", 120),
    WalkthroughStep(3, "restart_with_channels_flag", 30),
    WalkthroughStep(4, "dm_bot_and_pair", 60),
    WalkthroughStep(5, "lock_allowlist_policy", 0),  # system-silent
    WalkthroughStep(6, "round_trip_verify", 0),  # system-silent
]


TOKEN_REGEX = re.compile(r"^\d+:[A-Za-z0-9_-]{20,}$")


@dataclass
class SetupWalkthrough:
    """In-session orchestrator. The primary persona invokes this from
    the session-two turn. Each call advances at most one step.
    """

    marker: SetupMarker
    access: AccessFile
    emit: Callable[[str], Awaitable[None]]
    # System steps wired in by the orchestrator:
    write_token: Callable[[str], Awaitable[None]] | None = None
    pair_sender: Callable[[str], Awaitable[str]] | None = None  # returns user_id
    set_allowlist_policy: Callable[[], Awaitable[None]] | None = None
    round_trip_verify: Callable[[], Awaitable[bool]] | None = None

    async def offer(self) -> None:
        obs.setup_step(step=0, status="offer")
        self.marker.write(status=SetupStatus.offered)
        await self.emit(OPENING_OFFER)

    async def decline(self) -> None:
        obs.setup_step(step=0, status="declined")
        self.marker.write(status=SetupStatus.declined)

    async def defer(self) -> None:
        obs.setup_step(step=0, status="deferred")
        self.marker.write(status=SetupStatus.deferred)

    async def step1_emit(self) -> None:
        obs.setup_step(step=1, status="start")
        self.marker.write(status=SetupStatus.in_progress, current_step=1)
        await self.emit(STEP1)

    async def step1_confirm(self) -> None:
        if not plugin_installed():
            obs.setup_step(
                step=1, status="failed", detail="plugin cache not found"
            )
            self.marker.write(
                status=SetupStatus.failed,
                failed_at_step=1,
                detail="plugin cache directory absent — retry the /plugin install command",
            )
            await self.emit(
                "The plugin doesn't appear to be installed — the cache "
                "directory at ~/.claude/plugins/cache/claude-plugins-official/"
                "telegram/ is missing. Try `/plugin install telegram@claude-"
                "plugins-official` again, then `/reload-plugins`."
            )
            return
        obs.setup_step(step=1, status="ok")
        await self.step2_emit()

    async def step2_emit(self) -> None:
        obs.setup_step(step=2, status="start")
        self.marker.write(status=SetupStatus.in_progress, current_step=2)
        await self.emit(STEP2)

    async def step2_confirm(self, token: str) -> None:
        t = token.strip()
        if not TOKEN_REGEX.match(t):
            obs.setup_step(step=2, status="failed", detail="token regex mismatch")
            self.marker.write(
                status=SetupStatus.failed,
                failed_at_step=2,
                detail="token does not match BotFather shape (digits:letters)",
            )
            await self.emit(
                "That doesn't look like a BotFather token — I expect the "
                "form 123456789:AAHdqTcv... Could you double-check you "
                "pasted the whole line including the number and colon?"
            )
            return
        if self.write_token is None:
            raise RuntimeError("write_token hook not wired")
        await self.write_token(t)
        obs.setup_step(step=2, status="ok")
        await self.step3_emit()

    async def step3_emit(self) -> None:
        obs.setup_step(step=3, status="start")
        self.marker.write(status=SetupStatus.in_progress, current_step=3)
        await self.emit(STEP3)

    async def step4_emit(self) -> None:
        obs.setup_step(step=4, status="start")
        self.marker.write(status=SetupStatus.in_progress, current_step=4)
        await self.emit(STEP4)

    async def step4_confirm(self, pairing_code: str) -> None:
        code = pairing_code.strip()
        if len(code) != 6 or not code.isalnum():
            obs.setup_step(step=4, status="failed", detail="pairing code shape")
            self.marker.write(
                status=SetupStatus.failed,
                failed_at_step=4,
                detail="pairing code should be 6 alphanumeric chars",
            )
            await self.emit(
                "That pairing code isn't the right shape — BotFather emits "
                "6 alphanumeric characters. Could you re-check what the "
                "bot replied with?"
            )
            return
        if self.pair_sender is None:
            raise RuntimeError("pair_sender hook not wired")
        try:
            user_id = await self.pair_sender(code)
        except Exception as e:  # noqa: BLE001
            obs.setup_step(step=4, status="failed", detail=str(e))
            self.marker.write(
                status=SetupStatus.failed,
                failed_at_step=4,
                detail=f"pairing failed: {e}. Most likely: session not "
                "launched with --channels flag, or stale poller.",
            )
            await self.emit(
                "The pairing didn't complete. Two most likely causes: "
                "this session isn't launched with `--channels "
                "plugin:telegram@claude-plugins-official`, or an old "
                "bot poller is still holding the token. Could you "
                "restart with the flag (step 3) and DM the bot again?"
            )
            return
        # Populate pos_identities with the owner record.
        self.access.add_identity(
            user_id=user_id,
            display_name="owner",
            relationship="owner",
            authority_class=AuthorityClass.OWNER,
            actor="setup_walkthrough",
        )
        self.access.save()
        obs.setup_step(step=4, status="ok")
        await self.step5_silent()

    async def step5_silent(self) -> None:
        obs.setup_step(step=5, status="start")
        if self.set_allowlist_policy is not None:
            try:
                await self.set_allowlist_policy()
                obs.setup_step(step=5, status="ok")
            except Exception as e:  # noqa: BLE001
                obs.setup_step(step=5, status="failed", detail=str(e))
                self.marker.write(
                    status=SetupStatus.failed,
                    failed_at_step=5,
                    detail=f"could not set allowlist policy: {e}",
                )
                await self.emit(
                    "I couldn't lock down the allowlist policy — "
                    "check ~/.claude/channels/telegram/ permissions."
                )
                return
        await self.step6_silent()

    async def step6_silent(self) -> None:
        obs.setup_step(step=6, status="start")
        if self.round_trip_verify is None:
            # Without a verifier we still self-retire; real orchestrator
            # wires this.
            ok = True
        else:
            try:
                ok = await self.round_trip_verify()
            except Exception as e:  # noqa: BLE001
                obs.setup_step(step=6, status="failed", detail=str(e))
                self.marker.write(
                    status=SetupStatus.failed,
                    failed_at_step=6,
                    detail=f"round-trip verify raised: {e}",
                )
                await self.emit(
                    "I couldn't complete the round-trip verify — "
                    f"error: {e}. Telegram might be offline or the "
                    "pairing might not have fully landed; try again "
                    "in a minute."
                )
                return
        if not ok:
            obs.setup_step(step=6, status="failed", detail="verify returned False")
            self.marker.write(
                status=SetupStatus.failed,
                failed_at_step=6,
                detail="round-trip verify returned False",
            )
            await self.emit(
                "Round-trip verify didn't complete. The pairing is in "
                "place but I couldn't confirm end-to-end delivery. Try "
                "sending the bot a message to confirm."
            )
            return
        obs.setup_step(step=6, status="ok")
        self.marker.write(status=SetupStatus.done)
        await self.emit(
            "Done. Telegram is primary now. I'll use this thread for "
            "anything that doesn't need you in a full Claude Code "
            "session. Say \"stop using Telegram\" any time to switch "
            "back."
        )
