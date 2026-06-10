# Context-Management Cycle 1 — SEE layer (the sensor)

> **Status:** sub-plan-doc (ODD-shaped). PLAN ONLY.
> **Master plan:** `docs/plans/context-management-see-budget-eviction-master.md`.
> **WD:** `/Users/lukeivers/loam`.
> **Parent objective:** AC.PO.1 + AC.PO.2 (via master §4).
> **Confidence (Lens 4):** HIGH — tight scope. The statusline-script + meter-file +
> live-read pattern is twice proven in-repo
> (`framework/hands-off-lifecycle/hooks/statusline.py`,
> `framework/usage-window-guard/src/loam/usage_window_guard/probe.py`).
> **Independently shippable:** YES — the sensor stands alone; Cycles 2–3 consume it.

---

## §1 Objective

Give loam a live context-occupancy sensor: a stdlib-only statusline script that
parses Claude Code's stdin `context_window` JSON every turn and writes the
occupancy reading to `<workspace>/.loam/context-meter.json`, plus a `read()`
production entry-point that returns the live reading or a fail-open "unavailable"
sentinel.

## §2 Predecessors / context

- `framework/usage-window-guard/` — mirror its `read()` shape (real default path,
  injectable transport for fixtures, fail-open sentinel, `AC.USG.S` outcome-altitude).
- `framework/hands-off-lifecycle/hooks/statusline.py` — mirror its statusline-script
  contract (stdlib-only, stdin JSON, fail-closed exit 0, never raises/blocks/spams).
- Research §2.2 + §5.1 — the VERIFIED statusline `context_window.{used_percentage,
  total_input_tokens, total_output_tokens, context_window_size}` schema (min CC
  version 2.1.132); updates per assistant message + after `/compact`.

## §3 Scope

**In scope:**
- New `framework/context-management/` package (layout mirrors `usage-window-guard`).
- Statusline entry-point script: reads stdin JSON, extracts the `context_window`
  object, writes the meter file, renders a glanceable occupancy line, exits 0.
- Meter file writer + the meter data shape ({occupancy %, input tokens, output
  tokens, window size, timestamp, source-version}).
- `read()` production entry-point returning the live reading or the unavailable sentinel.
- One-file-per-AC tests including the outcome-altitude `AC.CTXSEE.S`.

**Out of scope:**
- The budget math (Cycle 2). The threshold classification (Cycle 2).
- The per-category `/context` breakdown (research §7 PLAUSIBLE-not-verified;
  future verify-then-build).
- Any `strategic-compact` SKILL edit (Cycle 2).
- Auto-firing `/compact` (never — owner-class).
- Wiring the script into a workspace's `settings.json` `statusLine` slot as the
  DEFAULT (the script ships + is documented; whether it becomes a workspace's
  active statusLine is a separate install decision — surface, don't bake, to avoid
  colliding with the `hands-off-lifecycle` first-run statusLine).

## §4 Acceptance criteria

| AC ID | Outcome | Verification |
|---|---|---|
| `AC.CTXSEE.1` | Given a stdin envelope carrying a populated `context_window` object, the meter file written contains the occupancy reading: percentage, input/output token counts, window size, a timestamp. | Fixture envelope → invoke script → parse meter file → fields match envelope. |
| `AC.CTXSEE.2` | Given a stdin envelope with NO `context_window` field, the script writes/leaves an "unavailable" sentinel reading and exits 0 — never fabricates a number, never raises. | Envelope without the field → invoke → meter reads unavailable; exit 0. |
| `AC.CTXSEE.3` | `read()` returns the live occupancy reading parsed from the meter file, or the unavailable sentinel on any failure (missing file, malformed JSON, absent field). | Stage each failure mode → `read()` returns sentinel, never raises. |
| `AC.CTXSEE.S` **(OUTCOME-ALTITUDE)** | Invoking the production statusline entry-point with a realistic `context_window` envelope and NO pre-arranged meter file yields a meter file whose occupancy reading equals the envelope's reported occupancy. | Real entry-point, fresh tmp workspace, no staged state; assert meter occupancy == envelope occupancy. RED-on-mutation: break the extract step → assertion fails. |

**Method-in-AC test:** the meter file format, the field names, the sentinel
representation, the rendered line text are all the builder's call. Each AC is
satisfiable by methods other than any I have in mind. Outcome-shape confirmed.

**Ladder-up:** AC.CTXSEE.* → master AC family → AC.PO.1 (measured number replaces
the persona's guess) + AC.PO.2 (the sensor is the prerequisite for the
eviction/protection levers).

## §5 Sealed-component fence

- **`framework/context-management/`** (NEW component — seal test +
  `test_no_sealed_amendments.py` sidecar created in this cycle).
- Universal admissions: `docs/plans/` (this plan + manifest).
- **No other component touched.** If the builder finds the meter must write
  through an existing component's path, HALT (master §9 trigger 5).

## §6 Halt triggers

1. WD not `cd /Users/lukeivers/loam` before source edits → halt.
2. **The live statusline stdin envelope at build time does NOT carry a
   `context_window` object** (CC version drift below 2.1.132, or schema change) →
   halt + surface; the sensor's premise has failed. Verify Tier-0 empirically
   before source edits (research §9: surfaces move weekly).
3. Meter write would require touching a sealed component → halt.
4. An AC reframes to method-in-AC and can't be made outcome-shape → halt.

## §7 Ship shape

Single cycle, single seal. Manifest:
`docs/plans/context-management-see-budget-eviction-c1-see.manifest.yaml`. Source
edits land before `loam amend apply`; apply auto-commits; `loam amend seal`
deterministic-seals. HARD-smoke ride-along deferred to the minor's last cycle per
`feedback_hard_smoke_per_minor_before_publish`.

## §8 Risk / open questions

- **Q1 — meter file path.** `<workspace>/.loam/context-meter.json` recommended
  (sibling to the existing `.loam/` build-cursor + migrations). Builder's call on
  exact filename; the AC tests the contents, not the path string.
- **Q2 — statusLine install collision.** The `hands-off-lifecycle` first-run
  statusLine already claims the `statusLine` slot during first-run. This cycle
  ships the script + documents it but does NOT auto-claim the slot. Surface the
  install path (merge vs separate) as a Cycle-1-dispatch note; do not bake.

## §14 Method-decision register (populated at build time)

- D-build.1 — meter file path/name. *(builder)*
- D-build.2 — meter data shape + sentinel representation. *(builder)*
- D-build.3 — statusline-script structure (mirror hands-off-lifecycle vs fresh). *(builder)*
- D-build.4 — `read()` transport injection shape for fixtures. *(builder)*

## §15 Backwards-compat verification

New package only; no existing test regresses. Verify no `statusLine`
settings-collision with `hands-off-lifecycle` (Q2).

## §16 Halt-and-surface findings (plan-authoring)

- Surfaced (non-blocking): Q2 statusLine-install collision; the per-category gap
  (master §10 F2.3). No owner gate blocks this cycle.
