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

"""★ AC.UM.READ.4 — OUTCOME-ALTITUDE (``outcome-altitude: true``).

The operational proof that the prime-objective brick FUNCTIONS: the REAL
``user-prompt-submit`` hook entry-point — ``main()`` reading a real
envelope from stdin, running the registered ``contributors()`` list
through ``run_chain``, emitting the merged ``additionalContext`` to
stdout — given a SEEDED fixture matrix, observes the correct per-area
cell in the emitted directive.

Outcome-altitude discipline (``feedback_test_outcome_altitude_required``):
  - PRODUCTION entry-point: ``user_prompt_submit.main`` (the real CLI
    entry the live hook invokes), through the registered
    ``contributors()`` list — NOT a unit call of an inner lookup.
  - NO pre-arranged inner state, NO mock of the classifier: the matrix is
    a real file on a fixture ``~/.claude`` home (``Path.home`` patched),
    the envelope is real, the classifier runs for real.
  - A STUB-class test of an inner lookup does NOT satisfy this AC; this
    test crosses the real stdin->run_chain->stdout line.
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path
from unittest import mock

import pytest

from loam.primary_persona.keep_pace import interaction_model as im
from loam.workspace_bootstrap.seed_writer import render_interaction_model


# Import the REAL hook entry-point module (the live CLI surface).
_HOOKS_KP = (
    Path(__file__).resolve().parents[3]
    / "framework"
    / "hands-off-lifecycle"
    / "hooks"
    / "keep_pace"
)
sys.path.insert(0, str(_HOOKS_KP))
import user_prompt_submit as ups  # noqa: E402


def _seed_fixture_home(tmp_path: Path) -> Path:
    """Seed an isolated ``~/.claude`` fixture home with the N3 matrix +
    a distinguishing override, returning the HOME root to patch."""
    home = tmp_path / "home"
    claude = home / ".claude"
    claude.mkdir(parents=True)
    (claude / "INTERACTION-MODEL.md").write_text(
        render_interaction_model() + "\n", encoding="utf-8"
    )
    return home


def _run_real_hook(home: Path, envelope: dict) -> str:
    """Invoke the REAL ``main()`` entry-point with stdin=envelope,
    ``Path.home`` patched at the fixture home, capturing stdout's
    additionalContext."""
    raw = json.dumps(envelope)
    buf = io.StringIO()
    with mock.patch.object(Path, "home", staticmethod(lambda: home)), \
         mock.patch.object(sys, "stdin", io.StringIO(raw)), \
         mock.patch.object(sys, "stdout", buf):
        rc = ups.main([])
    assert rc == 0  # fail-open-whole-chain (AC.KP0.4) — always exits 0
    out_raw = buf.getvalue()
    if not out_raw.strip():
        return ""
    out = json.loads(out_raw)
    return out.get("hookSpecificOutput", {}).get("additionalContext", "")


def test_AC_UM_READ_4_real_hook_injects_overridden_cell(
    tmp_path: Path,
) -> None:
    """The REAL hook entry-point, given a seeded matrix with a
    their-domain-work exposure OVERRIDE to ``plain``, injects the plain
    directive for a litrpg (their-domain-work) turn — distinguishable
    from the seeded ``open`` prior, proving the file's actual contents
    steer the live emission."""
    home = _seed_fixture_home(tmp_path)
    # Override their-domain-work exposure to PLAIN (differs from the
    # seeded OPEN prior) so the assertion proves the FILE content reached
    # the turn, not the static default.
    im.apply_override(
        area="their-domain-work",
        axis="technical-exposure",
        value="plain",
        claude_home=home / ".claude",
    )
    ctx = _run_real_hook(
        home, {"prompt": "write the next chapter of the litrpg novel canon"}
    )
    assert ctx, "the real hook emitted no additionalContext"
    # The PLAIN exposure directive (the overridden value) reached the turn.
    assert "keep the wording everyday" in ctx
    # NOT the seeded open prior's directive.
    assert "substance is always on the table" not in ctx


def test_AC_UM_READ_4_real_hook_injects_seeded_prior_cell(
    tmp_path: Path,
) -> None:
    """With ONLY the seeded matrix (no override), the real hook injects
    the seeded prior cell for a money turn — open exposure + the cautious
    surface autonomy floor."""
    home = _seed_fixture_home(tmp_path)
    ctx = _run_real_hook(
        home, {"prompt": "handle the invoice and the revenue payment"}
    )
    assert ctx, "the real hook emitted no additionalContext"
    # ops-and-money seeded prior: open exposure + surface autonomy floor.
    assert "substance is always on the table" in ctx
    assert "surface the plan" in ctx


def test_AC_UM_READ_4_real_hook_fail_open_no_matrix(tmp_path: Path) -> None:
    """The real hook with NO matrix file still exits 0 (fail-open) and the
    interaction-model contributor degrades to the openness prior — the
    turn is never broken (AC.UM.READ.2 at the live entry-point)."""
    home = tmp_path / "home"
    (home / ".claude").mkdir(parents=True)  # home exists, no matrix file
    # Must not raise; exits 0.
    ctx = _run_real_hook(home, {"prompt": "fix the python build"})
    # Either no injection or the openness-prior directive — never a crash.
    assert isinstance(ctx, str)
