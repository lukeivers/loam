# Layered-skill architecture

**Status:** authored 2026-05-04 as part of v0.1.7 Cycle 3.

**Audience:** loam contributors and harness operators who need to understand
where SKILLs live, how they are discovered, and how they compose across the
three layers.

**References:**
- Anthropic SKILL.md spec — verified 2026-05-04. Discovery locations
  (precedence: enterprise > personal > project; plugin in its own
  `plugin-name:skill-name` namespace).
- `docs/plans/layered-skill-story-research-2026-05-04.md` — research
  pass that grounds this doc.
- `docs/plans/v0-1-7-personas-pm-layered-skills.md` — parent plan,
  §5 AC.LAYERED.* family.
- `docs/plans/v0-1-7-cycle-3-layered-skill-discovery.md` — sub-plan
  that ships this doc + the auto-symlinking mechanism.

---

## §1 — The three layers

**Base loam skills** — skills that ship with the harness's core skill
plugin at `plugins/loam-skills/skills/<name>/SKILL.md`. Available to every
loam user when the plugin is enabled in `bootstrap.yaml`. These capture
loam's load-bearing translation patterns that aren't dev-specific
(memory-recall, scope-decompose, dispatch-with-gates,
onboarding-conversation, session-handoff, translation-discipline,
audit-block-on-telegram, owner-decision-summary).

