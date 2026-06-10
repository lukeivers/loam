# Dormant write-time gates — archived by decision (2026-06-10)

**Status:** ruled, owner-ratified (methodology-synthesis verdict §2.4,
ratified 2026-06-10 15:06 CDT, Discord 1514360242; KEEL adoption program
Phase 1, AC.KDOC.4).

Two write-time enforcement hooks were built and sealed but never registered
in canonical `.claude/settings.json` (Tier-0 verified at plan-authoring HEAD
`c232ab3e` and re-verified at build time — the only live hook is the Stop
hook):

- `plugins/dev-sdlc/hooks/objective_binding_gate.py` — per-edit
  objective-binding gate (ODD §2.5 write-time check).
- `plugins/dev-sdlc/hooks/tdd_guard.py` — per-edit TDD guard.

**Ruling: ARCHIVE — do not wire, do not promote to KEEL's Gate.** The files
stay in the tree (this note is the archive mechanism; deleting sealed code
is a separate cut-class amendment if ever wanted), but they are
**archived-by-decision**: doctrine no longer claims them, nothing may
register them without a new owner-ratified amendment, and the rewritten
spec (`plugins/dev-sdlc/docs/odd-methodology.md` §10.3) states plainly that
no write-time structural enforcement is active.

## The three reasons (verdict §2.4, verbatim in substance)

1. **Completion-time vs write-time.** KEEL's Gate is a *completion-time*
   choke point; per-edit write gating polices *method during build*, which
   KEEL deliberately leaves free ("Method is entirely the builder's
   business"; mid-build waste is explicitly Tier-3). Wiring these gates
   would be anti-KEEL.
2. **The record was produced with them off.** The implementation-fidelity
   audit proves the works-as-expected outcome record was produced with both
   gates dormant — they are not load-bearing and never were.
3. **Built+sealed+dormant is the worst state** (audit rec #2): doctrine
   claiming enforcement that does not run is the doctrine falsifying
   itself. This dated note ends that state.

## The salvaged component

One piece of the write-time idea survives, reborn at the correct (dispatch,
not edit) altitude: **dispatch contract-carriage** — KEEL's Tier-1 "a
sub-agent dispatched without the contract does not launch" — lands as an
extension of the existing `plugins/dev-sdlc/hooks/dispatch_setup_hook.py`
(which already carries the `<AC-MANIFEST>` contract), requiring (charter
path, criteria path, content hash) on contract-carrying dispatches. Built
in **KEEL adoption program Cycle A** (`docs/plans/keel-adoption-program.md`
§6), with a liveness AC per decision D10: every hook that program ships
must be LIVE-registered and observed firing on a production path — the
program that archives these dormant gates must not mint new ones.
