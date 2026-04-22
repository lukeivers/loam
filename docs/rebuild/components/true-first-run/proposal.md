# Proposal — True First-Run

**Status:** DRAFT — awaiting owner's G3 approval.
**Authored by:** Eve. **Date:** 2026-04-22.
**Research baseline:** `research.md` at this component's directory.

---

## 1. Objective

A user clones pos-v2, `cd`'s into the directory, and runs `claude`. The session opens, setup completes on its own (venv creation, per-component dependency install, `.claude/settings.json` authorship, plist-template substitution, service launch), a single confirmation sentence reports completion, the first-run script removes itself from the filesystem and from the SessionStart hook registration, and the supervisor path is now wired. Subsequent sessions fire the SessionStart hook and it goes straight to the supervisor — no first-run code remains to run.

Three shell commands and one confirmation sentence is the entire manual sequence.

## 2. Owner rulings (locked inputs)

Rulings received across G2 + the setup-self-retire clarification, 2026-04-22.

### 2.1 The seven G2 questions

| Q | Ruling |
|---|---|
| Q1 — Do doc-only edits count as sealed amendments? | **No.** Clarifications to README prose or `_comment` fields do not change observable behaviour and are permitted within any component build without reopening the sealed surface. Recorded as a small named class ("clarification") to keep the discipline honest. |
| Q2 — Confirmation-sentence wording | **Accept the researcher's draft** as an extension of Amendment 4's existing sentence, subject to minor tuning during the build if any phrasing lands wrong. |
| Q3 — Hook timeout | **120 seconds** as ceiling; the prototype may revise after measuring real install times on a cold-cache clone. |
| Q4 — `first-run-inventory.yaml` location | **pos-v2 root.** Workspace-level manifest of which components have their own venv vs share the top-level one; living multi-component content belongs at root, not inside a sealed component. |
| Q5 — `.claude/settings.json` user-override preservation | **Merge with stanza-specific precedence: pos-v2 wins only for the `SessionStart` stanza; user overrides preserved everywhere else.** Fourth lens requires the hook to win; everything else is the user's config surface and stays theirs. |
| Q6 — Third-session silence | **Structural, not a policy.** The first-run script removes itself on success; session two onward has no first-run code to produce any output. Silence is the consequence of absence, not of a check-and-skip. |
| Q7 — Uninstall path scope | **Defer to its own component cycle.** BACKLOG'd with trigger "any user asks to uninstall pos-v2." |

### 2.2 The setup-self-retire rule

The owner's rule, stated verbatim 2026-04-22 07:36: *"the first run stuff should just have the last step, once everything is confirmed, as removing itself from the files so that it doesn't run each time. if subsequent updates need new things to be set up on the next run, then they should have their own mechanism for enforcing that."*

Mechanical implications:

- First-run's final phase on verified success is to delete its shell script from the filesystem and rewrite `.claude/settings.json`'s SessionStart stanza to invoke the sealed supervisor path directly.
- No state-marker file, no check-and-skip, no resume-or-restart logic past the narrow window before successful self-removal.
- Future update-triggered setup ships its own self-removing script with its own registration moment; first-run code is not reused as check-and-skip scaffolding.

Captured as a named Core Development Convention in `FUTURE_IDEAS.md` — setup scripts self-retire on success.

## 3. Design shape

### 3.1 The first-run lifecycle, end-to-end

