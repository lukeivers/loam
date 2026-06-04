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

"""Shared test helpers for the WMS increment-3 INTAKE suite (AC.INTK.*).

A FAKE work-intent extractor (no spawn, no LLM) so the detect/gate/dedup/propose
pipeline is exercised deterministically, plus a fresh-store factory + a
fixture-home matrix writer for the #34 aggressiveness cell. The outcome-altitude
AC.INTK.LIVE.1 uses the production extractor seam directly with a fake registered
through ``register_work_intent_extractor`` (the same seam production fills) — the
turn-path itself is real."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from loam.objective_tracker.runtime import ObjectiveTracker
from loam.primary_persona.keep_pace.intake import (
    WorkIntent,
    WorkIntentUnavailableError,
)


class FakeWorkIntentExtractor:
    """A deterministic work-intent extractor for tests (no spawn, no LLM).

    Maps each input turn text to a pre-arranged :class:`WorkIntent`, or raises
    :class:`WorkIntentUnavailableError` when ``decline`` is set (the fail-soft
    case). When a turn text is not in the map, returns a NON-work read (the
    chatter default) so an un-mapped turn is treated as no-capture."""

    def __init__(
        self,
        mapping: Optional[dict[str, WorkIntent]] = None,
        *,
        decline: bool = False,
    ) -> None:
        self._mapping = dict(mapping or {})
        self._decline = decline
        self.calls: list[str] = []

    def extract(self, turn_text: str) -> WorkIntent:
        self.calls.append(turn_text)
        if self._decline:
            raise WorkIntentUnavailableError("fake extractor declined")
        mapped = self._mapping.get(turn_text)
        if mapped is not None:
            return mapped
        # Un-mapped turn -> chatter (no work).
        return WorkIntent(is_work=False)


def fresh_tracker(tmp_path: Path) -> ObjectiveTracker:
    """A fresh, empty work-item store (no pre-arranged state)."""
    db = tmp_path / "objective_tracker.sqlite"
    return ObjectiveTracker(db_path=db)


def write_aggressiveness_matrix(claude_home: Path, value: str) -> Path:
    """Write a #34 INTERACTION-MODEL.md fixture with the intake aggressiveness
    cell set to ``value`` under the ``work-tracking`` area. Returns the home dir
    to pass as ``claude_home``."""
    claude_home.mkdir(parents=True, exist_ok=True)
    matrix = claude_home / "INTERACTION-MODEL.md"
    matrix.write_text(
        "# interaction-model\n\n"
        "## work-tracking\n"
        f"intake-aggressiveness: {{ value: {value}, confidence: stated, evidence: [] }}\n",
        encoding="utf-8",
    )
    return claude_home
