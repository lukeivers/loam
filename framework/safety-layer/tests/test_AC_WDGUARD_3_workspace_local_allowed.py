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

"""AC.WDGUARD.3 — workspace-local content is ALLOWED everywhere,
including inside a DERIVED workspace. These paths legitimately live in
the workspace; the guard must never block them.
"""

from __future__ import annotations

import pytest

from ._wd_guard_harness import (
    DERIVED_ORIGIN,
    envelope,
    invoke,
    is_deny,
    make_repo,
    write_source,
)


@pytest.mark.parametrize(
    "rel",
    [
        ".loam/memory/user-model/note.md",
        ".scratch/claude-output/report.md",
        ".claude/hooks/some_workspace_hook.py",
        "products/litrpg-writer/chapter.md",
        "workspace/data/thing.yaml",
        "docs/plans/some-plan.md",
        "CLAUDE.md",
        ".claude/settings.json",
    ],
)
def test_AC_WDGUARD_3_workspace_local_allowed_in_derived(tmp_path, rel):
    """Even inside a DERIVED (non-canonical) repo, workspace-local
    content writes are allowed."""
    repo = make_repo(tmp_path / "derived", origin_url=DERIVED_ORIGIN)
    target = write_source(repo, rel, body="local\n")
    env = envelope(cwd=str(repo), file_path=str(target))

    rc, out, _ = invoke(env)

    assert rc == 0
    assert not is_deny(out), (
        f"workspace-local path {rel!r} must be allowed in a derived "
        f"workspace; stdout={out!r}"
    )


def test_AC_WDGUARD_3_non_framework_top_level_allowed(tmp_path):
    """A top-level non-framework file (e.g. a README at workspace root)
    in a derived repo is not framework-source -> allowed."""
    repo = make_repo(tmp_path / "derived2", origin_url=DERIVED_ORIGIN)
    target = write_source(repo, "README.md", body="# readme\n")
    env = envelope(cwd=str(repo), file_path=str(target))

    rc, out, _ = invoke(env)

    assert rc == 0
    assert not is_deny(out)
