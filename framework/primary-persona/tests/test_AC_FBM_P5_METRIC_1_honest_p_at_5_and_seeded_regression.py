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

"""AC.FBM-P5-METRIC.1 (Slice F / F1) — the metric computes an HONEST P@5 over a
controlled probe fixture AND catches a SEEDED relevance regression.

The controlled fixture (relevance authored on TOPIC, never on ranker output):

  * 40 off-topic distractor corpus docs (realistic IDF so BM25 discriminates).
  * 5 topical relevant corpus docs (the AUTHORED relevant set for the probe) —
    four strong matches + one deliberately-WEAK match (it matches only one query
    token, so its raw BM25 is low — the slot a re-admitted junk hit can contest).
  * 1 junk episode (a ``<task-notification>`` turn — a real junk class) carrying
    the topic tokens, injected into the HOT FTS index (simulating a pre-Slice-A
    junk episode still on disk / a write-gate regression).

With the salience signal HEALTHY the gate suppresses the junk episode, so the 5
topical relevant docs hold the top-5 (P@5 = 1.0). With the salience signal
REGRESSED — ``_salience_from_body`` patched to return full salience, modelling
the structural-salience classifier breaking — the junk episode is scored as
substantive, competes on its (higher) BM25, and DISPLACES the weak relevant doc
from the top-5, dropping P@5 below the conservative floor: the guard FIRES.

The labels are NOT reverse-engineered from the ranker — they are the topical
titles of the authored relevant docs, fixed before any ranking runs. A
tautological label set would force P@5 = 1.0 in BOTH regimes (it would relabel
whatever the ranker surfaced as "relevant"); here the regression provably drops
P@5, which is only possible because the labels are independent of the ranker.

Plan: docs/plans/fbm-retrieval-relevance-metric-p-at-5.md §5 (F1).
"""

from __future__ import annotations

import random
from datetime import datetime, timezone
from pathlib import Path

import loam.primary_persona.file_memory as file_memory
from loam.primary_persona.file_memory import EPISODES_SUBDIR, FileMemoryStore
from loam.primary_persona.keep_pace.retrieval import RetrievalConfig
from loam.primary_persona.keep_pace.retrieval_metric import Probe, precision_at_k


# The conservative floor — set BETWEEN the healthy P@5 (1.0, measured at build
# time) and the regressed P@5 (0.8, measured at build time). A margin under the
# healthy value so noise cannot flip the guard, above the regressed value so the
# seeded regression fires. NAMED + tunable: raising it tightens the guard as
# retrieval improves.
_CONSERVATIVE_FLOOR = 0.9

_DISTRACTOR_VOCAB = [
    "alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta",
    "iota", "kappa", "lambda", "mu", "nu", "xi", "omicron", "pi", "rho",
    "sigma", "tau", "upsilon",
]

_QUERY = "canyon geological survey gorge sector deep formation drone"


def _build_fixture(tmp_path: Path) -> tuple[RetrievalConfig, Probe]:
    """Author the controlled probe fixture; return (config, probe).

    Relevance is decided here, on TOPIC, BEFORE any ranking — the probe's
    relevant set is the five topical corpus-doc titles.
    """
    mem = tmp_path / "corpus"
    mem.mkdir()
    epdir = tmp_path / "episodes-store"
    store = FileMemoryStore(memory_dir=epdir)
    now = datetime.now(timezone.utc)

    # 40 off-topic distractor docs — populate the IDF space.
    rng = random.Random(3)
    for i in range(40):
        word = rng.choice(_DISTRACTOR_VOCAB)
        word2 = rng.choice(_DISTRACTOR_VOCAB)
        (mem / f"feedback_filler_{i}.md").write_text(
            f"# Office {word} note {i}\n\nroom {i} {word2} procedure.\n"
        )

    # 5 topical relevant docs — four strong + one deliberately weak.
    titles: list[str] = []
    for i, aspect in enumerate(["strata", "erosion", "rimrock", "sandstone"]):
        title = f"Canyon {aspect} note {i}"
        titles.append(title)
        (mem / f"feedback_canyon_{i}.md").write_text(
            f"# {title}\n\ncanyon {aspect} geological survey gorge sector "
            f"deep formation note {i}.\n"
        )
    weak_title = "Canyon drone sparse note 4"
    titles.append(weak_title)
    (mem / "feedback_canyon_4.md").write_text(
        f"# {weak_title}\n\ncanyon drone reference only.\n"
    )

    # 1 junk episode injected into the HOT FTS index (pre-Slice-A junk on disk).
    hot = epdir / EPISODES_SUBDIR / "pos3" / "2026-06-03"
    hot.mkdir(parents=True, exist_ok=True)
    junk_body = (
        "[user]\n<task-notification> canyon geological survey gorge sector "
        "deep formation pipeline batch status complete done\n\n"
        "[assistant]\nok.\n"
    )
    junk_path = hot / "junk0.md"
    junk_path.write_text("---\n---\n" + junk_body)
    store._index_episode(
        path=junk_path,
        name="turn/junk0",
        body=junk_body,
        group_id="pos3",
        reference_time=now,
    )

    config = RetrievalConfig(
        workspace_root=tmp_path,
        memory_dir=mem,
        claude_homes=(),
        objectives_home=tmp_path / "no-objectives",
        episode_memory_dir=epdir,
        episode_group_ids=("pos3",),
        top_n=5,
    )
    # Labels = the topical titles, authored on relevance — NOT ranker output.
    probe = Probe.from_labels(_QUERY, titles)
    return config, probe


def test_AC_FBM_P5_METRIC_1_honest_p_at_5_clears_floor(tmp_path: Path) -> None:
    """Healthy retrieval: the metric computes a real P@5 that clears the floor."""
    config, probe = _build_fixture(tmp_path)
    report = precision_at_k([probe], config, k=5)
    assert report.k == 5
    assert report.num_probes == 1
    # The salience gate is healthy -> the five topical relevant docs hold the
    # top-5; the junk episode is suppressed. Honest P@5 = 1.0.
    assert report.mean >= _CONSERVATIVE_FLOOR, (
        f"healthy P@5 {report.mean} must clear the conservative floor "
        f"{_CONSERVATIVE_FLOOR}; per-probe={report.per_probe}"
    )


def test_AC_FBM_P5_METRIC_1_seeded_regression_drops_below_floor(
    tmp_path: Path, monkeypatch
) -> None:
    """Seeded regression: the structural-salience classifier breaks (scores
    everything full salience), the gate stops suppressing the junk episode, the
    junk DISPLACES the weak relevant doc, and the measured P@5 drops BELOW the
    floor — the regression guard fires."""
    config, probe = _build_fixture(tmp_path)

    # Sanity: healthy regime clears the floor (same fixture, gate working).
    healthy = precision_at_k([probe], config, k=5)
    assert healthy.mean >= _CONSERVATIVE_FLOOR

    # Seed the regression: the salience classifier fails to flag junk.
    monkeypatch.setattr(
        file_memory, "_salience_from_body", lambda body: file_memory.SALIENCE_FULL
    )
    regressed = precision_at_k([probe], config, k=5)
    assert regressed.mean < _CONSERVATIVE_FLOOR, (
        f"the seeded relevance regression must drop P@5 below the floor "
        f"{_CONSERVATIVE_FLOOR}; got {regressed.mean} "
        f"(per-probe={regressed.per_probe}). If this does not fire, the guard "
        f"is not catching a junk re-introduction."
    )
    # The regression strictly worsens P@5 — the junk displaced a relevant hit.
    assert regressed.mean < healthy.mean
