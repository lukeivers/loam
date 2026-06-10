# frame-kernel — SubagentStart envelope cwd-fallback (workspace-root resolution corrective)

> **Status:** plan-doc (ODD-shaped). Single-purpose corrective amendment.
> **WD:** `/Users/lukeivers/loam`.
> **Parent objective:** AC.PO.1 + AC.PO.2 (the SubagentStart bundle IS the
> persona→subagent translation handoff; a bundle that degrades on every real
> dispatch delivers neither).
> **Confidence (Lens 4):** HIGH — tight scope. The fix shape is already proven
> in-fence: `frame_judge.py` (slice 1b, same sealed component) resolves
> workspace_root from `workspace.project_dir` with a `cwd` fallback
> (`framework/frame-kernel/src/loam/frame_kernel/frame_judge.py:370-379`).
> This corrective brings `bundle.py::parse_envelope` (slice 1a) to the same
> contract.

---

## §1 Objective

The SubagentStart context bundle resolves the workspace root from REAL Claude
Code envelopes — which carry `cwd` (the standard hook-envelope common-input
field) and NOT `workspace.project_dir` — so the microkernel + workstream +
memory tiers populate on real dispatches instead of degrading to placeholders.

## §2 Predecessors / context

- **Slice 1a** (`frame-kernel-subagent-start-context-handoff`) — shipped
  `bundle.py::parse_envelope` reading workspace_root ONLY from
  `envelope["workspace"]["project_dir"]`.
- **Slice 1b** (`frame-kernel-subagent-stop-frame-check-1b`) — shipped
  `frame_judge.py` with the project_dir-then-cwd fallback already in place.
  1a and 1b currently disagree on the envelope contract; 1b is right.
- **The Tier-0 live finding (2026-06-10, pos3 watched activation):** a probe
  agent reading its own injected context observed the marker present but ALL
  THREE tiers degraded (`[... unavailable ...]`) on a real dispatch, while a
  synthetic envelope with `workspace.project_dir` produced a full 6.3KB
  bundle. Real SubagentStart envelopes carry `cwd`, not
  `workspace.project_dir`. The injection plumbing + fail-soft contracts work;
  the 1a envelope contract is wrong.

## §3 Scope

**In scope:**
- `bundle.py::parse_envelope` — workspace-root resolution gains the `cwd`
  fallback (priority: `workspace.project_dir` when present, else `cwd`),
  mirroring the 1b `frame_judge.py` pattern.
- New AC.EWR.* tests (one file per AC) including the outcome-altitude
  regression through the production hook entry-point with the REAL observed
  envelope shape (cwd-only).

**Out of scope:**
- Any change to the fail-soft markers, tier rendering, bundle assembly, or
  the hook script (`subagent_start_context.py`) — the plumbing is verified
  working.
- Any change to `frame_judge.py` (already correct).
- Any change to the existing AC.SACH.* / AC.DMP.* / AC.SSFC.* contracts or
  tests. Existing tests must stay green untouched.
- Task-text field handling (`prompt`/`task`/`description`) — unchanged.
- Live `.claude/settings.json` wiring; publish/push (owner-gated; rides the
  next release after v1.4.0).

## §4 Acceptance criteria

| AC ID | Outcome | Verification |
|---|---|---|
| `AC.EWR.1` | Given an envelope carrying ONLY `cwd` (no `workspace` dict — the real observed shape), `parse_envelope` resolves `workspace_root` from it, and the composed bundle is byte-identical to the bundle composed from a `workspace.project_dir` envelope naming the same root (all tiers resolve identically). Priority order: `workspace.project_dir` when present wins over `cwd`. | Unit: cwd-only envelope → `workspace_root` set; equivalence: `compose_bundle(cwd-only) == compose_bundle(project_dir)` against a real-kernel workspace; priority: both-present envelope resolves to project_dir. |
| `AC.EWR.S` **(OUTCOME-ALTITUDE)** | The REAL envelope shape (cwd-only, `hook_event_name: SubagentStart`, a `prompt`) driven end-to-end through the production hook entry-point (`subagent_start_context.py` as a subprocess — the AC.SACH.S pattern) yields an injected `additionalContext` whose microkernel tier is NON-degraded: the real on-disk `kernel/loam-microkernel.md` content is present and `MISSING_KERNEL_MARKER` is absent. | Real subprocess invocation, real repo-root kernel file, NO pre-arranged state; assert prime marker + real-kernel content present, missing-marker absent, exit 0. |

(AC3 of the dispatch — existing frame-kernel tests stay green; AC.SACH.*
contracts unchanged — is §15 backwards-compat verification, not a new test.)

**Method-in-AC test:** the resolution helper's structure, naming, and where
the fallback branch lives are the builder's call; each AC is satisfiable by
other methods. Outcome-shape confirmed.

**Ladder-up:** AC.EWR.* → AC.SACH.1/3 (the tiers must actually reach real
dispatched subagents) → AC.PO.1 + AC.PO.2.

## §5 Sealed-component fence

- **`frame-kernel`** (EXTEND; `frozen_baseline: false`) — `bundle.py` +
  new tests only.
- Universal admissions: `docs/plans/` (this plan + manifest).
- **No other component touched.**

## §6 Halt triggers

1. WD not `/Users/lukeivers/loam` before source edits → halt.
2. Investigation contradicts the Tier-0 finding (real envelopes DO carry
   `workspace.project_dir` on SubagentStart) → halt + surface, don't guess.
   (Note: the fix keeps project_dir as first priority, so the corrective is
   safe under either reality; the halt fires only on evidence the finding
   itself was wrong.)
3. The fix would require touching anything beyond `bundle.py` + new tests →
   halt (no longer a small single-purpose amendment).
4. Any existing AC.SACH.* / AC.DMP.* / AC.SSFC.* test fails after the edit →
   halt; do NOT loosen tests.

## §7 Ship shape

Single cycle, single seal. Manifest:
`docs/plans/frame-kernel-subagent-envelope-cwd-fallback.manifest.yaml`.
Commit ladder: plan+manifest (`docs(plans):`) → source+tests
(`fix(frame-kernel):`) → `loam amend apply` → `loam amend seal` → §14
backfill. Source edits commit BEFORE apply (apply runs against committed
HEAD). No push (publish is owner-gated; rides the next release).

## §14 Method-decision register (populated at build time)

- D-build.1 — fallback branch placement + shape (mirror 1b's
  `frame_judge.py` vs shared helper). *(builder)*
- SHAs backfilled post-seal.

## §15 Backwards-compat verification

All 62 existing frame-kernel tests pass untouched under the workspace venv
Python (baseline verified green pre-edit). The AC.SACH.4 fail-soft contract
(exit-0, degraded markers on genuinely-degenerate envelopes) is unchanged —
an envelope with NEITHER `workspace.project_dir` NOR `cwd` still degrades
exactly as before.

## §16 Halt-and-surface findings (plan-authoring)

- Non-blocking: the existing AC.SACH.S probe uses the synthetic
  `workspace.project_dir` shape — it stays valid (that shape remains
  first-priority) but it is the reason the contract gap shipped unobserved.
  AC.EWR.S adds the real-shape twin rather than rewriting it.
- Non-blocking: 1a/1b envelope-contract disagreement (§2) — resolved by this
  corrective; no shared-helper extraction forced (kept small; builder may
  surface extraction as a future idea, not do it here).
