"""AC.SE.3 — active-scope sentinel read contract.

Per the locked plan-doc §4 AC.SE.3: a documented sentinel-reader
surface returns the parsed JSON object as a typed structure (or
``None`` when absent / malformed / unreadable). Reader never raises
on environmental failure; malformed JSON is surfaced as ``None``.
Concurrent read while writer is mid-rename returns either pre-
rename content or post-rename content (atomic — never a partial
read).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
HOOKS_DIR = REPO_ROOT / "hands-off-lifecycle" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

from active_scope_sentinel import (  # noqa: E402
    ActiveScopeSentinel,
    ScopeBinding,
    read_active_scope_sentinel,
    write_active_scope_sentinel,
)


def test_AC_SE_3_returns_none_when_absent(tmp_path: Path) -> None:
    assert read_active_scope_sentinel(tmp_path) is None


def test_AC_SE_3_round_trip_returns_typed_structure(
    tmp_path: Path,
) -> None:
    write_active_scope_sentinel(
        tmp_path,
        scope_id="A1",
        plan_path="docs/p.md",
        bindings=[
            ScopeBinding(component="objective-tracker", ac_id="AC.SE.6"),
            ScopeBinding(component="hands-off-lifecycle", ac_id="AC.SE.4"),
        ],
        session_id="sess-1",
    )
    sentinel = read_active_scope_sentinel(tmp_path)
    assert isinstance(sentinel, ActiveScopeSentinel)
    assert sentinel.scope_id == "A1"
    assert sentinel.plan_path == "docs/p.md"
    assert sentinel.session_id == "sess-1"
    assert len(sentinel.bindings) == 2
    assert sentinel.bindings[0].component == "objective-tracker"
    assert sentinel.bindings[0].ac_id == "AC.SE.6"


def test_AC_SE_3_returns_none_on_malformed_json(tmp_path: Path) -> None:
    pos = tmp_path / ".pos"
    pos.mkdir()
    (pos / "active-scope.json").write_text("not { valid json", encoding="utf-8")
    assert read_active_scope_sentinel(tmp_path) is None


def test_AC_SE_3_returns_none_on_missing_required_field(
    tmp_path: Path,
) -> None:
    pos = tmp_path / ".pos"
    pos.mkdir()
    (pos / "active-scope.json").write_text(
        '{"scope_id": "x"}\n', encoding="utf-8"
    )
    assert read_active_scope_sentinel(tmp_path) is None


def test_AC_SE_3_returns_none_on_bad_binding_shape(
    tmp_path: Path,
) -> None:
    """Bindings entries must each be a {component, ac_id} dict."""
    pos = tmp_path / ".pos"
    pos.mkdir()
    (pos / "active-scope.json").write_text(
        '{"scope_id": "x", "plan_path": "p", "bindings": '
        '[{"component": "c"}], "created_at": "2026-01-01T00:00:00Z"}\n',
        encoding="utf-8",
    )
    # Missing ac_id in a binding entry → reader returns None.
    assert read_active_scope_sentinel(tmp_path) is None


def test_AC_SE_3_reader_never_raises_on_environmental_failure(
    tmp_path: Path,
) -> None:
    """OSError on read returns None, not an exception."""
    pos = tmp_path / ".pos"
    pos.mkdir()
    target = pos / "active-scope.json"
    # Make the path a directory rather than a file — reading it as
    # text will OSError. The reader catches and returns None.
    target.mkdir()
    result = read_active_scope_sentinel(tmp_path)
    assert result is None
