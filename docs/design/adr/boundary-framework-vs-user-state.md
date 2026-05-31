# ADR-0001 — the framework ↔ user-state boundary

**Status:** ACCEPTED. **Date:** 2026-05-31. **Roadmap item:** N1
(critical-path head). **Plan:**
`docs/plans/n1-loam-boundary-lock-adr-and-enforcement-gate.md`.

> This is the **first ADR in loam's kernel-decision series** and
> establishes the `docs/design/adr/` convention (D-1 ruling). A later
> kernel author reads this BEFORE writing code that touches user-state —
> it is a citable contract, not a docstring. Subsequent kernel
> architectural decisions (the migration-cursor design, the upgrade-
> trigger UX, …) get their own numbered ADRs here.

---

## §1. Context — why a boundary at all

loam's prime directive is per-user-tuned translation **and protection**.
The protection leg has a load-bearing seam: the line between *the
framework* (loam's own machinery, identical for every user, replaced
wholesale on upgrade) and *user-state* (everything about THIS user and
their work, unique per user, migrated never overwritten).

That seam is what makes the upgrade contract enforceable — a framework
change cannot corrupt user-state, and a prune of framework cruft cannot
delete user content — which is exactly what bounds the blast radius of
every future kernel change. Without a written, enforced boundary, the two
migration systems, the FBM store, the onboarding flow, and the user-model
each invent their own notion of "where state lives," and the seam rots
silently.

This ADR records the decision. The companion release gate
(`check_boundary_respected`, gate 9 in
`framework/tools/loam/src/loam_cli/release/gates.py`) ENFORCES it.

---

## §2. The two sides

**Framework** = loam's own machinery. Everything under `framework/` and
`plugins/`, the doctrine, the methodology, the migration *engine*, the
release gates, the hands-off-lifecycle hooks. Versioned with loam.
Identical for every user. **Replaced wholesale on upgrade.**

**User-state** = everything *about this user and their work*: the per-user
profile / interaction-model, rules / preferences, content, objectives +
work-state, the FBM episode store, AND the applied-migration **cursor**.
Unique per user. **Migrated, never overwritten.**

### The classification rule (the subtle part)

A path is classified by **what it is ABOUT, not by what writes it.**

Framework code routinely *writes* user-state — that is its job.
`establish_loam_layout()` is framework code whose output is the user's
`.loam/` tree. `gates.py`, cost-governance, the hands-off-lifecycle hooks
all write user-state. So the boundary is NOT "framework must not write
user-state." It is:

> **Framework-written user-state must LAND inside one of the two declared
> homes. A framework-code write of user-state to anywhere ELSE is the
> violation.**

---

## §3. The two-tier physical home

User-state has exactly **two** legal physical homes — enumerated in the
declared allowlist `docs/design/adr/user-state-homes.yaml` (see §5):

| Home | Path | Scope | Holds |
|---|---|---|---|
| **global** | `~/.claude/` | cross-workspace | CLAUDE.md, OBJECTIVES.md, the feedback corpus, the per-user interaction model |
| **workspace** | `<workspace>/.loam/` | workspace-scoped | the FBM episode store, the applied-migration cursor (`migrations/.cursor`), the user/session/environment model homes |

Both are already live and both are gitignored on the user side
(`.gitignore`: `.claude/` and `.loam/`). The `.loam/` layout is
established by `establish_loam_layout()` (slice P1.2, `01f3b40`); this ADR
does NOT re-scaffold it — it records and enforces the boundary that
scaffold already embodies.

A framework-code write of user-state to any path outside these two homes
(e.g. a per-user file under `framework/`, or a cwd-relative junk path) is
the boundary violation gate 9 catches.

---

## §4. The seam contract (the upgrade rule)

The two sides cross the seam under exactly one contract:

- **Framework is replaced WHOLESALE on upgrade.** A new loam version
  ships a new `framework/` tree; the old one is replaced (and, once the
  new is proven, pruned — protection-governed). No per-user customization
  lives in framework, so wholesale replacement loses nothing user-specific.

- **User-state is MIGRATED, never overwritten.** A release declares what
  it changes in user-state via a tracked migration contract
  (`docs/state-migrations/`, gate 7); the migration *engine* carries that
  state forward; the applied-migration *cursor* (user-state side) records
  what this workspace has applied. User content is never clobbered by an
  upgrade.

