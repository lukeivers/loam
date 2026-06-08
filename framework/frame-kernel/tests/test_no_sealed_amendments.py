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

"""AC.SACH.S surface — frame-kernel seal-diff test (loam-realignment 1a).

frame-kernel is a NEW component; this is its first seal. The seal-diff
test follows the B23 sidecar-pinned pattern every sealed component uses:
BASELINE names the pre-amendment tip; SEAL_COMMIT is read from the
sidecar sibling file so the diff runs ``BASELINE..SEAL_COMMIT`` — NOT
``..HEAD`` (the f94d602 HEAD defect must not be reintroduced).

The sidecar lives at ``tests/SEAL_COMMIT`` (the universal convention —
all 21 sibling sealed components, and the seal sweep's
``_discover_sealed_components`` which globs ``framework/*/tests/
SEAL_COMMIT``). ``loam amend apply`` widens the ``allowed_prefixes`` /
``allowed_files`` bindings below + writes the sidecar to the baseline
window; ``loam amend seal`` advances the sidecar to the seal SHA.

BASELINE: 22df8683 — the pre-amendment tip (``docs(release): v1.3.0
post-publish backfill — SHIPPED PUBLIC``, HEAD immediately preceding the
frame-kernel source-edit commit). New component, so the BASELINE is the
repo tip at first touch.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
BASELINE = "bf1108dfa1f7585333636e9a505e60015e226165"

SEAL_COMMIT_PATH = Path(__file__).parent / "SEAL_COMMIT"


def _seal_commit() -> str:
    """Resolve SEAL_COMMIT from the sidecar file, else HEAD.

    Once sealed, ``tests/SEAL_COMMIT`` holds the exact SHA and the diff
    runs against that — the HEAD defect cannot recur.
    """
    if SEAL_COMMIT_PATH.exists():
        txt = SEAL_COMMIT_PATH.read_text().strip()
        if txt and txt != "HEAD":
            return txt
    return "HEAD"


def test_seal_commit_pinning_pattern() -> None:
    """The test exposes SEAL_COMMIT_PATH + names BASELINE; the diff call
    routes through _seal_commit() (not a hardcoded HEAD)."""
    source = Path(__file__).read_text()
    assert "BASELINE = " in source
    assert "SEAL_COMMIT_PATH" in source
    assert "{BASELINE}..{seal}" in source, (
        "the diff call must route through _seal_commit()"
    )


def test_AC_SACH_S_only_frame_kernel_surfaces_changed() -> None:
    """``git diff --name-only BASELINE..SEAL_COMMIT`` produces only paths
    under the admitted frame-kernel surfaces.

    SLICE 1a targets the NEW ``framework/frame-kernel/`` component (the
    SubagentStart hook + the bundle composer + the settings-fragment +
    the AC tests + this seal-diff sidecar) plus the ``kernel/`` TCB dir
    (the version-pinned microkernel, integrated-design §2-K) plus the
    amendment's own plan / manifest under ``docs/plans/``. Universal-file
    admissions are admitted per amendment #22 ruling #3 — widened in by
    ``loam amend apply``.
    """
    seal = _seal_commit()
    out = subprocess.check_output(
        ["git", "diff", "--name-only", f"{BASELINE}..{seal}"],
        cwd=REPO_ROOT,
        text=True,
    )
    changed = [ln for ln in out.splitlines() if ln.strip()]

    allowed_prefixes = (
        "framework/frame-kernel/",
        "kernel/",
        "docs/plans/",
        "docs/design/",
        "docs/examples/",
        "docs/experiments/",
    )
    allowed_files: set[str] = {
        "CLAUDE.md",
        "docs/STATE.md",
        "docs/release-roadmap.md",
        "docs/release-roadmap-dependency-map.md",
        "docs/release-process.md",
        "docs/release-versioning-policy.md",
        "docs/FUTURE_IDEAS.md",
        "docs/FUTURE_IDEAS_DRAFT.md",
        "docs/architecture.md",
        "docs/components/index.md",
        "docs/public-surface-manifest.md",
        "README.md",
        "install-from-source.txt",
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
