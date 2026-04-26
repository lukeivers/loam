"""SessionStart CLI entry — writes the corpus-load sentinel.

Added by the structural-enforcement A1 substrate amendment.

Reads the Claude Code SessionStart JSON envelope from stdin (the
documented hook surface), extracts ``workspace.project_dir`` and
``session_id``, and calls
``corpus_load_sentinel.write_corpus_load_sentinel`` to persist the
sentinel for this session.

Per AC.SE.4: completes within the 5s SessionStart inner-hook budget
and exits 0 on every path (fail-soft). The hook does not emit any
``additionalContext`` — the sentinel is consumed by future gates,
not by the model directly. Should the future composition surface
the sentinel into ``additionalContext`` (per the plan-doc Lens 1
note), this CLI's stdout becomes the surface; today it is empty.

Stdlib only (loam_mode is optional; the helper inside
``corpus_load_sentinel`` falls back to ``"normal-use"`` mode when
loam_mode is unavailable, so this entry remains stdlib-only at
import time).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure sibling modules are importable when invoked as
# ``python <hooks-dir>/corpus_load_session_start.py``.
_HOOKS_DIR = Path(__file__).resolve().parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

from corpus_load_sentinel import write_corpus_load_sentinel  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    """Read the SessionStart envelope; write the sentinel; exit 0.

    The hook never raises into Claude Code: every exception path
    converts to ``return 0`` so the SessionStart fan-out continues.
    """
    try:
        raw = sys.stdin.read()
    except Exception:  # noqa: BLE001 — fail-soft per AC.SE.4
        return 0
    if not raw.strip():
        return 0
    try:
        envelope = json.loads(raw)
    except json.JSONDecodeError:
        return 0
    if not isinstance(envelope, dict):
        return 0

    workspace = envelope.get("workspace")
    if not isinstance(workspace, dict):
        return 0
    workspace_root = workspace.get("project_dir")
    if not isinstance(workspace_root, str) or not workspace_root:
        return 0

    session_id = envelope.get("session_id")
    if not isinstance(session_id, str) or not session_id:
        return 0

    try:
        write_corpus_load_sentinel(workspace_root, session_id=session_id)
    except Exception:  # noqa: BLE001 — fail-soft per AC.SE.4
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