**Plugin skills** — skills that ship with optional plugins, located at
`plugins/<plugin>/skills/<name>/SKILL.md`. Available only when the plugin
is enabled. These capture domain-specific patterns (dev-sdlc patterns,
hypothetical Slack-workflow patterns when a Slack plugin lands, legal-
research patterns when a legal plugin lands per Lens 1's example).

**Workspace-local skills** — skills authored in a specific workspace,
persisted at `<workspace>/.claude/skills/<name>/SKILL.md`. Available only
in that workspace. These capture project-specific patterns the operator
has accumulated through actual usage (e.g., "for Eric's SaaS, run
`bundle exec rspec spec/integration/payments/` not `rspec`" — useless to
other workspaces).

---

## §2 — Discovery + override semantics

### 2.1 — Anthropic-native discovery

Per Anthropic spec (verified 2026-05-04), Claude Code walks three
locations:

| Location | Path |
|---|---|
| Personal | `~/.claude/skills/<name>/SKILL.md` |
| Project (workspace) | `<workspace>/.claude/skills/<name>/SKILL.md` |
| Plugin | `<plugin>/skills/<name>/SKILL.md` (when the plugin is on the Python path) |

Precedence: **enterprise overrides personal, personal overrides project**.
Plugin skills are namespaced and cannot collide with project / personal
skills *in the discovery surface itself* — they appear as
`plugin-name:skill-name`. This is Anthropic-native behavior; loam does not
re-implement it.

### 2.2 — loam's auto-symlink layer

To make plugin-shipped skills uniformly visible at the project layer (so
the operator's `/` menu shows `dispatch-with-gates` rather than only
`loam-skills:dispatch-with-gates`), the workspace-bootstrap first-run
scaffold **auto-symlinks** every plugin's skill directory into the
project location:

```
<workspace>/.claude/skills/<name>/
  -> plugins/<plugin>/skills/<name>/
```

The symlink targets the skill **directory** (not the SKILL.md file),
because skills can ship companion files (scripts, references, templates)
that the discovery walk needs intact.

This is the same mechanical pattern as Cycle 1's subagent-persona
symlinking (`_symlink_plugin_agents` in
`framework/workspace-bootstrap/src/loam/workspace_bootstrap/adapters/first_run_scaffold.py`),
applied to the skill surface.

### 2.3 — Override semantics

Three cases:

**Case A — workspace extends a base skill.** Operator wants project-
specific extras on a base skill. Two implementation shapes possible:

1. **Shadow with full-replacement.** Operator authors a complete
   `<workspace>/.claude/skills/<name>/SKILL.md`. The auto-symlinker
   refuses to overwrite (operator-precedence) and raises
   `PluginSkillCollisionError` so the operator resolves explicitly.
   *Risk:* the workspace's copy goes stale when the base updates.
2. **Reference + extend.** Operator authors a thin
   `<workspace>/.claude/skills/<name>-eric/SKILL.md` that references
   the base. *Recommended* — workspace-local skills should rename to
   avoid shadowing; explicit composition is more legible than implicit
   override.

**Case B — plugin shadows base.** Almost never correct. If a plugin
ships a skill with the same name as a base skill, the auto-symlinker
raises `PluginSkillCollisionError` at scaffold time. The plugin author
should rename to a plugin-prefixed handle (e.g., `dev-sdlc-dispatch`
rather than `dispatch-with-gates`).

**Case C — workspace extends a plugin skill.** Same shape as Case A —
workspace-local rename recommended; full-replacement raises
`PluginSkillCollisionError`. Operator either renames their workspace
skill or deletes it to accept the plugin skill.

### 2.4 — Collision precedence summary

When the auto-symlinker encounters a target path
`<workspace>/.claude/skills/<name>` that is already populated:

| Existing state | Behavior |
|---|---|
| Symlink to the correct plugin source | Idempotent — leave alone. |
| Symlink to a different path (operator retargeted) | Operator-precedence — leave alone. |
| Non-symlink directory or file (operator-authored override) | **Halt** — raise `PluginSkillCollisionError`. |
| Two plugins shipping the same skill name | **Halt** — raise `PluginSkillCollisionError`. |

The halt-and-surface posture mirrors the agent-symlink collision rules
from Cycle 1 (`PluginAgentCollisionError`). Uniform operator-precedence
across both surfaces.

---

## §3 — Lifecycle

**Base skills.** Authored as part of a sealed-component amendment cycle
(the v0.1.3 SKILL bundle being the precedent). Garbage-collection is a
deliberate amendment cycle (deprecation → removal). Cannot be removed
mid-session.

**Plugin skills.** Same as base, scoped to a plugin's own seal cycles.

**Workspace-local skills.** Created at any moment, including mid-session
via the persona's `Write` tool. Garbage-collected via:

1. **Manual.** Operator deletes the directory.
2. **Stale-detection.** A daily/weekly review skill (proposed for v0.2.1)
   walks workspace-local skills, surfaces ones that haven't fired in N
   days, recommends review.
3. **Promotion-driven.** Promoted skill is removed from the workspace
   once it lands in a plugin or base.

### 3.1 — First-skill restart hint

Anthropic's live-change-detection picks up new SKILL.md files inside an
**existing** `<workspace>/.claude/skills/` directory without restart. But
creating the top-level `.claude/skills/` directory mid-session requires
restart.

Mitigation: workspace-bootstrap pre-creates an empty
`<workspace>/.claude/skills/.gitkeep` at first-run scaffold time per
v0.1.6 AC.SKILLS-BUG.2. Subsequent additions are picked up live without
restart.

---

## §4 — Auto-symlinking mechanism (Cycle 3)

The first-run scaffold (`run_first_run_scaffold`) calls
`_symlink_plugin_skills(workspace_root)` immediately after
`_symlink_plugin_agents(workspace_root)`. The function:

1. Resolves `plugins/` root via `_resolve_plugins_root()` (canonical
   `<workspace>/plugins/` or derived `<workspace>/framework/plugins/`).
2. Iterates each plugin directory.
3. For each plugin, iterates `<plugin>/skills/<name>/` directories that
   contain a `SKILL.md` file.
4. For each candidate skill directory, attempts to create a symlink at
   `<workspace>/.claude/skills/<name>` pointing at the absolute path of
   the plugin skill directory.
5. Idempotent — existing symlinks pointing at the correct target are
   left untouched. Symlinks elsewhere are left untouched
   (operator-precedence). Non-symlink collisions raise
   `PluginSkillCollisionError`.

### 4.1 — Out of scope for this layer

- **Auto-creation of workspace-local skills by the persona.** Deferred to
  v0.2.0. Cycle 3 ships only the discovery mechanism; persona-proposed-
  and-user-ratified skill capture lands later.
- **Promotion rubric (workspace-local → plugin / base).** Deferred to
  v0.2.1.
- **Flat-file `<plugin>/skills/<name>.md` shape.** Out of fence. Anthropic
  spec walks per-directory; flat-file skills (e.g.,
  `plugins/dev-sdlc/skills/start-project.md`) are not auto-symlinked.

---

## §5 — Composition

### 5.1 — With per-project PM (Cycle 2)

The per-project PM owns project-domain decision state at
`<workspace>/workspace/.loam/pms/<handle>/`; it does NOT own
workspace-local skills (Anthropic-native at `<workspace>/.claude/skills/`).
The PM's `composes_with_skills: list[str]` field is advisory metadata
(Cycle 2; not enforced at runtime). Cycle 4+ may wire enforcement
("when this PM activates, auto-load these skills"), but auto-load is
already Anthropic-native — the PM-side knob is just a hint for the
persona's invocation logic.

### 5.2 — With subagent personas (Cycle 1)

Subagent personas (e.g., `loam-builder`) compose against the same skill
surface. A persona dispatch may invoke a base or plugin skill the same
way the primary persona invokes one.

---

## §6 — References

- `framework/workspace-bootstrap/src/loam/workspace_bootstrap/adapters/first_run_scaffold.py`
  — implementation (`_symlink_plugin_skills`, `PluginSkillCollisionError`).
- `framework/workspace-bootstrap/tests/test_AC_LAYERED_2_skill_symlink_registration.py`
  — symlink registration + idempotence tests.
- `framework/workspace-bootstrap/tests/test_AC_LAYERED_3_4_skill_collision_halt.py`
  — collision-halt tests (workspace-local override + cross-plugin).
- `framework/workspace-bootstrap/tests/test_AC_LAYERED_7_gitkeep_idempotent.py`
  — `.gitkeep` idempotency test.
