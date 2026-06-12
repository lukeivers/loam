# Claude capability map for loam — INDEX (demoted surface)

> **This file is an index/redirect, not a reference.** It was demoted in
> place on 2026-06-11 (claude-leverage-program Slice 1, D-CLP.5 —
> master-locked; plan: `docs/plans/claude-leverage-program-s1-currency.md`).
> **The canonical capability-reference surface is
> [`docs/capability-corpus/`](capability-corpus/AUTHORING.md)** — exactly
> one canonical surface exists; this file carries no independently
> maintained capability claims.

## Why this file was demoted

The previous content was a 1,038-line hand-authored snapshot dated
2026-04-23. It went seven weeks stale and factually wrong on a
load-bearing claim (it asserted a no-recursion limit for sub-agents;
Claude Code 2.1.172 ships sub-agent nesting to 5 levels deep —
changelog-verified live 2026-06-11). Two independently maintained
reference surfaces (this snapshot + the capability corpus) drifting
apart is exactly how that failure happened; the demotion leaves one.
The full historical snapshot remains recoverable from git history
(last full version at commit `6ea2e6b5`).

The corpus is kept current by `framework/tools/capability-refresh/`
(deterministic projection from canonical upstreams on locked cadence
classes — see that component's README for the refresh contract and
activation).

## Where to look instead

| Topic (old snapshot section) | Canonical surface now |
|---|---|
| Claude Code CLI — slash commands, hook events, settings.json, CLI flags, headless mode (§1) | Corpus: [`capability-corpus/claude-code/hooks.md`](capability-corpus/claude-code/hooks.md); upstream: <https://code.claude.com/docs/en/hooks>, <https://code.claude.com/docs/en/cli-reference>, <https://code.claude.com/docs/en/interactive-mode> |
| Claude Agent SDK (§2) | Upstream: <https://code.claude.com/docs/en/sdk/sdk-overview> |
| Anthropic API — Messages, tool use, thinking, caching, batches, citations, files (§3) | The `claude-api` skill (in-session reference); upstream: <https://docs.claude.com/en/api> |
| Model Context Protocol (§4) | Upstream: <https://code.claude.com/docs/en/mcp>, <https://modelcontextprotocol.io> |
| Plugin system (§5) | Upstream: <https://code.claude.com/docs/en/plugins> |
| Skills (§6) | Upstream: <https://code.claude.com/docs/en/skills> |
| Agent tool / subagents (§7) | Corpus: [`capability-corpus/claude-code/background-agents.md`](capability-corpus/claude-code/background-agents.md); upstream: <https://code.claude.com/docs/en/sub-agents> + the changelog (release truth): <https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md> |
| Background-task primitives (§8) | Corpus: [`capability-corpus/claude-code/background-agents.md`](capability-corpus/claude-code/background-agents.md) |
| Session persistence (§9) | Upstream: <https://code.claude.com/docs/en/interactive-mode> |
| Recurring execution — `/loop`, `/schedule` | Corpus: [`capability-corpus/claude-code/loop.md`](capability-corpus/claude-code/loop.md), [`capability-corpus/claude-code/schedule.md`](capability-corpus/claude-code/schedule.md) |
| loam harness primitives | Corpus: [`capability-corpus/harness/scope-of-work.md`](capability-corpus/harness/scope-of-work.md) + per-component `framework/<comp>/docs/` |
| Best-practice patterns (when/how, anti-patterns) | Corpus Class B: [`capability-corpus/best-practice/`](capability-corpus/best-practice/) |

## How the canonical surface stays current

- **Class A entries** (`capability-corpus/claude-code/`,
  `capability-corpus/harness/`) carry a `## Source` block with
  `source_url` + `source_fetch_ts`; `framework/tools/capability-refresh/`
  re-projects them from those upstreams on the locked cadences
  (high-velocity daily, long-form weekly) and marks an entry stale when
  its source fetch fails — a stale entry is never silently presented as
  current.
- **New claims, removals, and `[user-intent phrasings]` overlay changes
  never auto-land** — they surface as pending-deltas under
  `capability-corpus/pending-deltas/` for review.
- Anything load-bearing should be read from the corpus entry (check its
  `source_fetch_ts`) or re-fetched live from the upstream URL — never
  from a stale snapshot.
