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

"""AC-FBM-W-4 (LIVE-CORPUS COLD-WALK — the bar) — the hard floor on the REAL
``feedback_*.md`` corpus, in a fresh process, through the production
``retrieve()`` entry-point with no pre-arranged retrieval state.

The test COPIES the live rules corpus into a TEMP repo root (it never reads or
writes the live store), adds ``pinned: true`` frontmatter to ONE real doc, then
runs a single ``retrieve()`` against a hyper-relevant freshly-written episode
flood. The pinned rule must survive in the surfaced block. The same scenario
WITHOUT the pin must drop the rule — the multiplier-alone-cannot-do-it
demonstration, proven end-to-end on the live corpus.

Skips (does not fail) if the live corpus dir is absent (CI / a fresh machine).
"""

from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path

import pytest

from loam.primary_persona.file_memory import FileMemoryStore
from loam.primary_persona.keep_pace.retrieval import RetrievalConfig, retrieve


LIVE_CORPUS = (
    Path.home()
    / ".claude"
    / "projects"
    / "-Users-lukeivers-pos3"
    / "memory"
)

# A distinctive token that does NOT appear in the live corpus, so the
# hyper-relevant episode flood is the only thing that matches it strongly —
# the pinned rule has ~0 relevance to this token and would drop without the
# floor.
HOT_TOKEN = "zzqxflooble"


def _copy_live_corpus(dest: Path) -> list[Path]:
    """Copy the live ``feedback_*.md`` corpus into a temp dir (read-only of the
    source; never writes the live store)."""
    dest.mkdir(parents=True, exist_ok=True)
    copied: list[Path] = []
    for src in sorted(LIVE_CORPUS.glob("*.md")):
        if not src.is_file():
            continue
        out = dest / src.name
        shutil.copyfile(src, out)
        copied.append(out)
    return copied


def _pin_doc(path: Path) -> str:
    """Prepend ``pinned: true`` frontmatter to a copied corpus doc.

    Returns the doc's title (first ``# `` heading or prettified stem) so the
    test can assert the doc's pointer surfaces. If the doc already has a
    frontmatter block, the pin key is injected into it; else a fresh block is
    written ahead of the body."""
    raw = path.read_text(encoding="utf-8")
    if raw.startswith("---\n"):
        end = raw.find("\n---", 4)
        head = raw[4:end]
        rest = raw[end:]
        new = "---\n" + head + "\npinned: true" + rest
    else:
        new = "---\npinned: true\n---\n" + raw
    path.write_text(new, encoding="utf-8")
    # Title = first heading in the body (after any frontmatter).
    for line in raw.splitlines():
        s = line.strip()
        if s.startswith("# "):
            return s[2:].strip()
    return path.stem.replace("_", " ").replace("-", " ")


def _seed_hot_episodes(memory_dir: Path, group_id: str, n: int) -> None:
    store = FileMemoryStore(memory_dir=memory_dir)
    for i in range(n):
        store.write_episode(
            name=f"turn/hot-{i}",
            body=(
                f"{HOT_TOKEN} {HOT_TOKEN} {HOT_TOKEN} this turn is overwhelmingly "
                f"about {HOT_TOKEN} and nothing else, repeated {HOT_TOKEN}."
            ),
            source_description="test seed",
            reference_time=datetime.now(timezone.utc),
            source="message",
            group_id=group_id,
        )


def _run(tmp_path: Path, *, pin: bool) -> tuple[str, str]:
    """Build a temp corpus (live copy, one doc optionally pinned) + a hot
    episode flood, run retrieve() on the hot token, return (block, pinned_title)."""
    corpus_dir = tmp_path / "memory"
    copied = _copy_live_corpus(corpus_dir)
    assert copied, "no live corpus docs copied"
    # Choose a stable real doc to pin — the ruthless-feedback rule (always
    # present in the live corpus; a genuinely critical always-include rule).
    target = corpus_dir / "feedback_ruthless_feedback.md"
    if not target.exists():
        target = copied[0]
    pinned_title = _pin_doc(target) if pin else _doc_title_only(target)

    episode_dir = tmp_path / "episodes-store"
    _seed_hot_episodes(episode_dir, "pos3", 6)

    cfg = RetrievalConfig(
        workspace_root=tmp_path,
        memory_dir=corpus_dir,
        claude_homes=(),
        objectives_home=tmp_path / "no-objectives",
        episode_memory_dir=episode_dir,
        episode_group_ids=("pos3",),
        top_n=5,
    )
    block = retrieve(prompt=HOT_TOKEN, config=cfg)
    return block, pinned_title


def _doc_title_only(path: Path) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if s.startswith("# "):
            return s[2:].strip()
    return path.stem.replace("_", " ").replace("-", " ")


@pytest.mark.skipif(
    not LIVE_CORPUS.is_dir(), reason="live feedback_*.md corpus not present"
)
def test_AC_FBM_W_4_pinned_rule_survives_on_live_corpus(tmp_path: Path) -> None:
    """A ``pinned: true`` real corpus doc co-surfaces against a hyper-relevant
    episode flood — through the production retrieve() on the LIVE corpus copy."""
    block, pinned_title = _run(tmp_path, pin=True)
    assert block, "retrieve() produced no injection on the live-corpus cold-walk"
    assert pinned_title and pinned_title in block, (
        "the pinned critical rule must survive in the surfaced block against "
        f"the hyper-relevant episode flood; title={pinned_title!r} "
        f"block={block!r}"
    )


@pytest.mark.skipif(
    not LIVE_CORPUS.is_dir(), reason="live feedback_*.md corpus not present"
)
def test_AC_FBM_W_4_unpinned_variant_drops_on_live_corpus(tmp_path: Path) -> None:
    """The multiplier-alone-can't-do-it demonstration, end-to-end on the live
    corpus: the SAME rule WITHOUT the pin drops out of the surfaced set — the
    hot-token episodes own all the slots. Only the force-include rescued it."""
    block, pinned_title = _run(tmp_path, pin=False)
    # The hot token matches no corpus doc strongly; the un-pinned rule has ~0
    # relevance and is not force-included, so it does not surface.
    assert pinned_title not in block, (
        "without the pin the ~0-relevance rule must drop under the "
        f"hyper-relevant episodes — proving the floor is load-bearing; "
        f"title={pinned_title!r} block={block!r}"
    )
