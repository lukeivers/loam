"""Workspace-sync merge-resolver factory.

Re-vendored from ``tools/upgrade-merge-resolver/src/
upgrade_merge_resolver/__init__.py`` so workspace-sync owns its own
copy of the ``claude -p`` subprocess wrap (per workspace-sync plan
Hard Constraint #11: salvage-by-COPY-not-import). The original
``upgrade_merge_resolver`` package remains in place under
``tools/`` for the canonical-side ``pos upgrade --merge-resolver-
module upgrade_merge_resolver`` flow; workspace-sync's copy below
imports only from ``workspace_sync.merge_resolver`` so there is no
A↔B runtime coupling.

Exposes :func:`build_merge_resolver` returning a configured
:class:`workspace_sync.merge_resolver.MergeResolver` whose underlying
LLM client routes calls through the ``claude -p --output-format json``
subprocess — the same shape memory-system's ``ClaudePrintLLMClient``
uses to consume the operator's Claude Max OAuth without an
``ANTHROPIC_API_KEY``.

CLI wiring:

    pos-sync --canonical <path> --ref <commit-or-tag> \\
        --merge-resolver-module workspace_sync._resolver_client

This is the default factory; an operator can override via the
``--merge-resolver-module`` flag to plug in a stub or alternative
adapter for tests.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from typing import Any

from pydantic import BaseModel, ValidationError

from .merge_resolver import (
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

# Empty MCP config payload used by α.3 MCP-isolation (AC.WSα.8). The
# resolver subprocess invokes ``claude -p`` with
# ``--strict-mcp-config --mcp-config <path>`` referencing a tempfile
# whose contents are exactly this object. Strict-MCP-config tells
# Claude to ignore every other MCP-config source (project, user,
# environment); pointing it at an empty servers map disables every
# MCP server in the subprocess. Prevents bun-process contention with
# the parent session's MCP servers (e.g. the user's telegram MCP,
# memory-graphiti MCP). Verified empirically 2026-04-27 to work
# under Claude Max OAuth without ``ANTHROPIC_API_KEY``.
_EMPTY_MCP_CONFIG: dict[str, dict[str, Any]] = {"mcpServers": {}}


class _ClaudePrintResolverClient:
    """Duck-typed ``LLMClient`` for ``MergeResolver``.

    Implements the resolver's tight Protocol surface
    (``invoke(prompt, response_model) -> tuple[BaseModel, int]``)
    by spawning ``claude -p --output-format json`` per call and
    parsing the JSON envelope. Failures translate to
    :class:`ResolverFailure` (fail-closed per AC.WS.12).

    α.3 MCP-isolation (AC.WSα.8). At init time the client writes an
    empty MCP config (``{"mcpServers": {}}``) to a process-cached
    tempfile path; every ``invoke()`` call appends
    ``--strict-mcp-config --mcp-config <path>`` to argv so the
    subprocess loads no MCP servers (preserving the parent session's
    bun MCP processes from contention). The OAuth/Claude-Max path is
    preserved — no env-scrubber changes; no ``ANTHROPIC_API_KEY``
    requirement.
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
        self._empty_mcp_config_path = self._write_empty_mcp_config()

    @staticmethod
    def _write_empty_mcp_config() -> str:
        """Write the empty MCP config to a process-cached tempfile.

        Returns the absolute path. The file is left in place at
        process exit (best-effort cleanup); it is small (~25 bytes)
        and lives in ``$TMPDIR`` / ``/tmp``. The tempfile is
        ``delete=False`` because the subprocess inherits the path
        and reads it after the writing handle is closed.
        """
        fd = tempfile.NamedTemporaryFile(
            mode="w",
            suffix="-pos-sync-empty-mcp.json",
            delete=False,
            encoding="utf-8",
        )
        try:
            json.dump(_EMPTY_MCP_CONFIG, fd)
            fd.flush()
        finally:
            fd.close()
        return fd.name

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
            # α.3 MCP-isolation (AC.WSα.8). Order matters: these
            # flags must precede ``-p`` so they bind to the print-
            # mode invocation. ``--strict-mcp-config`` plus an
            # empty ``--mcp-config`` makes Claude ignore every
            # other MCP source; the subprocess loads zero servers.
            "--strict-mcp-config",
            "--mcp-config",
            self._empty_mcp_config_path,
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


def build_merge_resolver(
    *,
    budget: ResolverBudget | None = None,
) -> MergeResolver:
    """Factory invoked by ``pos-sync --merge-resolver-module``.

    Returns a :class:`MergeResolver` whose LLM client spawns
    ``claude -p`` per call. Budgets default to BB D-1 locks
    (5_000 / 100_000); workspace-tunable via
    ``<workspace>/.pos/sync-config.yaml`` or
    ``~/.loam/sync-config.yaml`` (β.1 wires the precedence chain
    via ``cli.py``; locked plan §11 D-2).
    """
    client = _ClaudePrintResolverClient()
    return MergeResolver(client, budget or ResolverBudget())
