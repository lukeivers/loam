r"""AC.V025-C6.2 — `resolve_pm_handle` error message references actionable
guidance, not the nonexistent `loam project init` subcommand.

Per v0.2.5 corrective C6 (HARD-smoke F-DESIGN-2): the pre-C6 error
message said `Run \`loam project init\` to author one`, but
`loam project` is NOT registered as a subcommand on the unified
loam CLI (only `odd-extract`, `init`, `amend`, `onboard`, `pr-safety`
are registered). That guidance sent users chasing a phantom command.

Post-C6 the message points at:

  - the workspace-relative path where a PM contract.yaml is expected
    (`<workspace>/workspace/.loam/pms/<handle>/contract.yaml`), and
  - the `--pm-handle` CLI flag as the explicit-disambiguation path,

both of which are paths a user can act on without invoking a CLI
surface that does not exist.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from loam_odd_extractor.errors import OddExtractorError
from loam_odd_extractor.interview import resolve_pm_handle


def test_AC_V025_C6_2_no_pm_message_omits_loam_project_init(
    tmp_path: Path,
) -> None:
    """The error raised on the no-PM path MUST NOT reference
    `loam project init`."""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    (workspace / "workspace").mkdir()
    # No PM authored.

    with pytest.raises(OddExtractorError) as exc_info:
        resolve_pm_handle(workspace, explicit_handle=None)

    msg = str(exc_info.value)
    assert "loam project init" not in msg, (
        f"error message must NOT reference the nonexistent "
        f"`loam project init` subcommand (v0.2.5 corrective C6 "
        f"F-DESIGN-2 fix); got: {msg!r}"
    )


def test_AC_V025_C6_2_no_pm_message_references_workspace_path(
    tmp_path: Path,
) -> None:
    """The error message MUST name the workspace-relative path where a
    PM contract.yaml is expected (so the user knows where to author
    one)."""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    (workspace / "workspace").mkdir()

    with pytest.raises(OddExtractorError) as exc_info:
        resolve_pm_handle(workspace, explicit_handle=None)

    msg = str(exc_info.value)
    assert "workspace/.loam/pms" in msg, (
        f"error message must name the workspace-relative path where "
        f"a PM is expected; got: {msg!r}"
    )
    assert "contract.yaml" in msg, (
        f"error message must mention the contract.yaml file required "
        f"to author a PM; got: {msg!r}"
    )


def test_AC_V025_C6_2_no_pm_message_references_pm_handle_flag(
    tmp_path: Path,
) -> None:
    """The error message MUST mention the `--pm-handle` flag as the
    explicit-disambiguation path."""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    (workspace / "workspace").mkdir()

    with pytest.raises(OddExtractorError) as exc_info:
        resolve_pm_handle(workspace, explicit_handle=None)

    msg = str(exc_info.value)
    assert "--pm-handle" in msg, (
        f"error message must reference the `--pm-handle` CLI flag as "
        f"the explicit-disambiguation path; got: {msg!r}"
    )
