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

"""AC.TPI.6 — the §1a already-isolated sites and §1c non-`claude`
sites are unchanged by the fix (fence integrity — no no-op churn, no
scope creep).

Plan: docs/plans/telegram-poller-isolation-fix.md
Contract: pos3/.../telegram-isolation-fix-plan-2026-05-16.md §1a / §1c
/ §3.3.  Satisfiable trivially by fence discipline; falsifiable by a
diff touching the §1a/§1c files.

The diff window is BASELINE..SEAL_COMMIT — bounded at BOTH ends.  The
BASELINE is the manifest's pre-apply tip; the upper bound is THIS
amendment's seal commit (read via the SEAL_COMMIT-sidecar pattern the
sibling fence tests — protection-matrix / workspace-bootstrap — use:
sidecar SHA if present, else the pinned seal SHA, else HEAD pre-seal).
The seal-commit UPPER bound is load-bearing for DURABILITY: without it
the window ran ``BASELINE..HEAD`` and swept in every later unrelated
amendment, so once a post-seal amendment touched a fenced §1a/§1c file
(e.g. 2edf2f43 touched first_run_dispatch.py) the fence falsely
tripped.  Bounding at the seal makes the fence permanent — only THIS
amendment's deltas are ever in scope.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
_MANIFEST = (
    REPO_ROOT / "docs" / "plans" / "sealed"
    / "telegram-poller-isolation-fix.manifest.yaml"
)

# Upper bound of the fence diff window — this amendment's seal commit.
# Mirrors the SEAL_COMMIT-sidecar pattern the sibling fence tests
# (protection-matrix / workspace-bootstrap) use: read the sidecar SHA
# if present, else the pinned seal SHA below, else HEAD (pre-seal, so a
# build on an unfinished seal still exercises the test).  Bounding at
# the seal (instead of HEAD) keeps the fence DURABLE — later unrelated
# amendments that touch a §1a/§1c file can never fall inside the window.
SEAL_COMMIT_PATH = Path(__file__).parent / "SEAL_COMMIT"
_SEAL_COMMIT = "e0b71cbc"


def _seal_commit() -> str:
    """Resolve the diff-window upper bound: sidecar SHA, else the
    pinned seal SHA, else HEAD."""
    if SEAL_COMMIT_PATH.exists():
        txt = SEAL_COMMIT_PATH.read_text().strip()
        if txt and txt != "HEAD":
            return txt
    return _SEAL_COMMIT or "HEAD"

# Contract §1a — ALREADY isolated `claude`-spawn sites (NOT this fix's
# target; touching them is no-op churn / scope creep).
_FENCE_1A = (
    "framework/tools/subloam-driver/src/subloam_driver/driver.py",
    "framework/tools/upgrade-merge-resolver/src/loam/"
    "upgrade_merge_resolver/__init__.py",
    "framework/workspace-sync/src/loam/workspace_sync/"
    "_resolver_client.py",
    "plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/"
    "claude_print_synthesis_client.py",
)

# Contract §1c — non-`claude` subprocess sites (ruled out so the fence
# is exact; not kill-vector sites; untouched).
_FENCE_1C = (
    "framework/hands-off-lifecycle/hooks/first_run_dispatch.py",
    "framework/hands-off-lifecycle/hooks/first_run_helper.py",
    "framework/tools/handsoff-loop/src/handsoff_loop/verify.py",
)


def _baseline() -> str:
    """Read the BASELINE the manifest pins (the commit immediately
    preceding this amendment's source-edit commit)."""
    for line in _MANIFEST.read_text().splitlines():
        s = line.strip()
        if s.startswith("baseline:"):
            return s.split(":", 1)[1].strip().strip('"').strip("'")
    raise AssertionError("manifest carries no baseline")


def _changed_paths() -> list[str]:
    baseline = _baseline()
    seal = _seal_commit()
    out = subprocess.check_output(
        ["git", "diff", "--name-only", f"{baseline}..{seal}"],
        cwd=REPO_ROOT,
        text=True,
    )
    return [ln for ln in out.splitlines() if ln.strip()]


@pytest.mark.parametrize("fenced", [*_FENCE_1A, *_FENCE_1C])
def test_AC_TPI_6_fenced_site_unchanged(fenced: str) -> None:
    """No §1a (already-isolated) or §1c (non-`claude`) site appears in
    this amendment's diff window — the fix touches §1b only."""
    changed = _changed_paths()
    assert fenced not in changed, (
        f"OUT-OF-FENCE: {fenced!r} was modified by this amendment. "
        f"The fix is §1b-only; §1a/§1c are forbidden to touch "
        f"(AC.TPI.6). Changed: {changed}"
    )


def test_AC_TPI_6_only_1b_handsoff_sources_changed() -> None:
    """Affirmative side: the only `handsoff_loop` source files in the
    diff window are the three §1b launch sites + the new isolation
    helper — no other handsoff-loop source is churned."""
    changed = _changed_paths()
    hl_src_prefix = (
        "framework/tools/handsoff-loop/src/handsoff_loop/"
    )
    hl_sources = [
        p for p in changed
        if p.startswith(hl_src_prefix) and p.endswith(".py")
    ]
    allowed = {
        hl_src_prefix + "intake.py",
        hl_src_prefix + "goal_drive.py",
        hl_src_prefix + "orchestrator.py",
        hl_src_prefix + "_isolation.py",
    }
    unexpected = sorted(set(hl_sources) - allowed)
    assert unexpected == [], (
        f"unexpected handsoff-loop source churn beyond the §1b "
        f"sites + isolation helper: {unexpected}"
    )
