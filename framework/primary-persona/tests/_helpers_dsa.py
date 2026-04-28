"""Shared test helpers for amendment #74 (AC.DSA.*) — dispatcher-side
test-stub authoring.

Composes on amendment #52's `_helpers_a8` patterns: stub IPC client,
workspace-builder fixture, and a stub agent runner.

Adds two amendment-#74 specific helpers:
  - ``stub_workspace_dev_mode`` — monkeypatches the workspace_mode
    reader so the setup phase fires (AC.DSA.6).
  - ``stub_tracker`` / ``RecordingTracker`` — captures
    ``register_source_binding`` calls without needing a real SQLite
    DB (cheap path for the wrapper's setup-phase tests).
"""

from __future__ import annotations

import sys
import types
from pathlib import Path
from typing import Any


class RecordingTracker:
    """In-memory stand-in for ``ObjectiveTracker``.

    Records every ``register_source_binding`` call. The dispatcher's
    setup phase only consumes this method, so the stub does not need
    to implement ``manifest_rows_for_*`` etc. Tests that need
    cross-substrate composition (AC.DSA.8) build a tracker with rows
    pre-populated by hand.
    """

    def __init__(self) -> None:
        self.calls: list[dict[str, str]] = []
        self._raise: BaseException | None = None

    def set_register_exception(self, exc: BaseException) -> None:
        self._raise = exc

    def register_source_binding(
        self,
        *,
        component: str,
        ac_id: str,
        source_path_glob: str,
    ) -> None:
        if self._raise is not None:
            raise self._raise
        self.calls.append(
            {
                "component": component,
                "ac_id": ac_id,
                "source_path_glob": source_path_glob,
            }
        )


def stub_workspace_dev_mode(monkeypatch, *, mode: str = "dev-mode") -> None:
    """Inject a ``corpus_load_sentinel`` module returning ``mode``.

    The dispatch wrapper imports ``corpus_load_sentinel.workspace_mode``
    lazily inside ``_read_workspace_mode``. Monkeypatching
    ``sys.modules`` swaps the module before the lazy import resolves.
    """
    cls_mod = types.ModuleType("corpus_load_sentinel")
    cls_mod.workspace_mode = lambda _ws: mode
    monkeypatch.setitem(sys.modules, "corpus_load_sentinel", cls_mod)


def install_stub_active_scope_sentinel(monkeypatch) -> dict[str, Any]:
    """Install a recording stand-in for the
    ``active_scope_sentinel`` module.

    Captures every ``write_active_scope_sentinel`` call into a recorder
    dict the test asserts against. Returns the recorder.
    """
    recorder: dict[str, Any] = {"writes": [], "next_result": None}
    ass_mod = types.ModuleType("active_scope_sentinel")

    class _ScopeBinding:
        def __init__(self, *, component: str, ac_id: str) -> None:
            self.component = component
            self.ac_id = ac_id

    class _Result:
        def __init__(self, *, wrote: bool, reason: str, path: Path) -> None:
            self.wrote = wrote
            self.reason = reason
            self.path = path
            self.error_detail = ""

    def _write(workspace_root, *, scope_id, plan_path, bindings, session_id=None):
        recorder["writes"].append(
            {
                "workspace_root": Path(workspace_root),
                "scope_id": scope_id,
                "plan_path": plan_path,
                "bindings": tuple(
                    (b.component, b.ac_id) for b in bindings
                ),
                "session_id": session_id,
            }
        )
        if recorder["next_result"] is not None:
            return recorder["next_result"]
        target = Path(workspace_root) / "workspace" / ".pos" / "active-scope.json"
        return _Result(wrote=True, reason="written", path=target)

    ass_mod.ScopeBinding = _ScopeBinding
    ass_mod.write_active_scope_sentinel = _write
    monkeypatch.setitem(sys.modules, "active_scope_sentinel", ass_mod)
    return recorder


def install_stub_tracker(monkeypatch, tracker: RecordingTracker) -> None:
    """Replace the dispatch wrapper's ``_open_tracker`` with a function
    returning ``tracker``.

    This is the convention amendment #52's tests use for ``_open_tracker``-
    style module-level shims (see also A2 tests). It avoids having to
    set up a real SQLite DB for the setup-phase tests.
    """
    from primary_persona import dispatch_wrapper

    monkeypatch.setattr(
        dispatch_wrapper, "_open_tracker", lambda _ws: tracker
    )


def disable_iso_second_wait(monkeypatch) -> None:
    """No-op the deterministic ISO-second wait so tests run fast.

    Tests that explicitly verify the sentinel-before-manifest
    timestamp ordering invoke ``_wait_until_next_iso_second`` directly;
    other tests don't need to wait. This helper keeps the test suite
    sub-second total.
    """
    from primary_persona import dispatch_wrapper

    monkeypatch.setattr(
        dispatch_wrapper, "_wait_until_next_iso_second", lambda: None
    )
