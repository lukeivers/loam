"""AC.D.2.4 — HC#6 structural guard fires.

The ``WorkspaceLayout`` Pydantic model carries a model-level
validator refusing construction when the supplied ``workspace_root``
contains a path segment named ``framework``. This is the structural
enforcement of the HC#6 contract: workspace-state must not land
under ``framework/``.

Pre-D.2 this was convention (every reader chose its own path post-
hoc). Post-D.2 it's a Pydantic-validated structural guarantee.

Backing AC: AC.D.2.4 (HC#6 structural guard via WorkspaceLayout).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from workspace_bootstrap.workspace_paths import WorkspaceLayout


def test_d2_layout_refuses_framework_basename(tmp_path: Path) -> None:
    """A workspace_root whose basename is exactly ``framework`` is
    refused at construction time. This is the structural mis-
    construction HC#6 names: a workspace_root literally named
    ``framework`` would route workspace-state writes into the
    canonical-repo's framework subtree.
    """
    bad_root = tmp_path / "framework"
    bad_root.mkdir()

    with pytest.raises(ValidationError) as exc_info:
        WorkspaceLayout(workspace_root=bad_root)

    err = str(exc_info.value)
    assert "framework" in err
    assert "HC#6" in err or "AC.D.2.4" in err


def test_d2_layout_accepts_framework_segment_in_non_root_path(
    tmp_path: Path,
) -> None:
    """The validator refuses on basename match only. Legitimate paths
    under a release-archive simulation (e.g. self-upgrade's release
    directory ``pos-base/framework/releases/<tag>/``) use ``framework``
    as a non-root segment and must NOT trip the validator.

    The structural guarantee is that the workspace_root itself must
    not BE a framework subdirectory; what's above it is the operator's
    business.
    """
    nested = tmp_path / "deeper" / "framework" / "ws-named-not-framework"
    nested.mkdir(parents=True)

    layout = WorkspaceLayout(workspace_root=nested)
    assert layout.workspace_root == nested


def test_d2_layout_accepts_valid_workspace_root(tmp_path: Path) -> None:
    """Production workspace roots have names like ``pos3`` or
    ``ivers-corp-pos-v2`` — never ``framework``. The validator must
    not refuse them.
    """
    good_root = tmp_path / "ivers-corp-pos-v2"
    good_root.mkdir()

    layout = WorkspaceLayout(workspace_root=good_root)
    assert layout.workspace_root == good_root


def test_d2_layout_accepts_workspace_named_framework_substring(
    tmp_path: Path,
) -> None:
    """The validator matches on segment-equality, not substring. A
    workspace whose basename CONTAINS 'framework' as a substring (e.g.
    ``framework-test``) is permitted; only an exact ``framework``
    basename triggers refusal.
    """
    good_root = tmp_path / "framework-test-ws"
    good_root.mkdir()

    layout = WorkspaceLayout(workspace_root=good_root)
    assert layout.workspace_root == good_root


def test_d2_helpers_propagate_validation_error(tmp_path: Path) -> None:
    """Helper functions (``pos_subdir``, ``personas_dir``, etc.)
    construct a WorkspaceLayout per call, so they propagate the
    validator's refusal to call sites — defence depth at every
    workspace-state path computation.
    """
    bad_root = tmp_path / "framework"
    bad_root.mkdir()

    from workspace_bootstrap.workspace_paths import pos_subdir, personas_dir

    with pytest.raises(ValidationError):
        pos_subdir(bad_root)
    with pytest.raises(ValidationError):
        personas_dir(bad_root)
