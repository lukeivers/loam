# Research Plan — True First-Run

**Status:** DRAFT — awaiting owner approval at G1.
**Authored by:** Eve. **Date:** 2026-04-22.
**Phase 5, second component.** Sister to `hands-off-lifecycle`; closes the gap between "foundation-complete" and "clone-and-open-a-session-and-it-just-works."

---

## 1. Why this component

`hands-off-lifecycle` (sealed 2026-04-22 06:53) delivered exactly the scope it was given: a Claude Code session-start hook, supervisor, durable staging, reconcile drain, first-run YAML scaffold, launchd/systemd-user plist installation, loud escalation. When Eve surfaced the workspace-setup steps immediately after that seal, the honest inspection of a freshly-cloned `pos-v2` workspace revealed four genuine gaps the component did not close:

1. No `.claude/settings.json` in the workspace root (hook-registration surface Claude Code reads is absent).
2. The shipped hook fragment references `${POS_V2_REPO}/.venv/bin/python` — a top-level virtualenv that does not exist in a fresh clone.
3. No Python dependencies are pre-installed. Each component's `requirements.txt` is declared; none is installed on clone.
4. The orchestrator launchd plist ships as a `.tmpl` template requiring substitution of at least `${POS_V2_REPO}` before it is a valid plist.

The owner's ruling at this surfacing, 2026-04-22 07:15 CDT: *"option b. i want to have the authentic clean start experience."* — meaning the first-run automation must be real, not patched manually by Eve on one owner's machine. Proper component cycle.

The pOS-v2 value proposition depends on this. The fourth lens (*zero manual lifecycle management, ever*, and by extension zero manual setup) cannot be honoured if the authentic clean-start experience requires four setup steps the user reads and performs. Non-technical users do not have a `.venv`, a `pip`, or an intuition for launchd plist templating; the claim that pos-v2 runnable by them is only true if this component lands.

## 2. Objective

When a user clones pos-v2 into a fresh directory and opens a Claude Code session in that directory, the full system comes up automatically. The session-start hook fires, completes all setup (venv creation, dependency install, `.claude/settings.json` authorship, plist-template substitution-and-install, service launch), and reports in one confirmation sentence. Subsequent session opens detect completed setup and do nothing visible.

The user has `git clone`'d, `cd`'d, and run `claude`. That is the only manual sequence.

## 3. Scope

### 3.1 In scope

