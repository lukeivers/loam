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

import os
from pathlib import Path

import pytest

from workspace_bootstrap import PHASE_ORDER, Phase
from workspace_bootstrap.adapters.first_run_scaffold import (
    CONFIRMATION_SENTENCE,
    ERR_PARTIAL_SCAFFOLD,
    ERR_PLATFORM_UNSUPPORTED,
    ERR_HANDS_OFF_INTERNAL,
    FirstRunScaffoldContribution,
    PartialScaffoldError,
    PlatformUnsupportedError,
    ScaffoldResult,
    ServiceManagerBootoutError,
    ServiceManagerRunner,
    WorkspaceSlugUnrepresentableError,
    run_first_run_scaffold,
    service_label,
    workspace_slug,
)


# ---- H1 — fresh scaffold writes the config tree ----------------------


def test_H1_fresh_first_run_writes_all_yamls(tmp_path: Path) -> None:
    pos_root = tmp_path / ".pos"
    service_dir = tmp_path / "LaunchAgents"
    # Amendment #6: workspace basename becomes the slug in service
    # labels. A workspace at ``<tmp>/pos-v2`` yields slug ``pos-v2`` →
    # ``com.pos-v2.pos-v2.{kind}`` labels. (Yes, the doubled ``pos-v2``
    # is an artefact of naming the test fixture after the repo — the
    # first ``pos-v2`` is the prefix constant, the second is the slug.)
    # Amendment #9: ``telegram.yaml`` is the thirteenth scaffold file.
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
        "telegram.yaml",
    ):
        assert (pos_root / rel).exists(), f"missing {rel}"
    # Service-manager files present under namespaced labels.
    # Amendment J / AC.J.5 added the ``memory-write-worker`` kind to
    # the launchd-supervised set; the per-workspace label list grows
    # accordingly.
    plists = list(service_dir.glob("*.plist"))
    labels = {p.stem for p in plists}
    assert labels == {
        "com.pos-v2.pos-v2.memory-graphiti",
        "com.pos-v2.pos-v2.orchestrator",
        "com.pos-v2.pos-v2.memory-write-worker",
    }


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
    # Amendment #9 (telegram-interface-framework-integration) updated
    # the adapter count from twelve to thirteen — the Q7 approved
    # wording advances in lockstep. The body below tracks this
    # amendment count and is the one place tests pin it.
    expected = (
        "pos v2 first-run scaffold complete: thirteen foundational "
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


# ---- Amendment #6 — namespaced-labels-and-bootout --------------------
#
# Acceptance criteria AC1, AC4, AC5, AC6, AC8 from
# docs/rebuild/components/namespaced-labels-and-bootout/proposal.md.
# AC2 and AC3 are covered by the updated H1 tests above (plist/unit
# filenames embed the workspace slug). AC7 is asserted from the
# hands-off-lifecycle side (test_first_run.py). AC9 is enforced by
# the seal-diff tests advanced in this amendment's seal commit.


def test_AC1_workspace_slug_deterministic_across_inputs() -> None:
    """AC1 — slug is basename lowercased, non-matching chars → '-',
    runs collapsed, leading/trailing '-' trimmed."""
    fixtures = [
        # (workspace_root, expected_slug)
        (Path("/tmp/pos3"), "pos3"),
        (Path("/tmp/POS3"), "pos3"),                    # uppercase
        (Path("/tmp/pos_v2_dev"), "pos-v2-dev"),        # underscores
        (Path("/tmp/My.App"), "my-app"),                # dots
        (Path("/tmp/!pos!_v2!"), "pos-v2"),             # punct + trim
        (Path("/tmp/alpha---beta"), "alpha-beta"),      # collapse runs
        (Path("/tmp/ivers-corp-pos-v2"), "ivers-corp-pos-v2"),
    ]
    for root, expected in fixtures:
        got = workspace_slug(root)
        assert got == expected, f"{root} → {got!r} (expected {expected!r})"


def test_AC1_service_label_composed_from_kind_and_slug() -> None:
    """AC1 adjunct — label-composition is pure and reverse-DNS shaped."""
    assert service_label("orchestrator", "pos3") == "com.pos-v2.pos3.orchestrator"
    assert service_label("memory-graphiti", "alpha") == (
        "com.pos-v2.alpha.memory-graphiti"
    )


def test_AC8_unrepresentable_slug_refuses_structurally(
    tmp_path: Path,
) -> None:
    """AC8 — a workspace basename that sanitises to empty is refused
    before any file write."""
    # Basename '...' sanitises: '.' → '-', collapse → '-', trim → ''.
    empty_slug_root = tmp_path / "..."
    empty_slug_root.mkdir()
    pos_root = tmp_path / ".pos"
    with pytest.raises(WorkspaceSlugUnrepresentableError) as excinfo:
        run_first_run_scaffold(
            pos_root=pos_root,
            platform_override="macos",
            service_bootstrap=False,
            service_manager_dir_override=tmp_path / "LaunchAgents",
            workspace_root=empty_slug_root,
        )
    assert excinfo.value.code == ERR_HANDS_OFF_INTERNAL
    # No files written — the refusal fires before the write loop.
    assert not pos_root.exists()
    assert not (tmp_path / "LaunchAgents").exists()


def test_AC8_workspace_slug_helper_raises_on_empty_basename() -> None:
    """AC8 adjunct — the helper itself fails closed on an unrepresentable
    input, independent of the scaffold caller."""
    with pytest.raises(WorkspaceSlugUnrepresentableError):
        workspace_slug(Path("/tmp/---"))
    with pytest.raises(WorkspaceSlugUnrepresentableError):
        workspace_slug(Path("/tmp/..."))


# ---- AC4 / AC5: bootout-before-bootstrap via fake subprocess ---------


class _RecordingSubprocessRunner:
    """Captures calls to subprocess.run for ServiceManagerRunner tests.

    Each invocation is recorded; the runner returns configurable
    CompletedProcess objects keyed by the first two argv tokens. This
    lets a test assert call order (bootout-before-bootstrap) without
    spawning real launchctl.
    """

    def __init__(
        self,
        *,
        bootout_returncode: int = 0,
        bootout_stderr: str = "",
    ) -> None:
        self.calls: list[list[str]] = []
        self._bootout_returncode = bootout_returncode
        self._bootout_stderr = bootout_stderr

    def __call__(self, argv, **kwargs):  # type: ignore[no-untyped-def]
        import subprocess as _sp

        self.calls.append(list(argv))
        # Check-what-is-this dispatch:
        if len(argv) >= 2 and argv[1] == "bootout":
            return _sp.CompletedProcess(
                args=argv,
                returncode=self._bootout_returncode,
                stdout="",
                stderr=self._bootout_stderr,
            )
        return _sp.CompletedProcess(
            args=argv, returncode=0, stdout="", stderr=""
        )


def test_AC4_bootout_precedes_bootstrap_on_macos(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """AC4 — ServiceManagerRunner.bootstrap issues launchctl bootout
    before launchctl bootstrap. Call order is load-bearing: bootstrap
    alone is a no-op when the label is already loaded."""
    import workspace_bootstrap.adapters.first_run_scaffold as fr

    fake = _RecordingSubprocessRunner()
    monkeypatch.setattr(fr, "subprocess", type("M", (), {"run": fake})())

    plist = tmp_path / "com.pos-v2.alpha.orchestrator.plist"
    plist.write_text("<plist/>")
    runner = ServiceManagerRunner(platform_label="macos")
    runner.bootstrap(
        label="com.pos-v2.alpha.orchestrator", service_file=plist
    )

    argv_sequence = [tuple(call[1:3]) for call in fake.calls]
    # Exactly two launchctl calls, bootout first then bootstrap.
    assert argv_sequence == [
        ("bootout", f"gui/{os.getuid()}/com.pos-v2.alpha.orchestrator"),
        ("bootstrap", f"gui/{os.getuid()}"),
    ]


def test_AC4_bootout_benign_when_service_not_loaded(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """AC4 — when launchctl bootout reports the label isn't loaded
    (the fresh-host case), the bootstrap call still proceeds."""
    import workspace_bootstrap.adapters.first_run_scaffold as fr

    fake = _RecordingSubprocessRunner(
        bootout_returncode=3,
        bootout_stderr="Boot-out failed: 113: Could not find specified service",
    )
    monkeypatch.setattr(fr, "subprocess", type("M", (), {"run": fake})())

    plist = tmp_path / "com.pos-v2.alpha.orchestrator.plist"
    plist.write_text("<plist/>")
    runner = ServiceManagerRunner(platform_label="macos")
    runner.bootstrap(
        label="com.pos-v2.alpha.orchestrator", service_file=plist
    )

    assert [call[1] for call in fake.calls] == ["bootout", "bootstrap"]


def test_AC4_bootout_hard_failure_raises_before_bootstrap(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """AC4 halt trigger — a non-'not loaded' bootout failure raises
    ServiceManagerBootoutError rather than pushing through to
    bootstrap with an ambiguous service-manager state."""
    import workspace_bootstrap.adapters.first_run_scaffold as fr

    fake = _RecordingSubprocessRunner(
        bootout_returncode=1,
        bootout_stderr="Some other launchctl failure",
    )
    monkeypatch.setattr(fr, "subprocess", type("M", (), {"run": fake})())

    plist = tmp_path / "com.pos-v2.alpha.orchestrator.plist"
    plist.write_text("<plist/>")
    runner = ServiceManagerRunner(platform_label="macos")
    with pytest.raises(ServiceManagerBootoutError) as excinfo:
        runner.bootstrap(
            label="com.pos-v2.alpha.orchestrator", service_file=plist
        )
    assert excinfo.value.code == ERR_HANDS_OFF_INTERNAL
    # bootstrap call must not have been issued.
    assert [call[1] for call in fake.calls] == ["bootout"]


def test_AC4_idempotent_bootstrap_is_a_noop(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """AC4 idempotency — calling bootstrap twice in a row issues two
    bootout-then-bootstrap sequences; final state is identical to one
    call from the caller's perspective (no exception, no mutation)."""
    import workspace_bootstrap.adapters.first_run_scaffold as fr

    fake = _RecordingSubprocessRunner()
    monkeypatch.setattr(fr, "subprocess", type("M", (), {"run": fake})())

    plist = tmp_path / "com.pos-v2.alpha.orchestrator.plist"
    plist.write_text("<plist/>")
    runner = ServiceManagerRunner(platform_label="macos")
    runner.bootstrap(label="com.pos-v2.alpha.orchestrator", service_file=plist)
    runner.bootstrap(label="com.pos-v2.alpha.orchestrator", service_file=plist)

    verbs = [call[1] for call in fake.calls]
    assert verbs == ["bootout", "bootstrap", "bootout", "bootstrap"]


def test_AC5_stale_label_clears_on_rebootstrap(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """AC5 — re-bootstrap with a new plist file issues a bootout on the
    same label first, so launchd drops the stale cached config before
    loading the new plist. This is the structural fix for the pos3
    regression (2026-04-22)."""
    import workspace_bootstrap.adapters.first_run_scaffold as fr

    fake = _RecordingSubprocessRunner()
    monkeypatch.setattr(fr, "subprocess", type("M", (), {"run": fake})())

    old_plist = tmp_path / "old" / "com.pos-v2.alpha.orchestrator.plist"
    new_plist = tmp_path / "new" / "com.pos-v2.alpha.orchestrator.plist"
    old_plist.parent.mkdir(parents=True)
    new_plist.parent.mkdir(parents=True)
    old_plist.write_text("<plist/>")
    new_plist.write_text("<plist/>")

    runner = ServiceManagerRunner(platform_label="macos")
    runner.bootstrap(label="com.pos-v2.alpha.orchestrator", service_file=old_plist)
    runner.bootstrap(label="com.pos-v2.alpha.orchestrator", service_file=new_plist)

    # Second bootstrap's bootout carries the same label — so launchd's
    # cache of the first (old_plist) is dropped before the second
    # bootstrap loads new_plist.
    bootouts = [call for call in fake.calls if call[1] == "bootout"]
    assert len(bootouts) == 2
    assert all(
        f"com.pos-v2.alpha.orchestrator" in call[2] for call in bootouts
    )
    # Second bootstrap references new_plist, not old_plist.
    bootstraps = [call for call in fake.calls if call[1] == "bootstrap"]
    assert len(bootstraps) == 2
    assert str(old_plist) in bootstraps[0]
    assert str(new_plist) in bootstraps[1]


def test_AC6_multi_workspace_writes_distinct_labels(tmp_path: Path) -> None:
    """AC6 — two scaffold calls under different workspace slugs write
    distinct service-manager files; neither evicts the other's."""
    # Workspace A.
    ws_a = tmp_path / "alpha"
    ws_a.mkdir()
    pos_root_a = tmp_path / "pos-a"
    agents_a = tmp_path / "LaunchAgents-a"
    run_first_run_scaffold(
        pos_root=pos_root_a,
        platform_override="macos",
        service_bootstrap=False,
        service_manager_dir_override=agents_a,
        workspace_root=ws_a,
    )
    # Workspace B.
    ws_b = tmp_path / "beta"
    ws_b.mkdir()
    pos_root_b = tmp_path / "pos-b"
    agents_b = tmp_path / "LaunchAgents-b"
    run_first_run_scaffold(
        pos_root=pos_root_b,
        platform_override="macos",
        service_bootstrap=False,
        service_manager_dir_override=agents_b,
        workspace_root=ws_b,
    )

    labels_a = {p.stem for p in agents_a.glob("*.plist")}
    labels_b = {p.stem for p in agents_b.glob("*.plist")}
    # Label sets are distinct — no slug overlap.
    assert labels_a.isdisjoint(labels_b)
    assert "com.pos-v2.alpha.orchestrator" in labels_a
    assert "com.pos-v2.beta.orchestrator" in labels_b


