"""Subscription-routed LLM client for graphiti (amendment #8).

All graphiti LLM calls route through ``claude -p`` subprocess invocations
that consume the user's Claude Max subscription via OAuth — **no**
``ANTHROPIC_API_KEY`` environment variable is required or consulted.
This is the sole path for graphiti LLM work after amendment #8's
option-1 re-scope (GLiNER2 entity-extraction fast-path dropped; see
``docs/archive/component-research/memory-system-subscription-routed-llm/proposal.md``
§0 for the re-scope rationale).

Error codes. Memory-system's historical claim inside the
hands-off-lifecycle block (``-32095`` staging-overflow,
``-32096`` drain-poison) only covered install-phase + staging
failures. This amendment claims a fresh memory-system runtime
block at ``-32110..-32119`` — it sits after telegram-interface's
``-32100..-32109`` and is the first memory-system-owned block
outside the hands-off-lifecycle carve-out. Existing codes on
-32095/-32096 stay with their original owners (staging, drain);
no overloading.

  * ``-32110`` ``claude-binary-missing`` — ``shutil.which("claude")``
    returned ``None`` at factory construction.
  * ``-32111`` ``claude-unauthenticated`` — the probe subprocess
    emitted the "Not logged in" signal the CLI produces when OAuth is
    absent.
  * ``-32112`` ``claude-print-response-malformed`` — per-call parse
    failure from a malformed ``claude -p --output-format json``
    payload. Non-fatal; graphiti's retry machinery catches and
    backs off.
  * ``-32119`` ``claude-print-client-internal`` — base-class sentinel
    (amendment #11 audit-closure §F13 moved this here from ``-32099``
    so it no longer collides with hands-off-lifecycle's own
    ``hands_off_lifecycle_internal`` catch-all).

Subprocess shape (empirical, verified 2026-04-22):

    claude -p --no-session-persistence --output-format json \\
        --model claude-haiku-4-5 "<prompt>"

``--bare`` is **not** passed; ``--bare`` bypasses OAuth keychain reads
and requires ``ANTHROPIC_API_KEY`` — the exact thing this client
avoids. The child subprocess's environment is explicitly constructed
(PATH, HOME, plus a short benign allow-list) so that
``ANTHROPIC_API_KEY`` and ``OPENAI_API_KEY`` cannot leak from the parent
into the child and accidentally route through the Console rather than
the Max subscription.

Response JSON shape from ``claude -p --output-format json``::

    {"type": "result",
     "result": "<model text, JSON-schema-matching for structured outputs>",
     "total_cost_usd": <float, 0.0 when on Max subscription>,
     "is_error": <bool>, ...}

``total_cost_usd`` is surfaced as observability (inference §5 #4) even
though the actual billing cost on Max is 0 — the field still represents
Anthropic's equivalent-cost estimate for subscription usage budgeting.
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import tempfile
import typing
from dataclasses import dataclass
from typing import Any

from graphiti_core.llm_client.client import LLMClient
from graphiti_core.llm_client.config import DEFAULT_MAX_TOKENS, LLMConfig, ModelSize
from graphiti_core.llm_client.errors import RateLimitError
from graphiti_core.prompts.models import Message
from pydantic import BaseModel, ValidationError


DEFAULT_MODEL = "claude-haiku-4-5"

# Explicit env allow-list for the child subprocess. Only the minimum
# vars tests actually verify. Anything else (notably
# ``ANTHROPIC_API_KEY`` / ``OPENAI_API_KEY`` / ``GEMINI_API_KEY``) is
# dropped so the child cannot fall through to a billed API path. If a
# runtime failure later shows `claude -p` needs another var, add it
# together with a concrete AC extension naming the failure observed
# (amendment #11 audit-closure §F5 ruling).
#
# ``USER`` admitted by amendment #30 (memory-system-env-scrubber-user):
# macOS launchd's gui-domain session injects USER into agent-spawned
# processes, and ``claude -p``'s OAuth keychain lookup requires USER
# to match the real login name. Without USER in the child env the
# CLI emits "Not logged in · Please run /login" even on an
# authenticated host. Research §Q1 empirical bisection
# (docs/plans/research/memory-system-env-scrubber-research.md)
# pins the minimum allowlist at PATH + USER; HOME retains membership
# for future ``~/.claude/*`` config reads per §Q3 row 2. Every other
# candidate surveyed (LOGNAME, TMPDIR, SHELL, LANG,
# __CF_USER_TEXT_ENCODING, …) is ruled OUT with evidence and must
# stay OUT under the §2.5 code-for-cases-no-objective-names rule.
_ENV_ALLOWED_VARS = (
    "PATH",
    "HOME",
    "USER",
)

# Markers (substring match, case-insensitive) that the probe subprocess
# emits when OAuth is absent.
_UNAUTH_MARKERS = (
    "not logged in",
    "please run /login",
)

# v0.2.5 corrective C5 — MCP-isolation payload for the child ``claude -p``
# subprocess. Mirrors ``framework/workspace-sync/src/loam/workspace_sync/_resolver_client.py``
# (AC.WSα.8, verified 2026-04-27).
#
# Without this isolation, the child claude inherits the parent session's MCP
# server config — including the telegram MCP. The telegram loader at
# ``~/.claude/plugins/cache/claude-plugins-official/telegram/0.0.6/server.ts:60-78``
# has PID-stomp dedup logic: any new instance SIGTERMs the prior PID-file
# holder. Result without isolation: every memory-system ingest that forks
# ``claude -p`` kills the parent session's telegram bot.
#
# Owner ruling 2026-05-05 (Telegram 10196): subprocess invocations must launch
# without telegram. We use ``--strict-mcp-config --mcp-config <empty config>``
# rather than the alternative ``CLAUDE_PERSONA`` env-var skip mechanism (which
# is telegram-specific) because the flag-based approach disables EVERY MCP
# server in the child — protecting telegram and any other MCP the user adds.
# See plan-doc §14 D-1 method-decision register for the full rationale.
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
        suffix="-memory-system-empty-mcp.json",
        delete=False,
        encoding="utf-8",
    )
    try:
        json.dump(_EMPTY_MCP_CONFIG, fd)
        fd.flush()
    finally:
        fd.close()
    return fd.name

# Markers that indicate the model hit a subscription rate-limit.
# Only the two substrings AC6's live tests exercise (amendment #11
# audit-closure §F8 ruling). A new real-world phrasing surfaces with
# an AC extension + a new marker together.
_RATE_LIMIT_MARKERS = (
    "rate limit",
    "usage limit",
)


# ---- errors ---------------------------------------------------------


class ClaudePrintClientError(Exception):
    """Base for all ClaudePrintLLMClient fail-closed conditions.

    ``code`` and ``kind`` together identify the error: ``code`` slots
    the failure into memory-system's reserved numeric block, ``kind``
    is a stable machine-readable label for structured logs / exception
    payload inspection.

    The base-class ``.code`` sentinel sits at ``-32119`` — the last
    slot of memory-system's own ``-32110..-32119`` runtime block. The
    original draft used ``-32099`` which collided with
    ``hands_off_lifecycle_internal`` (the hands-off-lifecycle README's
    catch-all claim for that component's block). Amendment #11
    audit-closure §F13 moved the sentinel into this component's own
    block so the collision is structurally impossible.
    """

    code: int = -32119
    kind: str = "claude-print-client-internal"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ClaudeBinaryMissingError(ClaudePrintClientError):
    """``claude`` CLI not found on PATH at factory construction (AC4).

    Remediation: install Claude Code
    (https://docs.anthropic.com/claude-code) so the ``claude`` binary
    resolves on the caller's PATH.
    """

    code: int = -32110
    kind: str = "claude-binary-missing"


class ClaudeUnauthenticatedError(ClaudePrintClientError):
    """``claude`` CLI is on PATH but OAuth state is absent (AC5).

    The probe subprocess emitted the "Not logged in" signal.
    Remediation: run ``claude /login`` interactively so the CLI can
    write an OAuth token to the system keychain.
    """

    code: int = -32111
    kind: str = "claude-unauthenticated"


class ClaudePrintResponseError(ClaudePrintClientError):
    """The subprocess returned a response that could not be parsed.

    Non-fatal at construction; raised per-call from
    ``_generate_response``. Graphiti's retry loop catches this via
    ``is_server_or_retry_error``-sibling paths.
    """

    code: int = -32112
    kind: str = "claude-print-response-malformed"


# ---- cost tracker ---------------------------------------------------


@dataclass
class SubscriptionCostTracker:
    """Accumulates ``total_cost_usd`` across calls for observability.

    Max-subscription calls typically report 0.0 here, but the field is
    Anthropic's equivalent-cost estimate useful for subscription-usage
    budgeting even when no actual billing occurs.

    ``MemoryAPI.ingest`` reads ``total_usd`` before and after each
    ingest and emits the delta as the ``claude.equivalent_cost_usd``
    span attribute (amendment #11 audit-closure §F3 ruling — the
    landed implementation of proposal §5 #4 observability ruling).
    """

    total_usd: float = 0.0
    call_count: int = 0

    def record(self, cost_usd: float) -> None:
        self.total_usd += cost_usd
        self.call_count += 1


# ---- probe: called at construction to detect AC4 / AC5 -------------


def _build_child_env(parent_env: dict[str, str] | None = None) -> dict[str, str]:
    """Construct the scrubbed env dict passed to every child subprocess.

    Drops ``ANTHROPIC_API_KEY`` / ``OPENAI_API_KEY`` / ``GEMINI_API_KEY``
    even when set in the parent, so the subprocess cannot fall through
    to a billed API path. ``claude -p`` without ``--bare`` reads
    OAuth from the macOS keychain; no env var is needed for auth.
    """
    if parent_env is None:
        parent_env = os.environ  # type: ignore[assignment]
    env: dict[str, str] = {}
    for name in _ENV_ALLOWED_VARS:
        if name in parent_env:
            env[name] = parent_env[name]
    # PATH must always be set for `claude` resolution in the child.
    env.setdefault("PATH", "/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin")
    return env


def _response_is_rate_limit(result_text: str, is_error: bool) -> bool:
    """Heuristic detection (AC6).

    Graphiti's retry machinery catches ``RateLimitError`` and retries
    with exponential backoff. Over-triggering this path costs a retry;
    under-triggering surfaces as a generic error and bypasses retry.
    The lower-cost failure mode is over-triggering, so err on the
    side of flagging rate limits.
    """
    if not is_error:
        return False
    haystack = (result_text or "").lower()
    return any(marker in haystack for marker in _RATE_LIMIT_MARKERS)


def _response_is_unauthenticated(result_text: str) -> bool:
    """Detect the "Not logged in · Please run /login" signal (AC5)."""
    haystack = (result_text or "").lower()
    return any(marker in haystack for marker in _UNAUTH_MARKERS)


async def _probe_claude_authenticated(
    binary_path: str, env: dict[str, str], empty_mcp_config_path: str
) -> None:
    """Invoke ``claude -p`` with a trivial prompt to verify OAuth state.

    If the probe emits the "Not logged in" marker, raise
    ``ClaudeUnauthenticatedError``. Any other non-empty response means
    OAuth resolved (even if the model produced unusable output — the
    factory is checking auth, not response quality).

    ``empty_mcp_config_path`` is the absolute path of the tempfile
    written by :func:`_write_empty_mcp_config`; the probe argv carries
    ``--strict-mcp-config --mcp-config <path>`` before ``-p`` so the
    probe subprocess loads zero MCP servers (v0.2.5 corrective C5).
    """
    argv = [
        binary_path,
        # v0.2.5 corrective C5 — MCP-isolation flags. Order matters:
        # MUST precede ``-p`` so they bind to the print-mode invocation.
        "--strict-mcp-config",
        "--mcp-config",
        empty_mcp_config_path,
        "-p",
        "--no-session-persistence",
        "--output-format",
        "json",
        "--model",
        DEFAULT_MODEL,
        "probe",
    ]
    proc = await asyncio.create_subprocess_exec(
        *argv,
        stdin=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env,
    )
    stdout_bytes, stderr_bytes = await proc.communicate()
    stdout = stdout_bytes.decode("utf-8", errors="replace") if stdout_bytes else ""
    stderr = stderr_bytes.decode("utf-8", errors="replace") if stderr_bytes else ""

    # Substring match works uniformly whether stdout is raw CLI text
    # ("Not logged in · Please run /login") or an envelope-wrapped
    # JSON body ({"result":"Not logged in..."}) — both cases contain
    # the marker substring. The earlier defensive JSON re-parse +
    # ``except json.JSONDecodeError: pass`` branch (amendment #11
    # audit-closure §F11) was a silent-except violating §8 rule 8
    # and redundant with the substring check; removed.
    if _response_is_unauthenticated(stdout) or _response_is_unauthenticated(stderr):
        raise ClaudeUnauthenticatedError(
            "claude CLI is installed but not authenticated (OAuth state "
            "absent). Run `claude /login` interactively so the CLI can "
            "write an OAuth token to the system keychain."
        )


# ---- client ---------------------------------------------------------


class ClaudePrintLLMClient(LLMClient):
    """LLM client that routes every graphiti call through ``claude -p``.

    Fails closed at construction if the ``claude`` binary is missing
    (AC4) or if OAuth is absent (AC5). Once constructed, every
    ``_generate_response`` call spawns a fresh subprocess with a
    scrubbed env (AC2), parses the JSON envelope, validates the
    ``.result`` against ``response_model`` if provided (AC3), and
    translates rate-limit signals into graphiti's ``RateLimitError``
    (AC6).
    """

    def __init__(
        self,
        config: LLMConfig | None = None,
        cache: bool = False,
        *,
        binary_path: str | None = None,
        skip_auth_probe: bool = False,
    ) -> None:
        if config is None:
            config = LLMConfig(
                model=DEFAULT_MODEL,
                small_model=DEFAULT_MODEL,
            )
        if config.model is None:
            config.model = DEFAULT_MODEL
        if config.small_model is None:
            config.small_model = DEFAULT_MODEL

        super().__init__(config, cache)

        # AC4: structural refusal before any orchestrator import / spawn.
        resolved = binary_path or shutil.which("claude")
        if resolved is None:
            raise ClaudeBinaryMissingError(
                "claude CLI not found on PATH. Install Claude Code "
                "(https://docs.anthropic.com/claude-code) so the "
                "`claude` binary resolves on this process's PATH."
            )
        self._binary_path: str = resolved
        self._child_env: dict[str, str] = _build_child_env()
        # v0.2.5 corrective C5 — write the empty MCP config tempfile once
        # at construction; every probe + per-call subprocess argv references
        # this path via ``--mcp-config`` so the child claude loads zero MCP
        # servers. Without this, the child inherits the parent session's
        # telegram MCP and SIGTERMs the parent's bot via the loader's
        # PID-stomp dedup branch.
        self._empty_mcp_config_path: str = _write_empty_mcp_config()
        self.cost_tracker = SubscriptionCostTracker()

        # AC5: probe OAuth state before returning a "ready" client.
        # ``skip_auth_probe=True`` defers the probe to the async
        # ``probe_authenticated()`` method — that seam is how
        # ``make_claude_print_client`` (async) calls the probe without
        # needing a sync-over-async bridge. Sync-context callers (AC4 /
        # AC5 tests, ad-hoc instantiations) get the probe inline via
        # ``asyncio.run`` — no running loop, no thread-pool fallback.
        # Amendment #11 audit-closure §F2 removed the running-loop
        # branch; callers in async contexts must use
        # ``skip_auth_probe=True`` + ``await client.probe_authenticated()``.
        if not skip_auth_probe:
            _run_sync(
                _probe_claude_authenticated(
                    self._binary_path,
                    self._child_env,
                    self._empty_mcp_config_path,
                )
            )

    async def probe_authenticated(self) -> None:
        """Async-context variant of the construction-time OAuth probe.

        Call this from an async factory (e.g. ``make_claude_print_client``)
        after constructing the client with ``skip_auth_probe=True``.
        Semantically equivalent to the probe that runs inside sync
        ``__init__`` — raises ``ClaudeUnauthenticatedError`` on the
        "Not logged in" signal, returns ``None`` on success.
        """
        await _probe_claude_authenticated(
            self._binary_path, self._child_env, self._empty_mcp_config_path
        )

    # ---- LLMClient API ---------------------------------------------

    async def _generate_response(
        self,
        messages: list[Message],
        response_model: type[BaseModel] | None = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        model_size: ModelSize = ModelSize.medium,
    ) -> dict[str, Any]:
        model = self.small_model if model_size == ModelSize.small else self.model
        if model is None:
            model = DEFAULT_MODEL

        prompt = self._build_prompt(messages, response_model)
        argv = self._build_argv(model, prompt)

        proc = await asyncio.create_subprocess_exec(
            *argv,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=self._child_env,
        )
        stdout_bytes, stderr_bytes = await proc.communicate()
        stdout = stdout_bytes.decode("utf-8", errors="replace") if stdout_bytes else ""
        stderr = stderr_bytes.decode("utf-8", errors="replace") if stderr_bytes else ""

        return self._parse_response(stdout, stderr, response_model)

    # ---- helpers ---------------------------------------------------

    def _build_prompt(
        self,
        messages: list[Message],
        response_model: type[BaseModel] | None,
    ) -> str:
        """Flatten graphiti ``Message`` list into a single ``claude -p`` prompt.

        Graphiti sends [system, user, ...user] messages. ``claude -p``
        takes a single positional prompt; we build a labelled
        concatenation preserving role structure so the model can
        distinguish system from user turns.
        """
        parts: list[str] = []
        for m in messages:
            role = (m.role or "user").upper()
            parts.append(f"[{role}]\n{m.content}")
        if response_model is not None:
            schema = json.dumps(response_model.model_json_schema())
            parts.append(
                "[SYSTEM]\nRespond with a single JSON object matching "
                f"this schema. Do not include any prose before or after "
                f"the JSON. Schema:\n{schema}"
            )
        return "\n\n".join(parts)

    def _build_argv(self, model: str, prompt: str) -> list[str]:
        """Construct the argv passed to ``asyncio.create_subprocess_exec``.

        ``--bare`` is explicitly NOT included — the whole point of this
        client is to route through OAuth, which ``--bare`` bypasses.

        v0.2.5 corrective C5: prepends ``--strict-mcp-config --mcp-config <path>``
        before ``-p`` so the child subprocess loads zero MCP servers. Order
        matters — these flags MUST precede ``-p``.
        """
        return [
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

    def _parse_response(
        self,
        stdout: str,
        stderr: str,
        response_model: type[BaseModel] | None,
    ) -> dict[str, Any]:
        """Extract the result from claude -p --output-format json output.

        Envelope shape::

            {"type":"result","result":"<text>","total_cost_usd":<float>,
             "is_error":<bool>, ...}

        - AC5 (late-detected): if ``result`` contains "Not logged in" we
          surface ClaudeUnauthenticatedError.
        - AC6: if ``is_error`` + a rate-limit marker fires, translate
          to ``graphiti_core.llm_client.errors.RateLimitError``.
        - AC3: validate ``.result`` as JSON against ``response_model``.
        """
        try:
            envelope = json.loads(stdout) if stdout.strip() else {}
        except json.JSONDecodeError as exc:
            raise ClaudePrintResponseError(
                f"claude -p returned non-JSON envelope. stderr={stderr[:500]!r}"
            ) from exc

        if not isinstance(envelope, dict):
            raise ClaudePrintResponseError(
                f"claude -p envelope is not an object: {type(envelope).__name__}"
            )

        result_text: str = envelope.get("result", "") or ""
        is_error: bool = bool(envelope.get("is_error", False))
        cost_usd: float = float(envelope.get("total_cost_usd", 0.0) or 0.0)
        self.cost_tracker.record(cost_usd)

        if _response_is_rate_limit(result_text, is_error):
            raise RateLimitError(
                f"claude -p subscription rate limit reached: {result_text[:200]}"
            )

        if _response_is_unauthenticated(result_text):
            raise ClaudeUnauthenticatedError(
                "claude -p returned 'Not logged in' during a live call. "
                "Run `claude /login`."
            )

        if is_error:
            raise ClaudePrintResponseError(
                f"claude -p is_error=true: {result_text[:500]}"
            )

        if response_model is None:
            # No schema constraint — return raw envelope result wrapped
            # as a dict so graphiti's downstream type expectations hold.
            return {"result": result_text}

        # AC3: extract first JSON object from result_text and validate.
        parsed = _extract_json_object(result_text)
        try:
            response_model(**parsed)
        except ValidationError as exc:
            raise ClaudePrintResponseError(
                f"claude -p result failed {response_model.__name__} "
                f"validation: {exc}"
            ) from exc
        return parsed


# ---- small shared utilities ---------------------------------------


def _extract_json_object(text: str) -> dict[str, Any]:
    """Pull the first ``{...}`` JSON object out of a text blob.

    Graphiti's prompt instructs the model to return bare JSON, but
    real-world responses sometimes prefix with markdown fencing or
    trailing commentary.
    """
    try:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start < 0 or end <= start:
            raise ClaudePrintResponseError(
                f"no JSON object found in result text: {text[:200]!r}"
            )
        return json.loads(text[start:end])
    except json.JSONDecodeError as exc:
        raise ClaudePrintResponseError(
            f"result JSON failed to parse: {text[:200]!r}"
        ) from exc


def _run_sync(coro: typing.Awaitable[Any]) -> Any:
    """Execute a coroutine from a sync context (no running loop).

    Used by ``ClaudePrintLLMClient.__init__`` when the caller is in a
    plain sync context (AC4/AC5 tests, ad-hoc instantiations). If an
    event loop is already running in this thread, the caller is in
    async context and must use ``skip_auth_probe=True`` +
    ``await client.probe_authenticated()`` instead — amendment #11
    audit-closure §F2 removed the threadpool-running-loop fallback
    (no AC named that pathway; §2.5 violation).
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)  # type: ignore[arg-type]

    raise RuntimeError(
        "ClaudePrintLLMClient construction invoked from a running "
        "event loop with skip_auth_probe=False. Pass "
        "skip_auth_probe=True and `await client.probe_authenticated()` "
        "from async context."
    )