- **Claude Code `settings.json` authorship on first run.** Writing `~/pos2/.claude/settings.json` (or whatever the user's chosen workspace root name is) with the SessionStart hook stanza, correct path substitution for `${POS_V2_REPO}` resolved from the actual workspace root, and any other Claude Code configuration pos-v2 wants enabled by default.
- **Top-level virtualenv creation.** Creating `<workspace-root>/.venv/` for the shared-venv components with the declared Python version.
- **Per-component virtualenv creation where applicable.** Memory-system has its own canonical venv (Graphiti deps are segregated). Other components may grow their own over time; the component must handle the pattern generally rather than case-by-case for memory-system.
- **Dependency installation.** Running `pip install -r requirements.txt` into the right venv for each component that has a `requirements.txt`.
- **Plist-template substitution.** Resolving `${POS_V2_REPO}` and any other variables in `.tmpl` files; writing the substituted plist to `~/Library/LaunchAgents/` (macOS) or equivalent on Linux.
- **Chicken-and-egg protocol.** The hand-off-lifecycle hook currently references `${POS_V2_REPO}/.venv/bin/python` — which does not exist on first run. First-run has to happen BEFORE that hook can possibly fire successfully. This component must reconcile: either bootstrap the setup from something that does not require a venv (shell script, POSIX-only tooling), or restructure the hook so the first-run-setup path is shell-based and the ongoing supervisory path is venv-based once the venv exists.
- **Idempotent re-run.** If first-run was interrupted (network failure during `pip install`, plist install crashed, etc.), the next session-start detects partial state and completes it, not blindly re-runs.
- **One confirmation sentence.** Same pattern as hands-off-lifecycle's §Q7 — report completion in plain language, once, and otherwise silent on subsequent opens.
- **Loud escalation on irrecoverable failure.** No Python installed on the user's machine? `pip install` fails for a dependency that cannot resolve? `launchctl bootstrap` refused? Surface with the named diagnostic, do not silently degrade.

### 3.2 Out of scope

- Installing Python itself if the user does not have it. First-run can detect and refuse with a clear "install Python 3.13+ and retry" message, but cannot install the interpreter for them.
- Installing `git`, `claude` (Claude Code CLI), or other prerequisites. Same posture — detect and refuse with clear messaging.
- Authoring user-specific persona files, memory content, or workspace-specific config beyond the framework-defaults hands-off-lifecycle already covers.

## 4. The central design tension — first-run bootstrap without a venv

This is the crux. The SessionStart hook currently invokes a Python script. On first-run the venv that script runs in does not exist. Three candidate shapes:

- **A — shell-first bootstrap.** The hook invokes a POSIX shell script that handles venv creation, dependency install, plist substitution, and then (optionally) hands off to the Python helper for any work that benefits from being in Python. The shell script must succeed on macOS and on a common Linux baseline without external deps.
- **B — Python with a bootstrap venv inline.** The hook invokes a Python script using the system Python (assumed to exist by pre-check), which creates the workspace's `.venv/`, installs deps into it, then re-exec's itself inside the new venv for anything that needs the workspace's package set.
- **C — two-phase hook.** The SessionStart hook detects first-run state via a cheap file check; on first-run it runs a dedicated first-run script; on subsequent runs it runs the ongoing supervisor. Two distinct code paths, chosen by state.

Eve's lean pending research: **shape A** (shell-first). Shell avoids the Python version-mismatch class of bug (what if the user has 3.10 installed, not 3.13?), avoids the re-exec complexity of shape B, and cleanly separates first-run concerns from the ongoing-operation helper. Shape C is right philosophically but adds branching inside what should be a simple hook; shape A collapses to two scripts (one-shot first-run shell, ongoing Python supervisor) without needing state-branching inside either.

The research's central question is which of these shapes holds under closer reading.

## 5. Questions the research must answer

1. **Bootstrap shape** — A, B, or C. Which is cleanest, which fails in practice, which is most debuggable on user machines we will not have shell access to.
2. **System-Python detection and version requirement.** What version does pos-v2 require (3.13 per recent convention)? How does the hook detect a compatible Python and what does it say when the user lacks one? What macOS / Linux distributions ship 3.13 by default today and what fraction of likely early users have it installed?
3. **venv creation mechanics.** Top-level `<root>/.venv/` vs `uv` vs `virtualenv` vs `python -m venv`. What Python-ecosystem conventions are least surprising to someone who is not a Python developer.
4. **Per-component venv handling.** Memory-system has its own. Which components currently or likely future have their own. How does the first-run script discover "this component wants its own venv" vs "this component uses the shared venv" — manifest declaration in the component's `requirements.txt`? A top-level `pos-v2.yaml` inventory? A convention (component has a `.needs-venv` marker file)?
5. **Dependency-install error handling.** Network failure during `pip install`. A dependency that cannot resolve. A dependency that installs but fails its post-install. Each needs a named failure mode and either retry or escalate behaviour.
6. **Claude Code settings.json authorship.** Does the component write `.claude/settings.json` from scratch, or merge into an existing file? What if the user already has `.claude/settings.json` in their workspace with their own hooks? What Claude Code conventions exist for plugin-shipped hook registration.
7. **Plist-template substitution mechanics.** Variables to substitute (beyond `${POS_V2_REPO}`). File destinations. Cleanup on re-run. Conflict with any pre-existing plist at the same paths.
8. **Chicken-and-egg protocol.** The hands-off-lifecycle hook references the venv's Python. First-run creates the venv. Which of (a) the hook is changed to reference a venv-agnostic bootstrap; (b) first-run happens before the hook's ongoing path; (c) the hook's fragment itself changes at first-run — is correct. Note: if the answer requires amending hands-off-lifecycle's hook fragment, that is amendment 5 territory (Eve did not anticipate a 5th amendment, and the hands-off-lifecycle seal should not reopen lightly — surface this explicitly if it turns out to be required).
9. **Idempotent re-run detection.** What file or state marker tells the script "first-run is complete vs. in-progress vs. not started." What happens on partial completion from an interrupted prior run.
10. **Platform coverage.** macOS is primary. Linux (with systemd-user) is secondary per hands-off-lifecycle ruling. Windows is explicitly out. Does first-run scope match that coverage?
11. **Sealed-component amendments required.** Does this component require amending hands-off-lifecycle (the hook fragment), workspace-bootstrap (the first-run phase), or any other sealed component? Each amendment surfaced as a halt-signal candidate.

## 6. Constraints the research must respect

- **Python 3.13 target.** pos-v2 conventions.
- **No new heavyweight deps for bootstrap.** Shell scripts use POSIX-baseline tools. Python bootstrap uses stdlib plus `venv`. No `uv`, `poetry`, `pipenv` dependency for first-run; stdlib venv is enough.
- **Macro constraint: memory is mandatory.** The memory sidecar must come up as part of first-run, which means its own venv creation + dependency install + plist substitution-and-install happen in first-run, not later.
- **Silent-stay-degraded is forbidden** (fourth lens). First-run that half-completes and leaves the session in a broken state fails the lens.
- **Zero manual lifecycle management, ever.** The component must deliver the "clone, cd, claude" promise without a fifth user step.
- **No amendments to sealed components without surfacing.** hands-off-lifecycle's hook-fragment change — if required — is a halt-signal amendment case.
- **Claude Code hook primitives only.** The first-run path uses `SessionStart`; if Claude Code's hook surface does not support what this component needs, halt and surface rather than invent a workaround.
- **Halt on deviation.**

## 7. Deliverable — what the research document must contain

A markdown document at `components/true-first-run/research.md` with:

1. **Survey of existing patterns** — how other developer tools handle first-run setup (Homebrew first-run, pyenv init, Docker Desktop, VS Code extension activation, pre-commit hook install-on-first-run, etc.).
2. **Recommended bootstrap shape** — A / B / C, with rationale and failure-mode catalogue.
3. **System-Python detection + version gate** — concrete check and failure-mode messaging.
4. **Per-component venv discovery protocol** — the manifest / marker / convention that tells first-run "this component has its own venv."
5. **Dependency-install error-handling catalogue** — each named failure mode + disposition.
6. **`.claude/settings.json` authorship strategy** — from-scratch vs merge, Claude Code convention check.
7. **Plist-template substitution spec** — variables, destinations, conflict handling, cleanup.
8. **Chicken-and-egg resolution** — whether hands-off-lifecycle amendment is required.
9. **Idempotent re-run state model** — markers, partial-completion detection, resume-or-restart decision.
10. **Sealed-component amendment inventory** — each amendment named as halt-signal.
11. **Complexity estimate** — AI-time calibrated honestly. Probably comparable to hands-off-lifecycle's build (170–220 min wall-clock) given the scope breadth.
12. **Prototyping priorities** — things only a live prototype can answer (interaction with Claude Code's settings.json merge behaviour, etc.).

## 8. Gate structure

Four gates consistent with recent rebuild practice:

- **G1** — this research plan → owner approves.
- **G2** — research doc → owner approves dispositions, rules on any amendment cases.
- **G3** — proposal → owner approves scope and acceptance criteria.
- **G4** — brief → owner approves operational instruction; build dispatches.

## 9. Execution note

On G1 approval, Eve dispatches the research agent to `components/true-first-run/research.md`. The agent is read-only against pos-v2; any sealed-component amendment case is a halt-signal that surfaces during research, not a change made during research.

---

## 10. Awaiting owner's approval

- Approve as written → research dispatch.
- Approve with changes → revise and resubmit.
- Reject → rework.
