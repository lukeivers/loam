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

"""Live-guard-set derivation from GROUND TRUTH (AC.FMG-CHECK.2).

The reconcile invariant: the check does NOT trust the catalogue's own claim
that a guard exists — it RESOLVES each row's ``guard_ref`` against the real
tree (a path, or a ``path:symbol`` whose symbol must be defined in the file)
and confirms ALL_GATES membership for release-gate rows. A row that claims a
guard the tree does not actually carry is a divergence — the protection
pillar must not itself hallucinate coverage (the recursive-FM.HALLUCINATION
risk, plan §10 item 2).

This module is DETERMINISTIC — pure filesystem + static text inspection, no
LLM call, no network (feedback_no_anthropic_api_key: the check must be
deterministic; if it could not be, the design would be wrong).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


def find_repo_root(start: Path | None = None) -> Path:
    """Locate the loam repo root from *start* (default: this package).

    Walks up until a directory containing both ``framework/`` and ``docs/``
    is found (the loam layout). Falls back to the package-relative root.
    """
    if start is None:
        # The package lives at framework/protection-matrix/src/loam/
        # protection_matrix; the repo root is parents[5].
        start = Path(__file__).resolve()
    cur = start if start.is_dir() else start.parent
    for cand in (cur, *cur.parents):
        if (cand / "framework").is_dir() and (cand / "docs").is_dir():
            return cand
    # Fallback: package-relative repo root.
    return Path(__file__).resolve().parents[5]


@dataclass(frozen=True)
class GuardRefResolution:
    """The result of resolving one row's ``guard_ref`` against the tree."""

    row_id: str
    guard_ref: str
    path_part: str
    symbol_part: str | None
    path_exists: bool
    symbol_defined: bool | None  # None when no symbol was requested.

    @property
    def resolved(self) -> bool:
        """True iff the ref fully resolves (path exists + symbol, if any)."""
        if not self.path_exists:
            return False
        if self.symbol_part is None:
            return True
        return self.symbol_defined is True

    def reason(self) -> str:
        if self.resolved:
            return "resolved"
        if not self.path_exists:
            return f"path does not exist: {self.path_part}"
        return f"symbol {self.symbol_part!r} not defined in {self.path_part}"


def _symbol_defined_in(text: str, symbol: str) -> bool:
    """True iff *symbol* is defined (def/class/assignment) in *text*.

    Static inspection only — matches a top-or-nested ``def``/``class`` of that
    name or a module-level ``NAME = ...`` assignment (covers function gates,
    class guards, and the ``ALL_GATES`` tuple).
    """
    pat = re.compile(
        rf"^\s*(?:def|class)\s+{re.escape(symbol)}\b"
        rf"|^{re.escape(symbol)}\s*=",
        re.MULTILINE,
    )
    return bool(pat.search(text))


def resolve_guard_ref(
    row_id: str, guard_ref: str, repo_root: Path
) -> GuardRefResolution:
    """Resolve a ``path`` or ``path:symbol`` guard_ref against the real tree.

    A guard_ref of the form ``framework/.../gates.py:check_substrate_audit``
    splits into a path (must exist as a file) and a symbol (must be defined in
    that file). A bare path must exist (file or directory). The resolution is
    the GROUND TRUTH the reconcile compares the catalogue's claim against.
    """
    path_part = guard_ref
    symbol_part: str | None = None
    # Split on the LAST colon only if the tail looks like a Python symbol
    # (so a Windows-style or URL-ish path is not mis-split). Guard refs in
    # this catalogue are POSIX repo-relative paths, so a single ':' splits.
    if ":" in guard_ref:
        head, _, tail = guard_ref.rpartition(":")
        if head and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", tail):
            path_part, symbol_part = head, tail

    target = (repo_root / path_part).resolve()
    path_exists = target.exists()
    symbol_defined: bool | None = None
    if symbol_part is not None:
        if path_exists and target.is_file():
            try:
                text = target.read_text(encoding="utf-8")
            except OSError:
                text = ""
            symbol_defined = _symbol_defined_in(text, symbol_part)
        else:
            symbol_defined = False

    return GuardRefResolution(
        row_id=row_id,
        guard_ref=guard_ref,
        path_part=path_part,
        symbol_part=symbol_part,
        path_exists=path_exists,
        symbol_defined=symbol_defined,
    )
