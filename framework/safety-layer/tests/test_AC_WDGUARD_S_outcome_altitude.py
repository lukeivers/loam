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

"""AC.WDGUARD.S — OUTCOME-ALTITUDE per
`feedback_test_outcome_altitude_required.md`.

Drives the PRODUCTION hook script as a real subprocess (no fakes, no
module-level patches, no pre-arranged internal state) against TWO real
throwaway git repos — one with a canonical-loam origin, one with a
non-canonical (derived) origin — and asserts the production deny/allow
shape on stdout for the four load-bearing cases:

  (a) derived  x framework-source        -> BLOCK
  (b) canonical x framework-source       -> ALLOW
  (c) derived  x workspace-local         -> ALLOW
  (d) derived  x framework-source + env-override -> ALLOW

This is the cross-cutting confidence-builder for the whole guard,
exercising the real git-identity probe end to end.
"""

from __future__ import annotations

from ._wd_guard_harness import (
    CANONICAL_ORIGIN,
    DERIVED_ORIGIN,
    envelope,
    invoke,
    is_deny,
    make_repo,
    write_source,
)


def test_AC_WDGUARD_S_outcome_altitude_four_cases(tmp_path):
    canonical = make_repo(tmp_path / "canonical", origin_url=CANONICAL_ORIGIN)
    derived = make_repo(tmp_path / "derived", origin_url=DERIVED_ORIGIN)

    fw_rel = "framework/safety-layer/hooks/wd_discipline_guard.py"
    ws_rel = ".loam/memory/user-model/note.md"

    # (a) derived x framework-source -> BLOCK
    a_target = write_source(derived, fw_rel)
    rc_a, out_a, _ = invoke(
        envelope(cwd=str(derived), file_path=str(a_target))
    )
    assert rc_a == 0
    assert is_deny(out_a), f"(a) derived framework-source must BLOCK: {out_a!r}"

    # (b) canonical x framework-source -> ALLOW
    b_target = write_source(canonical, fw_rel)
    rc_b, out_b, _ = invoke(
        envelope(cwd=str(canonical), file_path=str(b_target))
    )
    assert rc_b == 0
    assert not is_deny(out_b), (
        f"(b) canonical framework-source must ALLOW: {out_b!r}"
    )

    # (c) derived x workspace-local -> ALLOW
    c_target = write_source(derived, ws_rel, body="local\n")
    rc_c, out_c, _ = invoke(
        envelope(cwd=str(derived), file_path=str(c_target))
    )
    assert rc_c == 0
    assert not is_deny(out_c), (
        f"(c) derived workspace-local must ALLOW: {out_c!r}"
    )

    # (d) derived x framework-source + override -> ALLOW
    rc_d, out_d, _ = invoke(
        envelope(cwd=str(derived), file_path=str(a_target)),
        extra_env={"LOAM_WD_GUARD": "off"},
    )
    assert rc_d == 0
    assert not is_deny(out_d), (
        f"(d) override must ALLOW the derived framework-source edit: {out_d!r}"
    )
