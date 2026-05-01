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

"""AC.MPF.1 — Stop hook is re-seated on every session-start.

Outcome (per locked plan §4 AC.MPF.1): ``pos_session_start.py``'s
``main()`` invokes ``_maybe_reseat_stop_hook(loam_root)`` on every
session-start. The helper is fail-soft (any exception caught,
returns silently), and the underlying ``_maybe_merge_stop`` from
``first_run_helper`` is idempotent over pos-v2-owned stanzas
(``test_AC_M_11_merge_stop_re_merge_pos_v2_owned.py`` confirms this).

This closes Surface 1 of the diagnostic agent's report
(``.scratch/claude-output/stop-hook-and-retrieval-diagnostic.md``):
pos3's first-run completed 2026-04-23 16:23 UTC and ``hooks.Stop``
was never merged because the merge code only fired from first-run-
only paths in ``first_run_helper.py``. Post-amendment-#95 the
supervisor path retrofits the stanza on every session-start.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from scripts.pos_session_start import _maybe_reseat_stop_hook


REPO_ROOT = Path(__file__).resolve().parents[3]
HOOKS_DIR = REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks"


def _make_workspace(tmp_path: Path) -> Path:
    """Build a tmp_path workspace with .claude/settings.json carrying
    pre-amendment-#95 shape (SessionStart + UserPromptSubmit only)."""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    claude_dir = workspace / ".claude"
    claude_dir.mkdir()
    (claude_dir / "settings.json").write_text(
        json.dumps(
            {
                "hooks": {
                    "SessionStart": [
                        {
                            "matcher": "",
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": (
                                        f"{workspace}/.venv/bin/python "
                                        "-m loam.primary_persona.cli "
                                        "session-start"
                                    ),
                                    "async": False,
                                    "timeout": 5,
                                }
                            ],
                        }
                    ],
                    "UserPromptSubmit": [
                        {
                            "matcher": "",
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": (
                                        f"{workspace}/.venv/bin/python "
                                        "-m loam.primary_persona.cli "
                                        "user-prompt-submit"
                                    ),
                                    "async": False,
                                    "timeout": 5,
                                }
                            ],
                        }
                    ],
                },
                "agent": "primary",
            }
        )
    )
    # Mock framework structure so the helper's hooks_dir check passes.
    (workspace / "framework" / "hands-off-lifecycle" / "hooks").mkdir(
        parents=True
    )
    return workspace


def test_AC_MPF_1_reseat_helper_fail_soft_on_missing_hooks_dir(
    tmp_path: Path,
) -> None:
    """When ``framework/hands-off-lifecycle/hooks/`` doesn't exist
    under loam_root, the helper returns silently — no exception
    propagates to the supervisor's main path.
    """
    workspace = tmp_path / "ws-no-hooks"
    workspace.mkdir()
    # No framework/hands-off-lifecycle/hooks directory.
    # Must not raise.
    _maybe_reseat_stop_hook(workspace)
    # No settings.json was created.
    assert not (workspace / ".claude" / "settings.json").exists()


def test_AC_MPF_1_reseat_helper_fail_soft_on_import_error(
    tmp_path: Path,
) -> None:
    """When the hooks_dir exists but ``first_run_helper`` is missing
    (e.g. malformed framework tree), the helper still returns
    silently.
    """
    workspace = tmp_path / "ws-bad-hooks"
    workspace.mkdir()
    (workspace / "framework" / "hands-off-lifecycle" / "hooks").mkdir(
        parents=True
    )
    # The directory exists but does NOT contain first_run_helper.py
    # — the lazy import raises ImportError. Helper must catch.
    _maybe_reseat_stop_hook(workspace)
    assert not (workspace / ".claude" / "settings.json").exists()


def test_AC_MPF_1_reseat_helper_calls_maybe_merge_stop_with_correct_args(
    tmp_path: Path,
) -> None:
    """The helper imports ``_maybe_merge_stop`` from
    ``first_run_helper`` and invokes it with ``loam_root`` +
    ``settings_path`` derived from ``loam_root / .claude /
    settings.json``.
    """
    workspace = _make_workspace(tmp_path)

    # Patch _maybe_merge_stop in the imported module so we can record
    # the call. The helper imports lazily inside the function.
    with patch.dict(sys.modules, {}, clear=False):
        # Insert hooks dir into sys.path so the lazy import resolves.
        if str(HOOKS_DIR) not in sys.path:
            sys.path.insert(0, str(HOOKS_DIR))

        import first_run_helper  # type: ignore[import-not-found]

        original = first_run_helper._maybe_merge_stop
        recorder = MagicMock()
        try:
            first_run_helper._maybe_merge_stop = recorder
            _maybe_reseat_stop_hook(workspace)
        finally:
            first_run_helper._maybe_merge_stop = original

    assert recorder.call_count == 1
    kwargs = recorder.call_args.kwargs
    assert kwargs["loam_root"] == workspace
    assert kwargs["settings_path"] == workspace / ".claude" / "settings.json"


def test_AC_MPF_1_reseat_helper_called_from_main(monkeypatch) -> None:
    """``main()`` invokes ``_maybe_reseat_stop_hook(loam_root)`` after
    ``_maybe_install_status_line``. The exact call ordering matters
    because both write to the same settings.json — the runtime
    invariant is that all three (status_line, stop, primary work)
    leave a coherent file.

    Regression-prevention: source-grep that ``main()``'s body
    references ``_maybe_reseat_stop_hook``.
    """
    import inspect

    from scripts import pos_session_start

    src = inspect.getsource(pos_session_start.main)
    assert "_maybe_reseat_stop_hook" in src, (
        "main() must invoke _maybe_reseat_stop_hook(loam_root) so "
        "workspaces past first-run gain hooks.Stop on next session-start"
    )
    # Also assert it's positionally after _maybe_install_status_line —
    # both are supervisor-path retrofits and the order is "additive UX
    # first, then memory-pipeline". Concrete: status_line index <
    # reseat_stop index in the function's source.
    src_status = src.find("_maybe_install_status_line")
    src_stop = src.find("_maybe_reseat_stop_hook")
    assert 0 <= src_status < src_stop, (
        f"_maybe_install_status_line ({src_status}) should appear "
        f"before _maybe_reseat_stop_hook ({src_stop}) in main()"
    )
