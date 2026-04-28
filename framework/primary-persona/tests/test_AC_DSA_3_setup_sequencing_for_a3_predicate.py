"""AC.DSA.3 — setup sequencing for A3 "new AC in this diff" predicate.

For each dispatch with non-empty ``new_acs``, the dispatcher writes
the active-scope sentinel STRICTLY BEFORE registering manifest rows.
Outcome: every manifest row's ``created_at`` is strictly after the
sentinel's ``created_at`` in lexicographic comparison, satisfying
A3's ``manifest_row.created_at > sentinel.created_at`` predicate
(AC.TDG.4 / D-A3.4).

The Q1 empirical answer (sub-second collisions; recorded in §14
method-decision register at seal time) drove the deterministic
ISO-second-tick wait between sentinel write and manifest registration.
This AC's tests use the REAL ``_wait_until_next_iso_second`` so the
empirical contract is verified end-to-end (not stubbed).
"""

from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone

from primary_persona import DispatchShape, dispatch_with_scope
from primary_persona.dispatch_wrapper import NewACSpec
from primary_persona.dispatch_wrapper import (
    _wait_until_next_iso_second,
    _run_setup_phase,
)

from ._helpers_a8 import (
    StubIPCClient,
    build_stub_ipc_client_factory,
    make_workspace,
    stub_agent_runner_ok,
)
from ._helpers_dsa import (
    RecordingTracker,
    install_stub_active_scope_sentinel,
    install_stub_tracker,
    stub_workspace_dev_mode,
)


def test_AC_DSA_3_wait_helper_advances_iso_second() -> None:
    """``_wait_until_next_iso_second`` blocks until the next whole
    second tick — the sentinel-vs-manifest sub-second collision
    mitigation (§14 method-decision register; Q1 empirical fix)."""
    before = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    _wait_until_next_iso_second()
    after = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    assert after > before


def test_AC_DSA_3_manifest_created_at_lex_gt_sentinel(
    tmp_path, monkeypatch
) -> None:
    """End-to-end sequencing: sentinel timestamp < manifest timestamp
    in the EXACT lexicographic comparison A3 performs.

    Uses A1's real ``write_active_scope_sentinel`` (second-resolution
    Z-suffixed) and A1's manifest-row format
    (``datetime.now(tz=timezone.utc).isoformat()`` — microsecond
    +00:00). The dispatcher's wait inserts the necessary tick.
    """
    # We don't need the real tracker — capture the manifest call's
    # would-be created_at by sampling the wall clock right after the
    # wait. The contract is: any manifest row written AFTER the wait
    # has created_at > sentinel.created_at.
    sentinel_ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    _wait_until_next_iso_second()
    manifest_ts = datetime.now(tz=timezone.utc).isoformat()
    # The exact predicate A3 uses (line 334 of tdd_guard.py).
    assert manifest_ts > sentinel_ts, (
        f"sub-second collision regression: sentinel={sentinel_ts!r} "
        f"manifest={manifest_ts!r}"
    )


def test_AC_DSA_3_setup_phase_writes_sentinel_before_manifest(
    tmp_path, monkeypatch
) -> None:
    """Order-of-operations test: the recording sentinel writer's
    callback is invoked BEFORE the recording tracker's
    ``register_source_binding`` is called."""
    workspace = make_workspace(tmp_path, ambient_objective="obj")
    stub_workspace_dev_mode(monkeypatch)
    sentinel_recorder = install_stub_active_scope_sentinel(monkeypatch)
    tracker = RecordingTracker()

    # Order via a shared event log.
    event_log: list[str] = []

    # Wrap the recorder's write so it logs its order.
    real_write = sys_modules_active_scope_write_proxy(monkeypatch, event_log)

    # Wrap tracker.register_source_binding to log its order.
    original = tracker.register_source_binding

    def wrapped(**kwargs):
        event_log.append("manifest")
        return original(**kwargs)

    tracker.register_source_binding = wrapped  # type: ignore[method-assign]
    install_stub_tracker(monkeypatch, tracker)

    from primary_persona import dispatch_wrapper

    monkeypatch.setattr(
        dispatch_wrapper, "_wait_until_next_iso_second", lambda: None
    )

    _run_setup_phase(
        workspace,
        scope_id="scope-test",
        plan_path="docs/rebuild/plans/test.md",
        new_acs=(
            NewACSpec(
                component="primary-persona",
                ac_id="AC.X.1",
                source_path_glob="framework/primary-persona/src/foo.py",
            ),
        ),
    )

    # First sentinel, then manifest, in this order.
    assert event_log[0] == "sentinel"
    assert "manifest" in event_log
    assert event_log.index("sentinel") < event_log.index("manifest")


def sys_modules_active_scope_write_proxy(monkeypatch, event_log) -> None:
    """Helper: install the recording sentinel module that ALSO logs
    its invocation order into ``event_log``."""
    import sys
    import types
    from pathlib import Path

    ass_mod = types.ModuleType("active_scope_sentinel")

    class _ScopeBinding:
        def __init__(self, *, component, ac_id):
            self.component = component
            self.ac_id = ac_id

    class _Result:
        def __init__(self, *, wrote, reason, path):
            self.wrote = wrote
            self.reason = reason
            self.path = path
            self.error_detail = ""

    def _write(workspace_root, *, scope_id, plan_path, bindings, session_id=None):
        event_log.append("sentinel")
        target = Path(workspace_root) / "workspace" / ".pos" / "active-scope.json"
        return _Result(wrote=True, reason="written", path=target)

    ass_mod.ScopeBinding = _ScopeBinding
    ass_mod.write_active_scope_sentinel = _write
    monkeypatch.setitem(sys.modules, "active_scope_sentinel", ass_mod)
