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

"""Structural-impossibility defence-in-depth — C27, C28.

- C27: Reservation construction with any negative amount raises
  ValidationError. SQL CHECK constraints match.
- C28: CostConfig refuses malformed YAML (negative ceilings, invalid
  warning_fraction) at load time.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from pydantic import ValidationError

from loam.cost_governance import (
    CostConfig,
    CostStore,
    Reservation,
    RollingCeiling,
    SessionCeiling,
    load_config,
)


def test_C27_reservation_refuses_negative_amounts() -> None:
    with pytest.raises(ValidationError):
        Reservation(
            scope_id="s", session_id="sess",
            reserved_money_cents=-1,
        )
    with pytest.raises(ValidationError):
        Reservation(
            scope_id="s", session_id="sess",
            actual_tokens=-5,
        )
    with pytest.raises(ValidationError):
        Reservation(
            scope_id="s", session_id="sess",
            reserved_time_seconds=-10,
        )


def test_C27_sql_check_constraints_refuse_negatives(tmp_path: Path) -> None:
    """Direct SQL INSERT with a negative amount is rejected by SQLite."""
    store = CostStore(tmp_path / "cost.sqlite")
    try:
        with pytest.raises(sqlite3.IntegrityError):
            store._conn.execute(
                """INSERT INTO reservations
                   (scope_id, session_id, state,
                    reserved_money_cents, reserved_tokens, reserved_time_seconds,
                    actual_money_cents, actual_tokens, actual_time_seconds,
                    reserved_at, reconciled_at)
                   VALUES ('s', 'sess', 'active',
                           -1, 0, 0,
                           0, 0, 0,
                           '2026-01-01T00:00:00+00:00', NULL)"""
            )
    finally:
        store.close()


def test_C27_sql_check_refuses_negative_in_session_rollup(tmp_path: Path) -> None:
    store = CostStore(tmp_path / "cost.sqlite")
    try:
        with pytest.raises(sqlite3.IntegrityError):
            store._conn.execute(
                """INSERT INTO session_rollups
                   (session_id, total_time_seconds, total_tokens, total_money_cents,
                    started_at)
                   VALUES ('s', 0, 0, -1, '2026-01-01T00:00:00+00:00')"""
            )
    finally:
        store.close()


def test_C28_config_refuses_negative_ceiling() -> None:
    with pytest.raises(ValidationError):
        SessionCeiling(money_cents=-1)
    with pytest.raises(ValidationError):
        RollingCeiling(
            window_kind="daily",
            duration_seconds=3600,
            tokens=-1,
        )
    with pytest.raises(ValidationError):
        RollingCeiling(
            window_kind="daily",
            duration_seconds=0,  # must be > 0
        )


def test_C28_config_refuses_invalid_warning_fraction() -> None:
    with pytest.raises(ValidationError):
        CostConfig(warning_fraction=-0.1)
    with pytest.raises(ValidationError):
        CostConfig(warning_fraction=0.0)
    with pytest.raises(ValidationError):
        CostConfig(warning_fraction=1.0)
    with pytest.raises(ValidationError):
        CostConfig(warning_fraction=2.0)


def test_C28_load_config_refuses_bad_yaml(tmp_path: Path) -> None:
    bad_path = tmp_path / "bad.yaml"
    bad_path.write_text(
        """
warning_fraction: 1.5
session:
  money_cents: 1000
"""
    )
    with pytest.raises(ValidationError):
        load_config(bad_path)


def test_C28_load_config_refuses_negative_ceiling_in_yaml(tmp_path: Path) -> None:
    bad_path = tmp_path / "bad.yaml"
    bad_path.write_text(
        """
session:
  money_cents: -100
"""
    )
    with pytest.raises(ValidationError):
        load_config(bad_path)


def test_C28_load_config_returns_default_when_file_absent(tmp_path: Path) -> None:
    """Missing config is not an error — cost governance is opt-in."""
    cfg = load_config(tmp_path / "nonexistent.yaml")
    assert cfg.session.money_cents is None
    # Default rolling windows are daily + hourly.
    windows = {r.window_kind for r in cfg.rolling}
    assert windows == {"daily", "hourly"}
    assert cfg.warning_fraction == 0.8
