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

"""AC.A.S — Sub-plan A is a single-component amendment on `primary-persona`.

Sub-plan A (two-modes-and-multi-workspace) is a single-component
amendment on the ``primary-persona`` sealed surface. Per the master
plan's seal-diff discipline, no source surface outside
``primary-persona/`` may change as part of this amendment; the
amendment commit's diff is restricted to ``primary-persona/`` plus
universal admissions (``docs/rebuild/plans/``, ``CLAUDE.md``,
``docs/odd-*.md``, ``docs/rebuild/FUTURE_IDEAS.md``).

Two enforcement layers:

1. The universal ``test_no_sealed_amendments.py`` enforces
   BASELINE..SEAL_COMMIT diff windows for every sealed component.
   This test asserts that machinery is present and routes through
   the correct sidecar pattern (B23) — i.e., the seal-diff window
   for sub-plan A's amendment commit is structurally enforced once
   ``SEAL_COMMIT`` advances.

2. The sub-plan A manifest declares exactly one component
   (``primary-persona``); this test asserts that scope-shape so a
   future hand-edit to the manifest cannot silently widen the
   amendment to multiple sealed surfaces without updating this AC.

Plan: docs/rebuild/plans/two-modes-and-multi-workspace/A-onboarding-dev-intent.md
"""

from __future__ import annotations

from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# Sub-plan A's manifest (single source of truth for the amendment
# scope). The committed path is fixed by the plan-doc layout.
MANIFEST_PATH = (
    REPO_ROOT
    / "docs"
    / "rebuild"
    / "plans"
    / "two-modes-and-multi-workspace"
    / "A-onboarding-dev-intent.manifest.yaml"
)


def test_AC_A_S_manifest_exists_and_is_single_component():
    """The sub-plan A manifest declares exactly one component, and
    that component is ``primary-persona``."""
    assert MANIFEST_PATH.exists(), (
        f"sub-plan A manifest missing at {MANIFEST_PATH.relative_to(REPO_ROOT)}"
    )
    manifest = yaml.safe_load(MANIFEST_PATH.read_text())
    components = manifest.get("components", [])
    assert len(components) == 1, (
        f"sub-plan A is single-component; manifest declares {len(components)}"
    )
    names = {c.get("name") for c in components}
    assert names == {"primary-persona"}, (
        f"sub-plan A's component is primary-persona; got {names}"
    )


def test_AC_A_S_universal_seal_diff_test_present():
    """``primary-persona/tests/test_no_sealed_amendments.py`` is the
    universal seal-diff enforcement; AC.A.S delegates the actual
    BASELINE..SEAL_COMMIT diff window check to it. Assert presence
    + B23 sidecar pattern (so the diff routes through SEAL_COMMIT,
    not HEAD)."""
    seal_test = (
        REPO_ROOT / "framework" / "primary-persona" / "tests" / "test_no_sealed_amendments.py"
    )
    assert seal_test.exists()
    source = seal_test.read_text()
    # B23 sidecar pattern markers (mirrors the assertion in
    # test_no_sealed_amendments.py's own self-check).
    assert "BASELINE = " in source
    assert "SEAL_COMMIT_PATH" in source
    assert "{BASELINE}..{seal}" in source


def test_AC_A_S_seal_commit_sidecar_present():
    """The ``SEAL_COMMIT`` sidecar that pins the diff endpoint is
    present (B23). ``pos-amend seal`` advances it to the seal commit
    SHA on the seal commit; sub-plan A's amendment commit becomes
    visible to the seal-diff machinery once the sidecar is updated."""
    sidecar = (
        REPO_ROOT / "framework" / "primary-persona" / "tests" / "SEAL_COMMIT"
    )
    assert sidecar.exists()
    txt = sidecar.read_text().strip()
    assert txt, "SEAL_COMMIT sidecar must carry a SHA (or 'HEAD')"
