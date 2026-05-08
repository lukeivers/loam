# loam rename — decisions

**Status:** TABLED 2026-04-23. Rename decisions recorded; execution deferred pending prerequisite amendments (#26 teardown retrofit + open-source launch readiness per Idea 12) and available bandwidth. Un-table when ready to commence the multi-amendment migration.

**Status:** approved 2026-04-23. Execution scheduled as a tiered rename
sequence across multiple future amendments, kicked off after
amendment #23 (frozen-H19 per-invariant baseline, sealed at `a27a833`).

**Research:** `.scratch/claude-output/loam-rename-migration-plan.md`
(inventory, bucketing, phased migration sketch; this doc does not
duplicate its rationale).

**Theme source:** `.scratch/claude-output/pos-v2-rename-brainstorm.md`
(loam = the enriched substrate the user cultivates their Claude agent
in; user-intent = seed, Claude = genetic machinery, grown agent =
plant).

---

## Accepted name

**`loam`.** Four letters, left-hand QWERTY, substrate-not-plant
metaphor that matches what the project actually is: the enriched medium
the user grows their agent in. See the brainstorm pointer above for the
framing.

The canonical "seed" framing at
`docs/spec/pos-v2-objectives-spec.md:73`
(*"a seed from which users develop their own implementations on top of
the core"*) is **preserved** — `loam` names the substrate; the
seed / cultivar / growth metaphor carried in existing narrative is
unchanged.

---

## Approved Tier-1 renames

1. `pos-v2` / `pOS v2` → `loam` — brand, docs, repo directory.
2. `~/.pos/` → `~/.loam/` — per-host config dir.
3. `POS_V2_*` env var prefix → `LOAM_*` — all eight vars; dedupe at
   rename time (see research §2.5).
4. `com.pos-v2.<slug>.*` launchd labels → `com.loam.<slug>.*` — the
   version suffix is dropped concurrently (no `v1` to differentiate).
5. OTel span / event roots `pos.*` → `loam.*` — all 23 roots rebase;
   attribute-level names below the second segment stay unchanged.
6. `pos-amend` CLI → `loam amend` — subcommand under a unified `loam`
   top-level CLI (daily-driver brand concentrator; future subcommands
   like `loam scope new`, `loam status` live under the same umbrella).

Research doc §3 carries the mechanics, breaking-change flags, and
dependency ordering for each of these.

---

## Approved Tier-2 rename

**graceful-degradation → `dormancy`.** The single strongest thematic
rename in the catalogue: dormancy is the exact botanical word for the
behaviour (the system goes quiet when the upstream is unavailable,
resumes without damage when it returns). Directory, package, event
namespace, docs subdir, config-file paths (`degradation.sqlite`,
`degradation-config.yaml`) all cascade. AC prefix `P` stays (P = Policy,
still accurate). Research doc §4.1 has the migration note.

---

## Kept technical — do NOT rename

- **memory-system** — engineer-searchable term; `taproot` would hurt
  clarity. Rejected (research §2.2).
- **self-correction** — ML-industry-recognisable term; `pruning` is
  tempting but loses external recognisability. Rejected (research §4.3).
- **scope-of-work (primitive)** — keep internal name + spec semantics
  + `structural_hash()` etc. `plot` is **acceptable as a user-facing
  CLI alias only** (`loam plot new ...` reads beautifully); the
  primary-persona language layer may prefer "plot" in user prose while
  internal code, tests, proposals, events, and audit trails continue
  to say "scope." Research doc §4.2 has the shape.

Additional keep-technical decisions (orchestrator, safety-layer,
reversibility-primitive, cost-governance, observability-aggregator,
objective-tracker, telegram-interface, self-upgrade, primary-persona,
workspace-bootstrap, hands-off-lifecycle, AC prefixes, error codes,
all ODD/process vocabulary) are enumerated in research doc §6 and
confirmed here by reference.

---

## Rulings on the three open questions

Research doc §8 posed several open questions; three required owner
rulings.

1. **Package layout under the rename — monolithic or flat?**
   **Monolithic `loam.*` namespace.** Imports become
   `from loam.safety_layer import ...`, `from loam.orchestrator
   import ...`, etc. Concentrates identity; single umbrella package
   matches the unified-CLI choice above.

2. **Historical record — rewrite or preserve?**
   **Preserve contemporary terminology.** Commit messages and seal
   narratives that cite "pOS v2" stay untouched; no retroactive
   rewrites. History keeps its own moment. Only current/live docs
   rebrand. (Research doc §8 question 7; this ruling matches the
   recommendation there.)

3. **graceful-degradation → dormancy — rename or keep?**
   **Approved.** See Tier-2 section above.

The remaining §8 questions (repo-rename timing, CLI unification,
plot-alias experiment, plugin pre-naming) are resolved by the Tier-1
list above (unified CLI) or deferred to their own cycles (repo rename,
plugin names).

---

## Migration path

Research doc §7 has the tiered phased plan (Phase 1 documentary
rebrand → Phase 2 code rename → Phase 3 dormancy rename → Phase 4
plugin names deferred → Phase 5 plot CLI alias optional). Each phase
lands as its own amendment or small amendment cluster.

Individual rename amendments **cite this decisions doc** as the
authority for the scope they execute. No new decision authoring
happens inside a rename amendment — amendments execute the decisions
recorded here.

Kick-off is scheduled for after amendment #23 (frozen-H19 per-invariant
baseline, sealed `a27a833`, 2026-04-23). The next amendment cycle
begins Phase 1.

---

## Status

- **Approved:** 2026-04-23 (Luke).
- **Authority for execution:** this doc; research doc for mechanics.
- **First amendment:** Phase 1 (documentary rebrand), to be scoped
  after this commit lands.
