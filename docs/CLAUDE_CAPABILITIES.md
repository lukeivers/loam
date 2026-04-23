# Claude capability map for pOS v2

- **Snapshot date:** 2026-04-23
- **Version:** 0.1 (skeleton — being filled incrementally)
- **Stewarded by:** primary persona; future refresh automation per `docs/rebuild/FUTURE_IDEAS.md` Idea 1 Step 4
- **Refresh cadence (target):** daily, budget-permitting, once Step 4 lands
- **Scope:** the Claude-attached capability surface available to pOS v2 feature research — Claude Code CLI, Claude Agent SDK, Anthropic API, MCP, plugins, skills, subagents, background tasks, session persistence

## Purpose

This map is the reference an AI agent (or a human author) consults during feature research for pOS v2 to answer Lens 1 — *"what Claude capability does this lean on or extend?"* — without having to re-discover the surface. The file is not a tutorial and not an API reference; it is a curated map that names each capability, says how it composes with pOS v2's existing sealed components, flags the known pitfalls, and points at the end-user configuration surface.

How to use it: open this file at the start of any feature research. For each capability that might plausibly back the feature, read the four subsections (one-line description, pos-v2 composition, pitfalls, end-user configuration). If none of the capabilities fit, that is itself a finding — write it up in the research plan so the Lens 1 gate (once enforcement lands in Idea 1 Step 3) can record the negative answer.

The map is deliberately a **2026-04-23 snapshot**. Claude's surface drifts weekly. Sections flagged *Volatile* are particularly likely to be stale by the time you read them; the refresh automation in Idea 1 Step 4 will keep the snapshot current once it ships. Until then, cross-check anything load-bearing against the cited source URL before you build on it.

## How entries are structured

Every capability entry has four parts:

1. **What it does** — one line.
2. **How it composes with pos-v2** — which sealed components already use it or could latently compose with it. Citations are to `docs/rebuild/components/<name>/` narratives where relevant.
3. **Pitfalls** — known footguns, version skew risks, rate limits, silent-failure modes.
4. **End-user configuration surface** — where a user turns the capability on, off, or tunes it. Typically a file path, a CLI flag, an env var, or a settings key.

Where sources are thin, the entry ends with `_Unclear from available sources as of 2026-04-23; flagged for Idea 1 Step 4 refresh._`

---

## Table of contents

1. [Claude Code CLI](#1-claude-code-cli)
2. [Claude Agent SDK](#2-claude-agent-sdk)
3. [Anthropic API (Messages + adjacent)](#3-anthropic-api-messages--adjacent)
4. [Model Context Protocol (MCP)](#4-model-context-protocol-mcp)
5. [Plugin system](#5-plugin-system)
6. [Skills](#6-skills)
7. [Agent tool and subagents](#7-agent-tool-and-subagents)
8. [Background-task primitives](#8-background-task-primitives)
9. [Session persistence](#9-session-persistence)
10. [Cross-capability notes](#10-cross-capability-notes)

---

## 1. Claude Code CLI

<!-- PLACEHOLDER -->

---

## 2. Claude Agent SDK

<!-- PLACEHOLDER -->

---

## 3. Anthropic API (Messages + adjacent)

<!-- PLACEHOLDER -->

---

## 4. Model Context Protocol (MCP)

<!-- PLACEHOLDER -->

---

## 5. Plugin system

<!-- PLACEHOLDER -->

---

## 6. Skills

<!-- PLACEHOLDER -->

---

## 7. Agent tool and subagents

<!-- PLACEHOLDER -->

---

## 8. Background-task primitives

<!-- PLACEHOLDER -->

---

## 9. Session persistence

<!-- PLACEHOLDER -->

---

## 10. Cross-capability notes

<!-- PLACEHOLDER -->

---

## Source log

Every non-trivial claim in this file is traceable to an entry below. URLs recorded with fetch date; claude-code-guide subagent dispatch count recorded at end.

- _(populated as sections land)_
