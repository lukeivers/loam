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

"""AC.DSA.1 — DispatchShape carries an optional ``new_acs`` field.

When omitted or empty, the dispatcher does not author setup
artefacts. When non-empty, the dispatcher proceeds with setup per
AC.DSA.2 / AC.DSA.3 / AC.DSA.4. The field is keyword-only with a
default of ``()`` so structural compatibility with amendment #52 is
preserved (AC.DSA.10).
"""

from __future__ import annotations

import pytest

from loam.primary_persona import DispatchShape
from loam.primary_persona.dispatch_wrapper import NewACSpec


def test_AC_DSA_1_dispatch_shape_default_is_empty_new_acs() -> None:
    """A DispatchShape constructed without ``new_acs`` carries the
    empty-tuple default — the AC.DSA.10 backwards-compat invariant."""
    shape = DispatchShape(objective="research the foo")
    assert shape.new_acs == ()


def test_AC_DSA_1_dispatch_shape_accepts_explicit_new_acs() -> None:
    """A DispatchShape constructed with an explicit ``new_acs`` tuple
    carries the triples verbatim."""
    triples = (
        NewACSpec(
            component="primary-persona",
            ac_id="AC.X.1",
            source_path_glob="framework/primary-persona/src/foo.py",
        ),
        NewACSpec(
            component="primary-persona",
            ac_id="AC.X.2",
            source_path_glob="framework/primary-persona/src/bar.py",
        ),
    )
    shape = DispatchShape(objective="build X", new_acs=triples)
    assert shape.new_acs == triples
    # Field is keyword-only by virtue of being declared after
    # field-with-default ``agent_payload``; positional construction
    # would not interleave it. Sanity:
    assert isinstance(shape.new_acs[0], NewACSpec)
    assert shape.new_acs[0].component == "primary-persona"


def test_AC_DSA_1_NewACSpec_is_frozen() -> None:
    """``NewACSpec`` is a frozen dataclass so triples are hashable
    and tuple-of-NewACSpec is a valid frozen-dataclass field type."""
    spec = NewACSpec(
        component="c",
        ac_id="AC.X.1",
        source_path_glob="framework/c/src/y.py",
    )
    with pytest.raises(Exception):  # FrozenInstanceError or AttributeError
        spec.component = "other"  # type: ignore[misc]


def test_AC_DSA_1_dispatch_shape_is_still_frozen_with_new_acs() -> None:
    """The amendment-#74 field does not break ``DispatchShape``'s
    frozen-dataclass invariant."""
    shape = DispatchShape(objective="x")
    with pytest.raises(Exception):
        shape.new_acs = (NewACSpec("c", "AC.X.1", "framework/c/src/y.py"),)  # type: ignore[misc]
