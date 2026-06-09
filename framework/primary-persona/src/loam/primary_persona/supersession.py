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

"""Supersession marking (FBM correctness cycle, Slice 3 — AC.SUP.1 +
AC.SUP.3).

The T1.1 ``superseded-by: <relative-path>`` frontmatter convention
exists and is honored on the episode-store side
(:mod:`loam.primary_persona.file_memory` — ``SUPERSEDED_PENALTY``);
until this cycle there was NO production mechanism to APPLY the mark
(the 2026-06-09 instance was a hand-edit) and the corpus-retrieval
side ignored it entirely. This module is the marking mechanism; the
corpus-retrieval honor lands in :mod:`keep_pace.corpus_index`.

Contracts:

  * **AC.SUP.1** — :func:`mark_superseded` durably writes the mark
    on-disk in the EXISTING convention's key (``superseded-by``), plus
    a ``superseded-date``, machine-readable
    (:func:`read_supersession` round-trips it). Because the key is
    the same one the episode ranker reads, marking an episode file
    with this entry point composes with the existing
    ``SUPERSEDED_PENALTY`` honor unchanged.
  * **AC.SUP.3** — marking ANNOTATES, never deletes: the document's
    content beyond the marker lines is preserved byte-for-byte, and
    :func:`unmark_superseded` restores the original bytes exactly
    (a mark-created frontmatter block is removed whole; a pre-existing
    block keeps its other keys). Un-marking restores prior retrieval
    behaviour because retrieval keys ONLY on the marker's presence.

Stdlib-only; no LLM anywhere (D5 — premise-flip AUTO-detection is a
named deferral; humans/persona invoke the mark).
"""

from __future__ import annotations

import re
from datetime import date as _date
from pathlib import Path
from typing import Optional

#: The T1.1 convention's key (file_memory.py frontmatter contract).
SUPERSEDED_BY_KEY = "superseded-by"
#: The mark's date key (AC.SUP.1 — the mark carries date + successor).
SUPERSEDED_DATE_KEY = "superseded-date"

# A leading YAML frontmatter block: ``---`` first line through the
# next ``---`` line. Mirrors the corpus-index reader's shape so a mark
# written here is read there.
_FRONTMATTER_RE = re.compile(
    r"\A---[ \t]*\r?\n(.*?\r?\n)---[ \t]*\r?\n", re.DOTALL
)
_MARKER_LINE_RE = re.compile(
    rf"^(?:{SUPERSEDED_BY_KEY}|{SUPERSEDED_DATE_KEY}):[^\n]*\n",
    re.MULTILINE,
)


def mark_superseded(
    path: Path | str,
    successor: str,
    *,
    date: Optional[str] = None,
) -> None:
    """Durably mark the document at *path* superseded-by *successor*
    (AC.SUP.1 — the production marking entry point).

    Writes ``superseded-by: <successor>`` + ``superseded-date:
    <YYYY-MM-DD>`` into the document's leading YAML frontmatter —
    extending an existing block (replacing any prior marker lines), or
    prepending a minimal new block when the document has none. The
    content beyond the marker is preserved byte-for-byte (AC.SUP.3).

    *successor* is the convention's relative-path pointer to the
    superseding document; *date* defaults to today (ISO).
    """
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    when = date if date is not None else _date.today().isoformat()
    marker = (
        f"{SUPERSEDED_BY_KEY}: {successor}\n"
        f"{SUPERSEDED_DATE_KEY}: {when}\n"
    )
    m = _FRONTMATTER_RE.match(text)
    if m:
        inner = _MARKER_LINE_RE.sub("", m.group(1))
        new_block = f"---\n{inner}{marker}---\n"
        text = new_block + text[m.end():]
    else:
        text = f"---\n{marker}---\n" + text
    target.write_text(text, encoding="utf-8")


def unmark_superseded(path: Path | str) -> None:
    """Remove the supersession marker, restoring prior retrieval
    behaviour (AC.SUP.3 — reversibility).

    Removes the ``superseded-by`` / ``superseded-date`` lines from the
    leading frontmatter; a block left EMPTY by the removal (i.e. one
    the mark itself created) is removed whole, restoring the original
    bytes exactly. A document with no marker is left untouched.
    """
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return
    inner = _MARKER_LINE_RE.sub("", m.group(1))
    if inner.strip():
        new_text = f"---\n{inner}---\n" + text[m.end():]
    else:
        new_text = text[m.end():]
    if new_text != text:
        target.write_text(new_text, encoding="utf-8")


def read_supersession(path: Path | str) -> Optional[dict[str, str]]:
    """Machine-read the mark (AC.SUP.1): ``{"superseded-by": …,
    "superseded-date": …}`` or ``None`` when the document is not
    marked / unreadable (fail-soft — a read surface never raises on a
    missing or malformed file)."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return None
    out: dict[str, str] = {}
    for line in m.group(1).splitlines():
        key, _, value = line.partition(":")
        key = key.strip()
        if key in (SUPERSEDED_BY_KEY, SUPERSEDED_DATE_KEY) and value.strip():
            out[key] = value.strip()
    if SUPERSEDED_BY_KEY not in out:
        return None
    return out
