"""Subscription-routed LLM client for graphiti (amendment #8).

All graphiti LLM calls route through ``claude -p`` subprocess invocations
that consume the user's Claude Max subscription via OAuth — **no**
``ANTHROPIC_API_KEY`` environment variable is required or consulted.
This is the sole path for graphiti LLM work after amendment #8's
option-1 re-scope (GLiNER2 entity-extraction fast-path dropped; see
``docs/rebuild/components/memory-system-subscription-routed-llm/proposal.md``
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
import logging
import os
import shutil
import typing
from dataclasses import dataclass, field
from typing import Any

from graphiti_core.llm_client.client import LLMClient
from graphiti_core.llm_client.config import DEFAULT_MAX_TOKENS, LLMConfig, ModelSize
from graphiti_core.llm_client.errors import RateLimitError
from graphiti_core.prompts.models import Message
from pydantic import BaseModel, ValidationError


logger = logging.getLogger(__name__)


DEFAULT_MODEL = "claude-haiku-4-5"
DEFAULT_SMALL_MODEL = "claude-haiku-4-5"

# Explicit env allow-list for the child subprocess. Everything else
# (notably ``ANTHROPIC_API_KEY`` / ``OPENAI_API_KEY`` / ``GEMINI_API_KEY``)
# is dropped so the child cannot fall through to a billed API path.
_ENV_ALLOWED_VARS = (
    "PATH",
    "HOME",
    "USER",
    "LOGNAME",
    "SHELL",
    "LANG",
    "LC_ALL",
    "LC_CTYPE",
    "TERM",
    "TMPDIR",
    "XDG_CONFIG_HOME",
    "XDG_DATA_HOME",
    "XDG_CACHE_HOME",
)

# Markers (substring match, case-insensitive) that the probe subprocess
# emits when OAuth is absent. Kept as a tuple so additional phrasings
# surface over time can be appended without touching call sites.
_UNAUTH_MARKERS = (
    "not logged in",
    "please run /login",
)

# Markers that indicate the model hit a subscription rate-limit.
_RATE_LIMIT_MARKERS = (
    "rate limit",
    "rate-limit",
    "rate_limit",
    "429",
    "too many requests",
    "usage limit",
)


# ---- errors ---------------------------------------------------------


class ClaudePrintClientError(Exception):
    """Base for all ClaudePrintLLMClient fail-closed conditions.

    ``code`` and ``kind`` together identify the error: ``code`` slots
    the failure into memory-system's reserved numeric block, ``kind``
    is a stable machine-readable label for structured logs / exception
    payload inspection.
    """

    code: int = -32099
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
    """

    total_usd: float = 0.0
    call_count: int = 0
    per_call_usd: list[float] = field(default_factory=list)

    def record(self, cost_usd: float) -> None:
        self.total_usd += cost_usd
        self.call_count += 1
        self.per_call_usd.append(cost_usd)


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
    binary_path: str, env: dict[str, str]
) -> None:
    """Invoke ``claude -p`` with a trivial prompt to verify OAuth state.

    If the probe emits the "Not logged in" marker, raise
    ``ClaudeUnauthenticatedError``. Any other non-empty response means
    OAuth resolved (even if the model produced unusable output — the
    factory is checking auth, not response quality).
    """
    argv = [
        binary_path,
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

    # The "Not logged in" signal can appear in either stream depending
    # on CLI version; check both.
    if _response_is_unauthenticated(stdout) or _response_is_unauthenticated(stderr):
        raise ClaudeUnauthenticatedError(
            "claude CLI is installed but not authenticated (OAuth state "
            "absent). Run `claude /login` interactively so the CLI can "
            "write an OAuth token to the system keychain."
        )

    # Some probe responses are also wrapped in the JSON envelope — parse
    # defensively so a "Not logged in" result surfacing as
    # {"result": "Not logged in..."} still halts.
    try:
        payload = json.loads(stdout)
        if isinstance(payload, dict):
            text = payload.get("result", "") or ""
            if _response_is_unauthenticated(text):
                raise ClaudeUnauthenticatedError(
                    "claude CLI emitted 'Not logged in' in probe response. "
                    "Run `claude /login`."
                )
    except json.JSONDecodeError:
        # Non-JSON probe output is fine as long as no unauth marker fired.
        pass


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
                small_model=DEFAULT_SMALL_MODEL,
            )
        if config.model is None:
            config.model = DEFAULT_MODEL
        if config.small_model is None:
            config.small_model = DEFAULT_SMALL_MODEL

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
        self.cost_tracker = SubscriptionCostTracker()

        # AC5: probe OAuth state before returning a "ready" client. The
        # probe is synchronous-from-the-caller's-point-of-view; we run
        # it via asyncio.run in a fresh loop so construction remains a
        # plain synchronous call-path. ``skip_auth_probe`` is the seam
        # tests use when the probe itself is being asserted about via
        # mocked subprocess.
        if not skip_auth_probe:
            _run_sync(
                _probe_claude_authenticated(self._binary_path, self._child_env)
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
        """
        return [
            self._binary_path,
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
    trailing commentary. Mirror ``AnthropicClient._extract_json_from_text``.
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
    """Execute a coroutine from a synchronous context.

    Factory construction is synchronous (``make_graphiti`` is async but
    the client class itself is instantiated as part of its setup; we
    call the probe from ``__init__``). When no event loop is running,
    ``asyncio.run`` is fine. When a loop IS running (e.g. inside a
    pytest-asyncio test that instantiates the client mid-coroutine), we
    fall back to creating a nested loop in a thread so we don't
    deadlock on the already-running loop.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop is None:
        return asyncio.run(coro)  # type: ignore[arg-type]

    # Running-loop path: run the coro in a worker thread with its own
    # fresh loop so we don't re-enter the caller's loop.
    import concurrent.futures

    def _runner() -> Any:
        return asyncio.run(coro)  # type: ignore[arg-type]

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(_runner)
        return future.result()
