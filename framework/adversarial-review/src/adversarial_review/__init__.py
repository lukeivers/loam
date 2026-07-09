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

"""adversarial_review — loam's standing adversarial-review capability.

Ships READY but INACTIVE (the gate does not fire live until owner
activation). The MANUAL on-demand path is the usable v1 surface. See
``README.md`` for the design + the pin -> module map.

Public API:

  * :func:`review_file` / :func:`review_text` — manual on-demand review.
  * :func:`render_report` — render a review as a text report.
  * :func:`gate_review` — the boundary gate (no-op while inactive).
  * :func:`calibrate` / :func:`score` — seeded-flaw calibration.
  * :class:`Tier`, :class:`Verdict`, :class:`Finding`, :class:`Severity`.
"""

from __future__ import annotations

from .calibration import CalibrationResult, SeededFlaw, calibrate, score
from .findings import Finding, Severity, ValidationState
from .gate import GateDecision, GateOutcome, gate_review
from .insession import (
    emit_derive_prompt,
    emit_diff_prompt,
    replay_model_fn,
    run_insession_standard,
)
from .manual import render_report, review_file, review_text
from .pipeline import ReviewResult, run_standard_review
from .registry import (
    DEFAULT_LEG_NAME,
    DEFAULT_REGISTRY,
    ModelLeg,
    ModelRoleRegistry,
    Role,
)
from .tiers import Tier, run_deep_review
from .verdict import Disposition, Verdict

__version__ = "0.1.0"

__all__ = [
    "review_file",
    "review_text",
    "render_report",
    "gate_review",
    "GateDecision",
    "GateOutcome",
    "run_standard_review",
    "run_deep_review",
    "run_insession_standard",
    "emit_derive_prompt",
    "emit_diff_prompt",
    "replay_model_fn",
    "ReviewResult",
    "Role",
    "ModelLeg",
    "ModelRoleRegistry",
    "DEFAULT_REGISTRY",
    "DEFAULT_LEG_NAME",
    "Tier",
    "Verdict",
    "Disposition",
    "Finding",
    "Severity",
    "ValidationState",
    "calibrate",
    "score",
    "SeededFlaw",
    "CalibrationResult",
    "__version__",
]
