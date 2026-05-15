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

"""AC.LIPW.2 — the persona prompt bound at first run contains ZERO
literal unsubstituted `{...}` template tokens. A fresh-init non-tech
user never sees a bound prompt with `{user_preferred_name}`-style
braces.

Plan: docs/plans/loam-init-persona-wiring-and-isolated-subloam-driver.md
Ladders to AC.PO.1.

Verification: read the bound persona prompt surface post-scaffold;
assert no `{persona_given_name}` / `{user_preferred_name}` / any
`{...}` template-token literal remains. The binding renders the
prompt through the EXISTING `_render_prompt_md` substitution path
with a brace-free placeholder identity.
"""

from __future__ import annotations

import re
from pathlib import Path

from loam.workspace_bootstrap.adapters.first_run_scaffold import (
    DEFAULT_PERSONA_HANDLE,
    run_first_run_scaffold,
)
from loam.workspace_bootstrap.new_workspace import (
    _scaffold_persona_binding,
)

LOAM_ROOT = Path(__file__).resolve().parents[3]

_TOKEN_RE = re.compile(r"\{[a-zA-Z_][a-zA-Z0-9_]*\}")


def _bound_agent_md(tmp_path: Path) -> str:
    workspace = tmp_path / "ws"
    workspace.mkdir()
    run_first_run_scaffold(
        pos_root=tmp_path / ".pos",
        platform_override="macos",
        service_bootstrap=False,
        service_manager_dir_override=tmp_path / "LaunchAgents",
        workspace_root=workspace,
        persona_handle=DEFAULT_PERSONA_HANDLE,
    )
    _scaffold_persona_binding(
        workspace_root=workspace,
        handle=DEFAULT_PERSONA_HANDLE,
        loam_root=LOAM_ROOT,
    )
    return (
        workspace / ".claude" / "agents" / f"{DEFAULT_PERSONA_HANDLE}.md"
    ).read_text()


def test_AC_LIPW_2_no_named_substitution_tokens_in_bound_prompt(
    tmp_path: Path,
) -> None:
    text = _bound_agent_md(tmp_path)
    assert "{user_preferred_name}" not in text
    assert "{persona_given_name}" not in text


def test_AC_LIPW_2_no_brace_template_token_literal_anywhere(
    tmp_path: Path,
) -> None:
    """No `{identifier}` template-token literal remains anywhere in
    the bound surface (defence against any future template token)."""
    text = _bound_agent_md(tmp_path)
    leftover = _TOKEN_RE.findall(text)
    assert leftover == [], (
        f"bound persona prompt carries unsubstituted token "
        f"literals: {leftover}"
    )
