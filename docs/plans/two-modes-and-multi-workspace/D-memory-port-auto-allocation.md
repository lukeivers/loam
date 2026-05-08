# Sub-plan D — Per-workspace memory-graphiti port auto-allocation

**Status:** authored 2026-04-25; revised 2026-04-25 to reflect
D-MASTER.2's revision (commit `217477e`) — the allocator writes a
per-workspace `memory.yaml` *override* at `<workspace>/.pos/memory.yaml`
under the new state/preference partition. Sealed-component amendment
to `workspace-bootstrap` (and possibly `memory-system` for a probe-
side seam if needed). Spec objective: re-extension under FUTURE_IDEAS
Idea 9 + amendment #29's named-but-not-shipped auto-allocation.

**Master plan:** `MASTER.md`.

---

## 1. Summary / TLDR

Amendment #29 named the bug — "workspaces with the same default 8765
collide; operator manually edits memory.yaml to disambiguate" — and
shipped the seam (per-workspace port via memory.yaml,
plist-EnvironmentVariables propagation, AC29.5 workspace-identity
/health). It deliberately did NOT auto-allocate the port. Multi-
workspace as a v1 requirement (locked owner ruling 3) raises the cost
of "operator manually edits."

This sub-plan auto-allocates the port at first-run scaffold time:
when a workspace-local `memory.yaml` does not yet exist, the scaffold
finds an unused port (proposed mechanism: `socket.bind(("127.0.0.1", 0))`
to let the kernel pick), writes the chosen port into
`<workspace>/.pos/memory.yaml` (the workspace override, per the C-plan
partition), and the plist's `EnvironmentVariables` carry it through.
Subsequent scaffold-runs honour the existing override (never
overwrite an operator-edited port). Two workspaces scaffolded back-to-
back resolve to two distinct ports without operator intervention.

**Where the override lands (per C-plan partition):**
`<workspace>/.pos/memory.yaml` is the workspace override. The global
`~/.pos/memory.yaml` (if the operator has one) keeps its current
default port (8765) untouched and continues to apply to any workspace
that hasn't been scaffolded under the new auto-allocator. The
graphiti service reads the workspace override via the resolver
introduced in C; D simply ensures the override exists with a
collision-free port for every newly-scaffolded workspace.

Per AC29.3 the port source is workspace-local; per AC29.5 the
/health response carries workspace identity. D adds AC.D4: the
allocation is collision-free at scaffold time.

---

## 2. Spec-objective placement

Sealed-component amendment to `workspace-bootstrap`. Spec objective:
same as amendment #29's — Idea 9 re-extension. Where #29 stopped at
"operator edits memory.yaml," D ships "scaffold writes a non-
colliding workspace override."

§2.5 forward+reverse audit per the standard cycle.

---

## 3. Three-lens analysis

### Lens 1 — Claude-leverage

No new Claude primitive. The mechanism uses OS-level port-bind
discovery; Claude never sees the port allocation step. The override
file lands at the location the C-plan resolver expects, so the
graphiti service composes on the resolver chain rather than having a
bespoke read path.

### Lens 2 — Harness + primary-persona value

**Primary-persona test.** *Does this reduce the translation burden?*

Yes. Today a second-workspace operator runs into "Address already in
use," reads memory.yaml, picks a free port, edits it. The persona has
to translate "memory-system won't start" → "the port is taken" →
"edit memory.yaml" → "restart launchd." After D, the scaffold writes
a workspace override with a free port; the operator never learns
about port allocation.

**Harness test.** *Does this add to the toolkit the primary persona
can draw from?*

Indirectly — the persona's session-start probe (amendment #29's
AC29.5 health check) becomes more reliable because the underlying
allocation is collision-free. The toolkit gains "auto-allocated
workspace-local ports written as workspace overrides on the
preference-class resolver chain" as a reach-for primitive that future
multi-port components compose against.

### Lens 3 — ODD authoring

ACs are outcome-shaped. Method (the OS-level discovery mechanism vs
a registry-based allocator) is the builder's call.

---

## 4. Acceptance criteria (AC.D1–AC.D5)

### AC.D1 — Scaffold writes a non-default port when 8765 is busy

When the scaffold runs for the first time on a host where port 8765
is already bound (by another workspace's memory-sidecar, or by an
unrelated service), the scaffold's workspace override
(`<workspace>/.pos/memory.yaml`) carries a port other than 8765. The
chosen port is in the ephemeral range (or any free range — builder's
call) and is verified free at the moment of selection.

**Test shape:** in a fixture that opens a listener on 8765 before
calling the scaffold, run the scaffold; assert the resulting
`<workspace>/.pos/memory.yaml` `port` field is NOT 8765 and that
`socket.bind` to that port succeeds (proves it was free at write time).

**Maps to:** AC.PO.1 + AC.PO.2.

