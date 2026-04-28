"""AC.DSA.8 — composition: build dispatch with declared new_acs sails
through A2 + A3.

Given a dispatch with ``new_acs`` against a workspace where A2 + A3
are installed and DEV MODE is active, after the dispatcher's setup
phase completes, evaluating A2's ``objective_binding_gate.evaluate``
against a hypothetical Edit at any path matching the registered glob
returns ALLOW, and evaluating A3's ``tdd_guard.evaluate`` against
the same hypothetical Edit returns ALLOW.

This is the structural composition contract: the gates become
INVISIBLE on the happy path. Failure means the dispatcher's setup
phase did not actually pre-condition the gate predicates.
"""

from __future__ import annotations

import sys
import types
from datetime import datetime, timezone
from pathlib import Path

from primary_persona.dispatch_wrapper import NewACSpec
from primary_persona.dispatch_wrapper import (
    _write_stub_idempotent,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
HOOKS_DIR = REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks"


def _import_gates_with_workspace_mode(monkeypatch, *, mode: str):
    """Import A2 + A3 with a stubbed workspace_mode reader so the
    DEV-MODE-bit short-circuit branches as configured."""
    if str(HOOKS_DIR) not in sys.path:
        sys.path.insert(0, str(HOOKS_DIR))
    cls_mod = types.ModuleType("corpus_load_sentinel")
    cls_mod.workspace_mode = lambda _ws: mode
    monkeypatch.setitem(sys.modules, "corpus_load_sentinel", cls_mod)
    # Force re-import for hook-side _gate_helpers.read_workspace_mode_or_normal_use
    # which lazy-imports corpus_load_sentinel inside the helper.
    import objective_binding_gate as obg
    import tdd_guard as a3
    return obg, a3


class _RowsTracker:
    """Stand-in tracker exposing the read-side ``manifest_rows_for_ac``
    used by both A2 and A3. Constructed from a list of pre-registered
    rows."""

    def __init__(self, rows: list[dict]) -> None:
        self._rows = rows

    def manifest_rows_for_ac(self, component: str, ac_id: str) -> list[dict]:
        return [
            r for r in self._rows
            if r["component"] == component and r["ac_id"] == ac_id
        ]


def test_AC_DSA_8_after_setup_a2_admits_path(tmp_path, monkeypatch) -> None:
    """After the dispatcher's setup phase, A2's evaluate returns
    ALLOW for an Edit at a path matching the registered glob."""
    obg, a3 = _import_gates_with_workspace_mode(monkeypatch, mode="dev-mode")

    # Build a sentinel binding the new AC. Use the REAL A1 sentinel
    # writer so the on-disk JSON shape matches what A2 reads.
    sys.path.insert(0, str(HOOKS_DIR))
    from active_scope_sentinel import (
        ScopeBinding,
        write_active_scope_sentinel,
    )

    write_active_scope_sentinel(
        tmp_path,
        scope_id="scope-test",
        plan_path="docs/p.md",
        bindings=(ScopeBinding(component="primary-persona", ac_id="AC.DSA.99"),),
    )
    # Amendment #75 (AC.TFN.4): no synthetic wait. Both A1 emitters
    # produce format γ (microsecond ``Z`` suffix); microsecond
    # resolution makes the back-to-back lex-compare correct without
    # the wait helper. The fixture below mirrors the post-#75 manifest
    # emitter shape (``%Y-%m-%dT%H:%M:%S.%fZ``) so the lex-compare
    # against the real γ-format sentinel is structurally correct.
    rows = [
        {
            "component": "primary-persona",
            "ac_id": "AC.DSA.99",
            "source_path_glob": (
                "framework/primary-persona/src/foo.py"
            ),
            "created_at": datetime.now(tz=timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%S.%fZ"
            ),
        }
    ]
    monkeypatch.setattr(
        obg, "_open_tracker", lambda _ws: _RowsTracker(rows)
    )

    decision = obg.evaluate(
        workspace_root=tmp_path,
        tool_name="Edit",
        tool_input={
            "file_path": str(
                tmp_path / "framework" / "primary-persona" / "src" / "foo.py"
            )
        },
    )
    assert decision.decision == "allow"


def test_AC_DSA_8_after_setup_a3_admits_path(tmp_path, monkeypatch) -> None:
    """After the dispatcher's setup phase, A3's evaluate returns
    ALLOW for an Edit at a path matching the registered glob —
    because the dispatcher pre-authored the placeholder test stub
    at A3's expected glob with a function matching A3's expected
    prefix."""
    obg, a3 = _import_gates_with_workspace_mode(monkeypatch, mode="dev-mode")

    sys.path.insert(0, str(HOOKS_DIR))
    from active_scope_sentinel import (
        ScopeBinding,
        write_active_scope_sentinel,
    )

    write_active_scope_sentinel(
        tmp_path,
        scope_id="scope-test",
        plan_path="docs/p.md",
        bindings=(ScopeBinding(component="primary-persona", ac_id="AC.DSA.99"),),
    )
    # Amendment #75 (AC.TFN.4): no synthetic wait; format γ on both
    # A1 emitters makes the lex-compare structurally correct.
    rows = [
        {
            "component": "primary-persona",
            "ac_id": "AC.DSA.99",
            "source_path_glob": (
                "framework/primary-persona/src/foo.py"
            ),
            "created_at": datetime.now(tz=timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%S.%fZ"
            ),
        }
    ]
    monkeypatch.setattr(
        a3, "_open_tracker", lambda _ws: _RowsTracker(rows)
    )

    # Author the dispatcher's stub at A3's expected location.
    spec = NewACSpec(
        component="primary-persona",
        ac_id="AC.DSA.99",
        source_path_glob="framework/primary-persona/src/foo.py",
    )
    out = _write_stub_idempotent(
        tmp_path, spec, scope_id="scope-test", plan_path="docs/p.md"
    )
    assert out["outcome"] == "written"

    decision = a3.evaluate(
        workspace_root=tmp_path,
        tool_name="Edit",
        tool_input={
            "file_path": str(
                tmp_path / "framework" / "primary-persona" / "src" / "foo.py"
            )
        },
    )
    assert decision.decision == "allow"


def test_AC_DSA_8_a3_denies_without_dispatcher_stub(
    tmp_path, monkeypatch
) -> None:
    """Negative control: WITHOUT the dispatcher's stub, A3 denies
    (the new AC has no matching test file). Confirms the
    composition test isn't a false positive — the stub IS what makes
    A3 admit."""
    obg, a3 = _import_gates_with_workspace_mode(monkeypatch, mode="dev-mode")

    sys.path.insert(0, str(HOOKS_DIR))
    from active_scope_sentinel import (
        ScopeBinding,
        write_active_scope_sentinel,
    )

    write_active_scope_sentinel(
        tmp_path,
        scope_id="scope-test",
        plan_path="docs/p.md",
        bindings=(ScopeBinding(component="primary-persona", ac_id="AC.DSA.99"),),
    )
    # Amendment #75 (AC.TFN.4): no synthetic wait; format γ on both
    # A1 emitters makes the lex-compare structurally correct.
    rows = [
        {
            "component": "primary-persona",
            "ac_id": "AC.DSA.99",
            "source_path_glob": (
                "framework/primary-persona/src/foo.py"
            ),
            "created_at": datetime.now(tz=timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%S.%fZ"
            ),
        }
    ]
    monkeypatch.setattr(
        a3, "_open_tracker", lambda _ws: _RowsTracker(rows)
    )

    # NO stub authored. A3 must DENY.
    decision = a3.evaluate(
        workspace_root=tmp_path,
        tool_name="Edit",
        tool_input={
            "file_path": str(
                tmp_path / "framework" / "primary-persona" / "src" / "foo.py"
            )
        },
    )
    assert decision.decision == "deny"
