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

"""AC.SACH.4 — the hook NEVER aborts a subagent dispatch. Any internal
error (missing kernel file, malformed/empty envelope, memory backend
down) still lets the subagent start: the bundle degrades to a
``[...]``-style marker but the hook never raises + always exits 0.

Each degenerate input is fed to the production hook entry-point
(``main()``) and to the composer; the assertions are (a) clean exit 0,
(b) no raise, (c) a degraded-but-present bundle.
"""

from __future__ import annotations

import importlib.util
import io
import json
from pathlib import Path

import pytest

from conftest import REPO_ROOT, make_envelope

from loam.frame_kernel.bundle import (
    MISSING_KERNEL_MARKER,
    compose_bundle,
    render_envelope,
)

# Load the hook script module by path (it lives under hooks/, not the
# package) so we exercise the REAL production entry-point.
_HOOK_PATH = REPO_ROOT / "framework" / "frame-kernel" / "hooks" / "subagent_start_context.py"
_spec = importlib.util.spec_from_file_location("subagent_start_context", _HOOK_PATH)
assert _spec is not None and _spec.loader is not None
hook = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(hook)


def _run_hook(stdin_text: str, monkeypatch) -> tuple[int, str]:
    """Drive the hook's main() with *stdin_text*; return (rc, stdout)."""
    monkeypatch.setattr("sys.stdin", io.StringIO(stdin_text))
    out = io.StringIO()
    monkeypatch.setattr("sys.stdout", out)
    rc = hook.main()
    return rc, out.getvalue()


def test_absent_kernel_file_degrades_not_raises(tmp_path: Path) -> None:
    """A workspace with NO kernel file: the microkernel tier degrades to
    the missing-marker; compose_bundle does not raise."""
    # tmp_path has no kernel/loam-microkernel.md.
    bundle = compose_bundle(make_envelope(tmp_path))
    assert MISSING_KERNEL_MARKER in bundle


def test_unreadable_kernel_file_degrades_not_raises(tmp_path: Path) -> None:
    """A kernel path that is a DIRECTORY (read raises OSError): degrades
    to the missing-marker, no raise."""
    kernel_dir = tmp_path / "kernel"
    kernel_dir.mkdir(parents=True)
    # Make loam-microkernel.md a directory so read_text raises.
    (kernel_dir / "loam-microkernel.md").mkdir()
    bundle = compose_bundle(make_envelope(tmp_path))
    assert MISSING_KERNEL_MARKER in bundle


def test_empty_envelope_still_emits_microkernel_only_bundle(monkeypatch) -> None:
    """Empty stdin: the hook exits 0 and emits a microkernel-only bundle
    (degenerate-but-present), never blocks the dispatch."""
    rc, out = _run_hook("", monkeypatch)
    assert rc == 0
    # Empty envelope -> no workspace -> microkernel missing-marker, but
    # the bundle (and the JSON envelope) is still emitted.
    payload = json.loads(out)
    assert payload["hookSpecificOutput"]["hookEventName"] == "SubagentStart"


def test_malformed_json_envelope_exits_clean(monkeypatch) -> None:
    """Garbage (non-JSON) stdin: the hook exits 0, never raises."""
    rc, out = _run_hook("}{ this is not json", monkeypatch)
    assert rc == 0
    # Treated as empty envelope; still emits a structured envelope.
    payload = json.loads(out)
    assert "hookSpecificOutput" in payload


def test_memory_backend_error_degrades_not_raises(
    real_kernel_workspace: Path, monkeypatch,
) -> None:
    """When the memory factory raises (backend down), the memory tier
    degrades to the unavailable-marker and the bundle still composes."""
    from loam.primary_persona import mcp_memory_client as live_mod

    def _boom(workspace_root):
        raise RuntimeError("memory backend down")

    monkeypatch.setattr(live_mod, "build_live_mcp_memory_client", _boom)
    bundle = compose_bundle(
        make_envelope(real_kernel_workspace, task_text="anything")
    )
    assert "=== relevant memory ===" in bundle
    assert "[memory unavailable" in bundle


def test_full_hook_real_envelope_exits_zero(
    real_kernel_workspace: Path, monkeypatch,
) -> None:
    """End-to-end: a well-formed envelope through the production hook
    exits 0 and emits a valid additionalContext envelope (the
    no-abort guarantee on the happy path too)."""
    env = make_envelope(real_kernel_workspace, task_text="do the thing")
    rc, out = _run_hook(json.dumps(env), monkeypatch)
    assert rc == 0
    payload = json.loads(out)
    injected = payload["hookSpecificOutput"]["additionalContext"]
    # All three tiers present.
    assert "=== loam microkernel" in injected
    assert "=== active workstream context ===" in injected
    assert "=== relevant memory ===" in injected


def test_render_envelope_is_valid_json() -> None:
    """The emitted envelope is always valid JSON (a malformed envelope
    would itself be a dispatch-abort risk)."""
    payload = json.loads(render_envelope("any bundle text"))
    assert payload["hookSpecificOutput"]["additionalContext"] == "any bundle text"
