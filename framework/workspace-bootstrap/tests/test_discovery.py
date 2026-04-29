"""B2, B5 — discovery fail-closed behaviour."""

from __future__ import annotations

from pathlib import Path

import pytest

from loam.workspace_bootstrap import (
    ContributionNotFoundError,
    IPC_BOOTSTRAP_CONTRIBUTION_NOT_FOUND,
    load_manifest,
    resolve_ref,
)


def test_B2_missing_entrypoint_raises_32081(tmp_path: Path, write_manifest_fn) -> None:
    """Entry-point name not registered raises -32081."""
    path = write_manifest_fn(
        tmp_path / "bootstrap.yaml", ["does_not_exist_xyz"]
    )
    m = load_manifest(path)
    with pytest.raises(ContributionNotFoundError) as excinfo:
        resolve_ref(m.refs[0])
    assert excinfo.value.code == IPC_BOOTSTRAP_CONTRIBUTION_NOT_FOUND
    assert "does_not_exist_xyz" in excinfo.value.message


def test_B5_missing_path_file_raises_32081(tmp_path: Path, write_manifest_fn) -> None:
    """Path-form entry with missing file raises -32081."""
    path = write_manifest_fn(
        tmp_path / "bootstrap.yaml",
        [{"name": "x", "path": "./does_not_exist.py", "attr": "X"}],
    )
    m = load_manifest(path)
    with pytest.raises(ContributionNotFoundError) as excinfo:
        resolve_ref(m.refs[0])
    assert excinfo.value.code == IPC_BOOTSTRAP_CONTRIBUTION_NOT_FOUND


def test_B5_missing_attr_in_file_raises_32081(tmp_path: Path, write_manifest_fn) -> None:
    """Path-form entry where attr does not exist on module raises -32081."""
    adapter = tmp_path / "adapter.py"
    adapter.write_text("class Y: pass\n")
    path = write_manifest_fn(
        tmp_path / "bootstrap.yaml",
        [{"name": "x", "path": "./adapter.py", "attr": "NotThere"}],
    )
    m = load_manifest(path)
    with pytest.raises(ContributionNotFoundError) as excinfo:
        resolve_ref(m.refs[0])
    assert excinfo.value.code == IPC_BOOTSTRAP_CONTRIBUTION_NOT_FOUND


def test_module_form_missing_module_raises_32081(tmp_path: Path, write_manifest_fn) -> None:
    path = write_manifest_fn(
        tmp_path / "bootstrap.yaml",
        [{"name": "x", "module": "nothing.at_all_xyz", "attr": "X"}],
    )
    m = load_manifest(path)
    with pytest.raises(ContributionNotFoundError):
        resolve_ref(m.refs[0])


def test_entrypoint_loads_real_class(tmp_path: Path, write_manifest_fn) -> None:
    """The bundled observability_aggregator entry-point resolves."""
    path = write_manifest_fn(
        tmp_path / "bootstrap.yaml", ["observability_aggregator"]
    )
    m = load_manifest(path)
    cls = resolve_ref(m.refs[0])
    assert cls.__name__ == "ObservabilityAggregatorContribution"
