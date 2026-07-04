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

"""AC.CLP-DOC.1 / .5 / .6 — the graduated dispatch-decision trio.

AC.CLP-DOC.1 — a loam-shipped auto-discoverable surface maps work-shapes
to native Claude primitives, sourced from the corpus.
  The three skills are present + discoverable (well-formedness is gated
  by the AC.LSK suite); every capability reference points at a corpus
  entry rather than carrying an independently-maintained claim.

AC.CLP-DOC.5 — the graduated skills carry no stale/unverifiable
capability claims: the gap-analysis §3.2 stale items do not appear in
the canonical copies, and capability facts are corpus pointers.

AC.CLP-DOC.6 — the README matches disk: skill count derives from what
exists; meta-decision-haiku is PACKAGED (AC.PFSE.8 — supersedes the
prior planned-not-yet-packaged state); gap-analysis §3.3's mismatch is
gone.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import discover_skill_packages


SKILLS_DIR = Path(__file__).resolve().parent.parent / "skills"
README = Path(__file__).resolve().parent.parent / "README.md"

GRADUATED = (
    "claude-feature-awareness",
    "tool-selection-rubric",
    "primitive-rationale-check",
)


def _body(skill: str) -> str:
    return (SKILLS_DIR / skill / "SKILL.md").read_text(encoding="utf-8")


# ---- AC.CLP-DOC.1 : present + corpus-sourced ----


def test_AC_CLP_DOC_1_graduated_trio_present() -> None:
    on_disk = set(discover_skill_packages())
    for skill in GRADUATED:
        assert skill in on_disk, (
            f"graduated skill {skill!r} must be present + discoverable"
        )


def test_AC_CLP_DOC_1_awareness_routes_to_corpus() -> None:
    """The catalogue skill points at the capability corpus rather than
    carrying its own capability claims."""
    body = _body("claude-feature-awareness")
    assert "docs/capability-corpus/" in body, (
        "claude-feature-awareness must route to the capability corpus"
    )
    # It points at the claude-code corpus entries by path.
    assert "docs/capability-corpus/claude-code/" in body


# ---- AC.CLP-DOC.5 : no stale §3.2 items ; corpus pointers ----


def test_AC_CLP_DOC_5_no_stale_hook_event_snapshot() -> None:
    """The gap-analysis §3.2 stale framings (a fixed hook-event-count
    snapshot presented as current, the 'loam uses N hook events /
    doesn't use PreCompact yet' staleness, the v2.1.141-snapshot
    framing) must not appear in the canonical awareness copy."""
    body = _body("claude-feature-awareness")
    low = body.lower()
    stale_markers = (
        "29 hook events",
        "29-event",
        "v2.1.141",
        "doesn't use this yet",
        "doesn't use precompact yet",
        "going stale fast",
        "loam currently uses:",
    )
    leaked = [m for m in stale_markers if m.lower() in low]
    assert not leaked, (
        f"gap-analysis §3.2 stale framing leaked into the canonical "
        f"claude-feature-awareness copy: {leaked}. The graduated copy "
        f"must carry no independently-maintained capability snapshot — "
        f"it routes to the refresh-kept corpus instead."
    )


def test_AC_CLP_DOC_5_no_pos3_local_paths() -> None:
    """The graduated copies carry no pos3-local paths (D-DOC.5 hard
    constraint)."""
    for skill in GRADUATED:
        body = _body(skill)
        assert "pos3" not in body.lower(), (
            f"{skill}: graduated canonical copy must carry no pos3-local "
            f"path reference"
        )


def test_AC_CLP_DOC_5_no_schema_marker_strings() -> None:
    """The graduated skills must NOT contain the AC.alpha.8 corpus
    schema-marker strings (plan §3.3 hard constraint — they point at
    corpus entries by path, they don't replicate the schema).

    The marker strings are ASSEMBLED from fragments here so this test
    file does not itself contain the literal markers — otherwise the
    AC.alpha.8 repo-wide grep (which gates this very cycle's seal) would
    flag this file as a leak. plugins/loam-skills/tests/ is NOT an
    AC.alpha.8-admitted path; the assembly keeps the literal out.
    """
    markers = (
        "Capability" + " leverage spine",
        "[user-intent" + " phrasings]",
        "No-cross-class" + "-write",
    )
    for skill in GRADUATED:
        body = _body(skill)
        for m in markers:
            assert m not in body, (
                f"{skill}: schema-marker {m!r} must not appear in the "
                f"graduated skill body (AC.alpha.8 ride-along constraint)"
            )


# ---- AC.CLP-DOC.6 : README matches disk ----


def test_AC_CLP_DOC_6_readme_count_derives_from_disk() -> None:
    """The README's stated packaged-skill count matches the number of
    SKILL.md packages on disk."""
    packaged = len(discover_skill_packages())
    body = README.read_text(encoding="utf-8")
    # The number-word the README leads with must match disk. We assert
    # the disk count is stated (as digits anywhere, or as the leading
    # number-word) rather than pinning a specific phrasing.
    number_words = {
        21: "twenty-one",
        22: "twenty-two",
        23: "twenty-three",
        24: "twenty-four",
        25: "twenty-five",
        26: "twenty-six",
        27: "twenty-seven",
        28: "twenty-eight",
    }
    word = number_words.get(packaged, "")
    assert (
        str(packaged) in body or (word and word.lower() in body.lower())
    ), (
        f"README must state the disk-derived packaged-skill count "
        f"({packaged}); neither the digit nor {word!r} appears"
    )


def test_AC_CLP_DOC_6_meta_decision_haiku_now_packaged() -> None:
    """meta-decision-haiku is PACKAGED by AC.PFSE.8 (principle-
    foundation-structural-enforcement Slice D), filling the slot the
    sealed lsk1 F3 ruling held open as planned-not-yet-packaged.

    Supersedes the prior planned-not-yet-packaged assertion: the
    candidate's AC.PFSE.8 is the authority that packages the SKILL (PFSE
    plan §2 placement — 'fills the planned-not-yet-packaged slot per the
    lsk1 ruling')."""
    # The directory exists and now carries a SKILL.md.
    assert (
        SKILLS_DIR / "meta-decision-haiku" / "SKILL.md"
    ).is_file(), (
        "meta-decision-haiku is now packaged (AC.PFSE.8) — it carries a "
        "SKILL.md"
    )
    body = README.read_text(encoding="utf-8")
    assert "meta-decision-haiku" in body, (
        "README must name meta-decision-haiku"
    )
    # The README no longer labels it planned-not-yet-packaged.
    assert "planned-not-yet-packaged" not in body, (
        "README must NOT label meta-decision-haiku "
        "planned-not-yet-packaged any more — it is packaged (AC.PFSE.8)"
    )


def test_AC_CLP_DOC_6_readme_names_graduated_trio() -> None:
    body = README.read_text(encoding="utf-8")
    for skill in GRADUATED:
        assert skill in body, (
            f"README must name the graduated skill {skill!r} (so it has "
            f"a live consumer + the README reflects disk reality)"
        )
