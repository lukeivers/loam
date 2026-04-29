"""AC.E.5 — Downstream value-prop loader still reads
docs/rebuild/VALUE_PROPOSITION.md on dev workspaces.

Sub-plan E (two-modes-and-multi-workspace, amendment #42) decouples
the classification source-of-truth from the content source. The
classifier now reads dev_intent; the ``load_value_prop_source``
function — which decides which file to read for the value-prop
content — is unchanged in shape. On a workspace classified as
``"pos-v2-dev"``, ``load_value_prop_source`` reads
``docs/rebuild/VALUE_PROPOSITION.md``. On a workspace classified as
``"user"``, it reads ``<workspace>/value-prop.md``.

This test asserts the loader's behaviour is preserved across the
amendment.

Plan: docs/rebuild/plans/two-modes-and-multi-workspace/E-classify-workspace-replacement.md
"""

from __future__ import annotations

from pathlib import Path

from loam.workspace_bootstrap.adapters.tracker_seed import (
    CLASSIFICATION_LOAM_DEV,
    CLASSIFICATION_USER,
    FRAMEWORK_VALUE_PROP_RELPATH,
    WORKSPACE_VALUE_PROP_RELPATH,
    load_value_prop_source,
)


def test_AC_E_5_loader_reads_framework_path_on_dev_classification(
    tmp_path: Path,
) -> None:
    """When the classification is ``"pos-v2-dev"``, the loader reads
    ``docs/rebuild/VALUE_PROPOSITION.md`` (the framework path)."""
    workspace = tmp_path / "ws-dev"
    workspace.mkdir()
    framework_path = workspace / FRAMEWORK_VALUE_PROP_RELPATH
    framework_path.parent.mkdir(parents=True, exist_ok=True)
    framework_path.write_text("# Framework VP\n\nbody\n")

    src = load_value_prop_source(
        workspace_root=workspace,
        classification=CLASSIFICATION_LOAM_DEV,
    )
    assert src.available is True
    assert src.source_doc == FRAMEWORK_VALUE_PROP_RELPATH
    assert "Framework VP" in src.source_text


def test_AC_E_5_loader_reads_workspace_path_on_user_classification(
    tmp_path: Path,
) -> None:
    """When the classification is ``"user"``, the loader reads
    ``<workspace>/value-prop.md`` (the workspace-supplied path)."""
    workspace = tmp_path / "ws-user"
    workspace.mkdir()
    user_path = workspace / WORKSPACE_VALUE_PROP_RELPATH
    user_path.write_text("# Workspace VP\n\nbody\n")

    src = load_value_prop_source(
        workspace_root=workspace,
        classification=CLASSIFICATION_USER,
    )
    assert src.available is True
    assert src.source_doc == WORKSPACE_VALUE_PROP_RELPATH
    assert "Workspace VP" in src.source_text


def test_AC_E_5_loader_reports_unavailable_on_user_classification_without_file(
    tmp_path: Path,
) -> None:
    """Non-dev workspace without a ``value-prop.md`` file: the loader
    returns ``available=False`` (skip-with-diagnostic shape preserved
    from amendment #39)."""
    workspace = tmp_path / "ws-user-empty"
    workspace.mkdir()

    src = load_value_prop_source(
        workspace_root=workspace,
        classification=CLASSIFICATION_USER,
    )
    assert src.available is False
    assert src.source_doc == WORKSPACE_VALUE_PROP_RELPATH
