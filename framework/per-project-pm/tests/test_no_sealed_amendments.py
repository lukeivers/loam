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

"""Seal-fence test for the per-project-pm component.

NEW component — first seal cycle is v0.1.7 Cycle 2. Mirrors the
``plugins/loam-skills/tests/test_no_sealed_amendments.py`` pattern:
NEW components land their seal-test + sidecar surface alongside the
first behaviour change so sealed-component discipline applies from
day one.

BASELINE history:
  - <to-be-set-at-source-edit-commit>  at v0.1.7 Cycle 2 (per-project
    PM NEW component first seal). The component's first appearance in
    the tree IS the BASELINE per amendment-22 NEW-component pattern;
    the source-edit commit's SHA goes here.

SEAL_COMMIT: populated at seal time by ``loam amend seal`` per the
amendment ritual.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
# BASELINE = the source-edit commit landing the per-project-pm
# component. Set by `loam amend apply` at apply time.
BASELINE = "HEAD"

SEAL_COMMIT_PATH = Path(__file__).parent / "SEAL_COMMIT"


def _seal_commit() -> str:
    """Resolve SEAL_COMMIT from sidecar file, else HEAD."""
    if SEAL_COMMIT_PATH.exists():
        txt = SEAL_COMMIT_PATH.read_text().strip()
        if txt and txt != "HEAD":
            return txt
    return "HEAD"


def test_seal_commit_pinning_pattern() -> None:
    """The test file exposes BASELINE + SEAL_COMMIT_PATH and does not
    diff against ..HEAD literally. Post-seal, tests/SEAL_COMMIT
    contains the SHA."""
    source = Path(__file__).read_text()
    assert "BASELINE = " in source
    assert "SEAL_COMMIT_PATH" in source
    assert "{BASELINE}..{seal}" in source, (
        "the diff call must route through _seal_commit()"
    )


def test_only_per_project_pm_changed() -> None:
    """No sealed-component surface moved between BASELINE and seal
    outside the per-project-pm component tree + admitted partners.

    Cycle 2 fence: the component's own subtree
    (``framework/per-project-pm/``) plus universal admissions
    (``docs/rebuild/plans/`` for sub-plan + manifest;
    ``framework/first-run-inventory.yaml`` for shared-venv-component
    enrollment). No cross-component partners are needed —
    per-project-pm is leaf-shaped at Cycle 2; future cycles compose
    against it without it composing back.
    """
    seal = _seal_commit()
    # When BASELINE is "HEAD" (pre-apply state), the diff window is
    # empty and the test passes trivially. `loam amend apply`
    # advances BASELINE to the source-edit commit and SEAL_COMMIT to
    # the seal commit.
    if BASELINE == "HEAD" and seal == "HEAD":
        return
    out = subprocess.check_output(
        ["git", "diff", "--name-only", f"{BASELINE}..{seal}"],
        cwd=REPO_ROOT,
        text=True,
    )
    changed = [ln for ln in out.splitlines() if ln.strip()]

    allowed_prefixes = (
        "framework/per-project-pm/",
        "docs/rebuild/plans/",
    )
    allowed_files: set[str] = {
        # Universal-file admissions per amendment #22 ruling #3.
        "CLAUDE.md",
        "docs/odd-in-loam.md",
        "docs/odd-methodology.md",
        "docs/rebuild/FUTURE_IDEAS.md",
        "docs/rebuild/FUTURE_IDEAS_DRAFT.md",
        "docs/rebuild/STATE.md",
        # Per cycle-2 plan §4 Surface #10: NEW component admission
        # to the shared venv's components list.
        "framework/first-run-inventory.yaml",
        "first-run-inventory.yaml",
    }

    offending = []
    for path in changed:
        if any(path.startswith(p) for p in allowed_prefixes):
            continue
        if path in allowed_files:
            continue
        offending.append(path)
    assert offending == [], (
        f"Sealed-component paths modified: {offending}. "
        "Halt-signal condition."
    )
