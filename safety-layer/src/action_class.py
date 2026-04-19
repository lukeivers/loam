"""Framework-floor action-class enum.

The seven categories are locked per proposal §3.4 and mirror spec v1.0
Prime Rule 6 high-stakes-irreversible actions. The enum is the
framework's structural contract — a workspace cannot remove a category
because the validator refuses any ask-list load that drops a floor
entry (see `ask_list.AlwaysAskList._floor_cannot_shrink`).

Note on Eve-inference #4 (proposal §8): "seven framework-floor categories
ratified as a set, not individually." The builder has reviewed each
entry against the Tier A/B taxonomy in .claude/rules/security.md and
finds them internally consistent — `strategy_pivot_or_mission_change`
and `personal_life_judgment_call` read as governance events rather than
action classes, but they are classifiable as "action classes produced
by the primary persona before user consent" so the taxonomy holds.
Shipped as per proposal.
"""

from __future__ import annotations

from enum import Enum


class FrameworkFloorCategory(str, Enum):
    """Seven framework-fixed ask categories. A workspace cannot remove
    any of these from its always_ask.yaml — the Pydantic validator
    refuses the load (structural impossibility pattern, clause (g))."""

    commit_external_funds = "commit_external_funds"
    send_communication_as_user_to_third_party = "send_communication_as_user_to_third_party"
    strategy_pivot_or_mission_change = "strategy_pivot_or_mission_change"
    personal_life_judgment_call = "personal_life_judgment_call"
    destroy_user_data_beyond_workspace = "destroy_user_data_beyond_workspace"
    publish_to_public_surface_user_does_not_control = "publish_to_public_surface_user_does_not_control"
    modify_production_systems_serving_real_users = "modify_production_systems_serving_real_users"
