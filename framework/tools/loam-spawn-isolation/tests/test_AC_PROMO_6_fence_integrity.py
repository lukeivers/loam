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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.  See the License for the specific language governing
# permissions and limitations under the License.

"""AC.PROMO.6 — the §1a / §1b / §1c already-isolated (or non-`claude`)
sites are BYTE-UNCHANGED by this fix (fence integrity — no no-op
churn, no scope creep; the promote ADDS a shared surface, it does NOT
re-wire the proven sites).

Plan: docs/plans/telegram-5-fix.md §1a / §1b / §1c / §3.2 OUT / §3.3
(plan pair archived under docs/plans/sealed/ by amendment #143).
Satisfiable trivially by fence discipline; falsifiable by a diff
touching any §1a/§1b/§1c file inside THIS amendment's diff window.

The diff window is BASELINE..SEAL_COMMIT — bounded at BOTH ends,
mirroring the sealed `test_AC_TPI_6_*` cure (broken-suite-family-fixes
AC.SUITEFIX.1). The original form diffed ``BASELINE..HEAD``; unbounded
above, every later unrelated amendment fell inside the fence window,
so the fence falsely tripped once post-seal history touched a fenced
§1a/§1b file (e.g. the PB-retirement docstring edits to handsoff-loop).
Bounding at the telegram-5-fix seal (`ca7f7157`) makes the fence
permanent — only THIS amendment's deltas are ever in scope.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

# .../loam-spawn-isolation/tests/<this> -> parents[4] == repo root.
REPO_ROOT = Path(__file__).resolve().parents[4]
_MANIFEST = (
    REPO_ROOT / "docs" / "plans" / "sealed"
    / "telegram-5-fix.manifest.yaml"
)

# Upper bound of the fence diff window — the telegram-5-fix seal
# commit (`chore(seals): telegram-5-fix — workspace-bootstrap at
# a7ca729`). Mirrors the TPI_6 sidecar pattern: read a local sidecar
# SHA if one ever exists, else the pinned seal SHA, else HEAD (the
# pre-seal in-cycle fallback). loam-spawn-isolation sealed against
# the workspace-bootstrap anchor, so no tests/SEAL_COMMIT sidecar
# exists here and the pinned SHA governs.
SEAL_COMMIT_PATH = Path(__file__).parent / "SEAL_COMMIT"
_SEAL_COMMIT = "ca7f7157"


def _seal_commit() -> str:
    """Resolve the diff-window upper bound: sidecar SHA, else the
    pinned seal SHA, else HEAD."""
    if SEAL_COMMIT_PATH.exists():
        txt = SEAL_COMMIT_PATH.read_text().strip()
        if txt and txt != "HEAD":
            return txt
    return _SEAL_COMMIT or "HEAD"

# Contract §1a — ALREADY isolated production `claude -p` clients.
_FENCE_1A = (
    "framework/tools/subloam-driver/src/subloam_driver/driver.py",
    "framework/tools/upgrade-merge-resolver/src/loam/"
    "upgrade_merge_resolver/__init__.py",
    "framework/workspace-sync/src/loam/workspace_sync/"
    "_resolver_client.py",
    "plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/"
    "claude_print_synthesis_client.py",
)

# Contract §1b — the prior fix's three handsoff-loop launch sites +
# its adapter (b33c0a8/e0b71cb, AC.TPI.*).  The promote LIFTS the
# adapter PATTERN into a new shared package; it does NOT edit the
# sealed §1b adapter or the three launch sites.
_FENCE_1B = (
    "framework/tools/handsoff-loop/src/handsoff_loop/_isolation.py",
    "framework/tools/handsoff-loop/src/handsoff_loop/intake.py",
    "framework/tools/handsoff-loop/src/handsoff_loop/goal_drive.py",
    "framework/tools/handsoff-loop/src/handsoff_loop/"
    "orchestrator.py",
)

# Contract §1c — non-`claude` subprocess sites (ruled out so the
# fence is exact; not kill-vector sites; untouched).
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
            return (
                s.split(":", 1)[1].strip().strip('"').strip("'")
            )
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


@pytest.mark.parametrize(
    "fenced", [*_FENCE_1A, *_FENCE_1B, *_FENCE_1C]
)
def test_AC_PROMO_6_fenced_site_unchanged(fenced: str) -> None:
    """No §1a/§1b/§1c site appears in this amendment's diff window —
    the promote ADDS a shared surface, it does not churn the proven
    sites."""
    changed = _changed_paths()
    assert fenced not in changed, (
        f"OUT-OF-FENCE: {fenced!r} was modified by this amendment. "
        f"The promote is additive (a new shared package); §1a/§1b/"
        f"§1c are forbidden to touch (AC.PROMO.6). Changed: {changed}"
    )


def test_AC_PROMO_6_only_additive_new_package() -> None:
    """Affirmative side: every changed source path is either the new
    shared package, or a doc/plan/state universal — NO sealed
    §1a/§1b/§1c source is in the diff window (no scope creep)."""
    changed = _changed_paths()
    new_pkg_prefix = "framework/tools/loam-spawn-isolation/"
    universal_prefixes = (
        "docs/plans/",
        "docs/design/",
        "docs/experiments/",
        "docs/papers/",
        "docs/examples/",
    )
    universal_files = {
        "docs/STATE.md",
        "docs/release-roadmap.md",
        "docs/FUTURE_IDEAS.md",
        "docs/FUTURE_IDEAS_DRAFT.md",
        "CLAUDE.md",
    }
    # The amendment-ritual bookkeeping surface the manifest-declared
    # workspace-bootstrap seal anchor legitimately produces EVERY
    # cycle: `loam amend apply` advances the sidecar (SEAL_COMMIT) +
    # bumps the seal-test BASELINE; `loam amend seal` advances them
    # again + writes the narrative. These are the seal MECHANISM, not
    # §1a/§1b/§1c source churn and not scope creep (the prior
    # phase-b-intake-fix / telegram-poller-isolation-fix apply commits
    # touched the identical two paths). The load-bearing
    # §1a/§1b/§1c-untouched assertion is the parametrized
    # `test_AC_PROMO_6_fenced_site_unchanged` above — it stays exact.
    ritual_bookkeeping = {
        "framework/workspace-bootstrap/tests/SEAL_COMMIT",
        "framework/workspace-bootstrap/tests/"
        "test_no_sealed_amendments.py",
        "framework/hands-off-lifecycle/seals/"
        "SEAL_COMMIT.telegram-5-fix",
    }
    src_changed = [
        p
        for p in changed
        if p.endswith(".py")
        and "/tests/" not in p
        and not p.startswith("docs/")
        and p not in ritual_bookkeeping
    ]
    unexpected = sorted(
        p
        for p in src_changed
        if not p.startswith(new_pkg_prefix)
    )
    assert unexpected == [], (
        f"non-additive source churn outside the new shared package: "
        f"{unexpected} (AC.PROMO.6). Full changed set: {changed}"
    )
    # Sanity: anything else changed must be the new package, a test
    # under it, a universal doc/state path, or the amendment-ritual
    # bookkeeping surface (sidecar / seal-test BASELINE / narrative).
    leftover = [
        p
        for p in changed
        if not p.startswith(new_pkg_prefix)
        and not any(
            p.startswith(up) for up in universal_prefixes
        )
        and p not in universal_files
        and p not in ritual_bookkeeping
    ]
    assert leftover == [], (
        f"changed paths outside the new package + universal "
        f"doc/state admissions: {leftover} (AC.PROMO.6)"
    )
