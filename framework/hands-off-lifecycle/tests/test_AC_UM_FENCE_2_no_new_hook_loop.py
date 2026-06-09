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

"""AC.UM.FENCE.2 — no new hook, no new loop, no consolidation pass.

N4's read-path is a NEW contributor on the EXISTING keep-pace
UserPromptSubmit hook (Lens 1 — compose, don't add a hook). It adds no
scheduled job, no ``claude -p`` consolidation, no distress detector —
verified by absence: the live ``contributors()`` list gains the N4
contributor, but the hook EVENT surface gains no new registration.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
KEEP_PACE_DIR = (
    REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks" / "keep_pace"
)
sys.path.insert(0, str(KEEP_PACE_DIR))

import user_prompt_submit as ups  # noqa: E402


def test_AC_UM_FENCE_2_n4_contributor_on_existing_hook() -> None:
    """The N4 read-path is a contributor on the EXISTING UserPromptSubmit
    contributors() list — not a new hook."""
    names = [c.name for c in ups.contributors()]
    assert "n4-interaction-model" in names, (
        "the N4 read-path contributor is not registered on the live hook"
    )
    # It composes alongside the existing KP1 + KP7 contributors (no
    # displacement).
    assert "kp1-retrieval" in names
    assert "kp7-reassert" in names


def test_AC_UM_FENCE_2_no_new_hook_module_added() -> None:
    """N4 adds NO new hook entry-point module — the read-path lives in the
    EXISTING user_prompt_submit.py + a primary-persona contributor. The
    keep_pace hook dir gains no new ``*_submit`` / ``*_hook`` entry."""
    keep_pace_hooks = sorted(
        p.name for p in KEEP_PACE_DIR.glob("*.py") if p.is_file()
    )
    # The keep_pace hook modules are the pre-N4 set — N4 added none here
    # (the new code is a contributor in primary-persona + a registration
    # line in the existing user_prompt_submit.py).
    # FBM correctness cycle (2026-06-09) rebaseline: `claim_guard.py`
    # added to the expected set — it is a routed SIBLING module the
    # existing draft-gate calls (the same non-entry-point class as
    # `draft_gate.py` itself: no `main()`, no stdin envelope, no
    # settings-fragment registration), explicitly authorized by that
    # cycle's plan §5 fence ("a new claim-guard layer or routed
    # sibling module"). N4's contract — no new hook ENTRY-POINT
    # module, no new hook EVENT — is untouched: the event surface
    # still consists of `pre_tool_use.py` + `user_prompt_submit.py`
    # only. In-band retire-and-rebaseline per the loose-AC-text
    # discipline (`feedback_loose_AC_text_fix_AC_not_implementation`).
    expected = {
        "__init__.py",
        "chain_runner.py",
        "claim_guard.py",
        "draft_gate.py",
        "pre_tool_use.py",
        "user_prompt_submit.py",
    }
    actual = {n for n in keep_pace_hooks if not n.startswith("test_")}
    # No N4-named new hook module.
    new_modules = actual - expected
    assert not new_modules, (
        f"N4 added a new hook module {new_modules!r} — the fence (compose, "
        f"don't add a hook) is breached"
    )


def test_AC_UM_FENCE_2_no_scheduled_job_or_consolidation() -> None:
    """The N4 contributor wrapper carries no scheduled-job / consolidation
    / distress-detector surface — it is a synchronous read-and-inject only.
    Verified by absence in the registration wrapper source."""
    import inspect

    src = inspect.getsource(ups._n4_interaction_model_contributor)
    for banned in ("cron", "schedule", "claude -p", "subprocess", "distress"):
        assert banned not in src, (
            f"the N4 read-path wrapper carries {banned!r} — the fence "
            f"(no new loop/consolidation) is breached"
        )
