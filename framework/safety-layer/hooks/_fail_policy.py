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

"""Per-gate fail-policy primitive (AC.DSF.5 — G15 keystone).

The reusable mechanism that lets each PreToolUse gate DECLARE how it
behaves when its *own* evaluation faults — raises, times out, or
receives input it cannot classify. Two policies:

* ``FAIL_OPEN`` — the advisory-guard convention ``D-SECHK.FAIL-OPEN``:
  on fault, ALLOW (emit nothing, exit 0). Every existing sealed
  advisory guard keeps this behaviour, and it is the DEFAULT
  (``DEFAULT_FAIL_POLICY``) — so a gate that declares nothing fails
  open, exactly as before. An advisory guard that failed CLOSED would
  block all work on its first bug; that is why the convention is not
  blanket-flipped (plan Decision C).
* ``FAIL_CLOSED`` — the floor destructive-gate posture (G15): on
  fault against a destructive *candidate*, DENY (emit the PreToolUse
  deny envelope). A non-candidate (a read / a non-destructive op)
  still fails OPEN even under a fail-closed gate — parity with the
  floor gate's existing behaviour, so a fail-closed gate never blocks
  reads merely because its own check errored on an unrelated input.

This is a per-gate *field*: a gate module declares ``FAIL_POLICY =
FailPolicy.FAIL_OPEN`` (or ``FAIL_CLOSED``) and routes its top-level
fault handler through :func:`apply_fault_policy`. The convention lives
where it is amended (``framework/safety-layer/``); only the floor
destructive-gate class opts into ``FAIL_CLOSED``.

Stdlib only (enum, json, sys, dataclasses) and ZERO intra-package
imports, so a bare-script PreToolUse hook can import it via the
hooks-dir sibling pattern (``sys.path.insert(0, <hooks dir>); from
_fail_policy import ...``) WITHOUT pulling the ``loam.safety_layer``
package — and its heavier dependencies — at hook runtime. This mirrors
``_secret_patterns.py``: hook-runtime robustness is the reason the
advisory guards are stdlib-only, and this primitive preserves it.

The deny envelope shape emitted here is the contract Claude Code
honours as a PreToolUse block even under bypass-all permission modes
(empirically verified at build time: a ``permissionDecision: deny``
blocks the tool call under both ``--permission-mode bypassPermissions``
and ``--dangerously-skip-permissions``).
"""

from __future__ import annotations

import enum
import json
import sys
from dataclasses import dataclass
from typing import Any, TextIO


class FailPolicy(enum.Enum):
    """How a gate behaves when its own evaluation faults."""

    FAIL_OPEN = "fail-open"
    FAIL_CLOSED = "fail-closed"


# The default a gate gets when it declares nothing — preserves every
# existing sealed advisory guard's ``D-SECHK.FAIL-OPEN`` behaviour with
# zero regression.
DEFAULT_FAIL_POLICY: FailPolicy = FailPolicy.FAIL_OPEN


# Log decision labels — kept byte-identical to the labels the
# pre-primitive guards already wrote (``fail-open`` /
# ``deny-fail-closed`` / ``fail-open-non-candidate``) so the convention's
# audit-trail shape does not change.
LABEL_FAIL_OPEN = "fail-open"
LABEL_DENY_FAIL_CLOSED = "deny-fail-closed"
LABEL_FAIL_OPEN_NON_CANDIDATE = "fail-open-non-candidate"


@dataclass(frozen=True)
class FaultDecision:
    """The terminal decision a faulting gate must take.

    ``deny`` is the only behavioural output (emit a deny vs allow);
    ``policy`` and ``label`` carry the declared policy and the
    audit-log label so the caller can log without re-deriving them.
    """

    deny: bool
    policy: FailPolicy
    label: str


def resolve_fault(
    policy: FailPolicy, *, is_destructive_candidate: bool = False
) -> FaultDecision:
    """Resolve a gate's on-fault decision from its declared policy.

    * ``FAIL_CLOSED`` + destructive candidate  -> DENY.
    * ``FAIL_CLOSED`` + non-candidate          -> ALLOW (read parity).
    * ``FAIL_OPEN`` (and any default)          -> ALLOW.

    Pure: no I/O, no globals. The caller decides whether to emit/log.
    """
    if policy is FailPolicy.FAIL_CLOSED:
        if is_destructive_candidate:
            return FaultDecision(
                deny=True, policy=policy, label=LABEL_DENY_FAIL_CLOSED
            )
        return FaultDecision(
            deny=False, policy=policy, label=LABEL_FAIL_OPEN_NON_CANDIDATE
        )
    # FAIL_OPEN — the advisory convention and the safe default.
    return FaultDecision(deny=False, policy=policy, label=LABEL_FAIL_OPEN)


def deny_payload(reason: str) -> dict[str, Any]:
    """The canonical PreToolUse deny envelope.

    This exact shape is honoured by Claude Code as a tool-call block
    under every permission mode, including bypass-all (build-time
    keystone-verified)."""
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def emit_deny(reason: str, *, out: TextIO | None = None) -> None:
    """Write the PreToolUse deny envelope to ``out`` (default stdout)."""
    stream = sys.stdout if out is None else out
    stream.write(json.dumps(deny_payload(reason), ensure_ascii=False))
    stream.flush()


def apply_fault_policy(
    policy: FailPolicy,
    *,
    is_destructive_candidate: bool = False,
    deny_reason: str = "",
    out: TextIO | None = None,
) -> FaultDecision:
    """Resolve and ENACT a gate's on-fault decision.

    Resolves the decision from the declared ``policy`` (and, for a
    fail-closed gate, whether the faulting input was a destructive
    candidate), emits the deny envelope to ``out`` iff the decision is
    DENY, and returns the :class:`FaultDecision` so the caller can log
    its ``label``. A gate's top-level fault handler reduces to::

        except Exception as exc:
            decision = apply_fault_policy(
                FAIL_POLICY,
                is_destructive_candidate=<candidate?>,
                deny_reason=<plain-words reason>,
            )
            _log(..., decision=decision.label, exception=repr(exc))
            return 0
    """
    decision = resolve_fault(
        policy, is_destructive_candidate=is_destructive_candidate
    )
    if decision.deny:
        emit_deny(deny_reason, out=out)
    return decision
