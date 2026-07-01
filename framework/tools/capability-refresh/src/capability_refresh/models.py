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

"""Model-lineup tracking (AC.CLP-MDL.1/2).

Extracts Claude API model IDs from a fetched model-overview page,
persists the current lineup as a machine-derivable artifact under
``.refresh/model-lineup/<source-id>.json``, and computes the delta
(added / removed) vs the prior run.

The extract step uses a deterministic regex over the raw fetched text
(no LLM call — consistent with D-CUR.4's no-hallucination-entry guard).
The lineup artifact is machine state (same class as snapshots): it is a
baseline for delta computation, NOT a reference doc.

Uses ``corpus.resolve_state_path`` for all writes so the containment
guard (AC.CLP-CUR.7) covers model-lineup paths automatically.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List, Optional


# Matches backtick-quoted `claude-X` identifiers in Markdown text.
# Claude API IDs in the models-overview page appear as `claude-fable-5`,
# `claude-sonnet-5`, etc. The pattern accepts letters, digits, hyphens,
# and dots (some IDs include a date suffix like claude-opus-4-1-20250805).
_MODEL_ID_PATTERN = re.compile(r"`(claude-[a-zA-Z0-9][a-zA-Z0-9.-]*)`")


def extract_model_ids(text: str) -> List[str]:
    """Return the sorted, deduplicated set of Claude API model IDs found
    in *text*.  Operates on raw fetched text (not the normalized form)
    so that backticks are always present regardless of HTML stripping.
    AC.CLP-MDL.1 / AC.CLP-MDL.2."""
    return sorted(set(_MODEL_ID_PATTERN.findall(text)))


def compute_model_delta(old_ids: List[str], new_ids: List[str]) -> Dict:
    """Compare two model-ID sets; return the structured delta.

    Returns a dict with:
      ``added``    — IDs present in *new_ids* but not *old_ids*.
      ``removed``  — IDs present in *old_ids* but not *new_ids*.
      ``no_prior`` — always ``False`` (caller sets ``True`` for first run).

    AC.CLP-MDL.2: a prior-lineup delta that adds a new model ID names it
    in ``added``.
    """
    old_set = set(old_ids)
    new_set = set(new_ids)
    return {
        "added": sorted(new_set - old_set),
        "removed": sorted(old_set - new_set),
        "no_prior": False,
    }


def _lineup_path(corpus_root: Path, source_id: str) -> Path:
    """Resolve the model-lineup artifact path via the corpus containment
    guard (AC.CLP-CUR.7 — writes must stay inside STATE_DIRS)."""
    from capability_refresh.corpus import resolve_state_path
    return resolve_state_path(corpus_root, ".refresh", "model-lineup",
                              f"{source_id}.json")


def load_model_lineup(corpus_root: Path, source_id: str) -> Optional[List[str]]:
    """Load the prior-run model lineup from the artifact, or ``None`` if
    no prior run exists (first-run case; delta is meaningless)."""
    path = _lineup_path(corpus_root, source_id)
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("ids")


def save_model_lineup(corpus_root: Path, source_id: str, ids: List[str],
                      ts: str) -> None:
    """Persist the current model lineup + run timestamp as the
    machine-derivable artifact (AC.CLP-MDL.1)."""
    path = _lineup_path(corpus_root, source_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"ids": ids, "run_ts": ts}
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
