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

"""SubagentStart hook — inject the loam frame-kernel context bundle into
every dispatched subagent (loam-realignment SLICE 1a, AC.SACH.*).

The keystone of the frame-robustness realignment: this is the
human->persona governance carried DOWN to the persona->subagent boundary
by lifting the SubagentStart primitive. On every subagent dispatch the
hook reads the SubagentStart envelope, composes the three-tier bundle
(microkernel + active-workstream context + relevant memory), and emits
it as ``hookSpecificOutput.additionalContext`` so the bundle lands in the
subagent's context (D-SACH.5; mirrors ``principle_reminder.py``).

Production entry-point: ``main()`` reads the SubagentStart envelope from
stdin, prints the JSON envelope to stdout. AC.SACH.S exercises THIS entry
-point with a real envelope + the real on-disk kernel, no pre-arranged
bundle.

Fail-soft contract (AC.SACH.4): every path exits 0. The hook never
raises into Claude Code's SubagentStart fan-out — a degraded bundle
(structured markers) still lets the subagent start. Mirrors
``corpus_inline_session_start.py``'s exit-0 contract.

Invoked by ``settings.fragment.json`` under the workspace venv Python so
``loam.frame_kernel`` + the persona's sealed memory surface import.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the frame-kernel package is importable when invoked as a script
# under the workspace venv Python (mirrors corpus_inline_session_start's
# sys.path bootstrap). The package is installed in the venv in
# production; the path insert is belt-and-suspenders for source-tree
# invocation (e.g. the AC.SACH.S probe).
_SRC = Path(__file__).resolve().parent.parent / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


def main(argv: list[str] | None = None) -> int:
    """Read the SubagentStart envelope; emit the context bundle; exit 0.

    AC.SACH.4: every error path returns 0 with no output (a no-op hook
    never blocks a dispatch). The success path prints the JSON
    additionalContext envelope.
    """
    import json

    try:
        raw = sys.stdin.read()
    except Exception:  # noqa: BLE001 — fail-soft per AC.SACH.4
        return 0
    if not raw.strip():
        # No envelope — still emit a microkernel-only bundle so the
        # always-on core reaches the subagent even on a degenerate
        # SubagentStart payload (AC.SACH.1 + AC.SACH.4).
        envelope: object = {}
    else:
        try:
            envelope = json.loads(raw)
        except json.JSONDecodeError:
            envelope = {}

    try:
        from loam.frame_kernel.bundle import compose_bundle, render_envelope

        bundle = compose_bundle(envelope)
        sys.stdout.write(render_envelope(bundle))
        sys.stdout.write("\n")
    except Exception:  # noqa: BLE001 — fail-soft per AC.SACH.4
        # Any unexpected failure in composition: emit nothing, exit
        # clean. The subagent still starts (the hook is a no-op on
        # failure, never a blocker).
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
