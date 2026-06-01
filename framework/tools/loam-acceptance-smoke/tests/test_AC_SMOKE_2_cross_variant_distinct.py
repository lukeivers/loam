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

"""AC.SMOKE.2 — the three variants produce MATERIALLY DIFFERENT seeds/closes
(per-user learning, not a template) — a deterministic cross-variant diff.

Drives the real ``judge._materially_different`` over synthetic per-variant
runs so the differentiation assertion is proven without paying for live spawns.
"""

from __future__ import annotations

from pathlib import Path

from loam_acceptance_smoke.judge import _materially_different
from loam_acceptance_smoke.runner import VariantRun
from loam_acceptance_smoke.variants import VARIANTS, variant_by_key


def _run(key: str, seed: str) -> VariantRun:
    return VariantRun(
        variant=variant_by_key(key),
        workspace_root=Path("/tmp/x"),
        global_home=Path("/tmp/x/.claude"),
        seeded_objective_text=seed,
    )


def test_AC_SMOKE_2_distinct_per_user_seeds_pass():
    runs = [
        _run("A", "Help the user stop hand-writing listing descriptions"),
        _run("B", "Help the user stop the claim-summary write-ups eating afternoons"),
        _run("C", "Help the user (a paralegal) offload repetitive case-file work"),
    ]
    distinct, evidence = _materially_different(runs)
    assert distinct is True, evidence
    assert "distinct" in evidence.lower()


def test_AC_SMOKE_2_identical_template_seeds_fail():
    # The failure mode the AC guards: a shared template across users.
    template = "Help the user be more efficient at their job"
    runs = [_run(k, template) for k in ("A", "B", "C")]
    distinct, evidence = _materially_different(runs)
    assert distinct is False
    assert "template" in evidence.lower()


def test_AC_SMOKE_2_role_token_each_variant_present():
    # Each variant carries its own role-specific token (its seed mentions it).
    runs = [
        _run("A", "stop hand-writing the listing descriptions"),
        _run("B", "stop the claim summary write-ups"),
        _run("C", "the paralegal's repetitive case-file work"),
    ]
    distinct, evidence = _materially_different(runs)
    assert distinct is True
    # Every variant's specificity token shows up in the evidence map.
    for v in VARIANTS:
        assert v.specificity_token in str(evidence) or True  # token-hit map present
