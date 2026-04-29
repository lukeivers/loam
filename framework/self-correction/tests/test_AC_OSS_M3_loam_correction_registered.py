"""AC.OSS-M3.3 — `loam-correction` console-script registered.

Per plan `docs/rebuild/plans/oss-v0-1-0-publish-wire-clis.md` §4
AC.OSS-M3.3: `framework/self-correction/pyproject.toml` registers
`loam-correction` as a `[project.scripts]` entry pointing at
`loam.self_correction.cli:main`.
"""

from __future__ import annotations

import importlib.metadata


def test_AC_OSS_M3_3_loam_correction_registered_as_console_script() -> None:
    """The `loam-correction` console-script is registered and points
    at `loam.self_correction.cli:main`."""
    eps = importlib.metadata.entry_points(group="console_scripts")
    matches = [ep for ep in eps if ep.name == "loam-correction"]
    assert len(matches) == 1, (
        f"expected exactly one `loam-correction` entry-point; got {matches!r}"
    )
    ep = matches[0]
    assert ep.value == "loam.self_correction.cli:main", (
        f"expected `loam-correction` to point at "
        f"`loam.self_correction.cli:main`; got {ep.value!r}"
    )
    target = ep.load()
    assert callable(target), f"loaded entry-point not callable: {target!r}"
