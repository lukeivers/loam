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

"""Per-project Claude-token totals from the local transcript store (proxy).

**Why this is a parser and not ``ccusage`` (D-A5-1).** The plan directs adopting
``ccusage``, and it does run (``npx -y ccusage@latest``), but it groups usage
only by date / month / week / *session* — its JSON carries a session UUID and a
``lastActivity`` timestamp and **no cwd/project path**. The project dimension
this roll-up ranks on is exactly what ccusage discards, so it cannot answer
"top-3 *projects* by tokens". The transcript files ccusage reads
(``~/.claude/projects/<encoded-cwd>/<session>.jsonl``) DO carry the project (the
directory name is the encoded cwd), so this reads them directly.

**Correctness the naive sum would miss (D-A5-1b).** This is a *weekly* burn
signal, so two things are load-bearing for a *correct* ranking:

* **Dedup.** Resumed / compacted sessions re-emit the same assistant message, so
  a per-line sum double-counts. Each assistant usage block is counted **once**
  per ``(message.id, requestId)`` (the same keys ccusage dedupes on).
* **Windowing.** An all-time sum never moves week to week and misranks toward
  whatever was resumed most. Only lines whose top-level ``timestamp`` falls in
  the last ``window_days`` (default 7) are counted.

The result is a **proxy** — it ranks consumption, it is never dollars (a flat
subscription has no per-project invoice; stream 04 §1c).
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

# Env override for the transcript root (test-fixture seam); else the real store.
_PROJECTS_DIR_ENV = "LOAM_CLAUDE_PROJECTS_DIR"
_DEFAULT_PROJECTS_DIR = "~/.claude/projects"

# The four token fields whose sum is one message's total (matches ccusage's
# totalTokens = input + output + cache-creation + cache-read).
_TOKEN_FIELDS = (
    "input_tokens",
    "output_tokens",
    "cache_creation_input_tokens",
    "cache_read_input_tokens",
)


@dataclass(frozen=True)
class ProjectTokens:
    """One project's summed Claude tokens over the window (the proxy unit)."""

    project: str
    tokens: int


@dataclass(frozen=True)
class TokenUsageUnavailable:
    """The token source could not produce a ranking — a NAMED absence.

    ``reason`` is a stable categorical token (``no_transcripts`` when the store
    is missing/empty, ``no_recent_activity`` when nothing falls in the window),
    so the roll-up can name the gap instead of silently dropping the section.
    """

    reason: str


def projects_dir() -> Path:
    """The resolved transcript root: the env override if set, else the default."""
    raw = os.environ.get(_PROJECTS_DIR_ENV) or _DEFAULT_PROJECTS_DIR
    return Path(raw).expanduser()


def _parse_timestamp(raw: object) -> Optional[datetime]:
    """Parse a transcript line's ISO ``timestamp`` into an aware datetime."""
    if not isinstance(raw, str):
        return None
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _line_tokens(usage: dict) -> int:
    """Sum the four token fields of one ``message.usage`` block."""
    total = 0
    for field in _TOKEN_FIELDS:
        value = usage.get(field)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            total += int(value)
    return total


def _sum_project(path: Path, cutoff: datetime, seen: set[str]) -> int:
    """Sum in-window, deduped assistant tokens across one project's sessions."""
    total = 0
    for session_file in sorted(path.glob("*.jsonl")):
        try:
            text = session_file.read_text(encoding="utf-8")
        except OSError:
            continue
        for raw_line in text.splitlines():
            raw_line = raw_line.strip()
            if not raw_line:
                continue
            try:
                record = json.loads(raw_line)
            except (json.JSONDecodeError, ValueError):
                # A partial last line (mid-write) or malformed record is skipped;
                # it never crashes the roll-up.
                continue
            if not isinstance(record, dict):
                continue
            message = record.get("message")
            if not isinstance(message, dict):
                continue
            usage = message.get("usage")
            if not isinstance(usage, dict):
                continue
            when = _parse_timestamp(record.get("timestamp"))
            if when is None or when < cutoff:
                continue
            message_id = message.get("id")
            request_id = record.get("requestId")
            if isinstance(message_id, str) and isinstance(request_id, str):
                key = f"{message_id}:{request_id}"
                if key in seen:
                    continue
                seen.add(key)
            total += _line_tokens(usage)
    return total


def read_project_tokens(
    root: Optional[Path] = None,
    *,
    window_days: int = 7,
    now: Optional[datetime] = None,
) -> "list[ProjectTokens] | TokenUsageUnavailable":
    """Rank projects by summed Claude tokens over the last ``window_days``.

    Reads ``<root>/<project>/<session>.jsonl``, dedupes assistant usage blocks on
    ``(message.id, requestId)``, windows by each line's ``timestamp``, sums the
    four token fields per project, and returns the projects sorted by tokens
    descending. Returns :class:`TokenUsageUnavailable` (a NAMED absence) when the
    store is missing/empty or nothing falls in the window — never an empty list
    the caller has to guess about.
    """
    base = root if root is not None else projects_dir()
    reference = now if now is not None else datetime.now(timezone.utc)
    cutoff = reference - timedelta(days=window_days)

    if not base.is_dir():
        return TokenUsageUnavailable(reason="no_transcripts")

    project_dirs = sorted(p for p in base.iterdir() if p.is_dir())
    if not project_dirs:
        return TokenUsageUnavailable(reason="no_transcripts")

    # One dedup set spans all projects: a message.id/requestId pair is globally
    # unique, so a resumed session copied under two dirs is still counted once.
    seen: set[str] = set()
    ranked: list[ProjectTokens] = []
    for project_dir in project_dirs:
        tokens = _sum_project(project_dir, cutoff, seen)
        if tokens > 0:
            label = project_dir.name.lstrip("-") or project_dir.name
            ranked.append(ProjectTokens(project=label, tokens=tokens))

    if not ranked:
        return TokenUsageUnavailable(reason="no_recent_activity")

    ranked.sort(key=lambda pt: pt.tokens, reverse=True)
    return ranked
