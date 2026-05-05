# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""AC.ONBOARD.1 — `loam onboard` trigger + LOAM_ONBOARDING_SKIP=1 disable.

Per v0.2.1 Cycle 1 plan-doc §3 AC.ONBOARD.1: optional invocation;
idempotent; LOAM_ONBOARDING_SKIP=1 short-circuits.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import pytest

from loam.workspace_bootstrap.onboarding import (
    SKIP_ENV_VAR,
    run_onboarding,
)
from loam.workspace_bootstrap.onboarding_cli import (
    build_onboard_subcommand,
)


def _scripted_answerer(answers: list[str]):
    iterator = iter(answers)

    def _ask(slug: str, prompt: str) -> str:
        return next(iterator)

    return _ask


def test_skip_env_var_short_circuits(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """LOAM_ONBOARDING_SKIP=1 returns immediately with skipped=True
    and writes no audit-log entries."""
    monkeypatch.setenv(SKIP_ENV_VAR, "1")
    workspace = tmp_path
    (workspace / "bootstrap.yaml").write_text(
        "version: 1\ncontributions: []\n"
    )

    result = run_onboarding(
        workspace,
        answerer=_scripted_answerer([]),
    )

    assert result.skipped is True
    audit_dir = workspace / ".loam" / "audit-log"
    assert not audit_dir.exists() or not list(audit_dir.iterdir())


def test_default_invocation_runs_question_loop(tmp_path: Path) -> None:
    """When SKIP not set, ritual enters the question loop and writes
    audit-log entries (proves the trigger fires)."""
    workspace = tmp_path
    (workspace / "bootstrap.yaml").write_text(
        "version: 1\ncontributions: []\n"
    )
    answers = ["y", "3", "2", "2", "2", "2"]

    result = run_onboarding(
        workspace,
        answerer=_scripted_answerer(answers),
    )

    assert result.skipped is False
    audit_dir = workspace / ".loam" / "audit-log"
    assert audit_dir.exists()
    audit_files = list(audit_dir.iterdir())
    assert audit_files, "audit-log must contain at least one onboarding-*.yaml file"


def test_argparse_subcommand_registers() -> None:
    """`loam onboard` builder registers a subparser with the M6a
    contract (positional path + set_defaults func)."""
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="subcommand")
    build_onboard_subcommand(sub)

    args = parser.parse_args(["onboard", "/tmp/some/workspace"])
    assert args.subcommand == "onboard"
    assert args.path == Path("/tmp/some/workspace")
    assert callable(args.func), "M6a contract: set_defaults(func=...)"
