# Core Development Convention — setup scripts self-retire on success

> **Work that happens once should leave no code behind that runs every session.** First-run setup completes its job, verifies the outcome, then removes itself — from the filesystem where the script lives, and from the hook registration that invoked it. Subsequent sessions never run first-run code because first-run code is not present to run. Future update-triggered setup ships its own self-removing script; setup logic is not reused session-after-session as check-and-skip scaffolding.

Rationale. Check-and-skip surfaces are an anti-pattern: they accumulate over time (each new setup concern adds another conditional), they add ongoing session-start cost for zero payoff once the one-time job is done, and they turn "is setup complete?" into a live-at-every-session state-machine query that the fourth lens was explicitly trying to retire. Self-retiring setup makes "setup is done" structural — the absence of the script is the proof, not a state flag the script consults.

Applied immediately to true-first-run (Phase 5 second component): the first-run shell script's last act before exit is to (a) write `.claude/settings.json` with the SessionStart hook pointing at the sealed supervisor path, (b) delete itself from the filesystem. Subsequent SessionStart fires invoke the supervisor directly; no first-run surface remains.

Design principle for future components: any setup code should answer the question *"how do I remove myself on success?"* as part of its scope, not as a maintenance afterthought.