This contract is *why* the boundary is load-bearing: it is the mechanism
that contains blast radius. The migration ENGINE and cursor are already
sealed (`58bead7`); this ADR only references the home that scaffold
established.

### Ratified repo shape — EVOLVE-IN-PLACE (G2)

**The repo shape is evolve-in-place on the existing canonical tree.**
Today's v-next work — the migration engine, the audit subpackage,
keep-pace — all landed *inside* the existing `framework/` tree on `main`.
There is no separate `kernel/` tree. **G2 ratifies evolve-in-place.**
git history is the fallback (not a parallel intact `framework/`).

> **SUPERSEDES** the v-next-build-plan §3 decision-#1 *recommendation* of
> "(a) a clean new structure inside the canonical loam repo … its own
> tree." That recommendation was never executed; practice chose
> evolve-in-place, and **practice is the ratified decision** (locked-design-
> is-not-license, in reverse: practice diverged from the plan's
> recommendation and that divergence IS the decision). A future kernel
> author must NOT build toward a clean tree that is not coming. The
> v-next-plan §3 text carries a dated-and-superseded note pointing here.

---

## §5. How a component declares which side a path is on (D-2)

There is **ONE** source of truth for the legal homes, read by both this
ADR and the enforcement gate: the declared allowlist

> **`docs/design/adr/user-state-homes.yaml`**

It enumerates the two legal homes (`~/.claude/`, `<workspace>/.loam/`) and
the user-state path markers the gate scans for. The gate
(`check_boundary_respected`) reads THIS file as its allowlist — it does
not hardcode a parallel list. Changing the allowlist changes both the
documented rule and the enforced rule simultaneously; they cannot drift.

This mirrors gate-7 (`check_migration_declared`), which reads the declared
migration contract under `docs/state-migrations/` rather than hardcoding
a parallel migration rule (Lens-1 symmetry: compose on the proven
declared-contract pattern, do not invent a second mechanism).

**Why a declared allowlist and not convention-only:** convention-only
(the two homes hardcoded separately in both the ADR prose and the gate
code) permits exactly the doc↔code drift the boundary lock exists to
prevent. The allowlist is the cheapest mechanism that gives doc and check
one source. It is also forward-compatible: if a future runtime PreWrite
guard is built (deferred — see §6), the same allowlist becomes its input.

---

## §6. Enforcement — detection at release, not runtime prevention (N1)

N1's enforcement is a **release-gate detection**: a boundary violation is
CAUGHT before publish by gate 9 (`check_boundary_respected`) in the same
`loam release` pass as the other eight gates. It is NOT (yet) a runtime
PreToolUse/PreWrite *prevention* hook.

Rationale (structural-enforcement-on-recurrence): a rule is escalated to a
runtime hook once it has been violated despite being in the corpus. The
boundary rule is brand new and has not been violated even once; a
release-gate is the proportionate FIRST enforcement, matching gate-7's
declare-and-check precedent exactly. A runtime guard becomes the correct
ESCALATION *if* a real violation ever slips a release — tracked as a
deferred follow-up, not built at N1.

---

## §7. Consequences

- N3 (onboarding), N4 (user-model), and Phase-3 (migrate) all read and
  write user-state THROUGH this locked seam. The allowlist is their shared
  notion of "where state legally lives."
- A release that introduces a framework-code path writing user-state
  outside the two homes goes RED at `loam release` — the leak is caught
  before publish, with a corrective hint naming the offending path and the
  legal homes.
- The boundary is now a **citable contract** (this ADR + the allowlist),
  not a docstring buried in `loam_layout.py`.

---

## §8. Provenance

- Scaffold (not re-built here): `01f3b40` —
  `framework/workspace-bootstrap/src/loam/workspace_bootstrap/loam_layout.py`
  (`establish_loam_layout`, the boundary-rule README prose).
- Migration engine + cursor (referenced, not built): `58bead7`.
- Composition target for enforcement: the release-gate `ALL_GATES` spine,
  `check_migration_declared` (gate 7) the structural twin.
- The two homes' gitignore reality: `.gitignore` (`.loam/`, `.claude/`).
- Superseded recommendation: `docs/plans/loam-vnext-build-plan.md` §3
  decision-#1.
