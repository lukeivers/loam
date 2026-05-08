# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""AC.DSA.5 — fail-soft on substrate failure.

When any setup step fails (sentinel write returns ``wrote=False,
reason="failed-*"``; ``register_source_binding`` raises; stub write
raises OSError), the dispatcher records a structured NDJSON
diagnostic to ``<workspace>/workspace/.pos/dispatch-wrapper.log`` (the
existing diagnostic surface from amendment #52 D8) and PROCEEDS with
the dispatch. Setup failure does NOT cause the dispatcher to return
early or refuse the dispatch; the gates (A2/A3) provide the structural
enforcement and surface the failure to the operator at first-edit
time.
"""

from __future__ import annotations

import json
from pathlib import Path

from loam.primary_persona.dispatch_wrapper import NewACSpec
from loam.primary_persona.dispatch_wrapper import (
    _run_setup_phase,
    _diagnostic_log_path,
)

from ._helpers_dsa import (
    RecordingTracker,
    install_stub_active_scope_sentinel,
    install_stub_tracker,
    stub_workspace_dev_mode,
    disable_iso_second_wait,
)


def _diagnostic_records(workspace: Path) -> list[dict]:
    log = _diagnostic_log_path(workspace)
    if not log.exists():
        return []
    return [
        json.loads(ln)
        for ln in log.read_text(encoding="utf-8").splitlines()
        if ln.strip()
    ]


def test_AC_DSA_5_sentinel_failure_logs_diagnostic_and_proceeds(
    tmp_path, monkeypatch
) -> None:
    """Sentinel write returning ``wrote=False, reason='failed-permission'``
    logs the diagnostic and the function returns normally."""
    workspace = tmp_path
    stub_workspace_dev_mode(monkeypatch)
    disable_iso_second_wait(monkeypatch)
    recorder = install_stub_active_scope_sentinel(monkeypatch)

    # Make the sentinel writer return a failure outcome.
    class _FailureResult:
        def __init__(self):
            self.wrote = False
            self.reason = "failed-permission"
            self.path = workspace / "x"
            self.error_detail = "PermissionError: simulated"

    recorder["next_result"] = _FailureResult()

    tracker = RecordingTracker()
    install_stub_tracker(monkeypatch, tracker)

    # Function should not raise.
    _run_setup_phase(
        workspace,
        scope_id="scope-fail",
        plan_path="docs/p.md",
        new_acs=(NewACSpec("c", "AC.X.1", "framework/c/src/y.py"),),
    )

    records = _diagnostic_records(workspace)
    sentinel_records = [
        r for r in records
        if r.get("event") == "setup" and r.get("step") == "sentinel"
    ]
    assert len(sentinel_records) == 1
    assert sentinel_records[0]["wrote"] is False
    assert sentinel_records[0]["reason"] == "failed-permission"
    assert sentinel_records[0]["error_detail"]


def test_AC_DSA_5_register_source_binding_raises_logs_and_proceeds(
    tmp_path, monkeypatch
) -> None:
    """Tracker raise → diagnostic logged with the exception class +
    message; subsequent steps still execute."""
    workspace = tmp_path
    stub_workspace_dev_mode(monkeypatch)
    disable_iso_second_wait(monkeypatch)
    install_stub_active_scope_sentinel(monkeypatch)

    tracker = RecordingTracker()
    tracker.set_register_exception(RuntimeError("DB is locked"))
    install_stub_tracker(monkeypatch, tracker)

    _run_setup_phase(
        workspace,
        scope_id="scope-fail",
        plan_path="docs/p.md",
        new_acs=(
            NewACSpec("c", "AC.X.1", "framework/c/src/y.py"),
            NewACSpec("c", "AC.X.2", "framework/c/src/z.py"),
        ),
    )

    records = _diagnostic_records(workspace)
    manifest_records = [
        r for r in records
        if r.get("event") == "setup" and r.get("step") == "manifest"
    ]
    # Both manifest registrations fired (fail-soft: one's failure
    # doesn't suppress the next).
    assert len(manifest_records) == 2
    assert all(r["outcome"] == "failed-exception" for r in manifest_records)
    assert all(
        "RuntimeError" in r["error_detail"] for r in manifest_records
    )

    # Stub-writes also fire — fail-soft contract.
    stub_records = [
        r for r in records
        if r.get("event") == "setup" and r.get("step") == "stub"
    ]
    assert len(stub_records) == 2


def test_AC_DSA_5_tracker_unavailable_logs_and_proceeds(
    tmp_path, monkeypatch
) -> None:
    """``_open_tracker`` returning None ⇒ each manifest row's
    diagnostic carries 'failed-tracker-unavailable' and the function
    returns normally."""
    workspace = tmp_path
    stub_workspace_dev_mode(monkeypatch)
    disable_iso_second_wait(monkeypatch)
    install_stub_active_scope_sentinel(monkeypatch)

    from loam.primary_persona import dispatch_wrapper

    monkeypatch.setattr(dispatch_wrapper, "_open_tracker", lambda _ws: None)

    _run_setup_phase(
        workspace,
        scope_id="scope-fail",
        plan_path="docs/p.md",
        new_acs=(NewACSpec("c", "AC.X.1", "framework/c/src/y.py"),),
    )

    records = _diagnostic_records(workspace)
    mr = [
        r for r in records
        if r.get("event") == "setup" and r.get("step") == "manifest"
    ]
    assert len(mr) == 1
    assert mr[0]["outcome"] == "failed-tracker-unavailable"


def test_AC_DSA_5_stub_write_oserror_logs_and_proceeds(
    tmp_path, monkeypatch
) -> None:
    """A stub write OSError yields ``failed-os-error`` outcome; the
    function returns normally and does not raise."""
    workspace = tmp_path
    stub_workspace_dev_mode(monkeypatch)
    disable_iso_second_wait(monkeypatch)
    install_stub_active_scope_sentinel(monkeypatch)
    install_stub_tracker(monkeypatch, RecordingTracker())

    # Pre-create the stub directory with a hostile permission so
    # write_text raises OSError. Simpler trick: monkeypatch
    # _write_stub_idempotent's underlying Path.write_text. Easiest:
    # create a directory at the stub's expected file path so opening
    # it for write raises IsADirectoryError (an OSError subclass).
    stub_target = (
        workspace
        / "framework"
        / "c"
        / "tests"
        / "test_AC_X_1_placeholder.py"
    )
    stub_target.parent.mkdir(parents=True)
    # Make a directory at the file path → write_text raises
    # IsADirectoryError (a subclass of OSError).
    stub_target.mkdir()

    _run_setup_phase(
        workspace,
        scope_id="scope-x",
        plan_path="docs/p.md",
        new_acs=(NewACSpec("c", "AC.X.1", "framework/c/src/y.py"),),
    )

    records = _diagnostic_records(workspace)
    sr = [
        r for r in records
        if r.get("event") == "setup" and r.get("step") == "stub"
    ]
    assert len(sr) == 1
    # The 'outcome' is one of the failed-* classes.
    assert sr[0]["outcome"].startswith("failed-")
