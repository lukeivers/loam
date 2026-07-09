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

"""The fleet page regenerator scheduler (WS-A3).

The page is refreshed by a **launchd/cron job, NOT a
``.claude/settings.json`` hook** (§5 hard constraint: Track F is the
sole settings.json writer this phase, and a periodic regenerator must
run independent of any main-session Stop event).  This module writes the
scheduling ARTIFACT; installing it is a plain file write plus an
optional ``launchctl load`` the caller runs.

``render_plist(...)`` is pure (string in → plist XML out) so a test can
assert the artifact's shape (AC.PAGE.2a): it references the
``loam.fleet_page render`` command and contains NO reference to
``.claude/settings.json``.  ``install_launchd_job(...)`` writes that
artifact to a target dir (default ``~/Library/LaunchAgents``).
"""

from __future__ import annotations

import sys
from collections.abc import Sequence
from pathlib import Path
from xml.sax.saxutils import escape

DEFAULT_LABEL = "com.loam.fleet-page"
DEFAULT_INTERVAL_S = 300


def render_program_args(
    *,
    out_path: Path | str,
    roots: Sequence[Path | str],
    python: str | None = None,
) -> list[str]:
    """The argv the scheduled job runs: this interpreter, ``-m
    loam.fleet_page render``, absolute ``--out`` and one ``--root`` per
    scanned tree.  Absolute paths only — a launchd job has no useful
    cwd."""
    python = python or sys.executable
    args = [python, "-m", "loam.fleet_page", "render",
            "--out", str(Path(out_path))]
    for root in roots:
        args += ["--root", str(Path(root))]
    return args


def render_plist(
    *,
    out_path: Path | str,
    roots: Sequence[Path | str],
    label: str = DEFAULT_LABEL,
    interval_s: int = DEFAULT_INTERVAL_S,
    python: str | None = None,
) -> str:
    """A launchd LaunchAgent plist that runs the regenerator every
    ``interval_s`` seconds (AC.PAGE.2a).

    References only ``loam.fleet_page`` — never ``.claude/settings.json``
    (the artifact is verifiable proof the regenerator is a launchd job,
    not a hook)."""
    args = render_program_args(out_path=out_path, roots=roots, python=python)
    arg_xml = "\n".join(f"    <string>{escape(a)}</string>" for a in args)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
        '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
        '<plist version="1.0">\n'
        "<dict>\n"
        "  <key>Label</key>\n"
        f"  <string>{escape(label)}</string>\n"
        "  <key>ProgramArguments</key>\n"
        "  <array>\n"
        f"{arg_xml}\n"
        "  </array>\n"
        "  <key>StartInterval</key>\n"
        f"  <integer>{int(interval_s)}</integer>\n"
        "  <key>RunAtLoad</key>\n"
        "  <true/>\n"
        "</dict>\n"
        "</plist>\n"
    )


def install_launchd_job(
    *,
    out_path: Path | str,
    roots: Sequence[Path | str],
    launch_agents_dir: Path | str | None = None,
    label: str = DEFAULT_LABEL,
    interval_s: int = DEFAULT_INTERVAL_S,
    python: str | None = None,
) -> Path:
    """Write the launchd plist artifact and return its path (AC.PAGE.2a).

    Writes to ``launch_agents_dir`` (default ``~/Library/LaunchAgents``).
    Installing is complete once the artifact exists; the caller loads it
    with ``launchctl load <path>`` when ready — this function performs no
    ``launchctl`` side effect of its own."""
    if launch_agents_dir is None:
        launch_agents_dir = Path.home() / "Library" / "LaunchAgents"
    launch_agents_dir = Path(launch_agents_dir)
    launch_agents_dir.mkdir(parents=True, exist_ok=True)
    plist_path = launch_agents_dir / f"{label}.plist"
    plist_path.write_text(
        render_plist(out_path=out_path, roots=roots, label=label,
                     interval_s=interval_s, python=python),
        encoding="utf-8",
    )
    return plist_path


def render_cron_line(
    *,
    out_path: Path | str,
    roots: Sequence[Path | str],
    minutes: int = 5,
    python: str | None = None,
) -> str:
    """A crontab line (non-darwin fallback) running the regenerator every
    ``minutes`` minutes.  Same command as the launchd job; references
    only ``loam.fleet_page``."""
    args = render_program_args(out_path=out_path, roots=roots, python=python)
    return f"*/{int(minutes)} * * * * " + " ".join(args)
