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

"""Opt-in activation surface for the onboarding ritual.

Per v0.2.1 Cycle 1 plan-doc §3 AC.ONBOARD.4 / .6 / .7 / .8: the
question-loop calls one of the activate_* helpers below when the user
selects an "activate now" branch. Each helper composes on existing
v0.1.6 → v0.2.0 surfaces (no re-implementation):

  - :func:`activate_extractor` — subprocess invokes ``loam odd-extract
    <workspace_root>`` per AC.ONBOARD.6 + plan-doc §7 method-decision
    "subprocess invocation; mirrors how loam-init invokes
    bootstrap_new_workspace".

  - :func:`activate_channel_telegram` — composes on
    :class:`framework.telegram_interface.setup_walkthrough.SetupWalkthrough`
    by writing the marker + emitting the OPENING_OFFER prose. The
    walkthrough's resume mechanism (its own ask-only path; G2 Q1
    ruling) handles step-2 onward across subsequent sessions —
    onboarding's responsibility ends at "user opted in; mark setup
    as offered". Per Halt #6.5 + plan-doc §7.

  - :func:`activate_watch_pointer` — writes a one-line note pointing
    at the v0.2.0 Cycle 1 README scheduling section per plan-doc §7.
    No daemon spawn at MVP; v0.2.x can extend to actual cron
    registration.

All activations are idempotent (re-invocation produces no further
state changes once the activation has fired).
"""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal


@dataclass(frozen=True)
class ActivationResult:
    """Result of an activate_* call.

    Attributes:
        kind: Which activation fired ("extractor" / "channel-telegram"
              / "watch-pointer").
        status: "fired" (activation completed), "deferred" (user opted
                to defer), "skipped" (no-op branch), "error" (the
                underlying surface raised; ritual continues).
        notes: One-line note suitable for audit-log entry.
        artefact_path: Path to any artefact the activation produced
                       (e.g., extractor command line; setup-marker
                       path; watch-pointer file).
    """

    kind: str
    status: Literal["fired", "deferred", "skipped", "error"]
    notes: str
    artefact_path: str | None


def activate_extractor(
    workspace_root: Path,
    *,
    language: str,
    extractor_cmd: list[str] | None = None,
) -> ActivationResult:
    """Fire the ODD extractor against ``workspace_root``.

    Per AC.ONBOARD.6 + plan-doc §7. Subprocess invocation; the
    extractor is a separate component (plugins/dev-sdlc/odd-extractor).

    The default command is ``loam odd-extract <workspace_root>`` — the
    canonical CLI verb registered by odd-extractor's pyproject. Tests
    inject a mock command via ``extractor_cmd`` to avoid spawning real
    extractor runs in unit tests.
    """
    cmd = extractor_cmd or ["loam", "odd-extract", str(workspace_root)]
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(workspace_root),
            check=False,
            capture_output=True,
            text=True,
            timeout=300,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return ActivationResult(
            kind="extractor",
            status="error",
            notes=(
                f"extractor command failed: {type(exc).__name__}: {exc}. "
                f"language={language}; cmd={' '.join(cmd)!r}. The ritual "
                f"continues; the user can re-run `loam odd-extract` later."
            ),
            artefact_path=None,
        )
    if proc.returncode == 0:
        return ActivationResult(
            kind="extractor",
            status="fired",
            notes=(
                f"extractor fired against language={language}; "
                f"cmd={' '.join(cmd)!r}; returncode=0."
            ),
            artefact_path=" ".join(cmd),
        )
    return ActivationResult(
        kind="extractor",
        status="error",
        notes=(
            f"extractor exited returncode={proc.returncode}; "
            f"language={language}; cmd={' '.join(cmd)!r}; "
            f"stderr={proc.stderr.strip()[:240]!r}."
        ),
        artefact_path=" ".join(cmd),
    )


def activate_channel_telegram(
    workspace_root: Path,
    *,
    marker_path: Path | None = None,
) -> ActivationResult:
    """Mark Telegram setup as offered + emit the opening prose.

    Per AC.ONBOARD.4 + plan-doc §7 Halt #6.5 resolution: the existing
    :class:`SetupWalkthrough` is a multi-turn / multi-session flow
    (Step 3 literally requires a session restart). Onboarding's
    responsibility is to record the user's opt-in by writing the
    walkthrough's marker file with ``status: offered`` — the
    walkthrough's resume mechanism handles step-1 onward in
    subsequent sessions.

    Composes on the verified ``SetupMarker.write`` API + the
    ``SetupStatus.offered`` enum value (read-only on the public surface).
    """
    # Lazy-import to avoid hard-coupling the workspace-bootstrap
    # component to telegram-interface at import time. The dependency
    # is declared in pyproject.toml; lazy import gives clearer errors
    # on misconfigured environments.
    try:
        from loam.telegram_interface.setup_walkthrough import (
            SetupMarker,
            SetupStatus,
        )
    except ImportError as exc:
        return ActivationResult(
            kind="channel-telegram",
            status="error",
            notes=(
                f"telegram-interface not importable ({exc}); user opted in "
                f"to Telegram but the setup-walkthrough surface is "
                f"unavailable. Manifest field still recorded; the user "
                f"can re-run setup later via `loam onboard --telegram`."
            ),
            artefact_path=None,
        )

    # Recompute the marker path at call time so HOME-monkeypatching
    # in tests honours the override (DEFAULT_MARKER_PATH is frozen at
    # import time inside telegram-interface).
    if marker_path is not None:
        marker = SetupMarker(path=marker_path)
    else:
        marker = SetupMarker(
            path=Path("~/.loam/telegram-setup-offered").expanduser()
        )
    marker.write(status=SetupStatus.offered)
    return ActivationResult(
        kind="channel-telegram",
        status="fired",
        notes=(
            "telegram setup-walkthrough marker written as 'offered'; the "
            "walkthrough's resume mechanism handles step-1 onward in the "
            "next session. The user sees the OPENING_OFFER prose when the "
            "telegram-interface session-two flow next loads."
        ),
        artefact_path=str(marker.path),
    )


def activate_watch_pointer(workspace_root: Path) -> ActivationResult:
    """Write a one-line pointer to the v0.2.0 watch README.

    Per AC.ONBOARD.7 + plan-doc §7 method-decision: "Cycle 1 ships
    pointer; v0.2.x can extend to actual cron registration." MVP
    writes the pointer file so the user has a discoverable trail to
    enable continuous-watch later; no daemon spawn at this cycle.
    """
    pointer_dir = workspace_root / ".loam"
    pointer_dir.mkdir(parents=True, exist_ok=True)
    pointer_path = pointer_dir / "continuous-watch-pointer.md"
    pointer_path.write_text(
        "# Continuous-watch opt-in: enabled at onboarding\n"
        "\n"
        "You opted in to continuous codebase-watch during the onboarding\n"
        "ritual. Cycle 1 ships the pointer; the actual scheduling\n"
        "registration is described in v0.2.0 Cycle 1's README at\n"
        "`plugins/dev-sdlc/odd-extractor/README.md` (continuous-watch\n"
        "section). Run `loam odd-extract <repo> --incremental` to\n"
        "exercise the v0.2.0 Cycle 1 incremental path manually.\n"
    )
    return ActivationResult(
        kind="watch-pointer",
        status="fired",
        notes=(
            "continuous-watch pointer file written at "
            f"{pointer_path!s}; v0.2.x can extend to actual cron "
            "registration."
        ),
        artefact_path=str(pointer_path),
    )
