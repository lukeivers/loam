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

"""AC.SFR.3 — corpus_load_sentinel reader falls through to
``<workspace>/framework/`` when the workspace-root copy is absent.

Single-framework restructure (amendment #67). Verifies:

- ``compute_corpus_paths_required`` reads
  ``<workspace>/framework/docs/dev-mode-manifest.yaml`` when
  the workspace-root copy is absent (and resolves the manifest's
  paths against the framework root so they exist on disk).
- ``_classify_corpus_state`` counts a path as present when either
  ``<workspace>/<rel>`` OR ``<workspace>/framework/<rel>`` exists.
- ``write_corpus_load_sentinel`` end-to-end produces ``state ==
  "loaded"`` for a workspace whose corpus lives only under
  ``<workspace>/framework/``.
"""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
HOOKS_DIR = REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

from corpus_load_sentinel import (  # noqa: E402
    _classify_corpus_state,
    compute_corpus_paths_required,
    read_corpus_load_sentinel,
    write_corpus_load_sentinel,
)


# A minimal dev-mode-manifest with one always-loaded path.
_FIXTURE_MANIFEST = """\
roots:
  - docs/
audit_excludes: []
always_loaded:
  - path: docs/odd-methodology.md
dev_only: []
"""


def test_compute_corpus_paths_required_falls_through_to_framework(
    tmp_path: Path,
) -> None:
    """Manifest absent at workspace root → reader uses
    ``<workspace>/framework/docs/dev-mode-manifest.yaml``.
    The selector resolves manifest paths against the framework root.
    """
    workspace_root = tmp_path
    framework = workspace_root / "framework"
    framework_docs = framework / "docs"
    framework_docs.mkdir(parents=True)
    (framework_docs / "dev-mode-manifest.yaml").write_text(_FIXTURE_MANIFEST)

    # The corpus path the manifest names must exist on disk for the
    # selector to surface it. Place it under framework/ to match where
    # the workspace post-bootstrap holds it.
    (framework / "docs").mkdir(exist_ok=True)
    (framework / "docs" / "odd-methodology.md").write_text("# odd\n")

    paths = compute_corpus_paths_required(workspace_root, "normal-use")
    assert "docs/odd-methodology.md" in paths


def test_compute_corpus_paths_required_prefers_workspace_root(
    tmp_path: Path,
) -> None:
    """Manifest present at workspace root → reader uses workspace-root
    manifest, ignores framework copy.
    """
    workspace_root = tmp_path
    docs = workspace_root / "docs"
    docs.mkdir(parents=True)
    (docs / "dev-mode-manifest.yaml").write_text(_FIXTURE_MANIFEST)
    (workspace_root / "docs" / "odd-methodology.md").write_text(
        "# odd from root\n"
    )

    # Distinct framework manifest names a different path; if it leaks,
    # we'd see the wrong path returned.
    framework_docs = workspace_root / "framework" / "docs"
    framework_docs.mkdir(parents=True)
    (framework_docs / "dev-mode-manifest.yaml").write_text(
        _FIXTURE_MANIFEST.replace(
            "docs/odd-methodology.md", "docs/should-not-leak.md"
        )
    )

    paths = compute_corpus_paths_required(workspace_root, "normal-use")
    assert "docs/odd-methodology.md" in paths
    assert all("should-not-leak" not in p for p in paths)


# ---- _classify_corpus_state -----------------------------------------


def test_classify_corpus_state_falls_through_to_framework(
    tmp_path: Path,
) -> None:
    """Required path missing at workspace root but present under
    ``<workspace>/framework/`` → classified as present.
    """
    workspace_root = tmp_path
    framework = workspace_root / "framework"
    (framework / "docs").mkdir(parents=True)
    (framework / "docs" / "foo.md").write_text("# foo\n")

    state = _classify_corpus_state(workspace_root, ["docs/foo.md"])
    assert state == "loaded"


def test_classify_corpus_state_partial_when_split_across_locations(
    tmp_path: Path,
) -> None:
    """Mixed presence → ``partial``."""
    workspace_root = tmp_path
    framework = workspace_root / "framework"
    (framework / "docs").mkdir(parents=True)
    (framework / "docs" / "fw-only.md").write_text("# fw\n")

    (workspace_root / "docs").mkdir(parents=True)
    (workspace_root / "docs" / "ws-only.md").write_text("# ws\n")

    state = _classify_corpus_state(
        workspace_root, ["docs/fw-only.md", "docs/ws-only.md", "docs/missing.md"]
    )
    assert state == "partial"


def test_classify_corpus_state_missing_when_neither_present(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path
    state = _classify_corpus_state(workspace_root, ["docs/missing.md"])
    assert state == "missing"


# ---- end-to-end write ----------------------------------------------


def test_write_corpus_load_sentinel_loaded_via_framework_fall_through(
    tmp_path: Path,
) -> None:
    """The full hook flow over a framework-only-shaped workspace.

    Workspace-root has no docs; the manifest + corpus paths live
    under ``<workspace>/framework/``. The hook writes the sentinel
    with ``state == "loaded"``.
    """
    workspace_root = tmp_path
    framework = workspace_root / "framework"
    framework_docs_rebuild = framework / "docs"
    framework_docs_rebuild.mkdir(parents=True)
    (framework_docs_rebuild / "dev-mode-manifest.yaml").write_text(
        _FIXTURE_MANIFEST
    )
    (framework / "docs" / "odd-methodology.md").write_text("# odd\n")

    result = write_corpus_load_sentinel(
        workspace_root,
        session_id="sfr3-fall-through",
        mode="normal-use",
    )
    assert result.wrote
    assert result.path.exists()

    sentinel = read_corpus_load_sentinel(
        workspace_root, "sfr3-fall-through"
    )
    assert sentinel is not None
    assert sentinel.state == "loaded"
    assert "docs/odd-methodology.md" in sentinel.corpus_paths_required
