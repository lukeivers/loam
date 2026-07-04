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

"""Isolation seed assembly — the critic's fresh context (P1 / AC.AR.2).

The critic runs in a fresh isolated context seeded with EXACTLY four
things: the artifact, its stated objective, the domain methodology, and
the review protocol. Explicitly EXCLUDED: the parent conversation, the
author's reasoning / self-assessment, owner enthusiasm, and (where
strippable) authorship provenance. One leaked "the team is excited about
this" defeats the whole design (P1) — so the seed is BUILT from an
allow-list of blocks, never by passing through an ambient context.

This mirrors the sealed frame_judge ``assemble_seed`` discipline
(microkernel + objective + result ONLY), generalized to the adversarial
review's four blocks.

The two-phase ordering (P2 / J2) is the load-bearing structural choice:

  * :func:`derive_seed`   -> the DERIVE phase. Objective + methodology +
    protocol ONLY. The artifact is ABSENT (AC.AR.3). The critic
    constructs, from this alone, what a correct artifact must contain —
    so its later dissent is authentically held (Nemeth, GEN §3), not an
    assigned "be brutal" pose (F5).
  * :func:`diff_seed`     -> the DIFF phase. Seeded with the derived
    correct-artifact spec + the artifact, tasked to diff (AC.AR.3).

Per ODD §2.5: :func:`strip_provenance` -> AC.AR.2 (self-assessment /
provenance exclusion); the two seed builders -> AC.AR.2 + AC.AR.3.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Seed block delimiters — the seed is assembled from exactly these
# labeled blocks (AC.AR.2). The parent conversation is NEVER a block.
BLOCK_OBJECTIVE = "=== stated objective (attack THIS) ==="
BLOCK_METHODOLOGY = "=== domain review methodology (your failure taxonomy) ==="
BLOCK_PROTOCOL = "=== review protocol ==="
BLOCK_ARTIFACT = "=== the artifact ==="
BLOCK_DERIVED_SPEC = "=== what a correct artifact MUST contain (your derivation) ==="

# Provenance / self-assessment markers stripped from an artifact before
# it reaches the critic (AC.AR.2 / P1). These carry the author's world —
# exactly the sycophancy carrier (AI §F1) the isolation exists to cut.
_PROVENANCE_PATTERNS = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        r"^\s*author\s*:.*$",
        r"^\s*written by.*$",
        # Enthusiasm/self-praise: a first-person/team subject anywhere on
        # the line paired with a praise word. Requires the pronoun+praise
        # pairing so it does not strip a substantive line that merely
        # contains e.g. "confidence interval".
        r"\b(we|i|the team|the author)\b.{0,40}\b(excited|proud|confident|"
        r"thrilled|delighted|pleased|our best)\b.*$",
        r"^\s*self[- ]assessment\s*:.*$",
        r"^\s*reviewer['s]* note\s*:.*$",
        r"^\s*owner\s+(says|thinks|loves|wants)\b.*$",
    )
)


@dataclass(frozen=True)
class ReviewInputs:
    """The four allow-listed inputs a seed may draw from (AC.AR.2).

    Nothing else is a legal seed source. ``artifact`` is the raw text of
    the produced thing under review; ``objective`` is its stated
    objective / acceptance intent (the thing the critic attacks);
    ``methodology`` is the domain review-methodology text (the failure
    taxonomy); ``protocol`` is the review protocol instruction.
    ``strip_provenance`` (default True) removes authorship / self-praise
    lines from the artifact before it is seeded.
    """

    artifact: str
    objective: str
    methodology: str
    protocol: str
    strip_provenance: bool = True


def strip_provenance(text: str) -> str:
    """Remove authorship / self-assessment / enthusiasm lines (AC.AR.2).

    Line-oriented: drops any line matching a provenance pattern. The
    substance of the artifact is untouched — only the author's-world
    signal (the sycophancy carrier, AI §F1) is removed. Where provenance
    is NOT line-strippable (woven into prose), the isolation still holds
    at the context level: the critic never sees the parent conversation
    or the author's separate self-review.
    """
    kept = [
        line
        for line in text.splitlines()
        if not any(p.match(line) for p in _PROVENANCE_PATTERNS)
    ]
    return "\n".join(kept)


def _artifact_for_seed(inputs: ReviewInputs) -> str:
    return (
        strip_provenance(inputs.artifact)
        if inputs.strip_provenance
        else inputs.artifact
    )


def derive_seed(inputs: ReviewInputs) -> str:
    """The DERIVE-phase seed — artifact ABSENT (AC.AR.3 / P2).

    Objective + methodology + protocol ONLY. The critic is asked to
    construct, from these alone, the specification a correct artifact
    would have to satisfy — BEFORE it ever sees the artifact. This is the
    structural guarantee that the derivation is artifact-blind, which is
    what makes the later dissent authentic rather than role-played
    (Nemeth, GEN §3). The artifact string is NEVER concatenated into this
    seed — verified by AC.AR.3.
    """
    return "\n".join(
        (
            BLOCK_OBJECTIVE,
            "",
            inputs.objective.strip(),
            "",
            BLOCK_METHODOLOGY,
            "",
            inputs.methodology.strip(),
            "",
            BLOCK_PROTOCOL,
            "",
            inputs.protocol.strip(),
        )
    )


def diff_seed(inputs: ReviewInputs, derived_spec: str) -> str:
    """The DIFF-phase seed — derived spec + artifact (AC.AR.3 / P2).

    Seeded with the critic's OWN artifact-blind derivation plus the
    (provenance-stripped) artifact, tasked to diff reality against the
    derivation. Because the derivation was produced in the prior,
    artifact-absent phase, the disagreements the diff surfaces are
    genuinely held positions.
    """
    return "\n".join(
        (
            BLOCK_OBJECTIVE,
            "",
            inputs.objective.strip(),
            "",
            BLOCK_DERIVED_SPEC,
            "",
            derived_spec.strip(),
            "",
            BLOCK_METHODOLOGY,
            "",
            inputs.methodology.strip(),
            "",
            BLOCK_ARTIFACT,
            "",
            _artifact_for_seed(inputs),
        )
    )


def seed_contains_artifact(seed: str, artifact: str) -> bool:
    """True if a distinctive slice of the artifact appears in the seed.

    Used by AC.AR.3 to assert the DERIVE seed does NOT contain the
    artifact. Compares on a distinctive contiguous slice (robust to
    whitespace-only differences and to a short artifact).
    """
    needle = artifact.strip()
    if not needle:
        return False
    # A distinctive slice: the longest line >= 12 chars, else the whole.
    lines = [ln.strip() for ln in needle.splitlines() if len(ln.strip()) >= 12]
    probe = max(lines, key=len) if lines else needle[:40]
    return probe in seed
