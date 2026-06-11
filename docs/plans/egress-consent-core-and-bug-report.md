# egress-consent — Slice 1: the never-leak core + the bug-report consumer

**Owner-greenlit:** Luke, Telegram 13512 (privacy-safe data-sharing layer).
**Design:** `workspace/.scratch/claude-output/loam-privacy-safe-data-sharing-design.md`
(authored in pos3; this plan + the build land in `/Users/lukeivers/loam`).
**Slice:** Slice 1 of the design's §5 staged plan — the fail-closed egress-consent
CORE (§1) + the bug-report consumer (§2). The health/analytics evaluator (§3,
slices 2–3) is OUT OF SCOPE.
**BASELINE:** `9fd5593e` (loam HEAD @ plan-authoring, branch
`egress-consent-core-and-bug-report`). The builder re-baselines to the actual
source-edit commit if it differs.
**Seal:** LOCAL only. NEW commits only; never `--amend`. Do NOT push.

---

## §1 — Objective (ODD)

> **No data, file, or content leaves the user's machine unless the user has seen
> exactly what would leave, in plain language, and explicitly approved it
> per-item. The default is NOTHING-LEAVES, enforced by construction (a
> fail-closed release gate), not by a runtime promise.** A non-technical user who
> hit a problem can report it through a single audited choke point — without any
> data leaving that they did not see and approve, and without needing to know
> what GitHub is.

Method is the builder's call (ODD §1.1). This plan fixes the contract — the
fail-closed states, the content-identity binding, the single choke point, the
per-item decision model, the secret-pre-redaction, the plain-language review
surface, the always-available local fallback — NOT the implementation internals.

## §2 — Scope + placement

**NEW component** `framework/egress-consent/` (package `loam.egress_consent`).
A new component is the correct placement: a grep across `framework/` + `docs/`
finds NO existing egress / consent / off-machine-send surface (the FM.SILENT-EGRESS
matrix row, built in v1.0.1, explicitly records this gap as `guard_kind: none`).
The egress gate belongs in none of: reversibility-primitive (irreversible-op
binding, not egress), safety-layer (dangerous-op + secret floor — this CONSUMES
its secret floor + structural_hash, does not extend them), self-correction
(recovery/distress — this CONSUMES its recovery-surface vocab probe). Clean
boundary (doctrine §"How loam is built — in layers").

**Single-component fence.** All deltas land under `framework/egress-consent/`
plus the universal `docs/plans/` prefix + `CLAUDE.md`. Zero edits to any sealed
component — all compose-points are consumed through their public surfaces.

## §3 — Lens-1 compose-points (consumed via public surface, NOT re-implemented)

