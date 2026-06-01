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

"""The ``loam flow`` production verb — driven through the REAL unified
CLI dispatcher (``loam_cli.cli.main``), the same path ``loam flow ...``
runs at the shell.

This proves the format + pause checks surface through the operator-facing
entry-point (AC.FLOWDEF.3 / AC.PAUSE.1 / AC.PAUSE.2 through the real
verb), not just the library functions. The verb is registered via the
``loam.cli.subcommands`` entry-point group; when the package is installed
the dispatcher discovers it. When discovery does not surface it (e.g. the
test interpreter has not installed the editable package's entry-points),
the test registers the builder onto a real ``loam`` parser directly —
the same callable entry-point discovery would invoke — so the verb's
real argparse surface + dispatch funcs are exercised either way.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from loam_cli.flows.cli import build_flow_subcommand

REPO_ROOT = Path(__file__).resolve().parents[4]
FLOW_DEF = REPO_ROOT / "docs" / "flows" / "loam-vnext-build.flow.md"


def _run_flow(argv: list[str]) -> int:
    """Run ``loam flow ...`` through the real dispatcher.

    Tries the production ``loam_cli.cli.main`` (entry-point discovery)
    first; if the ``flow`` verb is not discovered in this interpreter,
    falls back to a real ``loam`` parser with the SAME builder attached
    (the exact callable discovery would invoke)."""
    from loam_cli.cli import main, _discover_subcommand_builders

    discovered = {name for name, _ in _discover_subcommand_builders()}
    if "flow" in discovered:
        return main(argv)

    parser = argparse.ArgumentParser(prog="loam")
    sub = parser.add_subparsers(dest="subcommand", required=True)
    build_flow_subcommand(sub)
    args = parser.parse_args(argv)
    return args.func(args)


def test_flow_validate_verb_accepts_real_dogfood_flow(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``loam flow validate <dogfood>`` exits 0 and reports VALID."""
    rc = _run_flow(["flow", "validate", str(FLOW_DEF)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "VALID" in out
    assert "loam-vnext-build" in out


def test_flow_validate_verb_rejects_malformed(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC.FLOWDEF.3 through the real verb — a malformed flow is rejected
    with a non-zero exit + corrective message."""
    bad = tmp_path / "bad.flow.md"
    bad.write_text(
        "---\nflow: t\nsteps:\n  - id: a\n    transitions: [missing]\n"
        "  - id: b\n    transitions: []\n  - id: c\n    transitions: []\n"
        "---\n# t\nbody.\n",
        encoding="utf-8",
    )
    rc = _run_flow(["flow", "validate", str(bad)])
    out = capsys.readouterr().out
    assert rc == 1
    assert "INVALID" in out
    assert "missing" in out


def test_flow_position_verb_resolves_dogfood(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """AC.PAUSE.1 through the real verb — ``loam flow position`` resolves
    the dogfood cursor + surfaces the position block (exit 0)."""
    rc = _run_flow(
        ["flow", "position", "--repo-root", str(REPO_ROOT)]
    )
    out = capsys.readouterr().out
    assert rc == 0
    assert "POSITION" in out
    assert "INTEGRATE+RECORD" in out


def test_flow_position_verb_pauses_when_no_active_flow(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """AC.PAUSE.2 through the real verb — with no active flow cursor,
    ``loam flow position`` surfaces the PAUSE directive (exit 2)."""
    empty = tmp_path / "empty-repo"
    empty.mkdir()
    rc = _run_flow(["flow", "position", "--repo-root", str(empty)])
    out = capsys.readouterr().out
    assert rc == 2
    assert "PAUSE" in out
