# Handoff Brief — True First-Run

**For:** the general-purpose Agent dispatched to build the true-first-run component.
**From:** Eve, 2026-04-22 07:55 CDT.
**Status:** awaiting owner's G4 review; not yet dispatched.

---

## 1. What you are building

The true-first-run component for pos-v2. When a user clones pos-v2 into a fresh directory, `cd`s into it, and runs `claude`, the session opens and setup completes on its own: Python version is gated, the top-level virtualenv is created, per-component dependencies are installed, `.claude/settings.json` is authored with the correct `SessionStart` stanza, the plist templates are substituted and installed as user services, both the memory sidecar and the orchestrator come up healthy, a single confirmation sentence reports completion, and the first-run shell script removes itself from the filesystem. The SessionStart stanza is rewritten to invoke the sealed supervisor path directly. Session two onward: no first-run code remains; the supervisor fires cleanly; session is silent except for its normal work.

Three shell commands — `git clone`, `cd`, `claude` — plus one confirmation sentence is the entire manual sequence.

## 2. Authoritative documents (read in this order)

1. **This brief.**
2. **`components/true-first-run/proposal.md`** — the binding contract. Halt and signal rather than deviate.
3. **`components/true-first-run/research.md`** — design detail. Reference only; the proposal governs where they conflict.
4. **`docs/rebuild/FUTURE_IDEAS.md`** in pos-v2 — the Core Development Conventions (*setup scripts self-retire on success*, *step-by-step when the system cannot act*) and the four research lenses this component's design was evaluated against.
5. **`docs/rebuild/components/hands-off-lifecycle/`** in pos-v2 — the prior component whose scope this one completes. Particular attention to the sealed hook-fragment's intent (the supervisor path it describes is what first-run hands off to on Phase 6).

## 3. The objective in one sentence

Deliver the seven-phase first-run lifecycle such that a fresh-cloned pos-v2 workspace becomes a running healthy system on the first `claude` invocation with no user setup steps beyond the three shell commands, the first-run script self-retires on verified success, and any mechanically-impossible step produces exact step-by-step user instructions rather than advice.

## 4. Hard constraints (non-negotiable)

- **Branch:** `pos-v2`. **Language:** Python 3.13 for the helper; POSIX shell for the bootstrap.
- **No heavyweight bootstrap deps.** Shell uses POSIX-baseline tools. Python helper uses stdlib `venv` and stdlib generally; `uv`, `poetry`, `pipenv` are not used.
- **Python version gate enforces 3.13.** On a machine without a compatible interpreter, halt at Phase 1 with a named diagnostic and exact step-by-step install instructions (per the step-by-step-when-impossible convention).
- **No behavioural amendments to sealed components.** hands-off-lifecycle's hook fragment's *intent* is honoured; the fragment's text is not amended. Two documentation-only edits (hands-off-lifecycle README + `_comment` field) are permitted per Q1 ruling — the "clarification" class.
- **Self-retire on success.** Phase 6 rewrites `.claude/settings.json`'s `SessionStart` stanza to invoke `orchestrator/scripts/pos_session_start.py` directly with the venv's Python, and deletes `hands-off-lifecycle/hooks/first-run.sh` from the filesystem. Phase 7 verifies both. No check-and-skip logic persists.
- **Step-by-step when the system cannot act.** Any failure whose remediation requires user action produces numbered instructions with expected time, not advice. Applies minimally to Python-version-gate failures (current canonical case); the pattern generalises to any future user-dependent step.
- **Stanza-specific settings.json precedence.** pos-v2 wins only for the `SessionStart` stanza; user-authored keys elsewhere are preserved. A user-authored pre-existing `SessionStart` hook is moved aside to a backup file with the user notified in the confirmation sentence.
- **Loud escalation on any failure.** No silent-continue, no partial-first-run pretending success. Each named phase failure produces a structured diagnostic.
- **Idempotent re-run.** First-run either completes cleanly (with self-retire) or halts with diagnostic; next session attempts again. No ambiguous state.
- **Memory is mandatory.** The memory sidecar's own venv + Graphiti install + plist install + service launch all complete in first-run. The sidecar must be healthy before Phase 6 self-retire.
- **`first-run-inventory.yaml` at pos-v2 root.** Workspace-level manifest.
- **Telegram support is NOT in scope.** Telegram is the next Phase 5 component; this build does not touch MCP-plugin-installation or Telegram-channel wiring.
- **Error codes in `-32091..-32099`** within hands-off-lifecycle's existing allocation. No new range; builder picks specific codes and updates hands-off-lifecycle's README error-code table as part of the permitted clarification class.
- **Halt on deviation.**

## 5. Acceptance (ODD — 18 T-criteria in proposal §4)

T1–T4: end-to-end flow — fresh clone + three shell commands produces healthy system + confirmation sentence; subsequent sessions silent supervisor-only; `.claude/settings.json` user-keys preserved.
T5–T6: Python version gate — 3.12 or no-Python halts with step-by-step instructions.
T7–T10: venv + dep install — top-level venv, shared-venv components install there, own-venv components install into their own (memory-system canonical), network failure halts with loud escalation (resumable).
T11–T13: settings.json authorship — from-scratch on absent file, stanza-merge on pre-existing, pre-existing `SessionStart` backed up with user notified.
T14–T15: plist substitution + service launch — both services healthy within Phase 4 timeout; service-launch failure loud-escalates.
T16–T18: self-retire — shell script gone, settings.json stanza points at supervisor directly, verification failure loud-escalates.

