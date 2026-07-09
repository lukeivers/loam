# Copyright 2026 Luke Ivers and contributors
# SPDX-License-Identifier: Apache-2.0
"""AC.CDX.3 (WS-D2) — the leg's subprocess env carries no inherited API key
beyond what D2's ruling grants (none, under ChatGPT sign-in): the ``env=``
actually handed to ``subprocess.run`` has no ``OPENAI_API_KEY`` and no
``ANTHROPIC_API_KEY``, while ``HOME``/``PATH`` (needed for the file-based
sign-in credential lookup) survive.

The high-altitude assertion captures the env at the REAL process boundary
(``run_codex_critic`` -> ``subprocess.run``); a direct ``codex_env`` unit
assertion covers the ``allow_openai_key`` metered-key relaxation (D2's escape
hatch, scoped to this subprocess only)."""
from __future__ import annotations

import subprocess

from adversarial_review import codex


def test_AC_CDX_3_spawn_env_scrubs_api_keys(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-should-be-scrubbed")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-should-be-scrubbed")
    monkeypatch.setenv("ANTHROPIC_AUTH_TOKEN", "tok-should-be-scrubbed")
    monkeypatch.setenv("HOME", "/Users/operator")
    monkeypatch.setenv("PATH", "/usr/bin:/bin")
    monkeypatch.setattr(codex.shutil, "which", lambda _bin: "/usr/local/bin/codex")

    captured: dict = {}

    def _fake_run(argv, **kwargs):
        captured["env"] = kwargs.get("env")
        return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")

    monkeypatch.setattr(codex.subprocess, "run", _fake_run)

    # Return value is None (empty stdout) — irrelevant here; we assert the env.
    codex.run_codex_critic("review this")

    env = captured["env"]
    assert env is not None, "the leg must pass an explicit scrubbed env"
    assert "OPENAI_API_KEY" not in env
    assert "ANTHROPIC_API_KEY" not in env
    assert "ANTHROPIC_AUTH_TOKEN" not in env
    # Sign-in is file-based — the child still needs these.
    assert env.get("HOME") == "/Users/operator"
    assert env.get("PATH") == "/usr/bin:/bin"


def test_AC_CDX_3_default_env_scrubs_openai_key():
    env = codex.codex_env(
        base_env={
            "OPENAI_API_KEY": "sk-x",
            "ANTHROPIC_API_KEY": "sk-ant",
            "HOME": "/h",
            "PATH": "/b",
        }
    )
    assert "OPENAI_API_KEY" not in env
    assert "ANTHROPIC_API_KEY" not in env
    assert env["HOME"] == "/h"
    assert env["PATH"] == "/b"


def test_AC_CDX_3_allow_openai_key_relaxes_scrub_for_this_subprocess_only():
    # D2's metered-key escape hatch: relaxed ONLY when explicitly enabled.
    env = codex.codex_env(
        allow_openai_key=True,
        base_env={"OPENAI_API_KEY": "sk-x", "ANTHROPIC_API_KEY": "sk-ant"},
    )
    assert env["OPENAI_API_KEY"] == "sk-x"
    # Anthropic keys are still scrubbed regardless — no business in codex.
    assert "ANTHROPIC_API_KEY" not in env


def test_AC_CDX_3_codex_leg_binds_allow_flag_into_fn(monkeypatch):
    # allow_openai_key=True on the leg factory reaches the subprocess env.
    monkeypatch.setenv("OPENAI_API_KEY", "sk-metered")
    monkeypatch.setattr(codex.shutil, "which", lambda _bin: "/usr/local/bin/codex")
    captured: dict = {}

    def _fake_run(argv, **kwargs):
        captured["env"] = kwargs.get("env")
        return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")

    monkeypatch.setattr(codex.subprocess, "run", _fake_run)

    leg = codex.codex_leg(allow_openai_key=True)
    leg.fn("review this")
    assert captured["env"].get("OPENAI_API_KEY") == "sk-metered"
