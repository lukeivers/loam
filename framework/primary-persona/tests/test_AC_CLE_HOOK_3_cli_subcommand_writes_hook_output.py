# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""AC.CLE.HOOK.3 — the ``primary_persona.cli intent-classifier``
subcommand reads UserPromptSubmit JSON from stdin and writes valid
hook output JSON to stdout.

Per amendment #144 Scope A: the subcommand is invoked via Claude
Code's UserPromptSubmit hook chain. Integration test invokes it as
a real subprocess, exercising the stdin/stdout JSON envelope
round-trip + exit-code-0 fail-soft contract.
"""

from __future__ import annotations

import json
import subprocess
import sys


def _invoke_intent_classifier(payload: dict) -> subprocess.CompletedProcess:
    """Invoke the intent-classifier CLI as a subprocess with the
    payload JSON on stdin. Returns the CompletedProcess for inspection."""
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "loam.primary_persona.cli",
            "intent-classifier",
        ],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )


def test_cli_emits_hook_output_on_build_with_verification_prompt() -> None:
    """Stdin envelope with a build-with-verification prompt → stdout
    is parseable Claude Code hookSpecificOutput JSON referencing the
    handsoff-loop SKILL + auto-load mechanism."""
    payload = {
        "prompt": "I want a tool that does X. show me it works",
        # Claude Code's UserPromptSubmit hook payload also carries
        # session_id / cwd / etc.; the classifier ignores them but we
        # include a stub to mirror the production envelope shape.
        "session_id": "test-session",
        "cwd": "/tmp/test-workspace",
    }
    result = _invoke_intent_classifier(payload)
    assert result.returncode == 0, (
        f"intent-classifier exited non-zero (stderr: {result.stderr!r})"
    )
    assert result.stdout.strip(), "expected non-empty stdout"
    parsed = json.loads(result.stdout)
    assert parsed["hookEventName"] == "UserPromptSubmit"
    inner = parsed["hookSpecificOutput"]
    assert "additionalContext" in inner
    body = inner["additionalContext"]
    assert "handsoff-loop" in body
    assert "auto-load" in body.lower()


def test_cli_emits_empty_stdout_on_pure_question_prompt() -> None:
    """Stdin envelope with a pure-question prompt → no injection;
    stdout is empty; exit code 0 (fail-soft pass-through)."""
    payload = {
        "prompt": "what does this function do",
        "session_id": "test-session",
    }
    result = _invoke_intent_classifier(payload)
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_cli_exits_zero_on_empty_stdin() -> None:
    """Empty stdin → exit 0, empty stdout (Claude Code's fan-out
    contract: a non-zero exit blocks the hook chain)."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "loam.primary_persona.cli",
            "intent-classifier",
        ],
        input="",
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_cli_exits_zero_on_non_json_stdin() -> None:
    """Non-JSON stdin → exit 0, empty stdout (fail-soft)."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "loam.primary_persona.cli",
            "intent-classifier",
        ],
        input="this is not JSON, just plain text",
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_cli_exits_zero_on_missing_prompt_field() -> None:
    """Stdin envelope without a 'prompt' field → exit 0, empty stdout."""
    payload = {"session_id": "test-session", "cwd": "/tmp/test"}
    result = _invoke_intent_classifier(payload)
    assert result.returncode == 0
    assert result.stdout.strip() == ""