## 6. Verify-against-code discipline

Before authoring any code, open the relevant files and confirm surfaces exist as the proposal describes. Five priority verifications:

- **`hands-off-lifecycle/hooks/settings.json.fragment`** — read the hook's target script path; confirm the supervisor-path the rewritten settings.json should point at post-self-retire.
- **`orchestrator/scripts/pos_session_start.py`** — confirm this is the sealed supervisor entry point your Phase 6 hands off to. Its signature and expected working directory are what you must match in the rewritten stanza.
- **Component `requirements.txt` files** — inventory them to drive `first-run-inventory.yaml`. Memory-system is known own-venv; check each other component for its own `requirements.txt` and infer from presence/content whether it needs its own venv.
- **`memory-system/launchd/com.pos-v2.memory-graphiti.plist`** and **`orchestrator/ops/launchd/com.pos.orchestrator.plist.tmpl`** — check variables needing substitution, destination paths, any existing substitution helper provided by Amendment 4.
- **Amendment 4's `first_run_scaffold.py`** in `workspace-bootstrap/` — confirm the YAML-scaffold + plist-substitution + service-bootstrap plumbing this component *uses as a library* rather than re-implements.

If any of these does not match a proposal claim, halt and signal with the named file and symbol.

## 7. Eve's inferences (proposal §8) — challenge any that feel wrong

Six items are Eve's extrapolation rather than owner rulings:

1. Phase ordering (seven phases in the specific sequence named).
2. Resume-or-restart disposition per phase.
3. Partial-first-run detection marker (absence of top-level `.venv/` vs a dedicated sentinel).
4. User-prior-`SessionStart` backup filename pattern.
5. Stdlib-only Python helper — no `pyyaml`; use stdlib `json` or a JSON-compatible YAML subset parseable by stdlib.
6. Specific error-code assignments within the `-32091..-32099` block.

Challenge any with a halt signal and an alternative.

## 8. Estimate

**60–95 minutes wall-clock; red line at 120.**

Shorter than hands-off-lifecycle because Amendment 4 already ships the YAML-scaffold + plist-substitution + service-bootstrap plumbing you consume as a library. Scope additions are venv creation, per-component dep install, settings.json authorship + merge, self-retire + verification.

**Halt triggers at build time:**

- Past 120 minutes without the eighteen T-criteria mapped to passing tests — halt and report partial progress.
- Any behavioural amendment surfacing to a sealed component (beyond the two permitted doc-only clarifications) — halt and surface.
- Any regression on an unamended sealed-component test suite — halt.
- stdlib-only discipline cannot hold for YAML parsing — halt and surface (this is a bootstrap-dep constraint, not flexible).

## 9. What I need back

On completion:

1. **Paths to commits on `pos-v2`** — commit granularity is your call. Minimum: the component build, the doc-only clarification edits to hands-off-lifecycle, and the SEAL_COMMIT sidecar for true-first-run.
2. **Test results** — every T-criterion (T1–T18, plus any T19+ you added with rationale) mapped to a passing test. All sealed-component regression suites passing.
3. **Sealed-component diff check** — `git diff --name-only <baseline>..<your-head>` should cover `hands-off-lifecycle/README.md` (doc-only), `hands-off-lifecycle/hooks/settings.json.fragment` (doc-only `_comment` edit), the new `.claude/settings.json` at pos-v2 root, the new `first-run-inventory.yaml` at pos-v2 root, new surfaces under `hands-off-lifecycle/hooks/`, and any new surface for the true-first-run component itself. Anything else is a halt-signal.
4. **SEAL_COMMIT sidecar present** for the new component.
5. **Eve-inferences challenged** and the alternative chosen (or halted on).
6. **Any halt signals** — named component + surface + what you tried first.
7. **Actual wall-clock vs the 60–95 min estimate.** Honest calendar minutes from the task-notification `duration_ms` field.
8. **Validation ran in BOTH the shared pos-v2/.venv AND memory-system's own venv** (ritual from the hands-off-lifecycle build). Report each.

Return summary: under 500 words. Code and tests carry the detail.

## 10. Failure modes I am watching for

- Scope creep beyond the seven phases. Don't add uninstall-path, don't add Telegram configuration, don't add orientation content. Each is its own component.
- Behavioural amendment to hands-off-lifecycle smuggled inside a "clarification." If the hook fragment's *text* changes beyond the `_comment` field, that's an amendment not a clarification — halt and surface.
- Monkey-patching Amendment 4's `first_run_scaffold.py` instead of consuming it as a library.
- Silent-continue on any failure — loud escalation is the constraint, not a preference.
- Partial self-retire (script deleted but settings.json not rewritten, or vice versa). Phase 7 exists specifically to catch this.
- Heavyweight bootstrap deps creeping in via a transitive import.
- Validating only in the shared venv; see the hands-off-lifecycle memory entry from 2026-04-22.

---

**End of brief.** Owner reviews at G4; on their green light, dispatch follows.