1. **Ship state.** Pos-v2 repo ships with `.claude/settings.json` already authored, containing a `SessionStart` hook that invokes `hands-off-lifecycle/hooks/first-run.sh` (the new shell bootstrap script, introduced by this component). No other Claude Code settings set by pos-v2 at ship time; user retains full control of their settings surface.
2. **Clone.** `git clone <pos-v2-source> ~/pos2`. The `.claude/settings.json` arrives with the clone because it is committed to the repo.
3. **First `claude` invocation.** Claude Code reads `.claude/settings.json`, identifies the SessionStart hook, invokes `first-run.sh` as the hook's command.
4. **`first-run.sh` runs.** POSIX shell, stdlib tools only. Detects first-run state (absence of `<workspace-root>/.venv/` is the canonical marker — no dedicated state-file). Performs the seven first-run phases in order:
   - **Phase 1 — Python version gate.** Detects system Python, verifies 3.13+, halts with `-32091 platform-unsupported:no-compatible-python-found` and a clear install-this-and-retry message on failure.
   - **Phase 2 — Top-level venv creation.** `python -m venv <workspace-root>/.venv/` via stdlib.
   - **Phase 3 — Python helper handoff.** Once the venv exists, shell invokes a stdlib-only Python helper (ships in pos-v2) that handles the heavier work: reads `first-run-inventory.yaml`, per-component venv creation where declared, `pip install` against each component's `requirements.txt`, `.claude/settings.json` merge with stanza-specific precedence, plist-template substitution and install, `launchctl bootstrap` / `systemctl --user start` invocation, confirmation sentence emission.
   - **Phase 4 — Service health verification.** After `launchctl bootstrap`, the helper polls each service's health endpoint (the memory sidecar and the orchestrator, from hands-off-lifecycle's supervisor surface) until healthy or `120s` timeout hit.
   - **Phase 5 — Confirmation sentence emission.** Single-line emission to the Claude Code session (via the hook's stdout-as-context path) describing what was scaffolded at category level.
   - **Phase 6 — Self-retire.** `.claude/settings.json`'s `SessionStart` stanza rewritten to invoke `pos_session_start.py` (hands-off-lifecycle's sealed supervisor entry point) directly, using the now-created venv's Python. The shell script `first-run.sh` deletes itself from the filesystem.
   - **Phase 7 — Final state verification.** The helper verifies that Phase 6 wrote the intended `.claude/settings.json` content and that `first-run.sh` is gone. If either check fails, loud escalation via the primary-persona channel (reusing hands-off-lifecycle's escalation protocol) names the inconsistency.

5. **Subsequent sessions.** Claude Code reads the rewritten `.claude/settings.json`, fires `pos_session_start.py` directly. No first-run code exists; the supervisor path runs cleanly every session.

### 3.2 First-run inventory manifest

A new top-level file, `<pos-v2-root>/first-run-inventory.yaml`, declares which components participate in first-run setup and how:

- Each component declares `shares_venv: true | false`.
- Components with `shares_venv: false` are created with their own venv path (memory-system is the current canonical example).
- Each component declares its `requirements.txt` path.
- Each component optionally declares plist templates or service-manager files to install.
- Each component optionally declares a health endpoint for Phase 4 verification.

The inventory is workspace-level because it is owned by the workspace's setup decisions, not by any single component. As future components land with their own venv requirements (or new service-lifecycle needs), they add themselves to this inventory.

### 3.3 Loud escalation on first-run failure

Any first-run failure (Python-version gate, venv creation, `pip install` network failure, plist bootstrap rejection, health-check timeout, self-retire verification failure) is a loud-escalation event. The helper emits a named-diagnostic message to stdout (which Claude Code surfaces as the session's early context) that:

- Names the failed phase.
- Names the specific failure mode.
- Tells the user what to do to remediate (install Python, check network, retry, etc.).

Silent-continue is forbidden. A partial-first-run state that leaves the user in an unclear condition violates the fourth lens.

### 3.4 Idempotent re-run

Narrow case: the very first session exited mid-first-run (owner Ctrl-C'd, network died during pip install, machine crashed between Phase 3 and Phase 6). The next `claude` invocation invokes `first-run.sh` again because self-retire did not complete. The shell script detects partial state and either resumes (if resumability is safe — e.g. incomplete pip install can idempotent-retry) or restarts (if the partial state is ambiguous — e.g. plist partially installed, settings.json partially merged).

Resume-or-restart disposition per phase is the builder's call during research of failure modes; the principle is that first-run either reaches Phase 6 cleanly or loudly escalates. No third state.

## 4. Acceptance criteria (ODD — 18 objectives)

### 4.1 End-to-end flow (T1–T4)

- **T1.** A fresh clone of pos-v2 into a new directory, followed by `cd <dir>` and `claude`, produces a session with a running healthy system (memory sidecar + orchestrator both healthy per hands-off-lifecycle's supervisor) within 120 seconds. The single confirmation sentence is emitted to the session. No further manual commands were issued.
- **T2.** The second session open on the same workspace fires `pos_session_start.py` directly via the rewritten `.claude/settings.json`. `hands-off-lifecycle/hooks/first-run.sh` does not exist in the filesystem. No confirmation sentence emitted.
- **T3.** The third, fourth, and Nth session opens produce identical behaviour to T2 — supervisor-only, silent, healthy.
- **T4.** The rewritten `.claude/settings.json` preserves any user-authored keys outside the `SessionStart` stanza; only the `SessionStart` stanza reflects pos-v2's authoritative content.

### 4.2 Python version gate (T5–T6)

- **T5.** On a machine with Python 3.12 as the only available interpreter, first-run halts at Phase 1 with error code `-32091` and a plain-language message naming the required version (3.13+) and pointing to an install path.
- **T6.** On a machine without any Python interpreter, first-run halts at Phase 1 with error code `-32091` and a plain-language message naming Python 3.13 as the dependency.

### 4.3 venv creation + dependency install (T7–T10)

- **T7.** Top-level `<workspace-root>/.venv/` is created via stdlib `python -m venv` in Phase 2.
- **T8.** Components declaring `shares_venv: true` in `first-run-inventory.yaml` have their `requirements.txt` installed into the top-level venv.
- **T9.** Components declaring `shares_venv: false` have their own venv created at the component's canonical path, with their `requirements.txt` installed into that venv. (Memory-system is the canonical case at time of build; the pattern generalises.)
- **T10.** `pip install` network failure for any component produces a loud-escalation message naming the component and the failing dependency. First-run does not complete; does not self-retire; next session retry is clean (resumable).

### 4.4 Settings.json authorship (T11–T13)

- **T11.** On a workspace without pre-existing `.claude/settings.json`, first-run's shipped settings.json is used as-is, then rewritten in Phase 6.
- **T12.** On a workspace with a pre-existing `.claude/settings.json` containing user-authored keys, first-run's merge in Phase 3 adds pos-v2's `SessionStart` stanza and leaves every other key untouched. Phase 6's rewrite updates only the `SessionStart` stanza.
- **T13.** A user `SessionStart` hook defined by the user before first-run ran is not silently overwritten without surfacing — user is notified in the confirmation sentence that their prior `SessionStart` was moved aside to `<path>/settings.json.user-backup-<timestamp>.json`, and pos-v2's stanza is authoritative going forward.

### 4.5 Plist-template substitution + service launch (T14–T15)

- **T14.** Orchestrator and memory-sidecar plist templates have `${POS_V2_REPO}` substituted to the resolved workspace root and are written to the platform-appropriate service-manager location. `launchctl bootstrap` / `systemctl --user start` is invoked on each; both services report healthy within the Phase 4 timeout.
- **T15.** Service-launch failure (plist rejected by launchd, systemctl refuses the unit, health-endpoint timeout) produces loud escalation with the named failure; first-run does not self-retire.

### 4.6 Self-retire (T16–T18)

- **T16.** On successful Phase 7 verification, `hands-off-lifecycle/hooks/first-run.sh` does not exist in the filesystem.
- **T17.** On successful Phase 7 verification, `.claude/settings.json`'s `SessionStart` stanza invokes `orchestrator/scripts/pos_session_start.py` with the top-level venv's Python, not `first-run.sh`.
- **T18.** If Phase 7's verification fails (script still present or settings.json stanza still points at first-run), first-run emits a loud-escalation diagnostic naming the inconsistency; does not pretend success.

## 5. Constraints

- **Python 3.13 target.** Detected, gated, and named in failure messages.
- **No heavyweight bootstrap deps.** Shell uses POSIX-baseline tools. Python helper uses stdlib `venv` and stdlib generally; `uv`, `poetry`, `pipenv` are not used for first-run.
- **No behavioural amendments to sealed components.** hands-off-lifecycle's hook fragment's *intent* is honoured (the supervisor path becomes the ongoing hook after first-run); the fragment's text is not amended. Two documentation-only edits (hands-off-lifecycle README + `_comment` field) are permitted as clarifications per Q1 ruling.
- **Self-retire on success.** First-run code removes itself; no check-and-skip surfaces persist.
- **Step-by-step when the system cannot act.** Per the newly-captured Core Development Convention in FUTURE_IDEAS, any first-run step that is mechanically impossible for the script to perform (the canonical case in this component's scope is "no Python 3.13 interpreter present") produces exact step-by-step instructions numbered with expected time, not advice. Loud-escalation messages in §3.3 inherit this shape.
- **Stanza-specific settings.json precedence.** `SessionStart` stanza is pos-v2's; every other key is the user's.
- **Loud escalation on any failure.** No silent-continue, no partial-first-run that pretends success.
- **Idempotent re-run.** First-run either completes cleanly (with self-retire) or halts with diagnostic; next session attempts again. Never leaves ambiguous state.
- **`first-run-inventory.yaml` at pos-v2 root.** Workspace-level manifest.
- **Error-code range `-32091..-32099` extended** within hands-off-lifecycle's already-allocated `-32090..-32099` range. (No new range allocation; this component's errors sit inside hands-off-lifecycle's reservation by design, because first-run is mechanically hands-off-lifecycle's own prerequisite.)
- **Telegram support is NOT in scope** for this component. Telegram one-on-one channel configuration is the Telegram-interface component's responsibility, landing as the immediately-following Phase 5 third component via the Claude MCP Telegram channel plugin (not a custom-built bot). First-run's confirmation sentence names that subsequent setup will happen in session two. Until Telegram is configured, the primary-persona one-on-one channel uses the in-session surface (Claude Code stdout) and `~/.pos/attention.md` as the durable unresolved-state mirror (inherited from hands-off-lifecycle).
- **Halt on deviation.**

## 6. File layout and phase shape

Builder's call on both. Two new surfaces ship:

- **Top-level `.claude/settings.json`** committed to pos-v2 root with the initial `SessionStart` stanza pointing at the first-run script.
- **`<pos-v2-root>/first-run-inventory.yaml`** committed declaring which components participate and how.
- **`hands-off-lifecycle/hooks/first-run.sh`** and **`hands-off-lifecycle/hooks/first-run-helper.py`** (or equivalent paths the builder chooses).

Documentation-only edits to `hands-off-lifecycle/README.md` and `hands-off-lifecycle/hooks/settings.json.fragment`'s `_comment` field per Q1's clarification class.

## 7. Build estimate

**60–95 minutes wall-clock; red line at 120.** Shorter than hands-off-lifecycle because Amendment 4 already ships the per-component YAML scaffold + plist substitution + service bootstrap plumbing; this component adds venv creation + dep install + settings.json authorship + self-retire + state verification on top.

**Halt triggers at build time:**

- Past 120 minutes without the eighteen T-criteria mapped to passing tests — halt and report partial progress.
- Any behavioural amendment surfacing to a sealed component (beyond the two permitted doc-only clarifications) — halt and surface.
- Any regression on an unamended sealed component's test suite — halt.

## 8. Eve's inferences — flagged for the builder to challenge

1. **Phase ordering (seven phases).** The sequence Python-gate → top-venv → helper-handoff → health-verify → confirmation → self-retire → verification is Eve's read. If the builder finds that health-verify belongs before confirmation (so the sentence reports live-healthy state), reorder.
2. **Resume-or-restart disposition per phase** — Eve did not enumerate; the builder makes the call per failure mode during implementation.
3. **Partial-first-run detection marker** is "absence of top-level `.venv/`" as the canonical first-run-not-complete signal. Alternative: a dedicated `.pos/.first-run-complete` sentinel file. Eve's lean is venv-absence because it is the thing self-retire cannot delete (the venv must persist); a dedicated sentinel adds a cleanup concern for the uninstall flow later. Challenge if the builder disagrees.
4. **User-prior-`SessionStart` backup filename** pattern `settings.json.user-backup-<timestamp>.json` is Eve's placeholder; builder may refine.
5. **Stdlib-only Python helper** — no `pyyaml` dependency for reading `first-run-inventory.yaml`; builder uses stdlib `json` or authors the inventory in JSON-compatible YAML that `ast.literal_eval`-or-equivalent can parse. If stdlib-only is untenable, halt and surface (this is a bootstrap-dep-discipline constraint, not flexible).
6. **Error codes `-32091..-32099`** sit inside hands-off-lifecycle's already-allocated block. Codes claimed by this component: `-32091 platform-unsupported` (already claimed by Amendment 4's partial_scaffold_detected case? — verify against hands-off-lifecycle's README), plus any new ones first-run needs for its specific failure modes (pip-install-failure, health-timeout, service-launch-rejected, phase-verification-failed). Builder picks specific codes within the block and updates hands-off-lifecycle's README's error-code table as part of the clarification-class edits.

## 9. Approval ask (G3)

Approve this proposal to open brief-drafting. Specifically:

- Locked rulings in §2 as faithful to the conversation.
- The eighteen T-criteria in §4.
- The constraints in §5.
- The 60–95 min estimate with 120-min red line.
- Eve's inferences in §8.

On G3 approval, Eve drafts the brief; on G4 brief review, the build agent dispatches.
