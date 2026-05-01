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

"""AC.OSS-M3.2 — `loam-cost` console-script registered.

Per plan `docs/rebuild/plans/oss-v0-1-0-publish-wire-clis.md` §4
AC.OSS-M3.2: `framework/cost-governance/pyproject.toml` registers
`loam-cost` as a `[project.scripts]` entry pointing at
`loam.cost_governance.cli:main`.
"""

from __future__ import annotations

import importlib.metadata


def test_AC_OSS_M3_2_loam_cost_registered_as_console_script() -> None:
    """The `loam-cost` console-script is registered and points at
    `loam.cost_governance.cli:main`."""
    eps = importlib.metadata.entry_points(group="console_scripts")
    matches = [ep for ep in eps if ep.name == "loam-cost"]
    assert len(matches) == 1, (
        f"expected exactly one `loam-cost` entry-point; got {matches!r}"
    )
    ep = matches[0]
    assert ep.value == "loam.cost_governance.cli:main", (
        f"expected `loam-cost` to point at "
        f"`loam.cost_governance.cli:main`; got {ep.value!r}"
    )
    target = ep.load()
    assert callable(target), f"loaded entry-point not callable: {target!r}"
