"""B1, B5 — manifest loader fail-closed behaviour."""

from __future__ import annotations

from pathlib import Path

import pytest

from workspace_bootstrap import (
    IPC_BOOTSTRAP_MISSING_CONFIG,
    MissingConfigError,
    load_manifest,
)


def test_B1_missing_manifest_raises_32080(tmp_path: Path) -> None:
    """A missing manifest file raises -32080 naming the path."""
    missing = tmp_path / "bootstrap.yaml"
    with pytest.raises(MissingConfigError) as excinfo:
        load_manifest(missing)
    assert excinfo.value.code == IPC_BOOTSTRAP_MISSING_CONFIG
    assert str(missing) in excinfo.value.message


def test_B1_malformed_yaml_raises_32080(tmp_path: Path, write_manifest_fn) -> None:
    """Malformed YAML raises -32080 with parse error in diagnostic."""
    bad = tmp_path / "bootstrap.yaml"
    bad.write_text("version: 1\n  contributions: - [broken")
    with pytest.raises(MissingConfigError) as excinfo:
        load_manifest(bad)
    assert excinfo.value.code == IPC_BOOTSTRAP_MISSING_CONFIG


def test_B1_missing_version_raises_32080(tmp_path: Path) -> None:
    """Missing `version: 1` raises -32080."""
    p = tmp_path / "bootstrap.yaml"
    p.write_text("contributions: []\n")
    with pytest.raises(MissingConfigError):
        load_manifest(p)


def test_B1_missing_contributions_raises_32080(tmp_path: Path) -> None:
    """Missing `contributions` list raises -32080."""
    p = tmp_path / "bootstrap.yaml"
    p.write_text("version: 1\n")
    with pytest.raises(MissingConfigError):
        load_manifest(p)


def test_B5_path_form_missing_attr_raises_32080(tmp_path: Path, write_manifest_fn) -> None:
    """Path-form entry without `attr` raises -32080."""
    write_manifest_fn(
        tmp_path / "bootstrap.yaml",
        [{"name": "x", "path": "./x.py"}],
    )
    with pytest.raises(MissingConfigError):
        load_manifest(tmp_path / "bootstrap.yaml")


def test_accepts_bare_string_entries(tmp_path: Path, write_manifest_fn) -> None:
    """Bare string entries are treated as entry-point names."""
    path = write_manifest_fn(
        tmp_path / "bootstrap.yaml", ["observability_aggregator"]
    )
    m = load_manifest(path)
    assert len(m.refs) == 1
    assert m.refs[0].kind == "entrypoint"
    assert m.refs[0].entrypoint_name == "observability_aggregator"


def test_accepts_path_form_entries(tmp_path: Path, write_manifest_fn) -> None:
    adapter_file = tmp_path / "adapter.py"
    adapter_file.write_text("class X: pass\n")
    path = write_manifest_fn(
        tmp_path / "bootstrap.yaml",
        [{"name": "local", "path": "./adapter.py", "attr": "X"}],
    )
    m = load_manifest(path)
    assert len(m.refs) == 1
    assert m.refs[0].kind == "path"
    assert m.refs[0].path_attr == "X"


def test_accepts_module_form_entries(tmp_path: Path, write_manifest_fn) -> None:
    path = write_manifest_fn(
        tmp_path / "bootstrap.yaml",
        [{"name": "mod", "module": "my.mod", "attr": "X"}],
    )
    m = load_manifest(path)
    assert m.refs[0].kind == "module"
    assert m.refs[0].module == "my.mod"
    assert m.refs[0].module_attr == "X"
