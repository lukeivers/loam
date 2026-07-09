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

"""Model-lineup tracking (AC.CLP-MDL.1/2, AC.CLP-MDLR.1-5).

Extracts Claude API model IDs from a fetched model-overview page,
persists the current lineup as a machine-derivable artifact under
``.refresh/model-lineup/<source-id>.json``, and computes the delta
(added / removed) vs the prior run.

The extract step uses deterministic parsing over the raw fetched text
(no LLM call — consistent with D-CUR.4's no-hallucination-entry guard).
The lineup artifact is machine state (same class as snapshots): it is a
baseline for delta computation, NOT a reference doc.

Format-robustness (AC.CLP-MDLR.*): detection must not key on a *presentation*
detail. Upstream reformatted the "Latest models comparison" table so the
Claude-API-ID row renders IDs as PLAIN text rather than backticked; a
backtick-only extractor under-detected live models and faked add/remove
deltas from a purely cosmetic edit. Extraction therefore unions two precise
signals: (1) a STRUCTURAL parse of the comparison table's Claude-API-ID row
(backtick-agnostic — the authoritative model list); (2) the original
backtick-quoted regex over the whole page (preserved so prose-only
backticked models with no table row are not dropped). Neither half is a
page-wide plain-text grep, so incidental-prose / Bedrock / Google-Cloud IDs
do not pollute the lineup.

Uses ``corpus.resolve_state_path`` for all writes so the containment
guard (AC.CLP-CUR.7) covers model-lineup paths automatically.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List, Optional


# Signal (2): backtick-quoted `claude-X` identifiers anywhere in the text.
# Preserved from the original extractor. Conservative (backtick-gated, so
# no over-capture) and REQUIRED to keep prose-only models that have no table
# row — e.g. `claude-mythos-5`, `claude-mythos-preview` (AC.CLP-MDLR.5).
_BACKTICK_MODEL_ID_PATTERN = re.compile(r"`(claude-[a-zA-Z0-9][a-zA-Z0-9.-]*)`")

# The label that identifies the authoritative model-ID row of a comparison
# table, after normalization (bold markers / backticks / whitespace stripped,
# lowercased). Matches both the real page (``**Claude API ID**``) and the
# fixture form (``Claude API ID``).
_MODEL_ID_ROW_LABEL = "claude api id"

# A single table cell holding exactly one canonical Claude API ID. Anchored
# whole-cell (after stripping surrounding backticks/whitespace) so it accepts
# ``claude-sonnet-5`` and ``claude-opus-4-8`` but rejects Bedrock-style
# ``anthropic.claude-*`` and Google-Cloud ``claude-*@date`` cells and any
# prose (AC.CLP-MDLR.4).
_MODEL_ID_CELL_PATTERN = re.compile(r"^claude-[a-zA-Z0-9][a-zA-Z0-9.-]*$")


def _normalize_cell(cell: str) -> str:
    """Strip Markdown bold markers, backticks, and surrounding whitespace
    from a table cell."""
    return cell.strip().strip("*").strip("`").strip()


def _extract_table_id_row_ids(text: str) -> List[str]:
    """Signal (1): structurally parse Markdown table rows and return the
    Claude API IDs from any row whose first cell is the Claude-API-ID label.

    Backtick-agnostic: an ID is detected whether or not it is wrapped in
    backticks in the cell. Row-label gating + whole-cell anchoring keep this
    from capturing Bedrock / Google-Cloud ID rows, header cells, or prose
    (AC.CLP-MDLR.1 / .4). Handles both the wide real-page table (one ID row
    with many model columns) and the narrow fixture table (one ID per row).
    """
    ids: List[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = stripped.split("|")
        # Drop the empty leading/trailing fields produced by the outer pipes.
        if cells and cells[0].strip() == "":
            cells = cells[1:]
        if cells and cells[-1].strip() == "":
            cells = cells[:-1]
        if not cells:
            continue
        if _normalize_cell(cells[0]).lower() != _MODEL_ID_ROW_LABEL:
            continue
        for cell in cells[1:]:
            value = _normalize_cell(cell)
            if _MODEL_ID_CELL_PATTERN.match(value):
                ids.append(value)
    return ids


def extract_model_ids(text: str) -> List[str]:
    """Return the sorted, deduplicated set of Claude API model IDs found
    in *text*.  Operates on raw fetched text (not the normalized form).

    Unions the structural comparison-table Claude-API-ID row parse
    (backtick-agnostic) with the conservative backtick-quoted prose regex,
    so a cosmetic upstream formatting change (backtick -> plain) cannot fake
    an add/remove delta and prose-only backticked models are still detected.
    AC.CLP-MDL.1 / AC.CLP-MDL.2 / AC.CLP-MDLR.1-5."""
    table_ids = _extract_table_id_row_ids(text)
    backtick_ids = _BACKTICK_MODEL_ID_PATTERN.findall(text)
    return sorted(set(table_ids) | set(backtick_ids))


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
