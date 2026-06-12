"""AC.GFLOOR.4 — the floor has no bypass.

Per ``docs/plans/seal-guard-sweep-floor.md`` §4 + D-GFLOOR.3: the
finalize-mode seal exposes no flag or parameter that skips the
GUARD-SWEEP FLOOR. ``--scoped-sweep`` is removed from the CLI
(argparse rejects it loudly) and ``scoped_sweep`` from the seal API.
(``--no-finalize`` remains the documented pre-extension legacy mode —
the named residual per the plan; it is out of this AC's scope.)
"""

from __future__ import annotations

import inspect

import pytest

from loam_amend.cli import main as cli_main
from loam_amend.commands import seal as seal_cmd


def test_AC_GFLOOR_4_cli_rejects_scoped_sweep() -> None:
    """argparse rejects the removed ``--scoped-sweep`` flag."""
    with pytest.raises(SystemExit) as excinfo:
        cli_main(["seal", "--scoped-sweep", "whatever.manifest.yaml"])
    assert excinfo.value.code == 2  # argparse usage-error exit code


def test_AC_GFLOOR_4_seal_api_has_no_scoped_sweep_parameter() -> None:
    """Neither the public ``run`` nor the internal ``_finalize``
    accepts a sweep-scoping parameter."""
    assert "scoped_sweep" not in inspect.signature(seal_cmd.run).parameters
    assert (
        "scoped_sweep"
        not in inspect.signature(seal_cmd._finalize).parameters
    )
