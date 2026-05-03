# FBE.5 sub-plan — Description scrub + LOW-fix sweep + `~/.loam/` verify

**Status:** sub-plan-doc, plan-before-code. Authored 2026-05-03.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Parent plan:** `docs/rebuild/plans/v0-1-0-foldback-scope-expansion.md` (FBE.5 row in §1 + AC ladder in §4 + §8 register).
**Programme master:** `docs/rebuild/plans/oss-v0-1-0-publish.md`.
**Predecessors:** FBE.1 sealed at `21b9480`; FBE.2 sealed at `8d2b770`; FBE.3 sealed at `becf183`; FBE.4 sealed at `99c03a6`; FBE.7 sealed at `a102bde`.
**BASELINE (pre-build tip):** `02a65e2` — current canonical pos-v2 HEAD (the foundation-revision rebuild plan-doc commit).

---

## 1. Summary / TLDR

FBE.5 closes the reviewer's last batch of stranger-perspective findings (HIGH 4 + LOW 1 + LOW 3) plus the AC.FBE.5.6 smoke verification of the post-FBE.1 `loam init` end-to-end behaviour. Three classes of edit:

1. **Pyproject `description` scrub (AC.FBE.5.1 + 5.2)** — 15 component `pyproject.toml` files have dev-vocabulary leakage (`pOS v2`, `Phase 4`, `amendment #N`, `M-series`, `M1g`, etc.) in their `description` field. Scrub per the AC.FBE.5.2 vocabulary table.
2. **Doc-prose fixes (AC.FBE.5.3, 5.4, 5.5)** — `loam_cli/cli.py` module docstring scrub; README "before public flip" block removed (the rename amendment landed; present-tense statement is the README's surrounding prose); `docs/getting-started.md` double "Step 5" re-numbered.
3. **`loam init` end-to-end smoke (AC.FBE.5.6)** — `loam init /tmp/test-fbe5-ws --from /Users/lukeivers/ivers-corp-pos-v2/` succeeds; post-invocation `~/.loam/` exists with the expected scaffolding (the `bootstrap_new_workspace` contract).

This is a vocabulary + doc-quality + smoke-verification amendment. **No behaviour changes** (AC.FBE.5.7 negative AC).

The sealed-component fence is **wide** (15 components touched via `description` edit) but every edit is a single line in a single file. The `loam_cli/cli.py` docstring edit lives in the `framework/tools/loam` fence component. The README + getting-started.md edits ride via universal-paths admission (top-level + `docs/` files).

---

## 2. Halt-and-surface BEFORE build

### Surface #1 (no halt — recorded; dev-only tool descriptions are OUT OF SCOPE)

Survey of all `pyproject.toml` `description` fields across the canonical tree (28 files, surveyed pre-build) shows **9 dev-only tools** (`heavy-b-migrate`, `loam-migrate-launchd-labels`, `loam-migrate-host-config`, `loam-migrate-dormancy-config`, `upgrade-merge-resolver`, `pos-publish-framework-only`, `orphan-plist-cleanup`, `loam-memory-inspect`, plus the dev-sdlc `loam-amend` + `loam-mode` subtools) have similar dev-vocabulary leakage in their descriptions (`post-M1g namespace pivot`, `M1e §11 finding #4`, `M-FBM`, `M6b.1`, `pos-v2`, `M1c`, `M1f`, etc.). These are partition-classified `dev_only` (per `framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml` lines 262-279 + the sub-tool partition for dev-sdlc internals), so their descriptions never reach the public synth tree.

**Decision (autonomous, builder's call):** these dev-only tool descriptions are **OUT OF SCOPE for FBE.5** per ODD §2.5 (no out-of-scope edits). AC.FBE.5.1 names a specific component set (the 15 sealed runtime components + `tools/loam` + `loam-init` + `dev-sdlc`); the dev-only tools are not in that set. Fixing them later is doc-quality work with no public-facing impact.

**FUTURE_IDEAS_DRAFT candidate:** "Dev-only tool pyproject `description` scrub — `framework/tools/{heavy-b-migrate,loam-migrate-launchd-labels,loam-migrate-host-config,loam-migrate-dormancy-config,upgrade-merge-resolver,pos-publish-framework-only,orphan-plist-cleanup,loam-memory-inspect}/pyproject.toml` + `plugins/dev-sdlc/tools/{loam-amend,loam-mode}/pyproject.toml` carry dev-vocabulary leakage in their `description` fields. Outside FBE.5 fence (dev-only partition); appropriate as a v0.1.x or v0.2 cleanup amendment."

This surface is recorded (not halted on) because the dispatcher's plan-doc explicitly named the 15-component scope; expanding now would violate scope-discipline.

### Surface #2 (no halt — recorded; `dormancy` + `loam-init` descriptions are already clean)

Survey verified:
- `framework/dormancy/pyproject.toml`: `description = "Dormancy policy layer for loam — Claude-upstream failure detection, per-mode FSMs, policy dispatch, notification, resume."` — already says "for loam", no leaky vocabulary. **No edit needed.**
- `framework/loam-init/pyproject.toml`: `description = "loam init subcommand — registers \`loam init <path> --from <canonical>\` as a loam.cli.subcommands entry-point. Wraps the existing workspace-bootstrap fresh-workspace primitive so the documented onboarding verb works end-to-end."` — clean. **No edit needed.**

The parent plan's AC.FBE.5.1 named these "verify at build" — the verification here resolves both as no-edit. Sub-plan §6 still includes them in the fence (sidecar bumps) per AC.FBE.5.S "every component whose pyproject was edited" — wait, NO. Per AC.FBE.5.S exact text: "every component whose pyproject was edited (likely all 15 + tools/loam + loam-init + dev-sdlc)". If `loam-init` and `dormancy` pyprojects are NOT edited, they are NOT in the fence. **Fence narrows accordingly.**

### Surface #3 (no halt — recorded; FBE.4 partner-prefix gap will recur for `dev-sdlc`)

The FBE.4 status file (`<workspace>/.scratch/claude-output/fbe4-status-2026-05-03.md` Surface #5) documents that `loam amend apply`'s partner-prefix derivation assumes `framework/<name>/` + bare-`<name>/` shape, which doesn't match `dev-sdlc`'s actual location at `plugins/dev-sdlc/`. FBE.4 hand-admitted `plugins/dev-sdlc/` in `framework/loam-init/tests/test_no_sealed_amendments.py`'s `allowed_prefixes` via corrective commit `0c4d9a0`.

For FBE.5, the fence likely includes `plugins/dev-sdlc/`. Other fence members will need `plugins/dev-sdlc/` admitted in their `allowed_prefixes`, and `dev-sdlc` itself will need `framework/<name>/` admitted for the other fence members.

**Build-time strategy:** run `loam amend apply` first; if `loam amend seal` fails on any of the touched fence components' fence tests with offending paths under the missing partner-prefix, apply a corrective hand-admit per FBE.4 precedent (`0c4d9a0`). Most of the 14 framework/* fence members already have `plugins/dev-sdlc/` admitted via M6a baseline (verified in FBE.4 status); the gap is only on components established AFTER M6a. Survey at apply time.

### Surface #4 (no halt — recorded; README "before public flip" block removal is the cleanest fix)

AC.FBE.5.4: "README.md 'before public flip' note (HIGH 4) rewritten in present tense or removed entirely." The block at README.md lines 52-58 is a "v0.1.0 release sequence" note explaining the legacy `pos` binary name vs the documented `loam` name. The rename amendment HAS landed (the synth ships `loam`); the block is a stale before-state explanation. The README's surrounding prose already uses `loam` exclusively. The cleanest edit is **block removal** (rather than rewriting in present tense — present-tense version would say "the binary is `loam`" but that's already stated in the immediately-preceding prose). Removing the block reads naturally; the next paragraph (`## What ships in v0.1.0`) follows without a beat.

### Surface #5 (no halt — recorded; getting-started.md "Five-step bootstrap" header needs updating to "Six-step bootstrap")

Survey of `docs/getting-started.md` shows the section header at line 41 says "Five-step bootstrap" but the actual content has 5 numbered "### N." subheadings, with TWO labelled "### 5." (lines 101 + 113). Re-numbering the second "### 5." to "### 6." per AC.FBE.5.5 produces a six-step structure; the "Five-step bootstrap" header at line 41 + the body intro at line 43 ("The whole walkthrough is five shell commands") become inconsistent. **Fix scope:** re-number the second "### 5." → "### 6." (AC.FBE.5.5 named edit) AND update the header at line 41 to "Six-step bootstrap" AND update the body sentence at line 43 to "The whole walkthrough is six shell commands" — three small consistency edits within the named "double-step-5" defect. This is the minimal coherent edit; not "drift beyond the named LOW 1 fix" per HT-3.

### Surface #6 (no halt — recorded; `dev-sdlc` description scrub is a vocabulary normalization, not a substantive change)

The `plugins/dev-sdlc/pyproject.toml` description currently says: `"... First plugin under loam's contribution-based extension protocol; pattern-establishing for v0.2+ plugins."` Per AC.FBE.5.2 vocabulary table: `Phase 4+ extension protocol` → `the plugin contribution protocol`. The dev-sdlc description doesn't say "Phase 4+" but does use the noun phrase "contribution-based extension protocol" — same concept. Normalization edit: `"contribution-based extension protocol"` → `"plugin contribution protocol"`. Vocabulary, not substance.

---

## 3. Spec-objective placement

**Binds to:**
- **AC.PO.1 + AC.PO.2** (prime objective per `docs/rebuild/VALUE_PROPOSITION.md`) — closing the "stranger reads the docs and is confused by `pOS v2` / `M1g` / `Phase 4` etc. vocabulary" failure mode that the M11a-3 reviewer flagged as HIGH 4 + LOW 1 + LOW 3.
- **Reviewer foldback HIGH 4 + LOW 1 + LOW 3** (per parent plan §2.5 + §2.8) — vocabulary scrub + getting-started.md double-step-5 fix.
- **AC.FBE.5.* per parent plan §4 FBE.5 row** — every AC ladders to the same parent.
- **AC.FBE.5.6 — `loam init` end-to-end smoke** binds to verifying the FBE.1 contract that `loam init` scaffolds `~/.loam/` (HIGH 2 closes by verification).

**Ladders to:** AC.FBE.5.* → AC.OSS-M11a.* (FBE.6 reviewer GO) → M12 publish-flip → AC.PO.1 + AC.PO.2.

---

## 4. Acceptance criteria (FBE.5.*)

AC family `AC.FBE.5.*` — collision-safe (verified: no prior amendment uses `AC.FBE.5.*`).

| AC ID | Outcome | Verification |
|---|---|---|
| **AC.FBE.5.1** | The `description` field of these 15 component `pyproject.toml` files no longer contains `pOS v2` / `Phase 4` / `amendment #N` / `M-series` / `M1` / `M1g` / `M6a` / `M6b.1` / `M11a` / `M-FBM`-style dev vocabulary: `framework/{cost-governance,observability-aggregator,orchestrator,objective-tracker,scope-of-work,safety-layer,primary-persona,reversibility-primitive,workspace-bootstrap,telegram-interface,self-upgrade,self-correction,workspace-sync}/pyproject.toml` + `plugins/dev-sdlc/pyproject.toml` + `framework/tools/loam/pyproject.toml`. Verified at planning: `framework/dormancy/pyproject.toml` and `framework/loam-init/pyproject.toml` are already clean (Surface #2) and are NOT in the edit list. `framework/hands-off-lifecycle/` has no `pyproject.toml` (config-only component). | `git grep -n -E "pOS v2\|Phase 4\|amendment #\|M[0-9][a-z]\|M-series\|M1g\|M-FBM" -- '*pyproject.toml' :^framework/tools/heavy-b-migrate :^framework/tools/loam-migrate-* :^framework/tools/upgrade-merge-resolver :^framework/tools/pos-publish-framework-only :^framework/tools/orphan-plist-cleanup :^framework/tools/loam-memory-inspect :^plugins/dev-sdlc/tools/` returns zero hits in the 15 in-scope `description` lines. |
| **AC.FBE.5.2** | The vocabulary substitutions used: `pOS v2` → `loam`; `Phase 4+ extension protocol` (and the synonym `contribution-based extension protocol`) → `the plugin contribution protocol`; `amendment #N`-shaped parentheticals → dropped; `M-series` / `M1g` / `M6a` / `M6b.1` etc. → dropped (the *behaviour* clause stays; only the amendment-number references go); `(post-M1g namespace pivot per M1e §11 finding #4)`-shaped parenthetical → dropped entirely. | Direct read of each edited description; spot-check 3 components: `cost-governance` ("for pOS v2" → "for loam"), `workspace-bootstrap` ("Phase 4+ extension protocol" → "plugin contribution protocol" + "pOS v2" → "loam"), `tools/loam` ("post-M1g rename of pos-amend per loam-rename-decisions.md Tier-1 #6" → dropped parenthetical entirely). |
| **AC.FBE.5.3** | `framework/tools/loam/src/loam_cli/cli.py` module docstring (lines 1-33) no longer references amendment numbers (`M1g`, `M6a`, `M6b.1`, `loam-rename-decisions.md`, `oss-v0-1-0-publish-dev-sdlc-plugin.md`, `master plan AC.OSS-M6.15`, etc.). The behaviour description stays; the amendment-trail references go. The in-function comments at lines 118-124 + 141-143 (which reference `M6a`, `M6b.1`, `D-build.M6.15`) ALSO scrub per the same vocabulary discipline. | `grep -n -E "M[0-9][a-z]\|amendment\|loam-rename-decisions\|oss-v0-1-0-publish\|master plan AC" framework/tools/loam/src/loam_cli/cli.py` returns zero hits. |
| **AC.FBE.5.4** | `README.md` "before public flip" block (lines 52-58) is REMOVED entirely. The README's surrounding prose (`Your first run scaffolds ~/.loam/...` paragraph at line 47-50 + `## What ships in v0.1.0` heading at line 60) reads coherently across the gap. | `grep -n "before public flip\|public flip\|legacy build name\|currently shipped as" README.md` returns zero hits. README still parses as Markdown (manual inspection — surrounding prose flows). |
| **AC.FBE.5.5** | `docs/getting-started.md` is consistently six-step: header at line 41 says "Six-step bootstrap"; intro at line 43 says "six shell commands"; the second "### 5." at line 113 is renumbered to "### 6.". Three minimal coherence edits within the LOW 1 named scope per Surface #5. | `grep -n "^### " docs/getting-started.md` shows 1, 2, 3, 4, 5, 6 in order with no duplicate "5"; `grep -n "Five-step\|Six-step\|five shell commands\|six shell commands" docs/getting-started.md` shows only the "Six-step" + "six shell commands" forms. |
| **AC.FBE.5.6** | `loam init /tmp/test-fbe5-ws --from /Users/lukeivers/ivers-corp-pos-v2/` (invoked from a fresh shell session against the post-seal canonical tree) succeeds with exit 0; post-invocation `~/.loam/` exists with at minimum `~/.loam/canonical-cache/` (the `bootstrap_new_workspace` contract per FBE.1's source delta). HIGH 2 closes by verification: no code edit needed if smoke passes. | Direct shell invocation against the canonical-installed `loam` (the venv at `/Users/lukeivers/ivers-corp-pos-v2/.venv/bin/loam`); verify `ls /tmp/test-fbe5-ws/{framework,workspace,.claude}` shows scaffolded structure; verify `ls ~/.loam/` shows scaffolded structure (carefully: `~/.loam/` is an EXISTING dev-machine state — verify the `bootstrap_new_workspace` write succeeded by checking the `canonical-cache/` subdir or sync-config marker, NOT by checking the dir's empty/non-empty state). |
| **AC.FBE.5.7** | Negative AC: zero behaviour changes from FBE.5. The only edits land in `description` fields, the `cli.py` docstring + comments, README prose, and `getting-started.md` prose. No source-code logic edits. | `git diff BASELINE..SEAL_COMMIT --stat` shows only doc-shape file changes; no `*.py` LOC delta beyond the cli.py docstring/comments lines; no test-source-code edits beyond sidecar bumps + BASELINE updates. |
| **AC.FBE.5.S** | Sealed-component fence: `framework/{cost-governance,observability-aggregator,orchestrator,objective-tracker,scope-of-work,safety-layer,primary-persona,reversibility-primitive,workspace-bootstrap,telegram-interface,self-upgrade,self-correction,workspace-sync}/` + `framework/tools/loam/` + `plugins/dev-sdlc/`. **15 sealed components** in fence. Every fence component edits its `description` only (single-line edit); `tools/loam` additionally edits the `cli.py` docstring + comments. README + `getting-started.md` ride via `universal_paths.files` admission. | `git diff BASELINE..SEAL_COMMIT --name-only` produces only paths under: (a) the 15 fence components (sidecar + BASELINE bump + pyproject.toml description edit; for `tools/loam` also `src/loam_cli/cli.py`), (b) `docs/rebuild/plans/` (sub-plan + manifest + parent backfill via universal prefix), (c) `README.md` + `docs/getting-started.md` (universal-admitted files). |

**ACs deliberately out of scope (NOT in FBE.5):**
- Dev-only tool pyproject description scrubs (Surface #1 — FUTURE_IDEAS_DRAFT candidate).
- Any `*.py` source code logic edits beyond the cli.py docstring/comments (Surface #2 — AC.FBE.5.7 negative).
- README rewrites beyond the named "before public flip" block removal (HT-3).
- getting-started.md edits beyond the named "double-step-5" + minimal coherence (HT-3 / Surface #5).
- `~/.loam/` state mutations or cleanup (the AC.FBE.5.6 smoke is read-only verification of the post-`loam init` state; no `~/.loam/` reset).

---

## 5. Three-lens analysis

### Lens 1 — Claude-leverage-first
Pure documentation cleanup; no Claude-leverage shape change. Composes with FBE.6's reviewer-agent re-run (a Claude-leveraged operation) by removing the dev-vocabulary noise the reviewer would otherwise re-flag.

### Lens 2 — Harness + primary-persona value
- **Primary-persona test:** PASS. Removes vocabulary friction for the stranger reading the framework's surface; the persona's first-greet narrative isn't blocked by "what is `pOS v2`?" surprises in a `pip show <component>` output.
- **Harness test:** PASS (neutral). Doesn't add to the toolkit; doesn't remove from it.

### Lens 3 — ODD authoring
Outcome ACs only (§4); method (which exact replacement string for each leaky description) is the builder's call but constrained tight by AC.FBE.5.2's vocabulary table. No "options to rule on" framed in this plan-doc.

### Lens 4 — Prompt scope ↔ confidence
High confidence in outcome shape: dispatcher named the AC set + the vocabulary table + the smoke verification. Tight scope. Method is inferable from constraints.

### Lens 5 — Swarming
FBE.5 is a leaf in the foldback ladder. ACs do not partition further: each binds to a single observable surface (description string content, smoke verification, fence diff). No sub-decomposition; the 15 description edits aren't worth dispatching as parallel sub-agents (each is a single Edit call; coordination overhead exceeds tighter-AC payoff).

---

## 6. File-by-file map

### Pyproject `description` edits (in fence — sidecar bumps via `loam amend apply`):

| Component | Current description (leaky) | New description (per AC.FBE.5.2) |
|---|---|---|
| `framework/cost-governance/` | `Cost governance for pOS v2 — aggregate budget ceilings (money / tokens / time) with activation-gate wrap + sidecar ledger.` | `Cost governance for loam — aggregate budget ceilings (money / tokens / time) with activation-gate wrap + sidecar ledger.` |
| `framework/observability-aggregator/` | `pOS v2 observability aggregator — single-user local-first trace store. ...` | `loam observability aggregator — single-user local-first trace store. ...` (rest preserved verbatim; "v1.1 R10 retention-class" reference preserved — not amendment-numbering, refers to a future spec class). |
| `framework/orchestrator/` | `Session-resilient orchestrator for pOS v2 — asyncio process host, Unix-socket JSON-RPC, bind_scope dispatch layer, compaction-survival integration.` | `Session-resilient orchestrator for loam — asyncio process host, Unix-socket JSON-RPC, bind_scope dispatch layer, compaction-survival integration.` |
| `framework/objective-tracker/` | `Objective tracker primitive for pOS v2 — forest-of-trees with event-sourced persistence, sidecar scope binding, and ODD integration.` | `Objective tracker primitive for loam — forest-of-trees with event-sourced persistence, sidecar scope binding, and ODD integration.` |
| `framework/scope-of-work/` | `Scope-of-work primitive for pOS v2 — event-sourced FSM with budget governance, observers, and escalation triggers.` | `Scope-of-work primitive for loam — event-sourced FSM with budget governance, observers, and escalation triggers.` |
| `framework/safety-layer/` | `Safety layer for pOS v2 — three kill switches, always-ask list, dangerous-op gate.` | `Safety layer for loam — three kill switches, always-ask list, dangerous-op gate.` |
| `framework/primary-persona/` | `Primary-persona layer for pOS v2 — loader, background-work monitor, and autonomous authoring framework.` | `Primary-persona layer for loam — loader, background-work monitor, and autonomous authoring framework.` |
| `framework/reversibility-primitive/` | `Reversibility primitive for pOS v2 — compensation-path binding, rollback runtime, path-choice telemetry.` | `Reversibility primitive for loam — compensation-path binding, rollback runtime, path-choice telemetry.` |
| `framework/workspace-bootstrap/` | `pOS v2 workspace bootstrap — two-layer framework composing the ten foundational components into a running orchestrator + three-gate chain, plus the published Phase 4+ extension protocol.` | `loam workspace bootstrap — two-layer framework composing the foundational components into a running orchestrator + three-gate chain, plus the published plugin contribution protocol.` (Note: "ten foundational components" → "the foundational components" since v0.1.0 ships fifteen; or just drop the count.) |
| `framework/telegram-interface/` | `Telegram channel adapter for pOS v2 — consumes the Claude MCP Telegram plugin via adapter-pattern injection into OneOnOneChannel; supports multi-identity allowlist, availability probe, direct Bot API fallback, and session-two setup walkthrough. Zero sealed-component amendments.` | `Telegram channel adapter for loam — consumes the Claude MCP Telegram plugin via adapter-pattern injection into OneOnOneChannel; supports multi-identity allowlist, availability probe, direct Bot API fallback, and session-two setup walkthrough.` (Drop "Zero sealed-component amendments." trailing clause — internal-vocabulary leakage about how it was built.) |
| `framework/self-upgrade/` | `pOS self-upgrade framework — coordinates every sealed component's upgrade-fidelity surfaces into a single atomic operation enforcing the seven-clause acceptance (a–g)` | `loam self-upgrade framework — coordinates every sealed component's upgrade-fidelity surfaces into a single atomic operation enforcing the seven-clause acceptance (a–g)` (Replace `pOS` → `loam`; "sealed component" + "seven-clause acceptance" stay — they're concept names users may search for.) |
| `framework/self-correction/` | `Self-correction loop for pOS v2 — four-part protocol structurally enforced; consumer of safety + reversibility + cost gates.` | `Self-correction loop for loam — four-part protocol structurally enforced; consumer of safety + reversibility + cost gates.` |
| `framework/workspace-sync/` | `pOS v2 workspace-sync — canonical-to-workspace git-shaped sync (Architecture B) with three-class workspace-data envelope and LLM-mediated semantic-merge gate. Companion to self-upgrade (Architecture A canonical-only).` | `loam workspace-sync — canonical-to-workspace git-shaped sync with three-class workspace-data envelope and LLM-mediated semantic-merge gate. Companion to self-upgrade.` (Drop the "Architecture A/B" parentheticals — internal architectural-letter shorthand.) |
| `framework/tools/loam/` | `Unified loam top-level CLI; amend subcommand for amendment dispatch (post-M1g rename of pos-amend per loam-rename-decisions.md Tier-1 #6).` | `Unified loam top-level CLI; amend subcommand for amendment dispatch.` (Drop the parenthetical entirely.) |
| `plugins/dev-sdlc/` | `Dev/SDLC plugin for loam — methodology-shaped 5-stage workflow (research → spec → plan → build → review/verify) with structural gate enforcement, scope-of-work + objective-tracker integration, methodology opt-out preserving an internal ODD mirror, and the loam project ... CLI subcommand surface. First plugin under loam's contribution-based extension protocol; pattern-establishing for v0.2+ plugins.` | `Dev/SDLC plugin for loam — methodology-shaped 5-stage workflow (research → spec → plan → build → review/verify) with structural gate enforcement, scope-of-work + objective-tracker integration, methodology opt-out preserving an internal ODD mirror, and the loam project ... CLI subcommand surface. First plugin under loam's plugin contribution protocol; pattern-establishing for v0.2+ plugins.` (Substitute `contribution-based extension protocol` → `plugin contribution protocol` per Surface #6.) |

### Source code edits (in fence — `framework/tools/loam`):

- `framework/tools/loam/src/loam_cli/cli.py` lines 1-33 (module docstring): scrub all `M1g`, `M6a`, `M6b.1`, `loam-rename-decisions.md`, `oss-v0-1-0-publish-dev-sdlc-plugin.md`, `master plan AC.OSS-M6.15`, `D-build.M6.5`, `D-build.M6.15` references. Behaviour description (entry-point group `loam.cli.subcommands`, plugin discovery pattern, `amend` resolves through entry-points) STAYS.
- `framework/tools/loam/src/loam_cli/cli.py` lines 118-124 + 141-143 (in-function comments): same scrub. Behaviour comments STAY; amendment-number references GO.

### Doc-prose edits (universal-admitted files):

- `README.md` lines 52-58: REMOVE the "Note on the CLI name during the v0.1.0 release sequence" block entirely. Surrounding prose (lines 47-50 + line 60) reads coherently.
- `docs/getting-started.md` line 41: `## Five-step bootstrap` → `## Six-step bootstrap`.
- `docs/getting-started.md` line 43: `The whole walkthrough is five shell commands. Run them in order.` → `The whole walkthrough is six shell commands. Run them in order.`
- `docs/getting-started.md` line 113: `### 5. Try a first turn` → `### 6. Try a first turn`.

### Sidecar bumps within sealed-component fence (15 total):

For each of the 15 fence components: `<comp>/tests/SEAL_COMMIT` advances to FBE.5 seal SHA via `loam amend seal`; `<comp>/tests/test_no_sealed_amendments.py` BASELINE literal bumps via `loam amend apply`. Narrative file at `framework/workspace-bootstrap/tests/SEAL_COMMIT.notes` (single narrative target per FBE.4 precedent — multi-fence bumps share one narrative anchor).

### Plan-doc + manifest (universal_paths.prefixes: `docs/rebuild/plans/`):

- `docs/rebuild/plans/v0-1-0-foldback-scope-expansion-fbe5.md` (this file).
- `docs/rebuild/plans/v0-1-0-foldback-scope-expansion-fbe5.manifest.yaml`.

### Parent plan-doc backfill (post-seal, separate commit):

- `docs/rebuild/plans/v0-1-0-foldback-scope-expansion.md` — §8 method-decision register: replace `### FBE.5` placeholder with apply commit SHA + seal commit SHA + verification summary.

**TOTAL fence diff:** 15 description edits (one line each, except `workspace-bootstrap` + `telegram-interface` + `workspace-sync` + `tools/loam` + `dev-sdlc` which carry larger one-liners with parenthetical drops); 1 cli.py docstring/comments scrub; 30 sidecar bumps (15 SEAL_COMMIT + 15 BASELINE literals); 1 SEAL_COMMIT.notes narrative; 2 universal-admitted files (README.md + docs/getting-started.md); plan-doc + manifest YAML + parent plan §8 backfill (universal prefix).

---

## 7. Smoke verification

**Smoke (AC.FBE.5.6):**

```
# Pre-cleanup: capture current ~/.loam/ state
ls ~/.loam/ > /tmp/dot-loam-before-fbe5.txt

# Smoke proper
rm -rf /tmp/test-fbe5-ws
/Users/lukeivers/ivers-corp-pos-v2/.venv/bin/loam init /tmp/test-fbe5-ws \
    --from /Users/lukeivers/ivers-corp-pos-v2/
echo "Exit: $?"

# Verify scaffolded structure
ls /tmp/test-fbe5-ws/framework/ /tmp/test-fbe5-ws/workspace/ /tmp/test-fbe5-ws/.claude/

# Verify ~/.loam/ scaffolding (post vs pre — additive, never destructive)
ls ~/.loam/ > /tmp/dot-loam-after-fbe5.txt
diff /tmp/dot-loam-before-fbe5.txt /tmp/dot-loam-after-fbe5.txt || true

# Cleanup
rm -rf /tmp/test-fbe5-ws
```

Expect:
- `loam init` exits 0.
- `/tmp/test-fbe5-ws/{framework,workspace,.claude}` all exist.
- `~/.loam/` either gains entries (if `bootstrap_new_workspace` writes a per-host marker on this run) or stays unchanged (if entries from prior dev-machine activity already cover it). Either is AC-passing — the AC is "exists with expected scaffolding", not "newly scaffolded" (the dev machine's `~/.loam/` has been scaffolded many times by prior runs).

**Failure modes:**
- `loam init` exits non-zero → FBE.1 regression. Halt; surface; do not iterate. Per parent plan FBE.5 halt-trigger #2: "loam init smoke fails → FBE.1 has a regression; halt and feedback to FBE.1."
- `/tmp/test-fbe5-ws/framework/` missing → clone step failed. Halt.
- `~/.loam/` doesn't exist post-invocation (and didn't exist pre-invocation) → `bootstrap_new_workspace` contract violated. Halt.

The smoke can run pre-seal OR post-seal — pre-seal exercises the canonical tree; post-seal re-exercises against the seal-bumped tree. Either is sufficient for AC.FBE.5.6 (description scrubs + doc edits don't touch `loam init` runtime). **Run pre-seal** to catch any FBE.1 regression early; if it passes, no need to re-run post-seal.

---

## 8. Hard constraints

- 15 sealed-component sidecars in fence. **Single-line description edits per pyproject; no logic edits anywhere.**
- No new external runtime deps.
- No `git commit --amend` per `feedback_no_amend_in_agent_dispatches`.
- `loam amend apply` invoked BEFORE seal commit per `feedback_dispatch_explicit_pos_amend_apply`.
- AC-prefix `AC.FBE.5.*` (collision-safe).
- Auto-memory `MEMORY.md` NOT touched.
- Component-scoped test rerun per `feedback_amendment_dispatch_speedups`: only the touched fence components' test suites must pass post-seal. The smoke (AC.FBE.5.6) is exercised manually pre-seal; no in-tree pytest covers it directly (it spans a fresh-shell `loam init` invocation against canonical).
- Per Surface #3 (FBE.4 partner-prefix gap): expect potential corrective hand-admit if `loam amend seal` fails on a fence component's fence test with `plugins/dev-sdlc/`-prefix paths.

---

## 9. Out of scope (per ODD §2.5)

- Dev-only tool pyproject `description` scrubs (Surface #1; FUTURE_IDEAS_DRAFT candidate).
- Behaviour code edits anywhere (AC.FBE.5.7 negative AC).
- README rewrites beyond the named "before public flip" block removal.
- getting-started.md edits beyond the named "double-step-5" + minimal coherence (header + intro sentence).
- `~/.loam/` reset / cleanup / verification beyond the AC.FBE.5.6 smoke read.
- `dormancy` and `loam-init` pyproject edits (Surface #2 — already clean).
- `hands-off-lifecycle` "pyproject edits" (no pyproject.toml; config-only component).
- v0.2 PyPI publish (FBE.4 deferred; FUTURE_IDEAS).

---

## 10. Halt-and-surface (during build)

Per `feedback_subagent_odd_violation_halt` — halt + surface (do not silently extend) on:

- **HT-1:** A description-scrub edit changes the SUBSTANCE of what the component does (not just vocabulary). Per parent plan FBE.5 halt-trigger #1. Halt; surface the substance change candidate; do not silently rewrite product description.
- **HT-2:** `loam init` smoke (AC.FBE.5.6) returns non-zero. Per parent plan FBE.5 halt-trigger #2. Halt; surface; FBE.1 regression candidate.
- **HT-3:** README rewrite drifts beyond the named "before public flip" block removal (e.g. tempted to also fix typos elsewhere, restructure paragraphs, etc.). Per parent plan FBE.5 halt-trigger #3. Halt; surface; ODD §2.5 violation. Same applies to getting-started.md beyond the named LOW 1 fix + minimal coherence (header + intro sentence — Surface #5).
- **HT-4:** `loam amend apply` rejects the manifest. Halt; surface; the manifest's `components` shape may need adjustment (e.g. one of the 15 components is not a recognised seal anchor).
- **HT-5:** `loam amend seal` rejects the seal. Halt; surface; usually means a touched-file lives outside the fence + universal admissions, OR partner-prefix gap per Surface #3 (apply corrective hand-admit per FBE.4 precedent `0c4d9a0` — single-file edit to the offending fence-test's `allowed_prefixes`).
- **HT-6:** A pyproject in any of the 15 fenced components has an unrelated edit detected post-seal (`git diff BASELINE..SEAL_COMMIT -- <pyproject>` shows non-description-line changes). Halt; surface; AC.FBE.5.7 violation; revert the unrelated change.
- **HT-7:** A component's pyproject `description` is so leaky that the post-scrub version reads as a substance change (e.g. removing dev-vocabulary leaves a meaningless stub). Halt + surface; let the dispatcher rule whether to defer.
- **HT-8:** Surrounding-code ODD §2.5 violation discovered in any touched file (e.g. a `pyproject.toml` body comment that's unrelated to the description but blatantly out-of-scope). Halt; surface; do NOT silently extend or fix in-band.
- **HT-9:** Wall-time exceeds 60 min (dispatch hard cap). Halt with partial findings.
- **HT-10:** WD drifts to pos3. Halt immediately.
- **HT-11:** Sealed-component fence breach beyond the 15 plan-named components. Halt; surface.

---

## 11. Risks

- **Risk: `~/.loam/` already populated from prior dev-machine activity.** AC.FBE.5.6 verification can't tell "newly scaffolded" from "previously scaffolded" without a state-clear, which would damage the dev machine. **Mitigation:** AC.FBE.5.6 verification is "exists with expected scaffolding", not "newly created"; pre/post `ls` diff is informational only.
- **Risk: A fence component's pyproject has been edited recently in a way that introduces NEW leakage (test-data, sidecar metadata, etc.) that the survey didn't catch.** Mitigation: re-run the survey grep at build time before the edit pass; if a NEW leak surfaces, halt-and-surface (HT-7).
- **Risk: `loam amend apply` dispatcher behaviour changed since FBE.4.** Mitigation: the prior FBE.{1,2,3,4,7} apply ladder is empirical evidence the tool works for multi-fence amendments; the partner-prefix gap is the only known issue (Surface #3) and has a known corrective recipe (FBE.4 `0c4d9a0`).
- **Risk: 15 sidecar bumps + 15 BASELINE literal bumps + 1 narrative is more bookkeeping than the apply tool has exercised in a single run before.** The largest prior fence was FBE.4 (3 components). Mitigation: if the apply tool times out or surfaces an unexpected error, halt-and-surface; do not iterate without analysis.
- **Risk: README block removal leaves stylistic discontinuity.** Mitigation: manual inspection of the cross-block prose flow post-edit; if the discontinuity is jarring, surface for dispatcher review (do not iterate the README beyond the AC).

---

## 12. Sequencing (commit ladder)

1. **Plan-doc commit** (this file authored alone, NEW commit).
2. **Pre-seal smoke verification** (AC.FBE.5.6) — run before any source edit to catch FBE.1 regressions early. If fails → HT-2 halt.
3. **Source-side delta commit** — single commit covering: 15 pyproject `description` edits + `cli.py` docstring + `cli.py` comments + README block removal + getting-started.md three-edit coherence fix.
4. **Manifest commit** — author `docs/rebuild/plans/v0-1-0-foldback-scope-expansion-fbe5.manifest.yaml` (15 components in `components:` block).
5. **`loam amend apply`** — invoke against the manifest. Produces apply-bookkeeping commit (BASELINE bumps in 15 components' `test_no_sealed_amendments.py`; sidecar `SEAL_COMMIT` files advance).
6. **`loam amend seal`** — produces deterministic seal commit; sidecar `SEAL_COMMIT` files advance to seal SHA; narrative file written at `framework/workspace-bootstrap/tests/SEAL_COMMIT.notes`.
   - **If seal fails on partner-prefix gap (Surface #3):** apply corrective hand-admit per FBE.4 recipe (`0c4d9a0`) — edit the offending fence-test's `allowed_prefixes` to add `plugins/dev-sdlc/` (or whichever prefix the apply tool missed); commit; re-run seal.
7. **Parent plan-doc backfill** — `docs/rebuild/plans/v0-1-0-foldback-scope-expansion.md` §8 backfill `### FBE.5` subsection with apply + seal SHAs (separate NEW commit; admitted via `docs/rebuild/plans/` universal prefix).
8. **Status file write** — `/Users/lukeivers/pos3/workspace/.scratch/claude-output/fbe5-status-2026-05-03.md` with seal report.

NO `git commit --amend` at any point. NO push to any remote.

---

## 13. References

- **Parent plan:** `docs/rebuild/plans/v0-1-0-foldback-scope-expansion.md` (§4 FBE.5 row).
- **FBE.4 status (partner-prefix gap precedent):** `<workspace>/.scratch/claude-output/fbe4-status-2026-05-03.md` Surface #5.
- **FBE.4 sub-plan / manifest YAML (multi-component fence shape precedent):** `docs/rebuild/plans/v0-1-0-foldback-scope-expansion-fbe4.{md,manifest.yaml}` — fence-three-no-edit shape; this FBE.5 sub-plan extends to fence-fifteen-with-edit.
- **Memory bullets honoured:**
  - `feedback_plan_before_code` (this is the plan; no code yet).
  - `feedback_no_amend_in_agent_dispatches` (commit ladder uses NEW commits only).
  - `feedback_dispatch_explicit_pos_amend_apply` (apply step explicit in §12).
  - `feedback_subagent_odd_violation_halt` (HT-1 through HT-11).
  - `feedback_amendment_dispatch_speedups` (test rerun scoped to fence components only).
  - `feedback_summarize_and_surface_decisions` (Surfaces 1–6 explicit; each surfaces a decision the dispatcher could review).
  - `feedback_specific_claims_verified_or_marked_guess` (every "verified at planning" claim has a path/line citation).
  - `feedback_critical_thinking_on_deviations` (Surface #1 + Surface #4 + Surface #5 enumerate alternatives weighed by outcome × cost × risk).

---

## 14. AI-time band

- Predicted: **20–40 min, midpoint 30 min**; dispatch hard cap 60 min.
- Justification: 15 small pyproject edits (1 line each) + 1 cli.py docstring + 1 cli.py comment scrub + 1 README block removal + 3 getting-started.md edits + manifest YAML + smoke verification + apply + seal (15 sidecar bumps — never tested at this scale) + possible corrective + parent §8 backfill + status file. Per rubric: amendment-build (multi-component-aware fifteen-fence single-edit-per) → 20–45 min midpoint 32; tighten lower bound to 20 because per-edit cost is minimal (single-line replacements); upper bound 40 because the 15-component apply is the largest fence ever exercised and may surface tooling gaps.

---

## 15. Method-decision register (post-build)

(Populated as commits land.)

- Plan-doc commit: `<TBD>`.
- Source-side delta commit: `<TBD>`.
- Manifest commit: `<TBD>`.
- Apply commit: `<TBD>`.
- Corrective commit (if needed): `<TBD>`.
- Seal commit: `<TBD>`.
- Parent plan-doc §8 backfill commit: `<TBD>`.

---

*End of FBE.5 sub-plan-doc. Ready to build.*
