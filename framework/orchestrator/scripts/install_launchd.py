"""Install the orchestrator as a launchd user agent (macOS).

Usage:
    python -m pos_orchestrator.scripts.install_launchd
    python -m pos_orchestrator.scripts.install_launchd --uninstall

Per Luke's brief-ruling for the build dispatch: launchd install is
authorised for D2 measurement only and must be uninstalled at end of
build (see scripts/uninstall_launchd.py). This script is the install
half; the uninstall half is a separate invocation.

The script:
  - renders the plist template with absolute paths
  - writes to ~/Library/LaunchAgents/com.pos.orchestrator.plist
  - bootstraps into launchd (`launchctl bootstrap gui/<uid>`)

It does NOT call kickstart; launchd auto-starts the job at load
because RunAtLoad=true.
"""

from __future__ import annotations

import argparse
import os
import pwd
import string
import subprocess
import sys
from pathlib import Path

LABEL = "com.pos.orchestrator"


def _render_plist(
    *,
    python_path: Path,
    working_dir: Path,
    stdout_log: Path,
    stderr_log: Path,
    throttle_secs: int,
) -> str:
    tmpl_path = Path(__file__).resolve().parent.parent / "ops" / "launchd" / "com.pos.orchestrator.plist.tmpl"
    tmpl = tmpl_path.read_text()
    return string.Template(tmpl).substitute(
        LABEL=LABEL,
        PYTHON=str(python_path),
        WORKING_DIR=str(working_dir),
        STDOUT_LOG=str(stdout_log),
        STDERR_LOG=str(stderr_log),
        THROTTLE_SECS=throttle_secs,
    )


def _plist_install_path() -> Path:
    return Path.home() / "Library" / "LaunchAgents" / f"{LABEL}.plist"


def _launchctl_domain() -> str:
    uid = os.getuid()
    return f"gui/{uid}"


def install(
    *,
    python_path: Path | None = None,
    working_dir: Path | None = None,
    throttle_secs: int = 30,
) -> Path:
    python_path = python_path or Path(sys.executable)
    working_dir = working_dir or Path.cwd()
    log_dir = Path.home() / ".pos" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    stdout_log = log_dir / "orchestrator.out"
    stderr_log = log_dir / "orchestrator.err"

    plist = _render_plist(
        python_path=python_path,
        working_dir=working_dir,
        stdout_log=stdout_log,
        stderr_log=stderr_log,
        throttle_secs=throttle_secs,
    )
    install_path = _plist_install_path()
    install_path.parent.mkdir(parents=True, exist_ok=True)
    install_path.write_text(plist)

    domain = _launchctl_domain()
    subprocess.check_call(
        ["launchctl", "bootstrap", domain, str(install_path)]
    )
    return install_path


def uninstall() -> None:
    install_path = _plist_install_path()
    domain = _launchctl_domain()
    # Best-effort bootout (ignore non-zero on absent).
    subprocess.run(
        ["launchctl", "bootout", f"{domain}/{LABEL}"],
        check=False,
    )
    try:
        install_path.unlink()
    except FileNotFoundError:
        pass


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--uninstall", action="store_true")
    ap.add_argument("--python", type=str, default=None)
    ap.add_argument("--working-dir", type=str, default=None)
    ap.add_argument("--throttle-secs", type=int, default=30)
    ns = ap.parse_args(argv)
    if ns.uninstall:
        uninstall()
        print(f"uninstalled {LABEL}")
        return 0
    path = install(
        python_path=Path(ns.python) if ns.python else None,
        working_dir=Path(ns.working_dir) if ns.working_dir else None,
        throttle_secs=ns.throttle_secs,
    )
    print(f"installed plist at {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
