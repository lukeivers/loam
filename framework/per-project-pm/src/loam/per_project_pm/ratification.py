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

"""Ratification-batch helper — composes a list of (question, provenance)
pairs from a banded contract draft and enqueues them through the PM.

Per v0.1.8 Cycle 2 plan-doc §4 AC.BANDS.7 + §5 Surface #7 — this is
the secondary fence's contribution: a thin helper module on top of
the existing :class:`PMRuntime` (Cycle 2 + Cycle 4 of v0.1.7). NO
changes to the Cycle 4 PM contract; this module only adds new code.

Composition direction is one-way: ``framework/per-project-pm/`` does
NOT import ``loam_odd_extractor`` (the dev-sdlc side does the
parsing). This module accepts duck-typed banded-AC inputs (a list of
mappings with ``ac_id``, ``text``, ``confidence``, ``evidence``) so
callers can supply either typed BandedAC instances or
already-dumped dicts without coupling per-project-pm to a specific
``BandedAC`` class.

Usage (persona-side flow):

.. code:: python

    from loam.per_project_pm import RatificationBatch, PMRuntime
    pm = PMRuntime.from_workspace(workspace_root, pm_handle)
    batch = RatificationBatch.from_banded_acs(
        extraction_id="repo-12345678",
        banded_acs=[ac.model_dump() for ac in banded_acs],
    )
    enqueued = batch.enqueue(pm)
    # next: pm.surface_next_questions_batch(n=1) + persona relay +
    # pm.record_response(...)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence


@dataclass(frozen=True)
class RatificationBatch:
    """A pre-built batch of (question_text, provenance) pairs ready
    to enqueue through a :class:`PMRuntime`.

    Per v0.1.8 Cycle 2 plan-doc §4 AC.BANDS.7. Frozen dataclass;
    constructed via :meth:`from_banded_acs` or
    :meth:`from_contract_draft` (latter for forward-compat — Cycle 2
    only ships ``from_banded_acs``).

    Provenance string format per plan-doc §5 Surface #8:
    ``f"odd-extract:{extraction_id}:{ac_id}"``.
    """

    extraction_id: str
    pairs: tuple[tuple[str, str], ...]  # (question_text, provenance)

    @classmethod
    def from_banded_acs(
        cls,
        *,
        extraction_id: str,
        banded_acs: Sequence[Mapping[str, Any]],
    ) -> "RatificationBatch":
        """Construct a batch from a sequence of banded-AC mappings.

        Each mapping must carry: ``ac_id``, ``text``, ``confidence``,
        ``evidence`` (a sub-mapping with ``kind`` + ``citations``
        + optional ``repo_sha`` / ``rationale``).

        Raises ``ValueError`` on missing required keys; the persona-
        side caller is expected to have constructed properly-banded
        ACs (the odd-extractor's :class:`BandedAC` model_validator is
        the structural enforcement layer).
        """
        if not extraction_id:
            raise ValueError(
                "RatificationBatch: extraction_id must be non-empty"
            )
        pairs: list[tuple[str, str]] = []
        for idx, ac in enumerate(banded_acs):
            if "ac_id" not in ac:
                raise ValueError(
                    f"RatificationBatch: banded_acs[{idx}] missing "
                    f"required 'ac_id' key"
                )
            if "text" not in ac:
                raise ValueError(
                    f"RatificationBatch: banded_acs[{idx}] missing "
                    f"required 'text' key"
                )
            if "confidence" not in ac:
                raise ValueError(
                    f"RatificationBatch: banded_acs[{idx}] missing "
                    f"required 'confidence' key"
                )
            ac_id = ac["ac_id"]
            band = ac["confidence"]
            text = ac["text"]
            ev = ac.get("evidence") or {}
            ev_kind = ev.get("kind", "?")
            citations = ev.get("citations") or []
            repo_sha = ev.get("repo_sha")
            rationale = ev.get("rationale")

            question_text = (
                f"Ratify AC {ac_id} (currently {band}): {text}\n\n"
                f"Evidence kind: {ev_kind}; "
                f"citations: {citations or '(none)'}; "
                f"repo_sha: {repo_sha or '(none)'}; "
                f"rationale: {rationale or '(none)'}.\n\n"
                f"Reply with: promote / demote / edit / reject "
                f"(and a reason or new text where applicable). "
                f"Note: PLAUSIBLE→VERIFIED requires explicit "
                f"confirmation."
            )
            provenance = f"odd-extract:{extraction_id}:{ac_id}"
            pairs.append((question_text, provenance))
        return cls(
            extraction_id=extraction_id,
            pairs=tuple(pairs),
        )

    def enqueue(self, pm_runtime) -> int:
        """Enqueue every pair via ``PMRuntime.enqueue_decision``;
        return the count of enqueued items.

        Each call writes to the PM's decision-queue.yaml atomically;
        the underlying primitive is the Cycle 2 contract from v0.1.7.
        """
        count = 0
        for question_text, provenance in self.pairs:
            pm_runtime.enqueue_decision(
                question_text,
                provenance=provenance,
            )
            count += 1
        return count
