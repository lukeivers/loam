# Component — Hands-Off Lifecycle

**Created:** 2026-04-21 17:25 CDT. **State:** ✅ **COMPLETE — sealed 2026-04-22 06:53 CDT.** Four sub-amendments + new component surface landed across twelve commits (1a55969 → 2ab132a). 967 tests passing across fourteen components; zero regression on nine unamended sealed components. All eight Eve-inferences adopted under close reading; no halts triggered; no fifth amendment case surfaced. One build-agent validation-venv miss (memory-system own-venv pytest-asyncio gap) caught in verification and fixed inline at 2ab132a.

**Phase 5 opener.** First component authored under the new fourth research lens (*zero manual lifecycle management, ever*).

---

## Outcome

Opening a Claude Code session in a fresh pos-v2 workspace produces a running, healthy system on its own, and keeps it healthy through ongoing operation. The user does nothing they cannot do.

Covers: auto-launch of the Graphiti-backed memory sidecar at session start; continuous health supervision; durable filesystem staging when the sidecar is unreachable; reconcile-on-recovery drain; loud escalation when self-heal fails; auto-scaffold of workspace configuration; orchestrator lifecycle bound to the session; fresh root `README.md`; codification of the fourth lens in `FUTURE_IDEAS.md`.

## Load-bearing constraint

The Graphiti-backed memory system is the base layer, non-optional. Filesystem staging is degraded-mode only, urgent-recovery territory, not graceful-degradation territory. Silent-stay-degraded is a failure of the fourth lens, not a satisfaction of it.

## Artifacts

- `research-plan.md` — drafted 2026-04-21; awaiting G1
- `research.md` — not yet produced
- `proposal.md` — not yet produced
- `brief.md` — not yet produced
- `outputs/` — empty

## History

- 2026-04-21 17:25 CDT — component created. Research plan drafted in-turn after owner flagged that the prior response described the action without taking it (the state-but-defer anti-pattern). Awaiting G1 approval.
