"""AC.TFN.6 — format invariant under back-to-back same-second writes.

Per the locked plan-doc §4 AC.TFN.6: two A1 substrate writes (any
combination of sentinel-then-manifest, manifest-then-sentinel,
sentinel-then-sentinel, manifest-then-manifest) issued within the
same wall-clock second produce DISTINCT ``created_at`` strings, AND
lex-comparison reflects the temporal write order.

Outcome: 1000/1000 same-second back-to-back writes have lex-compared
``created_at`` values matching the call order.

The empirical scope (1000 iterations) is the same as #74's pre-fix
empirical to make pre/post-fix collision rates directly comparable.
"""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
HOOKS_DIR = REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks"
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))


def test_AC_TFN_6_canonical_helper_same_second_pair_distinct_and_ordered() -> None:
    """``now_iso_microsecond_z`` called twice back-to-back produces
    two strings, the second strictly greater than the first."""
    from _gate_helpers import now_iso_microsecond_z

    collisions = 0
    out_of_order = 0
    for _ in range(1000):
        a = now_iso_microsecond_z()
        b = now_iso_microsecond_z()
        if a == b:
            collisions += 1
        elif b < a:
            out_of_order += 1
    assert collisions == 0, (
        f"AC.TFN.6: {collisions}/1000 same-microsecond collisions "
        f"(microsecond resolution insufficient to distinguish back-"
        f"to-back calls)"
    )
    assert out_of_order == 0, (
        f"AC.TFN.6: {out_of_order}/1000 lex-out-of-order pairs"
    )


def test_AC_TFN_6_sentinel_then_manifest_lex_ordered() -> None:
    """Mixed pair: active-scope sentinel emitter, then manifest
    emitter. Lex order matches call order."""
    from active_scope_sentinel import _now_iso as sentinel_now_iso
    from objective_tracker.store import (
        _now_iso_microsecond_z as manifest_now_iso,
    )

    collisions = 0
    for _ in range(1000):
        a = sentinel_now_iso()
        b = manifest_now_iso()
        if not b > a:
            collisions += 1
    assert collisions == 0, (
        f"AC.TFN.6: {collisions}/1000 sentinel-then-manifest pairs "
        f"failed lex-order"
    )


def test_AC_TFN_6_manifest_then_sentinel_lex_ordered() -> None:
    """Reverse pair: manifest first, then sentinel. Lex order
    matches call order."""
    from active_scope_sentinel import _now_iso as sentinel_now_iso
    from objective_tracker.store import (
        _now_iso_microsecond_z as manifest_now_iso,
    )

    collisions = 0
    for _ in range(1000):
        a = manifest_now_iso()
        b = sentinel_now_iso()
        if not b > a:
            collisions += 1
    assert collisions == 0, (
        f"AC.TFN.6: {collisions}/1000 manifest-then-sentinel pairs "
        f"failed lex-order"
    )


def test_AC_TFN_6_corpus_then_active_lex_ordered() -> None:
    """Pair of sentinel emitters: corpus-load then active-scope.
    Both delegate to the same canonical helper; lex order matches
    call order."""
    from active_scope_sentinel import _now_iso as active_now_iso
    from corpus_load_sentinel import _now_iso as corpus_now_iso

    collisions = 0
    for _ in range(1000):
        a = corpus_now_iso()
        b = active_now_iso()
        if not b > a:
            collisions += 1
    assert collisions == 0, (
        f"AC.TFN.6: {collisions}/1000 corpus-then-active pairs "
        f"failed lex-order"
    )
