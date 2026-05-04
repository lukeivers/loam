# FUTURE_IDEAS_DRAFT.md — no-overhead idea capture

This is a draft surface for *every* improvement idea about pos-v2 — Luke's or the assistant's — captured at point-of-occurrence with no overhead. Sibling to `FUTURE_IDEAS.md` but distinct in lifecycle:

- `FUTURE_IDEAS.md` is **curated**: each idea has a designated number, a rationale section, and a relationship to other ideas.
- `FUTURE_IDEAS_DRAFT.md` is **no-overhead capture**: append a brief bullet with rationale (~3–5 lines) the moment an idea surfaces. No numbering, no curation, no ordering.

**Lifecycle.** During the initial phase of pos-v2 development, entries accumulate. Periodic rigor reviews graduate worthy items to `FUTURE_IDEAS.md`, drop obsolete ones, and combine duplicates. Last review: 2026-04-27.

**Convention.** Agents (background or main-session) **surface to chat** — they do not write to this file directly. The parent (or owner) appends. This avoids file-write races when multiple agents run in parallel, and keeps the parent in the loop on every captured idea.

---

## Workspace-sync follow-on family (post-#56 milestone-test 2026-04-27)

Proposed consolidation: **two bundles** instead of eight follow-ons.

- **Bundle α — workspace-sync resolver cost overhaul.** Combines three attack vectors on the same problem (resolver cost dominates first-sync of long-diverged workspaces). Three internal ACs:
  - **(α.1) NN — content-vs-canonical-history ancestor detection.** If workspace path content matches some ancestor commit reachable from canonical's HEAD, fast-path accept-canonical without resolver call (workspace didn't diverge; it's just behind). Reduces first-sync cost from O(diverged-files × LLM) to O(diverged-files × git-rev-walk). For pos3 specifically: 90%+ of the 46 conflicts observed in the live-test were just-behind-canonical and could resolve without inference.
  - **(α.2) QQ-refined — deterministic-merge-with-LLM-verify-gate; LLM-as-classifier + LLM-as-verifier, never LLM-as-generator.** When merge IS needed, replace LLM-as-generator (full-file output, 60-120s+ for ~100-line files) with: (1) classify (~50 token output) "is this file structurally-mergeable?"; (2) deterministic primitive does the merge (free); (3) verify (~200 token output) "did the merge lose meaning?"; (4) verify-pass → accept; verify-fail → fall back to full-LLM-merger or halt-and-surface. 3-8× faster AND safer (deterministic merge is reproducible + audit-grade; verifier adds safety net). Generalizable meta-pattern — graduated to FUTURE_IDEAS Idea 20.
  - **(α.3) RR — workspace-sync resolver subprocess uses `claude --bare`.** One-line change in `_resolver_client.py`. `--bare` skips hooks, LSP, plugin sync, auto-memory, background prefetches, keychain reads, CLAUDE.md auto-discovery — saves 5-20s cold-start per call AND likely fixes the telegram-MCP disconnect correlation observed during pos-sync runs.
  - **Subsumes OO** (resolver timeout config + 300s default — irrelevant if cost is lower per call).

- **Bundle β — workspace-sync ergonomics.** Closes the "normal person can use pos" gap. Four internal ACs:
  - **(β.1) KK — workspace canonical-source config; `pos-sync` no-args.** Workspace stores canonical source URL/path in `<workspace>/.pos/sync-config.yaml`; `pos-sync` reads it; user runs `pos-sync` from inside workspace with no flags. Operator never has to know the canonical path.
  - **(β.2) LL — `pos new-workspace --from <repo>` bootstrap command.** Solves the chicken-and-egg: under Architecture B a fresh workspace has no framework code yet. `pos new-workspace ~/my-ws --from https://github.com/.../pos-v2` clones canonical, embeds framework via pos-sync, writes the canonical-source config. Composes with workspace-bootstrap's existing first-run plumbing.
  - **(β.3) MM — global install path for `pos` and `pos-sync`.** Today the binaries live only in canonical pos-v2's `.venv` — nothing on PATH for a normal user. Curl-bash installer / pipx / homebrew. Aligns with D-A1 ruling (Architecture A for the CLI binary).
  - **(β.4) PP — `--auto-accept` confidence-floor calibration / partial-accept tier.** Both verdicts in the live-test were 0.88 confidence (below the 0.90 default floor) yet demonstrably sharp. Either lower default to 0.85, or add a "confirm-with-reservations" tier where verdicts in [floor, 0.90) auto-stage and surface a one-line summary for human review before apply. Needs empirical sample to calibrate.

