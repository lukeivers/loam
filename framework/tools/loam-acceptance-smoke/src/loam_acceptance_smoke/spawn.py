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

"""The MANDATED spawn surface for the smoke — every `claude -p` (role-played
user side AND every judge probe) goes through here, and here ONLY routes
through ``loam_spawn_isolation.spawn_isolated_claude``.

WHY (design F-5 + feedback_spawned_claude_must_isolate_telegram_plugin): an
un-isolated `claude -p` loads the operator's enabled telegram plugin, which
spawns a competing ``bun server.ts`` that SIGTERMs the operator's single
Telegram poller for the one bot-token getUpdates slot — breaking the owner's
only channel. The isolation primitive injects ``--strict-mcp-config`` + an
empty MCP config and scrubs TELEGRAM_BOT_TOKEN / ANTHROPIC_API_KEY (no API key
— subscription-only, feedback_no_anthropic_api_key) from the env.

This module is a thin, COUNTED wrapper: it records every spawn so the run
report can assert "every claude -p was spawn-isolated" empirically, and it
re-asserts the isolation guard on the final argv as belt-and-braces.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path


def _ensure_isolation_importable() -> None:
    """Put the canonical loam-spawn-isolation src on sys.path (the documented
    one-line out-of-tree reach, AC.PROMO.5) when it is not already importable.

    Resolves the canonical tree from THIS file's location so the smoke works
    whether run in-tree or dispatched into /tmp.
    """
    try:
        import loam_spawn_isolation  # noqa: F401

        return
    except ImportError:
        pass
    # .../loam-acceptance-smoke/src/loam_acceptance_smoke/spawn.py
    # parents[3] == framework/tools/ ; the sibling primitive package's src.
    sibling = (
        Path(__file__).resolve().parents[3]
        / "loam-spawn-isolation"
        / "src"
    )
    if sibling.is_dir() and str(sibling) not in sys.path:
        sys.path.insert(0, str(sibling))


@dataclass
class SpawnRecord:
    """One isolated `claude -p` spawn, recorded for the protection audit."""

    purpose: str  # "role-play:A" / "judge:learned-this-person:B" / ...
    argv_isolated: bool  # the final argv carried --strict-mcp-config --mcp-config
    returncode: int
    persona_scrubbed: bool  # env had no telegram/api-key markers + CLAUDE_PERSONA set


@dataclass
class SpawnLedger:
    """Process-wide ledger of every isolated spawn the smoke made.

    The run report asserts ``all(r.argv_isolated and r.persona_scrubbed)`` —
    the empirical "every claude -p was spawn-isolated" proof.
    """

    records: list[SpawnRecord] = field(default_factory=list)

    @property
    def all_isolated(self) -> bool:
        return bool(self.records) and all(
            r.argv_isolated and r.persona_scrubbed for r in self.records
        )

    @property
    def count(self) -> int:
        return len(self.records)


# A single shared ledger for the whole run.
LEDGER = SpawnLedger()


def isolated_claude_text(
    prompt: str,
    *,
    purpose: str,
    model: str = "sonnet",
    timeout: float = 180.0,
    system_prompt: str | None = None,
) -> str:
    """Run a one-shot isolated `claude -p` and return the text result.

    Every spawn is routed through ``loam_spawn_isolation.spawn_isolated_claude``
    (the mandated surface) and recorded in :data:`LEDGER` for the protection
    audit. Raises RuntimeError on a failed dispatch so the caller surfaces it
    rather than silently scoring an empty transcript.
    """
    _ensure_isolation_importable()
    from loam_spawn_isolation import (
        assert_loam_spawn_isolated,
        inject_isolation,
        isolated_env,
        spawn_isolated_claude,
    )

    argv = [
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
    if system_prompt:
        argv += ["--append-system-prompt", system_prompt]

    # Belt-and-braces: confirm the final argv would be isolated + the env is
    # scrubbed BEFORE the spawn, and record the verdict.
    final_argv = inject_isolation(list(argv))
    argv_isolated = (
        "--strict-mcp-config" in final_argv and "--mcp-config" in final_argv
    )
    try:
        assert_loam_spawn_isolated(final_argv)
        guard_ok = True
    except Exception:
        guard_ok = False
    env = isolated_env()
    persona_scrubbed = (
        "TELEGRAM_BOT_TOKEN" not in env
        and "ANTHROPIC_API_KEY" not in env
        and env.get("CLAUDE_PERSONA") is not None
    )

    proc = spawn_isolated_claude(
        argv,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    LEDGER.records.append(
        SpawnRecord(
            purpose=purpose,
            argv_isolated=argv_isolated and guard_ok,
            returncode=proc.returncode,
            persona_scrubbed=persona_scrubbed,
        )
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"isolated claude -p ({purpose}) exited {proc.returncode}: "
            f"{(proc.stderr or '')[:400]}"
        )
    raw = (proc.stdout or "").strip()
    try:
        envelope = json.loads(raw)
    except (json.JSONDecodeError, ValueError) as exc:
        raise RuntimeError(
            f"isolated claude -p ({purpose}) returned non-JSON envelope: "
            f"{exc}: {raw[:300]}"
        ) from exc
    result = envelope.get("result")
    if not isinstance(result, str):
        raise RuntimeError(
            f"isolated claude -p ({purpose}) envelope has no string result: "
            f"{envelope!r}"
        )
    return result.strip()
