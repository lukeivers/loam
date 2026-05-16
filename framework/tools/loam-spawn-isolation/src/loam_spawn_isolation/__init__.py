# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.  See the License for the specific language governing
# permissions and limitations under the License.

"""loam-spawn-isolation — the ONE shared, importable, mandated
telegram-plugin-isolation surface for EVERY loam-adjacent ``claude``
spawn.

Maps to (plan docs/plans/telegram-5-fix.md §3.3):
  AC.PROMO.1 — a harness-style multi-spawn routed through this surface
               completes and a sentinel poller survives (the empirical
               proof; lead AC; exercised by the opt-in real-binary
               test).
  AC.PROMO.2 — an argv built via this surface carries the
               empty-strict-MCP isolation + zero telegram markers; the
               env has the bot-token/API-key spellings absent AND
               ``CLAUDE_PERSONA`` set (belt-and-braces).
  AC.PROMO.3 — this surface is what the fix's OWN acceptance test must
               spawn through (the dogfood-recursion closure; enforced
               structurally on the test module itself, not here).
  AC.PROMO.4 — :func:`assert_loam_spawn_isolated` makes a
               loam-adjacent ``claude`` argv built WITHOUT the
               isolation fail loudly (raises) rather than silently
               shipping a kill-capable invocation.
  AC.PROMO.5 — one-line importable from an arbitrary out-of-tree
               (/tmp-CWD) caller (the #5 harness class) — see the
               module docstring's reach recipe + :func:`canonical_src`.

WHY THIS EXISTS — Telegram-death #5, stated plainly.  The b33c0a8 /
e0b71cb handsoff-loop ``_isolation.py`` fix did NOT fail and was NOT
under-scoped for what it was built for: it isolates the three §1b
production launch sites and it holds.  #5 came through a doorway it
was never positioned to reach — a dispatched-agent-authored throwaway
re-harden harness in ``/tmp`` that hand-rolled

    subprocess.run(["claude", "-p", prompt, "--model", "sonnet",
                     "--output-format", "json", "--permission-mode",
                     "bypassPermissions"], ...)

with a ``ThreadPoolExecutor(max_workers=7)`` — up to 7 parallel
UN-isolated spawns.  Each loaded the user-enabled telegram plugin,
which spawns a competing ``bun server.ts`` that SIGTERMs the
operator's single-consumer Telegram poller for the one bot-token
``getUpdates`` slot.  The harness killed Telegram while purporting to
prove Telegram was protected — the recursion this surface closes.

The uncovered class is precisely-named: dispatched-agent-authored
``/tmp`` test / judge / probe / re-harden harnesses that hand-roll a
raw ``subprocess.run(["claude","-p",...])`` instead of importing
loam's isolation.  It is a *recurring spawn pattern produced by the
build process itself* (agents writing measurement harnesses), not a
fixed file.  The fix is therefore NOT to patch N files (there are
none uncovered in-tree — every in-tree spawn is already isolated).
The fix is to make the isolation a SHARED, ONE-LINE-IMPORTABLE,
DOGFOOD-MANDATED surface + a structural guard + a belt-and-braces
env-var so the *next* hand-rolled harness is caught or defanged.

THE PROVEN MECHANISM, PROMOTED — NOT RE-IMPLEMENTED (plan §2 / §0:
contained, not a re-architecture).  This module promotes the proven
``handsoff_loop._isolation`` adapter pattern (sealed b33c0a8/e0b71cb,
AC.TPI.*) out of the handsoff-loop package into a shared surface ANY
caller can import.  It wraps the SEALED subloam-driver isolation
functions (``build_isolated_claude_argv`` / ``build_isolated_env`` /
``write_empty_mcp_config`` / ``IsolationConfig``, sealed under
AC.LIPW.5/.6 — empirically verified necessary-AND-sufficient
operator-protection).  No new isolation machinery.

ONE-LINE REACH FROM AN OUT-OF-TREE /tmp CALLER (AC.PROMO.5).  A
dispatched harness whose CWD is ``/tmp`` (it is not inside the
canonical tree, so it cannot use ``Path(__file__)`` relative
resolution the way an in-tree module does) reaches this surface in
ONE line by putting the canonical package ``src`` on ``sys.path``::

    import sys; sys.path.insert(
        0, "/Users/lukeivers/loam/framework/tools/"
           "loam-spawn-isolation/src")
    from loam_spawn_isolation import spawn_isolated_claude
    # ...then NEVER hand-roll subprocess.run(["claude", ...]):
    result = spawn_isolated_claude(
        ["claude", "-p", PROMPT, "--model", "sonnet",
         "--output-format", "json",
         "--permission-mode", "bypassPermissions"])

The canonical tree path is stable (it is where loam lives); the
recipe is documented at the point a harness is authored (this
docstring + the package description) so future harness authors
import the surface rather than hand-roll.  :func:`canonical_src`
returns this path so an in-tree caller that knows the repo root can
hand it to a harness it dispatches.

Stdlib-only.  NO Anthropic API key (``feedback_no_anthropic_api_key``)
— the env scrub strips ``ANTHROPIC_API_KEY``; the real ``claude``
binary uses the keychain-stored subscription credential.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

# Promote the PROVEN handsoff-loop adapter PATTERN over the SEALED
# subloam-driver primitive (plan §2: reuse, do not re-implement).
# subloam-driver is a sibling tool package; resolve its src the same
# way the sealed handsoff_loop._isolation adapter + the AC.LIPW.5
# seal-test do.  parents[3] of
# .../loam-spawn-isolation/src/loam_spawn_isolation/__init__.py
# == framework/tools/ ; subloam-driver/src is the sibling.
_SUBLOAM_SRC = (
    Path(__file__).resolve().parents[3] / "subloam-driver" / "src"
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

__all__ = [
    "spawn_isolated_claude",
    "inject_isolation",
    "isolated_claude_argv",
    "isolated_env",
    "isolation_flags",
    "assert_loam_spawn_isolated",
    "ensure_empty_mcp_config",
    "canonical_src",
    "TELEGRAM_PLUGIN_MARKERS",
    "ISOLATED_PERSONA_VALUE",
]

# Re-export the sealed marker tuple so callers/guards reference ONE
# source of truth (no drift from the sealed kill-vector definition).
TELEGRAM_PLUGIN_MARKERS = _TELEGRAM_PLUGIN_MARKERS

# The belt-and-braces env-var value (plan §3.2 IN / AC.PROMO.2).  The
# root-cause report's independently-sufficient defense: a spawned
# ``claude`` that sees a non-default ``CLAUDE_PERSONA`` does not run
# the operator's persona/handsoff bootstrap, so even if a spawn DID
# load the telegram plugin it would not start a competing poller.
# This alone would have prevented #5 (the reharden judge inherited an
# env with no ``CLAUDE_PERSONA``).  It is INDEPENDENT of the
# empty-strict-MCP isolation — defense in depth, not a substitute.
ISOLATED_PERSONA_VALUE = "loam-isolated-spawn"

# The stable scratch root for the shared empty-MCP config.  NEVER the
# operator's ~/.claude (the IsolationConfig structural guard refuses
# that root — the plugin-cache singleton + bot-token root that carries
# the exact kill vector).
_ISOLATION_ROOT = Path(tempfile.gettempdir()) / "loam-spawn-isolation"
_EMPTY_MCP_CONFIG = _ISOLATION_ROOT / "empty.mcp.json"


def canonical_src() -> Path:
    """The canonical ``src`` dir of THIS package.

    An in-tree caller that dispatches a ``/tmp`` harness can pass
    ``str(canonical_src())`` into the harness so the harness reaches
    the shared surface in one ``sys.path.insert`` + ``import`` —
    AC.PROMO.5's one-line out-of-tree reach without re-architecture.
    """
    return Path(__file__).resolve().parents[1]


def _config() -> IsolationConfig:
    """The single IsolationConfig the shared surface reuses.

    ``air_gapped_config`` stays False (the default) so the spawned
    ``claude`` keeps the keychain-stored subscription credential
    reachable — there is NO API key (``feedback_no_anthropic_api_key``).
    Operator-protection does NOT depend on the config relocation: the
    kill vector is the telegram plugin (excluded from the argv via the
    empty strict-MCP config), not the config root.  Identical
    construction to the sealed ``handsoff_loop._isolation._config``.
    """
    return IsolationConfig(
        claude_config_dir=_ISOLATION_ROOT / ".claude-home",
        empty_mcp_config_path=_EMPTY_MCP_CONFIG,
        workspace_slug="loam-spawn-isolation",
    )


def ensure_empty_mcp_config() -> Path:
    """Write/refresh the explicit empty MCP config; return its path.

    Idempotent — delegates to the sealed
    ``subloam_driver.write_empty_mcp_config`` (no re-implementation).
    A non-existent ``--mcp-config`` path makes the real ``claude``
    reject the invocation, so the file MUST exist before any spawn.
    """
    return write_empty_mcp_config(_config().empty_mcp_config_path)


def assert_loam_spawn_isolated(argv: list[str]) -> None:
    """AC.PROMO.4 — the structural mandate guard.

    A loam-adjacent ``claude`` argv constructed WITHOUT the shared
    isolation fails LOUDLY here (raises ``ValueError``) rather than
    silently shipping a kill-capable invocation.  Reuses the SEALED
    marker-guard discipline (``driver.py`` ``_TELEGRAM_PLUGIN_MARKERS``
    / ``_isolation._assert_telegram_free``) verbatim AND additionally
    asserts the empty-strict-MCP isolation flag pair is present — a
    raw ``["claude","-p",...]`` with no isolation (the literal #5
    pattern) raises.  This is the chokepoint a regression cannot pass
    silently.

    Non-``claude`` argvs are out of scope (not a kill vector) and pass
    untouched — the guard is a spawn-isolation sentinel, not a blanket
    reject.
    """
    if not argv:
        raise ValueError("empty argv — cannot validate isolation")
    # Only loam-adjacent `claude` spawns are the kill class.  A
    # non-claude argv is not a SIGTERM vector; do not over-reach.
    binary = Path(argv[0]).name
    if binary != "claude":
        return
    joined = " ".join(argv)
    for marker in _TELEGRAM_PLUGIN_MARKERS:
        if marker in joined:
            raise ValueError(
                f"loam-adjacent claude argv carries telegram marker "
                f"{marker!r} — the sole kill vector. Refusing to "
                f"build a kill-capable invocation (AC.PROMO.4)."
            )
    if "--strict-mcp-config" not in argv or "--mcp-config" not in argv:
        raise ValueError(
            "loam-adjacent claude argv was constructed WITHOUT the "
            "shared isolation (missing --strict-mcp-config "
            "--mcp-config <empty>). This is the exact Telegram-death "
            "#5 pattern: a hand-rolled raw [\"claude\",\"-p\",...] "
            "that loads the user-enabled telegram plugin and SIGTERMs "
            "the operator's single-consumer poller. Build the spawn "
            "via loam_spawn_isolation.spawn_isolated_claude / "
            "inject_isolation instead of hand-rolling it "
            "(AC.PROMO.4)."
        )


def isolation_flags() -> list[str]:
    """The empty-strict-MCP isolation flag fragment.

    Derived from the SEALED ``build_isolated_claude_argv`` so the flag
    pair + empty-MCP path are byte-identical to the proven mechanism;
    the interactive-only/prompt/permission portions of the sealed argv
    are NOT borrowed (callers keep their own ``-p``/json shape — the
    same preservation the sealed ``_isolation.isolation_flags`` does).
    The empty-MCP file is guaranteed to exist.
    """
    ensure_empty_mcp_config()
    proven = build_isolated_claude_argv(_config())
    # proven == [claude, --dangerously-skip-permissions,
    #            --strict-mcp-config, --mcp-config, <empty>, --model, …]
    i = proven.index("--strict-mcp-config")
    flags = proven[i : i + 3]  # --strict-mcp-config --mcp-config <path>
    return list(flags)


def inject_isolation(argv: list[str]) -> list[str]:
    """Inject the empty-strict-MCP isolation into an existing argv.

    The caller's existing shape (positional ``-p`` prompt,
    ``--model``, ``--permission-mode``, ``--output-format json``) is
    PRESERVED — only the isolation flags are inserted (immediately
    after the ``claude`` binary, before the ``-p``).  The result is
    guarded telegram-free + isolation-present via
    :func:`assert_loam_spawn_isolated` (AC.PROMO.4).  Same contract as
    the sealed ``handsoff_loop._isolation.inject_isolation``, promoted
    to the shared surface.
    """
    if not argv:
        raise ValueError("empty argv — cannot isolate")
    isolated = [argv[0], *isolation_flags(), *argv[1:]]
    assert_loam_spawn_isolated(isolated)
    return isolated


def isolated_claude_argv(argv: list[str]) -> list[str]:
    """Alias of :func:`inject_isolation` with an outcome-named handle.

    Some callers read better with a noun ("give me the isolated
    argv"); the behaviour is identical.
    """
    return inject_isolation(argv)


def isolated_env(
    base_env: dict[str, str] | None = None,
) -> dict[str, str]:
    """The token/API-key-scrubbed env for a spawn, PLUS the
    ``CLAUDE_PERSONA`` belt-and-braces env-var (AC.PROMO.2).

    Delegates the scrub to the SEALED ``build_isolated_env`` (no
    re-implementation): strips ``TELEGRAM_BOT_TOKEN`` /
    ``CLAUDE_PLUGIN_TELEGRAM_BOT_TOKEN`` (so the spawned ``claude``
    cannot steal the operator's single-consumer poller slot) and
    ``ANTHROPIC_API_KEY`` (``feedback_no_anthropic_api_key`` —
    subscription-only).  Then sets ``CLAUDE_PERSONA`` to the isolated
    value — the independently-sufficient defense (plan §3.2 IN): even
    if a spawn somehow loaded the plugin, a non-operator persona does
    not start the competing poller.  ``air_gapped_config`` is False so
    ``CLAUDE_CONFIG_DIR`` is left unset and subscription auth resolves.
    """
    env = build_isolated_env(_config(), base_env=base_env)
    env["CLAUDE_PERSONA"] = ISOLATED_PERSONA_VALUE
    return env


def spawn_isolated_claude(
    argv: list[str],
    *,
    base_env: dict[str, str] | None = None,
    **run_kwargs: object,
) -> "subprocess.CompletedProcess[object]":
    """THE mandated entry point — run a ``claude`` spawn isolated.

    The single call a loam-adjacent caller (in-tree OR a hand-rolled
    ``/tmp`` harness) makes instead of ``subprocess.run(["claude",
    ...])``.  It (1) injects the empty-strict-MCP isolation into the
    argv (preserving the caller's ``-p``/json shape), (2) builds the
    token/API-key-scrubbed + ``CLAUDE_PERSONA``-set env, (3) asserts
    the final argv is isolated (AC.PROMO.4 — raises rather than
    shipping a kill-capable invocation), then (4) ``subprocess.run``s
    it.  ``run_kwargs`` are forwarded to ``subprocess.run`` (e.g.
    ``capture_output=True``, ``text=True``, ``timeout=...``); a
    caller-supplied ``env=`` is overridden by the isolated env (the
    isolation is non-negotiable — that is the mandate).
    """
    isolated_argv = inject_isolation(argv)
    assert_loam_spawn_isolated(isolated_argv)
    env = isolated_env(base_env)
    run_kwargs.pop("env", None)  # isolation is non-negotiable
    return subprocess.run(isolated_argv, env=env, **run_kwargs)  # type: ignore[call-overload]  # noqa: E501
