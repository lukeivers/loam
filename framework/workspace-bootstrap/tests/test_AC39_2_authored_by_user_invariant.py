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

"""Amendment #39 — AC39.2 — Seeded root + every descendant carry
``authored_by == "user"``.

Plan §4 AC39.2 outcomes:

- Every record produced by the seed has ``authored_by == "user"``.
- ``trace_to_root(<any seeded descendant>)`` returns a chain whose
  terminal ancestor is the value-prop root and whose every link's
  ``authored_by == "user"``.
- No record produced by the seed has ``authored_by`` set to any
  other value (no ``"primary-persona"``, no ``"workspace-bootstrap"``).

Maps to objective-tracker D2 (user-authored-root invariant) + D4
(``bind_scope`` enforcement) → AC.PO.1.
"""

from __future__ import annotations

from pathlib import Path

from loam.objective_tracker import ObjectiveTracker

from loam.workspace_bootstrap.adapters.first_run_scaffold import (
    run_first_run_scaffold,
)
from loam.workspace_bootstrap.adapters.tracker_seed import (
    FRAMEWORK_VALUE_PROP_RELPATH,
    ROOT_OBJECTIVE_ID,
    _SPEC_TIER_PHASES,
    tracker_db_path_for,
)


def _seed_dev(tmp_path: Path) -> Path:
    """Seed a dev-classified workspace. Sub-plan E (amendment #42):
    classification source-of-truth is the persona contract's
    ``dev_intent`` answer, so the fixture pre-creates the contract
    with ``dev_intent: yes`` BEFORE the scaffold runs. The scaffold's
    persona-install is idempotent (AC36.3) and leaves the pre-created
    dir alone. Returns the workspace path (the workspace-rooted
    tracker DB lives there per sub-plan E AC.E.6)."""
    workspace = tmp_path / "ws-auth"
    workspace.mkdir()
    (workspace / "docs").mkdir(parents=True)
    framework_vp = (
        Path(__file__).resolve().parent.parent.parent.parent
        / "docs"
        / "VALUE_PROPOSITION.md"
    )
    (workspace / FRAMEWORK_VALUE_PROP_RELPATH).write_text(
        framework_vp.read_text()
    )
    _seed_dev_intent_contract(workspace)
    pos_root = tmp_path / ".pos"
    agents = tmp_path / "LaunchAgents"
    run_first_run_scaffold(
        pos_root=pos_root,
        platform_override="macos",
        service_bootstrap=False,
        service_manager_dir_override=agents,
        workspace_root=workspace,
    )
    return workspace


def _seed_dev_intent_contract(workspace: Path) -> None:
    """Pre-create a persona contract carrying ``dev_intent: yes`` so
    sub-plan E's ``classify_workspace`` reads "pos-v2-dev"."""
    from loam.primary_persona.contract import PersonaContract
    from loam.primary_persona.onboarding import dev_intent_storage_path

    personas_dir = dev_intent_storage_path(workspace)
    persona_dir = personas_dir / "primary"
    persona_dir.mkdir(parents=True)
    contract = PersonaContract.model_validate(
        {
            "handle": "primary",
            "given_name": "Primary",
            "contract_version": "1.0.0",
            "responsibilities": {
                "single_point_of_contact": "Coordinator.",
                "context_holder": "Holds context.",
                "escalation_judge": "Decides surfacing.",
            },
            "authority_boundary": {
                "tier_a": "defer",
                "tier_b": "defer",
                "tier_c": "execute",
                "tier_d": "execute",
            },
            "escalation_taxonomy": {"categories": ["x"]},
            "severity_vocabulary": {"labels": ["a", "b"]},
            "is_starter": False,
            "is_primary": True,
            "dev_intent": "yes",
        }
    )
    (persona_dir / "contract.yaml").write_text(contract.to_yaml())


def test_AC39_2_every_seeded_record_authored_by_user(tmp_path: Path) -> None:
    """Enumerate every seeded record via the tracker — each carries
    ``authored_by == "user"``."""
    workspace = _seed_dev(tmp_path)
    tracker = ObjectiveTracker(tracker_db_path_for(workspace))
    try:
        ids_to_check = [ROOT_OBJECTIVE_ID] + [
            f"spec-{suffix}" for suffix, _, _ in _SPEC_TIER_PHASES
        ]
        for oid in ids_to_check:
            proj = tracker.get(oid)
            assert proj is not None, f"{oid} missing"
            assert proj.authored_by == "user", (
                f"{oid} authored_by = {proj.authored_by!r} (expected 'user')"
            )
    finally:
        tracker.close()


def test_AC39_2_trace_to_root_chain_every_link_user(tmp_path: Path) -> None:
    """For each seeded descendant, the trace_to_root chain terminates
    at the value-prop root and every link is user-authored."""
    workspace = _seed_dev(tmp_path)
    tracker = ObjectiveTracker(tracker_db_path_for(workspace))
    try:
        for suffix, _, _ in _SPEC_TIER_PHASES:
            chain = tracker.trace_to_root(f"spec-{suffix}")
            assert chain[-1].objective_id == ROOT_OBJECTIVE_ID
            for link in chain:
                assert link.authored_by == "user", (
                    f"link {link.objective_id} authored_by = "
                    f"{link.authored_by!r}; expected 'user'"
                )
    finally:
        tracker.close()


def test_AC39_2_no_record_has_persona_or_bootstrap_authored_by(
    tmp_path: Path,
) -> None:
    """Cross-check: no seeded record has ``authored_by`` set to any
    persona handle or to ``"workspace-bootstrap"`` — the seed is the
    user's authoring action structurally, not the framework's."""
    workspace = _seed_dev(tmp_path)
    tracker = ObjectiveTracker(tracker_db_path_for(workspace))
    try:
        all_recs = tracker.list()
        forbidden = {"primary-persona", "workspace-bootstrap", "primary"}
        for proj in all_recs:
            assert proj.authored_by not in forbidden, (
                f"{proj.objective_id} authored_by = {proj.authored_by!r} "
                f"(forbidden by AC39.2)"
            )
    finally:
        tracker.close()
