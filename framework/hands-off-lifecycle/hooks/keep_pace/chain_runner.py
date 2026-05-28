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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Fail-open-whole-chain runner for the keep-pace hook chain (KP0).

The single structural guarantee this module exists to provide
(AC.KP0.4): **a broken memory hook must never break the live session.**
A contributor that raises, hangs past its per-hook budget, or returns
garbage is isolated — the turn proceeds and any well-behaved
contributors still get to inject their context.

Design (D-KP0.2):
  - Each contributor is a ``Contributor`` (a name + a callable taking the
    parsed hook envelope and returning an ``additionalContext`` string or
    ``None``).
  - Each contributor runs in its own daemon thread with a per-hook
    wall-clock timeout. A contributor that overruns the timeout is
    abandoned (the daemon thread is left to die with the process); its
    output is discarded and the chain continues. This is the only safe
    in-process timeout for arbitrary callables on a hook that must exit
    promptly — we never block the turn waiting on a wedged contributor.
  - A per-turn total-latency budget caps the whole chain: once the
    cumulative wall-clock crosses the budget, remaining contributors are
    skipped (recorded as ``skipped-budget``) rather than run.
  - Every contributor's outcome + latency is recorded in a structured
    log line (AC.KP0.5) appended to the latency log path, so the
    per-turn budget can be reasoned about from real numbers (loam's own
    numbers — the design's $0/45ms figures are claude-mem's, not loam's,
    per RF-5).
  - ``run_chain`` itself NEVER raises: it is wrapped so that even an
    internal bug converts to "emit nothing, exit clean."

Stdlib-only.
"""

from __future__ import annotations

import json
import os
import sys
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Optional


# Defaults (overridable per call / via env for the live wiring).
DEFAULT_PER_HOOK_TIMEOUT_S = 1.5
DEFAULT_PER_TURN_BUDGET_S = 3.0


@dataclass
class Contributor:
    """One memory contributor on the chain.

    ``fn`` takes the parsed hook envelope (a dict) and returns an
    ``additionalContext`` string to inject, or ``None`` for "nothing to
    add." ``fn`` may raise — the runner isolates it.
    """

    name: str
    fn: Callable[[dict], Optional[str]]


@dataclass
class ContributorResult:
    name: str
    status: str  # "ok" | "empty" | "error" | "timeout" | "skipped-budget"
    latency_ms: float
    context: Optional[str] = None
    error: Optional[str] = None


@dataclass
class ChainResult:
    event: str
    results: list = field(default_factory=list)
    total_latency_ms: float = 0.0

    def merged_context(self) -> str:
        """Join every successful contributor's context, newest-chain-order."""
        parts = [
            r.context
            for r in self.results
            if r.status == "ok" and r.context and r.context.strip()
        ]
        return "\n\n".join(parts)


def _run_one(
    contributor: Contributor,
    envelope: dict,
    timeout_s: float,
) -> ContributorResult:
    """Run a single contributor under a per-hook timeout, isolating
    every failure mode into a ContributorResult (never raises)."""
    box: dict = {}

    def _target() -> None:
        try:
            box["context"] = contributor.fn(envelope)
        except BaseException as exc:  # noqa: BLE001 — total isolation
            box["error"] = repr(exc)

    start = time.monotonic()
    thread = threading.Thread(target=_target, daemon=True)
    thread.start()
    thread.join(timeout_s)
    latency_ms = (time.monotonic() - start) * 1000.0

    if thread.is_alive():
        # Wedged contributor: abandon it (daemon dies with the process),
        # discard any partial output, keep the turn moving.
        return ContributorResult(
            name=contributor.name,
            status="timeout",
            latency_ms=latency_ms,
        )
    if "error" in box:
        return ContributorResult(
            name=contributor.name,
            status="error",
            latency_ms=latency_ms,
            error=box["error"],
        )
    ctx = box.get("context")
    if ctx is None or (isinstance(ctx, str) and not ctx.strip()):
        return ContributorResult(
            name=contributor.name,
            status="empty",
            latency_ms=latency_ms,
        )
    if not isinstance(ctx, str):
        # A contributor returning a non-string is a bug; isolate it.
        return ContributorResult(
            name=contributor.name,
            status="error",
            latency_ms=latency_ms,
            error=f"non-str context: {type(ctx).__name__}",
        )
    return ContributorResult(
        name=contributor.name,
        status="ok",
        latency_ms=latency_ms,
        context=ctx,
    )


