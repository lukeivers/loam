"""AC.D.1.5.4 — Backwards-compat with v1 manifests + substantive
amendments. Pre-D.1.5 behaviour preserved for the common case.

Plan: ``docs/plans/d-migration-1-5.md`` AC.D.1.5.4.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_AC_D_1_5_4_existing_loam_amend_test_suite_still_green() -> None:
    """The pre-D.1.5 loam amend test suite (every test except this
    AC.D.1.5.* family) remains green. Equivalent of AC.D-sa.6's
    regression gate but with D.1.5 changes in place.

    Method: invoke pytest as a subprocess against the existing test
    files, deselecting the new D.1.5 modules. Uses the runtime
    interpreter the parent suite is running under.
    """
    loam_tool_root = Path(__file__).parent.parent
    tests_dir = loam_tool_root / "tests"
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "--ignore",
            str(tests_dir / "test_rename_detection.py"),
            "--ignore",
            str(tests_dir / "test_AC_D_1_5_2_apply_rename_only_skip.py"),
            "--ignore",
            str(tests_dir / "test_AC_D_1_5_3_dry_run_reports.py"),
            "--ignore",
            str(tests_dir / "test_AC_D_1_5_4_backwards_compat.py"),
            "--ignore",
            str(tests_dir / "test_AC_D_1_5_5_cleanup_directives.py"),
            "--ignore",
            # AC.D-sa.6's nested invocation also kicks off pytest in
            # this subprocess context — let it run; its assertion
            # contract is the same as ours, just different ignore set.
            str(tests_dir / "test_seal.py"),
            str(tests_dir),
        ],
        cwd=loam_tool_root,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, (
        "pre-D.1.5 loam amend test suite regressed under D.1.5 changes:\n"
        + proc.stdout
        + proc.stderr
    )
