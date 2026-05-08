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

"""AC.OSS-M3.4 — `loam-reversibility` + `loam-rollback` registered.

Per plan `docs/plans/oss-v0-1-0-publish-wire-clis.md` §4
AC.OSS-M3.4: `framework/reversibility-primitive/pyproject.toml`
registers TWO `[project.scripts]` entries:

    loam-reversibility = "loam.reversibility_primitive.cli:main_reversibility"
    loam-rollback      = "loam.reversibility_primitive.cli:main_rollback"

Both targets are NEW public functions added to
`loam.reversibility_primitive.cli` per plan §10 D-build.M3.1 (the
existing `main(call, argv)` is preserved untouched; the two shim
functions wrap it for zero-arg console-script compatibility).
"""

from __future__ import annotations

import importlib.metadata


def test_AC_OSS_M3_4a_loam_reversibility_registered_as_console_script() -> None:
    """The `loam-reversibility` console-script is registered and
    points at `loam.reversibility_primitive.cli:main_reversibility`."""
    eps = importlib.metadata.entry_points(group="console_scripts")
    matches = [ep for ep in eps if ep.name == "loam-reversibility"]
    assert len(matches) == 1, (
        f"expected exactly one `loam-reversibility` entry-point; got {matches!r}"
    )
    ep = matches[0]
    assert (
        ep.value == "loam.reversibility_primitive.cli:main_reversibility"
    ), (
        f"expected `loam-reversibility` to point at "
        f"`loam.reversibility_primitive.cli:main_reversibility`; got {ep.value!r}"
    )
    target = ep.load()
    assert callable(target), f"loaded entry-point not callable: {target!r}"


def test_AC_OSS_M3_4b_loam_rollback_registered_as_console_script() -> None:
    """The `loam-rollback` console-script is registered and points
    at `loam.reversibility_primitive.cli:main_rollback`."""
    eps = importlib.metadata.entry_points(group="console_scripts")
    matches = [ep for ep in eps if ep.name == "loam-rollback"]
    assert len(matches) == 1, (
        f"expected exactly one `loam-rollback` entry-point; got {matches!r}"
    )
    ep = matches[0]
    assert (
        ep.value == "loam.reversibility_primitive.cli:main_rollback"
    ), (
        f"expected `loam-rollback` to point at "
        f"`loam.reversibility_primitive.cli:main_rollback`; got {ep.value!r}"
    )
    target = ep.load()
    assert callable(target), f"loaded entry-point not callable: {target!r}"
