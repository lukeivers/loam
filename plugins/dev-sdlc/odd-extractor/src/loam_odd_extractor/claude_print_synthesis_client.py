"""Subscription-routed LLM client for odd-extractor synthesis (v0.2.5 corrective C4-pivot).

Per v0.2.5 corrective C4-pivot dispatch brief: NO Anthropic SDK, NO
``ANTHROPIC_API_KEY`` — the synthesis layer routes through ``claude -p``
subprocess invocations that consume the user's Claude Max subscription via
OAuth keychain. Mirrors the precedent at
``framework/memory-system/src/claude_print_client.py`` (memory-system
amendment #8) — same subprocess invocation shape, same env scrubbing, same
unauthenticated-marker detection.

This module is a **synthesis-layer-local** shim. It exists to keep the
odd-extractor's existing ``anthropic_client: Any`` parameter contract
intact across synthesis.py / backing_map.py / completeness.py /
build_next.py / altitude_validator.py without rewriting their call sites
or breaking sealed AC tests that pass duck-typed stubs with
``.messages.create(...)`` returning ``content[0].text``-shaped responses.

Shape contract (the subset of the Anthropic Messages API that
odd-extractor's call sites use):

    client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=8000,
        system=[{"type":"text","text":"<prompt>","cache_control":...}]
                | "<prompt-string>",
        messages=[{"role":"user","content":"<text>"}],
    ) -> response

    response.content[0].text   # str
    response.usage.input_tokens / .output_tokens   # int (estimate)

All call sites already tolerate either the list-of-blocks ``system`` shape
or the string ``system`` shape (per ``except TypeError`` fallback in
synthesis.py + completeness.py). Backing-map / build-next pass the string
shape directly.

Implementation: every ``messages.create(...)`` call composes a single
flattened prompt (system + user labelled), spawns ``claude -p
--no-session-persistence --output-format json --model <model> <prompt>``
under a scrubbed env (PATH/HOME/USER allow-list — drops
ANTHROPIC_API_KEY/OPENAI_API_KEY so a future SDK fall-through cannot leak
to a billed path), parses the result envelope, and synthesizes a
Message-shaped response. The ``--bare`` flag is explicitly NOT passed —
``--bare`` would bypass OAuth and require ANTHROPIC_API_KEY, which is the
exact thing this client avoids.

Cost: ``total_cost_usd`` from the envelope is mapped to ``usage`` token
estimates via the cents-per-token constants pinned at synthesis.py /
completeness.py / backing_map.py. On Max subscription, ``total_cost_usd``
typically reads 0.0 — the per-call cost-tracker treats this as the
billing-floor sentinel; the synthesis layer's ``cost_actual_cents``
accounting still computes via input/output token counts where the CLI
provides them.

Skip semantics: callers that want to test without a live ``claude``
binary must inject a stub directly (matching the existing
``messages.create()`` shape) — this client does NOT provide a
test-only mode. The shim's job is "be the production claude-p backend";
the stub-mode contract is the parameter's `Any` typing.

Errors:

- :class:`ClaudeBinaryMissingError` — ``shutil.which("claude")`` returned
  ``None`` at construction. Same surface as memory-system's
  -32110-coded equivalent; this module does not claim a numeric block
  (memory-system owns -32110-32119; reusing the names without claiming
  codes keeps blast radius local).
- :class:`ClaudePrintShimError` — per-call parse failure from a malformed
  ``claude -p --output-format json`` payload, or live "Not logged in"
  marker in the response.

References:

- ``framework/memory-system/src/claude_print_client.py`` — the precedent
  this client mirrors.
- ``docs/rebuild/plans/v0-2-5-corrective-c4-pivot-claude-print-synthesis.md``
  §14 method-decision register.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from typing import Any


DEFAULT_MODEL = "claude-sonnet-4-5"

# Per ``framework/memory-system/src/claude_print_client.py`` —
# minimum allow-list. ``USER`` admitted by amendment #30 because
# macOS launchd-spawned subprocess OAuth keychain lookup requires
# USER; PATH+HOME+USER is the tested floor.
_ENV_ALLOWED_VARS = (
    "PATH",
    "HOME",
    "USER",
)

# Substring markers (case-insensitive) the probe / per-call response
# emits when OAuth state is absent.
_UNAUTH_MARKERS = (
    "not logged in",
    "please run /login",
)

# v0.2.5 corrective C5 — MCP-isolation payload for the child ``claude -p``
# subprocess. Mirrors ``framework/workspace-sync/src/loam/workspace_sync/_resolver_client.py``
# (AC.WSα.8, verified 2026-04-27) + memory-system's claude_print_client.
#
# Without this isolation, the child claude inherits the parent session's MCP
# server config — including the telegram MCP. The telegram loader at
# ``~/.claude/plugins/cache/claude-plugins-official/telegram/0.0.6/server.ts:60-78``
# has PID-stomp dedup logic: any new instance SIGTERMs the prior PID-file
# holder. Result without isolation: every odd-extractor synthesis call that
# forks ``claude -p`` kills the parent session's telegram bot.
#
# Owner ruling 2026-05-05 (Telegram 10196): subprocess invocations must launch
# without telegram. ``--strict-mcp-config --mcp-config <empty config>``
# disables every MCP server in the child — protecting telegram and any other
# MCP the user adds later. See plan-doc §14 D-1 for the alternative
# (``CLAUDE_PERSONA`` env-var) and why it was rejected.
_EMPTY_MCP_CONFIG: dict[str, dict[str, Any]] = {"mcpServers": {}}


def _write_empty_mcp_config() -> str:
    """Write the empty MCP config to a process-cached tempfile.

    Returns the absolute path. ``delete=False`` because the subprocess
    inherits the path and reads it after the writing handle is closed.
    Cleanup is best-effort at process exit; the file is small (~25 bytes)
    and lives in ``$TMPDIR`` / ``/tmp``.
    """
    fd = tempfile.NamedTemporaryFile(
        mode="w",
        suffix="-odd-extractor-empty-mcp.json",
        delete=False,
        encoding="utf-8",
    )
    try:
        json.dump(_EMPTY_MCP_CONFIG, fd)
        fd.flush()
    finally:
        fd.close()
    return fd.name


# ---- errors --------------------------------------------------------


class ClaudePrintShimError(Exception):
    """Base for synthesis claude-print client failures.

    Local to odd-extractor; does not claim a memory-system numeric
    error block. Caller (``synthesize_objectives`` / cli.py) translates
    to ``StageError`` / ``OddExtractorError`` as needed.
    """

    pass


class ClaudeBinaryMissingError(ClaudePrintShimError):
    """``claude`` CLI not found on PATH.

    Remediation: install Claude Code
    (https://docs.anthropic.com/claude-code) so the ``claude`` binary
    resolves on the caller's PATH.
    """

    pass


# ---- response shapes mimicking anthropic.types.Message --------------


@dataclass
class _ShimContentBlock:
    """Mimics ``anthropic.types.TextBlock``: ``.type == "text"``, ``.text``."""

    type: str = "text"
    text: str = ""


@dataclass
class _ShimUsage:
    """Mimics ``anthropic.types.Usage``: ``.input_tokens``, ``.output_tokens``."""

    input_tokens: int = 0
    output_tokens: int = 0


@dataclass
class _ShimMessageResponse:
    """Mimics ``anthropic.types.Message``.

    ``.content`` is a list with one ``_ShimContentBlock`` (matching the
    real SDK's response shape for a single text response). ``.usage``
    carries token estimates derived from the ``claude -p`` envelope's
    ``total_cost_usd`` plus prompt-length heuristics.
    """

    content: list[_ShimContentBlock] = field(default_factory=list)
    usage: _ShimUsage = field(default_factory=_ShimUsage)


# ---- env scrub ------------------------------------------------------


def _build_child_env(parent_env: dict[str, str] | None = None) -> dict[str, str]:
    """Scrubbed env dict for the ``claude -p`` child subprocess.

    Drops ``ANTHROPIC_API_KEY`` / ``OPENAI_API_KEY`` / ``GEMINI_API_KEY``
    so a leaked env var cannot fall through to a billed API path.
    """
    if parent_env is None:
        parent_env = dict(os.environ)
    env: dict[str, str] = {}
    for name in _ENV_ALLOWED_VARS:
        if name in parent_env:
            env[name] = parent_env[name]
    env.setdefault("PATH", "/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin")
    return env


def _response_is_unauthenticated(text: str) -> bool:
    haystack = (text or "").lower()
    return any(marker in haystack for marker in _UNAUTH_MARKERS)


# ---- prompt flattening ---------------------------------------------


def _coerce_system_to_text(system: Any) -> str:
    """Flatten the ``system`` argument to a plain string.

    Accepts either:
    - ``str`` — used as-is.
    - ``list[dict]`` — Anthropic SDK shape with ``[{"type":"text","text":...}]``;
      concatenates each block's ``text`` field.
    """
    if isinstance(system, str):
        return system
    if isinstance(system, list):
        parts: list[str] = []
        for block in system:
            if isinstance(block, dict):
                t = block.get("text")
                if isinstance(t, str):
                    parts.append(t)
        return "\n".join(parts)
    return ""


def _coerce_messages_to_text(messages: Any) -> str:
    """Flatten the ``messages`` arg to a plain user-prompt string.

    Accepts the Anthropic SDK shape: ``[{"role":"user","content":"<str>"}]``.
    Multi-block content is joined.
    """
    if not isinstance(messages, list):
        return ""
    parts: list[str] = []
    for m in messages:
        if not isinstance(m, dict):
            continue
        role = (m.get("role") or "user").upper()
        content = m.get("content", "")
        if isinstance(content, list):
            text_parts = []
            for block in content:
                if isinstance(block, dict):
                    t = block.get("text")
                    if isinstance(t, str):
                        text_parts.append(t)
            content_text = "\n".join(text_parts)
        else:
            content_text = str(content)
        parts.append(f"[{role}]\n{content_text}")
    return "\n\n".join(parts)


def _build_prompt(system: Any, messages: Any) -> str:
    """Compose the single positional prompt for ``claude -p``."""
    system_text = _coerce_system_to_text(system)
    user_text = _coerce_messages_to_text(messages)
    if system_text and user_text:
        return f"[SYSTEM]\n{system_text}\n\n{user_text}"
    if system_text:
        return f"[SYSTEM]\n{system_text}"
    return user_text


# ---- shim client ---------------------------------------------------


class _Messages:
    """Mimics ``anthropic.Anthropic().messages``.

    The single ``create(...)`` method invokes ``claude -p`` and
    synthesizes a Message-shaped response.
    """

    def __init__(self, parent: "ClaudePrintAnthropicShimClient") -> None:
        self._parent = parent

    def create(
        self,
        *,
        model: str | None = None,
        max_tokens: int = 8000,  # noqa: ARG002 — accepted for SDK shape parity
        system: Any = "",
        messages: Any = None,
        **_extra: Any,  # absorb future SDK kwargs (e.g., temperature, tools)
    ) -> _ShimMessageResponse:
        chosen_model = model or self._parent.model or DEFAULT_MODEL
        prompt = _build_prompt(system, messages)
        return self._parent._invoke_claude_print(chosen_model, prompt)


class ClaudePrintAnthropicShimClient:
    """Subscription-routed shim presenting an Anthropic-Messages-shaped API.

    Construct with no arguments at production-call boundaries (the
    ``claude`` binary must be on PATH; OAuth state must already be
    written to the keychain via ``claude /login``). Test-mode callers
    do NOT use this class — they pass duck-typed stubs directly via
    the ``anthropic_client=...`` parameter on ``synthesize_objectives`` /
    ``populate_backing_map`` / ``flag_missing_objectives`` / etc.

    The shim is the production-default constructed by
    :func:`build_default_synthesis_client` (cli.py invokes this when
    ``--live`` is set).
    """

    def __init__(
        self,
        *,
        binary_path: str | None = None,
        model: str = DEFAULT_MODEL,
        timeout_seconds: float = 600.0,
    ) -> None:
        # Per v0.2.5.1 AC.V025-1.2 (F-TIMEOUT closure): default raised
        # from 180s to 600s after Eric's real-world run hit the 180s
        # ceiling on rd-automation. Operator can override via the
        # ``--synthesis-timeout`` CLI flag, which threads through
        # :func:`build_default_synthesis_client`.
        resolved = binary_path or shutil.which("claude")
        if resolved is None:
            raise ClaudeBinaryMissingError(
                "claude CLI not found on PATH. Install Claude Code "
                "(https://docs.anthropic.com/claude-code) so the "
                "`claude` binary resolves on this process's PATH. "
                "v0.2.5 corrective C4-pivot: NO Anthropic API key is "
                "required (subscription-only auth via claude -p)."
            )
        self._binary_path: str = resolved
        self.model: str = model
        self._timeout_seconds: float = timeout_seconds
        self._child_env: dict[str, str] = _build_child_env()
        # v0.2.5 corrective C5 — write the empty MCP config tempfile once
        # at construction; every per-call subprocess argv references this
        # path via ``--mcp-config`` so the child claude loads zero MCP
        # servers. Without this, the child inherits the parent session's
        # telegram MCP and SIGTERMs the parent's bot via the loader's
        # PID-stomp dedup branch.
        self._empty_mcp_config_path: str = _write_empty_mcp_config()
        # Lazily-constructed `.messages` accessor mirrors the SDK shape.
        self.messages: _Messages = _Messages(self)

    def _invoke_claude_print(self, model: str, prompt: str) -> _ShimMessageResponse:
        """Run ``claude -p`` synchronously and parse the JSON envelope.

        Sync subprocess (blocking) — synthesis call sites are sync; no
        asyncio loop is required here.

        v0.2.5 corrective C5: argv prepends ``--strict-mcp-config
        --mcp-config <path>`` before ``-p`` so the child subprocess loads
        zero MCP servers. Order matters — these flags MUST precede ``-p``.
        """
        argv = [
            self._binary_path,
            # v0.2.5 corrective C5 — MCP-isolation flags. See module docstring
            # + ``_EMPTY_MCP_CONFIG`` comment for the why.
            "--strict-mcp-config",
            "--mcp-config",
            self._empty_mcp_config_path,
            "-p",
            "--no-session-persistence",
            "--output-format",
            "json",
            "--model",
            model,
            prompt,
        ]
        try:
            proc = subprocess.run(
                argv,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=self._child_env,
                timeout=self._timeout_seconds,
                check=False,
            )
        except FileNotFoundError as exc:
            # Late-resolved binary disappeared mid-session.
            raise ClaudeBinaryMissingError(
                f"claude binary at {self._binary_path} could not be "
                f"executed: {exc}"
            ) from exc
        stdout = proc.stdout.decode("utf-8", errors="replace") if proc.stdout else ""
        stderr = proc.stderr.decode("utf-8", errors="replace") if proc.stderr else ""

        # Detect "Not logged in" before JSON parsing — the marker can
        # appear in raw stdout text or inside a JSON envelope.
        if _response_is_unauthenticated(stdout) or _response_is_unauthenticated(
            stderr
        ):
            raise ClaudePrintShimError(
                "claude -p reports OAuth state absent ('Not logged in'). "
                "Run `claude /login` interactively so the CLI can write "
                "an OAuth token to the system keychain."
            )

        try:
            envelope = json.loads(stdout) if stdout.strip() else {}
        except json.JSONDecodeError as exc:
            raise ClaudePrintShimError(
                f"claude -p returned non-JSON envelope. "
                f"stderr={stderr[:500]!r}; stdout={stdout[:500]!r}"
            ) from exc

        if not isinstance(envelope, dict):
            raise ClaudePrintShimError(
                f"claude -p envelope is not an object: "
                f"{type(envelope).__name__}"
            )

        is_error = bool(envelope.get("is_error", False))
        result_text = envelope.get("result", "") or ""
        if is_error:
            # Surface the result text up so the caller can decide whether
            # to retry (rate-limit) or raise (permanent).
            raise ClaudePrintShimError(
                f"claude -p is_error=true: {result_text[:500]}"
            )

        # Token estimates: claude -p does not always emit ``usage`` token
        # counts in the envelope (depends on CLI version). When absent,
        # estimate from prompt+response char counts (4 chars/token
        # approximation per master plan §6.1 + sub-plan-doc §7).
        usage_payload = envelope.get("usage") or {}
        if isinstance(usage_payload, dict):
            input_tokens = int(usage_payload.get("input_tokens", 0) or 0)
            output_tokens = int(usage_payload.get("output_tokens", 0) or 0)
        else:
            input_tokens = 0
            output_tokens = 0
        if input_tokens == 0:
            input_tokens = max(1, len(prompt) // 4)
        if output_tokens == 0:
            output_tokens = max(1, len(result_text) // 4)

        return _ShimMessageResponse(
            content=[_ShimContentBlock(type="text", text=result_text)],
            usage=_ShimUsage(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
            ),
        )


def build_default_synthesis_client(
    *,
    model: str = DEFAULT_MODEL,
    timeout_seconds: float | None = None,
) -> ClaudePrintAnthropicShimClient:
    """Construct the production-default subscription-routed synthesis client.

    Replaces ``synthesis.build_default_anthropic_client`` (removed by
    v0.2.5 corrective C4-pivot). Raises :class:`ClaudeBinaryMissingError`
    if the ``claude`` CLI is not on PATH.

    No environment variables consulted (no ``ANTHROPIC_API_KEY``); auth
    is the user's Claude Max subscription resolved via OAuth keychain.

    Per v0.2.5.1 AC.V025-1.2 (F-TIMEOUT closure): ``timeout_seconds``
    threads through to the shim ctor. ``None`` (the default) accepts
    the ctor's own default (600s). The CLI flag ``--synthesis-timeout``
    is the user-facing surface.
    """
    if timeout_seconds is None:
        return ClaudePrintAnthropicShimClient(model=model)
    return ClaudePrintAnthropicShimClient(
        model=model, timeout_seconds=timeout_seconds
    )
