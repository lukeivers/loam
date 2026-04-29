"""Clause-(h) merge-resolver factory.

Exposes :func:`build_merge_resolver` returning a configured
:class:`self_upgrade.merge_resolver.MergeResolver` whose underlying
LLM client routes calls through the ``claude -p --output-format json``
subprocess — the same shape memory-system's ``ClaudePrintLLMClient``
uses to consume the operator's Claude Max OAuth without an
``ANTHROPIC_API_KEY``. The graphiti-typed ``ClaudePrintLLMClient``
itself depends on ``graphiti_core``, which is not on the
self-upgrade venv's path; this module reproduces the subprocess +
JSON-envelope discipline directly so it imports cleanly under the
self-upgrade venv.

CLI wiring:

    pos upgrade <tag> --canonical <path> \\
        --merge-resolver-module upgrade_merge_resolver

``self_upgrade.cli._load_merge_resolver`` calls
``upgrade_merge_resolver.build_merge_resolver()`` and asserts the
return is a :class:`MergeResolver` instance.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from typing import Any

from pydantic import BaseModel, ValidationError

from loam.self_upgrade.merge_resolver import (
    MergeResolver,
    ResolverBudget,
    ResolverFailure,
)


DEFAULT_MODEL = "claude-haiku-4-5"

# Mirror memory-system/src/claude_print_client.py::_ENV_ALLOWED_VARS.
# Drops ANTHROPIC_API_KEY / OPENAI_API_KEY / GEMINI_API_KEY so the
# child cannot fall through to a billed API path. macOS OAuth keychain
# lookup needs USER (amendment #30 finding); HOME for ~/.claude reads.
_ENV_ALLOWED_VARS = ("PATH", "HOME", "USER")

_UNAUTH_MARKERS = ("not logged in", "please run /login")


class _ClaudePrintResolverClient:
    """Duck-typed ``LLMClient`` for ``MergeResolver``.

    Implements the resolver's tight Protocol surface
    (``invoke(prompt, response_model) -> tuple[BaseModel, int]``)
    by spawning ``claude -p --output-format json`` per call and
    parsing the JSON envelope. Failures translate to
    :class:`ResolverFailure` (fail-closed per AC.H.12).
    """

    def __init__(
        self,
        *,
        model: str = DEFAULT_MODEL,
        binary_path: str | None = None,
        timeout_s: float = 120.0,
    ) -> None:
        resolved = binary_path or shutil.which("claude")
        if resolved is None:
            raise ResolverFailure(
                "claude CLI not found on PATH. Install Claude Code "
                "(https://docs.anthropic.com/claude-code) so the "
                "`claude` binary resolves on this process's PATH."
            )
        self._binary_path = resolved
        self._model = model
        self._timeout_s = timeout_s
        self._child_env = self._build_child_env()

    @staticmethod
    def _build_child_env() -> dict[str, str]:
        env: dict[str, str] = {}
        for name in _ENV_ALLOWED_VARS:
            if name in os.environ:
                env[name] = os.environ[name]
        env.setdefault("PATH", "/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin")
        return env

    def _build_prompt(
        self, user_prompt: str, response_model: type[BaseModel]
    ) -> str:
        schema = json.dumps(response_model.model_json_schema())
        return (
            f"{user_prompt}\n\n"
            "[SYSTEM]\nRespond with a single JSON object matching "
            "this schema. Do not include any prose before or after "
            f"the JSON. Schema:\n{schema}"
        )

    def invoke(
        self,
        prompt: str,
        response_model: type[BaseModel],
    ) -> tuple[BaseModel, int]:
        full_prompt = self._build_prompt(prompt, response_model)
        argv = [
            self._binary_path,
            "-p",
            "--no-session-persistence",
            "--output-format",
            "json",
            "--model",
            self._model,
            full_prompt,
        ]
        try:
            completed = subprocess.run(  # noqa: S603 — argv is constructed
                argv,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=self._child_env,
                timeout=self._timeout_s,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise ResolverFailure(
                f"claude -p timed out after {self._timeout_s}s"
            ) from exc
        except OSError as exc:
            raise ResolverFailure(
                f"claude -p subprocess spawn failed: {exc}"
            ) from exc

        stdout = completed.stdout.decode("utf-8", errors="replace")
        stderr = completed.stderr.decode("utf-8", errors="replace")

        if not stdout.strip():
            raise ResolverFailure(
                f"claude -p returned empty stdout. "
                f"rc={completed.returncode}, stderr={stderr[:500]!r}"
            )
        try:
            envelope = json.loads(stdout)
        except json.JSONDecodeError as exc:
            raise ResolverFailure(
                f"claude -p returned non-JSON envelope. "
                f"stderr={stderr[:500]!r}"
            ) from exc

        if not isinstance(envelope, dict):
            raise ResolverFailure(
                f"claude -p envelope is not an object: "
                f"{type(envelope).__name__}"
            )

        result_text: str = envelope.get("result", "") or ""
        is_error: bool = bool(envelope.get("is_error", False))

        haystack = result_text.lower()
        if any(marker in haystack for marker in _UNAUTH_MARKERS):
            raise ResolverFailure(
                "claude -p returned 'Not logged in'. "
                "Run `claude /login` interactively to write OAuth state."
            )

        if is_error:
            raise ResolverFailure(
                f"claude -p is_error=true: {result_text[:500]}"
            )

        # Pull the first JSON object out of result_text and validate.
        start = result_text.find("{")
        end = result_text.rfind("}") + 1
        if start < 0 or end <= start:
            raise ResolverFailure(
                f"no JSON object found in result text: {result_text[:200]!r}"
            )
        try:
            parsed = json.loads(result_text[start:end])
        except json.JSONDecodeError as exc:
            raise ResolverFailure(
                f"result JSON failed to parse: {result_text[:200]!r}"
            ) from exc

        try:
            verdict = response_model(**parsed)
        except ValidationError as exc:
            raise ResolverFailure(
                f"result failed {response_model.__name__} validation: {exc}"
            ) from exc

        # Token-cost estimate. claude -p envelope exposes per-call usage
        # under "usage" or top-level token fields; in practice
        # total_cost_usd is 0.0 on Max subscription. Use input+output
        # token counts when the envelope surfaces them; otherwise
        # estimate from prompt + response length so cumulative-budget
        # bookkeeping still tracks.
        tokens = _extract_token_cost(envelope, full_prompt, result_text)
        return verdict, tokens


def _extract_token_cost(
    envelope: dict[str, Any], prompt: str, result_text: str
) -> int:
    """Best-effort token accounting from ``claude -p`` JSON envelope.

    Tries ``usage.input_tokens + usage.output_tokens`` first, then
    falls back to a chars-per-token approximation (4 chars/token) so
    the resolver's cumulative-budget bookkeeping still moves forward
    even when the envelope omits usage.
    """
    usage = envelope.get("usage")
    if isinstance(usage, dict):
        input_t = usage.get("input_tokens")
        output_t = usage.get("output_tokens")
        if isinstance(input_t, int) and isinstance(output_t, int):
            return int(input_t + output_t)
    return max(1, (len(prompt) + len(result_text)) // 4)


def build_merge_resolver() -> MergeResolver:
    """Factory invoked by ``pos upgrade --merge-resolver-module``.

    Returns a :class:`MergeResolver` whose LLM client spawns
    ``claude -p`` per call. Budgets default to BB D-1 locks
    (5_000 / 100_000); future amendments may expose tunables via
    ``~/.loam/upgrade-config.yaml``.
    """
    client = _ClaudePrintResolverClient()
    return MergeResolver(client, ResolverBudget())
