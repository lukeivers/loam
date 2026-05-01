"""T4 + T14 — CLI routing and help."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from loam_amend.cli import main


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
    # Post-M1g: ``loam amend --version`` reports ``loam amend
    # <version>``. The unified ``loam`` top-level CLI registers
    # ``--version`` at top-level too (``loam --version`` reports
    # ``loam <version>``); this test verifies the amend subcommand's
    # standalone --version surface.
    with pytest.raises(SystemExit):
        main(["--version"])
    out = capsys.readouterr().out
    assert "loam amend" in out


def test_console_script_available() -> None:
    """The pip-installed console script resolves to our main().

    Post-M1g: the registered console script is ``loam`` (not
    ``loam amend``). ``python -m loam_cli --version`` invokes the
    top-level dispatcher's --version surface.
    """
    result = subprocess.run(
        [sys.executable, "-m", "loam_cli", "--version"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "loam" in result.stdout
