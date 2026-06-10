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

"""SubagentStop hook — out-of-band frame-consistency check on a finished
subagent (loam-realignment SLICE 1b, AC.SSFC.*).

The OUT-side guarantee that pairs with 1a's IN-handoff. When a dispatched
subagent FINISHES, this hook reads the SubagentStop envelope (the
``agent_transcript_path`` field points at the finished subagent's OWN
transcript — probe-verified 2026-06-10; the ``transcript_path``
common-input field points at the PARENT session's transcript and is
never used for the judge seed — AC.FJO.1), delegates to
:func:`loam.frame_kernel.frame_judge.evaluate`
— which GATES on a structural cue (consequential subagents only), seeds a
FRESH out-of-band judge (microkernel + objective + result ONLY, never the
parent conversation), runs it as an ISOLATED ``claude -p``, and renders a
NON-BLOCKING dispatcher surface for an off-frame result — and emits that
surface (or nothing for an on-frame / trivial / degraded finish).

Production entry-point: ``main()`` reads the SubagentStop envelope from
stdin, prints the surface JSON to stdout (or nothing), exits 0. AC.SSFC.S
exercises THIS entry-point with a real finished-subagent transcript + the
real on-disk kernel.

Fail-soft contract (AC.SSFC.5): every path exits 0. The hook NEVER raises
into Claude Code's SubagentStop fan-out and NEVER blocks a subagent's
return — a judge error, an unreadable transcript, or a spawn failure all
let the subagent finish cleanly. Mirrors 1a's ``subagent_start_context.py``
exit-0 contract. The off-frame surface is a non-blocking ``systemMessage``,
NOT a ``decision: block`` (D-SSFC.4 — surface, never silently pass; no
hard abort for v1).

Invoked by ``settings.fragment.json`` under the workspace venv Python so
``loam.frame_kernel`` + the sealed ``loam_spawn_isolation`` surface import.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the frame-kernel package is importable when invoked as a script
# under the workspace venv Python (mirrors subagent_start_context.py's
# sys.path bootstrap). Installed in the venv in production; the insert is
# belt-and-suspenders for source-tree invocation (the AC.SSFC.S probe).
_SRC = Path(__file__).resolve().parent.parent / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


def main(argv: list[str] | None = None) -> int:
    """Read the SubagentStop envelope; emit the non-blocking off-frame
    surface (or nothing); exit 0.

    AC.SSFC.5: every error path returns 0 with no output (a no-op hook
    never blocks a subagent's return). The off-frame path prints the
    non-blocking surface envelope; on-frame / trivial / degraded prints
    nothing.
    """
    import json

    try:
        raw = sys.stdin.read()
    except Exception:  # noqa: BLE001 — fail-soft per AC.SSFC.5
        return 0
    if not raw.strip():
        # No envelope — nothing to evaluate; no-op, never blocks.
        return 0
    try:
        envelope = json.loads(raw)
    except json.JSONDecodeError:
        # Malformed envelope — fail-soft no-op (AC.SSFC.5).
        return 0

    try:
        from loam.frame_kernel.frame_judge import evaluate

        surface = evaluate(envelope)
    except Exception:  # noqa: BLE001 — fail-soft per AC.SSFC.5
        # Any unexpected failure: emit nothing, exit clean. The subagent
        # still finishes (the hook is a no-op on failure, never a
        # blocker).
        return 0

    if surface is not None:
        try:
            sys.stdout.write(json.dumps(surface))
            sys.stdout.write("\n")
        except Exception:  # noqa: BLE001 — even the emit is fail-soft
            return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
