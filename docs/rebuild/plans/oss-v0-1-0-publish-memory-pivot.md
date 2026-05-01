# OSS v0.1.0 publish — memory-substrate pivot — series master plan

**Status:** plan-doc (pre-build, plan-before-code). 2026-05-01.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/` (canonical pos-v2 / future loam).
**Programme master:** `docs/rebuild/plans/oss-v0-1-0-publish.md` — this series slots into §5 work decomposition (placement proposed §6 below).
**Owner authority.** Ruling 2026-05-01 21:09Z on the dispatcher channel:
> "lets do b, but instead of making it a rando opt-in thing, lets develop the graphiti memory system as a plugin for after first launch."

This authorises shape (B) from `.scratch/claude-output/graphiti-vs-native-files-research.md` §6 with the
amendment that graphiti is **not** a rando opt-in — it becomes a first-class loam plugin
landing post-v0.1.0.

**Authority documents:**
- Recommendation research: `.scratch/claude-output/graphiti-vs-native-files-research.md` (279 lines; GREEN/YELLOW/RED matrix; §4 native-extension shapes; §6 recommendation; §7 open questions; §8 halt-and-surface).
- Programme master: `docs/rebuild/plans/oss-v0-1-0-publish.md` §3 prime ACs AC.OSS.1–7; §5 work decomposition; §6 sequencing; §13 decisions register.
- Plugin precedent: `framework/plugins/dev-sdlc/pyproject.toml` (entry-point groups `loam.bootstrap.contributions` + `loam.cli.subcommands`); `framework/plugins/dev-sdlc/dev-mode-manifest.yaml`.
- Partition manifest: `framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml` — currently classifies `framework/memory-system/**` as `dev_and_public` (line 120); this series reclassifies.
- VALUE_PROPOSITION (prime objective): `docs/rebuild/VALUE_PROPOSITION.md` AC.PO.1 + AC.PO.2.
- CLAUDE.md design lenses: `framework/CLAUDE.md` §1 lenses 1/2/3.
- Persona-side surfaces in fence: `framework/primary-persona/src/loam/primary_persona/{memory_consumer.py,memory_write_queue.py,memory_write_worker.py,stop_emitter.py,mcp_memory_client.py,memory_prewarm.py,context_composer.py}`.

---

## 1. Summary / TLDR

**Two-amendment series replacing graphiti as the v0.1.0 default memory
substrate with file-based memory primitives; graphiti retires to a
post-v0.1.0 plugin.**

- **M-FBM (file-based-memory baseline) — v0.1.0 publish-blocker.**
  Authors file-based memory contributor + Stop-hook write target +
  UPS-hook retrieval surface inside `framework/primary-persona/` (no
  new sealed component); reclassifies `framework/memory-system/**`
  from `dev_and_public` to `dev_only` in M2's partition manifest;
  drops graphiti+Ollama+Kuzu+FastMCP+BGE from v0.1.0 synthesis output;
  retire-not-delete posture so M-GMP can relocate.
- **M-GMP (graphiti-memory plugin migration) — post-v0.1.0.** Relocates
  `framework/memory-system/` to `plugins/graphiti-memory/` mirroring
  Dev/SDLC plugin shape (own pyproject, entry-points, scoped tests/
  docs); composes against file-based baseline as graph-shaped
  enrichment, not default substrate. v0.1.x lane post-M12.

**Empirical justification:** 1 retrievable episode after weeks; 216MB /
25,394-traceback err.log; 4 sealed amendments today (#92/#94/#95/#96)
didn't fix reliability; sidecar crashed PID 63402 at 16:04:27 today
under normal workload; 3 of 4 RED-class graphiti surfaces unexercised
by persona's actual retrieval path; auto-memory MEMORY.md already
carries 24 hand-curated rules at zero infra cost.

**Estimated AI-time:** M-FBM 90–180 min midpoint ~135 min;
M-GMP 60–120 min midpoint ~90 min.

**Sequencing:** M-FBM lands v0.1.0 critical path between M5 and M6
(see §6); M-GMP defers v0.1.x lane post-M12.

---

## 2. Owner ruling captured (2026-05-01)

- **Recommendation shape (B) locked.** File-primary baseline at v0.1.0;
  graphiti repositioned. Research §6 accepted.
- **Scope amendment: graphiti is a first-class plugin, not opt-in.**
  Binds graphiti relocation to the plugin-extension protocol
  established by Dev/SDLC plugin (programme §2 R2). `plugins/dev-
  sdlc/` is the second-plugin template.

**Methodology heads-up.** Shape (B) is structurally similar to M9-scrub
reclassification (M9 dropped fixture residuals; M-FBM drops the entire
memory-system runtime). M-FBM fence touches at most 3 components
(primary-persona, workspace-bootstrap, M2 partition manifest);
memory-system source itself is untouched (only its partition class
changes). M-GMP performs the relocation.

---

## 3. Spec-objective placement (per CLAUDE.md §2.5)

The series binds to programme prime ACs:

- **AC.OSS.1 (stranger-bootable).** Removing graphiti as runtime dep
  collapses first-run scaffold by ~1GB (Ollama + BGE + Kuzu +
  sentence-transformers + FastMCP + launchd plist). Stranger-clone
  reaches first useful persona session via files alone.
- **AC.OSS.2 (every shipping component wired).** Memory-system is
  technically wired but delivers ~zero retrieval value (1 episode in
  weeks). Reclassifying as `dev_only` removes a component failing
  the spirit of AC.OSS.2 while preserving source for post-v0.1.0 plugin.
- **AC.OSS.3 (no dev-discipline machinery in synthesis).** Graphiti
  sidecar + FastMCP MCP-server + 216MB err.log are operational
  footguns; reclassification to `dev_only` aligns with partition
  invariant.
- **AC.PO.1 (translation-burden).** User no longer needs to learn
  what graphiti is, why Ollama is required, or how to debug a
  silent-swallow sidecar. Memory shape becomes visible/editable/
  greppable files.
- **AC.PO.2 (toolkit-primitive).** Harness gains file-based-memory
  primitive composing with Claude-native hooks/skills; plugins layer
  enrichment.

**ODD §2.5 reverse-direction commitment.** Every line in either
amendment's diff traces back to an AC; series-level ACs are outcome-
shape only; method-shape is builder's call inside AC outcome bound.

---

## 4. Three-lens analysis (per CLAUDE.md design lenses)

- **Lens 1 (Claude leverage).** **M-FBM** composes against Stop-hook
  (write target) + UserPromptSubmit-hook (retrieval contributor at
  `TriggerKind.turn` via existing `context_composer.py`) + skills
  (`/memory:search`, `/memory:archive`) + auto-memory MEMORY.md
  (orthogonal, Claude-managed; not touched). **M-GMP** composes
  against the workspace-bootstrap extension protocol
  (`loam.bootstrap.contributions` entry-point group, established at
  M6 Dev/SDLC plugin). **Pass on both.**
- **Lens 2 (harness + primary-persona value).** **M-FBM primary-
  persona test:** "remember/read/fix what got remembered" all collapse
  to filesystem operations the persona already understands; graphiti's
  MCP-then-Cypher-then-LLM-extraction shape disappears. **Harness
  test:** new file-based-memory primitive (write target + retrieval
  contributor + 2 skills); future plugins compose against it.
  **M-GMP primary-persona test:** preserves graphiti as opt-in for
  users wanting graph-shaped knowledge; users who don't enable see no
  translation burden. **Harness test:** establishes the memory-
  substrate plugin pattern; sets second plugin precedent.
  **Pass on both.**
- **Lens 3 (ODD authoring).** Each AC below is outcome-shape,
  observable, deterministic. Method-shape (filename convention,
  retrieval-rank algorithm, kuzu_db migration mechanism) is the
  sub-amendment builder's call inside the AC outcome bound. **Pass.**

---

## 5. Acceptance criteria (programme-level invariants for the series)

Outcome-shape only. Method-shape decisions are the per-amendment
builder's call. Each AC carries a deterministic verification.

### AC.MFBM.1 — Stop-hook writes the turn's episode to a file under the workspace's loam memory dir

Stranger-clone first-run yields a workspace where, at every Stop event,
the turn's transcript is written as a markdown file under the workspace
loam memory dir (exact path-shape is M-FBM's builder's call: candidates
include `<workspace>/.loam/memory/episodes/<workspace-slug>/<YYYY-MM-DD>/<turn-id>.md`,
`<workspace>/workspace/.loam/memory/episodes/<...>`, or
`<workspace>/.pos/loam-memory/episodes/<...>`; lock at builder-plan
authoring per D-Q.MFBM.3 below).

**Verification.** After N turns in a fresh workspace, the count of
files under the chosen dir equals N (or N±1 for in-flight turns); each
file's mtime is within 5 s of its turn's Stop event; each file contains
the `[user]` + `[persona]` body bundling the turn matched a fixture
turn-id.

### AC.MFBM.2 — UPS-hook retrieval surface returns relevant prior-session episodes via the file-based contributor

On every UserPromptSubmit, the persona's retrieval contributor emits a
`[memory-retrieval]` `additionalContext` block populated from the
file-based memory dir (not from graphiti). The block format matches the
existing `_render_retrieval` shape (1600-char soft cap, edges-OR-episodes
fallthrough, fail-closed on boundary error).

**Verification.** Across 10 hand-authored cross-session test fixtures
(fixture-shape: a previously-stored turn at session N-1 referencing
named entity X; a session-N prompt mentioning X), the contributor emits
a non-empty retrieval block citing the session-N-1 turn's filename in
≥7 of 10 fixtures. Failure-closed test: deleting the memory dir mid-test
returns an empty retrieval block, not a stack trace.

### AC.MFBM.3 — No graphiti runtime dep in v0.1.0 synthesis output

Synthesis-tool output (post-M2 partition manifest update) contains
zero references to graphiti, kuzu, ollama, sentence-transformers,
fastmcp (in `pyproject.toml` deps, in `framework/<comp>/` source under
the public partition, in workspace-bootstrap's first-run-inventory.yaml
runtime dependencies). The `framework/memory-system/**` glob in the
partition manifest reclassifies from `dev_and_public` to `dev_only`.

**Verification.** Synth canonical HEAD via the M2-extended pipeline;
grep the synthetic tree for literal strings `graphiti`, `kuzu`, `ollama`,
`sentence-transformers`, `fastmcp`, `BGE`, `Ollama`. Allowed residuals:
the M-GMP plugin metadata if M-GMP has landed by synthesis time
(post-v0.1.0 only). Public-tree count of disallowed matches: zero at
v0.1.0; allowed if v0.1.x synthesis runs after M-GMP.

### AC.MFBM.4 — Existing pos3 kuzu_db state migration explicit

The amendment ships an explicit decision (per D-Q.MFBM.6) on whether
existing kuzu_db state migrates into the file-based store or is
discarded. If migrate: a one-shot script translates each Episodic node
under the persona's group_id into a file-based episode at the
appropriate path. If discard: the amendment doc names this explicitly.

**Verification.** Per D-Q.MFBM.6 ruling: either (a) the migration
script runs in a clean test fixture with N seeded episodes and the
file-based dir post-migration contains N markdown files mirroring the
seeded names, or (b) the amendment doc carries a one-line "discarded"
note + a record in the migration plan.

### AC.MFBM.5 — Persona's memory-system MCP-client wiring retires from runtime

The `MemoryClient` Protocol binding in
`framework/primary-persona/src/loam/primary_persona/memory_consumer.py`
no longer instantiates an MCP client at v0.1.0. The
`memory_consumer.py` module retires its current write/read paths in
favour of the file-based contributor's write/read paths. The
`MemoryClient` Protocol may stay as a no-longer-runtime-bound type
if M-GMP intends to reuse it; or may retire entirely. Builder's call.

**Verification.** Grep the synthetic v0.1.0 tree for runtime instantiation
of `MemoryClient` outside of dev-only test fixtures: zero hits.

### AC.MFBM.6 — Skills `/memory:search` + `/memory:archive` (or builder-equivalent) ship at v0.1.0

User-invocable skills for explicit retrieval beyond the 1600-char turn
budget + explicit archival of old episodes. Skill names + scopes
(`paths:`, `disable-model-invocation`) are builder's call inside the
AC outcome bound.

**Verification.** `/memory:search <query>` returns a multi-result list
greater than the 1600-char turn-budget block when invoked with a
fixture seeded with ≥10 matching episodes. `/memory:archive <date>`
moves episodes older than the named date under an `archived/` subdir.

### AC.MFBM.7 — Workspace-bootstrap first-run-inventory drops memory-system service registration

`framework/first-run-inventory.yaml` (per partition manifest line 134)
no longer references the graphiti-service launchd plist, no longer
provisions the kuzu_db dir, no longer requires Ollama presence as a
first-run check. The file-based memory dir is created (if needed) by
workspace-bootstrap as a no-op `mkdir -p` step.

**Verification.** Diff `framework/first-run-inventory.yaml` against
pre-amendment baseline; the graphiti-service + kuzu_db + Ollama-check
entries are absent. Stranger-clone first-run on a host without Ollama
installed reaches the first useful primary-persona session.

### AC.MFBM.S — Sealed-component fence

Sealed components in M-FBM's fence: **primary-persona** (memory_consumer
+ context_composer surfaces — write/read pipeline change), **workspace-
bootstrap** (first-run-inventory.yaml + bootstrap adapter for
graphiti-service retire), **M2 partition manifest** (admitted via
universal-paths). `memory-system` itself is NOT in the fence —
its source is untouched (only its partition classification changes).
The dev-sdlc plugin's `dev-mode-manifest.yaml` may need a parallel
classification update if memory-system tests live there post-M6.

### AC.MGMP.1 — graphiti-memory plugin loads from `plugins/graphiti-memory/`

The relocated tree at `plugins/graphiti-memory/` carries its own
`pyproject.toml` (name `loam-plugin-graphiti-memory`, version
`0.1.0`), declares the `loam.bootstrap.contributions` entry-point
mirroring Dev/SDLC's pattern, ships its own README + dev-mode-manifest
(if dev-only artefacts exist), and exposes a memory-provider
contribution that the persona's contributor surface can compose
against.

**Verification.** Plugin's own AC suite passes; plugin-loading exercised
by a smoke test in `framework/workspace-bootstrap/tests/` or the
plugin's own tests; `loam --help` (or equivalent) surfaces any plugin-
contributed CLI verbs.

### AC.MGMP.2 — graphiti-memory plugin composes against the file-based baseline as enrichment, not replacement

When the plugin is enabled, retrieval calls return both the file-based
results (always) AND graphiti graph-traversal results (additive).
Disabling the plugin returns to the file-based-only behaviour.
Composition rule: file-based results are the floor; graphiti results
are additive enrichment.

**Verification.** Test fixture with the plugin disabled returns
file-based results only. With the plugin enabled and a seeded kuzu_db,
the contributor returns both. Disabling mid-session returns to
file-based-only on the next UPS event.

### AC.MGMP.3 — partition manifest reclassifies `framework/memory-system/**` retired path

After M-GMP relocation, `framework/memory-system/**` no longer exists;
the partition manifest's reference (currently `dev_only` post-M-FBM)
either retires entirely or carries a deprecation comment pointing
at `plugins/graphiti-memory/`. The new path
`plugins/graphiti-memory/**` classifies as `dev_only` (mirrors
Dev/SDLC plugin per partition manifest line 216) at v0.1.x — the
plugin is dev-only at the synthesis-tool level, but optionally
loaded by users post-clone.

**Verification.** Partition manifest grep for `framework/memory-system`
returns zero hits post-M-GMP; partition manifest grep for
`plugins/graphiti-memory/` returns the expected `dev_only` glob entry.

### AC.MGMP.4 — graphiti-service launchd plist relocates with plugin

The launchd plist label + script for `graphiti-service` (currently
`com.loam.<slug>.graphiti-service` post-M1c rename) relocates from
its current canonical location to plugin-scoped under
`plugins/graphiti-memory/`. Workspace-bootstrap's adapter loads the
plist only when the plugin is enabled.

**Verification.** Stranger-clone with the plugin disabled has zero
launchd plist registrations under `com.loam.<slug>.graphiti-service*`
after first-run. Enabling the plugin via the standard plugin-load
mechanism + re-running first-run-inventory provisions the plist.

### AC.MGMP.S — Sealed-component fence

Sealed components in M-GMP's fence: **memory-system** (renamed to
plugin-scoped path; tree relocates entirely; no source-shape changes
beyond import-path updates and the new plugin pyproject), **workspace-
bootstrap** (adapter rewires from canonical-path to plugin-path),
**M2 partition manifest** (universal-paths admission for the
reclassification). Mirrors Dev/SDLC plugin's fence shape.

---

## 6. Sequencing — slot proposal in master plan §5

The master plan §5 currently sequences M5.wire-dormancy → M6.dev-sdlc-
plugin → M9.scrub → M11.dry-run → M12.publish. The proposed slot for
M-FBM is **after M5.wire-dormancy and before M6.dev-sdlc-plugin** in
the v0.1.0 critical path; M-GMP defers to the v0.1.x lane post-M12.

**Concrete sequencing rules:**

1. **M-FBM after M5.** Both touch workspace-bootstrap; per
   `feedback_serialize_amendment_builds`, no parallel; M-FBM
   inherits M5's stable surface.
2. **M-FBM before M6.dev-sdlc-plugin.** (a) M6 is largest single
   cycle (~135 min); benefits from stable memory surface. (b) M6
   establishes the plugin pattern M-GMP inherits; plugin-shape
   decisions surfacing at M-FBM (D-Q.MFBM.5 `MemoryProvider`
   Protocol) inform M6's choices.
3. **M-FBM gates M9.scrub** (programme master §6 rule 7) and
   **M11.dry-run** (synthesises against M2-extended manifest).
4. **M-GMP runs post-M12.publish.** Not a v0.1.0 publish-blocker;
   v0.1.x followup establishing the second plugin pattern.

**Master plan §5 row insertions (proposed):**

```
| **M-FBM** | oss-v0-1-0-publish-memory-pivot.md | Multi-component sealed amendment (primary-persona + workspace-bootstrap + M2 partition manifest). File-based memory replaces graphiti as v0.1.0 default; Stop+UPS hook contributor; partition reclassifies memory-system as dev_only; first-run-inventory drops graphiti-service. | AC.MFBM.1..S | 90–180 min | 135 min |
| **M-GMP** | oss-v0-1-0-publish-memory-pivot.md | Multi-component sealed amendment (graphiti relocation to plugins/graphiti-memory/; bootstrap adapter rewire; partition reclass). v0.1.x lane. | AC.MGMP.1..S | 60–120 min | 90 min | (post-M12) |
```

Master plan §6 Lane A becomes: M1.rename-series → M2.partition →
M3.wire-clis → M4.wire-dispatch → M5.wire-dormancy → **M-FBM.memory-
pivot** → M6.dev-sdlc-plugin → M9.scrub → M11.dry-run → M12.publish.

**Programme total impact.** M-FBM 135-min adds to v0.1.0 critical
path: was 9–14 h AI wall midpoint; now 11–17 h midpoint ~13 h.
M-GMP 90-min sits in v0.1.x lane, not counted.

**Safety property.** Graphiti runtime remains live in canonical tree
post-M-FBM and through M11.dry-run — the only change is partition
manifest reclassification (hidden from synthesis but still runs in
canonical dev mode). M-GMP does not rush; canonical retains working
graphiti until M-GMP lands.

---

## 7. Hard constraints (series-wide)

- **No new external runtime deps in M-FBM.** File-based memory uses
  Python stdlib only (pathlib, datetime, json/yaml). The grep-based
  retrieval may use stdlib `re` or invoke `ripgrep` via subprocess if
  available; no new third-party dep.
- **No structural changes to memory-system source in M-FBM.** Only
  the partition classification changes. The source tree at
  `framework/memory-system/` stays as-is until M-GMP relocates it.
- **No graphiti-service shutdown in M-FBM.** The launchd service
  continues running in the canonical dev-mode session (it is
  reclassified as `dev_only` not killed). Owner can manually stop the
  service post-M-FBM if desired; the amendment does NOT bootout the
  service.
- **No git-history rewrite.** Memory-system's commit history is
  preserved; M-GMP's relocation uses `git mv` (or equivalent
  history-preserving move) per loam-rename-decisions Q1.
- **No `git commit --amend`.** Corrective commits are NEW commits per
  `feedback_no_amend_in_agent_dispatches`.
- **`pos-amend apply` (or post-rename `loam amend apply`) BEFORE the
  seal commit** in every sub-amendment per FIDRAFT note from
  amendment #41.
- **AC-prefix uniqueness:** M-FBM uses `AC.MFBM.*`; M-GMP uses
  `AC.MGMP.*`. Collisions structurally impossible.
- **Auto-memory MEMORY.md is NOT touched.** The `~/.claude/projects/
  <slug>/memory/` corpus is Claude-managed; loam does not edit, mirror,
  or supersede it. The relationship is captured in D-Q.MFBM.4.
- **Halt-and-surface on ODD §2.5 violations** in any code/doc/manifest
  the builder edits or reads (per `feedback_subagent_odd_violation_halt`).

---

## 8. Out of scope (series-wide; named explicitly per ODD §2.5)

- **Embedding-similarity ranking at v0.1.0** (research §3 row 12,
  YELLOW). Deferred; M-GMP restores via graphiti or future plugin.
- **Cross-encoder reranking** (research §3 row 17, RED). M-GMP.
- **Cross-episode entity dedup / community detection** (research §3
  row 15, RED). M-GMP.
- **Graph-traversal queries (`center_node_uuid`)** (research §3 row
  14, RED). M-GMP.
- **Anthropic server-side Memory API integration** (research §7
  open-q 1; surface uncertain). Re-evaluated post-publish.
- **Stop-hook subagent for entity extraction** (research §3 row 10,
  YELLOW). Post-v0.1.0; gates retrieval-quality only at high N.
- **MCP-server-over-file-store** (research §4). Future shape if
  non-Claude-Code clients consume loam memory.
- **Per-component CLI for memory ops** (`loam memory list`). FUTURE_
  IDEAS_DRAFT capture post-build.
- **InstructionsLoaded hook for memory-load verification.** Out of
  scope unless structural-enforcement need surfaces.
- **Retention-class enforcement (D5/D10).** Unexercised by persona
  writes per research §1.4; rich D5/D10 surface preserved in
  memory-system source for M-GMP; M-FBM does not re-implement.
- **Token-usage observability sink.** Lives in LLM client wrapper.
  Audit `ClaudePrintLLMClient` for residual coupling per research
  §7 open-q 6 (if Stop-hook entity-extraction is not built, wrapper
  retires; M-GMP-internal cleanup).

---

## 9. Halt-and-surface conditions

Per `feedback_subagent_odd_violation_halt` + `feedback_critical_thinking_
on_deviations`. Builders halt + surface to dispatcher on any of:

1. **Stranger-clone first-run on host without Ollama** doesn't reach
   first useful primary-persona session post-M-FBM. Means retire
   incomplete; widen fence.
2. **File-based contributor fails the cross-session-continuity test**
   (research §6 probe 1; AC.MFBM.2's ≥7 of 10 fixtures bar). Owner
   rules: extend M-FBM (embedding sidecar / sqlite-FTS5 / different
   episode-shape) or defer publish to v0.1.1 with file-based MVP.
3. **ODD §2.5 violation surfaces in surrounding code/docs.** Halt;
   no silent extension.
4. **Plugin pattern at `plugins/dev-sdlc/` doesn't compose with
   M-GMP's plugin shape** — entry-point group conflicts (`dev_sdlc`
   vs `graphiti_memory`); CLI-subcommand collisions (`loam project`
   vs `loam memory`); workspace-bootstrap adapter discovery order
   races. Owner rules.
5. **Pre-existing test fails post-amendment** (other than mechanical
   fixture updates for the surface shift). Per programme master §8
   halt trigger 9.
6. **Wall-time exceeds estimate by >50%.** Per programme master §8
   halt trigger 8.
7. **No new third-party deps in M-FBM** (HC-equivalent). New deps
   require permitted-list amendment + owner ruling.
8. **kuzu_db inspection finds episodes contradicting research §5
   evidence** (1 episode in weeks). Halt; owner re-rules D-Q.MFBM.6.
9. **Auto-memory + loam-memory collide on retrieval relevance** (same
   content surfaced twice; clutters retrieval block). Owner rules
   D-Q.MFBM.4.
10. **M11 dry-run reveals graphiti-residual references** in synthetic
    v0.1.0 tree (Ollama in public README, kuzu in public pyproject,
    FastMCP in public settings.json). Fold back to M-FBM; primary
    M11 sweep check.
11. **first-run-inventory.yaml mid-amendment finds undocumented
    coupling** between graphiti-service and another service (e.g.
    observability-aggregator subscribes to graphiti spans; scope-
    of-work invokes graphiti via MCP). Halt; extend fence or
    sequence as follow-on.
12. **`MemoryClient` Protocol referenced outside `memory_consumer.py`**
    in non-test code. Widen fence.

---

## 10. Risks (series-level)

1. **File-based retrieval-quality empirical risk** (research §6 probe 1).
   Mitigation: AC.MFBM.2's 7-of-10 fixtures bar; halt §9.2 fires if missed.
2. **kuzu_db state loss** (D-Q.MFBM.6 recommends discard). Mitigation:
   one-shot inspection script lands at amendment time; halt §9.8 fires
   if state contradicts research §5 evidence.
3. **Plugin-pattern-creep at M-GMP.** Mitigation: M-GMP defers to
   v0.1.x; pattern stabilises after second plugin (M-GMP) lands.
4. **Stop-hook write-failure silent-loss.** Mitigation: AC.MFBM.1
   permits a fail-loud sibling `.loam/memory/.errors` log; surfaces via
   observability-aggregator.
5. **launchd plist orphaning post-M-FBM.** The plist continues running
   in canonical dev tree (acceptable per series constraint); owner can
   `launchctl bootout` manually; M-GMP relocates plist at the right time.
6. **Decision-reversal cost if file-based retrieval underperforms post-
   publish.** Recovery path: M-GMP-early (rush graphiti to v0.1.1 instead
   of v0.1.x) — structurally short, not a re-architecture.

---

## 11. Decisions remaining for owner ruling

Per `feedback_summarize_and_surface_decisions` — six named decisions
with recommendations. Owner rules from this summary.

### D-Q.MFBM.1 — Episode file shape

**Q.** One markdown file per turn / append-to-daily-log /
summarised-monthly Stop-hook-subagent rollup?
**Rec.** **One file per turn.** Closest to graphiti's episode shape;
greppable; user-editable; ~5MB/yr/workspace footprint. Rolling-
summary is YELLOW-class; deferred post-v0.1.0.

### D-Q.MFBM.2 — Retrieval mechanism

**Q.** Pure grep+BM25-via-sqlite-FTS5 / embedding sidecar (faiss/
lance/sqlite-vss) / Claude-native skill-based / LLM-summarisation-
on-read / layered.
**Rec.** **Layered with grep as default.** Per turn: `find` recent
N + `rg -l <terms>` + content extraction + BM25-rank + render top-5.
Skills `/memory:search`, `/memory:archive` fall through explicitly.
Subagent-as-deep-retriever is YELLOW-class; deferred. **No embedding
index at v0.1.0** — research §5 single-workspace volume doesn't need
it; M-GMP / v0.1.x plugins reintroduce it if needed.

### D-Q.MFBM.3 — Memory-dir location

**Q.** Three candidates: `<workspace>/.loam/memory/`,
`<workspace>/workspace/.loam/memory/`, or `<workspace>/.pos/loam-
memory/` (collapse with existing `.pos/memory-write-queue/`).
**Rec.** **`<workspace>/.loam/memory/`.** Aligns with M1b's
`<workspace>/.pos/` → `<workspace>/.loam/` rename (sealed
2026-04-29); workspace-root-scoped is structurally clearer than
the duplicated `workspace/.loam/`; keeps `vim <workspace>/.loam/
memory/...` as the user-visible-edit shape. Builder may pivot if
M1b's landed shape differs; dispatcher verifies M1b state at
M-FBM dispatch time.

### D-Q.MFBM.4 — Relationship to Claude Code's auto-memory

**Q.** Loam memory dir vs auto-memory at `~/.claude/projects/
<slug>/memory/MEMORY.md`: orthogonal / unified / cross-linked?
**Rec.** **Orthogonal.** Auto-memory = project-scoped, Claude-
managed, learned-from-corrections rules. Loam memory = workspace-
scoped, loam-managed, per-turn-episode. The two compose by Claude
reading both at session start (auto-memory automatically; loam-
memory via SessionStart-hook-contributed recent-N episodes). M-FBM
does NOT touch auto-memory. Surface the distinction in v0.1.0 docs
(positioning + odd + getting-started).

### D-Q.MFBM.5 — Plugin entry-point pattern for graphiti-memory

**Q.** Existing `loam.bootstrap.contributions` only, or NEW
`loam.memory.providers` group for future memory-substrate plugins?
**Rec.** **Both.** Bootstrap entry-point = universal discovery
(every plugin registers); new `loam.memory.providers` =
substrate-composition contract (each provider exposes a
`MemoryProvider` Protocol with `add_episode`, `search`, `health`).
Persona contributor reads all registered providers; file-based
always first, graphiti additive when registered. M-FBM authors the
Protocol stub (zero runtime impact); M-GMP implements graphiti's
provider against it. Generalises cleanly for future memory-substrate
plugins.

### D-Q.MFBM.6 — Migration of existing kuzu_db data

**Q.** Discard at v0.1.0 or backfill into file-based store?
**Rec.** **Discard, with one-shot inspection script that surfaces
findings BEFORE discard.** Script lands at M-FBM build-time; reports
episode count + size + group_id distribution. If it contradicts
research §5 (1 episode after weeks), halt §9.8 fires + owner re-
rules. Discard rationale: kuzu_db is in untracked
`workspace/data/memory-system/`; canonical retains graphiti until
M-GMP (state not lost, just no longer persona's read source);
backfill needs LLM-pass-per-episode (not budgeted). Decision
reversible: M-GMP can write a kuzu→files migration if surfaced.

---

## 12. Halt-and-surface findings encountered during plan authoring

Per the dispatch's halt-and-surface clause: surface any audit /
methodology / surrounding-code / surrounding-docs ODD violations
encountered while authoring this plan.

**Findings (none triggers a halt):**

1. **No methodology breach.** Two-amendment shape maps cleanly onto
   the OSS-publish programme's amendment-sequence shape; each AC
   outcome-shape.
2. **`memory-system/src/factory.py` lines 200–207 swallow Binder
   exceptions** (research §8.1) — silent-graceful-fallthrough CDC
   violation tracked in FUTURE_IDEAS_DRAFT line 119. M-FBM removes
   this from public synthesis via reclassification; M-GMP-builder
   is natural owner for cleanup at relocation.
3. **`memory-system/config/memory.yml` 4 ephemerality rules guard
   telemetry-shape sources persona never writes** (research §1.5 +
   §8.2) — non-objective code by ODD §2.5 strict reading. M-FBM
   does not touch source; flagged for M-GMP-builder.
4. **Research §6 probe 1 risk surfaced explicitly:** file-based may
   underperform at high cross-turn entity-recall volume. Risk
   accepted via D-Q.MFBM.2 recommendation + AC.MFBM.2 7-of-10 bar
   + halt-trigger §9.2.
5. **Sequencing dependency on M1b verified:** D-Q.MFBM.3 memory-
   dir-location depends on M1b's `<workspace>/.loam/` rename;
   M1b sealed 2026-04-29 per master plan §14 — clean.
6. **Anthropic server-side Memory API uncertainty** (research §7
   open-question 1; CLAUDE_CAPABILITIES §3.8). Out-of-scope per §8;
   re-evaluated post-publish.
7. **Auto-memory MEMORY.md scale ceiling** (200 lines / 25KB per
   session; research §7 open-question 3). Orthogonal-not-collapsed
   per D-Q.MFBM.4 recommendation; loam-memory has its own scale
   runway.

**Halt summary.** None triggers a halt. All findings surfaced; plan
authorised pending owner sign-off on §11 D-Q.MFBM.1..6.

---

## 13. Out-of-band: master programme plan §5 row update

The master plan `oss-v0-1-0-publish.md` §5 does NOT yet carry M-FBM
or M-GMP rows. **Next dispatcher (post-this-commit) edits the master
plan** to insert M-FBM between M5.wire-dormancy and M6.dev-sdlc-
plugin per §6 + add M-GMP in v0.1.x lane. **This plan-doc commit
does NOT edit the master plan** — separate doc-only commit at next
dispatch, mirroring M1.rename-series's master-plan-update protocol.
Programme total re-prices: was 9–14 h AI wall; post-pivot 11–17 h
AI wall midpoint ~13 h, M-GMP in v0.1.x lane not counted toward
v0.1.0 critical-path total. Master plan §13 D-Q.OSS.* register
gains no new entries (D-Q.MFBM.* decisions are series-local).

---

## 14. Method-decision register (post-build, per amendment)

Filled by each amendment's builder post-build per existing precedent
(M1.rename-series; D-build.M9.* in scrub).

### M-FBM — OSS-build.M-FBM.x — (post-build)

- D-build.M-FBM.1: Episode file shape (D-Q.MFBM.1).
- D-build.M-FBM.2: Retrieval mechanism (D-Q.MFBM.2).
- D-build.M-FBM.3: Memory-dir location (D-Q.MFBM.3).
- D-build.M-FBM.4: Auto-memory relationship (D-Q.MFBM.4).
- D-build.M-FBM.5: `MemoryProvider` Protocol stub shape (D-Q.MFBM.5).
- D-build.M-FBM.6: kuzu_db migration (D-Q.MFBM.6).
- D-build.M-FBM.7..N: builder-discovered method decisions.

### M-GMP — OSS-build.M-GMP.x — (post-build, post-v0.1.0)

- D-build.M-GMP.1: plugin entry-point group decisions (D-Q.MFBM.5).
- D-build.M-GMP.2: launchd plist relocation mechanism.
- D-build.M-GMP.3: workspace-bootstrap adapter rewire shape.
- D-build.M-GMP.4..N: builder-discovered method decisions.

### Commit SHAs

- M-FBM plan-doc / feature / apply / corrective(s) / seal: `<TBD>`
- Master-plan-update doc-only commit: `<TBD>` (next dispatch).
- M-GMP plan-doc / feature / apply / seal: `<TBD>` (post-v0.1.0).

---

## 15. References

- **Recommendation research:** `.scratch/claude-output/graphiti-vs-native-files-research.md`.
- **Programme master:** `docs/rebuild/plans/oss-v0-1-0-publish.md`.
- **Plugin precedent:** `framework/plugins/dev-sdlc/{pyproject.toml,dev-mode-manifest.yaml}`;
  `docs/rebuild/plans/oss-v0-1-0-publish-dev-sdlc-plugin.md`.
- **Partition manifest:**
  `framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml`
  (current `framework/memory-system/**` classification: line 120 `dev_and_public`).
- **Persona-side surfaces in fence:**
  `framework/primary-persona/src/loam/primary_persona/{memory_consumer.py,memory_write_queue.py,memory_write_worker.py,stop_emitter.py,context_composer.py,mcp_memory_client.py,memory_prewarm.py}`.
- **Memory-system tree to relocate at M-GMP:** `framework/framework/memory-system/`
  (under D-architecture nested path; → `plugins/graphiti-memory/`).
- **Empirical evidence pile (per dispatch):**
  `workspace/data/memory-system/graphiti-service.err.log` (216MB; 25,394 tracebacks);
  `workspace/data/memory-system/kuzu_db/` (1 episode after weeks);
  `~/Library/Logs/DiagnosticReports/Python-2026-05-01-160431.ips` (sidecar crash).
- **Auto-memory corpus (orthogonal):** `~/.claude/projects/-Users-lukeivers-pos3/memory/`.
- **CLAUDE.md design lenses:** `framework/CLAUDE.md` §1.
- **VALUE_PROPOSITION:** `docs/rebuild/VALUE_PROPOSITION.md` AC.PO.1 + AC.PO.2.
- **Memory bullets carried forward (cited per dispatch corpus):**
  `feedback_plan_before_code`, `feedback_subagent_odd_violation_halt`,
  `feedback_summarize_and_surface_decisions`, `feedback_critical_thinking_on_deviations`,
  `feedback_serialize_amendment_builds`, `feedback_no_amend_in_agent_dispatches`,
  `feedback_dispatch_explicit_pos_amend_apply`, `feedback_value_proposition_as_prime_objective`,
  `feedback_duration_estimation_rubric`.

---

*End of plan.*
