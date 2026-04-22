# Research Plan — Telegram Interface

**Status:** DRAFT — awaiting owner approval at G1.
**Authored by:** Eve. **Date:** 2026-04-22.
**Phase 5, third component.** Opens immediately after true-first-run seals. Builds on the four research lenses and the two Core Development Conventions in `FUTURE_IDEAS.md`.

---

## 1. Why this component

The user has stated unambiguously that Telegram should be the primary channel for pos-v2 conversation when available. Telegram is where notifications land, where escalations arrive, where the primary persona initiates unprompted conversation with the user about work in progress. In-session (terminal + Claude app) remains the fallback for when Telegram is unavailable or when the user is deliberately in a Claude Code session at their desk.

The current sealed state: no Telegram surface. Hands-off-lifecycle's loud-escalation protocol uses `OneOnOneChannel` from the primary-persona layer and `~/.pos/attention.md` as the durable unresolved-state mirror. The one-on-one channel is an abstraction; it does not have a concrete Telegram backing.

This component provides that backing. The Claude MCP Telegram channel plugin is the channel surface — pos-v2 does not build a custom bot, it configures and consumes the MCP plugin Anthropic ships.

## 2. Objective

When Telegram is configured and available, the primary-persona one-on-one channel routes through the Claude MCP Telegram plugin — bidirectional. The user sends a message from Telegram to the bot; the primary persona receives and responds via Telegram. The system's initiated messages (morning briefings, escalations, scope-completion notifications, proactive suggestions) route through Telegram by default. When Telegram is unavailable (MCP plugin disconnected, user has not yet configured, network unreachable, Telegram API rate-limited, etc.), fall back to in-session (Claude Code stdout / Claude app).