### AC.D2 — Scaffold writes 8765 to the workspace override when free (default-preservation)

When 8765 is free, the scaffold writes 8765 to the workspace override
at `<workspace>/.pos/memory.yaml`. The default port is preserved when
no collision exists, while the override file's *existence* gives the
workspace explicit ownership of its port (no implicit dependency on
the global default).

**Test shape:** scaffold a fixture workspace on a host where 8765 is
free; assert `<workspace>/.pos/memory.yaml` `port` is 8765.

**Maps to:** AC.PO.1.

### AC.D3 — Subsequent runs preserve the operator-edited workspace override

A scaffold run against a workspace that already has
`<workspace>/.pos/memory.yaml` with a manually-edited port honours
the existing value (no overwrite). This is the existing AC29.3
contract; D extends it: the auto-allocation only fires on fresh
scaffold (no workspace override) or on partial-recovery (where the
file is absent under amendment #28's pattern).

**Test shape:** scaffold a fixture workspace, edit
`<workspace>/.pos/memory.yaml` manually to port 9000, re-scaffold;
assert the override retains 9000.

**Maps to:** AC.PO.1.

### AC.D4 — Two scaffold-runs back-to-back produce distinct ports

When two workspaces are scaffolded sequentially on the same host with
neither's memory-sidecar yet running, both workspace-override
`memory.yaml` files end up with distinct ports. (The race-window
where the second scaffold runs before the first's launchd boots its
sidecar is the failure mode this AC closes.)

**Test shape:** scaffold workspace A (no sidecar boot), scaffold
workspace B; assert ports differ. Edge case: scaffold A, boot A's
sidecar, scaffold B; assert B's port differs from A's.

**Maps to:** AC.PO.1 + AC.PO.2 + AC.PROG.1.

### AC.D5 — Allocation diagnostic on probe failure

When the scaffold cannot allocate (e.g., the host has no free ports
— not realistic, but defensive), it raises a structured diagnostic
naming the failure (no observability silent swallow). The default-
port 8765 path is documented as the fallback when allocation fails —
but fallback to 8765 is allowed only if no other workspace is using
it (AC.D1 still applies).

**Test shape:** mock the OS-level allocator to raise; assert a
structured error propagates with the failure mode named.

**Maps to:** AC.PO.1 + AC.PO.2.

---

## 5. Out of scope

- A workspace-local port-registry (centralised allocator). Inverse-
  asymmetric per §13 below.
- Allocation of any port other than memory-graphiti's. Other services
  (orchestrator UNIX socket, Telegram health) don't use TCP ports
  contention-prone for multi-workspace.
- Cross-host coordination. Single-host only.
- Port range constraints (firewall-friendly, etc.). Not in v1.
- Modifying the global `~/.pos/memory.yaml`. The auto-allocator only
  writes the workspace override; the global default stays untouched
  per the C-plan partition.

---

## 6. Halt triggers

1. **AC.D1's mechanism (e.g. `bind(0)`) creates a TOCTOU race that's
   load-bearing in production.** Halt and surface; D-D.2 names the
   alternative (registry).
2. **The amendment ends up touching `memory-system` source.** Surface
   — that's a re-extension of memory-system needing owner approval.
3. **AC.D4's two-workspace test cannot be authored without
   sealed-component apparatus.** Halt and surface; we may need a
   fixture-only seam.
4. **An operator-edited workspace override (AC.D3) gets clobbered by
   a bug in partial-recovery logic.** Halt — that's a regression on
   AC29.3.
5. **The C-plan resolver has not yet landed when D dispatches.** D's
   write target (`<workspace>/.pos/memory.yaml` as workspace override)
   depends on the partition being established; if the resolver isn't
   in place, halt and surface — D may need to land on top of C, or
   carry a transitional default that lands in `<workspace>/config/`
   pending C.

---

## 7. Bookkeeping

`pos-amend` manifest: single component (`workspace-bootstrap`).

- `seal_test`: `workspace-bootstrap/tests/test_no_sealed_amendments.py`
- `sidecar`: `workspace-bootstrap/tests/SEAL_COMMIT`
- `frozen_baseline: false`

If memory-system is touched: add a second component to the manifest;
that opens a #29-style multi-component path.

Universal paths: `docs/plans/`, `CLAUDE.md`, `docs/odd-*.md`.

Narrative target: `workspace-bootstrap/seals/SEAL_COMMIT.memory-port-auto-allocation`.

---

## 8. Dispatch-time additions

When the brief is drafted:

- WD: canonical.
- Plan-before-code.
- ODD §2.4 + §2.5 audit.
- Independent of A/B/E/F by surface; soft-coupled to C through the
  resolver/partition convention (D writes a workspace override at the
  location C's resolver expects). Recommended order: D dispatches
  after C.1 (resolver seam) lands, or carries a transitional write
  location with a follow-up to rotate. Per
  `feedback_serialize_amendment_builds`'s allowance for non-overlapping
  components in the same canonical tree, but ONLY if no other
  amendment is currently building; today canonical serialises. The
  owner can rule that D goes first or last.

---

## 9. Lens-2 trace blocks

| AC | AC.PO.1 | AC.PO.2 |
|----|---------|---------|
| AC.D1 | Operator never has to find a free port. | Auto-allocator extends scaffold primitive; workspace override on resolver chain. |
| AC.D2 | Default preserved when uncontested. | Existing default-preservation primitive; workspace override is explicit. |
| AC.D3 | Operator edit preserved across re-scaffolds. | AC29.3 contract preserved on the override location. |
| AC.D4 | Two-workspace coexistence works without operator. | Cross-workspace coexistence primitive. |
| AC.D5 | Allocation failure surfaces structurally. | Diagnostic primitive. |

---

## 10. Decision register (sub-plan-local)

| Code | Question | Recommendation |
|------|----------|----------------|
| D-D.1 | Allocation mechanism: `bind(0)` (kernel-picks) vs scan starting at 8765 (incremental)? | `bind(0)`. Simpler, no scan loop, kernel handles range exhaustion. The "starting at 8765" framing in the dispatch brief is a method hint not a constraint. |
| D-D.2 | Should D ship a workspace-local port-registry (`<workspace>/.pos/ports.yaml`)? | No. The OS port-table is the registry. A YAML file would duplicate state and create staleness hazards. Inverse-asymmetric. |
| D-D.3 | TOCTOU window: time between `bind(0)` close and the actual launchd-spawned sidecar bind. Worth mitigating with a port-reservation file? | No. The window is microseconds; in v1 we accept it. If a future amendment finds it bites, re-extend. |
| D-D.4 | Should `memory-staging.yaml` also auto-allocate (its own port)? | No. memory-staging uses an in-process SQLite, no TCP port. |
| D-D.5 | Should D write the override into `<workspace>/.pos/memory.yaml` even when 8765 is free, or only when allocating non-default? | Always write the override. Explicit ownership of the workspace's port avoids surprises if the global default later changes; the override file is small and aligned with C's partition. |

---

## 11. Builder freedom

Builder chooses: exact mechanism for AC.D1 (bind(0) vs scan), the
range for AC.D5 fallback, the YAML key the chosen port is written
under (the existing key is `port` per `_MEMORY_YAML`; method-level
preserved). Builder chooses how the override file is laid out beyond
the `port` field (minimal vs full clone of the global shape).

---

## 12. Test register

| AC | Suggested test file | Suggested test function |
|----|---------------------|--------------------------|
| AC.D1 | `workspace-bootstrap/tests/test_memory_port_auto_alloc.py` | `test_AC_D1_collides_with_8765_picks_free` |
| AC.D2 | `workspace-bootstrap/tests/test_memory_port_auto_alloc.py` | `test_AC_D2_default_8765_when_free` |
| AC.D3 | `workspace-bootstrap/tests/test_memory_port_auto_alloc.py` | `test_AC_D3_partial_recovery_preserves_edit` |
| AC.D4 | `workspace-bootstrap/tests/test_memory_port_auto_alloc.py` | `test_AC_D4_back_to_back_distinct_ports` |
| AC.D5 | `workspace-bootstrap/tests/test_memory_port_auto_alloc.py` | `test_AC_D5_allocation_failure_diagnostic` |

---

## 13. Asymmetric observations

1. **The OS port-table as registry is the asymmetric win.** A
   bind(0)-then-close-then-write-yaml dance is a couple lines of code,
   no new state surface, no race-on-cleanup. Effort: low. Leverage:
   high.

2. **Composing on C's partition (asymmetric win, taken).** The
   workspace override at `<workspace>/.pos/memory.yaml` is the
   natural target under C's resolver. Global `~/.pos/memory.yaml`
   keeps working untouched as a default for any workspace that
   doesn't carry an override. Effort: zero (just write to the
   override location); leverage: medium-high (no global mutation,
   per-workspace isolation by construction).

3. **Inverse-asymmetric: a workspace-local port-registry.** Tempting
   because it would let us reason about port allocation without
   touching OS state, but the kernel already handles allocation; a
   file-based registry duplicates that state and creates a new class
   of sync-hazards. Dropped per D-D.2.

4. **Inverse-asymmetric: cross-host coordination.** Allocating ports
   so the same workspace cloned on machine A and machine B uses the
   same port is a problem nobody has. Dropped.

5. **Compose with #29 cleanly.** D inherits AC29.5's workspace-
   identity /health check, AC29.3's workspace-local config, AC29.2's
   plist propagation. D is a one-AC delta over #29's surface,
   re-routed through C's partition.
