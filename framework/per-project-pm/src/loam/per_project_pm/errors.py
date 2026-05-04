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

"""Named exception classes for the per-project PM component.

Per ODD §2.5: every defensive branch / failure mode maps to a named
exception class, so callers can pattern-match on intent. Cycle 2 shipped
two exceptions; Cycle 4 adds :class:`PendingResponseError` for the
``require_owner_response``-blocking enforcement.

  - :class:`PMNotFoundError` — ``contract.yaml`` absent at the named
    PM's workspace-state directory. The PM has not been authored yet;
    the caller decides whether to interpret this as an empty project
    state-of-world or prompt the operator to author. Per AC.PPM.4.
  - :class:`PMStateCorruptedError` — ``contract.yaml`` (or any
    PM-state file) present but schema mismatch (missing required field,
    unexpected ``schema_version``, malformed YAML). Fail-loud at the
    loader boundary; never silently extend a corrupt state. Per
    AC.PPM.4.
  - :class:`PendingResponseError` — caller attempted to surface a new
    question while a prior surfacing is awaiting a recorded response,
    under a contract with ``require_owner_response=True``. The blocking
    enforcement is the structural side of the SOC-2 audit-trail floor
    (Eric synthesis Decision P) at the PM boundary: production-stake
    contracts cannot dispatch a second question before the first is
    answered. Per AC.QSURF.5 (Cycle 4).
"""

from __future__ import annotations


class PerProjectPMError(Exception):
    """Base class for all per-project-pm errors.

    Callers pattern-match on this base when they want catch-all
    behaviour for any PM error; on the leaf classes when they need
    specific semantics.
    """


class PMNotFoundError(PerProjectPMError):
    """The named PM has no ``contract.yaml`` at its workspace-state path.

    Raised by :meth:`loam.per_project_pm.runtime.PMRuntime.from_workspace`
    when the PM has not been authored yet. This is **not** a fault — the
    workspace simply has no PM by that name. Callers may interpret as
    an empty project (use
    :meth:`loam.per_project_pm.runtime.PMRuntime.empty_state_for`
    to obtain the empty :class:`~loam.per_project_pm.state.StateOfWorld`)
    or prompt the operator to author the contract.

    Per AC.PPM.4 (parent plan §5).
    """


class PMStateCorruptedError(PerProjectPMError):
    """A PM-state file is present but schema mismatch detected.

    Raised by the loader when:

      - ``contract.yaml`` is present but missing a required field, has
        an invalid ``project_kind``, has a non-absolute
        ``workspace_root``, or fails any other Pydantic validation.
      - ``state.yaml`` / ``decision-queue.yaml`` is present but has an
        unexpected ``schema_version``, is malformed YAML, or fails the
        runtime schema check.

    Fail-loud at the loader boundary so the operator (or a future
    self-correction loop) can repair the file. Never silently extend
    a corrupt state — that's the M5 ODD §2.5 violation per
    ``feedback_subagent_odd_violation_halt``.

    Per AC.PPM.4 (parent plan §5).
    """


class PendingResponseError(PerProjectPMError):
    """A surfacing was attempted while a prior surfacing is awaiting
    a recorded response, under a contract with
    ``require_owner_response=True``.

    Raised by:

      - :meth:`loam.per_project_pm.runtime.PMRuntime.surface_next_question`
      - :meth:`loam.per_project_pm.runtime.PMRuntime.surface_next_questions_batch`

    when ``state.yaml`` carries a non-null ``pending_response_for``
    and the PM contract's ``require_owner_response`` is True. The
    caller resolves by invoking
    :meth:`loam.per_project_pm.runtime.PMRuntime.record_response`
    against the prior surfacing's audit-log path; subsequent
    surfacings then succeed.

    The exception body carries:

      - ``pending_question`` — the still-unanswered question text
        (so the caller can re-prompt the user).
      - ``surfaced_audit_path`` — the audit-log path of the prior
        surfacing (``record_response`` parameter for clearance).

    Per AC.QSURF.5 (Cycle 4). The blocking is the structural side of
    Eric synthesis Decision P (SOC-2 audit-trail floor): no
    surfacing slips past without a response trace at production-stake
    mode.
    """

    def __init__(
        self,
        message: str,
        *,
        pending_question: str,
        surfaced_audit_path: str,
    ) -> None:
        super().__init__(message)
        self.pending_question = pending_question
        self.surfaced_audit_path = surfaced_audit_path
