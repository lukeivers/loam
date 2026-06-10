# General build-from-intent — the corrected #86 capability

Per `docs/plans/general-build-from-intent.md`, the build the June-8 demo should
have been. The owner's spec verbatim (Discord 1514064080, 2026-06-09): "It needs
to be able to take their input, ask meaningful questions if it has any, do any
research that's valuable to align expectations with industry standards, plan,
build, keep the user in the loop during the process so they can feel comfortable
that things are moving along." Hard constraints from the same ruling: no faking,
no hardcoded objectives, no pre-built tools posing as generated, no pre-gaming;
must run on a FRESH loam workspace in front of strangers.

Six sequenced slices on the sealed handsoff-loop spine (Lens 1: the intake
honesty machinery, freeze-isolation, independent judge, bounded re-drive, and
in-session dispatch are composed, never re-implemented):

  1. **Per-request intent + meaningful questions (S1, AC.REQ.*).** Any vague
     build-shaped ask in an established workspace triggers a live
     intent-extraction + plain-language confirm (provably non-canned), with a
     bounded number of meaningful questions ONLY when a build-shaping ambiguity
     is real — zero questions on a clear ask. The stated objective is derived
     from THAT run's ask; no objective text exists in pipeline source; the
     retired loam_autoroute shortcut has zero references in canonical loam.

  2. **Domain-grounding research IN the pipeline (S2, AC.DGR.*).** Between
     intent confirm and gate-freeze, a bounded web-research step produces a
     durable practitioner-grounding record (live-resolving citations, fetched
     that run) that demonstrably shapes the generated acceptance gate and flags
     expert-gate points in plain language where research cannot settle a
     judgment standard. Research failure degrades to an explicitly-flagged
     ungrounded build — never silent fake grounding. Records are written
     packs-compatible (durable, indexable) with no dependency on the in-build
     memory-recall cycle.

  3. **The generative middle (S3, AC.GEN.*).** From confirmed intent +
     grounding record, loam derives the objective and GENERATES the tool, the
     data shape, and the acceptance gate — none existing before the run, the
     gate hash-pinned before any build agent sees work (frozen-unseen contract
     preserved by construction). Zero vertical-specific code in framework
     source; one identical code path serves materially different domains.
     Form-factor surfaced in the confirm; verdicts state judge-scope honestly.

  4. **Convergence as canonical default (S4, AC.CVG.*).** Bounded
     re-drive-toward-the-frozen-gate is default fresh-workspace behavior;
     single generous named ceiling per agent leg with timeout terminal (NO
     retry-on-timeout — the #111 empirical lesson, binding); dispatcher-side
     own-the-wait from run artifacts; gate-pass and definite honest negative
     the only terminals, never retried-to-green.

  5. **In-loop progress surface (S5, AC.PRG.*).** Plain-language stage updates
     (understanding -> asking -> researching -> planning -> building ->
     checking -> verdict) with a named heartbeat bound during long legs;
     every progress claim verifiable against the run record (narration is
     not action, enforced). Carried by named Claude primitives: in-session
     Task subagents, dispatcher-side Monitor, SubagentStop events, persona
     narration (channel reply/edit when connected).

  6. **Honest smoke proof (S6, AC.SMK.*).** The Tilth back-office trio —
     App 1 (reconciliation), App 3 (customer-list dedupe), App 2 (books
     migration) — each generated on its own fresh workspace through the one
     general path, honestly scored fails-included with wall-clock + human-gate
     points logged; PLUS at least one OFF-vertical run from an owner-authored
     prompt no build agent saw before run time (D5) — the standing
     anti-rigging probe. Every number run-attributed; any run reproducible
     from one documented command. A change that wins on the trio but degrades
     the off-vertical run does not land.

AC families AC.REQ/DGR/GEN/CVG/PRG/SMK.* — every AC outcome-shape
(method-in-AC test passed per-AC), one outcome-altitude AC per family
(production entry points, fresh workspaces, no pre-arranged state; AC.GEN.OA
is the corrected June-8 demo as a standing test).

Fence: single workspace-bootstrap anchor (the three sealed handsoff-loop-spine
precedents); preserved byte-for-byte in outcome: frozen-unseen, independent
judge, honest-negative (no retry-to-green), the sealed goal-refinement intake
construct, AC.FOUND.0 consumed-not-re-proved, spawn isolation on every model
call. HALT on: any domain-keyed branch in framework source; any edit outside
the fence (incl. frame-kernel / in-build memory-recall surfaces); any
weakening of the honesty terminals; any slice that only works in a
dev-configured workspace. NO Anthropic SDK/API key anywhere. LOCAL SEAL ONLY —
publish is a separate owner-asked action. No version bump (derives at
release time). NEW commits only, no --amend.

No ODD violation in surrounding code; every added path traces to a named AC,
no defensive code for unnamed cases.
