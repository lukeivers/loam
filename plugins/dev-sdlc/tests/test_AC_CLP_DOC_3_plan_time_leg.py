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

"""AC.CLP-DOC.3 — plan-docs authored after the seal carry a named
primitive-check section, and the convention doc says so.

In-slice verification (the post-seal "next plan-doc conforms" claim
rides the roadmap checkpoint per plan §3.5):
  1. The plan-docs convention names the REQUIRED Primitive-check section.
  2. The plan template carries the slot (so generated plans inherit it).
  3. This cycle's own plan-doc carries its first conforming instance
     (§2bis).
"""

from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
CONVENTION = (
    REPO_ROOT
    / "plugins"
    / "dev-sdlc"
    / "docs"
    / "conventions"
    / "plan-docs.md"
)
TEMPLATE = (
    REPO_ROOT
    / "plugins"
    / "dev-sdlc"
    / "templates"
    / "plan"
    / "dev-discipline.md"
)
THIS_PLAN = (
    REPO_ROOT
    / "docs"
    / "plans"
    / "claude-leverage-program-s2-doctrine.md"
)


def test_AC_CLP_DOC_3_convention_names_required_primitive_check() -> None:
    body = CONVENTION.read_text(encoding="utf-8")
    assert "Primitive check" in body, (
        "plan-docs convention must name the Primitive-check section"
    )
    low = body.lower()
    assert "required" in low and "primitive" in low, (
        "the Primitive-check section must be named REQUIRED in the "
        "convention"
    )
    # It names the native-primitive-or-bespoke shape.
    assert "bespoke" in low, (
        "the convention must allow `bespoke — <reason>` as a valid "
        "primitive-check answer"
    )


def test_AC_CLP_DOC_3_template_carries_primitive_check_slot() -> None:
    body = TEMPLATE.read_text(encoding="utf-8")
    assert "Primitive check" in body, (
        "plan template must carry a Primitive-check section so generated "
        "plans inherit it"
    )
    assert "{{PRIMITIVE_CHECK}}" in body, (
        "plan template must carry the PRIMITIVE_CHECK substitution slot"
    )


def test_AC_CLP_DOC_3_this_plan_is_first_conforming_instance() -> None:
    """This cycle's plan-doc carries its own primitive-check section
    (§2bis) — the first conforming instance."""
    body = THIS_PLAN.read_text(encoding="utf-8")
    assert "Primitive check" in body, (
        "this plan-doc must carry its own Primitive-check section as the "
        "first conforming instance (§2bis)"
    )
