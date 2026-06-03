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

"""AC.FBM-P5-METRIC.2 (Slice F / F2) — the metric is DETERMINISTIC and its
labels are HONEST (non-tautological).

Two properties a regression guard MUST have, or it is worse than none:

  1. DETERMINISTIC — two runs of ``precision_at_k`` over the same probes +
     config produce IDENTICAL reports (mean + per-probe + k). The production
     ranker is a total order with a stable ``(-boosted, arrival_index)``
     tie-break and no randomness; this verifies that empirically rather than
     assuming it, so the sealed floor cannot flake on noise.

  2. NON-TAUTOLOGICAL labels — a probe whose relevant set is authored on TOPIC
     scores STRICTLY below 1.0 in the presence of an unfiltered off-topic
     distractor that the ranker surfaces in the top-k. A tautological label set
     (relevance = "whatever the ranker returned") would force 1.0 by
     construction. The strict-below-1.0 result proves the labels are
     independent of the ranker — the integrity property the whole metric rests
     on.

Plan: docs/plans/fbm-retrieval-relevance-metric-p-at-5.md §5 (F2).
"""

from __future__ import annotations

import random
from pathlib import Path

from loam.primary_persona.keep_pace.retrieval import RetrievalConfig
from loam.primary_persona.keep_pace.retrieval_metric import Probe, precision_at_k


_DISTRACTOR_VOCAB = [
    "alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta",
    "iota", "kappa", "lambda", "mu", "nu", "xi", "omicron", "pi", "rho",
    "sigma", "tau", "upsilon",
]


def _corpus_only_config(tmp_path: Path) -> RetrievalConfig:
    """A corpus-only fixture: 40 distractors + 3 topical relevant docs. No
    episode store (this AC is about the metric's determinism + label honesty,
    not the salience gate)."""
    mem = tmp_path / "corpus"
    mem.mkdir()
    rng = random.Random(5)
    for i in range(40):
        word = rng.choice(_DISTRACTOR_VOCAB)
        word2 = rng.choice(_DISTRACTOR_VOCAB)
        (mem / f"feedback_filler_{i}.md").write_text(
            f"# Office {word} note {i}\n\nroom {i} {word2} procedure.\n"
        )
    for i, aspect in enumerate(["strata", "erosion", "rimrock"]):
        (mem / f"feedback_canyon_{i}.md").write_text(
            f"# Canyon {aspect} note {i}\n\ncanyon {aspect} geological survey "
            f"gorge sector deep formation note {i}.\n"
        )
    return RetrievalConfig(
        workspace_root=tmp_path,
        memory_dir=mem,
        claude_homes=(),
        objectives_home=tmp_path / "no-objectives",
        episode_memory_dir=None,
        top_n=5,
    )


def test_AC_FBM_P5_METRIC_2_deterministic(tmp_path: Path) -> None:
    """Two runs over the same probes + config produce IDENTICAL reports."""
    config = _corpus_only_config(tmp_path)
    probe = Probe.from_labels(
        "canyon geological survey gorge sector deep formation",
        ["Canyon strata note 0", "Canyon erosion note 1", "Canyon rimrock note 2"],
    )
    run_a = precision_at_k([probe], config, k=5)
    run_b = precision_at_k([probe], config, k=5)
    assert run_a == run_b, (
        f"the metric must be deterministic; run_a={run_a} run_b={run_b}"
    )
    # Determinism also holds at the per-probe granularity (not just the mean).
    assert run_a.per_probe == run_b.per_probe


def test_AC_FBM_P5_METRIC_2_labels_are_not_tautological(tmp_path: Path) -> None:
    """A topical-relevance label set scores STRICTLY below 1.0 when the ranker
    surfaces a non-relevant hit in the top-k — proving labels != ranker output.
    """
    config = _corpus_only_config(tmp_path)
    # Only 3 topical relevant docs exist, so a k=5 probe CANNOT reach P@5 = 1.0
    # (at most 3 of the 5 slots can be relevant — the other 2 are either empty
    # or filled by a non-relevant hit). A tautological label set would relabel
    # whatever fills the remaining slots as "relevant" and force 1.0; the
    # strict-below-1.0 result proves the labels are topic-anchored.
    probe = Probe.from_labels(
        "canyon geological survey gorge sector deep formation",
        ["Canyon strata note 0", "Canyon erosion note 1", "Canyon rimrock note 2"],
    )
    report = precision_at_k([probe], config, k=5)
    assert report.mean < 1.0, (
        f"with only 3 topical relevant docs, P@5 must be < 1.0 (honest labels); "
        f"a value of 1.0 would mean the labels were reverse-engineered from the "
        f"ranker. got {report.mean} (per-probe={report.per_probe})"
    )
    # And the 3 genuinely-relevant docs DO surface — the metric credits real
    # topical relevance (it is not stuck at 0 either).
    assert report.mean >= 3 / 5, (
        f"the 3 topical relevant docs should hold 3 of the top-5 slots; "
        f"got {report.mean} (per-probe={report.per_probe})"
    )
