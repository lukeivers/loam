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

"""AC.SUP.OA (outcome-altitude: true) — mark a real corpus rule via the
production marking entry point, then run a production retrieval on the
rule's topic with no pre-arranged index state: the successor ranks
ahead of (or the stale rule is surfaced annotated-superseded versus)
the marked rule.

Follows the AC-FBM-W-4 live-corpus cold-walk precedent: the test COPIES
the live ``feedback_*.md`` corpus into a temp repo root (it never reads
destructively or writes the live store), marks one REAL rule in the
copy via the production :func:`mark_superseded`, and runs the
production :func:`retrieve` entry point against a fresh workspace root
(no pre-arranged index state). Skips (does not fail) if the live corpus
is absent (CI / a fresh machine).
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from loam.primary_persona.keep_pace.retrieval import RetrievalConfig, retrieve
from loam.primary_persona.supersession import mark_superseded


LIVE_CORPUS = (
    Path.home()
    / ".claude"
    / "projects"
    / "-Users-lukeivers-pos3"
    / "memory"
)

# Two REAL rules sharing a real topic (background-agent dispatch); the
# pre-mark phase decides dynamically which one ranks first and marks
# THAT one, so the test tracks the live corpus rather than assuming an
# ordering.
_PAIR = (
    "feedback_background_agents.md",
    "feedback_background_default_for_authoring.md",
)
_TOPIC_PROMPT = (
    "should this long research and authoring work go to background "
    "agents or stay in the main session"
)


def _copy_live_corpus(dest: Path) -> list[Path]:
    dest.mkdir(parents=True, exist_ok=True)
    copied: list[Path] = []
    for src in sorted(LIVE_CORPUS.glob("*.md")):
        if not src.is_file():
            continue
        out = dest / src.name
        shutil.copyfile(src, out)
        copied.append(out)
    return copied


def _doc_title(path: Path) -> str:
    """The doc's surfaced pointer text (first ``# `` heading after any
    frontmatter, else prettified stem) — independent of the module
    under test."""
    raw = path.read_text(encoding="utf-8")
    body = raw
    if raw.startswith("---"):
        end = raw.find("\n---", 3)
        if end != -1:
            body = raw[raw.find("\n", end + 1) + 1 :]
    for line in body.splitlines():
        s = line.strip()
        if s.startswith("# "):
            return s[2:].strip()
    return path.stem.replace("_", " ").replace("-", " ")


def _retrieve_block(workspace_root: Path, corpus_dir: Path) -> str:
    cfg = RetrievalConfig(
        workspace_root=workspace_root,
        memory_dir=corpus_dir,
        claude_homes=(),
        objectives_home=workspace_root / "no-objectives",
        top_n=5,
    )
    return retrieve(prompt=_TOPIC_PROMPT, config=cfg)


@pytest.mark.skipif(
    not LIVE_CORPUS.is_dir(), reason="live feedback_*.md corpus not present"
)
def test_AC_SUP_OA_marked_real_rule_stops_mispointing(
    tmp_path: Path,
) -> None:
    corpus_dir = tmp_path / "memory"
    copied = _copy_live_corpus(corpus_dir)
    assert copied, "no live corpus docs copied"
    a, b = (corpus_dir / _PAIR[0], corpus_dir / _PAIR[1])
    if not (a.exists() and b.exists()):
        pytest.skip("the real background-agent rule pair is not in the corpus")

    title_a, title_b = _doc_title(a), _doc_title(b)

    # Phase 1 (pre-mark, fresh workspace root): both real rules surface
    # on their shared topic; record which ranks first.
    pre_block = _retrieve_block(tmp_path / "ws-pre", corpus_dir)
    pre_lines = pre_block.splitlines()
    idx_a = next((i for i, l in enumerate(pre_lines) if title_a in l), None)
    idx_b = next((i for i, l in enumerate(pre_lines) if title_b in l), None)
    if idx_a is None or idx_b is None:
        pytest.skip(
            "the rule pair no longer co-surfaces on the topic prompt "
            f"(corpus drift); block={pre_block!r}"
        )
    if idx_a < idx_b:
        stale, stale_title = a, title_a
        successor, successor_title = b, title_b
    else:
        stale, stale_title = b, title_b
        successor, successor_title = a, title_a

    # Mark the front-runner superseded by the other — the PRODUCTION
    # marking entry point, on a REAL rule's real bytes.
    mark_superseded(stale, successor.name)

    # Phase 2: a production retrieval with NO pre-arranged index state
    # (fresh workspace root → fresh derived index).
    post_block = _retrieve_block(tmp_path / "ws-post", corpus_dir)
    post_lines = post_block.splitlines()
    s_idx = next(
        (i for i, l in enumerate(post_lines) if successor_title in l), None
    )
    m_idx = next(
        (i for i, l in enumerate(post_lines) if stale_title in l), None
    )
    assert s_idx is not None, (
        "the successor must still surface on the topic post-mark; "
        f"block={post_block!r}"
    )
    if m_idx is not None:
        # The stale rule still surfaces: it must rank BEHIND its
        # successor AND carry the supersession annotation — the reader
        # never sees the bare stale rule.
        assert s_idx < m_idx, (
            "the successor must rank ahead of the marked rule; "
            f"block={post_block!r}"
        )
        assert "superseded by" in post_lines[m_idx].lower(), (
            "a surfaced superseded rule must carry its annotation; "
            f"line={post_lines[m_idx]!r}"
        )
    # m_idx None ⇒ the successor ranks ahead by the marked rule's
    # demotion out of the surfaced set — the AC's first disjunct.
