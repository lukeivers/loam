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

"""The fleet page production entry point (WS-A3).

``generate_page(out_path, *, fleet_source, cost_source, decisions_source)``
is the single command the cron/launchd regenerator invokes and the same
entry point every AC test drives.  It reads each source through an
INJECTED zero-arg callable (default = the real reader in ``sources``),
degrades PER SOURCE, renders, and writes the file — overwriting any
stale page in place (AC.PAGE.2b).

Per-source degrade (D-A3-2, AC.PAGE.3): each source call is wrapped in
its own ``try/except``.  A raise → that source is ``MISSING`` (the panel
shows "source unavailable"); an empty-but-present value renders its own
empty state.  One source failing never blanks the page and never invents
data.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Callable, TypeVar

from .render import render_page

_T = TypeVar("_T")


def _safe(source: Callable[[], _T]) -> _T | None:
    """Call a source; on ANY exception return ``None`` (MISSING).

    The breadth is deliberate: an unavailable source can surface as
    ImportError (uninstalled), OSError (store/file gone), or a
    component's own typed error (corrupted state).  All of them mean the
    same thing to the page — this panel cannot be drawn — and none of
    them may take the whole page down (AC.PAGE.3).  Preserves the
    source's return type so the renderer's ``dict|None`` / ``list|None``
    parameters stay type-checked."""
    try:
        return source()
    except Exception:
        return None


def generate_page(
    out_path: Path | str,
    *,
    fleet_source: Callable[[], dict],
    cost_source: Callable[[], list[dict]],
    decisions_source: Callable[[], list[dict]],
    now: float | None = None,
) -> Path:
    """Read every source, render the page, write it to ``out_path``.

    Returns the written path.  The three ``*_source`` callables are the
    injection seam: the real CLI passes the ``sources`` readers bound to
    real roots; the AC suites pass fixtures / stubs / raising callables
    against the SAME entry point (D-A3-1)."""
    now = time.time() if now is None else now
    generated_iso = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(now))

    fleet = _safe(fleet_source)
    cost_rows = _safe(cost_source)
    decisions = _safe(decisions_source)

    html = render_page(
        fleet=fleet,
        cost_rows=cost_rows,
        decisions=decisions,
        generated_iso=generated_iso,
    )

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    return out_path
