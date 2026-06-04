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

"""AC.WDGUARD.2 — the SAME framework-source edit under CANONICAL loam
(a repo whose remote URL matches the canonical-loam upstream) is
ALLOWED. This is the no-false-positive guarantee: the guard must never
block legitimate framework dev.
"""

from __future__ import annotations

import pytest

from ._wd_guard_harness import (
    CANONICAL_ORIGIN,
    envelope,
    invoke,
    is_deny,
    make_repo,
    write_source,
)


@pytest.mark.parametrize(
    "origin",
    [
        "https://github.com/lukeivers/loam.git",
        "https://github.com/lukeivers/loam",  # no .git suffix
        "git@github.com:lukeivers/loam.git",  # SSH form
        "https://github.com/someotherfork/loam.git",  # fork-based canonical
    ],
)
def test_AC_WDGUARD_2_canonical_framework_source_allowed(tmp_path, origin):
    repo = make_repo(tmp_path / "canonical", origin_url=origin)
    target = write_source(
        repo, "framework/safety-layer/hooks/wd_discipline_guard.py"
    )
    env = envelope(cwd=str(repo), file_path=str(target))

    rc, out, _ = invoke(env)

    assert rc == 0
    assert not is_deny(out), (
        f"canonical-identity framework edit must NOT be blocked "
        f"(origin={origin!r}); stdout={out!r}"
    )


def test_AC_WDGUARD_2_canonical_via_non_origin_remote_allowed(tmp_path):
    """Canonical identity holds even when the canonical URL is on a
    NON-origin remote (e.g. a worktree that names it `upstream`)."""
    repo = make_repo(tmp_path / "canonical2", origin_url=None)
    # Add the canonical URL under a remote NOT named origin.
    import subprocess

    subprocess.run(
        ["git", "-C", str(repo), "remote", "add", "upstream", CANONICAL_ORIGIN],
        check=True,
        capture_output=True,
    )
    target = write_source(repo, "plugins/dev-sdlc/hooks/bash_guard.py")
    env = envelope(cwd=str(repo), file_path=str(target))

    rc, out, _ = invoke(env)

    assert rc == 0
    assert not is_deny(out), f"canonical via non-origin remote must allow: {out!r}"
