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

"""Fetch + deterministic normalisation (AC.CLP-CUR.3 / AC.CLP-CUR.5).

The body projection is a structural transform — fetch, parse,
normalise, emit. NO LLM call enters the body path (D-CUR.4 guard:
a hallucinated claim cannot enter by construction). A fetch failure
raises ``FetchError`` so the caller marks the entry STALE rather than
silently retaining it as current (AC.CLP-CUR.5).
"""

from __future__ import annotations

import html as html_mod
import re
import urllib.error
import urllib.request
from pathlib import Path

USER_AGENT = "loam-capability-refresh/0.1 (deterministic corpus projection)"
DEFAULT_TIMEOUT = 30


class FetchError(Exception):
    """A source could not be fetched / read."""


def fetch_source(url: str, repo_root: Path, timeout: int = DEFAULT_TIMEOUT) -> str:
    """Fetch one canonical upstream. Supports http(s)://, file://, internal:<path>."""
    if url.startswith("internal:"):
        rel = url[len("internal:"):]
        # Historical seed stamps ('internal:<label>:<date>') are labels,
        # not paths; a label that does not resolve to a repo file is a
        # fetch failure -> the entry is honestly marked stale.
        path = (Path(repo_root) / rel).resolve()
        try:
            path.relative_to(Path(repo_root).resolve())
        except ValueError:
            raise FetchError(f"internal source escapes repo root: {url}")
        if not path.is_file():
            raise FetchError(f"internal source not found: {url}")
        return path.read_text(encoding="utf-8")
    if url.startswith(("http://", "https://", "file://")):
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                status = getattr(resp, "status", 200)
                if status and status >= 400:
                    raise FetchError(f"HTTP {status} fetching {url}")
                data = resp.read()
        except (urllib.error.URLError, OSError, ValueError) as exc:
            raise FetchError(f"fetch failed for {url}: {exc}") from exc
        try:
            return data.decode("utf-8")
        except UnicodeDecodeError:
            return data.decode("utf-8", errors="replace")
    raise FetchError(f"unsupported source url scheme: {url}")


_TAG_STRIP = re.compile(r"<[^>]+>")
_SCRIPT_STYLE = re.compile(r"<(script|style)\b.*?</\1>", re.S | re.I)
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


def looks_like_html(text: str) -> bool:
    head = text[:2048].lower()
    return "<html" in head or "<!doctype html" in head


def normalize(text: str) -> str:
    """Deterministic canonical form: one statement-ish unit per line.

    Markdown/plain upstreams: lines, trailing whitespace stripped,
    blank-run collapsed. HTML upstreams: scripts/styles dropped, tags
    stripped, entities unescaped, then sentence-split. The transform is
    pure text-structural — same input bytes always yield the same
    output (the determinism AC.CLP-CUR.6's partition relies on).
    """
    if looks_like_html(text):
        body = _SCRIPT_STYLE.sub(" ", text)
        body = _TAG_STRIP.sub(" ", body)
        body = html_mod.unescape(body)
        body = re.sub(r"[ \t]+", " ", body)
        body = re.sub(r"\s*\n\s*", "\n", body).strip()
        flat = " ".join(body.split())
        units = [u.strip() for u in _SENTENCE_SPLIT.split(flat) if u.strip()]
        return "\n".join(units) + ("\n" if units else "")
    lines = [ln.rstrip() for ln in text.splitlines()]
    out = []
    prev_blank = False
    for ln in lines:
        blank = not ln.strip()
        if blank and prev_blank:
            continue
        out.append(ln)
        prev_blank = blank
    while out and not out[-1].strip():
        out.pop()
    return "\n".join(out) + ("\n" if out else "")
