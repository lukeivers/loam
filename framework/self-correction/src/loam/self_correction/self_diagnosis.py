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

"""Self-diagnosis content — what the distress trip CHECKS (AC.SR-DISTRESS.2).

When the distress detector trips (part 1 of the self-recovery system), it
opens a real self-correction ``user_reported`` episode via the EXISTING
engine. This module is the *content* of that diagnosis — the two
load-bearing checks the silent-night root causes demand:

  (a) **Comms-path liveness** — is the agent's user-facing output actually
      reaching the user's channel, or only going to a terminal the user
      never sees? (The invisible-text bug —
      ``feedback_narration_is_not_action`` §"The two stacked bugs".)

  (b) **Recent-actions-vs-claims** — was work claimed that has no artifact
      on disk? (The narration-not-action bug — a turn that ends cleanly
      having narrated progress without doing it.)

This module owns the diagnosis CONTENT, not the orchestration (plan §2):
the correction engine, episode store, and notifier already exist. The new
work is WHAT the diagnosis establishes + a thin wiring that feeds the
existing ``build_trigger_from_user_report`` -> ``controller.intake``.

Determinism: both checks are pure functions over injected probes /
on-disk artifact facts. No LLM, no API key (``feedback_no_anthropic_api_key``).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Awaitable, Callable

from .triggers import build_trigger_from_user_report


# ---------------------------------------------------------------------------
# Check (a): comms-path liveness.
# ---------------------------------------------------------------------------

#: A comms-path liveness probe returns True when the user-facing channel is
#: actually delivering to the user (vs a terminal they never see). The
#: probe is injected — in production it is the telegram-interface
#: ``AvailabilityProbe`` (composed by the watchdog); here the diagnosis only
#: needs the boolean answer, so it accepts any callable returning bool.
CommsLivenessProbe = Callable[[], bool]


@dataclass(frozen=True)
class CommsPathFinding:
    """The comms-path liveness result."""

    reaching_user: bool
    #: A short, plain-language phrase describing the state (no internal IDs).
    detail: str


def check_comms_path(probe: CommsLivenessProbe) -> CommsPathFinding:
    """Check whether the agent's replies are reaching the user.

    *probe* answers "is the user-visible channel live?" — True means
    replies reach the user; False means output is going somewhere the
    user cannot see (the invisible-text failure).
    """
    try:
        live = bool(probe())
    except Exception:  # noqa: BLE001 — a probe error is itself "not reaching"
        live = False
    if live:
        return CommsPathFinding(
            reaching_user=True,
            detail="replies are reaching you",
        )
    return CommsPathFinding(
        reaching_user=False,
        detail="replies are not reaching you right now",
    )


# ---------------------------------------------------------------------------
# Check (b): recent-actions-vs-claims (the narration-not-action check).
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ClaimCheck:
    """One claimed-work item paired with the artifact path that would
    prove it was actually done."""

    #: Plain-language description of what was claimed ("saved your notes").
    claim: str
    #: The on-disk path whose existence proves the claim. The check is
    #: existence-on-disk: present -> verified; absent -> unverified.
    artifact_path: Path


@dataclass(frozen=True)
class ActionsVsClaimsFinding:
    """The actions-vs-claims result — names which claims are unverified."""

    all_verified: bool
    #: Plain-language descriptions of claims with NO artifact on disk.
    unverified_claims: tuple[str, ...]


def check_actions_vs_claims(
    claims: tuple[ClaimCheck, ...],
) -> ActionsVsClaimsFinding:
    """Verify each claimed-work item against its artifact on disk.

    A claim whose ``artifact_path`` does not exist is the
    narration-not-action failure: work was narrated but the artifact that
    would prove it is absent. Returns the plain-language list of
    unverified claims.
    """
    unverified = tuple(
        c.claim for c in claims if not Path(c.artifact_path).exists()
    )
    return ActionsVsClaimsFinding(
        all_verified=not unverified,
        unverified_claims=unverified,
    )


# ---------------------------------------------------------------------------
# The composed self-diagnosis.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SelfDiagnosis:
    """The full diagnosis the distress trip runs — both load-bearing checks.

    ``healthy`` is True iff replies reach the user AND every claim is
    verified on disk. When False, ``comms`` / ``actions`` name what is
    wrong (in plain language, for the recovery surface to render)."""

    comms: CommsPathFinding
    actions: ActionsVsClaimsFinding

    @property
    def healthy(self) -> bool:
        return self.comms.reaching_user and self.actions.all_verified


def run_self_diagnosis(
    *,
    comms_probe: CommsLivenessProbe,
    claims: tuple[ClaimCheck, ...],
) -> SelfDiagnosis:
    """Run both checks and return the composed diagnosis.

    This is the diagnosis CONTENT AC.SR-DISTRESS.2 pins: it establishes
    (a) comms-path liveness and (b) recent-actions-vs-claims — the two
    silent-night root causes. A spurious trip on a healthy system finds
    nothing wrong (``healthy is True``) and is cheap + quiet.
    """
    return SelfDiagnosis(
        comms=check_comms_path(comms_probe),
        actions=check_actions_vs_claims(claims),
    )


# ---------------------------------------------------------------------------
# Wiring: a distress trip opens a REAL user_reported correction episode via
# the EXISTING engine (Lens 1 — compose, do not rebuild).
# ---------------------------------------------------------------------------

#: An ``intake`` callable — the existing ``SelfCorrectionController.intake``
#: coroutine. Typed structurally so the wiring does not import the
#: controller (avoids a cycle) and tests can pass a fake.
IntakeFn = Callable[..., Awaitable[object]]


async def open_user_reported_correction(
    *,
    intake: IntakeFn,
    description: str,
    reporter: str = "primary-persona",
    related_scope_id: str | None = None,
) -> object:
    """Build a ``user_reported`` trigger from the distress description and
    feed it to the existing correction intake.

    This is the seam where part 1 (detection) meets the existing engine:
    ``build_trigger_from_user_report`` is the sealed self-correction
    trigger surface; ``intake`` is the sealed controller path. The new
    code is only the wiring — no parallel engine.
    """
    trigger = build_trigger_from_user_report(
        description=description,
        related_scope_id=related_scope_id,
        reporter=reporter,
    )
    return await intake(trigger)
