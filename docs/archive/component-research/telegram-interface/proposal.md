# Proposal — Telegram Interface

**Status:** DRAFT — awaiting owner's G3 approval.
**Authored by:** Eve. **Date:** 2026-04-22.
**Research baseline:** `research.md` at this component's directory.

---

## 1. Objective

When Telegram is configured and available, the primary-persona one-on-one channel defaults to Telegram — bidirectional — via the Anthropic-shipped Claude MCP Telegram plugin (`telegram@claude-plugins-official`). When Telegram is unavailable (plugin not loaded, `--channels` flag absent, network down, 401 on token rotation, etc.), cleanly fall back to in-session + `~/.pos/attention.md`. The session-two setup walkthrough produces exact numbered step-by-step instructions for the user-dependent steps, automates everything it can, and self-retires on confirmed round-trip. Additional authorised identities (e.g. owner's wife) compose cleanly, addressed as distinct users with reduced-bound authority defaults.

## 2. Owner rulings (locked inputs)

Rulings received across two approval turns, 2026-04-22.

### 2.1 The seven G2 questions

| Q | Ruling |
|---|---|
| Q1 — Walkthrough-offer cadence after deferral | **Re-offer on explicit ask only, never proactively after the first decline.** `~/.pos/telegram-setup-offered` marker persists; persona reads it and remains silent on the subject until asked. |
| Q2 — Briefing routing confirmation | **Default-Telegram applies to all persona-initiated surfaces when available** — briefings, recaps, escalations, proactive suggestions. User-initiated in-session conversation is the only exception, because that is where the user put the question. |
| Q3 — `attention.md` + in-session duplication during outage | **Both, with clear framing.** In-session message prefixed with "Telegram is unavailable — delivered here instead"; `attention.md` entry preserved for the out-of-session case. |
| Q4 — Prompt-injection posture for destructive-ops from Telegram | **Telegram-originated requests get one extra explicit-confirmation step for any Tier-A/B action** that would normally execute autonomously for in-session requests. In-session destructive ops retain existing safety-gate discipline. |
| Q5 — Token-rotation detection proactivity | **Loud-escalation on first 401**, no proactive rotation probe. Polling tax for a rare event isn't worth paying. |
| Q6 — Single- or multi-user allowlist | **Multi-entry allowlist with hard-assert at plugin layer.** Owner populated at setup; additional authorised identities extensible via owner-mediated flow. Silent drop on unauthorised senders (plugin rejection is the security boundary). See §2.2 for the multi-identity model. |
| Q7 — Direct-Bot-API fallback when session lacks `--channels` flag | **In-session-only for sessions without `--channels`.** Proactive-initiated (out-of-session) messages still use direct Bot API — there is no session context there anyway. |

### 2.2 The two multi-identity ratifications

| Ratification | Ruling |
|---|---|
| Register-additional-identity flow | **Owner-mediated.** Owner (inside a Claude Code session) asks Eve "add my wife to Telegram" or equivalent; Eve produces step-by-step instructions for the wife (DM the bot, send pairing code), owner confirms the pairing, the allowlist appends. Prevents the self-registration-spoofing attack surface. |
| Per-identity authority bounds | **Reduced-bound default for non-owner identities.** Non-owner authorised users can converse with Eve, read memory Eve is willing to share, cannot authorise Tier-A/B actions on the owner's behalf. Owner retains full authority. Per-identity bounds are extensible later (e.g. wife gets full authority on household-domain, but not business-domain) but the v1 default is a flat reduced-bound. |

## 3. Design shape (summary — research.md is the detail)

### 3.1 Transport composition

A new package `telegram-interface/` on pos-v2. The package ships a `TelegramChannelAdapter` consumed by the sealed primary-persona `OneOnOneChannel` via adapter-pattern dependency injection — the sealed component's `send: Callable` parameter and `ChannelKind.personal_telegram` enum value already accept the wire-up. **Zero sealed-component amendments.**

Three transport paths inside the adapter:

- **In-session via MCP plugin.** When a Claude Code session is active with `--channels plugin:telegram@claude-plugins-official`, Eve's outbound messages invoke the plugin's `reply` tool with the relevant `chat_id`. Inbound `<channel source="telegram" …>` tags in the session input stream route into the persona's user-input surface.
- **Out-of-session via direct Bot API.** Background workers (scheduled tasks, supervisor escalations) cannot call MCP tools. They send via direct HTTPS to Telegram's Bot API using the token at `~/.claude/channels/telegram/.env`, honouring the same allowlist.
- **Fallback — in-session + `attention.md` when Telegram is unavailable.** Both surfaces receive the message, with the framing preamble naming the degraded state.

### 3.2 Availability probe + fallback disposition

Hybrid model from research §2.4:

- In-memory flag updated by a background `getMe` probe every 60s.
- At-send-time check before each outbound (cached-flag, no extra API call).
- On send-failure, aggressive 5s retry probes for 60s before declaring outage.
- On outage declared, route to fallback + loud-escalation one-time notification.
- On recovery detected, resume normal routing; short "Telegram recovered" in-session notice if the user is in a Claude Code session.

Nine named failure classes (research §2.4), each with disposition documented.

### 3.3 Session-two setup walkthrough

Six numbered steps per research §2.5, ~5 minutes total user time:

1. `/plugin install` + `/reload-plugins` — automated via step-by-step instructions for the user portion (one command).
2. BotFather → token creation — step-by-step user instructions; expected 2 minutes.
3. Restart with `--channels` flag — instructions include the exact flag; expected 30s.
4. DM the bot, paste the pairing code Eve emits — expected 1 minute.
5. Silent: Eve writes `policy` with allowlist populated.
6. Silent: Eve runs a round-trip verify, writes `~/.pos/telegram-setup-offered` marker, self-retires the "offer setup" code path.

**Self-retire mechanic:** the "offer Telegram setup" code path in the primary persona's session-two flow checks for the marker file and does nothing when it exists. The code stays for the case where a fresh workspace clones post-plugin-install, but its activation is absent-marker-gated and the marker only persists after successful setup.

### 3.4 Multi-identity model

- `access.json` allowlist entries carry `user_id`, `display_name`, `relationship` (e.g. `owner`, `spouse`, `colleague`), `authority_class` (e.g. `owner`, `reduced_bound`), `added_at`.
- Inbound message routing reads the `user` attribute from the `<channel>` tag, looks up the identity in the allowlist, injects the identity's display-name + relationship + authority-class into the persona's input context.
- Persona responds addressed to the specific identity, using memory and authority consistent with their bound.
- Tier-A/B actions requested by a non-owner identity refuse with a clear message; owner is notified via their own primary channel.

### 3.5 Destructive-op confirmation escalation

For Telegram-originated Tier-A/B requests:

- In-session-originated identical request would execute per the existing safety-layer policy.
- Telegram-originated request routes through an extra explicit-confirmation step — a reply from Eve naming the action and asking a clear yes/no, which the user must answer from Telegram before the action proceeds.
- Confirmation timeout (30 minutes default, config) → request refused + logged.

### 3.6 State and observability

- State file: `~/.claude/channels/telegram/access.json` (plugin's canonical state store, extended with the authority-class fields above).
- OTel emission on outbound, inbound, fallback-triggered, setup-walkthrough-step, allowlist-modification events.
- Supervisor integration: the availability flag is exposed as part of the primary-persona layer's channel-readiness query surface.

## 4. Acceptance criteria (ODD — 22 objectives)

### 4.1 Setup walkthrough (TG1–TG6)

- **TG1.** On session two after a true-first-run seal, the primary persona proactively offers Telegram setup with the six-step numbered instruction sequence. The offer text includes expected-time estimates per step.
- **TG2.** User declines → `~/.pos/telegram-setup-offered-declined` marker written; persona does not proactively raise Telegram setup again for the life of the workspace. Eve re-offers only on explicit user ask.
- **TG3.** User completes the pairing flow → pos-v2 runs a silent round-trip verify (sends a test message, receives the acknowledgement), writes `~/.pos/telegram-setup-offered` success marker, self-retires the offer-setup code path (the marker check short-circuits the offer logic).
- **TG4.** On a fresh clone where the plugin is already installed at the user's Claude Code config level, first-run detects plugin-available and emits the setup offer immediately in session two; on a workspace where the plugin is not installed, setup offer starts at step 1 (plugin install).
- **TG5.** User prior `settings.json` is preserved throughout setup — only the `channels` flag and the Telegram-specific additions are merged.
- **TG6.** Setup failure at any step surfaces a named diagnostic with remediation instructions; does not write a success marker; next session retry resumes from the failed step.

### 4.2 Transport routing (TG7–TG11)

- **TG7.** With Telegram available and the session flagged `--channels`, the primary persona's outbound `send` invokes the MCP plugin's `reply` tool; the user receives the message on Telegram.
- **TG8.** With Telegram available but the session not flagged with `--channels`, in-session responses route to in-session; out-of-session proactive messages route to direct Bot API.
- **TG9.** With Telegram unavailable (any of the nine named failure classes), outbound messages route to `attention.md` + in-session (during active session); framing preamble names the degraded state.
- **TG10.** Inbound `<channel source="telegram" …>` tag in the session input is normalised and passed to the primary persona's user-input surface with the `user` attribute's allowlist lookup result as context.
- **TG11.** On recovery from Telegram outage, the adapter resumes normal routing without restart; active session receives a short "Telegram recovered" notice; background workers' next outbound message uses the recovered channel.

### 4.3 Availability probe (TG12–TG13)

- **TG12.** Background probe fires every 60s, invokes `getMe`, updates the in-memory flag. Probe cost is OTel-emitted.
- **TG13.** On send-failure, adapter enters 5s-retry mode for 60s before declaring outage. OTel spans emit for each retry, outage-declaration, and recovery-declaration.

### 4.4 Multi-identity allowlist (TG14–TG17)

- **TG14.** Owner-initiated identity addition flow: owner asks Eve in-session to add a new identity; Eve produces step-by-step instructions for the new user; owner confirms in-session when the new user reports ready; pairing completes and the allowlist appends with `relationship` and `authority_class` populated by owner at add-time.
- **TG15.** Inbound messages from an allowlisted non-owner identity route to the persona with the identity's display-name and reduced-bound authority class in context. Responses are addressed to the specific identity.
- **TG16.** Tier-A/B action request from a non-owner identity is refused with a clear message. Owner is notified via their own primary channel of the refused request + identity + requested action.
- **TG17.** Unauthorised Telegram sender messages the bot → plugin rejects at the allowlist layer → pos-v2 receives nothing → no notification. No storm from discovery spam.

### 4.5 Destructive-op confirmation for Telegram requests (TG18–TG19)

- **TG18.** A Telegram-originated request that would normally execute autonomously for an in-session user (passes safety-layer dangerous-op gate) routes through an extra explicit-confirmation step before execution. The confirmation question is addressed to the same Telegram identity who originated the request.
- **TG19.** Confirmation timeout (30 minutes default) refuses the request with a logged event and a short Telegram notification to the originator. Owner is notified of the refused-by-timeout outcome.

### 4.6 Token rotation + failure modes (TG20–TG22)

- **TG20.** On 401 (token no longer valid), loud-escalation fires to the owner's primary channel (Telegram if another valid path exists, otherwise in-session + `attention.md`) with step-by-step re-pairing instructions. Adapter routes to fallback for all subsequent messages until the token is updated.
- **TG21.** On 429 (rate-limited), adapter respects the Retry-After header, queues pending messages briefly, loud-escalates if the rate-limit persists past a configurable bound (default 5 minutes).
- **TG22.** On 403 (user blocked the bot), the specific identity's allowlist entry is flagged `blocked_at`; messages to that identity attempt no further sends until the owner re-adds or the flag is cleared.

## 5. Constraints

- **Use the Claude MCP Telegram plugin** (`telegram@claude-plugins-official`). No custom bot. Plugin insufficiency → halt-and-surface.
- **Default-on when available.** Owner ruling.
- **In-session + `attention.md` as fallback.** No dropped messages.
- **Step-by-step-when-impossible** for the setup walkthrough. Self-retire on success.
- **Zero sealed-component amendments.** Primary-persona `OneOnOneChannel` consumed via adapter-pattern; `ChannelKind.personal_telegram` already exists.
- **Multi-identity allowlist with owner-mediated addition.** Non-owner identities default to reduced-bound authority.
- **Extra confirmation for Telegram-originated Tier-A/B ops.**
- **Loud-escalation on failure.** No silent-continue.
- **No group-chat support.** One-on-one is structural.
- **Python 3.13; pos-v2 branch.** Permitted deps as established.
- **Error codes in `-32100..-32109`** reserved to this component. No overlap with prior ranges.
- **Halt on deviation.**

## 6. File layout and phase shape

Builder's call. The component ships as a new `telegram-interface/` package at pos-v2 root. Consumes the sealed primary-persona `OneOnOneChannel` and the plugin's tools; exposes the `TelegramChannelAdapter` for workspace-bootstrap's registration path.

## 7. Build estimate

**54–85 AI-minutes wall-clock. Red line at 90.**

Honest calibration from research §12. Smaller than prior Phase 5 components because: no sealed-component amendments, plugin handles transport heavy-lifting, adapter-pattern consumption is well-established on pos-v2 through prior components. Out-of-session direct-Bot-API path and multi-identity acl are the two areas where scope can swell — watch for those.

Halt triggers:
- Past 90 minutes without the 22 TG-criteria green — halt and report partial progress.
- Any sealed-component amendment surfacing — halt.
- Any regression on an unamended sealed component — halt.
- MCP plugin behaviour materially diverging from research §2.2 — halt and surface.

## 8. Eve's inferences — flagged for the builder to challenge

1. **Error-code range `-32100..-32109`.** Eve's placeholder; contingent on no prior allocation in that block. Builder verifies against the allocated-ranges catalogue.
2. **30-minute confirmation timeout** for Telegram Tier-A/B. Owner did not specify; Eve's lean. Challenge if a different timeout serves better.
3. **5-minute rate-limit loud-escalation bound.** Eve's lean. Challenge if 10 or 15 minutes is more appropriate given Telegram's typical rate-limit dynamics.
4. **Authority-class enum values `owner` / `reduced_bound`.** Eve's lean for v1. Future per-domain authority (wife gets full-authority-on-household, reduced-on-business) is explicitly out-of-scope for v1 — challenge if v1 should open a richer enum immediately.
5. **`~/.pos/telegram-setup-offered-declined` as the decline-marker pattern.** Eve's lean. Builder may refine.
6. **Owner-mediated add-identity flow** running entirely in-session. Alternative: part of it could happen over Telegram (owner types "add a new user" in Telegram, Eve guides; owner confirms in Telegram). Eve's lean is in-session-mediated because the owner's ability to *authorise* adds is itself a Tier-A action; keeping that in-session reduces attack surface. Challenge if owner prefers the Telegram-guided flow.
7. **Recovery notice wording** ("Telegram recovered") is a placeholder; builder may refine.

## 9. Approval ask (G3)

Approve this proposal to open brief-drafting. Specifically:

- Locked rulings in §2 as faithful to the conversation.
- The 22 TG-criteria in §4.
- The constraints in §5.
- The 54–85 min estimate with 90-min red line.
- Eve's inferences in §8.

On G3 approval, Eve drafts the brief for G4 review; on G4, the build dispatches.
