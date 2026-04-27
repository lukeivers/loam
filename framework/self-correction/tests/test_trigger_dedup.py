"""CR6 — trigger dedup: same trigger within TTL produces one episode."""

from __future__ import annotations

import pytest

from self_correction import (
    SelfCorrectionController,
    build_trigger_from_user_report,
)
from self_correction.dedup import make_dedup_key, normalise_reason


def test_CR6_normalise_reason_lowers_and_collapses() -> None:
    assert normalise_reason("  FOO   BAR  ") == "foo bar"
    assert normalise_reason(None) == ""


def test_CR6_dedup_key_is_deterministic() -> None:
    k1 = make_dedup_key(scope_id="s1", source="scope_failure", normalised_reason="x")
    k2 = make_dedup_key(scope_id="s1", source="scope_failure", normalised_reason="x")
    assert k1 == k2
    k3 = make_dedup_key(scope_id="s2", source="scope_failure", normalised_reason="x")
    assert k1 != k3


async def test_CR6_same_trigger_within_ttl_dedups(
    controller: SelfCorrectionController,
) -> None:
    tr1 = build_trigger_from_user_report(
        description="same thing",
        related_scope_id="scope-1",
        reporter="eve",
    )
    tr2 = build_trigger_from_user_report(
        description="same thing",
        related_scope_id="scope-1",
        reporter="eve",
    )
    # Identical description → identical dedup_key.
    assert tr1.dedup_key == tr2.dedup_key

    # First intake should open (or at least not dedup).
    # We don't wire a real activate_fn here; the controller's
    # _open_correction_scope will skip activation when create_scope_fn
    # is None. The episode still gets persisted with state=running.
    r1 = await controller.intake(tr1)
    assert r1 is not None
    assert r1.episode_id is not None

    # Second intake with the same dedup_key should return None.
    r2 = await controller.intake(tr2)
    assert r2 is None


async def test_CR6_different_reason_does_not_dedup(
    controller: SelfCorrectionController,
) -> None:
    tr1 = build_trigger_from_user_report(
        description="first",
        related_scope_id="scope-X",
        reporter="eve",
    )
    tr2 = build_trigger_from_user_report(
        description="second — different",
        related_scope_id="scope-X",
        reporter="eve",
    )
    assert tr1.dedup_key != tr2.dedup_key
    r1 = await controller.intake(tr1)
    r2 = await controller.intake(tr2)
    assert r1 is not None
    assert r2 is not None
    assert r1.episode_id != r2.episode_id
