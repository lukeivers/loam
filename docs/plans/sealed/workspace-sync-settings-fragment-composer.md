# workspace-sync settings-fragment auto-composer (RF-1 closure)

loam-realignment RF-1 closure. EXTENDS the sealed `workspace-sync`
component. Sealed local; live activation against the operator's
workspace awaiting the dispatcher-timed gated step per ASK-FIRST.

The piece that turns the frame-kernel 1a/1b + keep-pace
`settings.fragment.json` declarations from HAND-MERGED-on-a-gated-step
into AUTO-WIRED-on-sync. On a successful `pos-sync`, the composer
DISCOVERS every loam component's `settings.fragment.json` under the
synced `<workspace>/framework/` tree and COMPOSES their `hooks` blocks
into `<workspace>/.claude/settings.json` — additively, idempotently,
and without clobbering the user's/workspace's own settings. This is
what makes scale-free governance real IN CODE: a fragment-shipping
component now wires up on sync with zero per-workspace hand-authoring,
closing the RF-1 gap named in frame-kernel 1a/1b §7-5 + keep-pace RF-6
(`workspace-sync does not auto-compose fragments today`).

AC.SFC.1 (discovery + compose) — every component shipping a
`settings.fragment.json` under its `hooks/` tree has its hook entries
present in the composed settings.json; the glob
`framework/*/hooks/**/settings.fragment.json` catches fragments at
BOTH `hooks/` and `hooks/<subdir>/` depths.

AC.SFC.2 (loam-ownership) — every composed group is identifiable as
loam-owned + traceable to its source fragment; a user-authored group
is not marked loam-owned (the clean-ownership boundary).

AC.SFC.3 (non-clobber) — composing never modifies/removes the
user's/workspace's own hook entries and never alters any non-`hooks`
key (`statusLine`, `permissions`, etc. survive byte-identical).

AC.SFC.4 (idempotency) — a second sync with an unchanged fragment set
adds no duplicate entry and leaves the loam-owned set identical.

AC.SFC.5 (clean removal) — a previously-composed component whose
fragment is gone has its loam-owned entry removed on the next
compose; user entries are never removed.

AC.SFC.6 (placeholder resolution) — `${LOAM_REPO}` resolves to the
synced workspace's framework root; no literal placeholder survives in
a composed command.

AC.SFC.7 (dry-run + never-destructive) — `--dry-run-compose` reports
the plan and writes nothing; a malformed/unparseable existing
settings.json causes the compose step to surface an error and write
nothing (never a destructive overwrite).

AC.SFC.S (outcome-altitude) — a REAL sync through the production
`pos-sync` entry-point against a fixture workspace composes the REAL
frame-kernel SubagentStart + SubagentStop fragment blocks into the
fixture `.claude/settings.json`; a pre-existing user `Stop` hook +
`statusLine` key survive byte-untouched; a SECOND real sync is
idempotent (no duplicates) — all asserted by READING the resulting
settings.json. No STUB-class test of the merge function satisfies this
AC; only the real sync→compose end-to-end path does.

D-SFC.0 ruled EXTEND the sealed `workspace-sync` component (not a new
component) — the composer is a sync-lifecycle step; `frozen_baseline:
false` advances the workspace-sync seal baseline.

D-SFC.1 ruled the merge is additive + idempotent via a loam-ownership
tag + a stable dedupe key (source-fragment identity + resolved
command); a re-run detect-and-skips already-present loam entries.

D-SFC.2 ruled the non-clobber guarantee is STRUCTURAL: the composer's
write set is tag-scoped (loam-owned entries only); user entries +
non-`hooks` keys are outside the write set; the only removal is a
loam-owned entry whose source fragment is gone.

D-SFC.3 ruled discovery is `framework/*/hooks/**/settings.fragment.json`
(catches both shipped fragments at differing depths); a component opts
a fragment in by SHIPPING that file (presence-as-opt-in, zero
ceremony).

D-SFC.4 ruled the composer runs AUTOMATICALLY on a successful sync
(safe because non-clobber holds) with a one-line surfaced summary;
`--no-compose` opts out, `--dry-run-compose` previews.

D-SFC.5 ruled `--dry-run-compose` writes nothing; every real write is
additive + tag-scoped + idempotent + atomic (temp-file + os.replace);
a malformed settings.json HALTS the compose (never overwrites) while
the sync itself stands.

FEASIBILITY CONFIRMED with a named caveat (RF-1): workspace-sync CAN
compose `<workspace>/.claude/settings.json` (a post-merge Python
write, not a git op; `workspace_root` + the `workspace_paths.claude_dir`
D-Q.A4-lock helper give the path) — but this REACHES OUTSIDE the
D-migration HC#6 git-only-in-`framework/` fence. The widening is NAMED,
not silent, with the safety envelope (additive + tag-scoped +
idempotent + dry-run + atomic) sized to the every-workspace blast
radius and a standalone-`pos-compose-settings` alternative surfaced
(EXTEND-workspace-sync recommended).

EXTENDS the `workspace-sync` fence (`frozen_baseline: false`); the
`workspace-bootstrap` `claude_dir` resolver + the frame-kernel/keep_pace
fragments are IMPORTED/READ, never edited; no other sealed component's
fence widens; no live `.claude/settings.json` is composed in this seal
(fixture-tested only; live activation is the dispatcher-timed gated
step per plan §7-1).

Plan-doc + manifest authored by loam-plan-author; source-edit batch
(fragment_composer module + cli.py wire-in + flags + tests) + apply +
seal TBD-AT-BUILD.
