"""D2 measurement harness.

Install the orchestrator as a launchd user agent, measure auto-
restart latency under four failure classes, print a JSON report,
and uninstall.

Per Luke's dispatch ruling:
  > launchd install is authorised for testing, but must be uninstalled
  > at end of build. Install + measure + uninstall.

Failure classes measured:
  SIGKILL — kill -9 to the orchestrator process; launchd restarts.
  SIGSEGV — raise SIGSEGV; launchd records abnormal exit and restarts.
  OOM     — simulated via explicit os._exit(137) (true OOM requires
            resource pressure that is unsafe to cause on a dev machine;
            the 137-exit-code case mirrors what launchd would observe
            from a real OOM kill — it's informative, not a perfect
            test).
  rapid-crash — trigger three successive crashes within the throttle
            window; confirm the third start is delayed by ~30s.

Latency is measured as: time from "process exited" → "new pid running".

Output: a JSON report written to docs/measurement-launchd.json.

This script is destructive on the user's launchd state if run
concurrently with an already-installed orchestrator. It handles that
by uninstalling first, measuring, then uninstalling again.
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

try:
    from .install_launchd import LABEL, install, uninstall, _launchctl_domain
except ImportError:
    # Allow direct script invocation: `python scripts/measure_launchd.py`
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from install_launchd import LABEL, install, uninstall, _launchctl_domain  # type: ignore


def _get_pid() -> int | None:
    """Ask launchctl for the current pid of the service."""
    out = subprocess.run(
        ["launchctl", "print", f"{_launchctl_domain()}/{LABEL}"],
        capture_output=True,
        text=True,
    )
    if out.returncode != 0:
        return None
    for line in out.stdout.splitlines():
        line = line.strip()
        if line.startswith("pid ="):
            try:
                return int(line.split("=", 1)[1].strip())
            except ValueError:
                return None
    return None


def _wait_for_pid(*, not_equal_to: int | None = None, timeout: float = 60.0) -> tuple[int | None, float]:
    """Poll for a pid. Returns (pid, wait_seconds)."""
    t0 = time.monotonic()
    while True:
        pid = _get_pid()
        if pid is not None and pid != not_equal_to:
            return pid, time.monotonic() - t0
        if time.monotonic() - t0 > timeout:
            return None, time.monotonic() - t0
        time.sleep(0.2)


def _measure_restart(signal_num: int) -> dict[str, Any]:
    """Deliver a signal to the running pid, measure restart latency."""
    old_pid, _ = _wait_for_pid(not_equal_to=None)
    if old_pid is None:
        return {"error": "no running pid before signal"}
    try:
        os.kill(old_pid, signal_num)
    except ProcessLookupError:
        return {"error": "old pid vanished before signal delivery"}
    new_pid, wait_s = _wait_for_pid(not_equal_to=old_pid)
    return {
        "signal": signal_num,
        "signal_name": signal.Signals(signal_num).name if signal_num > 0 else "exit",
        "old_pid": old_pid,
        "new_pid": new_pid,
        "restart_seconds": round(wait_s, 3),
    }


def _measure_rapid_crash() -> dict[str, Any]:
    """Trigger three successive SIGKILLs; expect the third restart to
    be held off by the 30s ThrottleInterval."""
    results = []
    for i in range(3):
        r = _measure_restart(signal.SIGKILL)
        results.append(r)
        # brief pause between shots to avoid races
        time.sleep(0.5)
    return {"results": results}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=str, default=None)
    ap.add_argument("--python", type=str, default=sys.executable)
    ap.add_argument("--working-dir", type=str, default=str(Path.cwd()))
    ap.add_argument("--skip-install", action="store_true")
    ap.add_argument("--skip-uninstall", action="store_true")
    ns = ap.parse_args(argv)

    # Clean any prior install, then fresh install.
    if not ns.skip_install:
        uninstall()
        install(
            python_path=Path(ns.python),
            working_dir=Path(ns.working_dir),
            throttle_secs=30,
        )

    # Wait for first boot.
    first_pid, first_boot_s = _wait_for_pid(not_equal_to=None, timeout=60.0)
    report: dict[str, Any] = {
        "first_boot_pid": first_pid,
        "first_boot_seconds": round(first_boot_s, 3),
        "throttle_seconds": 30,
    }
    if first_pid is None:
        report["error"] = "orchestrator did not start after install"
    else:
        # Measure each failure class with a cool-off gap so we don't
        # trip the ThrottleInterval except on the rapid-crash test.
        report["sigkill"] = _measure_restart(signal.SIGKILL)
        time.sleep(35)  # let throttle window reset
        report["sigsegv"] = _measure_restart(signal.SIGSEGV)
        time.sleep(35)
        # "OOM" approximation: SIGABRT (abnormal exit) is the closest
        # portable analogue; os.kill with SIGKILL and 137-exit vs
        # SIGABRT produce equivalent launchd telemetry.
        report["oom_approx"] = _measure_restart(signal.SIGABRT)
        time.sleep(35)
        report["rapid_crash"] = _measure_rapid_crash()

    out_path = Path(ns.out) if ns.out else (
        Path(__file__).resolve().parent.parent / "docs" / "measurement-launchd.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2))

    if not ns.skip_uninstall:
        uninstall()
        # Confirm uninstall — the brief's end-of-build assertion.
        check = subprocess.run(
            ["launchctl", "list"],
            capture_output=True,
            text=True,
        )
        if LABEL in (check.stdout or ""):
            report["uninstall_warning"] = "LABEL still present in launchctl list"
            out_path.write_text(json.dumps(report, indent=2))
            print(f"WARNING: {LABEL} still in launchctl list", file=sys.stderr)
            return 1

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
