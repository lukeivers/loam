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

"""AC.DCGID.1 — the question-identity filter counts a shared token
toward contradiction-resolution only when it is DISTINCTIVE: not a
generic stopword (1a) and not corpus-ubiquitous (1b — its full-ledger
declared-vocab document frequency exceeds the ubiquity cutoff). This is
the unit-level proof of the fix's signal; the live false-positive it
defeats is in test_AC_DCGID_OA_*.

dcg-question-identity-match, owner ruling D-DCGID.1.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
KEEP_PACE_DIR = (
    REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks" / "keep_pace"
)
sys.path.insert(0, str(KEEP_PACE_DIR))

from claim_guard import (  # noqa: E402
    _declared_vocab_overlap,
    _distinctive_tokens,
)


@dataclass
class _Rec:
    question: str = ""
    workstream: str = ""
    entities: tuple = ()
    aliases: tuple = ()
    status: str = "ruled"


def test_AC_DCGID_1a_stopwords_dropped() -> None:
    # Pure generic claim-language + function words carry no identity:
    # every token is a stopword, so none survives (no corpus needed).
    shared = {"what", "happens", "and", "the", "question", "remains"}
    assert _distinctive_tokens(shared, None) == set()


def test_AC_DCGID_1b_corpus_ubiquitous_token_dropped() -> None:
    # "loam" appears in 5 of 7 records (> 40% cutoff) → ubiquitous,
    # dropped; "fbm" appears in 1 → distinctive, kept. The stopword
    # filter alone would keep both (neither is a stopword); the
    # corpus-frequency leg is what discriminates.
    corpus = {"__nrec__": 7, "loam": 5, "fbm": 1, "build": 1}
    shared = {"loam", "fbm", "build"}
    assert _distinctive_tokens(shared, corpus) == {"fbm", "build"}


def test_AC_DCGID_1b_without_corpus_only_stopword_leg() -> None:
    # corpus_frequency None → ubiquity leg inert, stopword leg applies.
    shared = {"loam", "fbm", "what"}
    assert _distinctive_tokens(shared, None) == {"loam", "fbm"}


def test_AC_DCGID_1_overlap_counts_only_distinctive() -> None:
    # The live false-positive shape: an unrelated ruled record sharing
    # only generic claim-language + the ubiquitous "loam" with the
    # subject. Identity overlap must be < 2 (here: 1, "build").
    rec = _Rec(
        question="What happens to the FBM co-citation spread after the eval?",
        workstream="loam",
        entities=("fbm", "co-citation", "spread"),
    )
    subject_tokens = {
        "which", "model", "runs", "substantive", "loam", "build",
        "work", "and", "what", "happens", "on", "stall",
    }
    corpus = {"__nrec__": 7, "loam": 5, "happens": 2, "build": 1}
    overlap = _declared_vocab_overlap(
        rec, subject_tokens, corpus_frequency=corpus
    )
    # shared tokens: {loam, build, happens}; loam ubiquitous-dropped,
    # happens stopword-dropped → only "build" survives → 1 < 2.
    assert overlap < 2, f"generic+ubiquitous brush must not resolve; got {overlap}"


def test_AC_DCGID_1_overlap_keeps_genuine_identity() -> None:
    # A genuine same-question reopen shares the record's DISTINCTIVE
    # identity tokens → overlap >= 2.
    rec = _Rec(
        question="What happens to the FBM co-citation spread after the eval?",
        workstream="loam",
        entities=("fbm", "co-citation", "spread"),
    )
    subject_tokens = {"the", "fbm", "co", "citation", "spread", "question"}
    corpus = {"__nrec__": 7, "loam": 5, "fbm": 1, "spread": 1, "citation": 1}
    overlap = _declared_vocab_overlap(
        rec, subject_tokens, corpus_frequency=corpus
    )
    assert overlap >= 2, f"genuine identity overlap must resolve; got {overlap}"
