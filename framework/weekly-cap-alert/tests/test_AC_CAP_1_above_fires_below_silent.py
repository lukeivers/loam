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

"""AC.CAP.1 (outcome-altitude) — above threshold fires; below is silent.

Drives the REAL production entry point ``run_alert`` end-to-end, injecting only
the two live boundaries (the sealed usage probe and the channel delivery). No
internal helper is tested in isolation.
"""

from __future__ import annotations

import re

from conftest import CapturingNotify, probe_returning, windows_at

from loam.weekly_cap_alert import run_alert
from loam.weekly_cap_alert.alert import KIND_ABOVE, KIND_BELOW

_PERCENT = re.compile(r"\d+(?:\.\d+)?\s*%")


def test_above_threshold_fires_a_notification_with_the_number():
    notify = CapturingNotify()
    decision = run_alert(
        probe=probe_returning(windows_at(seven_day_pct=72.0)),
        threshold_pct=60.0,
        notify_fn=notify,
    )
    assert decision.kind == KIND_ABOVE
    assert decision.notify is True
    # A notification was actually delivered, carrying the utilization number.
    assert notify.called
    assert len(notify.messages) == 1
    assert _PERCENT.search(notify.messages[0])
    assert "72.0%" in notify.messages[0]


def test_at_threshold_boundary_fires():
    # Crossing is >= the threshold: exactly-at counts as a crossing.
    notify = CapturingNotify()
    decision = run_alert(
        probe=probe_returning(windows_at(seven_day_pct=60.0)),
        threshold_pct=60.0,
        notify_fn=notify,
    )
    assert decision.kind == KIND_ABOVE
    assert notify.called


def test_below_threshold_is_silent():
    notify = CapturingNotify()
    decision = run_alert(
        probe=probe_returning(windows_at(seven_day_pct=41.0)),
        threshold_pct=60.0,
        notify_fn=notify,
    )
    assert decision.kind == KIND_BELOW
    assert decision.notify is False
    # Silence: the channel was never pinged.
    assert not notify.called
    assert notify.messages == []


def test_reads_the_weekly_window_not_the_five_hour_throttle():
    # five_hour is way above threshold, seven_day is below. If the alert wrongly
    # read the 5-hour window it would fire; reading the WEEKLY window it stays
    # silent. This is the constraint that the seven_day bucket is the one read.
    notify = CapturingNotify()
    decision = run_alert(
        probe=probe_returning(windows_at(seven_day_pct=20.0, five_hour_pct=99.0)),
        threshold_pct=60.0,
        notify_fn=notify,
    )
    assert decision.kind == KIND_BELOW
    assert not notify.called


def test_threshold_defaults_to_the_owner_ratified_60(monkeypatch, tmp_path):
    # With no threshold override and no config file, run_alert resolves the
    # ratified default (D5 = 60%) through the real config loader: 55% stays
    # silent, 65% fires — proving the ratified default is actually 60.
    monkeypatch.setenv(
        "LOAM_WEEKLY_CAP_ALERT_CONFIG", str(tmp_path / "absent.json"))

    silent = CapturingNotify()
    run_alert(probe=probe_returning(windows_at(55.0)), notify_fn=silent)
    assert not silent.called

    loud = CapturingNotify()
    run_alert(probe=probe_returning(windows_at(65.0)), notify_fn=loud)
    assert loud.called
