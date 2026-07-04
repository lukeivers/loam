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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied. See the License for the specific language governing
# permissions and limitations under the License.

"""The boundary gate — built READY, INACTIVE by default (AC.AR.12 / D8).

The gate is the automation surface: it fires the review when a concrete
artifact crosses a consequence boundary (dev seal/merge, document send,
publication/delivery) and blocks the boundary on a BLOCK verdict. It is
built and tested now but does NOT fire live until the activation switch
is flipped (owner-gated). While inactive, :func:`gate_review` is a no-op
that returns a not-fired sentinel — it NEVER blocks a real ship/seal/send.

Boundary classification (D2 / outcome-shape #1): the gate fires on a
concrete produced artifact crossing a boundary and NOT on scratch,
bookkeeping, or in-progress drafts. :func:`crosses_boundary` is the
classifier; it is the wiring POINT for a real hook (a PreToolUse on a
seal command, a pre-send document hook) — that wiring is the ACTIVATION
step and is intentionally not connected here.

Per ODD §2.5: :func:`gate_review` -> AC.AR.12 (no-op while inactive;
blocks on BLOCK when active); :func:`crosses_boundary` -> AC.AR.12 /
D2 (fires on boundary artifacts, not scratch).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from .activation import gate_active
from .critic import ModelFn
from .pipeline import ReviewResult, run_standard_review
from .tiers import Tier, run_deep_review
from .validation import ValidatorFn


class GateOutcome(str, Enum):
    """What the gate did (AC.AR.12)."""

    NOT_FIRED_INACTIVE = "NOT_FIRED_INACTIVE"
    NOT_FIRED_NOT_A_BOUNDARY = "NOT_FIRED_NOT_A_BOUNDARY"
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"


@dataclass
class GateDecision:
    """The gate's decision (AC.AR.12).

    ``outcome`` is the gate-level result; ``review`` is the underlying
    review result when the gate fired (else None). ``blocked`` is the
    single boolean a caller wires to "hold the boundary".
    """

    outcome: GateOutcome
    review: Optional[ReviewResult] = None

    @property
    def blocked(self) -> bool:
        return self.outcome is GateOutcome.BLOCK


# Path/label markers that mean "scratch / bookkeeping / in-progress" — the
# gate does NOT fire on these (D2). A concrete produced artifact crossing
# a boundary is everything else.
_NON_BOUNDARY = re.compile(
    r"(^|/)\.scratch/|(^|/)scratch/|(^|/)tmp/|/draft[s]?/|\.wip\b|"
    r"\.bak\b|/bookkeeping/|WIP|/notes?/",
    re.IGNORECASE,
)


def crosses_boundary(artifact_label: str) -> bool:
    """Does this artifact cross a consequence boundary (D2 / AC.AR.12)?

    ``artifact_label`` is the path or name of the produced thing. Returns
    False for scratch / bookkeeping / in-progress / draft markers (the
    review must NOT fire on those), True otherwise. This is the classifier
    a live hook would consult; the hook wiring is the activation step.
    """
    if not artifact_label.strip():
        return False
    return _NON_BOUNDARY.search(artifact_label) is None


def gate_review(
    artifact: str,
    objective: str,
    artifact_label: str,
    *,
    tier: Tier = Tier.STANDARD,
    domain: Optional[str] = None,
    model_fn: ModelFn | None = None,
    validator_fn: ValidatorFn | None = None,
) -> GateDecision:
    """The boundary gate — a NO-OP while inactive (AC.AR.12 / D8).

    Order of checks:

      1. Activation switch OFF (default) -> NOT_FIRED_INACTIVE. The gate
         NEVER blocks a real boundary while inactive — this is the
         ready-but-inactive contract.
      2. Not a boundary artifact (scratch/bookkeeping/draft) ->
         NOT_FIRED_NOT_A_BOUNDARY.
      3. Active + boundary -> run the review (STANDARD or DEEP) and
         BLOCK on a blocking verdict, else ALLOW.

    Even when active, a BLOCK is owner-overridable via
    ``review.verdict.override(reason)`` before the boundary is enforced
    (D8) — the override is an explicit act recorded on the verdict.
    """
    if not gate_active():
        return GateDecision(outcome=GateOutcome.NOT_FIRED_INACTIVE)
    if not crosses_boundary(artifact_label):
        return GateDecision(outcome=GateOutcome.NOT_FIRED_NOT_A_BOUNDARY)

    runner = run_deep_review if tier is Tier.DEEP else run_standard_review
    review = runner(
        artifact,
        objective,
        domain=domain,
        model_fn=model_fn,
        validator_fn=validator_fn,
    )
    outcome = (
        GateOutcome.BLOCK if review.verdict.blocking else GateOutcome.ALLOW
    )
    return GateDecision(outcome=outcome, review=review)
