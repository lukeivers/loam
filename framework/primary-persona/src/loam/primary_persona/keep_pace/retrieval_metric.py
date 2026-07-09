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

"""Slice F — the FBM retrieval-relevance metric ("loam BrainBench").

A precision-at-5 (P@5) metric over the PRODUCTION FBM retrieval — a
regression guard that measures whether retrieval surfaces genuinely-RELEVANT
memories, so relevance quality cannot silently rot after the A-E changes
(write-gate, load-filter, per-project STATE, lens injection, multi-repo
visibility).

P@5 = (# of the top-5 surfaced hits that are labeled-relevant) / 5, averaged
over a labeled probe set.

The metric MEASURES retrieval; it does NOT re-implement ranking. It drives
the SAME ranked code path the production turn injects via
:func:`keep_pace.retrieval.rank` (which :func:`retrieve` delegates to), so
there is no drift between what the metric measures and what ships.

The honesty contract (the whole point of the metric — AC.FBM-P5-METRIC.*):

  * Relevance labels are AUTHORED on topical relevance, decided BEFORE any
    ranking is run — NEVER reverse-engineered from the ranker's output (which
    would make the metric tautological: it would pass by construction and
    guard nothing). The labels are a property of the probe set's authoring;
    this module never reads ranker output to decide what is relevant.

  * The metric is DETERMINISTIC. The production ranker is a total order
    (per-source min-max + weight/salience boost, sorted on
    ``(-boosted, arrival_index)``) with no randomness / no embeddings /
    no clock, so the same probes + config always yield the same report.
    The caller asserts this by running twice and comparing (the metric does
    not assume determinism, it is verifiable).

A probe's relevant set is a set of RELEVANCE SIGNATURES. A hit's signature is
the normalized token signature of its plain-language ``pointer`` — the exact
text the surface would show — so a label matches a hit iff the AUTHORED
relevant text matches the SURFACED text, ranker-output-free.

Stdlib-only. No API key (``feedback_no_anthropic_api_key``).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Optional

from .retrieval import (
    P_AT_K_MEASUREMENT_WINDOW,
    SALIENCE_THRESHOLD,
    RetrievalConfig,
    rank,
)

# Token shape for the relevance signature — alnum/underscore runs, lowercased.
# Mirrors the FTS / dedup tokenizer so the signature keys on content tokens,
# not punctuation.
_SIGNATURE_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")


def relevance_signature(text: str) -> frozenset[str]:
    """The stable, ranker-output-free relevance signature of a pointer / label.

    The lowercased alnum/underscore token-set of ``text``. A probe's relevant
    set is a set of these signatures (authored on topical relevance); a hit's
    signature is computed from its surfaced ``pointer``. Matching is a
    token-subset test (see :func:`_hit_is_relevant`) so an authored
    relevance phrase matches a surfaced pointer that CONTAINS that phrase's
    tokens — robust to the surface's framing prefix
    (``From an earlier turn: ...`` / a corpus title) while still keyed on the
    real content tokens.
    """
    return frozenset(t.lower() for t in _SIGNATURE_TOKEN_RE.findall(text or ""))


@dataclass(frozen=True)
class Probe:
    """One labeled retrieval probe (AC.FBM-P5-METRIC.*).

    ``query`` is the prompt fed to the production retrieval. ``relevant`` is
    the AUTHORED set of relevance signatures (each a frozenset of content
    tokens) that are genuinely topically relevant to the query — decided on
    topic, NEVER from ranker output. ``last_topic`` threads the optional
    work-anchor continuity slot (empty by default, matching the MVP turn).
    """

    query: str
    relevant: frozenset[frozenset[str]]
    last_topic: str = ""

    @staticmethod
    def from_labels(
        query: str, relevant_labels: Iterable[str], *, last_topic: str = ""
    ) -> "Probe":
        """Build a :class:`Probe` from human-authored relevance LABEL strings.

        Each label is a topical-relevance phrase (e.g. a distinctive marker
        from the relevant doc's content); it is converted to a relevance
        signature. This is the authoring surface — the labels are chosen on
        topic, then frozen into signatures here, so the relevant set is fixed
        BEFORE any ranking is run.
        """
        return Probe(
            query=query,
            relevant=frozenset(
                relevance_signature(label) for label in relevant_labels
            ),
            last_topic=last_topic,
        )


@dataclass(frozen=True)
class P5Report:
    """The P@k metric result (AC.FBM-P5-METRIC.*).

    ``mean`` is the mean P@k over the probe set; ``per_probe`` is the list of
    per-probe P@k values in probe order; ``k`` is the cut; ``num_probes`` is
    the probe count. Fully determined by the probes + config (no randomness).
    """

    mean: float
    per_probe: tuple[float, ...]
    k: int
    num_probes: int


def _hit_is_relevant(
    hit: dict[str, object], relevant: frozenset[frozenset[str]]
) -> bool:
    """Whether a surfaced hit matches an AUTHORED relevant signature.

    A hit is relevant iff some authored relevance signature is a token-SUBSET
    of the hit's pointer signature — the authored topical-relevance phrase's
    content tokens all appear in the surfaced pointer. Subset (not equality)
    so the surface's framing prefix (``From an earlier turn: ``) or a longer
    corpus title does not defeat a correct match, while a distractor whose
    pointer lacks the authored tokens is NOT counted relevant. An empty
    authored signature never matches (it would match everything — guard
    against a blank label).
    """
    hit_sig = relevance_signature(str(hit.get("pointer", "") or ""))
    if not hit_sig:
        return False
    return any(
        bool(label_sig) and label_sig <= hit_sig for label_sig in relevant
    )


def precision_at_k(
    probes: Iterable[Probe],
    config: RetrievalConfig,
    *,
    k: int = P_AT_K_MEASUREMENT_WINDOW,
    salience_threshold: float = SALIENCE_THRESHOLD,
) -> P5Report:
    """Precision-at-k over the PRODUCTION retrieval for a labeled probe set.

    For each probe: run the production :func:`rank` (the same ranked path
    :func:`retrieve` injects), take the top-``k`` surfaced hits, count how many
    carry a relevance signature in the probe's AUTHORED relevant set, divide by
    ``k``. The report's ``mean`` is the average over probes.

    P@k is normalized by ``k`` (the standard precision-at-k denominator), NOT
    by the number of hits returned: a query that surfaces only 2 hits, both
    relevant, scores ``2/k`` — surfacing FEWER relevant memories is correctly
    penalized (the metric rewards filling the top-k with relevant hits).

    Deterministic — the production ranker is a total order with a stable
    tie-break and no randomness; the same probes + config yield the same
    report. ``salience_threshold`` is threaded so a caller can SEED a
    regression (drop the gate to re-admit junk) and observe P@k fall — the
    AC.FBM-P5-METRIC.1 guard.
    """
    if k <= 0:
        raise ValueError("k must be positive for precision-at-k")
    per_probe: list[float] = []
    for probe in probes:
        hits = rank(
            prompt=probe.query,
            config=config,
            last_topic=probe.last_topic,
            salience_threshold=salience_threshold,
        )
        top_k = hits[:k]
        relevant_in_top_k = sum(
            1 for h in top_k if _hit_is_relevant(h, probe.relevant)
        )
        per_probe.append(relevant_in_top_k / k)
    num = len(per_probe)
    mean = (sum(per_probe) / num) if num else 0.0
    return P5Report(
        mean=mean,
        per_probe=tuple(per_probe),
        k=k,
        num_probes=num,
    )
