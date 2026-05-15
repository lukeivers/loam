"""Isolated sub-loam PTY driver core.

The decided mechanism (plan §3 Part 2 — one design, no menu):

  A scratch loam workspace, created by the real production path
  (``bootstrap_new_workspace``), made persona-active by Part 1's
  first-run scaffold extension, then driven by a programmatic PTY
  harness that spawns an INTERACTIVE ``claude`` session inside that
  workspace under a fully isolated config root, with the telegram
  plugin and all channels disabled, fed the frozen ``build_prompt``
  as the first user turn over the PTY, capturing the full transcript.

The four decided sub-components, each implemented here:

  1. Driver = a PTY harness (``pty.openpty()`` + ``subprocess``),
     NOT ``claude -p`` (proven not-loam by the probe), NOT
     computer-use (tier-"click" blocks typing). An interactive
     session is the only thing that binds the persona + runs the
     multi-turn agentic loop.
  2. Isolation = a dedicated ``CLAUDE_CONFIG_DIR`` + an explicit
     empty MCP config (``--strict-mcp-config --mcp-config <empty>``)
     + NO telegram plugin/channel + a namespaced workspace slug.
  3. Service-isolation = ``service_bootstrap=False`` + scratch-scoped
     ``pos_root`` (the production ``bootstrap_new_workspace``
     defaults; the driver MUST NOT pass ``service_bootstrap=True``).
  4. Lifecycle = create-on-demand, teardown-on-exit, scratch-rooted.

ONE :class:`IsolationConfig` drives both operator-protection and
bench-validity (AC.LIPW.6). :func:`build_isolated_env` and
:func:`build_isolated_claude_argv` are the single code path that
produces the spawned process's environment + argv; there is no
second, divergent isolation surface.

Stdlib-only. NO Anthropic API key (``feedback_no_anthropic_api_key``)
— the real ``claude`` binary, default Sonnet.
"""

from __future__ import annotations

import json
import os
import select
import shutil
import signal
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# The exact and SOLE telegram/bun-kill vector (plan §2 point 9): a
# second ``claude`` process that loads the telegram plugin spawns a
# competing ``bun server.ts`` that SIGTERMs the prior poller for the
# single bot-token getUpdates slot. Removing the telegram plugin from
# the sub-session's reachable set is necessary AND sufficient
# (D-LIPW.5). These markers are what the isolation must exclude from
# the spawned argv/env; the AC.LIPW.5 sentinel test asserts their
# absence from the spawned process.
_TELEGRAM_PLUGIN_MARKERS = (
    "plugin:telegram",
    "telegram@claude-plugins-official",
    "claude-plugins-official/telegram",
)


