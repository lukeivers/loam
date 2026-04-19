"""D2 — launchd + systemd-user process supervision (structural tests).

The live launchd measurement step is captured by the
`scripts/measure_launchd.py` harness and recorded in
`docs/measurement-launchd.md`. Per Luke's brief-ruling, the live
install is authorised for measurement and uninstalled at end of
build. The structural tests here verify the plist/unit templates
render correctly with the throttle interval locked at 30s.

Acceptance (structural slice of brief D2):
- launchd plist template renders to a valid plist with KeepAlive=true
  and ThrottleInterval=${THROTTLE_SECS}.
- systemd-user unit template renders to a valid unit with Restart=always
  and RestartSec=${THROTTLE_SECS}.
"""

from __future__ import annotations

import plistlib
import re
import string
import subprocess
import sys
from pathlib import Path

import pytest


_REPO_ROOT = Path(__file__).resolve().parent.parent
_LAUNCHD_TMPL = _REPO_ROOT / "ops" / "launchd" / "com.pos.orchestrator.plist.tmpl"
_SYSTEMD_TMPL = _REPO_ROOT / "ops" / "systemd" / "pos-orchestrator.service.tmpl"


def _render_launchd(**vars: object) -> str:
    return string.Template(_LAUNCHD_TMPL.read_text()).substitute(**vars)


def _render_systemd(**vars: object) -> str:
    return string.Template(_SYSTEMD_TMPL.read_text()).substitute(**vars)


def test_launchd_plist_renders_to_valid_plist():
    rendered = _render_launchd(
        LABEL="com.pos.orchestrator",
        PYTHON="/usr/bin/python3",
        WORKING_DIR="/tmp",
        STDOUT_LOG="/tmp/out",
        STDERR_LOG="/tmp/err",
        THROTTLE_SECS=30,
    )
    data = plistlib.loads(rendered.encode("utf-8"))
    assert data["Label"] == "com.pos.orchestrator"
    assert data["KeepAlive"] is True
    assert data["RunAtLoad"] is True
    assert data["ThrottleInterval"] == 30
    assert data["ProgramArguments"][0] == "/usr/bin/python3"
    assert data["ProgramArguments"][1:3] == ["-m", "pos_orchestrator"]


def test_launchd_throttle_interval_locked_at_30s():
    """Luke's decision: 30 seconds. Any deviation is a policy change."""
    rendered = _render_launchd(
        LABEL="com.pos.orchestrator",
        PYTHON="/usr/bin/python3",
        WORKING_DIR="/tmp",
        STDOUT_LOG="/tmp/out",
        STDERR_LOG="/tmp/err",
        THROTTLE_SECS=30,
    )
    data = plistlib.loads(rendered.encode("utf-8"))
    assert data["ThrottleInterval"] == 30


def test_systemd_unit_renders_with_restart_always():
    rendered = _render_systemd(
        PYTHON="/usr/bin/python3",
        WORKING_DIR="/tmp",
        THROTTLE_SECS=30,
    )
    assert "Restart=always" in rendered
    assert "RestartSec=30" in rendered
    assert "ExecStart=/usr/bin/python3 -m pos_orchestrator" in rendered


def test_systemd_throttle_locked_at_30s():
    rendered = _render_systemd(
        PYTHON="/usr/bin/python3",
        WORKING_DIR="/tmp",
        THROTTLE_SECS=30,
    )
    m = re.search(r"RestartSec=(\d+)", rendered)
    assert m is not None and int(m.group(1)) == 30


@pytest.mark.skipif(sys.platform != "darwin", reason="plutil is macOS-only")
def test_launchd_plist_passes_plutil_validation(tmp_path):
    rendered = _render_launchd(
        LABEL="com.pos.orchestrator",
        PYTHON="/usr/bin/python3",
        WORKING_DIR="/tmp",
        STDOUT_LOG="/tmp/out",
        STDERR_LOG="/tmp/err",
        THROTTLE_SECS=30,
    )
    p = tmp_path / "test.plist"
    p.write_text(rendered)
    out = subprocess.run(
        ["plutil", "-lint", str(p)],
        capture_output=True,
        text=True,
    )
    assert out.returncode == 0, out.stderr or out.stdout
