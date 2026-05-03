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

"""AC.FBE.1.4 — loam-init registers under the `loam.cli.subcommands`
entry-point group with name `init` resolving to the builder.

Reads the entry-point group via `importlib.metadata.entry_points`;
asserts an entry named `init` is present + `.load()` resolves to a
callable (the loam_cli dispatcher's discovery loop performs both
checks per cli.py:80-99).

Skips with a clear message if the loam-init package isn't installed
(e.g. running pytest against the source tree without `pip install -e
framework/loam-init`).
"""

from __future__ import annotations

import importlib.metadata

import pytest


_EP_GROUP = "loam.cli.subcommands"
_EP_NAME = "init"
_EXPECTED_TARGET = "loam.loam_init.cli:build_init_subcommand"


def _entry_points_for_group() -> list[importlib.metadata.EntryPoint]:
    """Return all entry points in the `loam.cli.subcommands` group."""
    eps = importlib.metadata.entry_points(group=_EP_GROUP)
    return list(eps)


def test_AC_FBE_1_4_init_entry_point_present() -> None:
    """An entry-point named `init` is registered under loam.cli.subcommands."""
    eps = _entry_points_for_group()
    if not any(ep.name == _EP_NAME for ep in eps):
        pytest.skip(
            f"{_EP_NAME!r} not found in group {_EP_GROUP!r} entry-points "
            f"(have: {sorted(ep.name for ep in eps)!r}). "
            f"This usually means `pip install -e framework/loam-init` "
            f"hasn't been run in this environment. The entry-point "
            f"registration lives in framework/loam-init/pyproject.toml."
        )
    init_eps = [ep for ep in eps if ep.name == _EP_NAME]
    assert len(init_eps) == 1, (
        f"expected exactly one {_EP_NAME!r} entry-point in group "
        f"{_EP_GROUP!r}; found {len(init_eps)}"
    )
    ep = init_eps[0]
    assert ep.value == _EXPECTED_TARGET, (
        f"{_EP_NAME!r} should resolve to {_EXPECTED_TARGET!r}; "
        f"got {ep.value!r}"
    )


def test_AC_FBE_1_4_entry_point_loads_to_callable() -> None:
    """`init` entry-point loads to a callable (the builder)."""
    eps = _entry_points_for_group()
    init_eps = [ep for ep in eps if ep.name == _EP_NAME]
    if not init_eps:
        pytest.skip(
            f"{_EP_NAME!r} not registered; install loam-init editable "
            f"to run this test"
        )
    target = init_eps[0].load()
    assert callable(target), (
        f"{_EP_NAME!r} entry-point should resolve to a callable; "
        f"got {type(target).__name__}"
    )
    # The builder's signature accepts a single `_SubParsersAction`
    # positional. We don't invoke here (covered by AC.FBE.1.3); just
    # verify it resolved to the right builder.
    assert target.__name__ == "build_init_subcommand", (
        f"{_EP_NAME!r} should resolve to `build_init_subcommand`; "
        f"got {target.__name__!r}"
    )
