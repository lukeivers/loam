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

"""B3, B24 — metadata validation structural defences."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from loam.workspace_bootstrap import (
    Bootstrapper,
    ContributionMetadata,
    IPC_BOOTSTRAP_METADATA_INVALID,
    MetadataInvalidError,
    Phase,
    load_manifest,
)


# B24 structural defences on ContributionMetadata itself.


def test_B24_empty_name_refused() -> None:
    with pytest.raises(ValidationError):
        ContributionMetadata(name="", phase=Phase.before_orchestrator_start)


def test_B24_phase_outside_enum_refused() -> None:
    with pytest.raises(ValidationError):
        ContributionMetadata(name="x", phase="not_a_phase")  # type: ignore[arg-type]


def test_B24_extra_fields_forbidden() -> None:
    with pytest.raises(ValidationError):
        ContributionMetadata(
            name="x",
            phase=Phase.before_orchestrator_start,
            unexpected_field="bad",  # type: ignore[call-arg]
        )


def test_B24_model_is_frozen() -> None:
    md = ContributionMetadata(name="x", phase=Phase.before_orchestrator_start)
    with pytest.raises(ValidationError):
        md.name = "y"  # type: ignore[misc]


def test_B24_after_accepts_list_coerces_to_tuple() -> None:
    md = ContributionMetadata(
        name="x",
        phase=Phase.before_orchestrator_start,
        after=["a", "b"],  # type: ignore[arg-type]
    )
    assert md.after == ("a", "b")


def test_B24_after_must_be_sequence() -> None:
    with pytest.raises(ValidationError):
        ContributionMetadata(
            name="x",
            phase=Phase.before_orchestrator_start,
            after="a",  # type: ignore[arg-type]
        )


# B3 — metadata validation at discovery.


def test_B3_no_metadata_raises_32082(tmp_path: Path, write_manifest_fn) -> None:
    adapter = tmp_path / "adapter.py"
    adapter.write_text("class X: pass\n")
    path = write_manifest_fn(
        tmp_path / "bootstrap.yaml",
        [{"name": "x", "path": "./adapter.py", "attr": "X"}],
    )
    with pytest.raises(MetadataInvalidError) as excinfo:
        bs = Bootstrapper(load_manifest(path))
        bs.resolve_and_order()
    assert excinfo.value.code == IPC_BOOTSTRAP_METADATA_INVALID


def test_B3_bad_metadata_raises_32082(tmp_path: Path, write_manifest_fn) -> None:
    """A class whose metadata dict fails validation raises -32082."""
    adapter = tmp_path / "adapter.py"
    adapter.write_text(
        "class X:\n"
        "    metadata = {'name': '', 'phase': 'before_orchestrator_start'}\n"
    )
    path = write_manifest_fn(
        tmp_path / "bootstrap.yaml",
        [{"name": "x", "path": "./adapter.py", "attr": "X"}],
    )
    with pytest.raises(MetadataInvalidError) as excinfo:
        bs = Bootstrapper(load_manifest(path))
        bs.resolve_and_order()
    assert excinfo.value.code == IPC_BOOTSTRAP_METADATA_INVALID
