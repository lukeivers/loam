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

"""AC.OGP.1 — Lean grounding doc auto-loads in DEV MODE corpus-required set.

Per v0.2.2 sub-plan-doc §3 AC.OGP.1: the lean ODD grounding doc
(`docs/odd-llm-grounding.lean.md`) is added to the dev-mode-manifest
``dev_only:`` block, and ``compute_corpus_paths_required`` returns a
list that includes the new path when invoked on a DEV-MODE workspace.

Mirrors the AC.SE.5 / AC.CI.* test pattern: synthetic DEV-MODE workspace
fixture; assert the structural mechanism (manifest entry → required
set) emits the new path.
"""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
HOOKS_DIR = REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks"


def _import_corpus_load_sentinel():
    if str(HOOKS_DIR) not in sys.path:
        sys.path.insert(0, str(HOOKS_DIR))
    from corpus_load_sentinel import compute_corpus_paths_required  # noqa: E402

    return compute_corpus_paths_required


def test_AC_OGP_1_lean_grounding_in_dev_mode_required_set() -> None:
    """DEV MODE workspace → required set includes lean grounding doc.

    The dev-mode-manifest at
    ``plugins/dev-sdlc/dev-mode-manifest.yaml`` declares
    ``docs/odd-llm-grounding.lean.md`` under ``dev_only:``. The
    selector composes ``always_loaded ∪ dev_only`` for DEV MODE; so
    ``compute_corpus_paths_required(workspace_root, "dev-mode")``
    returns a list containing the lean grounding path.
    """
    compute_corpus_paths_required = _import_corpus_load_sentinel()
    paths = compute_corpus_paths_required(str(REPO_ROOT), mode="dev-mode")
    assert "docs/odd-llm-grounding.lean.md" in paths, (
        "AC.OGP.1: docs/odd-llm-grounding.lean.md must appear in the "
        "DEV-MODE corpus-required set; got "
        f"{sorted(p for p in paths if 'grounding' in p)!r}"
    )


def test_AC_OGP_1_lean_grounding_absent_from_normal_use_required_set() -> None:
    """NORMAL USE workspace → lean grounding doc NOT in required set.

    The lean doc lives only under ``dev_only:``; a NORMAL USE
    selector returns ``always_loaded`` only. This pins the partition
    contract — the doc loads in dev mode, not in normal use.
    """
    compute_corpus_paths_required = _import_corpus_load_sentinel()
    paths = compute_corpus_paths_required(str(REPO_ROOT), mode="normal-use")
    assert "docs/odd-llm-grounding.lean.md" not in paths, (
        "AC.OGP.1: docs/odd-llm-grounding.lean.md must NOT appear in "
        "the NORMAL-USE corpus-required set (it lives under dev_only:)."
    )
