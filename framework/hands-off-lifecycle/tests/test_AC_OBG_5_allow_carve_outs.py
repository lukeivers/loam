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

"""AC.OBG.5 — Allow Edit on dev-discipline carve-out paths regardless
of sentinel state.

Per the locked plan-doc §4 AC.OBG.5: given ``tool_input.file_path``
is under any of: ``docs/``, ``tools/``, ``.scratch/``, ``personas/``,
OR matches ``CLAUDE*.md`` at workspace root, OR matches
``.gitignore`` at workspace root, OR matches ``framework/docs/``,
``framework/tools/`` (post-D-migration framework-rooted analogues),
OR is one of the universal-paths admissions
(``docs/odd-methodology.md``, ``docs/odd-in-loam.md``,
``docs/rebuild/FUTURE_IDEAS.md``, ``docs/rebuild/FUTURE_IDEAS_DRAFT.md``):
hook allows regardless of sentinel/manifest state and regardless of
mode.
"""

from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
HOOKS_DIR = REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks"
# Post-M6b.0: gate-hook source files MOVED to plugins/dev-sdlc/hooks/.
# Add plugin's hooks dir to sys.path so the test imports resolve to
# the moved gate modules. _gate_helpers.py STAYS at canonical
# (HOOKS_DIR above) and remains importable.
PLUGIN_HOOKS_DIR = REPO_ROOT / "plugins" / "dev-sdlc" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))
if PLUGIN_HOOKS_DIR.exists():
    sys.path.insert(0, str(PLUGIN_HOOKS_DIR))


@pytest.fixture
def gate_dev_mode_no_sentinel(monkeypatch):
    """Configure DEV MODE with NO sentinel — the carve-out path admits
    regardless of this state (the harshest case)."""
    cls_mod = types.ModuleType("corpus_load_sentinel")
    cls_mod.workspace_mode = lambda _: "dev-mode"
    monkeypatch.setitem(sys.modules, "corpus_load_sentinel", cls_mod)

    ass_mod = types.ModuleType("active_scope_sentinel")
    ass_mod.read_active_scope_sentinel = lambda _: None
    monkeypatch.setitem(sys.modules, "active_scope_sentinel", ass_mod)


@pytest.mark.parametrize(
    "rel_path",
    [
        "docs/rebuild/plans/x.md",
        "docs/odd-methodology.md",
        "docs/odd-in-loam.md",
        "docs/rebuild/FUTURE_IDEAS.md",
        "docs/rebuild/FUTURE_IDEAS_DRAFT.md",
        "tools/some-script.sh",
        ".scratch/notes.txt",
        "personas/primary.yaml",
        "framework/docs/internal.md",
        "framework/tools/t.sh",
        "CLAUDE.md",
        "CLAUDE.dev.md",
        "framework/CLAUDE.md",
        ".gitignore",
        "framework/.gitignore",
    ],
)
def test_AC_OBG_5_carve_out_path_allows(
    tmp_path, gate_dev_mode_no_sentinel, rel_path: str
) -> None:
    """Each carve-out path admits even without a sentinel in DEV MODE."""
    import objective_binding_gate as gate

    full = tmp_path / rel_path
    full.parent.mkdir(parents=True, exist_ok=True)
    full.touch()
    decision = gate.evaluate(
        workspace_root=tmp_path,
        tool_name="Edit",
        tool_input={"file_path": str(full)},
    )
    assert decision.decision == "allow", (
        f"carve-out path {rel_path} unexpectedly denied: "
        f"{decision.reason}"
    )


def test_AC_OBG_5_non_carve_out_in_same_branch_denies(
    tmp_path, gate_dev_mode_no_sentinel
) -> None:
    """Confirmation: a non-carve-out path under the same DEV MODE +
    no-sentinel state DOES still deny (the carve-out gate is the only
    thing admitting the carve-out paths above; the deny otherwise
    applies)."""
    import objective_binding_gate as gate

    bad = tmp_path / "framework" / "orchestrator" / "src" / "x.py"
    bad.parent.mkdir(parents=True, exist_ok=True)
    bad.touch()
    decision = gate.evaluate(
        workspace_root=tmp_path,
        tool_name="Edit",
        tool_input={"file_path": str(bad)},
    )
    assert decision.decision == "deny"
    assert decision.failure_class == "missing-sentinel"
