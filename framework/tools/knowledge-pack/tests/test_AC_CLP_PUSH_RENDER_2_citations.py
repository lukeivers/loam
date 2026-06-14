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

"""AC.CLP-PUSH-RENDER.2 — every pack claim carries its corpus citation.

Each projected skill names the corpus path it was projected from, the
upstream source_url, and re-emits the entry's
``[primitive: <class>:<name>]`` cross-references. No externally-sourced
claim is decoupled from its source.
"""

from __future__ import annotations

from knowledge_pack.render import render_pack


def test_AC_CLP_PUSH_RENDER_2_every_skill_names_its_corpus_path(fixture_corpus):
    corpus = fixture_corpus["corpus_root"]
    pack = fixture_corpus["repo_root"] / "pack"
    render_pack(corpus, pack, "2026-06-14T12:00:00Z")

    for skill_md in pack.rglob("SKILL.md"):
        text = skill_md.read_text(encoding="utf-8")
        assert "## Provenance" in text
        assert "Projected from: `docs/capability-corpus/" in text


def test_AC_CLP_PUSH_RENDER_2_source_url_passthrough(fixture_corpus):
    """A Class A skill carries its upstream source_url citation."""
    corpus = fixture_corpus["corpus_root"]
    pack = fixture_corpus["repo_root"] / "pack"
    render_pack(corpus, pack, "2026-06-14T12:00:00Z")

    goal = (pack / "plugins" / "loam-knowledge-claude-code"
            / "skills" / "goal" / "SKILL.md").read_text(encoding="utf-8")
    assert "https://code.claude.com/docs/en/commands" in goal


def test_AC_CLP_PUSH_RENDER_2_crossref_citation_reemitted(fixture_corpus):
    """A Class B skill re-emits its [primitive: <class>:<name>] citation."""
    corpus = fixture_corpus["corpus_root"]
    pack = fixture_corpus["repo_root"] / "pack"
    render_pack(corpus, pack, "2026-06-14T12:00:00Z")

    bp = (pack / "plugins" / "loam-knowledge-best-practice"
          / "skills" / "scope-only-dispatch" / "SKILL.md").read_text(encoding="utf-8")
    assert "[primitive: claude-code:goal]" in bp
    assert "Cross-references:" in bp
