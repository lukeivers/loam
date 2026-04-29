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
