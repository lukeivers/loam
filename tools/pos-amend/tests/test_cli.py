"""T4 + T14 — CLI routing and help."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from pos_amend.cli import main


FIXTURES = Path(__file__).parent / "fixtures"


def test_T4_validate_exits_zero_on_valid(capsys) -> None:
    rc = main(["validate", str(FIXTURES / "valid-minimal.yaml")])
    assert rc == 0
    out = capsys.readouterr().out
    assert "amendment #99" in out


def test_T4_validate_exits_nonzero_on_invalid(capsys) -> None:
    rc = main(["validate", str(FIXTURES / "invalid-unknown-schema-version.yaml")])
    assert rc == 2
    out = capsys.readouterr().out
    assert "invalid" in out


def test_T14_help_lists_subcommands(capsys) -> None:
    with pytest.raises(SystemExit):
        main(["--help"])
    out = capsys.readouterr().out
    assert "validate" in out
    assert "apply" in out
    assert "seal" in out


def test_T14_version_reports_version(capsys) -> None:
    with pytest.raises(SystemExit):
        main(["--version"])
    out = capsys.readouterr().out
    assert "pos-amend" in out


def test_console_script_available() -> None:
    """The pip-installed console script resolves to our main()."""
    result = subprocess.run(
        [sys.executable, "-m", "pos_amend", "--version"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "pos-amend" in result.stdout
