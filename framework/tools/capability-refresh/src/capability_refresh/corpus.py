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

"""Corpus entry I/O — stamping, stale-marking, substitution, and the
no-cross-class-write structural guard.

AC.CLP-CUR.7: the refresh NEVER writes outside Class A / Class A-prime
paths. ``best-practice/`` (Class B) is structurally out of reach — every
write in the package resolves through the guards here, so an upstream
fixture (or a hostile sources.yaml) cannot induce a Class B write.
This is the locked no-cross-class-write invariant
(docs/capability-corpus/AUTHORING.md + research doc section 7bis.3).

AC.CLP-CUR.5: ``stamp_source`` / ``mark_stale`` keep the ``## Source``
block honest — every successful fetch refreshes ``source_fetch_ts``;
a failed fetch sets ``source_status: stale (...)`` and leaves the body
+ old timestamp untouched (never silently current).

AC.CLP-CUR.6: ``apply_reprojection`` lands a same-statement update
in-place ONLY when the superseded text is found verbatim in the entry's
projected body region; a match inside the curated
``## [user-intent phrasings]`` overlay demotes to review (overlay-touch),
and no match demotes to review (curated-divergence). Curated content is
never clobbered mechanically.
"""

from __future__ import annotations

from pathlib import Path
from typing import Tuple

# Class A (Anthropic-canonical) + Class A-prime (harness) — the ONLY
# entry prefixes the refresh may write (AC.CLP-CUR.7).
CLASS_A_PREFIXES = ("claude-code", "harness")
# Refresh-owned state dirs inside the corpus root (snapshots + the
# structured run delta + surfaced pending-deltas). Not reference docs.
STATE_DIRS = (".refresh", "pending-deltas")

OVERLAY_HEADING = "## [user-intent phrasings]"
SOURCE_HEADING = "## Source"


class CrossClassWriteError(Exception):
    """A write was attempted outside Class A / A-prime / refresh state."""


def resolve_entry_path(corpus_root: Path, entry: str) -> Path:
    """Resolve a corpus-relative entry path with the Class A guard.

    Rejects: absolute paths, traversal escaping the corpus root, and any
    first path segment not in CLASS_A_PREFIXES (so ``best-practice/...``
    — Class B — is structurally unreachable). AC.CLP-CUR.7.
    """
    corpus_root = Path(corpus_root).resolve()
    p = Path(entry)
    if p.is_absolute():
        raise CrossClassWriteError(f"entry path must be corpus-relative: {entry!r}")
    resolved = (corpus_root / p).resolve()
    try:
        rel = resolved.relative_to(corpus_root)
    except ValueError:
        raise CrossClassWriteError(f"entry path escapes the corpus root: {entry!r}")
    parts = rel.parts
    if not parts or parts[0] not in CLASS_A_PREFIXES:
        raise CrossClassWriteError(
            f"refresh may only write Class A / A-prime entries "
            f"({CLASS_A_PREFIXES}); refused: {entry!r}"
        )
    return resolved


def resolve_state_path(corpus_root: Path, *rel_parts: str) -> Path:
    """Resolve a refresh-state path (snapshots / delta / pending-deltas)
    with the same containment guard (AC.CLP-CUR.7)."""
    corpus_root = Path(corpus_root).resolve()
    resolved = (corpus_root / Path(*rel_parts)).resolve()
    try:
        rel = resolved.relative_to(corpus_root)
    except ValueError:
        raise CrossClassWriteError(f"state path escapes the corpus root: {rel_parts!r}")
    if not rel.parts or rel.parts[0] not in STATE_DIRS:
        raise CrossClassWriteError(
            f"refresh state writes are confined to {STATE_DIRS}; refused: {rel_parts!r}"
        )
    return resolved


def _section_span(text: str, heading: str) -> Tuple[int, int]:
    """(start, end) char span of a ``## ...`` section body, or (-1, -1)."""
    idx = text.find(heading)
    if idx < 0:
        return (-1, -1)
    body_start = idx + len(heading)
    nxt = text.find("\n## ", body_start)
    return (idx, nxt if nxt >= 0 else len(text))