The setup experience honours the step-by-step-when-impossible convention: parts the system can do (reading the plugin's API, detecting availability, wiring `OneOnOneChannel`) are silent; parts that require the user (installing the Claude MCP Telegram plugin for Claude Code, authorising a bot, providing a bot token, messaging the bot once to register their user ID) are exact numbered instructions with expected time.

## 3. Scope

### 3.1 In scope

- **MCP plugin integration.** Consume the Claude MCP Telegram plugin as the channel surface. Detection of plugin presence; extraction of the tools the plugin exposes (send, reply, react, edit, etc.); wiring these into the primary-persona `OneOnOneChannel` abstraction such that an `on_one_message()` on that channel produces a Telegram message via the plugin.
- **Availability probe.** Continuous or at-send-time probe of Telegram availability. Success criteria: MCP plugin is loaded; the plugin reports connected; a round-trip test message succeeds. Failure modes enumerated and dispositioned.
- **Default routing.** When available, the primary-persona channel primary transport is Telegram. Eve speaks to the user via Telegram; the user speaks to Eve via Telegram. In-session surfaces continue to exist (the user may be actively in a Claude Code session) but are secondary unless Telegram is unavailable.
- **Fallback behaviour.** Clean fallback to in-session + `~/.pos/attention.md` when Telegram unavailable. No dropped messages; a message initiated during Telegram outage either queues-and-sends-on-recovery or surfaces in-session with an "and also delivered here because Telegram is down" note.
- **Setup walkthrough for session two.** On the session after true-first-run completes, the primary persona proactively offers Telegram setup. Numbered step-by-step instructions with expected time: install MCP plugin, create bot via BotFather, paste token where pos-v2 can read it, send a message to the bot to register user ID, confirm round-trip. Automated steps (writing the token to a pos-v2-managed config, detecting the MCP plugin presence, probing availability) happen silently around the user's steps. After successful setup, the walkthrough self-retires — the "offer Telegram setup" code path removes itself, per the self-retire-on-success convention.
- **Bidirectional messaging discipline.** Messages from the user arriving over Telegram are treated as a normal user-input to the primary persona. Messages the primary persona emits go to Telegram when that is the current primary channel.
- **Attachment support** if the MCP plugin supports it — images, files from the user to the persona and from the persona to the user.
- **Reaction + edit support** if the MCP plugin exposes them — per the MCP instructions Luke saw earlier in the session, reactions and edits are lightweight persona affordances.

### 3.2 Out of scope

- **Building a custom Telegram bot.** The MCP plugin is the surface, period. If the plugin is insufficient for a specific feature, halt-and-surface rather than bypass the plugin.
- **Telegram group-chat support.** pOS's primary-persona interaction is one-on-one by design (per the sealed one-on-one channel primitive). Group-chat deliveries are Tier-A external communications per the security rules and are not a pos-v2 default.
- **Other channels in this cycle.** Slack, Discord, SMS, email-as-channel — each would be its own component cycle. Telegram lands first because the user specifically asked for it and the MCP plugin exists.

## 4. Questions the research must answer

1. **Claude MCP Telegram plugin surface.** What tools does the plugin expose? What is its authorisation flow? What state does it persist (bot token, allowlisted user IDs, chat IDs)? What is the presence-detection signal pos-v2 uses to know the plugin is loaded? Is there a documented upper-bound on message rate or size? What happens when the plugin disconnects mid-session? Web search + consulting the plugin's documentation expected.
2. **OneOnOneChannel wiring.** The sealed one-on-one channel primitive lives in primary-persona-layer. What does its current surface look like in terms of transport-pluggability? Does it currently accept a transport adapter via dependency injection, or does it need to be consumed via a new adapter this component ships? (Reading primary-persona's sealed interface is the priority verification here.)
3. **Availability probe cadence and failure disposition.** Continuous probe (every N seconds) vs at-send-time probe vs hybrid. What counts as "Telegram unavailable" (plugin disconnected? network? rate-limited? user-blocked-the-bot?). For each named failure mode, fallback disposition.
4. **Message queuing during outage.** If Telegram is down when a message is emitted, does the message queue for later delivery, get duplicated to in-session, or get dropped? Queuing-for-delivery has a bounded-staging-size concern (reminiscent of memory-system staging). Duplicating to in-session has the "did the user see this twice?" concern. Dropping is forbidden by the loud-escalation-on-failure constraint.
5. **Session-two setup walkthrough.** How does the primary persona discover that Telegram is not yet configured? What's the trigger — first load of session two, a specific state query, a scheduled check? What does the exact numbered-instructions user experience look like? How does the walkthrough self-retire?
6. **Bidirectional message handling — session routing.** A message from the user arriving over Telegram mid-session (the user is at their desk in Claude Code AND sends a Telegram message) — where does it land? The primary persona's one-on-one channel has to handle both input sources coherently without message loss or duplication.
7. **Priority when user is actively in a Claude Code session.** The ruling was "default to Telegram when available, fall back to in-session when not." But is the user at their desk actively in Claude Code a case where in-session should win? Or does default-Telegram always hold? (The owner's ruling read as "always default Telegram when available." Verifying the interpretation.)
8. **Authorisation and identity.** The Claude MCP Telegram plugin probably has an allowlist mechanism (this session saw references to `access.json`). How does pos-v2 populate the owner's Telegram identity? What happens if a message arrives from an unauthorised Telegram account — silently dropped, surface to owner, active-decline?
9. **Privacy posture.** Every message sent over Telegram transits Anthropic infrastructure (via the MCP plugin) and Telegram's servers. The user has implicitly accepted this by configuring Telegram as the channel; but what does the confirmation-sentence or consent-moment during setup surface about this? Is any content-sensitivity gate warranted before certain classes of message route over Telegram vs in-session?
10. **Sealed-component amendments required.** Does this component require amending primary-persona-layer (for channel wiring)? Or can the `OneOnOneChannel` abstraction be consumed via a new adapter without amendment? Each amendment surfaced as a halt-signal.

## 5. Constraints the research must respect

- **Use the Claude MCP Telegram plugin** as the channel surface. Do not build a custom Telegram bot. If the plugin is insufficient for a needed feature, halt-and-surface.
- **Default to Telegram when available.** Owner ruling 2026-04-22 07:47.
- **In-session is the fallback**, not a parallel first-class transport.
- **Step-by-step when the system cannot act.** The Core Development Convention governs the setup walkthrough shape.
- **Self-retire on success.** The setup walkthrough removes itself on confirmed round-trip.
- **No sealed-component behavioural amendments without surfacing.** Primary-persona-layer is sealed; if this component requires amending it, halt-and-surface.
- **Loud escalation on failure.** Dropped messages are forbidden.
- **One-on-one channel only.** No group-chat deliveries.
- **Python 3.13; pos-v2 branch.** Permitted deps as established.
- **Halt on deviation.**

## 6. Deliverable — what the research document must contain

A markdown document at `components/telegram-interface/research.md` with:

1. **Survey of existing patterns** — how adjacent systems handle Telegram-as-primary-channel (Home Assistant's Telegram notifier, Grafana alerts-via-Telegram, personal-assistant bots in the community).
2. **Claude MCP Telegram plugin surface** — every tool the plugin exposes, its authorisation flow, its state, its failure modes, its documented limits.
3. **OneOnOneChannel wiring strategy** — adapter-pattern proposal, whether primary-persona-layer requires amendment, how state flows between the sealed abstraction and this component.
4. **Availability probe + fallback disposition** — per-failure-mode catalogue.
5. **Message queuing during outage** — design choice (queue / duplicate / escalate) with rationale.
6. **Session-two setup walkthrough design** — user-facing flow, exact numbered instructions sketch, self-retire mechanics.
7. **Bidirectional message routing model** — how Telegram-arriving and in-session-arriving messages compose in the same logical one-on-one channel.
8. **Priority and routing under concurrent surfaces** — when user is in Claude Code actively AND Telegram is available, where does Eve speak.
9. **Authorisation and identity model** — MCP plugin allowlist population, handling unauthorised senders.
10. **Privacy posture + consent surfacing** — what the setup walkthrough tells the user about data transit.
11. **Sealed-component amendment inventory** — each amendment named as halt-signal with named failure mode.
12. **Complexity estimate** — AI-time in calendar minutes; honest calibration.
13. **Prototyping priorities** — things only a live prototype with the MCP plugin installed can answer (plugin tool names, state file location, auth handshake, rate limits).

## 7. Gate structure

Four gates consistent with recent practice:

- **G1** — this research plan → owner approves.
- **G2** — research doc → owner rules dispositions and any amendment cases.
- **G3** — proposal → owner approves scope and acceptance criteria.
- **G4** — brief → owner approves operational instruction; build dispatches.

## 8. Execution note

On G1 approval, research agent dispatches to read the Claude MCP Telegram plugin docs, inspect primary-persona-layer's sealed surface, and produce the research document. Agent is read-only against pos-v2; sealed-component amendment cases are halt-signals surfaced during research, not improvised around.

---

## 9. Awaiting owner's approval

- Approve as written → research dispatch.
- Approve with changes → revise and resubmit.
- Reject → rework.
