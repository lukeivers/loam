# Amendment #28 — research: workspace-identity routing in first-run dispatch

**Authored:** 2026-04-23.
**Motivating defect report:** `.scratch/claude-output/bootstrap-reconsideration.md`
in the pos3 test clone (2026-04-23 session).
**Governs plan:** `docs/plans/amendment-28-workspace-identity-routed-first-run.md`.

This document is the research-before-plan artefact required by the
FUTURE_IDEAS "research before plan for non-trivial new work" CDC. It is
sized proportionately to the fix — a correctness amendment against an
existing surface, not a new component — and inlines primary-source
citations the plan's ACs build on.

---

## 1. The bug as observed

One host with two pos-v2 workspaces on disk:

- `/Users/lukeivers/ivers-corp-pos-v2` (canonical, slug
  `ivers-corp-pos-v2`).
- `/Users/lukeivers/pos3` (test clone, slug `pos3`).

Observed state after opening a Claude Code session in pos3 on 2026-04-23:

1. `~/.pos/first-run.state` reads `status: completed, generation: 7`;
   the state was written by a gen7 worker run that targeted the canonical
   workspace (slug evidence in `~/.pos/first-run.log`: phase-4b-health-poll
   targets `com.pos-v2.ivers-corp-pos-v2.*`).
2. `/Users/lukeivers/pos3/.venv/bin/python` does not exist.
3. `~/Library/LaunchAgents/` contains no `com.pos-v2.pos3.*.plist`.
4. `launchctl list` shows only `com.pos-v2.ivers-corp-pos-v2.*`.
5. pos3's `.claude/settings.json` is still the 18-line ship-time stanza
   invoking `hands-off-lifecycle/hooks/first-run.sh` (no self-retire).
6. pos3's `hands-off-lifecycle/hooks/first-run.sh` is still on disk.
7. The SessionStart hook in pos3 today printed the canned
   `_msg_completed()` string from `first_run_dispatch.py`
   ("pos-v2 first-run completed. The workspace is ready; subsequent
   sessions will launch straight into the supervisor path") — a false
   claim against pos3's actual state.

## 2. The design-level cause

### 2.1 State-file scope is host-global

`first_run_state.py` (hands-off-lifecycle hooks):

```python
# first_run_state.py:57
DEFAULT_POS_ROOT = Path.home() / ".pos"
```

The file at `~/.pos/first-run.state` is a **per-host** singleton. Every
workspace's SessionStart hook reads and writes it.

### 2.2 The state dataclass has no workspace identity

`first_run_state.py:71-110`:

```python
@dataclass
class FirstRunState:
    status: str = "starting"
    pid: int = 0
    started_at: float = 0.0
    updated_at: float = 0.0
    phase: str = ""
    detail: str = ""
    error_code: int = 0
    remediation: str = ""
    generation: int = 1
```

There is no `workspace_root`, no `slug`, no workspace-identity field.

### 2.3 Dispatcher Case 2 does not route

`first_run_dispatch.py:284-290`:

```python
# Case 2 — completed previously.
if existing is not None and existing.status == "completed":
    return _msg_completed()
```

The Case 2 check gates on the status alone; `pos_v2_root` is passed into
`dispatch()` but is not compared against any recorded owner of the
completed state.

### 2.4 Canonical quote from the amendment this regressed

The original true-first-run proposal specified a per-workspace marker:

> "Partial-first-run detection marker is 'absence of top-level `.venv/`'
> as the canonical first-run-not-complete signal."
> — `docs/archive/component-research/true-first-run/proposal.md:§8.3` (Eve's
> inference, builder-challengeable)

The 2026-04-22 session-start-detachment amendment introduced the global
`~/.pos/first-run.state` sentinel to close the hook-timeout-SIGKILL
class (worker SIGKILL'd mid-Phase-3 left an incompletable state that the
venv-presence marker could not distinguish from "install finished"). The
fix was correct for the failure class it closed, but the replacement
sentinel dropped the per-workspace keying the original marker had. That
is the regression this amendment closes.

## 3. Why AC6 of amendment #6 did not catch it

Amendment #6 (namespaced-labels-and-bootout) includes AC6:

> **AC6 — multi-workspace coexistence.** Scaffold on workspace A (slug
> `alpha`) and on workspace B (slug `beta`) in sequence. Both
> `com.pos-v2.alpha.orchestrator` and `com.pos-v2.beta.orchestrator` are
> loaded simultaneously; `launchctl print` for each reports a program
> path rooted at its own workspace. B's scaffold does not evict A.
> — `docs/archive/component-research/namespaced-labels-and-bootout/proposal.md:§3`

The AC6 test calls `run_first_run_scaffold()` directly on both
fixture workspaces, bypassing the SessionStart dispatcher. The scaffold
function is correctly per-workspace (it receives `workspace_root` and
computes its slug); the test confirms that layer. The dispatcher layer
— which reads the global state file and decides whether to invoke the
scaffold at all — is not exercised by AC6.

This is the §9.7 pattern documented in `odd-in-pos.md` (Linux-removal
precedent): an AC that covers a correct-at-one-layer behaviour without
covering the objective-level behaviour the user relies on end-to-end.
Re-extension per ODD §4 is the remedy.

## 4. Why this is distinct from Idea 9

`docs/FUTURE_IDEAS.md` Idea 9 (workspace-slug collision
detection, captured 2026-04-22) names the hazard of two workspaces with
the **same basename** producing the same slug. The failure today has
different-basename workspaces (`ivers-corp-pos-v2` vs `pos3`) that
produce different slugs. No slug collision occurred; the collision is
at a layer above — the state-file sentinel has no workspace identity at
all.

Idea 9's scope should widen to include state-file routing. That is
recorded in the plan doc's §8 ("Relationship to FUTURE_IDEAS.md Idea 9")
as the catalogue-update side of this amendment.

## 5. Options for the objective-level fix

The objective is: *first-run completion for workspace A must not
short-circuit workspace B's first-run.* Three structural shapes
satisfy it.

### 5.1 Option A — per-workspace state file under `~/.pos/`

`~/.pos/first-run-state/<slug>.state` — one file per workspace slug
under a shared directory. State-file reads/writes route by slug.

Pros: minimal change to the state-file contract; the dataclass stays
untouched; reuses the existing state-file writer/reader; slug derivation
already lives in `first_run_helper.py`.

Cons: host-global state directory still exists (compatible with
multi-workspace, but slug-collision hazard from Idea 9 reappears at this
layer — two workspaces with the same basename would share the file).
Idea 9's future cycle would have to address both launchd labels and this
path.

### 5.2 Option B — single state file keyed by workspace

`~/.pos/first-run.state` holds a dict keyed by slug;
`FirstRunState` gains a `workspace_root` and `slug` field; dispatcher
looks up by the currently-computed slug.

Pros: single file, atomic write per amendment's file layout.

Cons: larger schema change; concurrent writes across workspaces race on
the same path; the atomic-rename pattern assumed one writer.

### 5.3 Option C — workspace-local state file

`<workspace>/.pos/first-run.state` lives inside the workspace. The
state is structurally impossible to confuse between workspaces because
the file is under the workspace tree.

Pros: cleanest routing — workspace identity is implicit in the path. No
slug-collision concern at the state-file layer. Matches the spirit of
Eve's original venv-presence marker (per-workspace signal inside the
workspace). Uninstall is a recursive delete of the workspace.

