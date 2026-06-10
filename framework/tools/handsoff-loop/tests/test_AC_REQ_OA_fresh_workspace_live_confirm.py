"""AC.REQ.OA (outcome-altitude: true) — live confirm on a fresh workspace.

On a FRESH workspace through the production entry point
(`handsoff-loop understand --ask ...`) with NO pre-arranged state, a
typed vague ask whose wording no build agent has seen produces the
plain-language confirm (and questions iff ambiguous), and the
confirmed objective carries the ask's specifics.

Live-model test, env-gated per the component's TPI precedent: set
BFI_REAL_CLAUDE=1 to run (one real spawn-isolated `claude -p` call).
The ask wording below was composed for this test alone and exists in
no pipeline prompt, brief, or fixture.

Per docs/plans/general-build-from-intent.md §6.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

_SRC = Path(__file__).resolve().parents[1] / "src"

# Vague, build-shaped, deliberately off the back-office trio so no
# domain-keyed shortcut could help: a community-garden plot roster.
_UNSEEN_ASK = (
    "we run a little community garden and the plot signup sheet is a "
    "mess, people are double-booked on plots and I can never tell "
    "which beds are actually free - can you make me something that "
    "sorts that out"
)


@pytest.mark.skipif(
    os.environ.get("BFI_REAL_CLAUDE") != "1",
    reason="live claude -p test; set BFI_REAL_CLAUDE=1 to run",
)
def test_fresh_workspace_typed_ask_yields_live_confirm():
    with tempfile.TemporaryDirectory(prefix="bfi-oa-req-") as fresh:
        env = dict(os.environ)
        env["PYTHONPATH"] = str(_SRC)
        proc = subprocess.run(
            [sys.executable, "-m", "handsoff_loop.cli",
             "understand", "--ask", _UNSEEN_ASK],
            capture_output=True, text=True, timeout=400,
            cwd=fresh, env=env,
        )
        assert proc.returncode == 0, proc.stdout + proc.stderr
        payload = json.loads(proc.stdout)
        assert payload["understood"] is True
        confirm = payload["confirm_text"]
        # The confirm is plain language derived from THIS ask: it
        # echoes the ask's specifics (garden/plot vocabulary), not a
        # generic template.
        lowered = (confirm + " " + payload["objective"]).lower()
        assert any(tok in lowered for tok in ("plot", "garden", "bed")), (
            f"confirm/objective does not carry the ask's specifics: "
            f"{confirm!r} / {payload['objective']!r}"
        )
        # Questions iff ambiguous — the structural invariant holds on
        # the live read whichever way the model called it.
        assert payload["ambiguous"] == bool(payload["questions"])
        assert len(payload["questions"]) <= 3
        # Fresh workspace stayed fresh: understanding writes no
        # workspace content. (The spawned `claude` binary scaffolds
        # hidden session dirs like `.scratch` in its cwd — harness
        # scaffolding, not a pipeline write; dotfiles are ignored.)
        visible = [e for e in os.listdir(fresh) if not e.startswith(".")]
        assert visible == []
