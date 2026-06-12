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

"""D-CUR.4 delta partition (AC.CLP-CUR.6) — the protection-floor guard.

Upstream delta = diff(snapshot at t-1, fetch at t), classified
deterministically per hunk:

  - ``reprojection``           replace-hunk whose old/new similarity is
                               >= SIM_THRESHOLD — an update of the same
                               statement. AUTO-LAND candidate.
  - ``new-claim``              insert-hunk — a capability claim that did
                               not exist upstream before. REVIEW.
  - ``removal``                delete-hunk — a removed capability /
                               deprecation. REVIEW.
  - ``contradiction-suspect``  replace-hunk below SIM_THRESHOLD — the
                               new text is not a rewording of the old;
                               it may contradict it. REVIEW.

New claims, removals, overlay touches (classified downstream in
``corpus.apply_reprojection``), and contradiction-suspects NEVER land
automatically — a wrong auto-ingested claim poisoning the reference
surface is the floor failure this program exists to prevent.
"""

from __future__ import annotations

import difflib
from dataclasses import dataclass, field
from typing import List

SIM_THRESHOLD = 0.6

REVIEW_KINDS = ("new-claim", "removal", "contradiction-suspect")


@dataclass
class DeltaItem:
    kind: str  # reprojection | new-claim | removal | contradiction-suspect
    old: str = ""
    new: str = ""
    # filled downstream when an auto-land candidate is applied:
    disposition: str = "pending"  # pending | auto-landed | review
    reason: str = ""

    def as_dict(self) -> dict:
        return {
            "kind": self.kind,
            "old": self.old,
            "new": self.new,
            "disposition": self.disposition,
            "reason": self.reason,
        }


def _similarity(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a, b).ratio()


def partition_delta(old_lines: List[str], new_lines: List[str]) -> List[DeltaItem]:
    """Classify the upstream delta per D-CUR.4. Deterministic — difflib
    opcodes over normalized statement units + a similarity ratio; no
    judgement call enters the partition."""
    items: List[DeltaItem] = []
    matcher = difflib.SequenceMatcher(None, old_lines, new_lines)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        old_text = "\n".join(old_lines[i1:i2]).strip()
        new_text = "\n".join(new_lines[j1:j2]).strip()
        if tag == "insert":
            items.append(DeltaItem(kind="new-claim", new=new_text, disposition="review",
                                   reason="adds a capability claim not previously upstream"))
        elif tag == "delete":
            items.append(DeltaItem(kind="removal", old=old_text, disposition="review",
                                   reason="removes a previously-present capability claim"))
        elif tag == "replace":
            if _similarity(old_text, new_text) >= SIM_THRESHOLD:
                items.append(DeltaItem(kind="reprojection", old=old_text, new=new_text,
                                       disposition="pending",
                                       reason="same-statement update (similarity >= threshold)"))
            else:
                items.append(DeltaItem(kind="contradiction-suspect", old=old_text,
                                       new=new_text, disposition="review",
                                       reason="replacement text is not a rewording of the old "
                                              "(similarity < threshold); may contradict it"))
    return items