Cons: a workspace-local file inside a repo tree needs `.gitignore`
handling (or placement under a `.pos/` sub-path the workspace ignores).
The `~/.pos/` directory still carries other per-host artefacts
(configs, logs) — split between workspace-local and host-global is a
design choice the builder makes.

### 5.4 Recommendation and inference flag

Option **C** is the ODD-cleanest structural shape: the workspace-identity
routing is in the path itself, not in a field the dispatcher must
remember to check. The dispatcher reads a state file; the file is in
the workspace; the workspace identity is enforced by path, not by
code. Structural-over-advisory per `odd-methodology.md` §5.

**Flagged inference (builder may challenge):** the plan assumes Option C
unless the builder surfaces a concrete reason host-global state is
load-bearing (e.g., a planned cross-workspace supervisor that needs to
see every workspace's state from one place). If surfaced, fall back to
Option A with the slug-collision carve-out explicitly admitted.

Under any option, the `FirstRunState` dataclass gains a
`workspace_root: str` field so the content itself names its owner —
defence in depth against the path being moved by an admin later.

## 6. Re-extension targets under ODD §4

Two re-extensions land with this amendment. The first covers the
end-to-end dispatch path AC6 missed; the second covers the state-file
content itself.

- **AC10 (re-extension of AC6).** Workspace B's SessionStart hook
  fires after workspace A's first-run has completed; the dispatcher
  invokes a first-run worker for workspace B, not the `_msg_completed()`
  short-circuit; workspace B ends up with its own `.venv/`, its own
  `com.pos-v2.<slug-b>.*` plists, and its own self-retired
  `.claude/settings.json`. A's services remain loaded throughout.
- **AC11 — state carries workspace identity.** The
  persisted state explicitly records the workspace root it belongs to
  (path or slug). A state file whose recorded workspace does not match
  the current `pos_v2_root` is treated as absent by the dispatcher's
  Case 2 — the current workspace's first-run proceeds unmodified.

A criterion that tests the Case 4 silent-death path in a
multi-workspace context is not added here — the silent-death logic
already operates per-pid and does not cross workspaces. If the builder
discovers it does, re-extend under the same cycle.

## 7. Failure modes the fix must preserve

The 2026-04-22 session-start-detachment amendment closed these; the
fix must not reopen them:

1. Hook-timeout SIGKILL leaving partial state — state file still needed
   as a post-detach sentinel; venv-presence alone is insufficient.
2. Silent-death detection — state file needs `pid` + `updated_at` so
   `is_stale_live_state()` can diagnose crashes.
3. Atomic writes — concurrent readers must see complete snapshots.

Under Option C, per-workspace files trivially preserve all three.

## 8. Scope boundary vs Amendment #29 (orientation context)

This amendment is narrow: the first-run state and dispatch routing.
The user's paired concern — "future test sessions should not start
without loading the design corpus" — is a separate objective and
rides as its own amendment (or a full component cycle if the design
shape demands one, per Idea 8's open questions). This research doc
deliberately scopes only the routing defect.

## 9. Claude-leverage lens

Claude Code's SessionStart hook is the primitive this amendment is
built against; no additional Claude surface is leveraged. The fix is
internal to hands-off-lifecycle and does not introduce new Claude
composition.

## 10. Primary-persona / harness lens

The pos3 false-success message is exactly the failure mode
VALUE_PROPOSITION.md calls out — the harness claimed a state that was
not true, shifting diagnostic burden onto the user. The fix restores
the translation-layer contract: the SessionStart hook's text must
reflect the actual state of the workspace it speaks for.
