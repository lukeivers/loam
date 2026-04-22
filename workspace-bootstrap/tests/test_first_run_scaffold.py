"""Acceptance tests for Amendment 4 — workspace-bootstrap's new
``first_run_scaffold`` phase.

Maps to H-criteria in proposal §5.1:

    H1 — first-run scaffold writes the config tree
    H2 — confirmation sentence emitted once; not re-emitted
    H3 — platform-unsupported halts with a named diagnostic
    H4 — partial-prior-state halts instead of overwriting
    H5 — confirmation sentence matches the Q7 approved wording

Also covers the new phase's integration with the phase-ordering engine
(first_run_scaffold runs before before_orchestrator_start).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workspace_bootstrap import PHASE_ORDER, Phase
from workspace_bootstrap.adapters.first_run_scaffold import (
    CONFIRMATION_SENTENCE,
    ERR_PARTIAL_SCAFFOLD,
    ERR_PLATFORM_UNSUPPORTED,
    FirstRunScaffoldContribution,
    PartialScaffoldError,
    PlatformUnsupportedError,
    ScaffoldResult,
    run_first_run_scaffold,
)


# ---- H1 — fresh scaffold writes the config tree ----------------------


def test_H1_fresh_first_run_writes_all_yamls(tmp_path: Path) -> None:
    pos_root = tmp_path / ".pos"
    service_dir = tmp_path / "LaunchAgents"
    result = run_first_run_scaffold(
        pos_root=pos_root,
        platform_override="macos",
        service_bootstrap=False,
        service_manager_dir_override=service_dir,
        workspace_root=tmp_path / "pos-v2",
    )
    assert result.ran is True
    assert result.reason == "fresh_scaffold"
    for rel in (
        "bootstrap.yaml",
        "memory.yaml",
        "memory-staging.yaml",
        "safety/always_ask.yaml",
        "cost/ceilings.yaml",
        "reversibility.yaml",
        "self-correction.yaml",
        "degradation-config.yaml",
    ):
        assert (pos_root / rel).exists(), f"missing {rel}"
    # Both service-manager files present.
    plists = list(service_dir.glob("*.plist"))
    labels = {p.stem for p in plists}
    assert labels == {"com.pos-v2.memory-graphiti", "com.pos.orchestrator"}


def test_H1_linux_writes_systemd_units(tmp_path: Path) -> None:
    pos_root = tmp_path / ".pos"
    service_dir = tmp_path / "systemd-user"
    result = run_first_run_scaffold(
        pos_root=pos_root,
        platform_override="linux",
        service_bootstrap=False,
        service_manager_dir_override=service_dir,
        workspace_root=tmp_path / "pos-v2",
    )
    assert result.ran is True
    services = list(service_dir.glob("*.service"))
    labels = {s.stem for s in services}
    assert labels == {"pos-v2-memory-graphiti", "pos-orchestrator"}


# ---- H2 — confirmation emitted once -----------------------------------


def test_H2_confirmation_emitted_once(tmp_path: Path) -> None:
    pos_root = tmp_path / ".pos"
    first = run_first_run_scaffold(
        pos_root=pos_root,
        platform_override="macos",
        service_bootstrap=False,
        service_manager_dir_override=tmp_path / "svc",
        workspace_root=tmp_path / "pos-v2",
    )
    assert first.confirmation is not None
    # Second run: ~/.pos/ + bootstrap.yaml already exist → no-op.
    second = run_first_run_scaffold(
        pos_root=pos_root,
        platform_override="macos",
        service_bootstrap=False,
        service_manager_dir_override=tmp_path / "svc",
        workspace_root=tmp_path / "pos-v2",
    )
    assert second.ran is False
    assert second.reason == "already_scaffolded"
    assert second.confirmation is None


# ---- H3 — platform-unsupported structural refusal --------------------


def test_H3_platform_unsupported_raises_named_diagnostic(tmp_path: Path) -> None:
    with pytest.raises(PlatformUnsupportedError) as excinfo:
        run_first_run_scaffold(
            pos_root=tmp_path / ".pos",
            platform_override="win32",
            service_bootstrap=False,
        )
    assert excinfo.value.code == ERR_PLATFORM_UNSUPPORTED
    assert "platform-unsupported:win32" in str(excinfo.value)
    assert excinfo.value.data["platform"] == "win32"


# ---- H4 — partial-prior-state halts instead of overwriting -----------


def test_H4_partial_prior_state_refuses_to_overwrite(tmp_path: Path) -> None:
    pos_root = tmp_path / ".pos"
    pos_root.mkdir()
    (pos_root / "memory.yaml").write_text("# leftover\n")
    with pytest.raises(PartialScaffoldError) as excinfo:
        run_first_run_scaffold(
            pos_root=pos_root,
            platform_override="macos",
            service_bootstrap=False,
            service_manager_dir_override=tmp_path / "svc",
            workspace_root=tmp_path / "pos-v2",
        )
    assert excinfo.value.code == ERR_PARTIAL_SCAFFOLD
    # Leftover file must still be there — nothing overwritten.
    assert (pos_root / "memory.yaml").read_text() == "# leftover\n"


# ---- H5 — confirmation sentence matches Q7 exactly --------------------


def test_H5_confirmation_sentence_is_Q7_approved_wording() -> None:
    expected = (
        "pos v2 first-run scaffold complete: twelve foundational "
        "components configured at defaults (safety/always-ask, cost "
        "ceilings, reversibility, self-correction, memory, "
        "degradation), memory sidecar and orchestrator launched as "
        "user services, staging store initialised. `~/.pos/` is your "
        "config dir — edit any file to adjust. Proceeding."
    )
    assert CONFIRMATION_SENTENCE == expected


# ---- phase-ordering integration --------------------------------------


def test_first_run_scaffold_phase_comes_before_before_orchestrator_start() -> None:
    assert (
        PHASE_ORDER.index(Phase.first_run_scaffold)
        < PHASE_ORDER.index(Phase.before_orchestrator_start)
    )


def test_first_run_scaffold_contribution_metadata_is_correct() -> None:
    md = FirstRunScaffoldContribution.metadata
    assert md.name == "first_run_scaffold"
    assert md.phase is Phase.first_run_scaffold
    assert md.required is True


# ---- dry-run -----------------------------------------------------------


def test_dry_run_returns_planned_writes_without_writing(tmp_path: Path) -> None:
    pos_root = tmp_path / ".pos"
    result = run_first_run_scaffold(
        pos_root=pos_root,
        platform_override="macos",
        dry_run=True,
    )
    assert result.ran is False
    assert result.reason == "dry_run"
    assert not pos_root.exists()
    assert result.confirmation == CONFIRMATION_SENTENCE
