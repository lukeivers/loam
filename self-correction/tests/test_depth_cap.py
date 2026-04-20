"""CR15 — depth cap 3 via parent_correction_id walk."""

from __future__ import annotations

from self_correction import (
    CorrectionConfig,
    CorrectionEpisode,
    CorrectionStore,
    EpisodeState,
    SelfCorrectionController,
    build_trigger_from_user_report,
)
from self_correction.bounds import compute_depth, depth_cap_check
from self_correction.spec import CorrectionTrigger, TriggerSource


def _seed_chain(store: CorrectionStore, length: int) -> str:
    """Seed a chain of episodes of given length; return the deepest id."""
    prev = None
    last = None
    for i in range(length):
        trig_id = f"trig-chain-{i}"
        store.insert_trigger(
            CorrectionTrigger(
                trigger_id=trig_id,
                source=TriggerSource.user_reported,
            )
        )
        ep = CorrectionEpisode(
            episode_id=f"ep-chain-{i}",
            trigger_id=trig_id,
            correction_scope_id=f"scope-chain-{i}",
            parent_correction_id=prev,
            failure_class="chain_class",
            state=EpisodeState.running,
        )
        store.insert_episode(ep)
        prev = ep.episode_id
        last = ep.episode_id
    return last


def test_CR15_compute_depth_zero_when_no_parent(store: CorrectionStore) -> None:
    assert compute_depth(parent_correction_id=None, store=store) == 0


def test_CR15_compute_depth_walks_chain(store: CorrectionStore) -> None:
    last = _seed_chain(store, length=3)
    assert compute_depth(parent_correction_id=last, store=store) == 3


def test_CR15_depth_cap_check_trips_at_cap(store: CorrectionStore) -> None:
    cfg = CorrectionConfig(depth_cap=3)
    last = _seed_chain(store, length=3)
    # Opening one more would be the 4th — trip.
    trip = depth_cap_check(
        parent_correction_id=last, store=store, config=cfg
    )
    assert trip is not None
    assert trip.reason == "depth_cap"
    assert trip.depth == 3


def test_CR15_depth_cap_allows_under_cap(store: CorrectionStore) -> None:
    cfg = CorrectionConfig(depth_cap=3)
    last = _seed_chain(store, length=2)
    assert depth_cap_check(
        parent_correction_id=last, store=store, config=cfg
    ) is None


async def test_CR15_intake_refuses_at_cap_and_notifies(
    controller: SelfCorrectionController,
    channel_and_inbox,
) -> None:
    _, inbox = channel_and_inbox
    # Seed a chain of 3 episodes.
    last = _seed_chain(controller.store, length=3)

    tr = build_trigger_from_user_report(
        description="fourth in chain",
        related_scope_id=None,
        reporter="eve",
    )
    result = await controller.intake(tr, parent_correction_id=last)
    assert result is not None
    assert result.state == EpisodeState.escalated
    assert result.correction_scope_id is None
    assert result.refusal_reason == "depth_cap"

    # One-on-one notification fired.
    assert len(inbox) == 1
    assert "depth cap" in inbox[0].lower() or "depth" in inbox[0].lower()
