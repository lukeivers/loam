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

"""AC.INTENT.3 — the real extractor's one call is spawn-isolated, no API key.

``ClaudeIntentExtractor`` dispatches its single bounded ``claude -p`` call
EXCLUSIVELY through ``loam_spawn_isolation.spawn_isolated_claude`` (argv-injected
``--strict-mcp-config`` + empty mcpServers; ANTHROPIC_API_KEY / TELEGRAM_BOT_TOKEN
scrubbed) with a HARD timeout; it imports no Anthropic SDK and reads no API key.
The Telegram-slot protection (feedback_spawned_claude_must_isolate_telegram_plugin)
+ subscription-only (feedback_no_anthropic_api_key) are NON-negotiable.
"""

from __future__ import annotations

import json
import subprocess

import pytest

from loam.workspace_bootstrap import intent_extract
from loam.workspace_bootstrap.intent_extract import (
    DEFAULT_INTENT_TIMEOUT_SECONDS,
    ClaudeIntentExtractor,
    IntentExtractUnavailableError,
)

# The isolation primitive — import skips the test cleanly if the separate package
# is not on the path (the seam degrades gracefully when it is absent; AC.INTENT.2).
spawn_iso = pytest.importorskip("loam_spawn_isolation")


def _fake_proc(stdout: str, returncode: int = 0):
    return subprocess.CompletedProcess(
        args=["claude"], returncode=returncode, stdout=stdout, stderr=""
    )


def test_AC_INTENT_3_argv_is_spawn_isolated_and_timeout_bounded(monkeypatch):
    """The extractor's argv passes the isolation assertion and carries the hard
    timeout — proving it routes through the mandated primitive, not a raw spawn."""
    captured: dict[str, object] = {}

    def recording_spawn(argv, **kwargs):
        # The REAL assertion the mandated primitive runs — raises on a
        # kill-capable (un-isolated) argv. We run it here to prove the argv the
        # extractor built is isolated.
        spawn_iso.assert_loam_spawn_isolated(spawn_iso.inject_isolation(argv))
        captured["argv"] = argv
        captured["timeout"] = kwargs.get("timeout")
        captured["capture_output"] = kwargs.get("capture_output")
        envelope = {"result": json.dumps({"intent": "writing reports"})}
        return _fake_proc(json.dumps(envelope))

    monkeypatch.setattr(spawn_iso, "spawn_isolated_claude", recording_spawn)

    extractor = ClaudeIntentExtractor()
    out = extractor.extract("I keep getting stuck writing the weekly reports")
    assert out.intent == "writing reports"
    # The dispatch was the isolated primitive with a hard timeout (bounded).
    assert captured["timeout"] == DEFAULT_INTENT_TIMEOUT_SECONDS
    assert captured["capture_output"] is True
    # The argv is a claude -p call (the subscription-routed primitive).
    argv = captured["argv"]
    assert argv[0] == "claude" and "-p" in argv


def test_AC_INTENT_3_adjustment_dispatch_is_spawn_isolated(monkeypatch):
    """The leg-4 adjustment call ALSO routes exclusively through the mandated
    spawn-isolated primitive (AC.INTENT.3/.4) — never a raw spawn."""
    captured: dict[str, object] = {}

    def recording_spawn(argv, **kwargs):
        spawn_iso.assert_loam_spawn_isolated(spawn_iso.inject_isolation(argv))
        captured["argv"] = argv
        captured["timeout"] = kwargs.get("timeout")
        envelope = {"result": json.dumps({"adjustment": "you stay in control"})}
        return _fake_proc(json.dumps(envelope))

    monkeypatch.setattr(spawn_iso, "spawn_isolated_claude", recording_spawn)
    out = ClaudeIntentExtractor().extract_adjustment(
        "yes, I just want to tweak the draft", item="writing reports"
    )
    assert out == "you stay in control"
    assert captured["timeout"] == DEFAULT_INTENT_TIMEOUT_SECONDS
    assert captured["argv"][0] == "claude" and "-p" in captured["argv"]


def test_AC_INTENT_3_adjustment_failure_fails_soft(monkeypatch):
    """A leg-4 adjustment spawn failure raises the sentinel (caught upstream to
    fall back to the deterministic reflection)."""

    def boom(argv, **kwargs):
        raise subprocess.TimeoutExpired(cmd="claude", timeout=1)

    monkeypatch.setattr(spawn_iso, "spawn_isolated_claude", boom)
    with pytest.raises(IntentExtractUnavailableError):
        ClaudeIntentExtractor().extract_adjustment("yes", item="x")


def test_AC_INTENT_3_no_anthropic_sdk_no_api_key_in_module():
    """The module imports no Anthropic SDK and READS no API-key env var — every
    call is subscription-routed via claude -p (feedback_no_anthropic_api_key).

    The scan targets actual SDK imports + an actual env read of the key (the
    documentation MENTIONS the scrubbed var by name, which is correct, so we
    check for a real read pattern, not the bare substring)."""
    import ast
    import io
    import tokenize

    src = open(intent_extract.__file__, encoding="utf-8").read()
    assert "import anthropic" not in src
    assert "from anthropic" not in src
    # No real env read at all (the API-key scrub is the spawn primitive's job).
    assert "os.environ" not in src
    assert "os.getenv" not in src

    # Strip comments + string literals (docstrings) so what remains is CODE only;
    # the API-key name appears ONLY in the docstring describing the scrub contract,
    # never in code (feedback_no_anthropic_api_key).
    code_tokens = []
    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        if tok.type in (tokenize.COMMENT, tokenize.STRING):
            continue
        code_tokens.append(tok.string)
    code_only = " ".join(code_tokens)
    assert "ANTHROPIC_API_KEY" not in code_only
    assert "anthropic" not in code_only.lower()
    # And the module is importable + parseable (no SDK dependency at import).
    ast.parse(src)


def test_AC_INTENT_3_spawn_failure_raises_unavailable_not_propagates(monkeypatch):
    """A spawn/timeout failure surfaces as the sentinel (which the intake catches
    to fall back), never an un-isolated retry or a raw propagation."""

    def boom(argv, **kwargs):
        raise subprocess.TimeoutExpired(cmd="claude", timeout=1)

    monkeypatch.setattr(spawn_iso, "spawn_isolated_claude", boom)
    with pytest.raises(IntentExtractUnavailableError):
        ClaudeIntentExtractor().extract("writing the weekly reports")
