# security-hooks-bundle — apply ladder

2026-05-24. Wave 1.4 — final Wave 1 ECC absorption build.
Three-component multi-component fence on
`framework/safety-layer/` + `framework/hands-off-lifecycle/` +
`plugins/dev-sdlc/` per D-SECHK.OVERLAP option B (partial-
absorb, owner-ratified 2026-05-24 via Telegram 12311).

Plan: `docs/plans/security-hooks-bundle.md`.

Shape:
  - Three new PreToolUse hook scripts at
    `framework/safety-layer/hooks/` (secret_pattern_guard,
    dangerous_flag_guard, config_write_guard) + shared
    `_secret_patterns.py` data + loader + `__init__.py` for
    the new subpackage.
  - 11 AC test files at
    `framework/safety-layer/tests/test_AC_SECHK_*.py`
    (AC.SECHK.1, 2, 3, 4, 5, B2_MIGRATION, S_outcome_altitude).
  - `framework/safety-layer/docs/architecture.md` updated with
    the hooks subdir + composition with refusal-chain.
  - `framework/hands-off-lifecycle/hooks/first_run_settings.py`
    marker-set extension (3 new hook script basenames added to
    `_LOAM_PRE_TOOL_USE_COMMAND_MARKERS`) + three new
    `build_*_guard_stanza` helpers + `build_safety_layer_stanzas`
    convenience helper.
  - `framework/hands-off-lifecycle/tests/test_AC_SECHK_6_settings_merge.py`
    for the 6-test settings-merge integration coverage.
  - `framework/hands-off-lifecycle/tests/test_AC_BAG_1_secret_commit.py`
    rewritten as a post-migration regression suite (bash_guard
    no longer fires on secret-FILE commits).
  - `framework/hands-off-lifecycle/tests/test_AC_BAG_7_audit_log.py`
    fixture updated: `test_AC_BAG_7_deny_writes_one_ndjson_line`
    uses a B5 `curl | bash` input (still firing) instead of
    the prior B2 `git add .env` input (migrated out).
  - `plugins/dev-sdlc/hooks/bash_guard.py` docstring updated
    + AC.BAG.1 B2 universal-leg check removed from `evaluate()`
    (B1/B3/B4/B5 surfaces preserved verbatim).

Single-cycle, single-seal ladder per the cycle-merge condition
in plan §4 (D-SECHK.CYCLE-SHAPE default-merge-when-no-overlap;
Cycle-1-plan time found Cycle 2's workspace-bootstrap edits
unnecessary because the scaffold composes
`merge_pre_tool_use` via the existing multi-contributor
stanza builders; extending the marker set + adding builder
helpers in Cycle 1 is sufficient for fresh workspaces to
receive the hooks at first-run).

AC families (full text in plan §2):

  - AC.SECHK.1 — secret-pattern (14-pattern ECC floor +
    workspace-additions) on Bash + Edit/Write/MultiEdit
    content; structured deny diagnostic.
  - AC.SECHK.2 — dangerous-flag (git push|commit --no-verify;
    git push --force protected-branch); protected-branch
    floor + workspace-additions.
  - AC.SECHK.3 — config-write (.eslintrc family / biome.json /
    .pre-commit-config.yaml / .git/config / root .gitignore).
  - AC.SECHK.4 — fail-open on internal exception (NDJSON log
    + exit-0 + empty stdout default-allow).
  - AC.SECHK.5 — toggle-off env vars at single + per-hook
    granularity; logged for audit.
  - AC.SECHK.6 — settings.json merge composes the three hooks
    idempotently; user-authored stanzas backed up.
  - AC.SECHK.7 — bash_guard B5 + DEV-MODE B1/B3/B4 preserved
    (B2 migrated out, AC.BAG.1 file rewritten as
    post-migration regression).
  - AC.SECHK.S1/S2/S3 — outcome-altitude (real subprocess,
    production hook scripts, no pre-arranged state).
  - AC.SECHK.B2-MIGRATION-{1,2,3} — behavior parity +
    no-double-fire + B1/B3/B4/B5 preservation.

Method-level choices (ratified at plan-author time per §0 +
§14):

  - D-SECHK.OVERLAP — OPTION B (partial absorb) — owner
    override via Telegram 12311.
  - D-SECHK.FAIL-OPEN — FAIL-OPEN + structured NDJSON log.
  - D-SECHK.PATTERN-SET — ECC 14-pattern floor + workspace-
    additions loader (additive only).
  - D-SECHK.TOGGLE-GRANULARITY — BOTH single env var and
    per-hook env vars.
  - D-SECHK.DIAGNOSTIC-SHAPE — STRUCTURED JSON per Claude
    Code's hookSpecificOutput convention.
  - D-SECHK.CYCLE-SHAPE — SINGLE CYCLE (cycles merged per
    plan-author-time discretion; Cycle 2's workspace-bootstrap
    scope absorbed into Cycle 1 via the marker-set extension).

Halt triggers (per plan §9): none fired; all ten cleared
Tier-0 pre-source-edit per the manifest's HALT TRIGGERS
section above.

Predecessor commits (per plan §6 + Wave 1 sequence):
  - 0a76e12 — readme-ac3-synonym-list-widening corrective
              seal (Wave 1.1).
  - 84aa38a — strategic-compact-skill-graduation seal
              (Wave 1.2).
  - e4c3123 — token-defaults-optin-skill workspace-bootstrap
              chore-seal (Wave 1.3 seal).
  - 51e8ef7 — token-defaults seal-SHA backfill (Wave 1.3
              close; BASELINE for this amendment).
  - <source-edit commit (this amendment; lands BEFORE
     `loam amend apply`)>.

BASELINE — 51e8ef7 (canonical-clean pre-this-amendment HEAD).
Three-component fence on `framework/safety-layer/` +
`framework/hands-off-lifecycle/` + `plugins/dev-sdlc/`.
Sidecars advance to this amendment's seal SHA at apply time.
