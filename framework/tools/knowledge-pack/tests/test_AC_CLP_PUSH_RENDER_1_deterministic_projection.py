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

"""AC.CLP-PUSH-RENDER.1 — deterministic corpus->pack projection, no LLM
body authorship.

The pack body is a deterministic projection of the corpus: every
projected SKILL.md body contains the corpus entry body VERBATIM, and two
renders of the same corpus at the same generated-ts produce
byte-identical trees (no LLM pass, no nondeterminism). A hallucinated
leverage claim cannot enter by construction (D-PUSH.1 protection floor).
"""

from __future__ import annotations

from pathlib import Path

from knowledge_pack.render import render_pack


def _read_all(root: Path) -> dict:
    return {
        p.relative_to(root).as_posix(): p.read_text(encoding="utf-8")
        for p in sorted(root.rglob("*")) if p.is_file()
    }


def test_AC_CLP_PUSH_RENDER_1_body_is_verbatim(fixture_corpus):
    """Each projected SKILL.md carries the corpus entry body verbatim —
    the render authors no body text."""
    corpus = fixture_corpus["corpus_root"]
    pack = fixture_corpus["repo_root"] / "pack"
    render_pack(corpus, pack, "2026-06-14T12:00:00Z")

    corpus_goal = (corpus / "claude-code" / "goal.md").read_text(encoding="utf-8")
    skill = (pack / "plugins" / "loam-knowledge-claude-code"
             / "skills" / "goal" / "SKILL.md").read_text(encoding="utf-8")
    # The full corpus body appears verbatim inside the projected skill.
    assert corpus_goal.rstrip("\n") in skill
    # A distinctive corpus sentence is present unaltered (no paraphrase).
    assert "drives work to a checkable predicate" in skill


def test_AC_CLP_PUSH_RENDER_1_deterministic_bytes(fixture_corpus):
    """Two renders at the same generated-ts produce byte-identical trees."""
    corpus = fixture_corpus["corpus_root"]
    pack_a = fixture_corpus["repo_root"] / "pack_a"
    pack_b = fixture_corpus["repo_root"] / "pack_b"
    ts = "2026-06-14T12:00:00Z"
    render_pack(corpus, pack_a, ts)
    render_pack(corpus, pack_b, ts)

    files_a = _read_all(pack_a)
    files_b = _read_all(pack_b)
    assert files_a.keys() == files_b.keys()
    for rel in files_a:
        assert files_a[rel] == files_b[rel], f"non-deterministic render for {rel}"


def test_AC_CLP_PUSH_RENDER_1_content_hash_stable_across_ts(fixture_corpus):
    """The content-hash is over the projected bodies only — it is stable
    across different generated-ts (so the ts never spoofs a content
    change). Two renders at DIFFERENT ts share the same content-hash."""
    corpus = fixture_corpus["corpus_root"]
    r1 = render_pack(corpus, fixture_corpus["repo_root"] / "p1", "2026-06-14T00:00:00Z")
    r2 = render_pack(corpus, fixture_corpus["repo_root"] / "p2", "2026-12-31T23:59:59Z")
    assert r1.content_hash == r2.content_hash