def run_chain(
    event: str,
    envelope: dict,
    contributors: list,
    *,
    per_hook_timeout_s: float = DEFAULT_PER_HOOK_TIMEOUT_S,
    per_turn_budget_s: float = DEFAULT_PER_TURN_BUDGET_S,
    latency_log_path: Optional[str] = None,
) -> ChainResult:
    """Run every contributor fail-open under the per-turn budget.

    Returns a ChainResult. NEVER raises — an internal failure converts to
    an empty ChainResult so the caller still exits clean.
    """
    result = ChainResult(event=event)
    try:
        chain_start = time.monotonic()
        for contributor in contributors:
            elapsed = time.monotonic() - chain_start
            if elapsed >= per_turn_budget_s:
                result.results.append(
                    ContributorResult(
                        name=getattr(contributor, "name", "?"),
                        status="skipped-budget",
                        latency_ms=0.0,
                    )
                )
                continue
            # Don't let a single contributor exceed the remaining budget.
            remaining = per_turn_budget_s - elapsed
            effective_timeout = min(per_hook_timeout_s, max(0.0, remaining))
            try:
                result.results.append(
                    _run_one(contributor, envelope, effective_timeout)
                )
            except BaseException as exc:  # noqa: BLE001
                result.results.append(
                    ContributorResult(
                        name=getattr(contributor, "name", "?"),
                        status="error",
                        latency_ms=0.0,
                        error=repr(exc),
                    )
                )
        result.total_latency_ms = (time.monotonic() - chain_start) * 1000.0
    except BaseException:  # noqa: BLE001 — the whole-chain guarantee
        # Even a bug in the runner itself must not break the turn.
        pass

    if latency_log_path:
        _write_latency_log(latency_log_path, result)
    return result


def _write_latency_log(path: str, result: ChainResult) -> None:
    """Append one JSON line per chain run (AC.KP0.5). Never raises."""
    try:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        line = {
            "ts": round(time.time(), 3),
            "event": result.event,
            "total_latency_ms": round(result.total_latency_ms, 3),
            "contributors": [
                {
                    "name": r.name,
                    "status": r.status,
                    "latency_ms": round(r.latency_ms, 3),
                }
                for r in result.results
            ],
        }
        with open(path, "a") as fh:
            fh.write(json.dumps(line) + "\n")
    except BaseException:  # noqa: BLE001 — logging never breaks the turn
        pass


def emit_user_prompt_submit(result: ChainResult) -> None:
    """Print the UserPromptSubmit hookSpecificOutput envelope to stdout.

    Emits additionalContext only when there is merged context; otherwise
    prints nothing (silent-on-no-match composes here). Never raises.
    """
    try:
        merged = result.merged_context()
        if not merged.strip():
            return
        out = {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": merged,
            }
        }
        sys.stdout.write(json.dumps(out))
    except BaseException:  # noqa: BLE001
        pass


def default_latency_log_path(envelope: dict) -> Optional[str]:
    """Resolve the per-workspace latency log path under .scratch.

    Reads ``workspace.project_dir`` from the envelope; falls back to cwd.
    Returns None only if no writable base can be resolved (logging is
    then skipped — never an error).
    """
    try:
        ws = envelope.get("workspace") if isinstance(envelope, dict) else None
        base = None
        if isinstance(ws, dict):
            base = ws.get("project_dir")
        if not base or not isinstance(base, str):
            base = os.getcwd()
        return os.path.join(
            base, ".scratch", "keep-pace", "hook-latency.log"
        )
    except BaseException:  # noqa: BLE001
        return None
