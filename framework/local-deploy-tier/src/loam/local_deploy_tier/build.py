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

"""AC.LOCAL.C (outcome-altitude) — ``build_local``, the real LOCAL build
entry-point.

This is the production verb a non-technical owner reaches when they say "build
it / is it working" against their LOCAL environment. It composes the tier's
pieces over a real on-disk workspace with no pre-arranged state:

1. Read the additive LOCAL config view (``role`` / ``backing_services``) from
   the workspace's deploy config — the SAME file the sealed floor reads, the
   additive fields it ignores (``local_config``).
2. Run the project's declared independent check as a SUBPROCESS and mint a
   P0-shape Acceptance record from its real verdict — the producer cannot fake
   "done" (``acceptance``, AC.LOCAL.1).
3. Confirm the LOCAL command set exposes no irreversible/prod verb, so the
   sealed floor idles (``command_set``, AC.LOCAL.2).
4. Surface the plain-language backing-service parity gap against the first
   downstream environment, BEFORE any promotion is offered (``parity``,
   AC.LOCAL.3).
5. Render the whole thing as a plain-language status — substance exposed,
   vocabulary adapted (Lens 0).

The deploy boundary is never crossed here (shared-contract §4 / D-SC.6): this
verb builds and verifies LOCALLY and OFFERS nothing remote. Promotion is P2's
distinct, owner-asked action.
"""

from __future__ import annotations

import shlex
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .acceptance import Acceptance, CheckResult, produce_acceptance
from .command_set import (
    enabled_local_verbs,
    local_command_set_is_floor_idle,
    local_set_irreversible_overlap,
)
from .local_config import EnvProfile, LocalConfigView, load_local_config
from .parity import ParityReport, parity_report


# The optional per-workspace LOCAL-tier settings file (the independent check
# command the build runs). Read-only; never written by this tier.
LOCAL_TIER_RELATIVE = (".loam", "local-tier.yaml")


class LocalBuildError(RuntimeError):
    """The LOCAL build could not run (no deploy config / no local env)."""


@dataclass(frozen=True)
class LocalBuildResult:
    """The outcome of a LOCAL build — the Acceptance, the proven-idle command
    set, the parity surface, and the plain-language status."""

    workspace: str
    local_env: str
    acceptance: Acceptance
    floor_idle: bool
    irreversible_overlap: tuple[str, ...]
    enabled_verbs: tuple[str, ...]
    parity: ParityReport | None
    promotion_offered: bool = False
    status_lines: tuple[str, ...] = field(default_factory=tuple)

    def plain_language_status(self) -> str:
        return "\n".join(self.status_lines)


def _read_verify_command(workspace_root: Path) -> str | None:
    path = workspace_root.joinpath(*LOCAL_TIER_RELATIVE)
    if not path.is_file():
        return None
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return None
    cmd = data.get("verify_command")
    if cmd is None:
        return None
    if not isinstance(cmd, str) or not cmd.strip():
        raise LocalBuildError("'verify_command' must be a non-empty string if present")
    return cmd


def _subprocess_check(command: str, cwd: Path) -> CheckResult:
    """Run *command* as a real subprocess and report its verdict from the exit
    code. This is the independent check: ``build_local`` reads the exit status,
    it does not decide pass/fail itself."""
    try:
        proc = subprocess.run(
            shlex.split(command),
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=300,
        )
    except FileNotFoundError as exc:
        return CheckResult(
            passed=False,
            detail=f"the check command could not be run ({exc}).",
        )
    except subprocess.TimeoutExpired:
        return CheckResult(passed=False, detail="the check timed out after 5 minutes.")
    if proc.returncode == 0:
        return CheckResult(passed=True, detail="the project's own check passed.")
    tail = (proc.stderr or proc.stdout or "").strip().splitlines()
    why = tail[-1] if tail else f"exit code {proc.returncode}"
    return CheckResult(passed=False, detail=f"the project's own check failed: {why}")


def _first_downstream(view: LocalConfigView, local_env: EnvProfile) -> EnvProfile | None:
    for env in view.environments:
        if env.name != local_env.name and not env.is_local:
            return env
    return None


def build_local(
    workspace_root: Path,
    *,
    check: "object | None" = None,
) -> LocalBuildResult:
    """Run a LOCAL build against *workspace_root* and return its result.

    *check* may be supplied (a zero-arg callable returning a ``CheckResult``)
    for callers that already hold a verifier; absent, the project's declared
    ``verify_command`` is run as a subprocess. If neither exists the Acceptance
    is an honest negative ("no check declared") — never a fabricated pass."""
    workspace_root = Path(workspace_root)
    view = load_local_config(workspace_root)
    if view is None:
        raise LocalBuildError(
            f"no deploy config under {workspace_root} — the LOCAL tier is inert "
            "without one."
        )
    local_env = view.local_environment()
    if local_env is None:
        raise LocalBuildError(
            "no environment with tier 'local' is declared — nothing to build locally."
        )

    # (1) Independent check -> P0 Acceptance (AC.LOCAL.1).
    if check is not None:
        if not callable(check):
            raise TypeError("check must be a zero-argument callable")
        check_callable = check
    else:
        verify_command = _read_verify_command(workspace_root)
        if verify_command is None:
            def check_callable() -> CheckResult:
                return CheckResult(
                    passed=False,
                    detail=(
                        "no check is declared for this project, so 'done' cannot "
                        "be confirmed yet."
                    ),
                )
        else:
            def check_callable() -> CheckResult:
                return _subprocess_check(verify_command, workspace_root)

    acceptance = produce_acceptance(
        id="AC.LOCAL.BUILD",
        statement=(
            f"the project builds and passes its own check against the LOCAL "
            f"environment '{local_env.name}'"
        ),
        check=check_callable,
        altitude=True,
    )

    # (2) Floor-idle command set (AC.LOCAL.2).
    floor_idle = local_command_set_is_floor_idle()
    overlap = tuple(sorted(local_set_irreversible_overlap()))

    # (3) Parity surface vs the first downstream env (AC.LOCAL.3). Shown BEFORE
    # any promotion is offered — and this verb offers none (D-SC.6).
    downstream = _first_downstream(view, local_env)
    report = parity_report(local_env, downstream) if downstream is not None else None

    status = _render_status(local_env, acceptance, report, floor_idle)

    return LocalBuildResult(
        workspace=str(workspace_root),
        local_env=local_env.name,
        acceptance=acceptance,
        floor_idle=floor_idle,
        irreversible_overlap=overlap,
        enabled_verbs=tuple(sorted(enabled_local_verbs())),
        parity=report,
        promotion_offered=False,
        status_lines=status,
    )


def _render_status(
    local_env: EnvProfile,
    acceptance: Acceptance,
    report: ParityReport | None,
    floor_idle: bool,
) -> tuple[str, ...]:
    lines: list[str] = []
    if acceptance.met:
        lines.append(
            f"Your app built and passed its own check on this machine "
            f"(environment '{local_env.name}'). Nothing here is public."
        )
    else:
        lines.append(
            f"Your app did not pass its check on this machine yet "
            f"(environment '{local_env.name}'): {acceptance.detail}"
        )
    if floor_idle:
        lines.append(
            "Nothing you can do here can damage anything live — the local "
            "environment has no go-live or delete-for-real action."
        )
    if report is not None:
        lines.append("")
        lines.append(report.plain_language_summary())
    return tuple(lines)
