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

"""capability-refresh — deterministic Class A corpus currency.

The locked-2026-04-26 delta deterministic-projection core
(claude-leverage-program Slice 1; D-CUR.1..5):

    read source manifest (data) -> fetch canonical upstreams ->
    project Class A bodies (NO LLM authorship) -> structured delta ->
    partition per D-CUR.4 (auto-land body re-projections / fetch-ts
    stamps / stale-markings; REVIEW-flag new claims, removals,
    [user-intent phrasings] overlay touches, contradiction-suspects) ->
    stamp source_fetch_ts; fetch failure marks the entry stale, never
    silently current.

Every module maps to named ACs (ODD section 2.5):
  - sources.py    — AC.CLP-CUR.3 (sources declared as data, cadence classes)
  - fetch.py      — AC.CLP-CUR.3/5 (fetch + deterministic normalisation)
  - partition.py  — AC.CLP-CUR.6 (D-CUR.4 delta partition)
  - corpus.py     — AC.CLP-CUR.5/6/7 (stamp/stale/substitute + the
                    no-cross-class-write structural guard)
  - refresh.py    — AC.CLP-CUR.3/4/5/6/7 (the production refresh cycle)
  - cli.py        — AC.CLP-CUR.3/4 (the production entry-point the
                    cadence binding invokes)
"""

__version__ = "0.1.0"

from capability_refresh.refresh import run_refresh  # noqa: F401
from capability_refresh.corpus import CrossClassWriteError  # noqa: F401
