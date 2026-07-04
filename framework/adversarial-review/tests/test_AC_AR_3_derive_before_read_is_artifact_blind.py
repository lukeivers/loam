# Copyright 2026 Luke Ivers and contributors
# SPDX-License-Identifier: Apache-2.0
"""AC.AR.3 (P2/J2) — the derive phase is artifact-BLIND: the derive-phase
seed excludes the artifact bytes; the diff-phase seed carries the
derivation + the artifact. Two-spawn ordering is structural."""
from __future__ import annotations

from conftest import make_stub_critic

from adversarial_review.critic import derive_prompt, diff_prompt, run_critic
from adversarial_review.seed import (
    ReviewInputs,
    derive_seed,
    diff_seed,
    seed_contains_artifact,
)

_ARTIFACT = "the secret artifact claim is that the bridge holds 40 tons"


def _inputs() -> ReviewInputs:
    return ReviewInputs(
        artifact=_ARTIFACT,
        objective="a correct bridge spec",
        methodology="load-analysis failure taxonomy",
        protocol="premortem",
    )


def test_AC_AR_3_derive_seed_excludes_the_artifact():
    dseed = derive_seed(_inputs())
    assert not seed_contains_artifact(dseed, _ARTIFACT)
    assert "bridge holds 40 tons" not in dseed


def test_AC_AR_3_diff_seed_contains_derivation_and_artifact():
    fseed = diff_seed(_inputs(), "DERIVED: must include a load safety factor")
    assert "must include a load safety factor" in fseed
    assert seed_contains_artifact(fseed, _ARTIFACT)


def test_AC_AR_3_derive_prompt_never_carries_artifact():
    # The full DERIVE prompt (instruction + seed) must not carry the artifact.
    assert "bridge holds 40 tons" not in derive_prompt(_inputs())
    # The DIFF prompt does carry it.
    assert "bridge holds 40 tons" in diff_prompt(_inputs(), "spec")


def test_AC_AR_3_two_ordered_calls_are_made():
    # The critic makes TWO model calls in order: derive, then diff. A stub
    # that records prompts proves the derive call precedes and is
    # artifact-blind.
    seen = []

    def recorder(prompt: str):
        seen.append(prompt)
        if "You do NOT see the artifact yet" in prompt:
            return "DERIVED SPEC"
        return "FINDING\nlocation: x\nseverity: LOW\nscenario: minor.\nEND"

    findings, ran = run_critic(_inputs(), model_fn=recorder)
    assert ran is True
    assert len(seen) == 2
    # First call is the derive phase, and it did not contain the artifact.
    assert "You do NOT see the artifact yet" in seen[0]
    assert "bridge holds 40 tons" not in seen[0]
