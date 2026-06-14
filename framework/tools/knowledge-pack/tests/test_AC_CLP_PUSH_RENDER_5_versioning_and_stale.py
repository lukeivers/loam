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

"""AC.CLP-PUSH-RENDER.5 — pack carries generated-ts + content-hash +
per-entry passthrough; a stale corpus entry never renders as silently
current (D-PUSH.5).
"""

from __future__ import annotations

import json

from knowledge_pack.render import render_pack


def _manifest(pack):
    return json.loads((pack / "pack-manifest.json").read_text(encoding="utf-8"))


def test_AC_CLP_PUSH_RENDER_5_manifest_carries_ts_hash_version(fixture_corpus):
    corpus = fixture_corpus["corpus_root"]
    pack = fixture_corpus["repo_root"] / "pack"
    render_pack(corpus, pack, "2026-06-14T12:00:00Z")
    m = _manifest(pack)
    assert m["generated_ts"] == "2026-06-14T12:00:00Z"
    assert len(m["content_hash"]) == 64  # sha256 hex
    # version derives from (date, content-hash) — never pre-assigned.
    assert m["version"].startswith("2026.06.14+")
    assert m["version"].endswith(m["content_hash"][:12])


def test_AC_CLP_PUSH_RENDER_5_per_entry_passthrough(fixture_corpus):
    """Every entry's source_fetch_ts + source_status pass through to the
    pack manifest."""
    corpus = fixture_corpus["corpus_root"]
    pack = fixture_corpus["repo_root"] / "pack"
    render_pack(corpus, pack, "2026-06-14T12:00:00Z")
    m = _manifest(pack)
    by_skill = {e["skill"]: e for e in m["entries"]}
    assert by_skill["goal"]["source_status"] == "current"
    assert by_skill["goal"]["source_fetch_ts"] == "2026-06-14T00:00:00Z"


def test_AC_CLP_PUSH_RENDER_5_stale_entry_flagged_and_visible(fixture_corpus):
    """A stale corpus entry is (a) listed in the manifest stale_entries,
    (b) carries its stale status in its SKILL.md provenance footer — never
    rendered as silently current."""
    corpus = fixture_corpus["corpus_root"]
    pack = fixture_corpus["repo_root"] / "pack"
    result = render_pack(corpus, pack, "2026-06-14T12:00:00Z")

    # The stale loop.md entry is flagged.
    assert any("loop.md" in s for s in result.stale_entries)
    m = _manifest(pack)
    assert any("loop.md" in s for s in m["stale_entries"])

    # Its skill carries the stale status visibly in the provenance footer.
    loop_skill = (pack / "plugins" / "loam-knowledge-claude-code"
                  / "skills" / "loop" / "SKILL.md").read_text(encoding="utf-8")
    assert "Source status: stale" in loop_skill


def test_AC_CLP_PUSH_RENDER_5_hash_changes_when_body_changes(fixture_corpus):
    """The content-hash deterministically tracks pack-body changes — edit
    a corpus entry, the hash changes (drives whether a publish is even
    warranted)."""
    corpus = fixture_corpus["corpus_root"]
    r1 = render_pack(corpus, fixture_corpus["repo_root"] / "p1", "t")
    # Mutate a corpus entry body.
    goal = corpus / "claude-code" / "goal.md"
    goal.write_text(goal.read_text(encoding="utf-8") + "\nNew line.\n", encoding="utf-8")
    r2 = render_pack(corpus, fixture_corpus["repo_root"] / "p2", "t")
    assert r1.content_hash != r2.content_hash
