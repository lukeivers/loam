"""AC.DSA.3 — setup sequencing for A3 "new AC in this diff" predicate.

For each dispatch with non-empty ``new_acs``, the dispatcher writes
the active-scope sentinel STRICTLY BEFORE registering manifest rows.
Outcome: every manifest row's ``created_at`` is strictly after the
sentinel's ``created_at`` in lexicographic comparison, satisfying
A3's ``manifest_row.created_at > sentinel.created_at`` predicate
(AC.TDG.4 / D-A3.4).

Pre-amendment-#75 the sentinel emitted second-resolution Z-format and
the manifest emitted microsecond-+00:00 format; same-second writes
flipped the lex order (collision rate 100% in tight-loop empirical).
The dispatcher mitigated by waiting one ISO-second tick between
sentinel and manifest. Amendment #75 (AC.TFN.1, AC.TFN.2, AC.TFN.4)
migrated both A1 emitters to format γ (microsecond-Z, fixed-width 27
chars), eliminating the failure class structurally; the wait helper
was removed and these tests now verify the AC.DSA.3 outcome on the
post-fix substrate (no synthetic delay between writes).
"""

from __future__ import annotations

import sys
from pathlib import Path

from loam.primary_persona.dispatch_wrapper import NewACSpec, _run_setup_phase

from ._helpers_a8 import make_workspace
from ._helpers_dsa import (
    RecordingTracker,
    install_stub_active_scope_sentinel,
    install_stub_tracker,
    stub_workspace_dev_mode,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
HOOKS_DIR = REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks"


def test_AC_DSA_3_manifest_created_at_lex_gt_sentinel(tmp_path) -> None:
    """End-to-end sequencing: sentinel timestamp < manifest timestamp
    in the EXACT lexicographic comparison A3 performs, with NO
    synthetic wait between writes.

    Uses A1's real sentinel emitter (post-amendment-#75 format γ:
    microsecond ``Z``) and A1's real manifest emitter (post-#75
    format γ). Microsecond resolution distinguishes back-to-back
    writes; lex-comparison reflects the temporal write order
    structurally.
    """
    if str(HOOKS_DIR) not in sys.path:
        sys.path.insert(0, str(HOOKS_DIR))
    from active_scope_sentinel import _now_iso as _sentinel_now_iso

    sentinel_ts = _sentinel_now_iso()
    # No wait. Both sides emit format γ; microsecond resolution makes
    # back-to-back lex-compare correct.
    from loam.objective_tracker.store import _now_iso_microsecond_z as _manifest_now_iso

    manifest_ts = _manifest_now_iso()
    # The exact predicate A3 uses.
    assert manifest_ts > sentinel_ts, (
        f"same-second collision regression: sentinel={sentinel_ts!r} "
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
    install_stub_active_scope_sentinel(monkeypatch)
    tracker = RecordingTracker()

    # Order via a shared event log.
    event_log: list[str] = []

    # Wrap the recorder's write so it logs its order.
    sys_modules_active_scope_write_proxy(monkeypatch, event_log)

    # Wrap tracker.register_source_binding to log its order.
    original = tracker.register_source_binding

    def wrapped(**kwargs):
        event_log.append("manifest")
        return original(**kwargs)

    tracker.register_source_binding = wrapped  # type: ignore[method-assign]
    install_stub_tracker(monkeypatch, tracker)

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