def _rewrite_source_block(text: str, url: str, ts: str, status: str) -> str:
    """Rewrite source_url / source_fetch_ts / source_status lines inside
    the fenced block of ``## Source``. Missing lines are added; an entry
    without a Source block gets one appended (AUTHORING.md contract)."""
    start, end = _section_span(text, SOURCE_HEADING)
    if start < 0:
        block = (
            f"\n{SOURCE_HEADING}\n\n```\nsource_url: {url}\n"
            f"source_fetch_ts: {ts}\nsource_status: {status}\n```\n"
        )
        return text.rstrip("\n") + "\n" + block
    section = text[start:end]
    lines = section.splitlines()
    out = []
    seen = {"source_url": False, "source_fetch_ts": False, "source_status": False}
    fence_close_idx = None
    for i, ln in enumerate(lines):
        stripped = ln.strip()
        if stripped.startswith("source_url:") and url is not None:
            out.append(f"source_url: {url}")
            seen["source_url"] = True
        elif stripped.startswith("source_fetch_ts:") and ts is not None:
            out.append(f"source_fetch_ts: {ts}")
            seen["source_fetch_ts"] = True
        elif stripped.startswith("source_status:"):
            out.append(f"source_status: {status}")
            seen["source_status"] = True
        else:
            out.append(ln)
    if not seen["source_status"]:
        # insert before the closing fence
        for i in range(len(out) - 1, -1, -1):
            if out[i].strip() == "```":
                fence_close_idx = i
                break
        if fence_close_idx is not None:
            out.insert(fence_close_idx, f"source_status: {status}")
        else:
            out.append(f"source_status: {status}")
    new_section = "\n".join(out)
    if section.endswith("\n") and not new_section.endswith("\n"):
        new_section += "\n"
    return text[:start] + new_section + text[end:]


def stamp_source(entry_path: Path, url: str, ts: str) -> None:
    """Successful fetch: refresh source_url + source_fetch_ts, status
    ``current`` (AC.CLP-CUR.5). Replaces a seed ``internal:<label>``
    source_url with the real upstream URL on first re-projection
    (D-CUR.3)."""
    text = entry_path.read_text(encoding="utf-8")
    entry_path.write_text(_rewrite_source_block(text, url, ts, "current"), encoding="utf-8")


def mark_stale(entry_path: Path, reason: str, ts: str) -> None:
    """Failed fetch: mark the entry STALE; body + old source_url +
    old source_fetch_ts retained untouched (AC.CLP-CUR.5)."""
    text = entry_path.read_text(encoding="utf-8")
    entry_path.write_text(
        _rewrite_source_block(text, None, None, f"stale ({reason}; marked {ts})"),
        encoding="utf-8",
    )


def apply_reprojection(entry_path: Path, old: str, new: str) -> str:
    """Attempt to auto-land a same-statement update in the entry body.

    Returns one of:
      ``"auto-landed"``        old text found in the projected body
                               region and substituted with new text.
      ``"overlay-touch"``      old text found ONLY inside the curated
                               ``[user-intent phrasings]`` overlay —
                               REVIEW; the overlay is never auto-edited.
      ``"curated-divergence"`` old text not found verbatim — the entry
                               body has curatorially diverged from the
                               upstream statement; REVIEW, never a
                               mechanical guess. (AC.CLP-CUR.6)
    """
    text = entry_path.read_text(encoding="utf-8")
    overlay_start, overlay_end = _section_span(text, OVERLAY_HEADING)
    source_start, _ = _section_span(text, SOURCE_HEADING)
    body_end = len(text)
    for boundary in (overlay_start, source_start):
        if boundary >= 0:
            body_end = min(body_end, boundary)
    needle = old.strip()
    if not needle:
        return "curated-divergence"
    idx = text.find(needle)
    in_body = 0 <= idx < body_end if idx >= 0 else False
    if idx >= 0 and not in_body:
        if overlay_start >= 0 and overlay_start <= idx < overlay_end:
            return "overlay-touch"
        return "curated-divergence"
    if not in_body:
        return "curated-divergence"
    new_text = text[:idx] + new.strip() + text[idx + len(needle):]
    entry_path.write_text(new_text, encoding="utf-8")
    return "auto-landed"
