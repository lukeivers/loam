"""Telegram-poller isolation for the handsoff-loop launch sites.

Maps to:
  AC.TPI.3 — the argv every §1b handsoff-loop site spawns carries the
             empty-strict-MCP isolation and zero telegram-plugin
             markers.
  AC.TPI.4 — the env every §1b site spawns has TELEGRAM_BOT_TOKEN /
             CLAUDE_PLUGIN_TELEGRAM_BOT_TOKEN / ANTHROPIC_API_KEY
             absent.
  AC.TPI.5 — a regression that re-introduces a telegram-reachable argv
             at any §1b site fails loudly (raises) rather than silently
             shipping a kill-capable invocation.

THE PROVEN MECHANISM, REUSED — NOT RE-IMPLEMENTED (contract §2 / plan
§12 D-1: import).  This module is a thin adapter over the sealed
subloam-driver isolation functions (`build_isolated_claude_argv` /
`build_isolated_env` / `write_empty_mcp_config` / `IsolationConfig`,
sealed under AC.LIPW.5/.6 — empirically verified necessary-AND-
sufficient operator-protection: removing the telegram plugin from the
spawned process's reachable set via an empty strict-MCP config +
scrubbing the bot-token/API-key env stops the competing
``bun server.ts`` that SIGTERMs the operator's single-consumer poller).

The §1b sites spawn ``claude -p <prompt> --model … --permission-mode
bypassPermissions [--output-format json]`` (non-interactive).  The
subloam-driver's ``build_isolated_claude_argv`` produces an
INTERACTIVE-shaped argv (``--dangerously-skip-permissions``, no ``-p``).
Reshaping the §1b argv to that interactive shape would break the §1b
sites' ``-p``/json function and breach the fence (AC.TPI.6).  Per plan
§12 D-2 the §1b argv shape is preserved; only the isolation flags
(``--strict-mcp-config --mcp-config <empty>``) are INJECTED into each
site's existing argv — necessary-AND-sufficient per contract §5 (the
kill vector is the telegram plugin via MCP, not the prompt/permission
flags).  The marker-guard discipline is reused verbatim from the sealed
source so a regression that re-introduces a telegram-reachable argv
raises (AC.TPI.5).

Stdlib-only.  NO Anthropic API key (``feedback_no_anthropic_api_key``)
— the env scrub strips ``ANTHROPIC_API_KEY``; the real ``claude``
binary uses the keychain-stored subscription credential.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

# Import the PROVEN, SEALED isolation functions (contract §2: reuse,
# do not re-implement).  The subloam-driver package is a sibling tool;
# add its src to the path the same way the AC.LIPW.5 seal-test does.
_SUBLOAM_SRC = (
    Path(__file__).resolve().parents[3]
    / "subloam-driver"
    / "src"
)
if str(_SUBLOAM_SRC) not in sys.path:
    sys.path.insert(0, str(_SUBLOAM_SRC))

from subloam_driver import (  # noqa: E402
    IsolationConfig,
    build_isolated_claude_argv,
    build_isolated_env,
)
from subloam_driver.driver import (  # noqa: E402
    _TELEGRAM_PLUGIN_MARKERS,
    write_empty_mcp_config,
)


# The stable scratch root for the §1b empty-MCP config.  NEVER the
# operator's ~/.claude (the IsolationConfig structural guard refuses
# that root — the plugin-cache singleton + bot-token root that carries
# the exact kill vector).
_ISOLATION_ROOT = Path(tempfile.gettempdir()) / "loam-handsoff-isolation"
_EMPTY_MCP_CONFIG = _ISOLATION_ROOT / "empty.mcp.json"


def _config() -> IsolationConfig:
    """The single IsolationConfig the §1b sites reuse.

    ``air_gapped_config`` stays False (the default) so the spawned
    ``claude`` keeps the keychain-stored subscription credential
    reachable — there is NO API key (``feedback_no_anthropic_api_key``);
    a relocated virgin config root would report ``Not logged in``.
    Operator-protection does NOT depend on the config relocation: the
    kill vector is the telegram plugin (excluded from the argv via the
    empty strict-MCP config), not the config root.  ``claude_config_dir``
    is the scratch root (NOT ~/.claude — the structural guard enforces
    this); it is used only to anchor the empty-MCP path + scratch state.
    """
    return IsolationConfig(
        claude_config_dir=_ISOLATION_ROOT / ".claude-home",
        empty_mcp_config_path=_EMPTY_MCP_CONFIG,
        workspace_slug="loam-handsoff-isolation",
    )


def ensure_empty_mcp_config() -> Path:
    """Write/refresh the explicit empty MCP config and return its path.

    The empty-MCP-config file lifecycle the §1b sites need (plan §2 /
    contract §3.2 IN-fence).  Idempotent — ``write_empty_mcp_config``
    rewrites the canonical ``{"mcpServers":{}}``; a non-existent
    ``--mcp-config`` path makes the real ``claude`` reject the
    invocation, so the file MUST exist before any §1b spawn.  Delegates
    to the sealed subloam-driver function (no re-implementation).
    """
    return write_empty_mcp_config(_config().empty_mcp_config_path)


def _assert_telegram_free(argv: list[str]) -> None:
    """AC.TPI.5 — reuse the sealed marker-guard discipline verbatim.

    A regression that re-introduces a telegram-plugin marker into a
    §1b argv raises here rather than silently shipping a kill-capable
    invocation.  Same marker set the sealed
    ``build_isolated_claude_argv`` guards against.
    """
    joined = " ".join(argv)
    for marker in _TELEGRAM_PLUGIN_MARKERS:
        if marker in joined:
            raise ValueError(
                f"handsoff-loop §1b argv carries telegram marker "
                f"{marker!r} — the sole kill vector. Refusing to build "
                f"a kill-capable invocation (AC.TPI.5)."
            )


def isolation_flags() -> list[str]:
    """The empty-strict-MCP isolation flag fragment for a §1b argv.

    Derived from the sealed ``build_isolated_claude_argv`` so the flag
    pair + empty-MCP path are byte-identical to the proven mechanism;
    the interactive-only/prompt/permission portions of the sealed argv
    are NOT borrowed (the §1b sites carry their own ``-p``/json shape —
    plan §12 D-2).  The empty-MCP file is guaranteed to exist.
    """
    ensure_empty_mcp_config()
    proven = build_isolated_claude_argv(_config())
    # proven == [claude, --dangerously-skip-permissions,
    #            --strict-mcp-config, --mcp-config, <empty>, --model, …]
    # Extract ONLY the empty-strict-MCP isolation fragment; the §1b
    # sites keep their own permission/prompt/model flags.
    i = proven.index("--strict-mcp-config")
    flags = proven[i : i + 3]  # --strict-mcp-config --mcp-config <path>
    _assert_telegram_free(flags)
    return list(flags)


def inject_isolation(argv: list[str]) -> list[str]:
    """Inject the empty-strict-MCP isolation into an existing §1b argv.

    The §1b argv's existing shape (positional ``-p`` prompt,
    ``--model``, ``--permission-mode bypassPermissions``,
    ``--output-format json``) is PRESERVED — only the isolation flags
    are inserted (immediately after the ``claude`` binary, before the
    ``-p``).  The result is guarded telegram-free (AC.TPI.5).
    """
    if not argv:
        raise ValueError("empty argv — cannot isolate")
    isolated = [argv[0], *isolation_flags(), *argv[1:]]
    _assert_telegram_free(isolated)
    return isolated


def isolated_env(base_env: dict[str, str] | None = None) -> dict[str, str]:
    """The token/API-key-scrubbed env for a §1b spawn.

    Delegates to the sealed ``build_isolated_env`` (no
    re-implementation): scrubs ``TELEGRAM_BOT_TOKEN`` /
    ``CLAUDE_PLUGIN_TELEGRAM_BOT_TOKEN`` (so the spawned ``claude``
    cannot steal the operator's single-consumer poller slot) and
    ``ANTHROPIC_API_KEY`` (``feedback_no_anthropic_api_key`` —
    subscription-only).  ``air_gapped_config`` is False so
    ``CLAUDE_CONFIG_DIR`` is left unset and subscription auth resolves.
    """
    return build_isolated_env(_config(), base_env=base_env)
