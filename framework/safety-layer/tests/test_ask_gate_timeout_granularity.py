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

"""Ask-list timeout granularity — A9 + ruling #4.

A9. Timeout is a schema-validated duration string (Nm|Nh|Nd) with a
    15-minute minimum. `5m` or `0h` entries fail load; `15m`, `4h`,
    `2d` are accepted.
"""

from __future__ import annotations

import pytest

from loam.safety_layer import AskListEntry, parse_duration_spec


@pytest.mark.parametrize("bad", ["5m", "14m", "0h", "0d", "7", "foo", "", " "])
def test_A9_below_floor_and_malformed_rejected(bad):
    with pytest.raises(ValueError):
        parse_duration_spec(bad)


@pytest.mark.parametrize(
    "good,minutes",
    [
        ("15m", 15),
        ("16m", 16),
        ("1h", 60),
        ("4h", 240),
        ("24h", 1440),
        ("2d", 2 * 24 * 60),
        (" 3h ", 180),
    ],
)
def test_A9_accepted_values_resolve_to_minutes(good, minutes):
    assert parse_duration_spec(good) == minutes


@pytest.mark.parametrize("bad", ["5m", "14m", "0h"])
def test_A9_entry_field_validator_rejects_below_floor(bad):
    with pytest.raises(ValueError):
        AskListEntry(
            action_class="x",
            timeout=bad,
            description="y",
        )


def test_A9_entry_field_validator_accepts_good_values():
    entry = AskListEntry(
        action_class="x",
        timeout="15m",
        description="y",
    )
    assert entry.timeout_minutes == 15
