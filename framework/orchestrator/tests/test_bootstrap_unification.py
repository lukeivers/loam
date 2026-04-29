"""Amendment #7 — orchestrator-bootstrap-unification.

Each test is the 1:1 acceptance-criterion complement of the
corresponding AC in
``docs/rebuild/components/orchestrator-bootstrap-unification/proposal.md``.

Covered here (orchestrator-owned behaviours):
  * AC2 — a missing ``bootstrap.py`` is not a fail-closed condition
    anymore (exit 0, no ``bootstrap_refused`` event). AC2's poison-bomb
    fixture also structurally covers the intent of withdrawn-AC1
    (orchestrator no longer self-loads ``bootstrap.py``): the fixture
    writes a ``raise RuntimeError(...)`` into the workspace
    ``bootstrap.py`` and asserts clean exit, which cannot hold if the
    orchestrator still imports the workspace file.
  * AC7 — the ``--no-bootstrap`` flag is gone from argparse.
  * AC8 — ``run_first_run_scaffold`` does not write ``bootstrap.py``.

AC1 was withdrawn by amendment #12 (2026-04-22) because it was a
method-in-acceptance static-grep, which ODD §2.5 / §8.2 rule 9 forbid.
See the proposal's §3 AC1 stub for the audit rationale.

AC3/AC4/AC5/AC6 live in ``workspace-bootstrap/tests/`` because they
exercise framework-side behaviour; AC9 (diff-scope) lives in
``test_no_sealed_amendments.py``.
"""

from __future__ import annotations

import asyncio
import subprocess
import sys
from pathlib import Path

import pytest

from loam.orchestrator import Orchestrator
from loam.orchestrator.config import OrchestratorConfig

from .conftest import _short_socket_path


@pytest.mark.asyncio
async def test_AC2_missing_bootstrap_py_is_not_a_fail_closed_condition(
    tmp_path: Path,
) -> None:
    """With no ``bootstrap.py`` on disk and no framework-adapter
    layered on top, the orchestrator starts and stops cleanly.

    Post-amendment, the orchestrator's own startup no longer has a
    fail-closed branch tied to a workspace Python file. A bootstrap.py
    that would raise on import must be irrelevant to the orchestrator's
    exit code.
    """
    root = tmp_path / "pos-empty"
    root.mkdir(parents=True, exist_ok=True)
    # Write a poison-bomb bootstrap.py to prove it is NEVER read by
    # Orchestrator._startup. (The framework-adapter path is a separate
    # test in workspace-bootstrap.)
    (root / "bootstrap.py").write_text(
        'raise RuntimeError("amendment #7: orchestrator must not import this")\n'
    )
    cfg = OrchestratorConfig(
        root_dir=root,
        socket_path=_short_socket_path(),
        heartbeat_interval_seconds=0.05,
        sigterm_grace_seconds=1.0,
    )
    orch = Orchestrator(cfg)

    async def _stop_soon() -> None:
        await asyncio.sleep(0.08)
        orch.request_stop()

    stopper = asyncio.create_task(_stop_soon())
    exit_code = await asyncio.wait_for(orch.run(), timeout=2.0)
    await stopper

    assert exit_code == 0, (
        f"expected clean shutdown (0), got {exit_code}; amendment #7 "
        "removed the bootstrap fail-closed branch."
    )
    # No ``bootstrap_refused`` event should exist in local state.
    assert not orch.local_state.events_of_type("bootstrap_refused"), (
        "bootstrap_refused event emitted despite amendment #7 removing "
        "the emitter. Check Orchestrator.run() exception handlers."
    )


def test_AC7_no_bootstrap_flag_is_removed() -> None:
    """``python -m loam.orchestrator --no-bootstrap`` must exit with
    argparse's unknown-option error code (2), and ``--help`` output
    must not mention the flag.

    Per owner ruling on flagged inference #1 in the proposal: the flag
    has no remaining job once ``required: False`` is the adapter
    default, so it is removed rather than silenced.
    """
    # Reject unknown flag (argparse exits with code 2).
    proc = subprocess.run(
        [sys.executable, "-m", "loam.orchestrator", "--no-bootstrap"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert proc.returncode == 2, (
        f"expected argparse rejection (exit 2), got {proc.returncode}; "
        f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
    )
    assert "unrecognized arguments" in proc.stderr or "unrecognized argument" in proc.stderr, (
        f"argparse error message not found in stderr: {proc.stderr!r}"
    )

    # --help must not mention the flag.
    helpout = subprocess.run(
        [sys.executable, "-m", "loam.orchestrator", "--help"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert helpout.returncode == 0
    assert "--no-bootstrap" not in helpout.stdout, (
        "--no-bootstrap still listed in --help output; amendment #7 "
        "requires removal."
    )


def test_AC8_first_run_scaffold_does_not_write_bootstrap_py(
    tmp_path: Path,
) -> None:
    """After a fresh-workspace scaffold run, ``bootstrap.py`` must not
    exist under ``pos_root``. Writing a Python stub during scaffold
    would silently re-establish the orchestrator-loaded-bootstrap path
    the amendment is removing.

    Today the scaffold does not write ``bootstrap.py``; this test pins
    the invariant so future edits to ``first_run_scaffold.py`` that
    regress into templating a Python stub fail loudly.
    """
    from loam.workspace_bootstrap.adapters.first_run_scaffold import (
        run_first_run_scaffold,
    )

    pos_root = tmp_path / ".pos"
    # Run under platform_override=macos + service_bootstrap=False so the
    # scaffold is deterministic and writes zero side-effects beyond the
    # test tmp_path tree.
    result = run_first_run_scaffold(
        pos_root=pos_root,
        platform_override="macos",
        service_bootstrap=False,
        service_manager_dir_override=tmp_path / "agents",
        workspace_root=tmp_path / "fake-workspace",
    )
    assert result.ran, "scaffold must have run on a fresh tmp_path"

    bp = pos_root / "bootstrap.py"
    assert not bp.exists(), (
        f"first-run scaffold wrote a bootstrap.py stub at {bp}; "
        "amendment #7 forbids the scaffold from materialising a "
        "Python-stub bootstrap surface."
    )
    # Positive-space sanity: the yaml stub IS written.
    assert (pos_root / "bootstrap.yaml").exists(), (
        "sanity check failed — bootstrap.yaml missing after scaffold"
    )
