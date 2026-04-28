"""AC.DSA.9 — diagnostic surface for setup-phase observability.

Every setup-phase fire (success or failure for sentinel, manifest,
each stub) emits a structured NDJSON record to the existing
``<workspace>/workspace/.pos/dispatch-wrapper.log`` surface. The
recorded data is sufficient to reconstruct: when the setup fired,
which artefact was authored / failed, the AC IDs in scope, the
resolved file paths, and (on failure) the reason class.
"""

from __future__ import annotations

import json
from pathlib import Path

from primary_persona.dispatch_wrapper import NewACSpec
from primary_persona.dispatch_wrapper import (
    _diagnostic_log_path,
    _run_setup_phase,
)

from ._helpers_dsa import (
    RecordingTracker,
    install_stub_active_scope_sentinel,
    install_stub_tracker,
    stub_workspace_dev_mode,
    disable_iso_second_wait,
)


def _records(workspace: Path) -> list[dict]:
    log = _diagnostic_log_path(workspace)
    if not log.exists():
        return []
    return [
        json.loads(ln)
        for ln in log.read_text(encoding="utf-8").splitlines()
        if ln.strip()
    ]


def test_AC_DSA_9_setup_emits_one_record_per_step(
    tmp_path, monkeypatch
) -> None:
    """A successful setup phase emits: 1 sentinel + N manifest + N stub
    records, each tagged with ``event=setup`` + ``step=<class>``."""
    workspace = tmp_path
    stub_workspace_dev_mode(monkeypatch)
    disable_iso_second_wait(monkeypatch)
    install_stub_active_scope_sentinel(monkeypatch)
    install_stub_tracker(monkeypatch, RecordingTracker())

    new_acs = (
        NewACSpec("c", "AC.X.1", "framework/c/src/y.py"),
        NewACSpec("c", "AC.X.2", "framework/c/src/z.py"),
    )
    _run_setup_phase(
        workspace,
        scope_id="scope-test",
        plan_path="docs/p.md",
        new_acs=new_acs,
    )

    records = _records(workspace)
    setup = [r for r in records if r.get("event") == "setup"]
    assert len([r for r in setup if r["step"] == "sentinel"]) == 1
    assert len([r for r in setup if r["step"] == "manifest"]) == 2
    assert len([r for r in setup if r["step"] == "stub"]) == 2


def test_AC_DSA_9_record_carries_ac_ids_and_paths(
    tmp_path, monkeypatch
) -> None:
    """Every setup record carries enough data to identify the
    artefact, the AC, and the resolved on-disk path."""
    workspace = tmp_path
    stub_workspace_dev_mode(monkeypatch)
    disable_iso_second_wait(monkeypatch)
    install_stub_active_scope_sentinel(monkeypatch)
    install_stub_tracker(monkeypatch, RecordingTracker())

    spec = NewACSpec(
        component="primary-persona",
        ac_id="AC.X.1",
        source_path_glob="framework/primary-persona/src/y.py",
    )
    _run_setup_phase(
        workspace,
        scope_id="scope-record-test",
        plan_path="docs/the-plan.md",
        new_acs=(spec,),
    )

    records = _records(workspace)
    setup = [r for r in records if r.get("event") == "setup"]

    # Sentinel record carries scope_id + path.
    sentinel = [r for r in setup if r["step"] == "sentinel"][0]
    assert sentinel["scope_id"] == "scope-record-test"
    assert "path" in sentinel

    # Manifest record carries scope_id + component + ac_id +
    # source_path_glob + outcome.
    manifest = [r for r in setup if r["step"] == "manifest"][0]
    assert manifest["scope_id"] == "scope-record-test"
    assert manifest["component"] == "primary-persona"
    assert manifest["ac_id"] == "AC.X.1"
    assert manifest["source_path_glob"] == (
        "framework/primary-persona/src/y.py"
    )
    assert manifest["outcome"] == "registered"

    # Stub record carries scope_id + component + ac_id + outcome + path.
    stub = [r for r in setup if r["step"] == "stub"][0]
    assert stub["scope_id"] == "scope-record-test"
    assert stub["component"] == "primary-persona"
    assert stub["ac_id"] == "AC.X.1"
    assert stub["outcome"] in {
        "written",
        "skipped-identical",
        "skipped-agent-authored",
    }
    assert stub["path"].endswith("test_AC_X_1_placeholder.py")


def test_AC_DSA_9_record_has_ts(tmp_path, monkeypatch) -> None:
    """Every record has a UTC timestamp (the existing amendment-#52
    diagnostic shape)."""
    workspace = tmp_path
    stub_workspace_dev_mode(monkeypatch)
    disable_iso_second_wait(monkeypatch)
    install_stub_active_scope_sentinel(monkeypatch)
    install_stub_tracker(monkeypatch, RecordingTracker())

    _run_setup_phase(
        workspace,
        scope_id="scope-ts",
        plan_path="docs/p.md",
        new_acs=(NewACSpec("c", "AC.X.1", "framework/c/src/y.py"),),
    )

    records = _records(workspace)
    for r in records:
        assert "ts" in r
        # Roundtrip ISO parse.
        from datetime import datetime
        datetime.fromisoformat(r["ts"])
