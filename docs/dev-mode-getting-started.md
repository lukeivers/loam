# Getting started with loam dev-mode

This page is for contributors and harness builders working on loam
itself — the framework, plugins, and methodology — rather than users
running loam-attached projects. If you're a normal loam user, the
non-dev [`getting-started.md`](getting-started.md) is the page you
want; come back here only if you intend to extend loam.

dev-mode is a layered overlay on top of the standard loam workspace.
It auto-loads an extra fragment of `CLAUDE.md` (the codebase-and-
methodology instructions checked into the project root) so the primary
persona inherits the dev-specific conventions, ODD methodology, and
build discipline that govern how loam itself is constructed.

---

## Prerequisites

Before enabling dev-mode, confirm:

1. **A working loam workspace.** Run `loam init <path>` first per the
   non-dev getting-started; verify `claude` launches in the workspace
   without errors.
2. **The standard non-dev onboarding ritual completed.** dev-mode
   composes on top of the non-dev surface; if onboarding hasn't run,
   `loam onboard` settles the base configuration first.
3. **`git` access to the canonical loam repo.** Dev-mode workspaces
   need read-write access to the framework tree because contributors
   author plan-docs, ACs, and component code in-tree.
4. **Familiarity with the ODD methodology.** dev-mode assumes you
   work in the Outcome / Constraints / Acceptance shape. The
   reference is at [`design/odd.md`](design/odd.md); skim it once
   before your first session.
5. **Python 3.13** (not 3.11+ as the user-facing guide suggests).
   Dev-mode runs the full pos-v2 component build matrix; some
   components pin 3.13.

---

## Enabling dev-mode

dev-mode auto-loads when the workspace's `CLAUDE.md` fragment carries
the `dev-extension` marker. The mechanism is:

1. **Workspace-level `CLAUDE.md`.** The non-dev workspace's
   `CLAUDE.md` carries the standard always-on lenses + output
   conventions that shape every feature.
2. **`CLAUDE.dev.md` overlay.** When dev-mode is enabled, the harness
   also loads `CLAUDE.dev.md` from the workspace root. The overlay
   carries dev-specific machinery — the methodology vocabulary, the
   build-discipline rules, the in-flight amendment-cycle conventions.
3. **Auto-load gate.** The harness checks for `CLAUDE.dev.md` at
   session start. If present, it's auto-loaded; if absent, the
   standard non-dev path runs.

To enable dev-mode in an existing workspace, copy the canonical
`CLAUDE.dev.md` from the loam repo root into your workspace:

```bash
cp <canonical-loam>/CLAUDE.dev.md <your-workspace>/CLAUDE.dev.md
```

The next `claude` invocation in the workspace picks up the overlay
automatically. To disable, delete the file; the workspace falls back
to non-dev shape.

---

## Walkthrough — your first dev-mode turn

After enabling dev-mode, your first session will:

1. **Load both `CLAUDE.md` fragments.** The non-dev fragment + the
   `CLAUDE.dev.md` overlay both auto-load. The persona's session-
   start greeting will reflect the dev-mode context (it knows you're
   building loam, not building on top of loam).
2. **Surface in-flight amendment cycles.** If there are any
   uncommitted plan-docs, mid-cycle build agents, or pending owner-
   ratifications, the persona surfaces them. The `pos-v2-amend-cycle`
   discipline assumes one amendment cycle at a time per working tree;
   the persona enforces this by listing what's already in-flight
   before accepting new work.
3. **Default to plan-before-code.** Per the dev-mode methodology,
   every non-trivial build writes a plan-doc to
   `docs/plans/<slug>.md` BEFORE any code lands. The persona
   refuses to dispatch a build agent against a missing plan-doc.
4. **Run amendment cycles via `loam amend`.** The dev workflow uses
   `loam amend apply <manifest>` and `loam amend seal --plan-doc
   <abs-path> <manifest>` rather than free-hand `git commit`. The
   manifest pins the fence; `apply` produces the source-edit commit;
   `seal` produces a deterministic seal commit + post-seal §14
   backfill commit per AC.D-sa.7.

A typical first dev-mode turn looks like:

```
You: I want to add a new field to the Manifest dataclass.
Persona: That's component-level work in framework/workspace-
         bootstrap/. Plan-before-code applies. I'll write the plan-doc
         at docs/plans/<slug>.md first; do you have an AC
         family in mind, or should I propose one?
```

---

## Where to go next

- [`design/odd.md`](design/odd.md) — the methodology dev-mode is
  shaped around.
- [`plans/`](plans/) — the plan-doc archive; every
  shipped feature has a plan-doc here.
- [`STATE.md`](STATE.md) — current ship-state,
  in-flight cycles, and release rollups.
- [`../CLAUDE.dev.md`](../CLAUDE.dev.md) — the dev-mode overlay
  fragment itself; read it once to understand what gets auto-loaded.
- [`../CONTRIBUTING.md`](../CONTRIBUTING.md) — the contributor flow
  for sending patches.

---

## Common dev-mode problems

**`CLAUDE.dev.md` doesn't auto-load.** Verify the file exists at the
workspace root (not inside `framework/` or `workspace/`); the harness
checks the workspace-root level only. Restart Claude Code after
copying the file in.

**Plan-doc enforcement feels heavy-handed.** It is — that's the
point. dev-mode treats every build as a methodology exercise; if
you're prototyping and want to skip plan-before-code, work in a
non-dev workspace.

**`loam amend apply` fails with "manifest references missing
admissions."** The manifest's `universal_paths` block needs the path
you're editing. Read the existing manifest examples under
`docs/plans/*.manifest.yaml` for the shape.

**Anything else.** Open a GitHub issue on `lukeivers/loam` with
`dev-mode:` in the title and a copy of the failing command output.
