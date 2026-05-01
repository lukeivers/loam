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

"""AC.OSS-M3.1 — `loam-kill` console-script registered.

Per plan `docs/rebuild/plans/oss-v0-1-0-publish-wire-clis.md` §4
AC.OSS-M3.1: `framework/safety-layer/pyproject.toml` registers
`loam-kill` as a `[project.scripts]` entry pointing at
`loam.safety_layer.cli:main`.

The assertion reads `importlib.metadata.entry_points(group="console_scripts")`
which is the source-of-truth for installed entry-point metadata.
The registration is the AC; behaviour is out of scope (test scope
narrow per dispatch constraint).
"""

from __future__ import annotations

import importlib.metadata


def test_AC_OSS_M3_1_loam_kill_registered_as_console_script() -> None:
    """The `loam-kill` console-script is registered and points at
    `loam.safety_layer.cli:main`."""
    eps = importlib.metadata.entry_points(group="console_scripts")
    matches = [ep for ep in eps if ep.name == "loam-kill"]
    assert len(matches) == 1, (
        f"expected exactly one `loam-kill` entry-point; got {matches!r}"
    )
    ep = matches[0]
    assert ep.value == "loam.safety_layer.cli:main", (
        f"expected `loam-kill` to point at "
        f"`loam.safety_layer.cli:main`; got {ep.value!r}"
    )
    # Resolve callable to verify the target exists + is callable.
    target = ep.load()
    assert callable(target), f"loaded entry-point not callable: {target!r}"
