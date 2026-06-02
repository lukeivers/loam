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

"""loam egress-consent — the privacy floor in front of every off-machine send.

Public surface:

* The bundle model — ``EgressBundle`` / ``EgressItem`` / ``BundleState`` /
  ``ItemDecision`` / ``ItemKind`` (``bundle``).
* The fail-closed release gate — ``EgressReleaseGate`` / ``EgressRefused`` /
  ``release`` (``gate``).
* The content-identity binding — ``approval_binding`` / ``binding_matches``
  (``binding``).
* The pre-review secret auto-redaction — ``redact_secrets`` (``redaction``).
* The two-layer review surface — ``render_review`` / ``apply_decision``
  (``review``).
* The bug-report consumer entry-point — ``run_bug_report`` /
  ``assemble_report_bundle`` / ``ReportInterview`` / ``ReportOutcome``
  (``bug_report``).

The never-leak guarantee is enforced by construction: the bundle FSM defaults
to a no-egress state, every error path stays in a no-egress state, and the ONLY
transition to RELEASED runs through a single audited, deterministic, fail-closed
gate. There is no second egress path.
"""

from __future__ import annotations

from .binding import approval_binding, binding_matches
from .bug_report import (
    ReportInterview,
    ReportOutcome,
    assemble_report_bundle,
    run_bug_report,
)
from .bundle import (
    BundleState,
    EgressBundle,
    EgressItem,
    ItemDecision,
    ItemKind,
)
from .gate import EgressRefused, EgressReleaseGate, release
from .redaction import redact_secrets
from .review import apply_decision, render_review

__all__ = [
    "BundleState",
    "EgressBundle",
    "EgressItem",
    "ItemDecision",
    "ItemKind",
    "EgressReleaseGate",
    "EgressRefused",
    "release",
    "approval_binding",
    "binding_matches",
    "redact_secrets",
    "render_review",
    "apply_decision",
    "ReportInterview",
    "ReportOutcome",
    "assemble_report_bundle",
    "run_bug_report",
]
