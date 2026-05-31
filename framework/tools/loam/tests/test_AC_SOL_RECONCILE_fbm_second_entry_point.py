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

"""AC.SOL-RECONCILE.* — ONE detector, two entry points (the subsumption).

  * AC.SOL-RECONCILE.1 — the SAME comparator that detects a doc's stale
    status ALSO detects a stored FBM claim contradicting ground truth,
    invoked over a stored episode/claim instead of a doc.
  * AC.SOL-RECONCILE.2 — the reconcile output is dated + scoped to the
    check, never an eternal claim.
"""

from __future__ import annotations

from loam_cli.audit.probe import Liveness
from loam_cli.audit.reconcile import StoredClaim, reconcile_stored_claim
from loam_cli.audit.record import ComponentState, StateOfLoam


def _record() -> StateOfLoam:
    return StateOfLoam(
        head_sha="abc123",
        components=(
            ComponentState("fbm", Liveness.MERGED, "component", "seal merged"),
        ),
    )


def test_AC_SOL_RECONCILE_1_stored_claim_routed_through_same_comparator() -> None:
    """A stored FBM claim that a live component is dark is caught by the
    SAME comparator the doc-status caller uses (the subsumption)."""
    finding = reconcile_stored_claim(
        StoredClaim(component="fbm", claim_token="dark", episode_id="ep-42"),
        _record(),
        checked_on="2026-05-31",
    )
    assert finding.diverged is True
    assert finding.divergence is not None
    assert finding.divergence.derived is Liveness.MERGED
    assert finding.episode_id == "ep-42"


def test_AC_SOL_RECONCILE_1_agreeing_stored_claim_reconciles_clean() -> None:
    """A stored claim that agrees with ground truth reconciles clean —
    no divergence (low false-positive on the second entry point too)."""
    finding = reconcile_stored_claim(
        StoredClaim(component="fbm", claim_token="live", episode_id="ep-7"),
        _record(),
        checked_on="2026-05-31",
    )
    assert finding.diverged is False
    assert finding.divergence is None


def test_AC_SOL_RECONCILE_2_finding_is_dated_and_scoped() -> None:
    """The reconcile output carries the date the check ran + the episode/
    component scope — never stored as an eternal negative. The rendered
    finding names the dated check, so it cannot become the next stale
    claim."""
    finding = reconcile_stored_claim(
        StoredClaim(component="fbm", claim_token="dark", episode_id="ep-42"),
        _record(),
        checked_on="2026-05-31",
    )
    assert finding.checked_on == "2026-05-31"
    rendered = finding.render()
    # Dated + scoped to THIS check, not an eternal "fbm is X" claim.
    assert "2026-05-31" in rendered
    assert "ep-42" in rendered


def test_AC_SOL_RECONCILE_2_checked_on_defaults_to_today() -> None:
    """When no date is supplied the finding stamps today's ISO date —
    the dated scope is automatic, never omitted."""
    finding = reconcile_stored_claim(
        StoredClaim(component="fbm", claim_token="live", episode_id="ep-1"),
        _record(),
    )
    # ISO date shape YYYY-MM-DD.
    assert len(finding.checked_on) == 10
    assert finding.checked_on.count("-") == 2
