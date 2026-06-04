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

"""AC.WDGUARD.5 — fail-open. Malformed / empty / non-content-tool /
path-with-no-git-repo input ALLOWS (exit 0, no deny). The hook can
never wedge the session.
"""

from __future__ import annotations

import json

from ._wd_guard_harness import (
    DERIVED_ORIGIN,
    envelope,
    invoke,
    is_deny,
    make_repo,
    write_source,
)


def test_AC_WDGUARD_5_empty_stdin():
    rc, out, _ = invoke("")
    assert rc == 0
    assert not is_deny(out)


def test_AC_WDGUARD_5_malformed_json():
    rc, out, _ = invoke("{not json")
    assert rc == 0
    assert not is_deny(out)


def test_AC_WDGUARD_5_non_content_tool(tmp_path):
    repo = make_repo(tmp_path / "derived", origin_url=DERIVED_ORIGIN)
    target = write_source(repo, "framework/safety-layer/hooks/foo.py")
    # Bash tool — not Edit/Write/MultiEdit -> not our concern.
    env = json.dumps(
        {
            "cwd": str(repo),
            "tool_name": "Bash",
            "tool_input": {"command": f"echo x > {target}"},
        }
    )
    rc, out, _ = invoke(env)
    assert rc == 0
    assert not is_deny(out)


def test_AC_WDGUARD_5_missing_file_path(tmp_path):
    repo = make_repo(tmp_path / "derived", origin_url=DERIVED_ORIGIN)
    env = json.dumps(
        {"cwd": str(repo), "tool_name": "Write", "tool_input": {}}
    )
    rc, out, _ = invoke(env)
    assert rc == 0
    assert not is_deny(out)


def test_AC_WDGUARD_5_path_outside_any_git_repo(tmp_path):
    """A framework-looking path that is NOT inside any git repo cannot
    be a governed framework tree -> allow."""
    # tmp_path itself is not a git repo.
    nongit = tmp_path / "loose"
    target = nongit / "framework" / "safety-layer" / "hooks" / "foo.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("x\n", encoding="utf-8")
    env = envelope(cwd=str(nongit), file_path=str(target))
    rc, out, _ = invoke(env)
    assert rc == 0
    assert not is_deny(out)
