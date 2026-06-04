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

"""AC.WDGUARD.4 — the override hatch makes the guard no-op even for the
derived x framework-source cell, and the bypass is logged.

Three override forms:
  * env LOAM_WD_GUARD=off
  * env LOAM_SAFETY_HOOKS=off (all safety hooks)
  * <repo>/.loam/.wd-guard-override sentinel file
"""

from __future__ import annotations

from ._wd_guard_harness import (
    DERIVED_ORIGIN,
    envelope,
    invoke,
    is_deny,
    make_repo,
    write_source,
)


def _derived_framework_envelope(tmp_path):
    repo = make_repo(tmp_path / "derived", origin_url=DERIVED_ORIGIN)
    target = write_source(repo, "framework/safety-layer/hooks/foo.py")
    return repo, envelope(cwd=str(repo), file_path=str(target))


def test_AC_WDGUARD_4_env_this_guard_off(tmp_path):
    repo, env = _derived_framework_envelope(tmp_path)
    rc, out, _ = invoke(env, extra_env={"LOAM_WD_GUARD": "off"})
    assert rc == 0
    assert not is_deny(out), "LOAM_WD_GUARD=off must no-op the block"
    log = repo / ".loam" / "safety-hooks.log"
    assert log.exists() and "toggled-off" in log.read_text()


def test_AC_WDGUARD_4_env_all_safety_off(tmp_path):
    repo, env = _derived_framework_envelope(tmp_path)
    rc, out, _ = invoke(env, extra_env={"LOAM_SAFETY_HOOKS": "off"})
    assert rc == 0
    assert not is_deny(out), "LOAM_SAFETY_HOOKS=off must no-op the block"


def test_AC_WDGUARD_4_sentinel_file(tmp_path):
    repo, env = _derived_framework_envelope(tmp_path)
    sentinel = repo / ".loam" / ".wd-guard-override"
    sentinel.parent.mkdir(parents=True, exist_ok=True)
    sentinel.write_text("", encoding="utf-8")

    rc, out, _ = invoke(env)

    assert rc == 0
    assert not is_deny(out), "override sentinel must no-op the block"
    log = repo / ".loam" / "safety-hooks.log"
    assert log.exists() and "override-sentinel" in log.read_text()


def test_AC_WDGUARD_4_without_override_still_blocks(tmp_path):
    """Control: with NO override, the same envelope blocks (so the
    override tests are proving the override, not a dead block)."""
    _repo, env = _derived_framework_envelope(tmp_path)
    rc, out, _ = invoke(env)
    assert rc == 0
    assert is_deny(out), "without override the derived edit must block"