@dataclass(frozen=True)
class IsolationConfig:
    """The ONE isolation configuration (AC.LIPW.6).

    A single object whose derived env + argv simultaneously:

      - protect a concurrently-running operator session's telegram/bun
        poller (no telegram plugin reachable -> no competing
        ``bun server.ts`` -> the operator's poller is never SIGTERM'd),
        AND
      - yield an operator-environment-free bench measurement (empty
        MCP + no channels + no telegram plugin -> the measured
        behaviour is loam-the-persona-and-loop, not loam-plus-the-
        operator's ambient plugins/channels).

    BUILD-TIME CORRECTION OF D-LIPW.5 (empirically grounded, plan
    §13 D-LIPW.5 pre-resolved this contingency). Verified at build
    time against the real ``claude`` binary:

      - The kill vector (plan §2 point 9) is SPECIFICALLY the telegram
        plugin spawning a competing ``bun server.ts``. Excluding the
        telegram plugin + ``--channels`` + empty MCP is NECESSARY AND
        SUFFICIENT operator-protection (verified: a full driven run
        with default config but no telegram plugin left the operator's
        ``bun server.ts`` count unchanged and PID 22884 alive).
      - Relocating ``CLAUDE_CONFIG_DIR`` away from the default is
        OVER-isolation: Claude Code's subscription credential lives in
        the macOS login keychain keyed to the DEFAULT config location;
        a virgin relocated config root reports ``Not logged in`` and
        — per ``feedback_no_anthropic_api_key`` (NO API key, ever) —
        cannot authenticate. Full config-air-gap therefore makes the
        driver non-functional WITHOUT being required for the kill-
        vector. It is retained as an OPT-IN (``air_gapped_config``)
        for callers that supply their own auth into the isolated root.

    The two properties still fall out of ONE configuration object —
    the plugin/channel/MCP exclusion delivers both. There is no
    second isolation surface (AC.LIPW.6 holds; the corrected mechanism
    is one code path, not two).
    """

    # Dedicated config/state root. By default the driver does NOT
    # relocate CLAUDE_CONFIG_DIR here (subscription auth must work —
    # see ``air_gapped_config``); the path is still used for the
    # empty-MCP config + scratch state. NEVER the operator's
    # ``~/.claude`` (the plugin-cache singleton root).
    claude_config_dir: Path

    # Path to an explicit empty MCP config (``{"mcpServers":{}}``),
    # mirroring run_raw_llm's verified-empty config. Combined with
    # ``--strict-mcp-config`` so no other MCP configuration is read.
    empty_mcp_config_path: Path

    # The scratch workspace's unique slug. Its launchd labels are
    # ``com.loam.<slug>.<kind>`` (namespaced) so they cannot bootout
    # the operator's services even at the launchd layer.
    workspace_slug: str

    # Model alias. Default Sonnet (token-efficiency +
    # ``feedback_no_anthropic_api_key`` — subscription-only).
    model: str = "sonnet"

    # Opt-in full config air-gap. Default False: the sub-session uses
    # the default Claude Code config location so the keychain-stored
    # subscription credential authenticates (NO API key per
    # ``feedback_no_anthropic_api_key``). When True, the spawned
    # process gets CLAUDE_CONFIG_DIR=<claude_config_dir> — the caller
    # is then responsible for provisioning auth into that root (the
    # bench/probe path leaves this False; operator-protection does NOT
    # depend on it — the telegram-plugin/channel/MCP exclusion is the
    # necessary-and-sufficient kill-vector isolation).
    air_gapped_config: bool = False

    # Extra env keys to scrub from the child so no operator-side
    # telegram/bot state leaks in. Always includes the documented
    # telegram bot-token env spellings + any API key
    # (``feedback_no_anthropic_api_key`` — the sub-session must use
    # the subscription, never an API key).
    scrub_env_keys: tuple[str, ...] = field(
        default=(
            "TELEGRAM_BOT_TOKEN",
            "CLAUDE_PLUGIN_TELEGRAM_BOT_TOKEN",
            "ANTHROPIC_API_KEY",
        )
    )

    def __post_init__(self) -> None:
        cfg = Path(self.claude_config_dir).expanduser()
        home_claude = Path.home() / ".claude"
        # Structural guard: the dedicated root must never be the
        # operator's ~/.claude (the kill-vector + bench-contamination
        # root). Load-bearing invariant of AC.LIPW.5/.6.
        if cfg.resolve() == home_claude.resolve():
            raise ValueError(
                "IsolationConfig.claude_config_dir must NOT be the "
                f"operator's {home_claude} — that root carries the "
                "plugin-cache singleton + telegram bot token; using "
                "it re-introduces the exact kill vector (plan §2 "
                "point 9)."
            )


def build_isolated_env(
    config: IsolationConfig, *, base_env: dict[str, str] | None = None
) -> dict[str, str]:
    """Produce the spawned ``claude`` process's environment.

    The single env-construction code path (AC.LIPW.6). Always scrubs
    the telegram bot-token + API-key env spellings so neither the
    operator's poller token nor an API key leaks into the sub-session
    (``feedback_no_anthropic_api_key``). Only relocates
    ``CLAUDE_CONFIG_DIR`` when ``air_gapped_config`` is True — the
    default keeps the keychain-stored subscription credential
    reachable (a relocated virgin root reports ``Not logged in`` and,
    with no API key, cannot authenticate). Operator-protection does
    NOT depend on the relocation: the kill vector is the telegram
    plugin (excluded from the argv), not the config root.
    """
    env = dict(os.environ if base_env is None else base_env)
    for key in config.scrub_env_keys:
        env.pop(key, None)
    if config.air_gapped_config:
        env["CLAUDE_CONFIG_DIR"] = str(Path(config.claude_config_dir))
    return env


