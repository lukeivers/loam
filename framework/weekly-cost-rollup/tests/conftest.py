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

"""Path bootstrap + shared stubs + a transcript-fixture builder for the AC suites.

The AC tests drive the REAL entry points (``run_rollup``, the real transcript
parser, the install renderer) and inject only the boundaries an unattended build
must not hit live: the sealed usage probe (real network + keychain) and the
channel delivery. The token parser is exercised for real against a fixture
``~/.claude/projects``-shaped directory this builder assembles.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # framework/weekly-cost-rollup/
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from loam.usage_window_guard import (  # noqa: E402
    UnavailableReason,
    UsageUnavailable,
    UsageWindows,
    Window,
)


def windows_at(seven_day_pct: float, five_hour_pct: float = 0.0) -> UsageWindows:
    """Build a UsageWindows with the given seven_day (weekly) utilization.

    five_hour is set low and distinct so a test proves the roll-up reads the
    WEEKLY window, never the 5-hour throttle.
    """
    resets = datetime(2026, 7, 15, tzinfo=timezone.utc)
    return UsageWindows(
        five_hour=Window(utilization=five_hour_pct, resets_at=resets),
        seven_day=Window(utilization=seven_day_pct, resets_at=resets),
    )


def probe_returning(result):
    """A zero-arg probe stub returning ``result``."""
    return lambda: result


def unavailable(reason: UnavailableReason, detail: str = "") -> UsageUnavailable:
    return UsageUnavailable(reason=reason, detail=detail)


class CapturingNotify:
    """An injectable notify_fn that records every message it is handed."""

    def __init__(self) -> None:
        self.messages: list[str] = []

    def __call__(self, message: str) -> None:
        self.messages.append(message)

    @property
    def called(self) -> bool:
        return bool(self.messages)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_transcript(
    projects_root: Path,
    project: str,
    *,
    entries: list[dict],
) -> Path:
    """Write one project's session .jsonl under a fixture projects root.

    Each ``entry`` is ``{tokens, message_id, request_id, timestamp?}`` and is
    rendered as a real Claude-Code assistant transcript line carrying a
    ``message.usage`` block, so the REAL parser (dedup + window) is exercised.
    ``tokens`` is split across the four usage fields so their sum equals it.
    """
    project_dir = projects_root / project
    project_dir.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    for i, entry in enumerate(entries):
        tokens = int(entry["tokens"])
        # Split across the four summed fields (sum == tokens).
        usage = {
            "input_tokens": tokens - (tokens // 4) * 3,
            "output_tokens": tokens // 4,
            "cache_creation_input_tokens": tokens // 4,
            "cache_read_input_tokens": tokens // 4,
        }
        record = {
            "type": "assistant",
            "timestamp": entry.get("timestamp", _now_iso()),
            "requestId": entry.get("request_id", f"req-{project}-{i}"),
            "message": {
                "role": "assistant",
                "id": entry.get("message_id", f"msg-{project}-{i}"),
                "usage": usage,
            },
        }
        lines.append(json.dumps(record))
    session_file = project_dir / "session-0.jsonl"
    session_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return session_file
