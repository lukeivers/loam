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

"""AC.CLP-DOC.4 — the check has an explicit escape hatch for the cases
where bespoke IS correct, and using it leaves an audit-visible record.

Two hatches (D-DOC.3):
  1. The ``primitive-rationale:`` line in the dispatch prompt — a
     bespoke-shaped dispatch WITH the line is allowed; the line persists
     in the prompt + the NDJSON fire log records hatch-use.
  2. The emergency-off (env ``LOAM_PRIMITIVE_CHECK=off`` OR a workspace
     sentinel) — allowed + logged.

Both verified through the production ``main()`` entry-point (stdin
envelope → stdout + on-disk audit log), with the mode reader stubbed to
dev-mode at the module boundary exactly as a bootstrapped dev workspace
would read.
"""

from __future__ import annotations

import io
import json
import sys
import types
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
HOOKS_DIR = REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks"
PLUGIN_HOOKS_DIR = REPO_ROOT / "plugins" / "dev-sdlc" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))
sys.path.insert(0, str(PLUGIN_HOOKS_DIR))


def _stub_dev_mode(monkeypatch) -> None:
    cls_mod = types.ModuleType("corpus_load_sentinel")
    cls_mod.workspace_mode = lambda _: "dev-mode"
    monkeypatch.setitem(sys.modules, "corpus_load_sentinel", cls_mod)
    # _gate_helpers caches the import lazily; re-import the hook fresh so
    # its _helpers.read_workspace_mode_or_normal_use sees the stub.
    sys.modules.pop("primitive_check_guard", None)


def _run_main(monkeypatch, envelope: dict) -> str:
    import primitive_check_guard as guard

    monkeypatch.setattr(
        guard._helpers,
        "read_workspace_mode_or_normal_use",
        lambda _: "dev-mode",
    )
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(envelope)))
    captured = io.StringIO()
    monkeypatch.setattr(sys, "stdout", captured)
    rc = guard.main()
    assert rc == 0
    return captured.getvalue()


_BESPOKE_PROMPT = (
    "Build a polling loop that re-checks the deploy every hour."
)


def test_AC_CLP_DOC_4_rationale_line_is_the_hatch(
    tmp_path, monkeypatch
) -> None:
    """A bespoke-shaped dispatch WITH a primitive-rationale line is
    allowed (empty deny stdout) and the fire is logged as hatch-use."""
    _stub_dev_mode(monkeypatch)
    prompt = (
        _BESPOKE_PROMPT
        + "\nprimitive-rationale: bespoke — the per-iteration work "
        "needs a custom stop-condition the native loop does not expose."
    )
    out = _run_main(
        monkeypatch,
        {
            "cwd": str(tmp_path),
            "tool_name": "Task",
            "tool_input": {"prompt": prompt},
        },
    )
    assert out.strip() == "" or "deny" not in out, (
        f"rationale-line dispatch must be allowed; got {out!r}"
    )
    log = tmp_path / "workspace" / ".pos" / "primitive-check-guard.log"
    row = json.loads(log.read_text().strip().splitlines()[-1])
    assert row["decision"] == "allow"
    assert row["kind"] == "hatch", (
        "hatch-use must be recorded as kind=hatch in the audit log"
    )


def test_AC_CLP_DOC_4_emergency_off_env(tmp_path, monkeypatch) -> None:
    """The emergency-off env var allows a would-be-deny dispatch and
    logs it as kind=off."""
    _stub_dev_mode(monkeypatch)
    monkeypatch.setenv("LOAM_PRIMITIVE_CHECK", "off")
    out = _run_main(
        monkeypatch,
        {
            "cwd": str(tmp_path),
            "tool_name": "Task",
            "tool_input": {"prompt": _BESPOKE_PROMPT},
        },
    )
    assert "deny" not in out, "emergency-off must allow"
    log = tmp_path / "workspace" / ".pos" / "primitive-check-guard.log"
    row = json.loads(log.read_text().strip().splitlines()[-1])
    assert row["decision"] == "allow"
    assert row["kind"] == "off"


def test_AC_CLP_DOC_4_emergency_off_sentinel(
    tmp_path, monkeypatch
) -> None:
    """The workspace sentinel file allows a would-be-deny dispatch and
    logs it as kind=off."""
    _stub_dev_mode(monkeypatch)
    sentinel = tmp_path / ".loam" / ".primitive-check-off"
    sentinel.parent.mkdir(parents=True, exist_ok=True)
    sentinel.write_text("", encoding="utf-8")
    out = _run_main(
        monkeypatch,
        {
            "cwd": str(tmp_path),
            "tool_name": "Task",
            "tool_input": {"prompt": _BESPOKE_PROMPT},
        },
    )
    assert "deny" not in out, "sentinel must allow"
    log = tmp_path / "workspace" / ".pos" / "primitive-check-guard.log"
    row = json.loads(log.read_text().strip().splitlines()[-1])
    assert row["kind"] == "off"


def test_AC_CLP_DOC_4_no_hatch_denies(tmp_path, monkeypatch) -> None:
    """Control: the same bespoke dispatch WITHOUT a hatch is denied —
    so the hatch is what makes the difference, not a permissive default.
    """
    _stub_dev_mode(monkeypatch)
    out = _run_main(
        monkeypatch,
        {
            "cwd": str(tmp_path),
            "tool_name": "Task",
            "tool_input": {"prompt": _BESPOKE_PROMPT},
        },
    )
    payload = json.loads(out)
    assert (
        payload["hookSpecificOutput"]["permissionDecision"] == "deny"
    )
