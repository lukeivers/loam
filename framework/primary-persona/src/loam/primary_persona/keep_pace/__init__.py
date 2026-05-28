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

"""keep-pace MVP — Cycle 2 (KP5 + KP1) primary-persona modules.

This subpackage is the keep-pace memory read-path landed under the
``primary-persona`` component (the manifest fence for Cycle 2; see
``docs/plans/keep-pace-with-user-mvp.md`` §2 placement table). It is
distinct from the existing episode read-path in ``memory_consumer.py``:
where that retrieves over per-turn episode files keyed on the bare
prompt, KP1 retrieves over the **markdown corpus** (the
``feedback_*.md`` corpus + CLAUDE.md hierarchy + OBJECTIVES.md) keyed
on a **work-anchored key** (prompt + active-objective + active-subgoal
+ last-turn topic).

Modules:

  - :mod:`objectives` — KP5: the ``OBJECTIVES.md`` register schema +
    loader (owner-gated ``status`` vs soft-auto ``last-touched`` /
    ``cadence`` field-class split) + seed of the two real objectives.
  - :mod:`corpus_index` — KP1: a BM25/FTS5 index over the markdown
    corpus (no embeddings, no API key per
    ``feedback_no_anthropic_api_key`` / Surface #1).
  - :mod:`work_anchor` — KP1: the work-anchored retrieval key
    (prompt + active-objective + active-subgoal + last-turn topic;
    degrades gracefully when a component is absent).
  - :mod:`retrieval` — KP1: the production retrieval entry-point +
    the KP0-chain ``Contributor``-compatible callable (top-N <=5,
    silent on no-match, skip-trivial, fresh read each turn).

Per ODD §2.5 every code path traces to a named AC; defensive branches
without an AC anchor are not introduced.
"""

from __future__ import annotations
