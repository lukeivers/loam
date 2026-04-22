# Handoff Brief — Telegram Interface

**For:** the general-purpose Agent dispatched to build the telegram-interface component.
**From:** Eve, 2026-04-22 09:20 CDT.
**Status:** awaiting owner's G4 review; not yet dispatched.

---

## 1. What you are building

The Telegram interface component for pos-v2. When Telegram is configured and available, the primary-persona one-on-one channel routes through the Anthropic-shipped Claude MCP Telegram plugin — bidirectional, with multi-identity allowlist support (owner + allowlisted additional users, e.g. owner's spouse). When unavailable, clean fallback to in-session + `~/.pos/attention.md`. A session-two setup walkthrough emits exact numbered step-by-step instructions for user-dependent steps (install plugin, create bot, pair), self-retires the "offer setup" code path on confirmed round-trip.

No sealed-component amendments — the primary-persona `OneOnOneChannel` abstraction already admits this via adapter-pattern dependency injection.

## 2. Authoritative documents (read in this order)

1. **This brief.**
2. **`components/telegram-interface/proposal.md`** — the binding contract. Halt and signal rather than deviate.
3. **`components/telegram-interface/research.md`** — design detail including the plugin surface inspection. Reference only.
4. **The plugin cache** at `~/.claude/plugins/cache/claude-plugins-official/telegram/0.0.6/` — the canonical source of truth for the plugin's tools, state file, and pairing flow. The research doc summarises it; the code is the final word.
5. **`docs/rebuild/FUTURE_IDEAS.md`** in pos-v2 — the four research lenses and two Core Development Conventions the design was evaluated against.
6. **`docs/rebuild/components/primary-persona-loader/`** in pos-v2 — the sealed `OneOnOneChannel` surface this component consumes via adapter injection.

## 3. The objective in one sentence

Deliver the Telegram interface such that, when the plugin is installed and the session is flagged with `--channels plugin:telegram@claude-plugins-official`, the primary persona defaults to Telegram for every initiated surface (briefings, escalations, proactive suggestions, responses), accepts bidirectional messages from any allowlisted identity with per-identity authority context, routes Tier-A/B requests from Telegram through an extra explicit-confirmation step, and falls back cleanly to in-session + `attention.md` when Telegram is unavailable — without amending any sealed component.

## 4. Hard constraints (non-negotiable)

- **Branch:** `pos-v2`. **Language:** Python 3.13.
- **Permitted runtime deps:** stdlib, pydantic, pyee, opentelemetry, PyYAML, duckdb, plus anything needed for direct Telegram Bot API HTTPS calls (stdlib `urllib` is acceptable; `httpx` or similar third-party lib is fine if already permitted elsewhere in pos-v2).
- **No sealed-component amendments.** Primary-persona `OneOnOneChannel` is consumed via adapter-pattern; `ChannelKind.personal_telegram` already exists. If you find an amendment case, halt and signal.
- **Claude MCP Telegram plugin is the canonical channel surface.** Do not build a custom bot. Plugin insufficiency → halt and surface.
- **Default-on when available.** All persona-initiated messages route to Telegram when available; in-session is fallback. Only exception: user-initiated in-session conversation → response in-session.
- **Multi-identity allowlist.** Owner plus additional owner-added identities. Owner-mediated add flow (in-session, never self-registered). Per-identity authority-class tag (`owner` or `reduced_bound` in v1).
- **Extra-confirmation gate for Telegram-originated Tier-A/B actions.** In-session identical requests retain existing safety-gate discipline; Telegram adds the gate. 30-minute default confirmation timeout.
- **Step-by-step-when-impossible.** Setup walkthrough is numbered instructions with expected time per step, not advice.
- **Self-retire on success.** The "offer setup" code path reads `~/.pos/telegram-setup-offered` marker and short-circuits when it exists. Marker is written on confirmed round-trip.
- **Loud-escalation on failure.** No dropped messages, no silent-continue. Nine named failure classes per research §2.4 each have a disposition.
- **No group-chat support.** One-on-one is structural.
- **A1 correction held.** OTel via `trace.get_tracer("pos.telegram_interface")`; no `TracerProvider` construction.
- **Error-code range `-32100..-32109`** reserved. Verify no prior allocation; halt if collision.
- **Halt on deviation.**

## 5. Acceptance (ODD — 22 criteria in proposal §4)

TG1–TG6: setup walkthrough — offer, decline-path, success-and-self-retire, prior-settings preservation, per-step failure remediation.
TG7–TG11: transport routing — MCP plugin in-session, direct Bot API out-of-session, fallback during outage with framing preamble, inbound routing with allowlist lookup, recovery.
TG12–TG13: availability probe — 60s background probe + at-send check + 5s aggressive retry on failure, OTel spans per retry.
TG14–TG17: multi-identity allowlist — owner-mediated add, identity-scoped persona context, Tier-A/B refusal from non-owner, silent drop on unauthorised sender.
TG18–TG19: Telegram-originated Tier-A/B extra-confirmation — yes/no from Telegram required, 30-min timeout refuses.
TG20–TG22: token rotation + rate-limit + blocked-by-user failure modes.

Each criterion is an observable outcome testable deterministically. Tests target the criterion directly.

## 6. Verify-against-code discipline

Before authoring code, confirm surfaces against the actual pos-v2 tree and plugin cache. Five priority verifications:

- **`primary-persona-loader/` `OneOnOneChannel` surface** — confirm the `send: Callable[[str], Awaitable[None]]` injection pattern and `ChannelKind.personal_telegram` enum value exist as research §3 claims. Halt if not.
- **Plugin tools** — `~/.claude/plugins/cache/claude-plugins-official/telegram/0.0.6/` — confirm tool names (`reply`, `react`, `edit_message`, `download_attachment`) and their parameter signatures. Confirm the inbound `<channel>` tag shape in its handler.
- **`access.json` schema** — confirm the allowlist data structure supports multi-entry and the extension fields you add (`display_name`, `relationship`, `authority_class`, `added_at`) are orthogonal to the plugin's own keys so extending it does not break plugin behaviour.
- **Hands-off-lifecycle `attention.md` surface** — confirm its file path + append discipline before the fallback path writes to it.
- **Existing error-code allocations** — scan the rebuild tree for any prior claim to `-32100..-32109`. If any exist, halt and propose an alternative range.

If any verification fails against the proposal's claim, halt and signal with the named file and symbol.

## 7. Eve's inferences (proposal §8) — challenge any that feel wrong

1. Error-code range `-32100..-32109`.
2. 30-minute Telegram-confirmation timeout.
3. 5-minute rate-limit loud-escalation bound.
4. Authority-class enum values `owner` / `reduced_bound` only in v1.
5. `~/.pos/telegram-setup-offered-declined` filename pattern.
6. Owner-mediated add-identity flow stays in-session.
7. Recovery-notice wording placeholder.

Challenge any with a halt signal and your alternative.

## 8. Estimate

**54–85 AI-minutes wall-clock. Red line at 90.**

Honest calibration from research §12. Scope areas where complexity can swell: the out-of-session direct-Bot-API path and the multi-identity authority-class routing. Watch those.

**Halt triggers at build time:**

- Past 90 minutes without the 22 TG-criteria mapped to passing tests — halt and report.
- Any sealed-component amendment surfacing — halt.
- Any regression on an unamended sealed component — halt.
- MCP plugin behaviour materially diverging from research §2.2 — halt and surface.

## 9. What I need back

On completion:

1. **Paths to commits on `pos-v2`.** Commit granularity is your call.
2. **Test results** — every TG-criterion (TG1–TG22, plus any TG23+ you added with rationale) mapped to a passing test. All sealed-component regression suites passing.
3. **Sealed-component diff check** — `git diff --name-only <baseline>..<your-head>` should cover only `telegram-interface/` (new), and any adapter-registration entries at pos-v2 root (`first-run-inventory.yaml` possibly; `.claude/settings.json` if the `--channels` flag persistence needs it). Any sealed source under the sealed-component directories touched is a halt-signal.
4. **SEAL_COMMIT sidecar** present for the new component.
5. **Both-venvs validation** — report shared-venv pass count AND memory-system own-venv pass count separately (ritual inherited from hands-off-lifecycle).
6. **Eve-inferences challenged** and the alternative you chose (or halted on).
7. **Any halt signals.**
8. **Actual wall-clock vs 54–85 min estimate** from the `duration_ms` field of your task notification.

Return summary: under 500 words.

## 10. Failure modes I am watching for

- Custom Telegram bot sneaking in because the MCP plugin is "annoying to use." Don't — use the plugin.
- Amending primary-persona-layer because adapter-pattern "feels clean." Adapter wraps the existing surface; if you feel the urge to touch sealed code, halt and surface.
- Silent drop of messages during Telegram outage. Forbidden. Fallback routes to `attention.md` + in-session with framing.
- Non-owner identity escalation via prompt injection — Tier-A/B requests from any Telegram-originating message require the extra confirmation step, regardless of identity.
- Group-chat support smuggled in because the plugin technically supports it. One-on-one is structural; group deliveries are Tier-A external-comms territory outside pos-v2 default scope.
- Out-of-session direct Bot API path using a different authorisation surface than the MCP plugin — both paths share the same `access.json` allowlist.

---

**End of brief.** Owner reviews at G4; on their green light, dispatch follows.
