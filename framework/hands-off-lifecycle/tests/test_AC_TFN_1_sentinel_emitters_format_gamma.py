"""AC.TFN.1 — sentinel emitters produce a fixed-width microsecond
``Z``-suffixed timestamp (format γ).

Per the locked plan-doc
``docs/rebuild/plans/a1-substrate-timestamp-format-normalization.md``
§4 AC.TFN.1: the two A1 sentinel writers (``active_scope_sentinel``,
``corpus_load_sentinel``) emit ``created_at`` strings that
byte-conform to the regex
``^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}\\.\\d{6}Z$``.
Pre-amendment-#75 the sentinels emitted second-resolution
``%Y-%m-%dT%H:%M:%SZ``; the format change closes the same-second
collision class A3's lex-compare predicate exhibited.
"""

from __future__ import annotations

import json
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


def test_AC_TFN_1_active_scope_sentinel_created_at_matches_format_gamma(
    tmp_path: Path,
) -> None:
    """The active-scope sentinel writes ``created_at`` strings that
    match the fixed-width microsecond-Z regex."""
    from active_scope_sentinel import (
        ScopeBinding,
        write_active_scope_sentinel,
    )

    write_active_scope_sentinel(
        tmp_path,
        scope_id="scope-tfn1",
        plan_path="docs/p.md",
        bindings=[ScopeBinding(component="c", ac_id="AC.X")],
    )
    on_disk = json.loads(
        (tmp_path / "workspace" / ".pos" / "active-scope.json").read_text()
    )
    created_at = on_disk["created_at"]
    assert _FORMAT_GAMMA_RE.match(created_at), (
        f"sentinel created_at does not conform to format γ: {created_at!r}"
    )
    assert len(created_at) == 27


def test_AC_TFN_1_active_scope_sentinel_now_iso_matches_format_gamma() -> None:
    """The sentinel module's private ``_now_iso`` helper emits
    format γ directly (covers the source-of-truth side too)."""
    from active_scope_sentinel import _now_iso

    ts = _now_iso()
    assert _FORMAT_GAMMA_RE.match(ts), (
        f"_now_iso does not conform to format γ: {ts!r}"
    )
    assert len(ts) == 27


def test_AC_TFN_1_corpus_load_sentinel_now_iso_matches_format_gamma() -> None:
    """The corpus-load sentinel's ``_now_iso`` emits format γ."""
    from corpus_load_sentinel import _now_iso

    ts = _now_iso()
    assert _FORMAT_GAMMA_RE.match(ts), (
        f"_now_iso does not conform to format γ: {ts!r}"
    )
    assert len(ts) == 27
