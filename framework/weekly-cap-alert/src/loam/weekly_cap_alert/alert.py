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

"""The weekly-cap alert decision + production entry point.

Reads the SEALED usage-window-guard's REAL ``seven_day`` (weekly) cap
utilization and turns it into one of three outcomes:

* **above** the owner-set threshold  → fire a notification carrying the number;
* **below** the threshold            → silence (``notify_fn`` is never called);
* **usage unavailable**              → fire the categorical failure *reason*
  with **no** number (D-A1-1). Firing here is deliberate: WS-A4's cap guard
  fails open on ``UsageUnavailable`` *because this alert covers the blind
  window* — a silent unavailable would leave nobody watching a dark cap reader.

The weekly (``seven_day``) window is the one that is read, not the 5-hour one:
the weekly bucket is the only Claude limit that costs anything; the 5-hour
window is a throttle (standing owner rule).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from loam.usage_window_guard import UsageUnavailable, UsageWindows, read

from .config import load_threshold
from .notify import NotifyFn, stdout_notify

# The reading is injectable so the AC tests can drive deterministic probe
# results; the default is the real sealed probe, so run_alert() with no
# arguments exercises the full production path.
ProbeFn = Callable[[], "UsageWindows | UsageUnavailable"]

# The three mutually-exclusive outcomes.
KIND_ABOVE = "above"
KIND_BELOW = "below"
KIND_UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class AlertDecision:
    """The outcome of one alert evaluation.

    ``notify`` is whether the channel was pinged; ``message`` is the exact text
    delivered (or, for the silent ``below`` case, the text that would have been
    — kept for the job log, never sent). ``kind`` names which branch fired.
    """

    kind: str
    notify: bool
    message: str


def evaluate(
    result: "UsageWindows | UsageUnavailable",
    threshold_pct: float,
) -> AlertDecision:
    """Turn a probe result + threshold into the alert decision.

    * ``UsageWindows`` with ``seven_day.utilization >= threshold`` → ``above``
      (notify, message carries the utilization %).
    * ``UsageWindows`` below threshold → ``below`` (no notify; silence).
    * ``UsageUnavailable`` → ``unavailable`` (notify, message carries the
      categorical ``reason.value`` and NO utilization number — ``detail`` is
      deliberately NOT interpolated, so nothing that looks like a fabricated %
      reaches the message).
    """
    if isinstance(result, UsageUnavailable):
        # D-A1-1: fire the categorical reason, never a number. reason.value is a
        # stable diagnostic token (e.g. "auth_rejected") with no percentage.
        message = (
            "Weekly Claude cap alert could not read usage "
            f"(reason: {result.reason.value}). No utilization number available "
            "this run; the reading will be retried on the next scheduled probe."
        )
        return AlertDecision(kind=KIND_UNAVAILABLE, notify=True, message=message)

    utilization = result.seven_day.utilization
    if utilization >= threshold_pct:
        message = (
            f"Weekly Claude cap at {utilization:.1f}% of the enforced limit "
            f"(alert threshold {threshold_pct:.1f}%). Approaching the weekly "
            "cap — the only Claude limit that actually costs anything."
        )
        return AlertDecision(kind=KIND_ABOVE, notify=True, message=message)

    # Below threshold: silence. The message is retained for the job log only and
    # is never handed to notify_fn.
    message = (
        f"Weekly Claude cap at {utilization:.1f}% — below the "
        f"{threshold_pct:.1f}% alert threshold. No action."
    )
    return AlertDecision(kind=KIND_BELOW, notify=False, message=message)


def run_alert(
    *,
    probe: ProbeFn = read,
    threshold_pct: Optional[float] = None,
    notify_fn: NotifyFn = stdout_notify,
) -> AlertDecision:
    """Production entry point: probe → evaluate → (maybe) notify.

    Reads the weekly cap via ``probe`` (default: the real sealed probe), resolves
    the threshold (explicit ``threshold_pct`` wins, else the configured/ratified
    value), evaluates, and — only when the decision says so — hands the message
    to ``notify_fn``. Returns the :class:`AlertDecision` either way so a caller
    (and the launchd job log) can see what happened.

    Called with no arguments, this exercises the full production path: the real
    sealed usage probe and the stdout delivery default.
    """
    threshold = load_threshold() if threshold_pct is None else threshold_pct
    result = probe()
    decision = evaluate(result, threshold)
    if decision.notify:
        notify_fn(decision.message)
    return decision
