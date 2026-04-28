"""AC.TFN.4 — dispatcher no longer needs the iso-second wait.

Per the locked plan-doc
``docs/rebuild/plans/a1-substrate-timestamp-format-normalization.md``
§4 AC.TFN.4: the dispatcher's setup-phase sentinel-then-manifest
sequence produces strictly-increasing lex-compared ``created_at``
strings WITHOUT any wall-clock wait between the two writes.

Outcome: 1000/1000 back-to-back invocations produce
``manifest.created_at > sentinel.created_at`` lex-compared. The
previous ``_wait_until_next_iso_second`` helper is removed; no
caller depends on it.
"""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
HOOKS_DIR = REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks"
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))


def test_AC_TFN_4_wait_helper_is_removed_from_dispatch_wrapper() -> None:
    """Importing ``_wait_until_next_iso_second`` from the dispatch
    wrapper raises ``ImportError`` — the helper is gone."""
    from primary_persona import dispatch_wrapper

    assert not hasattr(dispatch_wrapper, "_wait_until_next_iso_second"), (
        "_wait_until_next_iso_second still present on dispatch_wrapper "
        "post-amendment-#75"
    )


def test_AC_TFN_4_back_to_back_emitters_lex_compare_correctly() -> None:
    """Tight loop: 1000 back-to-back (sentinel-now, manifest-now)
    pairs ALL satisfy ``manifest > sentinel`` lexicographically.

    Pre-amendment-#75 this was 1000/1000 collisions (the FIDRAFT
    capture's empirical). Post-fix it is 0/1000.
    """
    from active_scope_sentinel import _now_iso as sentinel_now_iso
    from objective_tracker.store import (
        _now_iso_microsecond_z as manifest_now_iso,
    )

    collisions = 0
    for _ in range(1000):
        sentinel_ts = sentinel_now_iso()
        manifest_ts = manifest_now_iso()
        if not manifest_ts > sentinel_ts:
            collisions += 1
    assert collisions == 0, (
        f"AC.TFN.4 regression: {collisions}/1000 back-to-back pairs "
        f"failed manifest > sentinel lex-compare"
    )
