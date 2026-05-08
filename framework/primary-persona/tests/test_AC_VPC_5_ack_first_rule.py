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

"""AC.VPC.5.* — ack-first persona contract amendment (v0.1.2 item 5).

The framework template
``primary-persona/templates/persona-template/prompt.md`` carries a
new operational-rule subsection ``### Acknowledge first on non-
trivial requests`` (AC.VPC.5.1) that lands the ack-first behavioural
default per:

  - v0.1.x roadmap §2 v0.1.2 item 5 (scope).
  - v0.1.x roadmap §5 Decision B (locked: hard rule with 5 explicit
    triggers).
  - FIDRAFT entry "Acknowledge-first on complex requests"
    (2026-05-03; rationale + composition).

The rule is hard, not heuristic (AC.VPC.5.3): imperative voice;
explicit trigger list; explicit carve-out; absence-as-observable-
violation framing (mirrors the swarming-corpus model-rationale
absence-as-violation pattern).

Plan: docs/plans/v0-1-2-ack-first-persona-contract.md
"""

from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
TEMPLATE_PROMPT_MD = (
    REPO_ROOT
    / "framework" / "primary-persona"
    / "templates"
    / "persona-template"
    / "prompt.md"
)


def _body() -> str:
    return TEMPLATE_PROMPT_MD.read_text()


def _ack_subsection() -> str:
    """Return the ack-first subsection text (heading-to-next-heading)."""
    body = _body()
    start = body.find("### Acknowledge first on non-trivial requests")
    assert start >= 0, (
        "ack-first subsection heading missing from template prompt.md"
    )
    # Find the next ``### `` or ``## `` heading after the ack subsection.
    next_h3 = body.find("\n### ", start + 1)
    next_h2 = body.find("\n## ", start + 1)
    candidates = [n for n in (next_h3, next_h2) if n > 0]
    end = min(candidates) if candidates else len(body)
    return body[start:end]


# ---- AC.VPC.5.1 — subsection structure + content ----


def test_AC_VPC_5_1_subsection_heading_present_under_operational_rules():
    """The ``### Acknowledge first on non-trivial requests`` heading
    is present under the ``## Operational rules`` section."""
    body = _body()
    assert "### Acknowledge first on non-trivial requests" in body
    # Heading positioned under the ``## Operational rules`` section
    # (not under a different ``## `` parent).
    ops_idx = body.find("## Operational rules")
    ack_idx = body.find("### Acknowledge first on non-trivial requests")
    assert ops_idx >= 0
    assert ack_idx > ops_idx, (
        "ack-first heading must appear after the ``## Operational rules`` heading"
    )
    # No intermediate ``## `` heading between operational-rules parent
    # and the ack subsection.
    intermediate = body[ops_idx + len("## Operational rules"):ack_idx]
    assert "\n## " not in intermediate, (
        "ack-first heading lands outside the ``## Operational rules`` parent"
    )


def test_AC_VPC_5_1_five_triggers_named():
    """All five triggers from FIDRAFT are named in the subsection.

    The triggers are quoted verbatim from the FIDRAFT entry
    "Acknowledge-first on complex requests" (2026-05-03):
      (a) ≥3 tool calls expected
      (b) ≥1 background-agent dispatch
      (c) decision/judgment vs pure execution
      (d) file authoring vs reading
      (e) message itself is multi-paragraph or multi-question
    """
    sub = _ack_subsection()
    lower = sub.lower()
    # (a) tool-call threshold
    assert "tool call" in lower or "tool-call" in lower
    assert "≥3" in sub or "3 tool" in lower or "three tool" in lower
    # (b) background dispatch
    assert "background" in lower
    assert "dispatch" in lower
    # (c) decision/judgment vs execution
    assert "decision" in lower or "judgment" in lower or "judgement" in lower
    assert "execution" in lower
    # (d) file authoring vs reading
    assert "authoring" in lower or "author" in lower
    assert "reading" in lower or "read" in lower
    # (e) multi-paragraph / multi-question message
    assert "multi-paragraph" in lower or "multi paragraph" in lower
    assert "multi-question" in lower or "multi question" in lower


def test_AC_VPC_5_1_carve_out_named():
    """The trivial-back-and-forth carve-out is named in the subsection."""
    sub = _ack_subsection()
    lower = sub.lower()
    assert "trivial" in lower, "carve-out (trivial back-and-forth) not named"
    # At least one of the example carve-out shapes is named (yes/no,
    # single-fact lookup, simple status, one-line confirmation).
    examples = ("yes/no", "single-fact", "single fact", "simple status",
                "one-line", "one line", "confirmation")
    assert any(e in lower for e in examples), (
        f"no carve-out example named (looking for any of: {examples})"
    )


def test_AC_VPC_5_1_ack_shape_literal_present():
    """The ack-shape literal example (``got it — doing X`` or
    equivalent quoted shape) is present in the subsection."""
    sub = _ack_subsection()
    lower = sub.lower()
    assert "got it" in lower, (
        'ack-shape literal "got it — doing X" missing from subsection'
    )


def test_AC_VPC_5_1_absence_as_violation_framed():
    """The absence-as-observable-violation framing is present."""
    sub = _ack_subsection()
    lower = sub.lower()
    assert "violation" in lower, (
        "absence-as-observable-violation framing missing from subsection"
    )
    assert "observable" in lower, (
        "the rule must explicitly call its violation 'observable'"
    )


# ---- AC.VPC.5.3 — hard-rule shape, not heuristic ----


def test_AC_VPC_5_3_hard_rule_imperative_voice():
    """The rule reads as a hard rule, not a heuristic.

    Checks for at least one hard-rule signal among
    (``ALWAYS`` / ``always`` / ``hard rule`` / ``FIRST`` / ``first
    output``) and no softening language (``you may consider`` / ``if
    appropriate``) inside the subsection.
    """
    sub = _ack_subsection()
    lower = sub.lower()
    hard_rule_signals = (
        "always",
        "hard rule",
        "first output",
        "the first",
    )
    assert any(s in lower for s in hard_rule_signals), (
        f"no hard-rule signal in subsection (looking for any of: "
        f"{hard_rule_signals})"
    )
    # Softening language that would indicate heuristic shape.
    softeners = ("you may consider", "if appropriate", "feel free to")
    for s in softeners:
        assert s not in lower, (
            f"softening phrase {s!r} in subsection — would weaken hard-rule shape"
        )
