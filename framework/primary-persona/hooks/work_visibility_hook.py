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

"""Work-visibility refresh hook — thin Claude-Code shim (AC.WVS-FRESH.2).

Composes onto Claude Code's hook primitive. Registered on the events
that change work-state (SessionStart / PreCompact / UserPromptSubmit /
PostToolUse — the reinject-carrier events), Claude Code spawns this
script with a JSON envelope on stdin. The script delegates to the
importable logic in ``loam.primary_persona.hooks_work_visibility`` —
regenerate the always-openable status file (a) + emit the live
in-context block (c), off the SHARED aggregator.

The SEALED deliverable is this framework-tracked entry-point + its
tests. Wiring it into a live ``.claude/settings.json`` is owner-gated
instance-config — OUT of cycle; the wiring step is surfaced, not
self-applied.

Fail-closed contract (the statusline.py precedent): any unhandled
exception → empty ``additionalContext`` + exit 0. The shim itself is
import-light (only adds the package ``src`` to ``sys.path`` if the
package is not already importable) so a pre-venv spawn still runs.
"""

from __future__ import annotations

import sys
from pathlib import Path


def _ensure_importable() -> None:
    """Best-effort: make ``loam.primary_persona`` importable when the
    shim is spawned outside the editable-installed venv (defensive of
    the pre-venv spawn path; fail-closed if it cannot)."""
    try:
        import loam.primary_persona  # noqa: F401
        return
    except Exception:
        pass
    # hooks/ -> component root -> src
    src = Path(__file__).resolve().parent.parent / "src"
    if src.is_dir() and str(src) not in sys.path:
        sys.path.insert(0, str(src))


def main() -> int:
    try:
        _ensure_importable()
        from loam.primary_persona.hooks_work_visibility import main as _main

        return _main()
    except Exception:
        # Fail-closed: never crash the host event. Emit nothing.
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
