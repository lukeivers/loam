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

"""The ``loam report`` verb is registered + builds a subparser (AC.BR.1/.4).

Symmetric to ``loam recover``: a deterministic named entry-point a non-tech
user can run. The builder follows the M6a contract (add a named subparser +
set ``args.func``). A bare invocation takes the safe local-fallback default
(zero egress).
"""

from __future__ import annotations

import argparse
from pathlib import Path

from loam.egress_consent.report_cli import build_report_subcommand, main


def test_builder_attaches_report_subparser() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="subcommand", required=True)
    build_report_subcommand(sub)
    # Parsing "report" must resolve a func.
    args = parser.parse_args(["report"])
    assert hasattr(args, "func")


def test_bare_report_run_saves_locally_zero_egress(tmp_path, capsys) -> None:
    out = tmp_path / "loam-report.txt"
    rc = main(
        [
            "--what-doing", "x",
            "--expected", "y",
            "--happened", "it broke",
            "--loam-version", "1.0.1",
            "--out", str(out),
        ]
    )
    assert rc == 0
    assert out.is_file()
    captured = capsys.readouterr().out
    assert "saved your report on your own computer" in captured
    assert "Nothing left your computer" in captured
