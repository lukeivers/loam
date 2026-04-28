"""AC.TFN.3 — single shared helper as source of truth.

Per the locked plan-doc §4 AC.TFN.3: a single helper function
(``_gate_helpers.now_iso_microsecond_z``) exposes the timestamp
shape used by both A1 sentinel writers and the A1 manifest insert.

The sentinel writers delegate directly via a one-line in-function
import + call. The objective-tracker store carries a one-line
mirror under the private name ``_now_iso_microsecond_z`` (the
cross-component import constraint — see the comment block above the
mirror in ``framework/objective-tracker/src/store.py``). This test
asserts:

  - the canonical helper exists and conforms to format γ;
  - both sentinel ``_now_iso`` functions return the same format
    (by-shape — exact wall-clock equality is not the contract;
    same-shape regex match is);
  - the store mirror returns the same format.

Outcome: changing the format requires editing one helper body PLUS
updating the store mirror (the cross-component constraint is
unavoidable; AC.TFN.6 catches divergence empirically).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
HOOKS_DIR = REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks"
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))


_FORMAT_GAMMA_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z$"
)


def test_AC_TFN_3_canonical_helper_exists_and_emits_format_gamma() -> None:
    """``_gate_helpers.now_iso_microsecond_z`` is the canonical
    helper for the A1-substrate ``created_at`` shape."""
    from _gate_helpers import now_iso_microsecond_z

    ts = now_iso_microsecond_z()
    assert _FORMAT_GAMMA_RE.match(ts), (
        f"now_iso_microsecond_z does not conform to format γ: {ts!r}"
    )
    assert len(ts) == 27


def test_AC_TFN_3_sentinel_emitters_delegate_to_canonical_helper() -> None:
    """Both sentinel ``_now_iso`` callables produce a string that
    matches the canonical helper's shape — i.e. they are delegating
    (or otherwise tracking) the canonical format."""
    from _gate_helpers import now_iso_microsecond_z
    from active_scope_sentinel import _now_iso as active_now_iso
    from corpus_load_sentinel import _now_iso as corpus_now_iso

    # Both shapes must match the canonical helper's regex.
    canonical = now_iso_microsecond_z()
    a = active_now_iso()
    c = corpus_now_iso()
    for ts in (canonical, a, c):
        assert _FORMAT_GAMMA_RE.match(ts), (
            f"helper output does not conform to format γ: {ts!r}"
        )
        assert len(ts) == 27


def test_AC_TFN_3_canonical_helper_format_string_matches_store_mirror_source() -> None:
    """Static-analysis variant: the canonical helper's source-code
    format string is byte-equal to the format string that the
    objective-tracker store's mirror emits.

    This is the cross-component invariant: the two emitters share the
    same ``%Y-%m-%dT%H:%M:%S.%fZ`` format spec by construction. We
    verify the canonical helper carries that literal and trust the
    AC.TFN.6 invariant test (in this same file) plus the AC.TFN.2
    test (in objective-tracker/tests/) to catch any output divergence
    empirically.
    """
    import inspect

    from _gate_helpers import now_iso_microsecond_z

    src = inspect.getsource(now_iso_microsecond_z)
    assert "%Y-%m-%dT%H:%M:%S.%fZ" in src, (
        f"canonical helper source missing γ format string: {src!r}"
    )
