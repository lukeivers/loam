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

"""Read-only corpus loader (AC.CLP-PUSH-RENDER.1/.2/.5).

The corpus is READ-ONLY input to the render (plan §8.3): NOTHING in this
package writes under ``docs/capability-corpus/`` source. This module
parses each corpus entry into a :class:`CorpusEntry` carrying the entry's
class, name, title, body, the source-metadata block (source_url /
source_fetch_ts / source_status — RENDER.5 passthrough), and the set of
``[primitive: <class>:<name>]`` cross-reference citations (RENDER.2).

Class A (``claude-code/``) + Class A-prime (``harness/``) entries carry a
``## Source`` block; Class B (``best-practice/``) entries carry a
``## Trust marker`` block + ``## Cross-references`` citations. Both are
projected; the render never authors body text (RENDER.1 — every projected
SKILL body is the corpus body verbatim, no LLM pass).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

# The three corpus classes and their directory prefixes (AUTHORING.md).
# Render-state dirs that are NOT reference entries.
CLASS_DIRS = ("claude-code", "harness", "best-practice")
STATE_DIRS = (".refresh", ".pack", "pending-deltas")

SOURCE_HEADING = "## Source"
CROSSREF_HEADING = "## Cross-references"

# A corpus cross-reference citation: ``[primitive: <class>:<name>]``.
_CITATION_RE = re.compile(r"\[primitive:\s*([a-z0-9-]+):([a-z0-9_-]+)\]")
# Source-block key lines inside the fenced ``## Source`` block.
_SOURCE_URL_RE = re.compile(r"^source_url:\s*(.+?)\s*$", re.MULTILINE)
_SOURCE_TS_RE = re.compile(r"^source_fetch_ts:\s*(.+?)\s*$", re.MULTILINE)
_SOURCE_STATUS_RE = re.compile(r"^source_status:\s*(.+?)\s*$", re.MULTILINE)


@dataclass(frozen=True)
class Citation:
    """A ``[primitive: <class>:<name>]`` corpus cross-reference."""

    cls: str
    name: str

    def render(self) -> str:
        return f"[primitive: {self.cls}:{self.name}]"


@dataclass
class CorpusEntry:
    """One parsed corpus entry — the unit the render projects into a skill.

    ``citations`` is the set of ``[primitive: ...]`` cross-references the
    entry carries (RENDER.2). ``source_url`` may be a real HTTP URL, an
    ``internal:<path>`` marker, or ``None`` (Class B has no Source block —
    its provenance is the in-repo corpus path itself, carried as
    ``corpus_path``). RENDER.5: ``source_fetch_ts`` + ``source_status``
    pass through unchanged so a stale corpus entry never renders as
    silently current.
    """

    cls: str
    name: str
    title: str
    body: str
    corpus_path: str
    source_url: Optional[str] = None
    source_fetch_ts: Optional[str] = None
    source_status: Optional[str] = None
    citations: List[Citation] = field(default_factory=list)

    @property
    def is_stale(self) -> bool:
        """True when the entry's source_status names it stale (RENDER.5)."""
        return bool(self.source_status) and self.source_status.startswith("stale")


def _title_of(body: str, fallback: str) -> str:
    """First ``# Heading`` line of the entry body, else *fallback*."""
    for line in body.splitlines():
        s = line.strip()
        if s.startswith("# "):
            return s[2:].strip()
    return fallback


def _source_field(body: str, regex: re.Pattern) -> Optional[str]:
    m = regex.search(body)
    return m.group(1).strip() if m else None


def parse_entry(corpus_root: Path, rel_path: str) -> CorpusEntry:
    """Parse a single corpus entry file into a :class:`CorpusEntry`.

    *rel_path* is corpus-root-relative, e.g. ``claude-code/goal.md``. The
    first path segment is the class; the stem is the entry name.
    """
    p = (Path(corpus_root) / rel_path)
    body = p.read_text(encoding="utf-8")
    parts = Path(rel_path).parts
    cls = parts[0]
    name = Path(rel_path).stem
    title = _title_of(body, name)
    citations = [Citation(c, n) for (c, n) in _CITATION_RE.findall(body)]
    return CorpusEntry(
        cls=cls,
        name=name,
        title=title,
        body=body,
        corpus_path=f"docs/capability-corpus/{rel_path}",
        source_url=_source_field(body, _SOURCE_URL_RE),
        source_fetch_ts=_source_field(body, _SOURCE_TS_RE),
        source_status=_source_field(body, _SOURCE_STATUS_RE),
        citations=citations,
    )


def load_corpus(corpus_root: Path) -> List[CorpusEntry]:
    """Load every reference entry under the corpus root, deterministically.

    Walks ``claude-code/`` + ``harness/`` + ``best-practice/`` (skipping
    state dirs + ``AUTHORING.md`` + ``sources.yaml``), returns entries
    sorted by ``(cls, name)`` so the render output is byte-stable across
    runs (RENDER.1 determinism; RENDER.5 content-hash stability).
    """
    corpus_root = Path(corpus_root)
    entries: List[CorpusEntry] = []
    for cls in CLASS_DIRS:
        cls_dir = corpus_root / cls
        if not cls_dir.is_dir():
            continue
        for md in sorted(cls_dir.rglob("*.md")):
            rel = md.relative_to(corpus_root).as_posix()
            # Skip anything under a state dir (defensive; rglob over a
            # class dir won't reach .refresh/.pack but keep the guard).
            if any(seg in STATE_DIRS for seg in Path(rel).parts):
                continue
            entries.append(parse_entry(corpus_root, rel))
    entries.sort(key=lambda e: (e.cls, e.name))
    return entries