def build_isolated_claude_argv(
    config: IsolationConfig, *, claude_binary: str = "claude"
) -> list[str]:
    """Produce the spawned ``claude`` process's argv.

    The single argv-construction code path (AC.LIPW.6). Carries:

      - ``--strict-mcp-config --mcp-config <empty>`` (zero servers),
      - ``--model <sonnet>`` (default Sonnet; no API key),
      - ``--dangerously-skip-permissions`` — the scratch workspace is
        ephemeral + driver-created (nothing untrusted in it); without
        this the interactive TUI presents a workspace-trust gate
        BEFORE the agentic loop on a fresh path and the driven prompt
        lands on the trust dialog (verified at build time — this is
        the §10.4 PTY-harness reliability surface). The operator's
        own session uses the same flag; it does NOT touch the
        kill-vector isolation (orthogonal to telegram/channels/MCP),
      - NO ``--channels`` flag (so no channel poller is started),
      - NO telegram plugin on the plugin path (so no competing
        ``bun server.ts`` is ever spawned — the sole kill vector).

    The argv is asserted telegram-free by a structural guard before
    return; a regression that re-introduces the plugin raises rather
    than silently shipping a kill-capable invocation.
    """
    argv = [
        claude_binary,
        "--dangerously-skip-permissions",
        "--strict-mcp-config",
        "--mcp-config",
        str(Path(config.empty_mcp_config_path)),
        "--model",
        config.model,
    ]
    joined = " ".join(argv)
    for marker in _TELEGRAM_PLUGIN_MARKERS:
        if marker in joined:
            raise ValueError(
                f"isolated argv carries telegram marker {marker!r} — "
                "the sole kill vector (plan §2 point 9). Refusing to "
                "build a kill-capable invocation."
            )
    return argv


