# v0.1.7 Cycle 3 — layered-skill discovery mechanism

**Status:** plan authored 2026-05-04; pre-code per `feedback_plan_before_code`.

**Predecessor seals:**
- `3aa20dd` — v0.1.7 Cycle 1 (5 subagent personas + symlink registration).
- `73505f0` — v0.1.7 Cycle 2 (per-project PM as NEW component).

**Parent plan:** `docs/rebuild/plans/v0-1-7-personas-pm-layered-skills.md` §5 AC.LAYERED.* family + §6 Cycle 3.

**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/` (canonical pos-v2). NOT pos3.

---

## §1 — Outcome shape (the "why")

The Anthropic SKILL.md primitive auto-discovers skills at three locations
(personal / project / plugin). v0.1.6 pre-created `<workspace>/.claude/skills/.gitkeep`
so the project-skill directory exists at session-zero. Cycle 1 layered the
plugin-shipped subagent personas into `<workspace>/.claude/agents/<name>.md`
via auto-symlinking at first-run. Cycle 3 mirrors that pattern for **skills**:
plugin-shipped skills (`plugins/<plugin>/skills/<name>/SKILL.md`) are
auto-symlinked into `<workspace>/.claude/skills/<name>/` so Claude Code's
project-skill discovery surface picks them up uniformly.

The *workspace-local skill discovery* surface (operator-authored
`<workspace>/.claude/skills/<name>/SKILL.md`) is Anthropic-native — we don't
re-implement it. We just guarantee the directory + symlinks are in place at
session-zero and that override semantics behave correctly when an operator
authors a workspace-local skill with the same name as a plugin one
(workspace-local wins).

**The release-note promise:** every plugin-shipped skill is discoverable in
the `/` menu of every workspace from session-zero, and operators can author
workspace-local SKILL.md files that override plugin skills without manual
symlink fiddling.

---

## §2 — Lens checks (per CLAUDE.md design lenses)

### Lens 1 — Claude-leverage-first

This entire feature *composes on top of* Anthropic's native SKILL.md
discovery primitive. We don't re-implement skill discovery; we just ensure
the directory + symlinks are in place so Anthropic's auto-walk picks them up.
The required Claude capability: project-skill discovery at
`<workspace>/.claude/skills/<name>/SKILL.md`. Verified 2026-05-04 in
`docs/rebuild/plans/layered-skill-story-research-2026-05-04.md` §1.4.

### Lens 2 — Harness + primary-persona value

- **Primary-persona test:** workspace-local skills automatically auto-load
  when relevant — the persona doesn't need to derive a procedure from
  CLAUDE.md when a skill capturing it exists. Reduces translation burden
  ("how do I do X here?" → invoked skill body).
- **Harness test:** plugin-shipped skills become a reusable toolkit the
  primary persona draws from in any workspace. Adds to harness toolkit.

Both pass.

### Lens 3 — ODD authoring

Outcome (above) + named ACs (§4 below) + halt-trigger constraints
(§5 below) + acceptance (§6 below). Method is the builder's call.

### Lens 4 — Prompt scope ↔ confidence

Outcome confidence is **HIGH**: we have a verified-working precedent (Cycle 1
agent symlinking) and the Anthropic discovery primitive is documented +
verified. Tight scope: mirror Cycle 1's pattern for skills; halt and surface
if the primitive doesn't behave as expected on smoke. Method (file
structure / API shape / collision sentinel mechanism) stays the builder's
call.

### Lens 5 — Swarming

Single-component fence (`framework/workspace-bootstrap/`); no
sub-task partition with tighter ACs than the parent — decomposition would
add only coordination overhead. Stop at single-cycle granularity.

---

## §3 — Single-component fence

**Scope:** `framework/workspace-bootstrap/` only.

- Modify `framework/workspace-bootstrap/src/loam/workspace_bootstrap/adapters/first_run_scaffold.py`
  to add `_symlink_plugin_skills()` mirroring `_symlink_plugin_agents()`,
  wire into the scaffold flow, and add `PluginSkillCollisionError`.
- New test files at `framework/workspace-bootstrap/tests/`.
- Universal-admitted artefacts:
  - `docs/rebuild/plans/v0-1-7-cycle-3-layered-skill-discovery.md` (this doc).
  - `docs/rebuild/plans/v0-1-7-cycle-3-layered-skill-discovery.manifest.yaml`.
  - `docs/design/layered-skill-architecture.md` (per parent plan Surface #10).

---

## §4 — AC family — `AC.LAYERED.*`

Locked exactly as named in parent plan §5:

- **AC.LAYERED.1 — workspace-local skill discoverable via Anthropic-native
  discovery (smoke).** Status-file recorded smoke: a manually-created
  workspace-local SKILL.md appears in the `/` menu without restart.
  Halt-and-surface if discovery fails. Verified by status-file in §6
  smoke D1 + D5.
- **AC.LAYERED.2 — plugin skills auto-symlinked at first-run.** Test
  asserts `<workspace>/.claude/skills/<name>/` exists as a symlink to
  `plugins/loam-skills/skills/<name>/` for all 8 base skills, after
  running the scaffold. Idempotent (second run does not duplicate).
- **AC.LAYERED.3 — collision-handling on workspace-local skill shadowing
  plugin skill.** Test pre-creates `<workspace>/.claude/skills/<name>/`
  as a non-symlink directory (operator-authored override); scaffold
  detects the collision and **halts-and-surfaces** with
  `PluginSkillCollisionError`. Operator-precedence preserved.
- **AC.LAYERED.4 — collision-handling on TWO plugins shipping the same
  skill name.** Tests construct two plugins each with `<plugin>/skills/foo/SKILL.md`;
  scaffold detects the cross-plugin collision and halts-and-surfaces with
  `PluginSkillCollisionError`. (Defensive — unlikely today; future-proofing
  per dispatch.)
- **AC.LAYERED.5 — design-note `docs/design/layered-skill-architecture.md`
  present.** File articulates the 3-tier model (base / plugin / workspace-local);
  override semantics; lifecycle; the auto-symlinking mechanism + collision
  rules; references Anthropic SKILL.md spec.
- **AC.LAYERED.6 — discovery in canonical pos-v2 (smoke).** Status-file
  recorded smoke: live `claude` session in canonical pos-v2 lists ALL
  plugin skills (8 base) via the workspace-local `.claude/skills/` surface.
  Confirms auto-symlinking is functional end-to-end.
- **AC.LAYERED.7 — `.gitkeep` idempotency.** A second invocation of the
  scaffold does not re-write the `.gitkeep` (verified by mtime / content);
  pre-existing operator edits to `.gitkeep` are preserved.

ODD §2.5 mapping: every test maps to exactly one named AC; named-references
checks (e.g., "8 skills" count) pin the AC text to a concrete observable.

---

## §5 — Halt triggers

- WD drifts away from `/Users/lukeivers/ivers-corp-pos-v2/` → halt + surface.
- Plan-doc not authored before code → halt (this is *the* plan-doc; if you
  are writing code without this doc, you are violating).
- Anthropic SKILL.md discovery doesn't behave as expected on D1/D5 smoke →
  halt + surface.
- Workspace-local skill discovery requires an explicit Claude Code config
  flag we haven't accounted for → halt + surface.
- More than 5 in-build decisions need Luke escalation → halt + describe.
- Cycle 3 wall-clock exceeds 5 hours → halt with partial findings.

---

## §6 — Smoke (REALISTIC CONDITION — all 6 dimensions)

Per dispatch:

- **D1 cold-state.** Fresh canonical workspace; bootstrap creates
  `.claude/skills/.gitkeep` + symlinks all 8 base skills from
  `plugins/loam-skills/`. All 8 should be discoverable in `/` menu.
- **D2 steady-state.** Skill discovery stays clean across N (5+) sessions;
  no symlink rot; no collision regression.
- **D3 restart.** Symlinks survive process restart; skills remain discoverable.
- **D4 reboot.** Symlinks + .gitkeep survive macOS reboot (or `launchctl
  bootout` + `bootstrap` cycle equivalent).
- **D5 cross-session.** Workspace-local SKILL.md created mid-session is
  visible after `/clear` (cross-session continuity = the ship-test).
- **D6 telemetry-floor.** Skill-discovery events log per audit-trail floor;
  if a natural Cycle 2 PM audit-log tie-in exists, use it; if not,
  document as Cycle 4 wire-up.

Smoke status file: `/Users/lukeivers/pos3/workspace/.scratch/claude-output/v0-1-7-cycle-3-status-2026-05-04.md`.

---

## §7 — Method-level choices (builder's call per ODD §1.1)

The Cycle 1 agent-symlink helper (`_symlink_plugin_agents`) is the structural
template. Method choices that fall out:

1. **Skill-directory granularity.** Anthropic's SKILL.md discovery is
   per-directory: `<plugin>/skills/<name>/SKILL.md`. So the symlink target
   is the **directory** (`<plugin>/skills/<name>/`) not the file
   (`<plugin>/skills/<name>/SKILL.md`). Symlink at
   `<workspace>/.claude/skills/<name>` → `<plugin>/skills/<name>/`. This
   matters because skills can ship companion files (scripts/, references/, etc.)
   and the discovery walk needs the whole directory.

2. **Walk skill-dir candidates.** Iterate `plugins/<plugin>/skills/`; for
   each child entry, accept if it is a directory containing `SKILL.md`.
   Skip flat-file `<plugin>/skills/<name>.md` shapes — those are not
   per-spec discoverable; halt-and-surface only if explicitly named in
   parent plan as in-fence (not the case here).

3. **`PluginSkillCollisionError`.** Mirrors `PluginAgentCollisionError`
   (same `BootstrapError` parent + `ERR_HANDS_OFF_INTERNAL` code).
   Two collision shapes:
   - **Workspace-local override:** target `<workspace>/.claude/skills/<name>`
     exists as a non-symlink directory (operator-authored). Scaffold
     halts-and-surfaces; operator either renames or deletes their dir
     to accept the plugin skill. (Per dispatch: "the plugin-tier symlink
     is renamed to `<name>.shadowed` or skipped". Picked **halt-and-
     surface** as cleaner — same shape as agents; operator-precedence
     uniform.)
   - **Cross-plugin collision:** two plugins ship the same skill name.
     First-encountered plugin wins on the `for` loop; second raises.
     Same exception type with `kind=` discriminator.

4. **Idempotence.** Symlinks pointing at the correct target are left
   untouched. Symlinks pointing elsewhere (operator manually retargeted)
   are left untouched (operator-precedence). Only non-symlink collisions
   raise.

5. **Plugin-root resolution.** Reuse `_resolve_plugins_root()` from
   Cycle 1 — same canonical/derived layout logic.

6. **Wire-up.** Add `_symlink_plugin_skills(Path(ws))` immediately after
   `_symlink_plugin_agents(Path(ws))` in the scaffold's main flow
   (`run_first_run_scaffold`); same `written.extend(...)` pattern.

7. **`.gitkeep` placement under symlinks.** AC.LAYERED.7 — pre-existing
   `.gitkeep` from v0.1.6 is preserved. The skills directory is created
   at `_write_skills_gitkeep` time; symlink loop afterwards just adds
   children. No conflict.

8. **Tests.** Mirror Cycle 1 file split:
   - `test_AC_LAYERED_2_skill_symlink_registration.py` — symlink shapes,
     idempotence, walks all plugins, plugins-without-skills-dir handled.
   - `test_AC_LAYERED_3_4_skill_collision_halt.py` — workspace-local
     override (LAYERED.3) + cross-plugin (LAYERED.4) collisions.
   - `test_AC_LAYERED_7_gitkeep_idempotent.py` — `.gitkeep` preservation
     (extends existing AC.SKILLS-BUG.2 test angle).
   - LAYERED.1 + LAYERED.6 are smoke-only, recorded in status file.
   - LAYERED.5 verified via design-doc presence + content grep.

9. **Design-doc `docs/design/layered-skill-architecture.md`.** Authored
   inside this Cycle's universal-admitted set per parent plan Surface #10.
   Articulates 3-tier model + override semantics + lifecycle + the
   auto-symlinking mechanism + collision rules + Anthropic SKILL.md
   reference.

---

## §8 — Out of scope

- Cycle 4 (one-question-at-a-time PM-enforced surfacing) — separate cycle
  per dispatcher.
- Auto-creation mechanism (v0.2.0) — workspace-local skills are AUTHORED
  in this release; persona-proposed-and-user-ratified comes later.
- Promotion rubric (v0.2.1) — workspace-local → plugin / base graduation.
- 12 dev-sdlc skill-ifications (v0.1.8 + v0.1.9).
- Migration of `plugins/dev-sdlc/skills/start-project.md` from flat-file
  to directory-shape (out of fence; flat-file shape doesn't conflict with
  directory-shape walking).

---

## §9 — Predecessor commit ladder

Pre-apply:
1. `73505f0` — v0.1.7 Cycle 2 seal (current HEAD when this plan was authored).
2. `<plan-doc commit>` — this doc.
3. `<source-edit commit>` — feat(v0.1.7): Cycle 3 source-edit BASELINE.
4. `<manifest commit>` — Cycle 3 manifest.
5. `<loam amend apply>` — auto-commit per v0.1.2 item 6.
6. `<loam amend seal>` — deterministic seal commit.

---

## §10 — Bookkeeping

- `loam amend apply` per cycle (NOT `git commit --amend`).
- Single semantic commit message per phase.
- Backfill of v0.1.7 release-level rows (STATE.md, roadmap §8, eric-final §2)
  DEFERRED to v0.1.7 RELEASE close. Document Cycle 3 SHAs in status file
  for eventual backfill.
- DO NOT push tags.
