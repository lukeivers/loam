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

"""AC.WDGUARD.1 — a framework-source edit inside a DERIVED workspace
(a git repo that is NOT canonical loam) is BLOCKED with a reason that
names the WD-discipline rule + redirects to canonical loam.
"""

from __future__ import annotations

import pytest

from ._wd_guard_harness import (
    DERIVED_ORIGIN,
    deny_reason,
    envelope,
    invoke,
    is_deny,
    make_repo,
    write_source,
)


@pytest.mark.parametrize(
    "rel",
    [
        "framework/safety-layer/hooks/wd_discipline_guard.py",
        "framework/primary-persona/src/loam/primary_persona/introduction.py",
        "plugins/dev-sdlc/tools/loam-amend/src/loam_amend/commands/apply.py",
    ],
)
def test_AC_WDGUARD_1_derived_framework_source_blocked(tmp_path, rel):
    repo = make_repo(tmp_path / "derived", origin_url=DERIVED_ORIGIN)
    target = write_source(repo, rel)
    env = envelope(cwd=str(repo), file_path=str(target))

    rc, out, err = invoke(env)

    assert rc == 0  # never wedge — the block is via stdout JSON
    assert is_deny(out), f"expected deny, got stdout={out!r}"
    reason = deny_reason(out)
    assert "AC.WDGUARD.1" in reason
    assert "/Users/lukeivers/loam" in reason  # redirect to canonical
    assert "DERIVED" in reason


def test_AC_WDGUARD_1_derived_with_empty_origin_blocked(tmp_path):
    """The real vendored copy has NO origin at all — still blocked."""
    repo = make_repo(tmp_path / "vendored", origin_url=None)
    target = write_source(repo, "framework/safety-layer/hooks/foo.py")
    env = envelope(cwd=str(repo), file_path=str(target))

    rc, out, _ = invoke(env)

    assert rc == 0
    assert is_deny(out), f"empty-origin derived copy must block: {out!r}"
