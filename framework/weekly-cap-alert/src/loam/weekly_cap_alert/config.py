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

"""The alert threshold — in **config, not code** (WS-A1 constraint / D-A1-4).

The threshold at which a weekly-cap crossing pings Luke is a value the owner
sets, not a constant the build hard-codes. :data:`DEFAULT_THRESHOLD_PCT` is the
**owner-ratified** number (backplane decision D5 = 60%), used when no config file
overrides it. :func:`load_threshold` reads an optional JSON config and **fails
open to the ratified default** on any absence/malformation — a bad config can
never wedge the alert or silently move the threshold to an un-ratified value.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

# Owner-ratified (backplane D5), NOT a placeholder: the weekly-cap utilization
# fraction (as a percentage of the enforced cap) at or above which the alert
# pings Luke. Overridable via the JSON config below or the --threshold-pct CLI
# flag; this constant is only the fallback when neither is present.
DEFAULT_THRESHOLD_PCT: float = 60.0

# Env override for the config path (test / CI seam); else the default location.
_CONFIG_ENV = "LOAM_WEEKLY_CAP_ALERT_CONFIG"
_DEFAULT_CONFIG_PATH = "~/.claude/weekly-cap-alert.json"

# The JSON key carrying the threshold percentage.
_THRESHOLD_KEY = "threshold_pct"


def config_path() -> Path:
    """The resolved config path: the env override if set, else the default."""
    raw = os.environ.get(_CONFIG_ENV) or _DEFAULT_CONFIG_PATH
    return Path(raw).expanduser()


def load_threshold() -> float:
    """Return the configured threshold percentage, or the ratified default.

    Reads ``{"threshold_pct": <number>}`` from :func:`config_path`. Fails open
    to :data:`DEFAULT_THRESHOLD_PCT` on a missing file, unreadable/invalid JSON,
    a non-object body, a missing/non-numeric ``threshold_pct``, or a value
    outside the sane ``(0, 100]`` band — a malformed config never yields a
    nonsensical threshold and never wedges the job.
    """
    path = config_path()
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return DEFAULT_THRESHOLD_PCT
    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return DEFAULT_THRESHOLD_PCT
    if not isinstance(payload, dict):
        return DEFAULT_THRESHOLD_PCT
    value = payload.get(_THRESHOLD_KEY)
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return DEFAULT_THRESHOLD_PCT
    threshold = float(value)
    if not 0.0 < threshold <= 100.0:
        return DEFAULT_THRESHOLD_PCT
    return threshold
