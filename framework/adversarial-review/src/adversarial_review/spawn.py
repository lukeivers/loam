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
# implied. See the License for the specific language governing
# permissions and limitations under the License.

"""Isolated critic/judge/validator spawn — via the SEALED spawn surface.

P9 / AC.AR.8: EVERY spawned critic, merge-judge, or non-executable
validator in this capability runs through loam's sealed
``spawn_isolated_claude`` entry-point — NEVER a hand-rolled
``subprocess.run(["claude", ...])``. The un-isolated spawn loads the
user-enabled telegram plugin and SIGTERMs the operator's single-consumer
poller (Telegram-death #5, a proven kill vector — not a style
preference). This module is the ONE place the capability reaches that
surface, using the surface's own documented out-of-tree reach recipe
(AC.PROMO.5), so the whole package composes on it rather than
re-implementing isolation (Lens 1).

Per ODD §2.5:

  * :func:`run_isolated_critic` (spawn via the sealed surface) -> AC.AR.8.
  * :func:`assert_isolated`     (loud-refuse a bare argv)       -> AC.AR.8.
  * :data:`SPAWN_AVAILABLE` gate + fail-soft returns            -> the
    manual/gate paths degrade to a REVIEW-INCONCLUSIVE surface rather
    than a false clean bill when the binary/surface is missing.

No Anthropic API key (``feedback_no_anthropic_api_key``) — the sealed
surface scrubs it and the real ``claude`` uses the subscription
credential. Default model Sonnet (Lens 5: no model-rationale needed).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

# The sealed spawn-isolation surface is a sibling component in the SAME
# canonical loam tree. Resolve it IN-TREE relative to this file so the
# reach holds in any checkout (worktree, cold-clone, a consumer's clone),
# not only the maintainer's primary path. (Pre-promotion this capability
# lived pos3-local and reached the surface via a documented out-of-tree
# absolute path — AC.PROMO.5; in canonical it is a plain sibling import.)
# This file: framework/adversarial-review/src/adversarial_review/spawn.py
# -> parents[4] is the repo root.
_SEALED_SPAWN_SRC = (
    Path(__file__).resolve().parents[4]
    / "framework"
    / "tools"
    / "loam-spawn-isolation"
    / "src"
)
if _SEALED_SPAWN_SRC.is_dir() and str(_SEALED_SPAWN_SRC) not in sys.path:
    sys.path.insert(0, str(_SEALED_SPAWN_SRC))

try:
    from loam_spawn_isolation import (  # type: ignore[import-not-found]
        assert_loam_spawn_isolated as _sealed_assert,
    )
    from loam_spawn_isolation import (  # type: ignore[import-not-found]
        inject_isolation as _sealed_inject,
    )
    from loam_spawn_isolation import (  # type: ignore[import-not-found]
        spawn_isolated_claude as _sealed_spawn,
    )

    SPAWN_AVAILABLE = True
except Exception:  # noqa: BLE001 — packaging gap degrades fail-soft
    SPAWN_AVAILABLE = False

DEFAULT_MODEL = "sonnet"
DEFAULT_TIMEOUT_S = 180


def assert_isolated(argv: list[str]) -> None:
    """Refuse a bare / un-isolated ``claude`` argv (AC.AR.8).

    Delegates to the SEALED guard so the kill-vector definition has ONE
    source of truth. When the sealed surface is unavailable we still
    refuse a bare ``claude`` argv locally (missing ``--strict-mcp-config``
    / ``--mcp-config``) — the guard must not silently pass just because
    the sealed import failed.
    """
    if SPAWN_AVAILABLE:
        _sealed_assert(argv)
        return
    if not argv:
        raise ValueError("empty argv — cannot validate isolation")
    if Path(argv[0]).name != "claude":
        return
    if "--strict-mcp-config" not in argv or "--mcp-config" not in argv:
        raise ValueError(
            "un-isolated claude argv refused (AC.AR.8): missing "
            "--strict-mcp-config/--mcp-config — the Telegram-death #5 "
            "kill vector. Route through loam_spawn_isolation."
        )


def build_argv(prompt: str, *, model: str = DEFAULT_MODEL) -> list[str]:
    """The pre-isolation base ``claude -p`` argv (the caller's own shape).

    The sealed surface injects the empty-strict-MCP isolation + scrubbed
    env around this at spawn time. Never spawned bare.
    """
    return [
        "claude",
        "-p",
        prompt,
        "--model",
        model,
        "--output-format",
        "json",
        "--permission-mode",
        "bypassPermissions",
    ]


def isolated_argv(prompt: str, *, model: str = DEFAULT_MODEL) -> list[str]:
    """Build + isolate an argv (AC.AR.8). Raises if isolation is absent.

    Exposed so tests can assert the isolation flags are present WITHOUT a
    real spawn (the frame_judge test posture).
    """
    base = build_argv(prompt, model=model)
    if SPAWN_AVAILABLE:
        argv = _sealed_inject(base)
    else:
        # Local isolation injection mirrors the sealed shape so the guard
        # and tests still see the flags when the sealed surface is absent.
        argv = [
            base[0],
            "--strict-mcp-config",
            "--mcp-config",
            "<empty-mcp-config>",
            *base[1:],
        ]
    assert_isolated(argv)
    return argv


def _unwrap_json(raw: str) -> str:
    """Unwrap the ``claude -p --output-format json`` envelope to the text.

    Returns the ``result`` field when the output is the JSON envelope,
    else the raw string. Tolerant of non-JSON (returns raw).
    """
    text = raw.strip()
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return text
    if isinstance(payload, dict):
        inner = payload.get("result")
        if isinstance(inner, str) and inner.strip():
            return inner.strip()
    return text


def run_isolated_critic(
    prompt: str,
    *,
    model: str = DEFAULT_MODEL,
    timeout: int = DEFAULT_TIMEOUT_S,
) -> str | None:
    """Run one isolated ``claude -p`` and return the unwrapped text (AC.AR.8).

    Goes through the SEALED ``spawn_isolated_claude`` — plugin isolation +
    token/API-key scrub + ``CLAUDE_PERSONA`` belt-and-braces. Fail-soft:
    a missing surface, spawn failure, timeout, or non-zero exit returns
    ``None`` (the caller renders REVIEW-INCONCLUSIVE — never a false clean
    bill). Returns the unwrapped model text on success.

    ``stdin=DEVNULL``: the child ``claude`` never inherits the parent's
    stdin, so it can never block reading it. This is cheap defensive
    hardening — NOTE it is NOT the fix for the interactive-session hang
    (probes show a nested ``claude -p`` returns fine with inherited /
    open-pipe / devnull stdin alike; the hang is an interactive-slot
    contention). The real in-session fix is the injected-leg backend
    (:mod:`adversarial_review.insession`), which does not spawn here at all.
    """
    if not SPAWN_AVAILABLE:
        return None
    argv = build_argv(prompt, model=model)
    try:
        proc = _sealed_spawn(
            argv,
            capture_output=True,
            text=True,
            timeout=timeout,
            stdin=subprocess.DEVNULL,
        )
    except Exception:  # noqa: BLE001 — spawn/timeout is fail-soft
        return None
    if getattr(proc, "returncode", 1) != 0:
        return None
    stdout = getattr(proc, "stdout", None)
    if not isinstance(stdout, str) or not stdout.strip():
        return None
    return _unwrap_json(stdout)
