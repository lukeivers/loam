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

"""Conservative glob-overlap detection (AC.LEASE.1).

Precise glob-intersection is undecidable in general, so the registry is
CONSERVATIVE: uncertain overlap counts as a conflict (a false conflict
costs a serialized dispatch; a false non-conflict costs a textual
collision the lease exists to prevent).  Two globs conflict when either:

  1. one's non-wildcard leading prefix is an ancestor-or-equal path of
     the other's prefix (same-tree / descendant / ancestor), or
  2. either glob, matched as a recursive-glob pattern, matches the
     other's leading prefix.
"""

from __future__ import annotations

import re

_META = set("*?[]")


def _prefix(glob: str) -> str:
    """Leading path segments of *glob* that contain no glob metachar."""
    out: list[str] = []
    for seg in glob.split("/"):
        if any(c in _META for c in seg):
            break
        out.append(seg)
    return "/".join(out)


def _is_ancestor_or_equal(a: str, b: str) -> bool:
    """True if concrete path *a* is an ancestor of, or equal to, *b*.

    Callers pass only non-empty prefixes here; an empty (wildcard-leading)
    prefix has no literal anchor and is handled separately in
    ``globs_conflict`` (regex match + both-unanchored conservatism).
    """
    if a == b:
        return True
    return b.startswith(a.rstrip("/") + "/")


def _glob_to_regex(glob: str) -> re.Pattern[str]:
    """Compile *glob* to a regex where ``**`` spans directories,
    ``*`` matches within a segment, and ``?`` matches one non-slash char.
    """
    out: list[str] = []
    i, n = 0, len(glob)
    while i < n:
        c = glob[i]
        if c == "*":
            if i + 1 < n and glob[i + 1] == "*":
                out.append(".*")
                i += 2
                if i < n and glob[i] == "/":
                    i += 1  # swallow the slash of "**/"
                continue
            out.append("[^/]*")
        elif c == "?":
            out.append("[^/]")
        else:
            out.append(re.escape(c))
        i += 1
    return re.compile("^" + "".join(out) + "$")


def _matches(glob: str, path: str) -> bool:
    if path == "":
        return False
    return _glob_to_regex(glob).fullmatch(path) is not None


def globs_conflict(a: str, b: str) -> bool:
    """Conservative overlap test between two glob patterns."""
    if a == b:
        return True
    pa, pb = _prefix(a), _prefix(b)
    # Same-tree / ancestor / descendant, judged on the literal prefixes.
    if pa and pb and (
        _is_ancestor_or_equal(pa, pb) or _is_ancestor_or_equal(pb, pa)
    ):
        return True
    # A wildcard pattern (e.g. ``**/package.json``) that matches the
    # other's literal prefix — catches depth-crossing patterns.
    if _matches(a, pb) or _matches(b, pa):
        return True
    # Both globs are wildcard-leading (no literal anchor): overlap cannot
    # be ruled out, so conservatively treat it as a conflict.
    if pa == "" and pb == "":
        return True
    return False
