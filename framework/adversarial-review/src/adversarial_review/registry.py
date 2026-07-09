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

"""Model-role registry — {role: [model_leg]} resolved from config (WS-D1).

Generalises the one-off injectable ``ModelFn`` critic seam (``critic.py``)
into a config-addressable registry: the writer / critic / judge roles each
resolve to an ORDERED tuple of NAMED model legs. A role can point at any
backend (the default isolated Claude spawn, a ``codex exec`` leg, a local
model) as a CONFIG entry rather than a code change — WS-D2 lands the Codex
critic as this registry's first non-default entry.

This is a dict + resolver, NOT a gateway: there is no HTTP, no proxy
process, and no provider SDK here (the buy-vs-build verdict — a
fleet-routing gateway for a one-call-site problem is the wrong weight;
revisit only at ≥3 providers × ≥3 roles). A leg is just a NAME plus a
``ModelFn`` (``fn=None`` means "the component's default isolated Claude
spawn").

Default behaviour is preserved EXACTLY: :data:`DEFAULT_REGISTRY` maps all
three roles to the single leg :data:`DEFAULT_LEG_NAME` (``"claude"``) with
``fn=None``. A review run with no registry configured is byte-identical to
the pre-amendment pipeline (AC.MRR.1) — the registry is purely additive
until a non-default leg is configured.

JUDGE-ROLE GUIDANCE (docs, not a runtime guard): when a JUDGE leg is
wired (e.g. the DEEP merge-judge or a future arbitration step), it should
NOT be the same model family as the WRITER that produced the artifact —
otherwise model self-preference re-enters review at arbitration (a
same-family judge systematically favours same-family output). Cross-family
judging is the de-correlation the multi-model design exists for (Lens 0:
expose the substance — every finding names its producing model). Only the
CRITIC role has a live call site in this pipeline today; WRITER and JUDGE
are resolvable config vocabulary for when their call sites exist.

Per ODD §2.5: :class:`Role` / :class:`ModelLeg` / :class:`ModelRoleRegistry`
/ :data:`DEFAULT_REGISTRY` -> AC.MRR.1/2/3 (the config-addressable role ->
leg resolution + the byte-identical default).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, Optional, Tuple

# A model leg: prompt -> raw text (or None on failure). Mirrors
# ``critic.ModelFn`` (kept as its own alias here to avoid a circular import;
# they are the same shape by contract).
ModelFn = Callable[[str], Optional[str]]

# The default leg's name. A finding produced by the default isolated Claude
# spawn is tagged with this; the render layer suppresses the per-finding
# leg annotation when ONLY this name is present, so the default review is
# byte-identical (AC.MRR.1).
DEFAULT_LEG_NAME = "claude"


class Role(str, Enum):
    """A model-dispatch role in the review pipeline (AC.MRR.1/2/3).

    The three named roles the objective fixes. Only :attr:`CRITIC` has a
    live call site in this component's pipeline today (the two-phase
    falsification critic); :attr:`WRITER` and :attr:`JUDGE` are resolvable
    config vocabulary for when their call sites exist (a future arbitration
    /merge-judge; the artifact-producing writer). They are DATA, never an
    ``if role == …`` dispatch branch here — an unwired branch would be
    untested (an ODD violation).
    """

    WRITER = "writer"
    CRITIC = "critic"
    JUDGE = "judge"


@dataclass(frozen=True)
class ModelLeg:
    """One named model leg (AC.MRR.2/3).

    ``name`` is the label every finding this leg produces is tagged with,
    and the label the render layer / a missing-leg notice names. ``fn`` is
    the model callable (prompt -> text|None); ``fn=None`` means "use the
    component's default isolated Claude spawn" (``run_isolated_critic``),
    which is how the default leg reproduces pre-amendment behaviour without
    naming the spawn here.
    """

    name: str
    fn: Optional[ModelFn] = None


@dataclass(frozen=True)
class ModelRoleRegistry:
    """A ``{role: (leg, ...)}`` resolver (AC.MRR.1/2/3).

    Each role maps to an ORDERED tuple of legs. A role resolves to a LIST
    (not a single leg) because a role can run more than one backend — the
    critic can run Claude AND Codex (WS-D2) so their blind spots
    de-correlate, and AC.MRR.3 requires the review to "proceed with the
    remaining legs" when one is unavailable. An unconfigured role falls
    back to the single default leg, so resolution never fails.
    """

    legs: Dict[Role, Tuple[ModelLeg, ...]] = field(default_factory=dict)

    def legs_for(self, role: Role) -> Tuple[ModelLeg, ...]:
        """The ordered legs configured for ``role`` (AC.MRR.2/3).

        Falls back to a single default leg (:data:`DEFAULT_LEG_NAME`,
        ``fn=None``) for a role with no explicit config, so every role
        always resolves to at least one leg.
        """
        legs = self.legs.get(role)
        if legs:
            return legs
        return (ModelLeg(DEFAULT_LEG_NAME),)

    def resolve(self, role: Role) -> ModelLeg:
        """The PRIMARY (first) leg for ``role`` (AC.MRR.1).

        A convenience for call sites that dispatch a single leg; the
        multi-leg critic path uses :meth:`legs_for`. Never raises — an
        unconfigured role resolves to the default leg.
        """
        return self.legs_for(role)[0]

    @classmethod
    def single_default(cls, model_fn: Optional[ModelFn] = None) -> "ModelRoleRegistry":
        """A registry whose CRITIC role is one default-named leg (AC.MRR.1).

        This is the back-compat shim the pipeline builds when NO registry
        is configured: the single leg carries the caller's ``model_fn``
        (a test stub, the insession replay leg, or ``None`` for the real
        isolated spawn) under :data:`DEFAULT_LEG_NAME`. The result is
        exactly the pre-amendment single-leg critic pass — byte-identical
        output, since the render layer suppresses the leg annotation for
        the lone default name.
        """
        return cls(legs={Role.CRITIC: (ModelLeg(DEFAULT_LEG_NAME, model_fn),)})


# The default registry: all three named roles -> the single default Claude
# leg. A review run against this (or against no registry at all) reproduces
# pre-amendment behaviour exactly (AC.MRR.1). A non-default entry (WS-D2's
# Codex critic) is a CONFIG change over this, never a code change.
DEFAULT_REGISTRY = ModelRoleRegistry(
    legs={
        Role.WRITER: (ModelLeg(DEFAULT_LEG_NAME),),
        Role.CRITIC: (ModelLeg(DEFAULT_LEG_NAME),),
        Role.JUDGE: (ModelLeg(DEFAULT_LEG_NAME),),
    }
)