- **`pos-sync --dry-run` UX bug.** Flag spawns real LLM calls. By the name "dry-run," operators expect a free preview; this spends tokens (5-10s wall-clock per Class-C conflict). Rename current behavior to `--preview-verdicts`; make `--dry-run` truly cheap (plan-only, no LLM). Composes with cost-governance.

---

## Tooling improvements (pos-amend / dev infra)

- **Dispatch-template family extension: memory-doc + commit-message templates.** The dispatch template (#25) and plan-doc skeleton (#51) prove the pattern. Memory-doc skeleton (frontmatter + Why + How-to-apply structure) and commit-message templates per category (`feat(<comp>): ... — amendment #N`, `chore(seals): ...`, `docs(plans): record amendment #N commit SHAs`) are natural extensions. Plus `pos-amend commit-msg <category> <vars>` helper.

- **`pos-amend log-decisions <plan> <key>=<value>...`** (stretch). Mechanise §14 method-decision register's deterministic subsections — test counts, dependents-cleared list, file-touched manifests — while leaving D-build.x prose to the builder.

- **`pos-amend apply` regex misses in-function literals.** Doesn't reach `allowed_prefixes` literals declared inside function bodies (vs module-level). Caused #50 to need a corrective commit (`6c90b9c`). Fix: extend regex or switch to AST parse. OR: document the limitation so dispatchers flag it.

- **`pos-amend seal` stash-pop conflict on existing working-tree files.** Stash-and-restore can fail when stash includes a file that already exists in the working tree (collision example: #50's `personas/primary/prompt.md`). Fix: detect collisions and either three-way-merge, abort with structured diagnostic, or use `git stash apply --index` then resolve.

- **Template engine notes.** (a) One-pass `{{var}}` substitution doesn't recursively expand defaults — a default containing `{{OTHER_VAR}}` renders the literal placeholder. Caught early in #25 build. Document in dispatch-template authoring guide. (b) Templates root resolves via `__file__` parents — works for editable installs only. If pos-amend ever ships PyPI/wheel, templates need `package-data` declaration in `pyproject.toml`. Not blocking; noted for eventual packaging story.

- **Template `description` frontmatter doubles as `list` one-liner.** The introspection-surface frontmatter the engine requires gives `pos-amend template list` its descriptions for free. Useful pattern when memory-doc/commit-message families land.

- **`claude --bare` mode for clean experiments / scripted scenarios.** Document the recipe: `claude --bare --settings .claude/settings.json` for pure-harness-free Claude invocations. Useful when the full pos-v2 harness shouldn't load. (Also relevant to RR.)

- **Test conftest collision pattern across `tools/<x>/tests/` dirs.** Adding tests in two `tools/<x>/tests/` directories with the same module names triggers a pytest cross-tree collision. Resolved in #17 by dropping `__init__.py` + using fixtures instead of cross-test imports. Capture in dispatch template's "Cycle mechanics" section or pytest-conventions doc.

---

## Methodology / discipline notes

- **AC text precision sweep.** Opportunistic batch of post-seal AC tightenings (similar to AC37.5, AC40.1) — when an AC pins specific vocabulary that turns out to be method-not-objective, tighten the AC. Could batch across multiple sealed amendments in one doc-only sweep. Borderline cases not tightened in #17's sweep: AC.A1, AC.A6, AC.A7, AC.B5 (specific OTel event names + Literal types — debatable; the names ARE contracts THIS amendment authors); F's AC.F1 (the `always_loaded`/`dev_only` partition keys — borderline, names are now load-bearing). Master plan §6.3 AC3 "additionalContext payload that names the loaded persona" wording is symmetric to AC37.5 tightening. Re-evaluate in a future precision sweep.

- **Integration-test methodology gap on SQLite file inspection.** Bare `stat()` on the main `.sqlite` file mid-WAL can mislead — size doesn't reflect committed data until WAL checkpoints. Future integration-test fixtures should sample sibling `-wal`/`-shm` files AND open-then-close a `sqlite3` connection before size-checking. (Caused #3's 0-byte Finding 2 false alarm.)

- **Master-research recommendations should pre-filter through the scope-fence constraint.** #17 build's D-build.6 had to deviate when research recommended a sealed attach point but the dispatch was dev-discipline (`tools/` fence). Recurring pattern; research dispatches should explicitly filter recommendations through scope-fence at research time.

- **H19 admission-debt pattern (PARTIALLY ACTIONED via dispatch-template at `a17f1f7`).** Amendments that introduce new top-level paths should admit them in their own H19 window, not leave it for the next hands-off-lifecycle amendment. Dispatch template now includes the check; ensure the convention propagates.

- **Cross-mode reference debt: `memory-system/launchd/README.md` references dev-only path.** F's AC.F3 reference scanner found memory-system/launchd/README.md (always-loaded) references `docs/rebuild/components/true-first-run/research.md` (dev-only). Editing the README would breach memory-system's sealed-component fence. F captured as `KNOWN_CROSS_MODE_DEBT` allowlist; allowlist must shrink to empty when fixed. Resolution path: future memory-system amendment scrubs the cross-ref (preferred — minimal partition surface).

- **`source_commit` backfill pass for Phase γ records.** #17 Phase γ projection populated 99 amendment-AC records but left `source_commit` field None. A follow-on backfill pass that walks `git log --grep` for each amendment's seal commit could populate these. Going forward, the live `pos-amend seal` cycle populates `source_commit` automatically (AC.D-mig.4 verified); only historical records need backfill.

- **AC anchor regex is conservative — tightening could yield 100-200 more records.** Phase β/γ extractor catches H2/H3 + bullet-form ACs but misses prose-style criteria. ~17 placeholders out of 25 plans + 21 components. Worth tuning once the projection is in active use and missing records become visibly missed.

- **`feedback_serialize_amendment_builds` may be over-broad.** #20 empirical finding: parallel doc-edit + dev-discipline-build is safe — the rule applies specifically to sealed-component-amendment-build pairs racing on `pos-amend`, not generic git activity. Tighten the memory to clarify scope.

- **Bash-tool eval-wrapper anomalies (consolidated).** Two related quirks: (a) glob expansion fails differently than interactive zsh — `(eval):1: no matches found` errors even with `setopt nomatch` unset; use Read or `find -name` or `bash -c '...'` for glob behaviour. (b) Stderr can be filtered/dropped on some Bash-tool invocations (e.g. pos-amend halts surfaced as silent rc=0 in main session, visible in fresh agent sessions). Workarounds: `2>&1 | tee /tmp/log`. Fix is upstream Claude Code harness concern. Practical persona-level rule: don't form claims about file existence from glob failures, don't form claims about command success from rc=0 alone.

- **`pos-amend seal --plan-doc` crashes on relative-path argument.** `Path.relative_to` raises ValueError when invoked from repo root with relative `--plan-doc` arg (commit `75c4d73` worked around). Fix: normalise to absolute path inside the subcommand.

---

## Structural-enforcement candidates (O program targets)

- **End-of-turn trait-reflection — Stop-hook contributor.** Today the trait-check is content-level (a rule the persona reads from prompt.md). Higher-leverage: a Stop-hook contributor that wraps the persona's reply with a deterministic self-reflection step. Composes with O program; could become an A5 amendment after A1 substrate landed.

- **Self-evolution directive — proactive own-behavior change suggestions.** Same shape: a Stop-hook contributor runs trait-check + improvement-proposal step, surfaces concrete suggested directives to next UPS additionalContext. Active surface (not just passive FUTURE_IDEAS_DRAFT capture).

- **Workspace-level `primary_channel` config slot.** Today the directive "Telegram is workspace default conversation layer" lives in dossier prose — advisory. Structural shape: workspace config (persona contract field `primary_channel`, or `<workspace>/.pos/channel.json`) read at session-start; persona routes default replies based on its value. Multiple workspaces can have different defaults.

- **Dossier (or any persona-maintained note) shouldn't duplicate canonical-truth values.** Caught 2026-04-26: dossier "Landed amendments" carried explicit numbers + commit SHAs; drifted off-by-one because git log was the canonical source. Generalisable rule: for any value canonically elsewhere (git log, plan-doc §14, manifest), reference don't duplicate. Pruning-trait extension. Structural-enforcement candidate: a Stop-hook contributor that derives current values from canonical source and warns on dossier-claims that disagree.

- **Default action verb is "I'm doing X", not "want me to X?"** Captured 2026-04-27. Persona has a recurring pattern of surfacing discretionary-check-in framing ("Want me to patch the plugin?") on work that's clearly within Luke's broad-autonomy grant. Reserve "want me to" for genuinely ambiguous-which-path cases (multiple defensible options where owner taste matters). For uncontroversial in-scope work: announce + execute. Composes with O program.

---

## Cosmetic / specific bugs

- **Stale `error_code` + `remediation` fields in completed `first-run.state`** (gen-2→gen-3 transition; `_advance_state` doesn't clear them on completion).

- **Phase-5 confirmation sentence "twelve components"** — actual install is 13 (telegram-interface auto-discovered). Hardcoded string in `_confirmation_sentence()`.

- **`/effort` confirmation message bug** (upstream Claude Code) — `/effort auto` says "Effort level set to max" but actual state is `xhigh` (correct behaviour). UI-only mismatch. File via `/feedback`.

- **Dynamic `/effort auto`** (upstream feature request) — Luke's intuition that "auto" should scale per task, not statically reset to model default.

- **`personas/primary/` at canonical root cleanup.** Cause identified by #42 build: workspace-bootstrap test invokes `run_first_run_scaffold` without `workspace_root` set; `_resolve_workspace_root` walk-up falls through to canonical repo root. Fix is workspace-bootstrap-test-side: tests should always pass an explicit `workspace_root` (tmp dir).

---

## Reactivation / deferred cross-references

- **G-activation-first dissolves D.** If sub-plan G (shared host-level memory-graphiti instance + workspace-keying via group_id) activates first at multi-workspace reactivation time, sub-plan D (per-workspace memory-graphiti port auto-allocation) becomes moot. Flag at reactivation-time triage so we don't redundantly build D before G.

- **Lazy-projection trigger ↔ amendment #32 session-start gate composition.** When sub-plan #17 (heavy-b-phase-α/β/γ-migration) reactivates as the lazy-projection job triggered by dev_intent=yes, the cheapest available attach point is amendment #32's session-start gate. Method-level note for #17's future builder.

- **C may activate as "audit + cleanup" rather than "migrate" when multi-workspace lands.** D-MASTER.2's owner-revised mirror of `~/.claude/` collapsed C's migration burden; if any of the resolver pattern is partially in place by reactivation time, C's scope shifts from "migrate state files" to "audit existing layout for compliance + close gaps."

---

## Removed (actioned or graduated, kept as audit trail until next review)

- **Dispatch-prompt template family** — landed via #25.
- **Plan-doc skeleton template** — landed via #51.
- **`pos-amend new-plan <slug>` orchestration** — landed via #51.
- **Telegram MCP plugin watchdog refix** — patched 2026-04-27 at `~/.claude/plugins/cache/claude-plugins-official/telegram/0.0.6/server.ts:670`.
- **C closure: Stop-hook learning-extraction = (c) trust graphiti** — task closed; Stream A #48 implements (c).
- **First-run sync of long-diverged workspace burns LLM budget** — graduated as α.1 (NN ancestor detection) above.
- **LLM-as-classifier-or-verifier-not-generator meta-pattern** — graduated to FUTURE_IDEAS Idea 20.
- **SDLC objective-extraction skill for existing repos** — graduated to FUTURE_IDEAS Idea 3 sub-section.

(Audit-trail entries clear at next review — they exist to confirm nothing was lost in the cleanup.)

---

*New entries append to the top of the relevant section.*

- **Apply-step verification REQUIRES file-content-on-disk match, not output-message signal.** Captured 2026-04-27 from a major calibration miss. I declared "milestone closed + live-verified" based on `[workspace-sync] applied: <ref>` output + audit shape + state.yaml status. Subsequent inspection found pos3's framework files were STILL at pre-apply state — Bundle α's NN ancestor-detection had a `resolved_content_path: null` bug that let apply silently no-op. Bundle α's 101 tests verified verdict-shape, NOT on-disk-file-content; the bug shipped. Generalizable rule for apply-style amendments (workspace-sync, anything that mutates workspace files): **the verification-loop MUST include byte-comparison of at least one workspace file's content against canonical's expected blob**. Output messages, audit log, and state files are NECESSARY but NOT SUFFICIENT signals. Structural-enforcement candidate: add a post-apply self-check to pos-sync that byte-verifies a sample of resolved entries; emit warning + halt-and-surface on mismatch. Composes with Idea 20 meta-pattern (verifier role) — apply-step-verifier is the symmetric counterpart to merge-step-verifier (α.2 QQ-refined).

- **`feedback_verify_post_amendment_state` should sharpen to "byte-verify, don't trust output messages".** Captured 2026-04-27. The existing memory says "verify post-amendment state from code, not prior-agent reports" — but I followed it nominally (read agent reports skeptically, ran tests, code-reviewed) yet still trusted output strings (`applied: <ref>`) without actual file-content inspection. The next-level discipline: **for any state-mutating amendment, verification must include a byte-content check on the actual mutation target**. Reading test assertions tells you tests pass; reading file content on disk tells you the mutation actually happened. The latter is the ground truth.

- **Persona "want me to / awaiting your read" pattern needs STRUCTURAL fix, not discipline.** Captured 2026-04-27 from a recurring failure mode: Luke called out the autonomy-violation pattern 4+ times in one session (asking permission on uncontroversial in-scope work despite explicit broad-autonomy directives + reminders). Inference-level discipline keeps failing because the pattern is too easy to slip into. The discipline-only approach has empirically failed. Structural fixes worth pursuing: (a) Stop-hook contributor that scans persona's outbound Telegram/terminal replies for permission-asking patterns ("awaiting", "want me to", "your call", "let me know", "ruling needed", "if you confirm") and either rewrites them to action announcements OR halts with a self-correction step; (b) a deterministic post-processor at Telegram-send time that converts "awaiting your call on X" → "doing X unless you object" for in-scope work (which the persona evaluates against the autonomy directive at send time); (c) a structural pre-send check baked into the reply tool wrapper. Composes with O program (structural-enforcement substrate) + Idea 1 (three-lens enforcement). High-leverage relative to ongoing discipline cost.

- **Structural-enforcement-default rule needs the "relocate vs eliminate" sharper test.** Captured 2026-04-27 from the D vs D′ near-miss. Existing rule says "prefer structural over advisory." Misses the case where both options are nominally structural but only one eliminates the failure class. Sharper test: "Can a future code change re-introduce the same failure class without active discipline? If yes, this is rule-shaped despite using a structural mechanism." Applied to D vs D′: D′'s .gitignore patterns relocate the "developer forgot" failure to .gitignore-pattern-management; D's directory split eliminates it (different-directory = can't accidentally touch). Already promoted into dossier rule 4 inline; consider also landing in canonical's `docs/odd-methodology.md` as a methodology refinement.

- **First-principles-trigger Stop-hook contributor.** Captured 2026-04-27 — Luke confirmed (A) methodology rule is landing now (in odd-methodology.md §4.6 via corpus-edit dispatch); option (B) deferred for future evaluation. Structural-enforcement complement to the (A) methodology rule: a Stop-hook contributor that scans recent amendment history (e.g., last 14 days of git log) + the pending dispatch list for the trigger patterns named in §4.6 (N≥2 hotfixes on same component, same-root-cause across ≥2 paths in one cycle, test-discipline failure markers, operator-confusion events, estimate inflation). When a trigger pattern matches, the contributor emits a soft-warning to next session-start additionalContext naming the trigger + suggesting first-principles review before next dispatch. The persona reads + decides whether the review is needed. **Difference from Idea 21:** Idea 21 is the autonomy-pattern stop-hook (rewrites permission-asking in outbound replies); this is the architecture-decay stop-hook (warns on dispatch shape). Both compose with the O program's structural-enforcement substrate. Activation gate: A1 substrate landed + the §4.6 methodology rule has been in use for some weeks (so we know which triggers actually fire). Luke noted he's "not sure if he wants to take it up" — left as draft capture for later evaluation.

- **`KNOWN_CROSS_MODE_DEBT` allowlist drift in loam-mode partition-references audit.** Captured 2026-05-04 during v0.1.8 Cycle 5 release-level smoke. `plugins/dev-sdlc/tools/loam-mode/tests/test_partition_references.py::test_AC_F3_always_loaded_no_dev_refs` fails because the `KNOWN_CROSS_MODE_DEBT` allowlist in the test contains entries no longer present in the source files: `('framework/primary-persona/templates/persona-template/prompt.md', 'docs/rebuild/FUTURE_IDEAS_DRAFT.md')` + 3× `('framework/workspace-sync/README.md', ...)` entries. Pre-existing failure at HEAD c648cf9 (Cycle 4b seal); NOT caused by Cycle 5. The test's design is correct (allowlist must SHRINK over time as debt is paid down); the failure is "good news" (debt was paid down without updating the allowlist). **Source:** Cycle 5 release-level smoke pass. **Provenance:** v0.1.8 Cycle 5 full-suite pytest sweep surfaced this as the only post-cycle failure. **Recommended next step:** `graduate` for v0.1.9 — small (≤5-line) test edit removing the stale entries from KNOWN_CROSS_MODE_DEBT. Composes with the existing "Cross-mode reference debt" entry above. **Cost-of-being-wrong:** zero (does not affect runtime; only affects the partition-audit lint surface).