| Need | Composes on (sealed, public surface) | Not rebuilt |
|---|---|---|
| Fail-closed structural refusal posture | reversibility `ActivationGate` shape — deterministic class-dispatch, no LLM, refuse-before-side-effect (`framework/reversibility-primitive/.../activation_gate.py`) | a new gate engine |
| Approval bound to content identity | safety-layer `structural_hash` semantics — canonical-JSON SHA-256 of the approved set; ANY mutation invalidates (`loam.safety_layer.events.structural_hash`) | a new hashing/binding scheme |
| Secret auto-redaction before review | safety-layer secret floor `loam.safety_layer.hooks._secret_patterns.CONTENT_PATTERNS` (the 14-pattern ECC floor) | a new secret scanner |
| Plain-language / zero-internal-vocab review surface | self-correction vocab probe `loam.self_correction.recovery_surface.find_internal_vocabulary` / `contains_internal_vocabulary` | a new vocab probe |
| Named user-runnable verb | `loam.cli.subcommands` entry-point group (symmetric to `loam recover` / `loam amend`) — builder ships a `build_report_subcommand(subparsers)` | a new CLI framework |
| Local-fallback artefact delivery | output-to-disk convention (write the bundle to the user's disk; plain-language path) | a new file-handoff path |

`feedback_no_anthropic_api_key`: the gate is DETERMINISTIC — no LLM inside the
gate, no network except the single allow-listed send at the very end of a PASS.

## §4 — Contract: the EgressBundle lifecycle + the fail-closed release gate

### §4.1 — Shape (the contract; method is the builder's)

```
EgressBundle:
  bundle_id
  purpose          (bug-report | <future>)
  destination      (plain-language name + the actual endpoint identifier)
  items            [EgressItem]
  state            (FSM below)
  approval_binding (content-identity hash of the APPROVED-or-redacted item set,
                    or absent)

EgressItem:
  item_id
  kind             (log-line | file | system-fact | freeform-text | metric)
  plain_summary    (one plain-English sentence — the label)
  exact_bytes      (the literal content that would be sent — the contract)
  decision         (pending | approved | redacted | declined)   default: pending
  redaction        (if redacted: the user-edited replacement bytes)
```

### §4.2 — Bundle FSM (default-everywhere is a no-egress state)

```
DRAFTING ─assemble─▶ AWAITING_REVIEW ─review─▶ REVIEWED
   │                                              │
   │             all items approved/redacted ─────┤
   │                                              │
   ▼                                     any item declined-and-required OR
APPROVED ─explicit "send it"─▶ RELEASED   user picks "don't send anything"
   │                            (off-machine)     │
   └──────────────────────────────────────▶ NO_EGRESS (local fallback taken)
```

A bundle never explicitly driven to RELEASED **cannot** emit. Crash, timeout,
abandoned review, dead channel, ambiguous input → every non-happy path lands in
DRAFTING / AWAITING_REVIEW / NO_EGRESS, all no-egress.

### §4.3 — The release gate (the structural guarantee — deterministic, no LLM)

The ONLY function in the component that performs an off-machine send takes an
`EgressBundle` and calls the gate FIRST. There is no other user-content egress
call site (AC.EG-CORE.3 grep test). Fail-closed dispatch, refusal RAISED before
any socket opens (mirrors the reversibility gate's `-32050`-before-`activate`):

```
bundle.state != APPROVED              → REFUSE (nothing approved yet)
approval_binding absent               → REFUSE (no recorded approval)
approval_binding != hash(current      → REFUSE (bundle mutated post-approval —
  approved-or-redacted item set)        content-identity binding broke)
any item still `pending`              → REFUSE (unreviewed item present)
destination not on the allow-list     → REFUSE (unknown endpoint)
else                                  → PASS → send the approved/redacted set ONLY
```

The send primitive exposes NO gate-skip path (AC.EG-CORE.3): like the
reversibility gate having no resolver-absent bypass, the egress send fail-closes
rather than offering a gate-absent door. The released payload contains EXACTLY
the approved + redacted items; declined items are STRUCTURALLY excluded
(constructed out of the payload, not skipped at send time). A redacted item ships
its replacement bytes; the original never leaves (AC.EG-CORE.5).

## §5 — The two-layer review surface (§1.3 of the design)

- **Layer A — plain-language default.** A numbered list, one line per item, in
  the abstraction-first voice: *what it is* in human terms + its current
  decision + the available actions (show / hide / remove or show / edit /
  remove). The rendered surface carries ZERO internal vocabulary, verified by the
  reused `find_internal_vocabulary` probe (AC.EG-REVIEW.1). A non-technical user
  drives it with a number / "send" / "don't send anything".
- **Layer B — exact-bytes expansion.** "show" on an item reveals the literal
  bytes the gate would send for that item. The expansion is byte-faithful to what
  the gate actually transmits for that item (AC.EG-REVIEW.2) — the label cannot
  lie about the contract.

Per-item decision model: every item is independently **approve / redact /
decline**. The approval binds (via `structural_hash` semantics) to the exact
approved-or-redacted set; the gate re-hashes at release and refuses on mismatch.

## §6 — The bug-report consumer (§2 of the design)

Production entry-point: a `loam report` verb registered on `loam.cli.subcommands`
(symmetric to `loam recover`), PLUS a programmatic entry-point function the
persona-flow + the outcome-altitude tests drive. The verb makes NO LLM call and
spawns NO Claude session (deterministic surface).

Flow:
1. **Understand it** — a short plain-language interview (1–3 questions, one at a
   time per `feedback_one_question_at_a_time`) characterizing the problem. The
   interview text is supplied to the entry-point (the persona conducts the
   conversation; the component consumes the answers) — so the entry-point is
   testable without an interactive prompt.
2. **Assemble a candidate bundle** (DRAFTING) from LOCAL signals only: the
   what-went-wrong note (the user's words, editable), loam version + coarse env
   facts (OS name — never username/paths), optionally a log excerpt or a file.
   **Files / logs default to `declined`** (AC.BR.2) — included only on an explicit
   per-item approve.
3. **Secret auto-redaction PRE-review** (AC.BR.3): every candidate item's bytes
   are scanned against the safety-layer `CONTENT_PATTERNS` floor during assembly
   and matches are redacted BEFORE the review surface is rendered — the user is
   never shown, and can never accidentally ship, a secret loam caught.
4. **Review** through the §5 surface (approve / redact / decline per item).
5. **Destination / fallback** (AC.BR.4): a **friendly intake** the user
   understands ("we'll send it to the loam team" — NO "GitHub" jargon shown), OR
   the always-available **local-only fallback** — loam writes the report to the
   user's own disk and tells them, in plain language, where it is + what they can
   do. The fallback is first-class, never a dead end, and lands a REAL on-disk
   artefact with zero egress.

**FORK F-BR-1 (friendly intake shape) — RULED for this slice:** ship
**local-fallback + an allow-listed friendly-intake destination identifier** with
the send wired through the gate. The concrete network transport to the intake is
a config-level endpoint behind the allow-list — the gate works identically
whether the intake is email-to-issue, a form, or GitHub-direct (the design's
choke-point property makes swapping the destination a config change, not a
redesign). The outcome-altitude AC exercises BOTH the local-fallback path (real
file on disk, zero egress) AND the gate-PASS release path (approved set only).
Recommendation for the eventual concrete intake stays email-to-issue (design
§2.4); not blocking this slice.

## §7 — Acceptance criteria (outcome-shape; every test maps to one — ODD §2.5)

**Core:**
- **AC.EG-CORE.1 — default is no-egress.** A bundle assembled but never
  explicitly approved-and-released emits nothing off-machine.
- **AC.EG-CORE.2 — fail-closed release gate.** The gate refuses on each of:
  not-approved, absent binding, binding-mismatch (post-approval mutation), any
  pending item, unknown destination — each refusal RAISED before any send.
- **AC.EG-CORE.3 — single choke point.** No user-content off-machine send exists
  except through the gate — a tree-grep test (no raw egress call sites in the
  component) + the send primitive has no gate-bypass path.
- **AC.EG-CORE.4 — content-identity binding.** An approval bound to item-set X is
  invalidated by ANY change to the set; the gate refuses a mutated set under a
  stale approval (reuses `structural_hash` semantics).
- **AC.EG-CORE.5 — per-item approve/redact/decline.** The released payload
  contains EXACTLY the approved + redacted items and structurally excludes
  declined items; a redacted item ships its replacement bytes, never the original.
- **AC.EG-REVIEW.1 — plain-language review surface.** The default review view is
  plain-English (no JSON-reading required) and carries ZERO internal vocabulary
  (reuses `find_internal_vocabulary`).
- **AC.EG-REVIEW.2 — exact-bytes faithfulness.** The exact-bytes expansion for an
  item is byte-faithful to what the gate would actually send for that item.

**Bug-report:**
- **AC.BR.1 — interactive triage.** A real "report this" entry triggers a
  plain-language interview that characterizes the issue before any bundle leaves
  DRAFTING.
- **AC.BR.2 — files/logs default-declined.** Any file/log candidate item defaults
  to `declined`; included only on an explicit per-item approve.
- **AC.BR.3 — secret auto-redaction pre-review.** Candidate item bytes matching
  the secret-pattern floor are redacted during assembly, BEFORE the review surface
  is rendered.
- **AC.BR.4 — friendly destination + always-available local fallback.** The
  default destination carries no technical jargon to the user; the local-only
  fallback is always offered and lands a real on-disk artefact the user controls.

**Outcome-altitude (`feedback_test_outcome_altitude_required` — STUB-class does
NOT satisfy these; production entry-point, NO pre-arranged state):**
- **★ AC.EG-S.1 — `outcome-altitude: true`.** A real end-to-end run at the
  production entry-point, no pre-arranged state: assemble a real bundle from real
  signals → render the real review surface → user declines one item + redacts one
  + approves the rest → release → assert (a) the off-machine payload contains
  EXACTLY the approved/redacted set and NOT the declined item or its bytes, and
  (b) an attempt to release a *mutated* bundle under the prior approval is
  REFUSED. No stubbed gate, no pre-seeded payload.
- **★ AC.BR-S.1 — `outcome-altitude: true`.** A real "loam broke" entry at the
  production entry-point, no pre-arranged state: interview → assemble → review
  (one item declined) → **local-fallback chosen** → assert a REAL report file on
  disk AND zero egress; then a second run choosing **"send"** → assert the
  approved set (minus the declined item) posts through the REAL gate.

**The never-leak invariant is STRUCTURALLY proven by:** (1) the FSM default + every
error path being a no-egress state (AC.EG-CORE.1); (2) the single grep-audited
choke point with no gate-bypass (AC.EG-CORE.3); (3) the deterministic fail-closed
gate refusing on any uncertainty (AC.EG-CORE.2) bound to content identity
(AC.EG-CORE.4); exercised at the production entry-point with no pre-arranged state
(AC.EG-S.1). "Is there another way out?" is a checkable grep, not a trust question.

## §8 — Out of scope (this slice)

- The health/self-behavior evaluator consumer (§3 of the design — slices 2–3):
  the Stop/SessionEnd hook, the local tuning record, the opt-in analytics bundle.
  **Explicitly NOT built this slice.**
- The concrete network transport to the friendly intake (the actual email-to-issue
  bridge / form endpoint) — the gate + allow-list are built; wiring a specific live
  endpoint is a config follow-on (F-BR-1).
- **FM.SILENT-EGRESS matrix binding** — see §9. Deferred as a follow-on fence.
- Pushing to origin (LOCAL seal only).

## §9 — FM.SILENT-EGRESS matrix binding (DEFERRED — follow-on fence, NOT this slice)

The `FM.SILENT-EGRESS` protection-matrix row already exists (v1.0.1,
`framework/protection-matrix/data/failure-mode-guard-matrix.yaml`), currently
`guard_kind: none` / `guard_ref: ""` / `default_on: NONE` (an honest named gap).
Binding it to this gate is **non-trivial** and is deferred per the brief's
"if binding is non-trivial, leave it for a follow-on and say so":

- The matrix `GUARD_KINDS` enum (`catalogue.py`) is `{hook, release-gate, odd,
  memory, comparator, persona-discipline, none}`. The egress gate is a RUNTIME
  fail-closed gate, NOT a publish-time ALL_GATES release-gate and NOT a hook —
  there is no clean existing `guard_kind` for a runtime egress gate. Forcing
  `guard_kind: release-gate` would resolve the `guard_ref` symbol (check.py only
  checks symbol-definition, not ALL_GATES membership) BUT would mislabel a runtime
  gate as a publish-time gate — a semantic lie in the protection ledger, which is
  exactly the "must not hallucinate its own coverage" property the matrix protects.
- The honest binding needs a NEW `guard_kind` (e.g. `egress-gate` or
  `runtime-gate`) added to the matrix `GUARD_KINDS` enum + the
  `GUARD_REF_REQUIRED_KINDS` set — an amendment to the SEALED protection-matrix
  component, a separate fence with its own AC + seal.

**Recommended follow-on (separate cycle):** add a runtime-gate `guard_kind` to the
matrix catalogue schema, then set the FM.SILENT-EGRESS row to
`guard_kind: <runtime-gate>`, `guard_ref:
framework/egress-consent/src/loam/egress_consent/<gate-file>.py:<GateClass>`,
`default_on: YES`. `loam guards` then shows the row `ok` with a resolved binding.

## §10 — Build mechanics

- Plan-before-code: THIS doc + the manifest land first.
- `loam amend apply` the manifest → author the component → tests green → seal.
- NEW-component first-seal fence on `framework/egress-consent/` (sidecar created
  at this seal; no prior seal to advance), mirroring the usage-window-guard /
  protection-matrix new-component precedent.
- `extra_allowed_prefixes` EMPTY; universal admissions = `docs/plans/` + `CLAUDE.md`.
- Touched-component test suite GREEN; the AC tests above all pass.

## §11 — §status: SEALED + SHIPPED (backfilled 2026-06-11, Tier-0 from the git ref graph)

*This section was backfilled 2026-06-11 — the cycle sealed 2026-06-02 but the
plan-doc was left without a closure record, which the plan-state tracker
misread as "partially built." All SHAs below re-derived from the git ref
graph at backfill time (`feedback_published_state_only_from_git_refs`), never
from prose.*

### Commit SHAs

- Apply (manifest + new-component sidecar): `a41a74cd` (2026-06-02).
- Code commit: `2304dea4` — Slice 1, the fail-closed never-leak core + the
  bug-report consumer, all 13 AC test files.
- Seal commit: `ffb99af2` (narrative at
  `framework/egress-consent/seals/SEAL_COMMIT.egress-consent-core-and-bug-report`;
  sidecar `framework/egress-consent/tests/SEAL_COMMIT` = `2304dea4`).
- Release state (verified from git refs): the seal is an ancestor of tag
  `v1.1.0` — the slice **SHIPPED PUBLIC in v1.1.0** (tagged 2026-06-03) and is
  contained in every later tag through `v1.5.0`.

### Verification at backfill (2026-06-11, HEAD)

- Full fenced suite `framework/egress-consent/tests/` — **45 passed** at HEAD,
  covering all slice-1 ACs (AC.EG-CORE.1–5, AC.EG-REVIEW.1–2, AC.BR.1–4) plus
  both outcome-altitude ACs (★ AC.EG-S.1, ★ AC.BR-S.1) and the seal/secret
  invariant tests.
- §9 (FM.SILENT-EGRESS matrix binding) stayed DEFERRED in this slice as planned,
  and was subsequently closed in its own separate protection-matrix fence:
  `502f9254` (2026-06-02) re-binds the FM.SILENT-EGRESS row to the sealed
  egress-consent gate — the recommended follow-on of §9, executed as a distinct
  cycle exactly as this plan prescribed. It is recorded here for traceability
  only; it is not part of this slice's fence.
