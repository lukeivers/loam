# workspace-sync — Bundle β: ergonomics (close "normal person can use pos" gap) — plan

Dev-discipline work. Bundle β bundles three independent ergonomics
ACs (β.1 / β.2 / β.3) that close the gap between "milestone-closed,
expert-only" (post-#57 state) and "non-tech operator can install pos,
create a workspace, and run subsequent syncs with no flags." β.1 +
β.2 are dev-discipline (touch `workspace-sync/` config-load surface
+ a NEW small component for the bootstrap; **NOT** sealed-component
amendments under the dispatch's framing). β.3 is plausibly
sealed-component-shaped (it adds packaging machinery). Plan-author
recommends in §11 D-β.4 that the bundle ship as **three separate
amendments** rather than one (reasoning + recommendation locked
post-§11). Plan-before-code per the dev CDC; corrective new commits
land each AC.

**Status:** plan (pre-dispatch). 2026-04-27.
**Working directory:** /Users/lukeivers/ivers-corp-pos-v2/
**Companions:**
- **#56 plan-doc** (parent — keystone workspace-sync component, defines `pos-sync` CLI surface + `~/.pos/sync-config.yaml` reference): `docs/rebuild/plans/workspace-sync.md`
- **#57 plan-doc** (Bundle α — just sealed; reference §11 for the existing config-file shape pattern): `docs/rebuild/plans/workspace-sync-resolver-cost-overhaul.md`
- **VALUE_PROPOSITION** (binding spec — AC.PO.1 translation-burden + AC.PO.2 toolkit-primitive growth): `docs/rebuild/VALUE_PROPOSITION.md`
- **`workspace-sync/src/workspace_sync/cli.py`** — current `pos-sync` argparse; β.1 attach point (workspace-root derivation already exists; β.1 extends with config-file lookup before `--canonical` is required)
- **`workspace-sync/src/workspace_sync/_resolver_client.py`** — references `~/.pos/sync-config.yaml` (line 292); β.1 wires the schema-validated load path
- **`self-upgrade/src/self_upgrade/cli.py`** — current `pos` console_script entry (`self_upgrade.cli:main`). Sealed component; β.2 must NOT touch it (Hard Constraint #2 below). Drives the β.2 outcome-shape decision (D-β.2: separate `pos-new-workspace` console_script rather than `pos` subcommand).
- **`workspace-bootstrap/src/workspace_bootstrap/adapters/first_run_scaffold.py`** — workspace-bootstrap's first-run plumbing (sealed). β.2 invokes its public API but does not edit it.
- **`workspace-sync/pyproject.toml`** — current console_script declarations (`pos-sync`, `pos-workspace-sync`); β.2's new console_script (`pos-new-workspace`) lands here OR in a NEW `tools/pos-new-workspace/` (D-β.1 method-decision; out of scope for this plan).
- **FUTURE_IDEAS_DRAFT** "Workspace-sync follow-on family" lines 14-31 (KK / LL / MM captures): `docs/rebuild/FUTURE_IDEAS_DRAFT.md`
- **Dialog-context-dossier** (recent context, milestone-closure status): `/Users/lukeivers/pos3/.scratch/claude-output/dialog-context-dossier.md`

**Ancestor record:**
- **#56 (workspace-sync keystone) sealed `0607dc7`** — established `pos-sync` CLI + `<workspace>/.pos/sync-protected.yaml` envelope + reference to a `~/.pos/sync-config.yaml` user-tunable knob.
- **#57 (Bundle α resolver cost overhaul) sealed `e619b6a`** — established the parallel-config pattern (workspace-local + ~/-rooted) for budget defaults via the same config-file family; verified end-to-end against pos3 (46 conflicts → 46 resolved → success in 1656 tokens, 2026-04-27).
- **Owner D-A1 ruling 2026-04-26** — Architecture A is locked for the `pos` CLI binary itself (binary-swap pattern P2). β.3 (global install path) ladders to D-A1; β.1 + β.2 sit below D-A1 and are framework-code (Architecture B).
- **Owner broad-autonomy directive 2026-04-26** — primary persona may rule on confidence-delegated decisions on Luke's behalf through the milestone window. The recommendations in §11 are pre-locked candidates; owner ruling explicitly requested for D-β.1 / D-β.2 / D-β.3 / D-β.4 (the four outcome-shape questions in §11).
- **No prior precedent inside pos-v2 for a curl-bash installer or a pipx-installable package**. β.3 introduces the FIRST install-path mechanism for pos. The component fence + Architecture A boundary are clean; the open question is which install path (D-β.3).

**Research:** No new research dispatched ahead of this plan. The companion documents above carry the locked decisions this plan composes against; no surface remained genuinely uncertain that warranted a research dispatch. (Plan-author considered dispatching research on "curl-bash vs pipx vs homebrew" for D-β.3; ruled against because the trade-off space is small + well-documented in upstream-tool docs, captured inline in §11 D-β.3 instead.)


---

## 1. Summary / TLDR

Three internal ACs that, together, close the "install once, `pos new-workspace`, `pos-sync` no args" non-tech-operator path:

1. **β.1 KK — workspace canonical-source config; `pos-sync` no-args from inside a workspace.** Today `pos-sync --canonical <path>` is required every invocation; the operator has to know + type the canonical path. β.1 adds a workspace-local `<workspace>/.pos/sync-config.yaml` whose `canonical_source:` field stores either a URL or a local path. `pos-sync` (with no `--canonical` flag) reads cwd → looks up `.pos/sync-config.yaml` → reads `canonical_source` → uses it (cloning to a cache dir if URL form). Composes with #57's existing `~/.pos/sync-config.yaml` schema (budget defaults) — same Pydantic config-file family, just adds workspace-local override + the new field. CLI flag remains backward-compatible (`--canonical <path>` continues to work + override).

2. **β.2 LL — `pos-new-workspace --from <repo>` bootstrap.** Solves the chicken-and-egg: under Architecture B a fresh workspace has no framework code yet. `pos-new-workspace ~/my-workspace --from https://github.com/lukeivers/pos-v2` (or a local path) clones canonical, embeds framework via `pos-sync` against the freshly-cloned canonical, writes `<new-ws>/.pos/sync-config.yaml` with `canonical_source:` pre-populated. Composes with β.1 + workspace-bootstrap's existing first-run plumbing. Plan-author recommends shipping as **a new console_script `pos-new-workspace`** (lives in workspace-sync OR in a new sibling `tools/pos-new-workspace/`) rather than a subcommand of `pos` — same hyphenation convention #56 used for `pos-sync`, avoids editing sealed `self-upgrade/cli.py`. D-β.2 surfaces this for owner ruling.

3. **β.3 MM — global install path for `pos` and `pos-sync`.** Today both binaries live only in canonical pos-v2's `.venv` — nothing on PATH for a normal user. β.3 ships **one** install-path mechanism so a non-tech operator can `<one-liner>` and end up with `pos`, `pos-sync`, and `pos-new-workspace` on PATH. Three options surface in D-β.3: curl-bash installer / pipx-installable package / homebrew formula. Plan-author recommends **pipx + a thin curl-bash wrapper** (`curl ... | bash` calls pipx install under the hood). Aligns with D-A1 ruling (Architecture A for the CLI binary).

**Hard Constraint #1 (binding from dispatch).** Bundle β does NOT regress the milestone-closure mechanism (#56 + #57). `pos-sync --canonical <path> --workspace <path>` continues to work for users without `<workspace>/.pos/sync-config.yaml`. β.1 is purely additive: when the file is absent, the CLI falls through to today's behaviour byte-for-byte. No edits to workspace-sync's resolver internals (just sealed under #57).

**Bundle splitting recommendation (D-β.4).** β.1 and β.2 are independent; β.3 depends on neither. Plan-author recommends shipping as **three separate amendments** (β.1 first as dev-discipline; β.2 second as dev-discipline OR sealed-component depending on D-β.2 ruling on placement; β.3 third as sealed-component if it adds packaging machinery + a new top-level component, else dev-discipline). Reasoning + alternate (one-bundle) trade-off captured in §11 D-β.4.

**This is dev-discipline scope.** Plan-author authors three plan-docs (one per AC) IF owner rules to split per D-β.4 recommendation; OR this plan-doc covers the bundle and three builder-plans land per §14. Decision routes through D-β.4. No new top-level objective.


---

## 2. Spec-objective placement (per CLAUDE.md §2.5 framing)

Bundle β composes under **VALUE_PROPOSITION's AC.PO.1 (translation-burden absorption)** and **AC.PO.2 (toolkit-primitive growth)** — the prime objective per CLAUDE.md §2.5. **No new top-level objective is required.** Halt trigger 1 evaluated: does not fire.

**Reverse trace per CLAUDE.md §2.5.** Every AC traces back to AC.PO.1 + AC.PO.2:

- **AC.PO.1 (translation-burden):** The operator says "pull the latest." Persona translates to `pos-sync` with no flags. Today, the persona has to translate to `pos-sync --canonical /Users/lukeivers/ivers-corp-pos-v2 --workspace /Users/lukeivers/pos3` — every invocation. Post-β.1, the persona translates to `pos-sync` only (cwd derivation + workspace-local config does the rest). **β.1's translation-burden absorption is the headline win.**

  Similarly AC.PO.1 governs β.2: "create a new workspace" today translates to a 6-step manual recipe (create directory, clone canonical to a known location, run pos-sync, hand-author `.pos/sync-config.yaml`, etc.). Post-β.2, "create a new workspace" translates to one verb: `pos-new-workspace ~/my-ws --from <canonical-url>`.

  And β.3: "install pos" today translates to "clone pos-v2, create a venv, `pip install -e .` in five places, source the venv every time you want to use the binary." Post-β.3, "install pos" translates to one one-liner (pipx + curl-bash wrapper). The non-tech operator never learns about virtualenvs, editable installs, or PATH-shadowing.

- **AC.PO.2 (toolkit-primitive growth):** Bundle β adds three primitives the persona composes against:
  1. **Workspace-local sync-config.yaml** — Pydantic-validated, schema-versioned, framework-floor-aware. Future tooling (workspace-export, workspace-clone, multi-workspace orchestration, workspace-state diagnostics) composes on the same envelope. Schema lives in workspace-sync; consumers across pos-v2 read via the public API.
  2. **`pos-new-workspace` bootstrap primitive** — invocable by the persona on the user's behalf when an operator says "set me up a new workspace for the photography client." The primitive composes with workspace-bootstrap's first-run plumbing (no edits to it; β.2 calls its public API after the embed completes).
  3. **Global install primitive (pipx + curl-bash wrapper or equivalent)** — a stable invocation surface that survives across machine-rebuilds. Future plugin-ecosystem tooling (per D-A1 Architecture A for the CLI binary) composes on the same install footprint.

**Halt note.** Plan-author considered surfacing a "new top-level objective" halt (per dispatch trigger 1) and ruled against. Bundle β is mission-shape under VALUE_PROPOSITION's two existing tests; no new outcome-axis appears. The work is "absorb translation chores the operator currently does manually" — exactly what AC.PO.1 names. Halt-trigger 1 does not fire.


---

## 3. Three-lens analysis (per CLAUDE.md design lenses)

### Lens 1 — Claude leverage

Composes on Claude-native primitives without inventing new ones:

1. **Slash-command + skill primitives.** Future amendment may wrap β.2's `pos-new-workspace` as a `/new-workspace <handle>` slash-command for direct persona-invokability when the operator's natural-language intent is unambiguous ("set me up a new workspace for X"). Out of scope for β; unlocked by it. Composes on Claude Code's slash-command surface.
2. **MCP server discovery via `<workspace>/.mcp.json`.** β.2 must populate (or trigger workspace-bootstrap's mcp_json_writer to populate) the new workspace's `.mcp.json` so the new workspace's first claude session has memory-graphiti + telegram MCP configured. Composes on amendment #47's existing mcp_json_writer adapter — no new MCP registration mechanism.
3. **`claude --add-dir <path>` for the new workspace.** β.2 may emit a one-liner the operator runs to attach the freshly-bootstrapped workspace to their next claude session. Composes on Claude Code's existing `--add-dir` flag rather than inventing a hand-off mechanism.
4. **No new LLM call surface.** None of β.1 / β.2 / β.3 invokes Claude. β.1 is a config-file load. β.2 is a clone + delegate-to-pos-sync + delegate-to-workspace-bootstrap. β.3 is a packaging mechanism. **Halt trigger 5 (LLM surface that doesn't exist) does not fire** — bundle β composes on file I/O + subprocess + git, no LLM.
5. **Cost-governance.** β.1 reads the existing budget schema (workspace_tunable per #57) and inherits the four-gate primitive without modification. No new cost mechanism.
6. **Plugin / skill / MCP cache delegation (ruling A3).** β.2's freshly-bootstrapped workspace's `~/.claude/{plugins,skills}/` cache is Claude Code's responsibility. β.2 does NOT attempt to seed it. The new workspace's `.mcp.json` IS Class A in the protected envelope; β.2 writes the default and never overwrites afterward.

### Lens 2 — Harness + primary-persona value

**Primary-persona test.** Reduces translation burden across all three ACs (detail per AC in §2 above). The headline: a non-tech operator's "pull the latest" / "create a new workspace" / "install pos" each become a single verb instead of a six-step recipe. **Pass on all three ACs.**

**Harness test.** Adds three primitives to the persona's toolkit (workspace-local sync-config.yaml, pos-new-workspace bootstrap primitive, global install primitive — listed in §2 above). Each is invocable by the persona; each is durable across sessions. **Pass on all three ACs.**

Per AC trace:
- **AC.β.1 → AC.PO.1 + AC.PO.2.** Translation-burden absorbed (no `--canonical` to type). Toolkit primitive added (workspace-local sync-config.yaml).
- **AC.β.2 → AC.PO.1 + AC.PO.2.** Translation-burden absorbed (one verb instead of six steps). Toolkit primitive added (pos-new-workspace bootstrap surface).
- **AC.β.3 → AC.PO.1 + AC.PO.2.** Translation-burden absorbed (one-liner install). Toolkit primitive added (global install path; substrate for future plugin-ecosystem tooling).

### Lens 3 — ODD authoring

Each AC below is outcome-shaped; method is the builder's call within the AC's bounds. The §11 named decisions are **outcome-shape** decisions for owner ruling (where does the cache-clone live, which install path, where does the bootstrap subcommand live). The §14 method-decision register is the post-build record per amendment #46/#47/#54/#56 precedent.

**Behaviour-count check** in §5 below: 3 declared behaviours, 3 ACs, no implicit-untested code. (No seal-diff invariant — bundle β is dev-discipline; if D-β.4 routes any AC to sealed-component shape, that AC's plan-doc gains a §14 register skeleton + AC.β.x.S seal-diff invariant.)


---

## 4. Acceptance criteria (AC.β.x — bundle β; dev-discipline plan)

Three outcome-shaped acceptance criteria. Each carries the deterministic test shape; method is the builder's call. AC numbering uses `AC.β.1 / AC.β.2 / AC.β.3` per the dispatch's "AC numbering at builder's call within β.x convention" guidance.

**AC.β.1 — Workspace canonical-source config; `pos-sync` no-args from inside a workspace.** When `<workspace>/.pos/sync-config.yaml` exists and contains a `canonical_source:` field (URL or absolute local path), invoking `pos-sync` (no `--canonical` flag) from inside the workspace (cwd inside the workspace OR `--workspace <path>` supplied) reads the field, resolves it (clone-to-cache for URL, use-direct for local path), and proceeds with the existing #56 + #57 sync flow. The workspace-local config file is Pydantic-validated on every load; missing required fields raise schema error; unknown fields raise via `extra="forbid"` (per the existing #56 pattern). When `--canonical <path>` IS supplied, it overrides the config-file value (CLI flag wins; per the existing flag-vs-config-file precedence convention). When neither the file's `canonical_source:` field NOR the `--canonical` flag is supplied, the CLI halts with a structured argument-validation error naming both fall-through conditions.

  **Backward-compat (Hard Constraint #1, binding):** A workspace WITHOUT `<workspace>/.pos/sync-config.yaml` (or with the file present but `canonical_source:` absent) sees byte-identical behaviour to today's `pos-sync`: `--canonical <path> --workspace <path>` continues to work; absence of either flag halts as today. Verified by a fixture: pos3-shape workspace with the file ABSENT runs `pos-sync --canonical <p>` and produces identical exit code + audit shape to today.

  **Cache-clone location (D-β.1, surfaced for owner ruling):** When `canonical_source:` is a URL, the clone target is `~/.pos/canonical-cache/<repo-id>/` (recommendation; D-β.1 detail in §11). The cache is workspace-shared (multiple workspaces with the same canonical source share one cache); per-workspace state stays workspace-local. `git fetch` runs on every invocation to update the cache; the resolved ref is honoured per #56's existing `--ref` semantic.

  **Schema additions (workspace-local + ~/.pos/ shared):** `<workspace>/.pos/sync-config.yaml` and `~/.pos/sync-config.yaml` share a Pydantic schema (current fields from #57: `cumulative_token_budget`, `per_conflict_token_budget`, etc.; new: `canonical_source: str | None = None`). Workspace-local file overrides ~/-rooted file (precedence: CLI flag > workspace-local file > ~/-rooted file > schema defaults). The shared schema lives in workspace-sync; both files validate against the same model.

  **Verified by:** fixture-1 (workspace WITH `canonical_source: <local-path>` → `pos-sync` no-args succeeds); fixture-2 (workspace WITH `canonical_source: <git-url>` → clone-to-cache succeeds + sync runs against cache); fixture-3 (workspace WITHOUT the file → `pos-sync` no-args halts with structured error naming both fall-through conditions); fixture-4 (workspace WITHOUT the file + `--canonical <p>` → byte-identical behaviour to today); fixture-5 (CLI flag overrides config file); fixture-6 (workspace-local file overrides ~/-rooted file).

**AC.β.2 — `pos-new-workspace --from <repo>` bootstrap command.** Invoking `pos-new-workspace <workspace-path> --from <canonical-source>` (where `<canonical-source>` is a git URL OR a local absolute path):

  1. Creates `<workspace-path>` if it does not exist (refuses if it exists and is non-empty; structured error).
  2. Clones canonical to `~/.pos/canonical-cache/<repo-id>/` (or uses existing local path if `<canonical-source>` is local).
  3. Embeds framework into `<workspace-path>` by internally invoking the `pos-sync` flow against the freshly-cloned (or local) canonical (this is the chicken-and-egg resolution: pos-new-workspace IS pos-sync, just with a freshly-seeded workspace as the target). The first-run path's "no `<workspace>/.pos/sync-protected.yaml` exists yet → seed default" branch (AC.WS.10 from #56) handles the absence-of-envelope.
  4. Writes `<workspace-path>/.pos/sync-config.yaml` with `canonical_source: <canonical-source>` (URL or absolute path, normalised per the schema).
  5. Optionally invokes workspace-bootstrap's first-run scaffold via its public API (no edits to workspace-bootstrap/) so the new workspace gets `.mcp.json`, persona scaffold, tracker DB seeding, etc., per amendments #36 / #39 / #47 etc. (D-β.2-detail in §11: whether β.2 invokes workspace-bootstrap or whether the operator's first claude session triggers it).

  **Console_script placement (D-β.2, surfaced for owner ruling):** Plan-author recommends shipping `pos-new-workspace` as a NEW `console_script` declared in `workspace-sync/pyproject.toml` (sibling to `pos-sync`, `pos-workspace-sync`) OR in a new sibling `tools/pos-new-workspace/` package. **Both options avoid editing sealed `self-upgrade/cli.py`.** D-β.2 selects between them. Rejected option: making `pos new-workspace` a subcommand of the existing `pos` CLI — that requires editing `self-upgrade/src/self_upgrade/cli.py:build_parser` which is sealed (#54 + earlier seals). Halt-trigger 4 fires if the build agent attempts this without an owner ruling.

  **Verified by:** fixture-1 (fresh empty directory + valid local-path canonical → workspace exists with framework + .pos/sync-config.yaml + first-run scaffold artefacts); fixture-2 (fresh empty directory + valid URL canonical → cache-clone + workspace-bootstrap scaffold + canonical_source URL recorded); fixture-3 (target directory exists and is non-empty → structured refusal with no side effects); fixture-4 (network failure on URL clone → fail-closed with no partial workspace); fixture-5 (post-β.2 invocation, the new workspace runs `pos-sync` no-args successfully — composes with AC.β.1).

**AC.β.3 — Global install path for `pos`, `pos-sync`, `pos-new-workspace`.** A non-tech operator can run a single one-liner that ends with the three binaries on PATH. The mechanism (D-β.3, surfaced for owner ruling) is one of:

  - **(a) curl-bash installer.** `curl -sSL https://pos-v2.example/install.sh | bash` writes a self-contained bootstrap that creates `~/.pos/bin/`, clones canonical pos-v2 to `~/.pos/install/`, creates a `~/.pos/install/.venv`, installs the components in editable mode, and writes thin shim scripts at `~/.pos/bin/{pos,pos-sync,pos-new-workspace}` that exec from the venv. Adds `~/.pos/bin/` to PATH via `~/.zshrc` / `~/.bashrc` / `~/.profile`.
  - **(b) pipx-installable package.** Publish (or vendor) a pos-v2 meta-package to PyPI. Operator runs `pipx install pos-v2` (or `pipx install git+https://...`) and pipx handles isolation + PATH injection. Plan-author recommendation for D-β.3.
  - **(c) homebrew formula.** Publish a homebrew tap with a `pos-v2.rb` formula. Operator runs `brew install ivers-corp/pos/pos-v2`. Most polished UX on macOS; non-trivial maintenance burden + adds a downstream-package-store dependency.

  Plan-author **recommends (b) pipx + thin curl-bash wrapper** as the primary mechanism (pipx is the modern Python-CLI distribution standard; the wrapper handles `pipx install pipx` for users who don't have pipx). Detail in D-β.3 §11.

  **Aligns with D-A1 ruling 2026-04-26.** D-A1 locked Architecture A (binary swap) for the `pos` CLI binary itself. β.3's install path IS the binary-swap substrate: `pos`, `pos-sync`, `pos-new-workspace` live on PATH; their internals can be upgraded by re-running the install script (or `pipx upgrade pos-v2`); the install footprint is independent of any individual workspace's framework code (which is per-workspace under Architecture B).

  **Verified by:** an end-to-end test on a fresh CI VM (or equivalent isolated environment): run the install one-liner; assert `pos`, `pos-sync`, `pos-new-workspace` are on PATH; assert each binary's `--version` returns the expected version; assert `pos-new-workspace ~/test-ws --from <local-canonical>` succeeds; assert `cd ~/test-ws && pos-sync` succeeds. Out-of-band: a documented uninstall path (`pipx uninstall pos-v2` OR a `rm -rf ~/.pos/{install,bin}` recipe in the install script's preamble).

  **Component fence (D-β.5 inferred-locked, captured for builder reference):** β.3 lives at `tools/pos-installer/` (NEW component) OR `install/` at repo root. β.3 is potentially **sealed-component-shaped** (it adds packaging machinery + a stable user-facing entry point). D-β.4 routes whether β.3 ships as sealed-component-amendment vs dev-discipline.

**No AC.β.S (seal-diff invariant) at the bundle level** — bundle β is dev-discipline. If D-β.4 routes any AC to sealed-component shape, that AC's plan-doc gains a §14 register skeleton + per-AC seal-diff invariant.


---

## 5. Behaviour-count check (ODD §3.3 forward; applied as dev-discipline check)

Three declared behaviours; three outcome-shaped ACs. Match.

| # | Declared behaviour | AC |
|---|--------------------|-----|
| 1 | Workspace canonical-source config; `pos-sync` no-args | AC.β.1 |
| 2 | `pos-new-workspace --from <repo>` bootstrap | AC.β.2 |
| 3 | Global install path for pos / pos-sync / pos-new-workspace | AC.β.3 |

Forward direction (every behaviour → AC) verified above.
Reverse direction (every code path / branch / dependency → AC) is the builder's pre-build check captured in each AC's builder-plan §5.


---

## 6. Hard constraints

1. **Backward-compat preserved unconditionally for `pos-sync`** (Hard Constraint #1 from dispatch, binding). A workspace WITHOUT `<workspace>/.pos/sync-config.yaml` continues to work with today's `pos-sync --canonical <p> --workspace <p>` invocation byte-identically. β.1 is purely additive: when the file is absent, the CLI falls through to today's behaviour without any new code path executing. AC.β.1 fixture-3 + fixture-4 are the test-shaped form. No edits to workspace-sync's resolver internals (#56 + #57 just sealed; out-of-fence).

2. **No edits to sealed `self-upgrade/`** (binding). The existing `pos` CLI entry (`self_upgrade.cli:main`) is sealed. β.2's `pos-new-workspace` MUST land as a NEW console_script (in workspace-sync OR in a new `tools/pos-new-workspace/`), NOT as a subcommand of `pos`. D-β.2 routes the placement; halt-trigger 4 fires if the build agent attempts to add `new-workspace` as a `pos` subcommand. Reasoning: amendment #54 sealed self-upgrade; touching self-upgrade-cli is amendment-shaped + violates the dispatch's Hard Constraint.

3. **No edits to sealed `workspace-bootstrap/` or `workspace-sync/` runtime resolver internals.** β.1's config-file load wires INTO the existing `pos-sync` CLI flow at the workspace-root-derivation step (`derive_workspace_root` in `workspace-sync/src/workspace_sync/cli.py`). β.1 modifies the CLI surface (which is in-fence for an additive change since the CLI module's public-shape contract is the argparse surface, and #56's seal-diff invariant covers it). **Open question (D-β.6 captured for builder reference):** is "additive change to argparse + new config-file loader" inside workspace-sync's seal? Plan-author reads it as YES — the seal-diff invariant covers the COMMITTED diff between BASELINE and SEAL, not future amendments. β.1 lands as an amendment-window edit to workspace-sync; pos-amend manifest discipline applies. **If D-β.4 routes β.1 to dev-discipline, β.1 is NOT a seal commit** — but the changes still land inside workspace-sync's source tree, which means a later seal commit (e.g. β.4 or a future amendment) would need to admit the β.1 edits. **Recommendation (D-β.4):** ship β.1 as a sealed-component amendment to workspace-sync (a new `pos-amend` manifest + SEAL_COMMIT bump + seal commit per the standard pattern). Saves the future-admission work.

4. **No new third-party runtime dependency** for β.1 + β.2. β.1 is Pydantic + PyYAML (already deps of workspace-sync). β.2 is stdlib + git binary + invokes existing pos-sync as a subprocess (or as an in-process call). **β.3 may ship a NEW dep on pipx** if D-β.3 picks (b); pipx is a system-tool dep (not a package dep), so installed via the curl-bash wrapper rather than declared in pyproject. If a new `pyproject` runtime dep surfaces in β.3, halt-and-surface (§10 trigger 5).

5. **No `--amend`** (binding per `feedback_no_amend_in_agent_dispatches`). Corrective new commits only.

6. **Plan-before-code** (binding per `feedback_plan_before_code`). This plan exists. Each AC's builder authors a builder-plan at `docs/rebuild/plans/<ac-slug>.builder-plan.md` (or, if D-β.4 routes the bundle as a single amendment, at `docs/rebuild/plans/workspace-sync-ergonomics.builder-plan.md`) before editing source.

7. **Workspace data loss is structurally impossible** (carried over from #56 Hard Constraint #6). β.1 + β.2 do NOT touch the three-class envelope or the resolver internals. β.2 seeds a default `<workspace>/.pos/sync-protected.yaml` per AC.WS.10 from #56 (the existing first-run path); β.2 does NOT re-implement Class-A protection. β.1 reads the new `canonical_source:` field but does NOT loosen any framework-floor constraint.

8. **`pos-sync` config-file is a config layer, not a state layer.** `<workspace>/.pos/sync-config.yaml` carries USER-CONFIGURABLE preferences (canonical source URL, budget overrides, etc.). Workspace STATE (the audit log, state.yaml, sync-protected.yaml envelope, ancestor-cache.yaml) lives elsewhere per #56's AC.WS.5 + AC.WS.8. Don't conflate. AC.β.1's schema MUST keep these layers cleanly separated; the validator rejects any state-shaped field landing in sync-config.yaml.

9. **β.2's bootstrap is operator-confirming when the target is non-empty.** AC.β.2 fixture-3 verifies refusal-on-non-empty. The default behaviour is fail-closed; an `--overwrite` flag is OUT OF SCOPE for β (a future amendment may add it after empirical demand). Operators don't accidentally clobber an existing workspace.

10. **β.3's install path is reproducible across machines.** The install script (or pipx invocation) MUST produce a byte-identical install footprint given the same canonical pos-v2 commit + same target host OS family. Reproducibility is a soft constraint here — perfectly byte-identical may not be achievable across Python minor versions or different macOS major versions; the install script documents the required Python version + macOS version in its preamble.

11. **CDC adherence.** Scope-only-dispatch CDC (the dispatch carries objective + scope + halt + ODD-check; the builder authors method in the builder-plan). For each AC routed to sealed-component shape under D-β.4, standard pos-amend manifest discipline applies; `pos-amend seal --plan-doc <abs-path>` backfills §14 of that AC's plan-doc.

12. **No top-level objective added** (per dispatch + §2). Composition under VALUE_PROPOSITION's AC.PO.1 + AC.PO.2 only. If the build surfaces a hard need for a new top-level objective, halt-and-surface (§10 trigger 1) — do NOT silently promote.


---

## 7. Out of scope (explicit)

Per ODD §2.5 and the dispatch's locked scope:

- **β.4 PP — `--auto-accept` confidence-floor calibration.** Captured in FUTURE_IDEAS_DRAFT but explicitly excluded from the dispatch's scope ("Three internal ACs (locked scope; AC numbering at builder's call within β.x convention)"). Future bundle / future amendment.
- **`pos-sync --dry-run` UX bug fix.** Captured in FUTURE_IDEAS_DRAFT (workspace-sync follow-on family). Not in β.
- **β.2 multi-workspace orchestration / batch-create.** β.2 ships single-workspace bootstrap; multi-workspace orchestration (e.g. "create three workspaces and link them via shared canonical") is out of scope.
- **β.2 `--overwrite` flag.** β.2 fail-closes on non-empty target. Future amendment may add `--overwrite` after empirical demand.
- **β.2 in-process embed of workspace-bootstrap's first-run scaffold** vs **subprocess invocation.** Method-shape decision; the builder authors in §14 D-build.x. Plan-author surfaces a recommendation in §11 D-β.2-detail but the choice between import-and-call vs subprocess is method-shape.
- **β.3 windows / linux installers.** pos-v2 is currently macOS-only (workspace-bootstrap's `platform.system()` halts on non-darwin per `first_run_scaffold.py`). β.3 ships macOS install path only. Linux/Windows install paths are future amendments after pos-v2's core supports those platforms.
- **β.3 auto-update mechanism** (e.g. `pos self-update` or `pipx upgrade pos-v2` automation). Composes on β.3 but is a separate amendment.
- **β.3 pre-built binaries / PyInstaller bundles.** β.3 ships source-distribution + pipx; binary distribution (PyInstaller / shiv / pex) is future tuning.
- **β.3 telemetry / install-success reporting.** Composes on observability-aggregator but is a separate amendment.
- **Workspace-clone primitive** (`pos clone-workspace <src> <dst>`). Captured in #56 §7 as future amendment. β.2 ships *new* workspace bootstrap from a canonical, NOT cloning between workspaces. Out of scope.
- **Telegram-channel integration of `pos-new-workspace`.** Future composition with telegram-interface; β.2's exit code + structured stderr is the substrate; telegram bot wrapper is separate.


---

## 8. Implementation order (suggested — builder's call to refine)

Suggested order — builder's call to refine in each AC's builder-plan:

1. **D-β.4 ruling first (one-bundle vs three-amendment).** Owner rules whether β.1 / β.2 / β.3 ship as one bundled amendment or three separate. This routes the next step.

2. **β.1 first (smallest surface, biggest UX win).** β.1 is purely additive to the existing `pos-sync` CLI; it touches one or two files in workspace-sync; it has the highest leverage (every subsequent invocation is no-args). Suggested implementation order within β.1:
    - (a) Author the shared `SyncConfig` Pydantic schema in workspace-sync (or extend the existing schema if #57 already landed one — builder verifies pre-build); add `canonical_source: str | None = None`.
    - (b) Add a `load_sync_config(workspace_root: Path) -> SyncConfig` helper that walks workspace-local → ~/-rooted → schema-defaults.
    - (c) Modify `workspace-sync/src/workspace_sync/cli.py:main` to call `load_sync_config` before `--canonical` is required; populate `args.canonical` from the config if absent.
    - (d) Add fixture-tests per AC.β.1's verified-by list.
    - (e) Pos-amend manifest + SEAL_COMMIT bump (if D-β.4 routes β.1 to sealed-component shape).

3. **β.2 second (depends on β.1's config-file shape; otherwise independent).** β.2 is a new console_script; suggested order:
    - (a) D-β.2 ruling (workspace-sync's pyproject.toml vs new tools/pos-new-workspace/).
    - (b) Author the bootstrap module + entry-point.
    - (c) Wire the cache-clone path (D-β.1 from β.1).
    - (d) Wire the workspace-bootstrap first-run-scaffold invocation (D-β.2-detail: in-process vs subprocess).
    - (e) Add fixture-tests per AC.β.2's verified-by list.
    - (f) Pos-amend manifest + SEAL_COMMIT bump (if D-β.4 routes to sealed-component shape).

4. **β.3 third (independent of β.1 + β.2; can land in parallel; same-tree-serialize applies if any other amendment is in flight).** Suggested order:
    - (a) D-β.3 ruling (curl-bash / pipx / homebrew).
    - (b) Author the install script / package metadata.
    - (c) Validate on a fresh VM or container (the build agent's plan should specify the validation environment).
    - (d) Document the install one-liner in `README.md` (scope-fence: README is workspace-bootstrap-adjacent? Or is it repo-root scope? Plan-author reads it as repo-root scope, in-fence for β.3's component).
    - (e) Pos-amend manifest + SEAL_COMMIT bump (if D-β.4 routes to sealed-component shape).

5. **Live-test the full chain end-to-end** on a fresh machine (or a fresh VM): install via β.3's path → `pos-new-workspace ~/scratch-ws --from <local-pos-v2>` → `cd ~/scratch-ws && pos-sync`. Assert the full chain succeeds without any flag the operator has to type beyond the install one-liner + the `--from` argument.


---

## 9. Bookkeeping surface (per-AC plan-doc convention)

Per the dev-discipline plan-skeleton convention (per amendment #51 + plan template at `tools/pos-amend/tests/fixtures/plan-skeleton/`):

- **Plan-doc** (this file): `docs/rebuild/plans/workspace-sync-ergonomics.md`
- **Vars-file** (this plan's variables): `docs/rebuild/plans/workspace-sync-ergonomics.vars.yaml`
- **Builder-plans** (post-D-β.4 ruling): one OR three, depending on bundle-shape ruling.
  - One-bundle: `docs/rebuild/plans/workspace-sync-ergonomics.builder-plan.md`
  - Three-amendment: `docs/rebuild/plans/workspace-sync-ergonomics-beta1.builder-plan.md` + `...-beta2.builder-plan.md` + `...-beta3.builder-plan.md`
- **Manifests** (per sealed-component AC under D-β.4 ruling): `docs/rebuild/plans/workspace-sync-ergonomics.manifest.yaml` (or per-AC if split). Builder finalises.

**Salvage map.** β.1 reuses the existing `<workspace>/.pos/sync-protected.yaml` Pydantic-validation pattern from #56's `sync_protected.py`. β.1's new `SyncConfig` schema lives alongside (or extends) the existing config schema. β.2 reuses workspace-bootstrap's public API (no internal edits). β.3 has no salvage source — first-of-its-kind install path.

**Test surface.** Each AC's builder-plan §5 captures the per-AC test breakdown; plan-author estimates:
- β.1: ~6-10 unit tests (fixture-1 through fixture-6 listed in AC.β.1) + 1-2 integration tests.
- β.2: ~5-8 unit tests + 1-2 integration tests (fresh-directory bootstrap end-to-end).
- β.3: 1-3 fresh-environment integration tests + a small unit test on the install-script's argument parsing if it has flags.


---

## 10. Halt triggers (builder halts + signals owner)

Per `feedback_subagent_odd_violation_halt`: halt and surface any ODD violation OR scope drift.

1. **New top-level objective surfaces.** If during build an outcome appears that doesn't ladder under VALUE_PROPOSITION's AC.PO.1 + AC.PO.2, halt-and-surface — do NOT silently promote.

2. **ODD violation in surrounding code.** Pre-build sweep + during-build sweep of the touched files (workspace-sync/cli.py, workspace-sync/sync_protected.py if extended, any new files); if any ODD non-objective code, untested branch, or method-coupled AC text surfaces, halt-and-surface.

3. **AC turns out method-coupled.** If during build, an AC's text turns out to be tightly bound to a specific method (e.g. AC.β.1 implicitly mandates a particular YAML library), halt-and-surface; the AC needs tightening per `feedback_loose_AC_text_fix_AC_not_implementation`.

4. **β.2 attempts to edit sealed `self-upgrade/cli.py`.** Hard Constraint #2 binding. Halt-and-surface. Resolution path: `pos-new-workspace` ships as a NEW console_script (per D-β.2 recommendation) instead of a `pos` subcommand.

5. **New runtime dependency surfaces** (Hard Constraint #4). If the implementation requires a new `pyproject` runtime dep, halt-and-surface; the recommendation is stdlib + existing-deps only.

6. **β.2 chicken-and-egg surfaces in implementation.** β.2 needs pos-sync, which needs canonical, which β.2 just cloned. The natural answer (captured in dispatch + §1): β.2 invokes pos-sync internally with `--canonical <local-clone-path>` after cloning. **If the builder finds this answer doesn't compose cleanly** (e.g. workspace-bootstrap's first-run scaffold has a circular dep on pos-sync's cache-clone path), halt-and-surface.

7. **Scope drift toward β.4 PP** (out of scope). If the build agent finds confidence-floor calibration is necessary to make β.1 / β.2 / β.3 ship cleanly, halt-and-surface; β.4 may need pulling in.

8. **Wall-time exceeds 4-6 hours per AC.** Plan-author estimates 2-3 hours per AC for builder. If wall-time is materially higher, halt-and-surface; the AC may be method-coupled, blocked by another decision, or the plan may need refactoring.

9. **β.3 install path surfaces a host-OS-specific failure.** macOS-only ship per Hard Constraint #10 (and pos-v2's broader macOS-only stance). If the install path passes on macOS but fails on a developer's incidental linux test machine, that's expected — capture in build notes, do NOT halt unless the macOS path itself fails.


---

## 11. Decisions remaining for the owner to rule on

**All four decisions LOCKED 2026-04-27 by primary persona under confidence-delegation** (Luke 2026-04-27 broad-autonomy directive). Detail preserved below for audit trail.

- **D-β.1 LOCKED:** Plan-author recommendation accepted. (a) Both URL and local-path forms; (b) cache at `~/.pos/canonical-cache/<repo-id>/`; (c) always-fetch.
- **D-β.2 LOCKED (KEY):** Plan-author recommendation accepted = path (b) — separate `pos-new-workspace` console_script in `workspace-sync/pyproject.toml` (sub-option b.i). NOT a `pos` subcommand. Pattern-consistent with `pos-amend` / `pos-bootstrap` / `pos-sync`. Avoids editing sealed self-upgrade per HC#2.
- **D-β.3 LOCKED:** Plan-author recommendation accepted = path (b) primary + thin curl-bash wrapper. pipx install for the binary; curl-bash handles the pipx pre-install gate. Top-level meta-pyproject sub-decision routed to builder per §14 D-build.x.
- **D-β.4 LOCKED: split into 3 separate amendments.** β.1 first (highest leverage, smallest surface), β.2 second (config shape settled by β.1), β.3 third (largest surface, platform-specific testing). Each shippable on its own. Same-tree-serialize sequencing.

**HALT-FOUND #2 (β.1 docstring promise)** noted in §13: `_resolver_client.py:292` docstring references `~/.pos/sync-config.yaml` but the lookup is NOT wired in source. β.1 will land both workspace-local AND ~/-rooted paths, honoring the existing docstring promise as part of AC.β.1 scope. Treated as in-scope.

**Decisions detail preserved below for audit trail purposes.**

Per the dispatch's "Decisions to surface for owner ruling at end of plan-author run (outcome-shape only)" guidance. Method-shape decisions (e.g. exact YAML key names, exact module-internal API shape, prompt text) are the builder's call inside the AC's outcome bounds and are recorded in §14 post-build.

### D-β.1. β.1 — `canonical_source:` URL vs local-path vs both? Where does the clone-cache live for URL form?

**Question.** Three coupled sub-questions:
- (a) Should `canonical_source:` accept URL form, local-path form, or both?
- (b) For URL form, where does the clone-cache live?
- (c) For URL form, what is the cache-update policy (always-fetch / fetch-on-stale / never-fetch)?

**Why genuinely uncertain.** A non-tech operator probably has a URL (pos-v2's GitHub URL); a developer probably has a local path (their canonical clone). Supporting only URL forces developers to clone an extra time. Supporting only local-path forces non-tech operators to manage their own clone. Supporting both is the most flexible but adds a small validation surface (URL-vs-path discrimination + path normalisation). For (b), `~/.pos/canonical-cache/<repo-id>/` is the natural shape (sibling to other `~/.pos/` state); inside `<workspace>/.pos/` would force per-workspace clones (wasteful disk). For (c), `git fetch` on every invocation is ~50ms-1s when the cache is warm (acceptable); always-fetch is the safest default — workspaces stay current with the canonical.

**Recommendation.**
- **(a) Both URL and local-path forms.** Schema accepts a string; the loader discriminates: starts with `http(s)://` or `git@` → URL; absolute path → local; relative path → halt with structured error (unambiguous shapes only).
- **(b) `~/.pos/canonical-cache/<repo-id>/`** where `<repo-id>` is derived from the URL's `host/owner/repo` segments (e.g. `github.com/lukeivers/pos-v2/`). Workspace-shared cache (multiple workspaces with the same canonical_source share one cache). Cache directory created on first use; idempotent.
- **(c) Always-fetch** (`git fetch` on every invocation; ~50ms warm). For `--ref HEAD` semantics, fetch + checkout fresh HEAD. For pinned refs (`--ref v1.2.3`), fetch + checkout the pinned ref. The audit records the resolved canonical SHA per #56 + #57 conventions.

**Locked-by-recommendation candidate.** If owner agrees with the recommendation, lock; else surface alternatives.

### D-β.2. β.2 — `pos new-workspace` as `pos` subcommand vs separate `pos-new-workspace` console_script? KEY question.

**Question.** Where does β.2's bootstrap subcommand live?

- **(a) Subcommand of existing `pos` CLI.** `pos new-workspace ~/my-ws --from <repo>`. Cleanest UX (single binary). Requires editing `self-upgrade/src/self_upgrade/cli.py:build_parser` to register the subcommand. **`self-upgrade/` is sealed** (#54 + earlier). Editing it is amendment-shaped; conflicts with Hard Constraint #2 (no edits to sealed self-upgrade).
- **(b) Separate `pos-new-workspace` console_script (recommended).** Same hyphenation convention #56 used for `pos-sync`. Lands as a new entry in `workspace-sync/pyproject.toml` (sibling to `pos-sync`, `pos-workspace-sync`) OR in a new sibling `tools/pos-new-workspace/` package. NO edits to self-upgrade. UX is slightly less polished (operator types `pos-new-workspace` instead of `pos new-workspace`) but symmetric to `pos-sync`.
- **(c) Subcommand-registry primitive on the existing `pos` CLI.** Add a plugin-discovery mechanism to `pos` so subcommands can be registered by sibling components without editing `self_upgrade/cli.py`. Composes well long-term but is a NEW primitive (subcommand registry); much larger surface than β.2's actual ask. Out of scope for β.2 itself.

**Why genuinely uncertain.** (a) is the cleanest UX but conflicts with the sealed-component fence — the dispatch's halt-trigger 4 names this exact case. (c) is the most extensible long-term but adds significant scope. (b) is the most conservative + matches the existing `pos-sync` / `pos-workspace-sync` precedent.

**Recommendation.** **Path (b).** Ship `pos-new-workspace` as a new console_script. Two sub-options on placement:

- **(b.i)** Add to `workspace-sync/pyproject.toml` alongside `pos-sync`. Module lives at `workspace-sync/src/workspace_sync/new_workspace_cli.py`. Composes on the same package's existing CLI machinery; the new subcommand internally invokes `pos-sync`'s flow as a library call (not a subprocess). Pro: one fewer top-level component. Con: workspace-sync's component scope grows from "sync" to "sync + bootstrap"; arguably the bootstrap is sync-shaped (it IS a first-sync against a fresh-clone) so the scope-bend is small.
- **(b.ii)** New top-level component `tools/pos-new-workspace/` with its own pyproject. Module structure mirrors other tools/ entries. Pro: clean component boundary. Con: more boilerplate; duplicate dep declarations.

**Sub-recommendation:** **(b.i)** — add to `workspace-sync/pyproject.toml`. β.2 IS a sync-shaped operation (first-sync from a fresh clone); workspace-sync is the natural home. Scope-bend is minimal.

**If owner prefers (a).** A separate small amendment unsealing self-upgrade for a subcommand-registry addition (a NEW primitive, scope-bent against self-upgrade) would have to land first. That's a much larger plan than β.2 itself; recommend deferring.

### D-β.3. β.3 — which install path? Curl-bash / pipx / homebrew?

**Question.** Three viable mechanisms; pick one as the primary; capture trade-offs.

- **(a) curl-bash installer.** `curl -sSL https://pos-v2.example/install.sh | bash`. Self-contained shell script that creates `~/.pos/{install,bin}/`, clones canonical, creates a venv, installs in editable mode, writes shim scripts. Pro: zero third-party tool dependency (just curl + bash + git + python). Con: shell-script complexity scales with edge cases (existing install detection, upgrade path, uninstall, path injection across shells). Auditing shell scripts for security is harder than auditing a pyproject.
- **(b) pipx-installable package (recommended).** Operator runs `pipx install pos-v2` (publishing to PyPI) OR `pipx install git+https://github.com/lukeivers/pos-v2.git` (no PyPI publish required). pipx handles isolation + PATH injection automatically. Pro: standard modern Python-CLI distribution; well-audited install machinery; clean uninstall (`pipx uninstall pos-v2`). Con: requires pipx to be installed first (mitigation: thin curl-bash wrapper that does `pip install --user pipx` if missing).
- **(c) homebrew formula.** `brew install ivers-corp/pos/pos-v2`. Most polished UX on macOS. Pro: macOS-native; users already have brew. Con: requires maintaining a homebrew tap; downstream dep on brew's package store; more setup per release.

**Why genuinely uncertain.** (a) is the simplest from-scratch but the install-script complexity creeps fast. (b) leverages the standard Python ecosystem but requires a pipx pre-install. (c) is the slickest macOS UX but adds a tap-maintenance burden.

**Recommendation.** **Path (b) primary + thin curl-bash wrapper for the pre-install.**

```
curl -sSL https://pos-v2.example/install.sh | bash
```

Where `install.sh` does:
1. Verify `python3 --version >= 3.13` (per pos-v2's `requires-python = ">=3.13"`); halt if not.
2. Verify `pipx --version` returns; if not, run `pip install --user pipx && python3 -m pipx ensurepath`.
3. Run `pipx install git+https://github.com/lukeivers/pos-v2.git` (or `pipx install pos-v2` if PyPI-published).
4. Print install-success summary + next-step ("run `pos-new-workspace ~/my-workspace --from <canonical>`").

Pro: leverages pipx's audited install machinery for the binary install; the curl-bash wrapper is small (~30 lines) and only handles the pipx pre-install gate. Con: pos-v2 is currently a multi-package project (workspace-sync, self-upgrade, workspace-bootstrap, etc.); pipx install requires either a meta-package or a single pyproject with all components as `optional-dependencies`. **Captured for builder reference (D-β.3-detail):** pos-v2 needs a top-level meta-package (or pyproject) for pipx to install against; the meta-package depends on the component packages. This is a separate sub-decision the builder routes in their builder-plan.

**If owner prefers (c) homebrew.** Add it AFTER (b) lands — homebrew formulas are a downstream wrapper around the pipx install (homebrew can install Python packages via brew formulas calling `pipx install` under the hood). β.3 ships pipx + curl-bash; future amendment ships homebrew tap.

### D-β.4. Should β be split into separate amendments (β.1 + β.2 + β.3 as three small amendments) vs landed as one bundle?

**Question.** One amendment with three internal ACs vs three amendments with one AC each.

**Why genuinely uncertain.** The three ACs are independent (β.1 doesn't depend on β.2; β.3 doesn't depend on β.1 or β.2 — though β.2 internally invokes β.1's config-file write). One bundle is a single seal commit + single amendment number. Three amendments give per-AC isolation: a problem with β.3 doesn't block β.1 + β.2 from landing.

**Recommendation.** **Three separate amendments** (β.1 first, β.2 second, β.3 third). Reasoning:

- **β.1 has the highest leverage + smallest surface.** Land it standalone so the UX win arrives fast (every subsequent `pos-sync` invocation is no-args).
- **β.2 has a moderate surface + an open D-β.2 ruling on placement.** Land it after β.1 so the config-file shape is settled first.
- **β.3 has the largest surface + the most platform-specific testing.** Land it last; if it surfaces unexpected platform issues, β.1 + β.2 are already shipped + delivering value.
- **Same-tree-serialize applies** per `feedback_serialize_amendment_builds`. Three sequential amendments are the safe default.

**Alternate (one bundle).** Pro: one amendment number; one seal commit. Con: any one AC blocking surfaces blocks the bundle; harder to roll back individual ACs; harder to slot between other in-flight amendments.

**Locked-by-recommendation candidate.** If owner agrees, lock as three amendments; assign amendment numbers at dispatch time; sequence via same-tree-serialize.

### Decisions captured for builder reference (NOT for owner ruling here):

- **D-β.5 (component fence for β.3).** β.3 lands at `tools/pos-installer/` OR `install/` at repo root. Method-shape; builder authors in §14 D-build.x. Out of scope for owner ruling.
- **D-β.6 (β.1 sealed-component vs dev-discipline).** Plan-author recommends sealed-component (saves future-admission work; β.1 lands inside workspace-sync's source tree). Captured in Hard Constraint #3 + the §1 framing. If D-β.4 splits the bundle, D-β.6 routes per-AC.
- **D-β.2-detail (β.2 in-process embed of workspace-bootstrap vs subprocess).** Method-shape; the builder authors in §14 D-build.x.
- **D-β.3-detail (pos-v2 meta-package for pipx).** Method-shape captured in D-β.3 above; builder routes in their builder-plan.


---

## 12. Summary of named decisions (owner-readable)

| Decision | Recommendation | Why it matters |
|---|---|---|
| D-β.1 — β.1 `canonical_source:` shape (URL/path) + cache location + fetch policy | **Accept both URL + absolute local-path; cache at `~/.pos/canonical-cache/<repo-id>/`; always-fetch on every invocation** | Maximum flexibility for both non-tech (URL) and developer (local-path) operators; workspace-shared cache avoids per-workspace duplicate clones; always-fetch keeps workspaces current |
| D-β.2 — β.2 placement: `pos` subcommand vs separate console_script | **Path (b.i): new console_script `pos-new-workspace` declared in `workspace-sync/pyproject.toml`. NOT a `pos` subcommand (Hard Constraint #2: no edits to sealed self-upgrade)** | Avoids editing sealed self-upgrade/cli.py; matches the `pos-sync` / `pos-workspace-sync` precedent #56 established; minimal scope |
| D-β.3 — β.3 install path | **Path (b): pipx install + thin curl-bash wrapper** for the pipx pre-install gate. Aligns with D-A1 ruling (Architecture A for the CLI binary) | Leverages standard Python-CLI distribution machinery; auditable; clean uninstall; small wrapper handles pipx pre-install |
| D-β.4 — Bundle splitting | **Ship as three separate amendments (β.1 → β.2 → β.3, sequenced by same-tree-serialize)** | β.1's UX win arrives fast; per-AC isolation; β.3's larger surface lands last so it doesn't block β.1 + β.2 |

All four decisions are reversible at the cost of a follow-on amendment; none is foundational. **D-β.2 is the most consequential** (drives whether β.2 is amendment-shaped against sealed self-upgrade — the recommendation avoids the conflict). **D-β.4 is the second-most consequential** (drives bundle vs split — the recommendation favours split).


---

## 13. Halt-and-surface findings encountered during plan authoring

Per `feedback_subagent_odd_violation_halt`: halt and surface any ODD violation observed in surrounding code/docs.

Plan-authoring scope (read-only audit of `workspace-sync/src/workspace_sync/cli.py`, `_resolver_client.py`, `pyproject.toml`; `self-upgrade/src/self_upgrade/cli.py`, `pyproject.toml`; `workspace-bootstrap/src/workspace_bootstrap/adapters/first_run_scaffold.py`, `pyproject.toml`; #56 + #57 plan-docs §11 + §14; FUTURE_IDEAS_DRAFT lines 14-31; the dialog-context-dossier).

### HALT-FOUND #1 (β.2) — `pos new-workspace` as `pos` subcommand would touch sealed `self-upgrade/cli.py` — surfaced + resolved in-plan via D-β.2.

The dispatch named this halt explicitly: *"a scope question: does β.2 LL touch `self-upgrade/cli.py` (where `pos` main lives)? If yes, that's a NEW concern (self-upgrade is sealed; touching it is amendment-shaped). Halt-and-surface; possible resolution is for `pos new-workspace` to live as its own console_script (`pos-new-workspace`) per the same hyphenation convention #56 used for pos-sync, avoiding self-upgrade edits. OR add a subcommand-registry primitive to pos."*

**Resolution path:** D-β.2 (recommendation: path (b) — new console_script `pos-new-workspace` in workspace-sync/pyproject.toml). NOT a `pos` subcommand. Documented in §11 D-β.2 + Hard Constraint #2 + Halt-trigger 4. Plan-author surfaces the recommendation; owner rules.

### HALT-FOUND #2 (β.1) — `~/.pos/sync-config.yaml` is referenced in `_resolver_client.py:292` docstring but the lookup is NOT actually wired in source.

Inspection of `workspace-sync/src/workspace_sync/_resolver_client.py:282-296` (the `build_merge_resolver` factory) reveals the docstring claims budgets are *"workspace-tunable via `~/.pos/sync-config.yaml`"* but the factory body does NOT load any config file — it instantiates `_ClaudePrintResolverClient()` and returns `MergeResolver(client, budget or ResolverBudget())`. The promised config-file lookup is not implemented.

**Implication for β.1.** β.1 must land BOTH: (a) the workspace-local `<workspace>/.pos/sync-config.yaml` schema + load path, AND (b) the documented-but-not-wired `~/.pos/sync-config.yaml` schema + load path. Without (b), the docstring's promise is broken. Plan-author treats this as IN-SCOPE for β.1 (it's the same schema, same loader, just a second precedence layer). Documented in AC.β.1's "Schema additions (workspace-local + ~/.pos/ shared)" subclause.

**Out-of-fence ODD-loose text.** The `_resolver_client.py:292` docstring is technically a non-objective claim (a documented-but-unimplemented behaviour). Plan-author recommends β.1's build agent tighten the docstring during build (the docstring becomes accurate when β.1 lands, no doc-fix needed) — not a separate ODD remediation.

### HALT-FOUND #3 (β.2) — workspace-bootstrap's first-run scaffold halts on non-darwin.

Inspection of `workspace-bootstrap/src/workspace_bootstrap/adapters/first_run_scaffold.py` (lines 1-100) reveals the scaffold halts with `platform-unsupported:<platform>` on non-macOS hosts. β.2's invocation of workspace-bootstrap (per AC.β.2 step 5) inherits this halt.

**Implication.** β.2 ships macOS-only (per Hard Constraint #10 + pos-v2's broader macOS-only stance). Captured. NOT a new finding — composes on the existing platform constraint. No halt-trigger fires; documented in §7 out-of-scope ("β.3 windows / linux installers").

### HALT-FOUND #4 — none observed beyond the three above.

Pre-build sweep clean otherwise. The three findings above are surface-level scope clarifications, not deep ODD violations. None blocks the plan.

### Halt-trigger surface review (per plan §10)

Summary of which §10 triggers fired during plan-authoring:

- **#1 (new top-level objective):** Did not fire. Composition under VALUE_PROPOSITION's AC.PO.1 + AC.PO.2.
- **#2 (ODD violation in surrounding code):** Marginally fired (HALT-FOUND #2 above re docstring). Resolution path: tighten on β.1 build (no separate remediation needed).
- **#3 (AC method-coupled):** Did not fire. Each AC is outcome-shaped.
- **#4 (β.2 attempts to edit sealed self-upgrade):** Did not fire (avoided by D-β.2 recommendation).
- **#5 (new runtime dep):** Did not fire (β.1 + β.2: no new dep; β.3 may add system-tool dep on pipx but that's not a pyproject runtime dep).
- **#6 (β.2 chicken-and-egg):** Did not fire (resolved per dispatch + §1 framing — β.2 invokes pos-sync internally with a freshly-cloned canonical).
- **#7 (scope drift to β.4):** Did not fire (β.4 PP cleanly out of scope).
- **#8 (wall-time):** Did not fire (plan-authoring complete within projected envelope).
- **#9 (β.3 host-OS-specific failure):** Plan-authoring is read-only; not applicable.


---

## 14. Method-decision record (builder, post-build)

The plan §11 left D-β.x outcome-shape decisions to owner ruling and D-build.x method choices to the builder within the ACs' outcome bounds. This section is populated post-build (per AC, per amendment if D-β.4 splits the bundle).

### D-build.x — (placeholder for the build agent's method choices)

(Post-build: builder records D-build.0 module placement, D-build.1 schema field names, D-build.2 cache-clone-id derivation, D-build.3 sub-process-vs-import for β.2 → workspace-bootstrap, D-build.4 install-script error-handling shape, etc.)

### Test breakdown

(placeholder; builder fills per-AC test count + AC-by-AC mapping per #56/#57 precedent)

### Backwards-compat verification

Per Hard Constraint #1 (binding):

(placeholder; builder verifies post-build:)
1. (β.1) `pos-sync` against post-#57 workspaces continues to work without `<workspace>/.pos/sync-config.yaml`. CLI signature unchanged in the additive direction.
2. (β.1) Audit YAML shape: forward-compatible.
3. (β.2) Existing workspaces (pos3) are NOT touched by β.2; the new console_script is opt-in.
4. (β.3) Pre-existing pos installs (e.g. canonical pos-v2's editable install) continue to work; the new install path is alongside, not replacing.
5. (All) No edits to sealed `self-upgrade/`, `workspace-bootstrap/` (per Hard Constraint #2 + #3).

### Halt-trigger surface review (per plan §10)

(placeholder; builder records which triggers fired during build)

### Speedup deltas vs baseline

(placeholder; per Luke's amendment-dispatch-speedups directive, builder records)

### Commit SHAs

- Amendment commit: `cd4c2f2d3ddad07012aa515dd8fb8cab91e7cf26` —
  `chore(workspace-sync): advance BASELINE + SEAL_COMMIT for amendment #58 window`
- Seal commit: `6860e4df3eec2822dffad2871f5720718c5d6d7d` —
  `chore(seals): workspace-sync — Bundle β.1 ergonomics: workspace canonical-source config + pos-sync no-args — workspace-sync at cd4c2f2`
### Dependents cleared to dispatch

(placeholder; post-β: workspace-clone primitive (out-of-scope here), `/sync` slash-command surface (Lens 1 future work), telegram-channel integration of pos-new-workspace, etc.)


---

## 15. References

- CLAUDE.md (project + global)
- `docs/odd-methodology.md`, `docs/odd-in-pos.md`
- `docs/rebuild/VALUE_PROPOSITION.md` (binding spec — AC.PO.1 + AC.PO.2)
- `docs/rebuild/STATE.md`, `docs/rebuild/FUTURE_IDEAS.md`, `docs/rebuild/FUTURE_IDEAS_DRAFT.md`
- `docs/rebuild/spec/pos-v2-objectives-spec.md`
- `docs/rebuild/plans/workspace-sync.md` (#56 plan-doc, 1377 lines; the parent plan; defines `pos-sync` CLI surface + `<workspace>/.pos/sync-protected.yaml` envelope)
- `docs/rebuild/plans/workspace-sync.builder-plan.md` (#56 builder-plan, 731 lines)
- `docs/rebuild/plans/workspace-sync-resolver-cost-overhaul.md` (#57 plan-doc, 1406 lines; the parent plan; reference §11 for the existing config-file shape pattern)
- `docs/rebuild/plans/dispatch-prompt-template-extension.md` (recent dev-discipline plan — shape reference for §1-§14 skeleton)
- `tools/pos-amend/tests/fixtures/plan-skeleton/expected.md` (canonical dev-discipline plan-skeleton; the §14 register shape)
- `tools/pos-amend/tests/fixtures/plan-skeleton/vars.yaml` (canonical vars-file shape; sibling to this plan's `workspace-sync-ergonomics.vars.yaml`)
- `workspace-sync/src/workspace_sync/cli.py` (β.1 attach point — current `pos-sync` argparse)
- `workspace-sync/src/workspace_sync/_resolver_client.py` (β.1's `~/.pos/sync-config.yaml` reference at line 292; HALT-FOUND #2)
- `workspace-sync/pyproject.toml` (β.2 console_script placement candidate per D-β.2)
- `self-upgrade/src/self_upgrade/cli.py` (β.2's "rejected option" — sealed; cannot edit)
- `workspace-bootstrap/src/workspace_bootstrap/adapters/first_run_scaffold.py` (β.2's first-run-scaffold composition point)
- `/Users/lukeivers/pos3/.scratch/claude-output/dialog-context-dossier.md` (recent context, milestone-closure status)
- `/Users/lukeivers/pos3/.scratch/claude-output/milestone-live-test-2026-04-27.md` (live-test against pos3; 46 conflicts → 46 resolved; structural validation of the post-#57 mechanism β builds on)

