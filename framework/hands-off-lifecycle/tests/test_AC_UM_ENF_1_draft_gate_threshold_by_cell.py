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

"""AC.UM.ENF.* — the enforce-path (D-N4.2 / AIM-2): the draft-gate
threshold is parameterized by the active area's technical-exposure cell.

This is the seam that makes the injected interaction-model directive
STRUCTURAL (the gate backs it), not merely ADVISORY. A ``deep`` exposure
area relaxes the exposure-dependent jargon classes (the user wants depth
there) while the SYNTACTIC-LEAK FLOOR (paths/SHAs/AC-IDs/ALLCAPS) is
enforced UNCONDITIONALLY regardless of any cell (G5 — no value loosens it).

A threshold lookup, NOT register-judge surgery: Layer C is untouched; the
exposure parameter only partitions Layer 1's classes.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
KEEP_PACE_DIR = (
    REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks" / "keep_pace"
)
sys.path.insert(0, str(KEEP_PACE_DIR))

import draft_gate  # noqa: E402


_JARGON_DRAFT = "we ran pytest against the manifest and checked the exit code"
_FLOOR_DRAFT = "see /Users/luke/framework/x.py at commit abc1234"


def test_AC_UM_ENF_1_deep_relaxes_jargon() -> None:
    """At ``deep`` exposure, the exposure-dependent jargon classes are
    relaxed — process jargon (pytest/manifest/exit-code) is no longer a
    block."""
    result = draft_gate.gate(_JARGON_DRAFT, exposure="deep")
    assert result.passed(), (
        f"deep exposure should relax jargon, got "
        f"{result.model_facing_report()}"
    )


def test_AC_UM_ENF_1_open_and_plain_still_block_jargon() -> None:
    """At ``open`` / ``plain`` exposure (and the None default), the jargon
    classes are STILL enforced — the pre-N4 behaviour is preserved off the
    deep path."""
    for exposure in ("open", "plain", None):
        result = draft_gate.gate(_JARGON_DRAFT, exposure=exposure)
        assert result.blocked(), (
            f"exposure {exposure!r} should still block process jargon"
        )


def test_AC_UM_ENF_1_floor_survives_deep_unconditionally() -> None:
    """The SYNTACTIC-LEAK FLOOR (paths / SHAs / AC-IDs / ALLCAPS) is
    enforced even at ``deep`` — no exposure value ever loosens it (G5)."""
    result = draft_gate.gate(_FLOOR_DRAFT, exposure="deep")
    assert result.blocked(), (
        "the syntactic-leak floor (path/SHA) must survive deep exposure "
        "unconditionally"
    )
    # AC-ID floor too.
    assert draft_gate.gate(
        "this maps to AC.KP9.1 in the spec", exposure="deep"
    ).blocked()


def test_AC_UM_ENF_1_layer1_lint_floor_partition_is_correct() -> None:
    """The floor partition is exactly the syntactic-leak set; the relaxed
    set is the exposure-dependent jargon — verified directly on
    layer1_lint."""
    # A pure-floor draft trips at deep (floor enforced).
    floor_only = draft_gate.layer1_lint(
        "look at /Users/x/a.py", exposure="deep"
    )
    assert floor_only  # the path floor still fires
    assert all(r.label in draft_gate._SYNTACTIC_LEAK_FLOOR for r in floor_only)

    # A pure-jargon draft is clean at deep (jargon relaxed).
    jargon_only = draft_gate.layer1_lint(
        "we ran pytest and sealed the manifest", exposure="deep"
    )
    assert jargon_only == []


def test_AC_UM_ENF_1_default_none_is_pre_n4_behaviour() -> None:
    """``exposure=None`` (the default) is byte-identical to the pre-N4
    layer1_lint behaviour — every class enforced, no relaxation."""
    draft = _JARGON_DRAFT
    with_none = [r.label for r in draft_gate.layer1_lint(draft, exposure=None)]
    no_arg = [r.label for r in draft_gate.layer1_lint(draft)]
    assert with_none == no_arg
    assert with_none  # the jargon classes fire (not relaxed)


def test_AC_UM_ENF_1_layerC_untouched_by_exposure() -> None:
    """The enforce-path is a Layer-1 threshold lookup ONLY — Layer C (the
    constraint check) is untouched by exposure (no register-judge
    surgery). A constraint contradiction still FLAGs at deep exposure."""
    # A draft contradicting the seeded loam-no-api-key ruling.
    contradiction = (
        "the model call uses an api key via the anthropic sdk directly"
    )
    deep = draft_gate.gate(contradiction, exposure="deep")
    # Layer C still fires (FLAG) — exposure didn't touch it. (Layer 1's
    # jargon for "api" may also fire as a floor/relax, but the LC flag is
    # the point: the constraint check is exposure-independent.)
    lc_labels = [r.label for r in deep.reasons if r.layer == "LC"]
    assert "loam-no-anthropic-api-key" in lc_labels
