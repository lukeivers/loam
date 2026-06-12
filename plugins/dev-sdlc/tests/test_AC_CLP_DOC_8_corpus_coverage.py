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

"""AC.CLP-DOC.8 — the check's primitive knowledge cannot silently drift
from the corpus.

The bidirectional coverage guard (D-DOC.4):
  1. Every ``claude-code/`` corpus entry has a matcher row pointing at
     it OR a named exclusion in COVERAGE_EXCLUSIONS.
  2. Every matcher row's ``corpus_entry`` pointer resolves to a real
     file on disk.
  3. A corpus entry added later without coverage is OBSERVABLE — a
     fixture corpus tree with an extra entry trips the guard.
  4. A row pointing at a removed corpus entry is OBSERVABLE — a fixture
     row with a dangling pointer trips the guard.

The guard runs against the live corpus tree (the real
``docs/capability-corpus/claude-code/``) for claims 1 + 2, and against
fixture trees for claims 3 + 4.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_HOOKS_DIR = REPO_ROOT / "plugins" / "dev-sdlc" / "hooks"
sys.path.insert(0, str(PLUGIN_HOOKS_DIR))

import primitive_check_matchers as matchers  # noqa: E402


def _corpus_claude_code_entries(corpus_dir: Path) -> set[str]:
    """Workspace-relative paths of every ``claude-code/`` corpus entry
    (``<dir>/*.md``), in the matcher-row pointer form."""
    if not corpus_dir.is_dir():
        return set()
    rel = matchers.CORPUS_CLAUDE_CODE_DIR
    return {
        f"{rel}/{p.name}"
        for p in corpus_dir.iterdir()
        if p.is_file() and p.suffix == ".md"
    }


# ----- claim 1: every corpus entry covered or excluded -----


def test_AC_CLP_DOC_8_every_corpus_entry_covered_or_excluded() -> None:
    corpus_dir = REPO_ROOT / matchers.CORPUS_CLAUDE_CODE_DIR
    on_disk = _corpus_claude_code_entries(corpus_dir)
    assert on_disk, (
        f"no claude-code corpus entries found under {corpus_dir} — "
        "the coverage guard needs the corpus tree present"
    )
    referenced = matchers.all_corpus_entries_referenced()
    excluded = set(matchers.COVERAGE_EXCLUSIONS)
    uncovered = on_disk - referenced - excluded
    assert not uncovered, (
        f"AC.CLP-DOC.8: corpus entries with NO matcher coverage and NO "
        f"named exclusion: {sorted(uncovered)}. A refresh-added entry "
        f"must gain a matcher row OR a COVERAGE_EXCLUSIONS entry — this "
        f"is the observable drift signal."
    )


# ----- claim 2: every row pointer resolves -----


def test_AC_CLP_DOC_8_every_row_pointer_resolves() -> None:
    for row in matchers.ROWS:
        target = REPO_ROOT / row.corpus_entry
        assert target.is_file(), (
            f"AC.CLP-DOC.8: matcher row {row.name!r} points at "
            f"{row.corpus_entry!r} which does not resolve to a file — "
            f"a dangling pointer (corpus entry renamed/removed?)"
        )
    # Exclusions must also name real entries (no phantom exclusions).
    for entry in matchers.COVERAGE_EXCLUSIONS:
        assert (REPO_ROOT / entry).is_file(), (
            f"AC.CLP-DOC.8: COVERAGE_EXCLUSIONS names {entry!r} which "
            f"does not resolve to a file."
        )


# ----- claim 3: a fixture entry without coverage is observable -----


def test_AC_CLP_DOC_8_fixture_added_entry_is_flagged(tmp_path) -> None:
    """Simulate a refresh adding a new corpus entry the matcher data
    does not cover: the coverage computation reports it as uncovered."""
    fixture = tmp_path / matchers.CORPUS_CLAUDE_CODE_DIR
    fixture.mkdir(parents=True)
    # Mirror the real referenced entries so they stay covered.
    for ref in matchers.all_corpus_entries_referenced():
        (tmp_path / ref).write_text("# stub\n", encoding="utf-8")
    # Add a brand-new, uncovered entry.
    (fixture / "brand-new-primitive.md").write_text(
        "# new\n", encoding="utf-8"
    )

    on_disk = _corpus_claude_code_entries(fixture)
    referenced = matchers.all_corpus_entries_referenced()
    excluded = set(matchers.COVERAGE_EXCLUSIONS)
    uncovered = on_disk - referenced - excluded
    assert (
        f"{matchers.CORPUS_CLAUDE_CODE_DIR}/brand-new-primitive.md"
        in uncovered
    ), (
        "AC.CLP-DOC.8: a newly-added corpus entry without a matcher row "
        "must surface as uncovered (the observable-drift contract)"
    )


# ----- claim 4: a dangling row pointer is observable -----


def test_AC_CLP_DOC_8_dangling_row_pointer_is_flagged(tmp_path) -> None:
    """A row whose pointer resolves to no file (corpus entry removed)
    is observable: resolution against a tree missing that entry fails."""
    # Build a corpus tree missing one referenced entry.
    referenced = sorted(matchers.all_corpus_entries_referenced())
    missing = referenced[0]
    for ref in referenced[1:]:
        (tmp_path / ref).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / ref).write_text("# stub\n", encoding="utf-8")

    unresolved = [
        ref for ref in referenced if not (tmp_path / ref).is_file()
    ]
    assert missing in unresolved, (
        "AC.CLP-DOC.8: a row pointing at a removed corpus entry must "
        "surface as an unresolved pointer (the observable-drift "
        "contract for the row→corpus direction)"
    )
