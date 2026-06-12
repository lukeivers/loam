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

"""AC.CLP-CUR.1 + AC.CLP-CUR.2 — the reference surface is correct and
singular.

AC.CLP-CUR.1: the corpus's subagent-recursion claim is factually correct
per the live Claude Code changelog at build time (2.1.172: sub-agents
spawn sub-agents up to 5 levels deep — verified live 2026-06-11), and no
in-repo REFERENCE doc contradicts it.

AC.CLP-CUR.2: exactly one canonical capability-reference surface exists —
``docs/CLAUDE_CAPABILITIES.md`` is an index/redirect carrying no
independently-maintained four-section capability entries.

Grep scope note (named exclusions, all non-reference surfaces):
  - ``docs/plans/`` — plan/seal narratives recount the historical wrong
    claim as history, not as a reference claim;
  - ``docs/archive/`` — archived snapshots;
  - ``docs/capability-corpus/.refresh/`` + ``.../pending-deltas/`` —
    verbatim upstream mirrors / surfaced upstream quotes (the sub-agents
    docs PAGE still carried the stale no-recursion sentence on
    2026-06-11 — upstream's lag is mirrored state, not a corpus claim);
  - this test file itself (it names the forbidden phrase).
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
CORPUS_ENTRY = REPO_ROOT / "docs" / "capability-corpus" / "claude-code" / "background-agents.md"
CAPS_INDEX = REPO_ROOT / "docs" / "CLAUDE_CAPABILITIES.md"

# matches "cannot spawn other subagents" / "can't spawn other sub-agents" etc.
CONTRADICTION = re.compile(r"can(?:no|')?t\s+spawn\s+other\s+sub", re.IGNORECASE)

EXCLUDED_PREFIXES = (
    "docs/plans/",
    "docs/archive/",
    "docs/capability-corpus/.refresh/",
    "docs/capability-corpus/pending-deltas/",
    "framework/tools/capability-refresh/tests/",
)


def _tracked_files():
    out = subprocess.check_output(["git", "ls-files"], cwd=REPO_ROOT, text=True)
    return [ln for ln in out.splitlines() if ln.strip()]


def test_AC_CLP_CUR_1_corpus_recursion_claim_correct():
    text = CORPUS_ENTRY.read_text(encoding="utf-8")
    assert "5 levels" in text and "2.1.172" in text, (
        "corpus entry missing the corrected recursion claim "
        "(sub-agents spawn sub-agents to 5 levels deep, Claude Code 2.1.172)"
    )
    assert not CONTRADICTION.search(text)


def test_AC_CLP_CUR_1_no_reference_doc_contradicts():
    offenders = []
    for rel in _tracked_files():
        if any(rel.startswith(p) for p in EXCLUDED_PREFIXES):
            continue
        if not rel.endswith((".md", ".py", ".txt", ".yaml", ".yml")):
            continue
        path = REPO_ROOT / rel
        try:
            content = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if CONTRADICTION.search(content):
            offenders.append(rel)
    assert not offenders, (
        f"reference docs still carry the superseded no-recursion claim: {offenders}"
    )


def test_AC_CLP_CUR_2_single_canonical_reference_surface():
    text = CAPS_INDEX.read_text(encoding="utf-8")
    assert "index/redirect" in text, "demotion banner missing"
    assert "capability-corpus" in text, "redirect target missing"
    # No four-section capability entries remain (the old snapshot's
    # per-capability structure): 'Pitfalls' + 'End-user configuration
    # surface' headings were its signature.
    assert "End-user configuration surface" not in text
    assert not re.search(r"^#{2,3}\s+\d+\.\d+\s", text, re.MULTILINE), (
        "numbered capability subsections survived the demotion"
    )
    assert len(text.splitlines()) < 100, (
        "the demoted index has grown reference-sized; capability claims "
        "belong in docs/capability-corpus/"
    )
