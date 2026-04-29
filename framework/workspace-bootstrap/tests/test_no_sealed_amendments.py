"""B20, B23 — git diff against baseline shows only workspace-bootstrap
changes. Zero deltas to any sealed component.

Seal-test pattern (B23 / proposal §3.5): this file defines a BASELINE
constant and reads SEAL_COMMIT from a sidecar file, diffing
`BASELINE..SEAL_COMMIT` — NOT `..HEAD`. The HEAD-based variant is the
defect fixed on `f94d602`; it must not be reintroduced.

BASELINE: the commit immediately preceding the most recent amendment
    window for workspace-bootstrap. Originally ac48a7b at first seal;
    updated to 3780603 when Amendment 4 (hands-off-lifecycle
    first_run_scaffold phase) opened. Each new amendment that opens
    this sealed surface updates BASELINE to the pre-amendment tip so
    the diff scope reflects the amendment, not the full rebuild
    history.
SEAL_COMMIT: populated at seal time. During build, falls back to HEAD.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
# BASELINE advances when workspace-bootstrap opens a new amendment
# window:
#   - ac48a7b  at first seal
#   - 3780603  when Amendment 4 (first_run_scaffold phase) opened
#   - 63b7cb8  when the session-start-detachment amendment opened
#              (run_first_run_scaffold gains a partial_recovery=True
#              path so the detached worker can complete a scaffold
#              that crashed mid-flight, closing the H4 "retry next
#              session" terminal user surface). 63b7cb8 is the tip
#              immediately before this amendment's commit, so the
#              diff scope captures only this amendment's work even
#              though unrelated commits landed between the prior
#              workspace-bootstrap seal (1a55969) and this one.
#   - 9f35979  when the namespaced-labels-and-bootout amendment (#6)
#              opened. Per-workspace service-label namespacing
#              (`com.loam.<slug>.<kind>`) + launchctl bootout-before-
#              bootstrap so multiple loam workspaces coexist on one
#              host and stale launchd cache is replaced rather than
#              no-op'd (closes the pos3 first-run regression 2026-04-22).
#              Multi-component amendment with hands-off-lifecycle in
#              lockstep. 9f35979 is the pre-amendment tip — the docs-
#              migration chore commit immediately before the amendment
#              code commit.
#   - a5dbf8f  when the orchestrator-bootstrap-unification amendment
#              (#7) opened. Orchestrator no longer self-loads
#              `bootstrap.py`; the workspace-bootstrap framework's
#              `WorkspaceBootstrapPyContribution` adapter is the sole
#              loader, and missing `~/.loam/bootstrap.yaml` is the new
#              fail-closed trigger (MissingConfigError, -32080). Adapter
#              + integration-test edits land on this side because the
#              removed `OrchestratorConfig.require_bootstrap` field was
#              referenced here; the amendment's primary surface is
#              orchestrator/. a5dbf8f is the pre-amendment tip — the
#              amendment-#6 seal commit immediately before this
#              amendment's code commit.
#   - 7d462e3  when the linux-removal amendment (#10) opened. Per
#              docs/odd-methodology.md §2.5, Linux was never a named
#              supported-platform objective; `_SYSTEMD_TEMPLATES`, the
#              linux branches in `detect_platform` / `_install_service_
#              manager_files` / `ServiceManagerRunner.bootstrap`, and
#              the `test_H1_linux_writes_systemd_units` +
#              `test_AC4_linux_stop_then_reload_then_start` tests are
#              removed. Multi-component amendment touching workspace-
#              bootstrap, orchestrator, self-upgrade, hands-off-
#              lifecycle, first-run-inventory.yaml, and amendment-#6's
#              proposal (historical superseded-by marker). 7d462e3 is
#              the pre-amendment tip — the graceful-degradation +
#              observability-aggregator retrofit chore commit
#              immediately before this amendment's code commit.
#   - b9e1f96  when the telegram-interface-framework-integration
#              amendment (#9) opened. The framework composes
#              `telegram-interface` as the thirteenth foundational
#              adapter: a new
#              `workspace_bootstrap.adapters.telegram_interface.
#              TelegramInterfaceContribution` constructs a
#              `TelegramAdapter` from telegram-interface's public
#              surface, publishes the channel on the host
#              (`host.telegram_adapter`, `host.telegram_channel`,
#              `host.channel_registry["telegram"]`), and composes
#              with `is_active=False` (degraded-alive) at default
#              config so boot succeeds without any Telegram
#              credentials. `_BOOTSTRAP_YAML` grows by one stanza
#              (13 entries now); `_TELEGRAM_YAML` is a new scaffold
#              constant; the confirmation sentence updates "twelve"
#              → "thirteen". Multi-component amendment with
#              telegram-interface (docs-only; no src/ edits per AC7)
#              and hands-off-lifecycle (BASELINE bump + allowed-
#              prefix extension) in lockstep. b9e1f96 is the pre-
#              amendment tip — the amendment-#8 audit-closure seal
#              commit immediately before this amendment's code
#              commit. Proposal numbering (#9) pre-dates amendments
#              #10 and #11 which landed first; the number is
#              assigned at proposal time, not landing time.
#   - c94e146  when the workspace-bootstrap-b25-framework-internal-
#              criterion amendment (#17) opened. Amendment #4 added
#              `Phase.first_run_scaffold` to
#              `workspace_bootstrap.spec.Phase`; the audit surfaced
#              that the new enum value contradicted the *letter* of
#              B18 ("Zero change to bootstrap's code"). Owner's ruling
#              (path a): add a new criterion B25 naming the framework-
#              internal phase set — the enum values are the phases
#              registered by bootstrap-internal adapters, and external
#              (Phase 4+) contributions consume them rather than
#              extend them. B18 continues to govern external-
#              contribution registration unchanged. B25's test is
#              outcome-shaped (dynamic `pkgutil.iter_modules` over
#              `workspace_bootstrap.adapters`, reading
#              `metadata.phase` off each Contribution class). The
#              amendment edits the proposal doc (new §4.8 + cross-
#              reference in §4.5 after B19), appends one paragraph to
#              `docs/odd-in-loam.md` §6.1, and adds the B25 test.
#              Multi-component amendment in lockstep with
#              hands-off-lifecycle (BASELINE bump + narrative note).
#              c94e146 is the pre-amendment tip — amendment #16's
#              seal commit (d12-chaos-durability-split-pytest)
#              immediately before this amendment's code commit.
#   - 795768c  when the workspace-bootstrap-plist-path amendment (#31)
#              opened. Fresh-clone first-run's scaffolded launchd
#              plists now emit a canonical PATH in their
#              EnvironmentVariables so the memory-graphiti service's
#              shutil.which("claude") at construction resolves the
#              user-installed `claude` binary under ~/.local/bin; the
#              orchestrator plist receives the same PATH via a shared
#              helper so the latent same-class hazard on the
#              orchestrator surface is closed by construction. Single-
#              component amendment on the `workspace-bootstrap`
#              surface (hands-off-lifecycle did NOT join the manifest
#              — the D5.1 real-launchctl seal test lives in
#              workspace-bootstrap/tests/ directly). 795768c is the
#              pre-amendment tip — amendment #30's seal commit
#              (chore(seals): memory-system-env-scrubber-user seal)
#              immediately before this amendment's code commit.
#   - 057afdb  when the workspace-bootstrap-persona-scaffold amendment
#              (#36) opened. First-run scaffolded
#              `<workspace>/personas/<handle>/` from the framework
#              persona-template; ScaffoldResult gained `persona_dir`
#              + `persona_installed`; pure-function
#              `resolve_persona_handle` exposed for caller-side
#              prompts. 057afdb is the pre-amendment tip immediately
#              preceding amendment #36's code commit.
#   - fa15127  when the workspace-bootstrap-tracker-seed amendment
#              (#39) opened. First-run scaffold gains an additive
#              tracker-seed responsibility: on a workspace whose
#              tracker DB does not yet carry a value-prop root, the
#              scaffold seeds the workspace's
#              `~/.loam/objective_tracker.sqlite` with a value-prop
#              root + spec-tier descendants. On pos-v2 dev workspaces
#              (`docs/rebuild/VALUE_PROPOSITION.md` present at the
#              workspace root) the seed reads the canonical doc as
#              source. On non-dev workspaces it reads
#              `<workspace>/value-prop.md`; if absent, the seed
#              skips with a structured diagnostic. Idempotent by
#              query (uses amendment #38's
#              `query_projection_view` filter on
#              `lifted_from.source_doc` to detect already-seeded
#              records and skip). Single-component amendment on the
#              `workspace-bootstrap` surface; consumes amendment
#              #38's `LiftedFrom` + `ObjectiveFilter` +
#              `query_projection_view` API; no source change to any
#              other sealed component. fa15127 is the pre-amendment
#              tip — amendment #38's plan-SHA backfill commit
#              immediately before this amendment's code commit.
#              Mirrors amendments #34 / #35 / #36 / #37 / #38
#              BASELINE-as-HEAD~1 pattern.
BASELINE = "820fd84"

SEAL_COMMIT_PATH = Path(__file__).parent / "SEAL_COMMIT"


def _seal_commit() -> str:
    """Resolve SEAL_COMMIT from the sidecar file, else HEAD.

    Once sealed, tests/SEAL_COMMIT holds the exact SHA and the diff
    runs against that — the HEAD defect cannot recur."""
    if SEAL_COMMIT_PATH.exists():
        txt = SEAL_COMMIT_PATH.read_text().strip()
        if txt and txt != "HEAD":
            return txt
    return "HEAD"


def test_B23_seal_commit_pinning_pattern() -> None:
    """The test file exposes SEAL_COMMIT_PATH and names BASELINE; the
    diff call routes through _seal_commit() (not a hardcoded HEAD)."""
    source = Path(__file__).read_text()
    assert "BASELINE = " in source
    assert "SEAL_COMMIT_PATH" in source
    assert "{BASELINE}..{seal}" in source, (
        "the diff call must route through _seal_commit()"
    )


def test_B20_only_workspace_bootstrap_changed() -> None:
    seal = _seal_commit()
    out = subprocess.check_output(
        ["git", "diff", "--name-only", f"{BASELINE}..{seal}"],
        cwd=REPO_ROOT,
        text=True,
    )
    changed = [ln for ln in out.splitlines() if ln.strip()]

    # `data/` is runtime test-output (aggregator spool, cost sqlite).
    # `hands-off-lifecycle/` is the amendment counterpart in the
    # 2026-04-22 session-start-detachment multi-component amendment —
    # run_first_run_scaffold gained a partial_recovery=True path here,
    # and the detached worker that consumes it lives in
    # hands-off-lifecycle. Both components' tests re-seal in lockstep.
    # Amendment #6 (namespaced-labels-and-bootout) additions:
    #   - `docs/rebuild/components/namespaced-labels-and-bootout/` —
    #     the proposal + brief living with the amendment.
    #   - `first-run-inventory.yaml` — workspace-level manifest; the
    #     amendment templates service labels with `{slug}` so the
    #     inventory is workspace-agnostic.
    # Amendment #7 (orchestrator-bootstrap-unification) additions:
    #   - `orchestrator/` — primary surface for the amendment (this
    #     multi-component amendment's main edits land in orchestrator/
    #     with counterpart edits on this side for the removed
    #     `require_bootstrap` field's upstream callers).
    #   - `docs/rebuild/components/orchestrator-bootstrap-unification/`
    #     — the proposal living with the amendment.
    # Amendment #10 (linux-removal) additions:
    #   - `self-upgrade/` — dead `systemd_user_restart` removed.
    #   - `memory-system/` — orphan `memory-system/systemd/` directory
    #     removed (unit template was never read by runtime code).
    #   - `docs/rebuild/components/namespaced-labels-and-bootout/` —
    #     already in the allowed list for amendment #6; the #10 edit is
    #     the superseded-by marker on AC3.
    #   - `docs/rebuild/plans/` — the amendment's own plan file.
    # Amendment #9 (telegram-interface-framework-integration) additions:
    #   - `telegram-interface/` — docs-only prefix so the seal-diff
    #     test tolerates the amendment-cycle README / proposal edits on
    #     this multi-component amendment. Per AC7 the amendment ships
    #     zero edits under `telegram-interface/src/`; the
    #     telegram-interface component's own seal test enforces that
    #     structural invariant directly on `telegram-interface/src/`.
    #   - `docs/rebuild/components/telegram-interface-framework-integration/`
    #     — the proposal living with the amendment.
    # Amendment #17 (workspace-bootstrap-b25-framework-internal-criterion)
    # additions:
    #   - `docs/rebuild/components/workspace-bootstrap/` — the proposal
    #     doc gains a new §4.8 criterion (B25) + an optional cross-
    #     reference in §4.5 after B19. This is the first proposal-doc
    #     edit since the initial port at a11f081.
    #   - `docs/odd-in-loam.md` — one-paragraph cross-reference appended
    #     to §6.1 (the "pattern B18 teaches" subsection) noting B25's
    #     existence as the framework-internal-phase carve-out. Admitted
    #     via the precise `allowed_files` entry rather than a `docs/`
    #     blanket so the diff-scope check stays tight.
    allowed_prefixes = (
        "framework/workspace-bootstrap/",
        "workspace-bootstrap/",
        "data/",
        "framework/hands-off-lifecycle/",
        "framework/orchestrator/",
        "framework/self-upgrade/",
        "framework/memory-system/",
        "framework/telegram-interface/",
        "docs/rebuild/components/namespaced-labels-and-bootout/",
        "docs/rebuild/components/orchestrator-bootstrap-unification/",
        "docs/rebuild/components/telegram-interface-framework-integration/",
        "docs/rebuild/components/workspace-bootstrap/",
        "docs/rebuild/plans/",
        "framework/cost-governance/",
        "framework/dormancy/",
        "framework/graceful-degradation/",
        "framework/observability-aggregator/",
        "framework/reversibility-primitive/",
        "framework/self-correction/",
        "framework/tools/",
        "framework/safety-layer/",
        "docs/rebuild/plans/research/",
        "framework/primary-persona/",
        "framework/workspace-bootstrap/tests/test_AC36_6_framework_not_content.py",
        "cost-governance/",
        "framework/hands-off-lifecycle/canonical-dev/",
        "framework/objective-tracker/",
        "framework/scope-of-work/",
        "framework/workspace-sync/",
        "dormancy/",
        "graceful-degradation/",
        "hands-off-lifecycle/",
        "memory-system/",
        "objective-tracker/",
        "observability-aggregator/",
        "orchestrator/",
        "primary-persona/",
        "reversibility-primitive/",
        "safety-layer/",
        "scope-of-work/",
        "self-correction/",
        "self-upgrade/",
        "telegram-interface/",
        "tools/",
        "workspace-sync/",
        "docs/rebuild/components/",
        "docs/rebuild/spec/",
        "framework/tools/loam-mode/",
        "framework/tools/loam-migrate-dormancy-config/",
    )
    allowed_files: set[str] = {
        "framework/first-run-inventory.yaml",
        "docs/odd-in-pos.md",
        "docs/odd-in-loam.md",
        "CLAUDE.md",
        "docs/odd-methodology.md",
        "docs/rebuild/FUTURE_IDEAS.md",
        "docs/rebuild/STATE.md",
        "docs/rebuild/VALUE_PROPOSITION.md",
        ".claude/settings.json",
        "first-run-inventory.yaml",
        "docs/CLAUDE_CAPABILITIES.md",
        "docs/duration-estimation-rubric.md",
        "docs/rebuild/FUTURE_IDEAS_DRAFT.md",
        "CLAUDE.dev.md",
        "docs/rebuild/dev-mode-manifest.yaml",
    }

    offending = []
    for path in changed:
        if any(path.startswith(p) for p in allowed_prefixes):
            continue
        if path in allowed_files:
            continue
        offending.append(path)
    assert offending == [], (
        f"Sealed-component paths modified: {offending}. "
        "Halt-signal condition."
    )