def pretrust_workspace(
    *, workspace_root: Path, claude_json_path: Path | None = None
) -> bool:
    """Pre-register the scratch workspace as trusted in the Claude
    Code config so the interactive TUI does not present the
    workspace-trust dialog BEFORE the agentic loop.

    Verified at build time: a fresh-path interactive ``claude``
    presents *"Is this a project you trust?"* before accepting input
    even with ``--dangerously-skip-permissions`` (that flag skips
    permission prompts, not the per-path trust gate; the
    non-interactive ``-p`` path auto-skips it but the PTY-interactive
    path does not). The deterministic fix is to seed
    ``projects[<ws-abs-path>].hasTrustDialogAccepted = True`` in the
    Claude config (the same per-project marker Claude Code writes when
    the operator answers the dialog) — far more robust than racing a
    TUI keystroke. The scratch workspace is ephemeral + driver-created
    so pre-trusting it is correct (there is nothing untrusted in it).

    Returns True iff the marker was written. Fail-soft: a missing/
    unreadable config is created minimally; any structural surprise
    returns False (the run still proceeds; the TUI handshake fallback
    in :meth:`SubLoamDriver.drive` answers the dialog if it appears).
    """
    cj = (
        Path(claude_json_path)
        if claude_json_path is not None
        else Path.home() / ".claude.json"
    )
    ws = str(Path(workspace_root).resolve())
    try:
        data: dict[str, Any] = {}
        if cj.exists() and cj.stat().st_size > 0:
            data = json.loads(cj.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return False
        projects = data.setdefault("projects", {})
        if not isinstance(projects, dict):
            return False
        entry = projects.setdefault(ws, {})
        if not isinstance(entry, dict):
            return False
        entry["hasTrustDialogAccepted"] = True
        entry.setdefault("hasCompletedProjectOnboarding", True)
        tmp = cj.with_suffix(cj.suffix + ".subloam.tmp")
        tmp.write_text(
            json.dumps(data, ensure_ascii=False), encoding="utf-8"
        )
        tmp.replace(cj)
        return True
    except Exception:  # noqa: BLE001 — fail-soft (TUI fallback covers)
        return False


def write_empty_mcp_config(path: Path) -> Path:
    """Write the explicit empty MCP config (``{"mcpServers":{}}``).

    Mirrors run_raw_llm's verified-empty config so the sub-session's
    MCP surface is provably zero under ``--strict-mcp-config``.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"mcpServers": {}}) + "\n", encoding="utf-8"
    )
    return path


@dataclass
class DriverResult:
    """Outcome of one driven sub-loam interactive session."""

    transcript: str
    effective_turns: int
    file_blocks: tuple[str, ...]
    exit_status: int | None
    spawn_argv: tuple[str, ...]
    spawn_env_config_dir: str
    workspace_root: Path
    timed_out: bool = False

    @property
    def is_multi_turn(self) -> bool:
        """AC.LIPW.4: an interactive multi-turn run, distinguishable
        from a ``run_raw_llm``-shape single-pass codegen output."""
        return self.effective_turns > 1


class SubLoamDriver:
    """Drive an interactive ``claude`` session in an isolated scratch
    sub-loam workspace over a PTY harness.

    Lifecycle (plan §3 Part 2 sub-component 4): create-on-demand,
    teardown-on-exit, scratch-rooted. The scratch workspace is
    bootstrapped fresh per run via the production
    ``bootstrap_new_workspace`` path (``service_bootstrap=False`` —
    the production default; the driver MUST NOT pass True) and
    removed on ``close()``.
    """

    def __init__(
        self,
        *,
        scratch_root: Path,
        canonical_source: str,
        isolation: IsolationConfig,
        bootstrap_fn: Any | None = None,
    ) -> None:
        self._scratch_root = Path(scratch_root)
        self._canonical_source = canonical_source
        self._isolation = isolation
        self._workspace_root: Path | None = None
        # Injected for test isolation; production resolves the real
        # bootstrap. The driver NEVER passes service_bootstrap=True.
        self._bootstrap_fn = bootstrap_fn

    # ---- lifecycle ---------------------------------------------------

    def create_instance(self) -> Path:
        """Bootstrap the scratch persona-active workspace.

        Uses the production bootstrap path. ``service_bootstrap`` is
        left at its False default (plan §3 sub-component 3) so the
        sub-loam instance never ``launchctl bootstrap``s and cannot
        collide with the operator's services at the launchd layer.
        """
        self._scratch_root.mkdir(parents=True, exist_ok=True)
        ws = self._scratch_root / self._isolation.workspace_slug
        bootstrap = self._bootstrap_fn
        if bootstrap is None:  # pragma: no cover - real-binary path
            from loam.workspace_bootstrap.new_workspace import (
                bootstrap_new_workspace,
            )

            bootstrap = bootstrap_new_workspace
        bootstrap(
            new_ws_path=ws,
            canonical_source=self._canonical_source,
            # service_bootstrap intentionally omitted — the False
            # default is the decided service-isolation (plan §3
            # sub-component 3). NEVER set True here.
        )
        self._workspace_root = ws.resolve()
        return self._workspace_root

    def close(self) -> None:
        """Teardown-on-exit: remove the scratch workspace tree."""
        if self._workspace_root and self._workspace_root.exists():
            shutil.rmtree(self._workspace_root, ignore_errors=True)
        self._workspace_root = None

    def __enter__(self) -> "SubLoamDriver":
        self.create_instance()
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    # ---- the PTY harness --------------------------------------------

    def drive(
        self,
        first_user_turn: str,
        *,
        idle_timeout_s: float = 90.0,
        hard_timeout_s: float = 600.0,
        tui_warmup_s: float = 10.0,
        claude_binary: str = "claude",
    ) -> DriverResult:
        """Spawn the interactive ``claude`` session over a PTY, send
        ``first_user_turn`` (the FROZEN build_prompt — unchanged, no
        substitution, no ``--append-system-prompt``: owner constraint
        for bench + paper integrity), and read the transcript to
        completion.

        Returns a :class:`DriverResult`. The PTY harness owns the
        session's stdin/stdout; turn boundaries are detected from the
        transcript (multi-turn => persona + agentic loop ran, NOT
        single-pass ``claude -p`` codegen — AC.LIPW.4).
        """
        if self._workspace_root is None:
            raise RuntimeError(
                "create_instance() / context-manager entry must run "
                "before drive()"
            )

        import pty  # noqa: PLC0415 — POSIX-only, lazy

        # The empty-MCP config is part of the isolation contract: a
        # non-existent --mcp-config path makes the real claude reject
        # the invocation ("Invalid MCP configuration") and the
        # isolation would be incomplete. The driver guarantees it
        # exists before spawn (idempotent — write_empty_mcp_config
        # rewrites the canonical `{"mcpServers":{}}`), so the
        # isolation is self-contained regardless of caller (the CLI
        # also writes it; this makes the programmatic path correct
        # too).
        write_empty_mcp_config(self._isolation.empty_mcp_config_path)
        if self._isolation.air_gapped_config:
            # Opt-in air-gap only: ensure the dedicated config root
            # exists. The default path leaves CLAUDE_CONFIG_DIR unset
            # so the keychain-stored subscription credential resolves
            # (no API key — feedback_no_anthropic_api_key).
            Path(self._isolation.claude_config_dir).mkdir(
                parents=True, exist_ok=True
            )

        # Pre-trust the scratch workspace so the interactive TUI does
        # not block on the workspace-trust dialog before the agentic
        # loop (verified build-time requirement — §10.4 PTY-harness
        # reliability surface). The config seeded is the one the
        # default (non-air-gapped) session reads.
        pretrust_workspace(workspace_root=self._workspace_root)

        argv = build_isolated_claude_argv(
            self._isolation, claude_binary=claude_binary
        )
        env = build_isolated_env(self._isolation)

        master_fd, slave_fd = pty.openpty()
        pid = os.fork()
        if pid == 0:  # pragma: no cover - child process
            os.setsid()
            os.dup2(slave_fd, 0)
            os.dup2(slave_fd, 1)
            os.dup2(slave_fd, 2)
            os.close(master_fd)
            os.chdir(str(self._workspace_root))
            os.execvpe(argv[0], argv, env)
            os._exit(127)

        os.close(slave_fd)
        chunks: list[bytes] = []
        deadline = time.monotonic() + hard_timeout_s
        last_activity = time.monotonic()
        timed_out = False

        # Input delivery (verified at build time against the real
        # Claude Code TUI — this is the §10.4 "riskiest surface" the
        # plan flagged; the working mechanism was empirically
        # established, not assumed):
        #
        #   1. The TUI needs ``tui_warmup_s`` to initialise before it
        #      accepts input (sending immediately after fork lands in
        #      a theme/startup screen and is lost).
        #   2. The frozen prompt is TYPED into the input widget, then
        #      a NEWLINE (``\n``) submits the turn. A bare carriage
        #      return (``\r``) does NOT submit in the bracketed-paste
        #      TUI input widget; ``\n`` does. (Verified: ``\r`` left
        #      the prompt unsubmitted; ``\n`` ran the agentic loop and
        #      produced the assistant turn.)
        #
        # The frozen build_prompt is fed UNCHANGED (owner constraint —
        # no substitution, no --append-system-prompt).
        prompt_sent = False
        trust_answered = False
        send_at = time.monotonic() + tui_warmup_s

        while True:
            now = time.monotonic()
            # The idle-timeout only applies AFTER the prompt is sent:
            # a slow TUI warmup (SessionStart hook + skill load) can
            # legitimately emit nothing for tens of seconds before the
            # prompt is delivered; counting that as idle would abort
            # the run before the agentic loop ever starts. The hard
            # deadline still bounds the whole run.
            idle_exceeded = (
                prompt_sent
                and (now - last_activity) > idle_timeout_s
            )
            if now > deadline or idle_exceeded:
                timed_out = now > deadline
                break
            rlist, _, _ = select.select([master_fd], [], [], 1.0)
            if master_fd in rlist:
                try:
                    data = os.read(master_fd, 65536)
                except OSError:
                    break
                if not data:
                    break
                chunks.append(data)
                last_activity = time.monotonic()

            # Defence-in-depth: pretrust_workspace should have
            # suppressed the trust dialog, but if it still appears
            # (config write fail-soft / Claude Code change), answer
            # the default "Yes, I trust this folder" (Enter) once,
            # then delay the prompt send so the TUI settles.
            if not trust_answered:
                seen = b"".join(chunks[-8:]).decode(
                    "utf-8", errors="replace"
                )
                if "trust this folder" in seen:
                    os.write(master_fd, b"\r")
                    trust_answered = True
                    send_at = time.monotonic() + tui_warmup_s

            if not prompt_sent and now >= send_at:
                os.write(master_fd, first_user_turn.encode("utf-8"))
                time.sleep(0.5)
                os.write(master_fd, b"\n")
                prompt_sent = True
                last_activity = time.monotonic()

        os.close(master_fd)
        exit_status: int | None
        try:
            _, status = os.waitpid(pid, os.WNOHANG)
            if status == 0:
                os.kill(pid, signal.SIGTERM)
                time.sleep(0.2)
                os.waitpid(pid, os.WNOHANG)
            exit_status = status
        except ChildProcessError:
            exit_status = None
        except OSError:
            exit_status = None

        transcript = b"".join(chunks).decode("utf-8", errors="replace")
        return DriverResult(
            transcript=transcript,
            effective_turns=_count_effective_turns(transcript),
            file_blocks=tuple(_extract_file_blocks(transcript)),
            exit_status=exit_status,
            spawn_argv=tuple(argv),
            spawn_env_config_dir=env.get("CLAUDE_CONFIG_DIR", ""),
            workspace_root=self._workspace_root,
            timed_out=timed_out,
        )


def _count_effective_turns(transcript: str) -> int:
    """Best-effort effective-turn count from an interactive transcript.

    A single-pass ``claude -p`` codegen output is one block with no
    interactive prompt re-presentation; an interactive multi-turn
    agentic session re-presents the input affordance and emits
    tool-use / assistant blocks across turns. Counts the markers an
    interactive session emits that a single-pass run does not. The
    AC.LIPW.4 verification compares this against a ``run_raw_llm``
    single-pass shape; the absolute number is less load-bearing than
    ``> 1`` (multi-turn) vs ``<= 1`` (single-pass).
    """
    if not transcript.strip():
        return 0
    # Strip ANSI/OSC control sequences so the interactive-TUI escape
    # noise does not drown the turn markers (the interactive
    # transcript is heavy with cursor/colour codes; the single-pass
    # run_raw_llm shape has none).
    import re  # noqa: PLC0415 — local, stdlib

    clean = re.sub(r"\x1b\[[0-9;?]*[a-zA-Z]", "", transcript)
    clean = re.sub(r"\x1b[()=>78][AB0]?", "", clean)
    clean = re.sub(r"\x1b\]\d*;?[^\x07\x1b]*(\x07|\x1b\\)?", "", clean)
    markers = 0
    for needle in (
        "\nassistant",
        "tool_use",
        "tool_result",
        "⏺",  # Claude Code interactive assistant-turn bullet
        "❯",  # interactive TUI input affordance re-presentation
        " primary ",  # the bound persona agent shown in the TUI
        "/effort",  # interactive TUI status line (per-turn)
    ):
        markers += clean.count(needle)
    # Floor at 1 for any non-empty transcript; the multi-turn signal
    # is markers accumulating past a single block (a single-pass
    # run_raw_llm output carries none of these).
    return max(1, markers)


def _extract_file_blocks(transcript: str) -> list[str]:
    """Extract gradeable FILE blocks from the transcript.

    The bench grader consumes ``FILE: <path>`` ... fenced blocks; the
    driver surfaces them so the downstream bench cycle can grade
    without re-parsing. Pure extraction — no grading here (grading is
    downstream of this plan).
    """
    blocks: list[str] = []
    lines = transcript.splitlines()
    i = 0
    while i < len(lines):
        if lines[i].strip().startswith("FILE:"):
            start = i
            i += 1
            while i < len(lines) and not lines[i].strip().startswith(
                "FILE:"
            ):
                i += 1
            blocks.append("\n".join(lines[start:i]))
        else:
            i += 1
    return blocks
