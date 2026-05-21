"""AC.FBMT1.APS.4 — session-start contributor lists only unsealed plans.

The session-start "amendments-in-flight" contributor reads
``docs/plans/`` directly (NOT ``docs/plans/sealed/``), so after the
T1.4 sweep it naturally lists only unsealed plans.

Per plan-doc ``amendment-134-fbm-tier1-foundations.md`` §4
AC.FBMT1.APS family + §15 backwards-compat.
"""

from __future__ import annotations

from pathlib import Path

import pytest


def test_AC_FBMT1_APS_4_glob_is_non_recursive(tmp_path: Path):
    """The contributor's glob ``amendment-*.md`` is non-recursive
    by construction — sealed plans under ``docs/plans/sealed/``
    do NOT surface."""
    from loam.primary_persona.session_start_gate import (
        enumerate_amendments_in_flight,
    )

    ws_root = tmp_path / "ws"
    plans = ws_root / "docs" / "plans"
    sealed = plans / "sealed"
    sealed.mkdir(parents=True)
    # Five in-flight plans at the top of docs/plans/.
    for i in range(5):
        (plans / f"amendment-{200 + i}-in-flight.md").write_text(
            f"# in-flight {i}\n", encoding="utf-8"
        )
    # Many sealed plans under docs/plans/sealed/.
    for i in range(20):
        (sealed / f"amendment-{100 + i}-sealed.md").write_text(
            f"# sealed {i}\n", encoding="utf-8"
        )

    result = enumerate_amendments_in_flight(ws_root)
    # Exactly five in-flight (the sealed/ subdir is invisible).
    assert len(result) == 5, (
        f"expected 5 in-flight; got {len(result)}: {result}"
    )
    # None of the listed paths are under sealed/.
    for path in result:
        assert "sealed/" not in path, (
            f"sealed plan-doc surfaced as in-flight: {path}"
        )


def test_AC_FBMT1_APS_4_empty_when_no_in_flight(tmp_path: Path):
    """When all plans are sealed (only ``docs/plans/sealed/`` is
    populated), the contributor returns an empty list — no in-
    flight plans to surface."""
    from loam.primary_persona.session_start_gate import (
        enumerate_amendments_in_flight,
    )

    ws_root = tmp_path / "ws"
    plans = ws_root / "docs" / "plans"
    sealed = plans / "sealed"
    sealed.mkdir(parents=True)
    for i in range(3):
        (sealed / f"amendment-{i}-sealed.md").write_text(
            "sealed\n", encoding="utf-8"
        )
    result = enumerate_amendments_in_flight(ws_root)
    assert result == []
