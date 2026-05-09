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

"""AC.NTU.3 — workspace corpus override pattern (doc + reference example).

Per ``docs/plans/v0-7-0-non-tech-user-surface.md`` AC.NTU.3:

    Doc exists at canonical path; covers what the override does +
    reader-fall-through order + 3 use cases; reviewable in 5 minutes.
    Reference override exists at canonical path + parses cleanly through
    the existing ``_resolve_corpus_path`` resolver. Test: integration
    test loads the reference override into a fixture workspace + verifies
    the resolver picks it over the canonical default.

The integration probe places the reference override at a fixture
workspace root and verifies the resolver returns it (not the framework
fall-through path).
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
HOOKS_DIR = REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

# Import the resolver under test (the canonical pattern documented at
# docs/workspace-corpus-overrides.md).
import corpus_inline_session_start  # noqa: E402


# ---------------------------------------------------------------------------
# (a) Doc exists at canonical path


def test_AC_NTU_3_doc_exists_at_canonical_path() -> None:
    """The workspace-corpus-overrides doc ships at the conventional
    docs/ path (sibling to release-process.md per the AC).
    """
    doc_path = REPO_ROOT / "docs" / "workspace-corpus-overrides.md"
    assert doc_path.is_file(), f"doc missing at {doc_path}"


def test_AC_NTU_3_doc_covers_required_sections() -> None:
    """The doc covers the AC's named topics: what the override does +
    reader-fall-through order + 3 use cases.
    """
    doc_path = REPO_ROOT / "docs" / "workspace-corpus-overrides.md"
    text = doc_path.read_text(encoding="utf-8")
    # 'What this enables' + 3 use cases + 'how to author' + 'when not to use'
    assert "What this enables" in text
    assert "How to author" in text
    assert "When NOT to use" in text or "When not to use" in text
    # Use cases — section enumerates 3
    assert "Domain-specific persona prompt" in text
    assert "Domain-specific value proposition" in text
    assert "Domain-specific state document" in text
    # Reader-fall-through order is explained
    assert "workspace root first" in text or "workspace-root first" in text or "probes the workspace root first" in text


# ---------------------------------------------------------------------------
# (b) Reference override exists at canonical path


def test_AC_NTU_3_reference_override_exists() -> None:
    """The reference override (household-finance-CLAUDE.md) ships at
    the conventional docs/examples/corpus-overrides/ path.
    """
    example_path = (
        REPO_ROOT
        / "docs"
        / "examples"
        / "corpus-overrides"
        / "household-finance-CLAUDE.md"
    )
    assert example_path.is_file(), f"reference override missing at {example_path}"
    # Sanity: non-empty + names the household-finance domain in the title.
    text = example_path.read_text(encoding="utf-8")
    assert len(text) > 500  # not a stub
    assert "Household finance" in text or "household finance" in text


# ---------------------------------------------------------------------------
# (c) Integration probe — resolver picks the override over the canonical


def test_AC_NTU_3_integration_resolver_picks_override(tmp_path: Path) -> None:
    """Place the reference override at a fixture workspace's CLAUDE.md
    location + verify _resolve_corpus_path returns the workspace-root
    path (the override), not the fall-through framework path.
    """
    # Fixture workspace: root has CLAUDE.md (the override); framework/
    # subdir also has CLAUDE.md (the canonical fallback).
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()
    framework_dir = workspace_root / "framework"
    framework_dir.mkdir()

    # Drop the reference override at the workspace root.
    reference_path = (
        REPO_ROOT
        / "docs"
        / "examples"
        / "corpus-overrides"
        / "household-finance-CLAUDE.md"
    )
    override_text = reference_path.read_text(encoding="utf-8")
    (workspace_root / "CLAUDE.md").write_text(override_text, encoding="utf-8")

    # Drop a stub canonical at framework/CLAUDE.md (would be loaded
    # without the override).
    (framework_dir / "CLAUDE.md").write_text(
        "# canonical CLAUDE.md (would be loaded without override)\n",
        encoding="utf-8",
    )

    # Resolve.
    resolved = corpus_inline_session_start._resolve_corpus_path(
        workspace_root, "CLAUDE.md"
    )
    assert resolved == workspace_root / "CLAUDE.md", (
        f"resolver picked {resolved}; expected workspace-root override "
        f"({workspace_root / 'CLAUDE.md'})"
    )

    # Sanity: the resolved file's text IS the household-finance override.
    assert "Household finance" in resolved.read_text(encoding="utf-8")


def test_AC_NTU_3_resolver_falls_through_when_no_override(
    tmp_path: Path,
) -> None:
    """Negative probe: with NO workspace-root file, the resolver falls
    through to framework/<rel>. Confirms the override pattern is
    opt-in (only present when a file exists at the workspace root).
    """
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()
    framework_dir = workspace_root / "framework"
    framework_dir.mkdir()
    (framework_dir / "CLAUDE.md").write_text(
        "# canonical content\n", encoding="utf-8"
    )

    resolved = corpus_inline_session_start._resolve_corpus_path(
        workspace_root, "CLAUDE.md"
    )
    assert resolved == framework_dir / "CLAUDE.md"
