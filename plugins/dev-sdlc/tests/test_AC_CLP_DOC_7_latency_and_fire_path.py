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

"""AC.CLP-DOC.7 — the check adds no observable latency cost outside its
target.

Three claims:
  1. Matcher-scoped: the hook is registered with matcher ``Task``, so
     non-Agent tool calls never invoke it (Claude Code's matcher
     primitive does the scoping). Verified against the registered
     stanza builder + a no-op on a non-Task tool.
  2. The fire path performs NO network I/O and NO LLM invocation —
     verified by source-audit (the fire path imports no http/socket/
     subprocess/claude module) AND a runtime guard that fails if the
     fire path tries to open a socket.
  3. A standalone fire on a representative envelope completes within
     100 ms p95: ≥20 timed in-process ``evaluate`` fires; assert p95.
"""

from __future__ import annotations

import io
import json
import socket
import sys
import time
import types
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
HOOKS_DIR = REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks"
PLUGIN_HOOKS_DIR = REPO_ROOT / "plugins" / "dev-sdlc" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))
sys.path.insert(0, str(PLUGIN_HOOKS_DIR))

HOOK_SRC = (PLUGIN_HOOKS_DIR / "primitive_check_guard.py").read_text(
    encoding="utf-8"
)
MATCHERS_SRC = (
    PLUGIN_HOOKS_DIR / "primitive_check_matchers.py"
).read_text(encoding="utf-8")


def _stub_dev_mode(monkeypatch) -> None:
    cls_mod = types.ModuleType("corpus_load_sentinel")
    cls_mod.workspace_mode = lambda _: "dev-mode"
    monkeypatch.setitem(sys.modules, "corpus_load_sentinel", cls_mod)


# ----- claim 1: matcher-scoped -----


def test_AC_CLP_DOC_7_registered_matcher_is_task() -> None:
    """The first-run wiring registers the guard with matcher ``Task``
    (so it fires only on Agent dispatch, zero cost to other tools)."""
    import first_run_helper

    stanza = first_run_helper._primitive_check_guard_stanza(REPO_ROOT)
    assert stanza["matcher"] == "Task", (
        f"primitive-check guard must be Task-scoped; got "
        f"{stanza['matcher']!r}"
    )


def test_AC_CLP_DOC_7_non_task_tool_is_no_op(monkeypatch) -> None:
    _stub_dev_mode(monkeypatch)
    import primitive_check_guard as guard

    monkeypatch.setattr(
        guard._helpers,
        "read_workspace_mode_or_normal_use",
        lambda _: "dev-mode",
    )
    decision = guard.evaluate(
        workspace_root=Path("/tmp"),
        tool_name="Bash",
        tool_input={"prompt": "build a scheduler cron job"},
    )
    assert decision.decision == "no-op"


# ----- claim 2: no network / no LLM on the fire path -----


def test_AC_CLP_DOC_7_fire_path_imports_no_network_or_llm() -> None:
    """Source-audit: neither the hook nor the matcher data imports a
    network / HTTP / LLM-client module on the fire path."""
    forbidden = (
        "import socket",
        "import http",
        "import urllib",
        "import requests",
        "claude_print_client",
        "anthropic",
        "import subprocess",
    )
    for token in forbidden:
        assert token not in HOOK_SRC, (
            f"primitive_check_guard fire path must not reference "
            f"{token!r} (AC.CLP-DOC.7: no network / no LLM / no "
            f"subprocess on the fire path)"
        )
        assert token not in MATCHERS_SRC, (
            f"primitive_check_matchers must not reference {token!r}"
        )


def test_AC_CLP_DOC_7_fire_path_opens_no_socket(monkeypatch) -> None:
    """Runtime guard: a fire raises nothing AND opens no socket. We
    replace socket.socket with a tripwire and run a fire."""
    _stub_dev_mode(monkeypatch)
    import primitive_check_guard as guard

    monkeypatch.setattr(
        guard._helpers,
        "read_workspace_mode_or_normal_use",
        lambda _: "dev-mode",
    )

    def _tripwire(*a, **k):
        raise AssertionError(
            "fire path opened a socket — AC.CLP-DOC.7 forbids network "
            "I/O on the fire path"
        )

    monkeypatch.setattr(socket, "socket", _tripwire)
    decision = guard.evaluate(
        workspace_root=Path("/tmp"),
        tool_name="Task",
        tool_input={
            "prompt": "Build a cron scheduler that runs every weekday."
        },
    )
    assert decision.decision == "deny"


# ----- claim 3: p95 latency <= 100 ms over >=20 fires -----


def test_AC_CLP_DOC_7_p95_latency_under_100ms(tmp_path, monkeypatch) -> None:
    """≥20 standalone fixture fires through the production main() path;
    p95 wall-time ≤ 100 ms. Measured, not asserted."""
    _stub_dev_mode(monkeypatch)
    import primitive_check_guard as guard

    monkeypatch.setattr(
        guard._helpers,
        "read_workspace_mode_or_normal_use",
        lambda _: "dev-mode",
    )

    envelope = {
        "cwd": str(tmp_path),
        "tool_name": "Task",
        "tool_input": {
            "prompt": (
                "Build a polling loop that re-checks the deploy every "
                "hour and reports when it goes green. " + ("x" * 1500)
            )
        },
    }
    raw = json.dumps(envelope)

    durations: list[float] = []
    n = 30
    for _ in range(n):
        monkeypatch.setattr(sys, "stdin", io.StringIO(raw))
        monkeypatch.setattr(sys, "stdout", io.StringIO())
        t0 = time.perf_counter()
        guard.main()
        durations.append((time.perf_counter() - t0) * 1000.0)

    durations.sort()
    p95 = durations[int(0.95 * (len(durations) - 1))]
    # Report the measured numbers in the assertion message so the seal
    # log carries them.
    assert p95 <= 100.0, (
        f"AC.CLP-DOC.7 p95 latency {p95:.3f} ms exceeds the 100 ms "
        f"bound (n={n}, min={durations[0]:.3f} ms, "
        f"max={durations[-1]:.3f} ms, median="
        f"{durations[len(durations)//2]:.3f} ms)"
    )
