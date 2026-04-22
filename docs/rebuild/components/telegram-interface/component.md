# Component — Telegram Interface

**Created:** 2026-04-22 07:48 CDT. **State:** ✅ **COMPLETE** — sealed 2026-04-22 09:55 CDT by Luke. Build commit `cdfb3f3`, seal-paperwork commit `d4e80cd`.

**Phase 5, third component.** Lands immediately after true-first-run to provide full bidirectional Telegram as the primary-persona channel.

---

## Outcome

When Telegram is configured, the system defaults to conversing with the user via Telegram — full bidirectional interface. The user messages Eve from Telegram; Eve responds via Telegram; background notifications, escalations, and daily briefings all route there. When Telegram is unavailable (user has not set it up, the MCP plugin is disconnected, the user is at their desk and explicitly in a Claude Code session), fall back to in-session + `~/.pos/attention.md` with a framing preamble.

## Key constraints (held)

- **Uses the Claude MCP Telegram channel plugin** (`claude-plugins-official/telegram@0.0.6`), not a custom-built bot. The plugin is the channel surface; this component wraps it behind `TelegramAdapter` and wires it into the sealed `OneOnOneChannel` primitive via `ChannelKind.personal_telegram`. Zero sealed-component amendments.
- **Owner ruling 2026-04-22 07:47:** *"when it is setup, the system should always default to conversing via telegram if it is available, and only via direct feedback in terminal or claude app when telegram isn't possible."* Default-on when available; in-session is fallback. Implemented.
- **Multi-identity allowlist** — owner plus additional owner-added identities (e.g. spouse). Per-identity `authority_class` tag (`owner` or `reduced_bound`). Owner-mediated add flow stays in-session.
- **First setup session (session two post-first-run):** six-step numbered walkthrough with expected-time estimates. Self-retires on confirmed round-trip (`~/.pos/telegram-setup-offered` marker with `status: done`).
- **Honours the step-by-step-when-impossible convention** (FUTURE_IDEAS Core Development Convention).
- **Extra-confirmation gate** for Telegram-originated Tier-A/B actions — yes/no required from the Telegram thread, 30-min timeout, non-owner auto-refused with owner notification.

## Artifacts

- `research-plan.md` — drafted 2026-04-22 08:47 CDT; approved G1.
- `research.md` — produced by research agent; approved G2 with seven rulings and two multi-identity ratifications.
- `proposal.md` — 22 TG-criteria; approved G3.
- `brief.md` — approved G4 2026-04-22 09:22.
- `outputs/` — build delivered on `pos-v2` under `telegram-interface/`.

## Build summary

- **Commit:** `cdfb3f3` on `pos-v2`. **Seal:** `d4e80cd`.
- **Files:** 24 (13 src, 9 tests, 2 seal sidecars). 3,354 insertions.
- **Diff scope:** zero files outside `telegram-interface/`. Zero sealed source touched.
- **Tests:** 29 passing in shared venv (TG1–TG22 + TG23); 47 in memory-system own venv. All other sealed-component regression suites green.
- **Wall-clock:** ~20.8 minutes against 54–85 minute estimate. No halt triggers fired.
- **Eve-inferences:** five of six held exactly. One refinement — setup marker consolidated into a single file with `status` field rather than two files. Judged improvement, not deviation.

## History

- 2026-04-22 07:48 CDT — component created as placeholder.
- 2026-04-22 08:47 CDT — research plan drafted; G1 approved.
- 2026-04-22 ~08:55 CDT — research produced; G2 approved with rulings and ratifications.
- 2026-04-22 ~09:10 CDT — proposal authored; G3 approved.
- 2026-04-22 09:22 CDT — brief reviewed; G4 approved; background build agent dispatched.
- 2026-04-22 09:41 CDT — build delivered at commit `cdfb3f3`. 29 TG-tests green. Zero sealed amendments.
- 2026-04-22 09:55 CDT — sealed by Luke. Sidecars updated to `cdfb3f3`; seal-paperwork commit `d4e80cd`.
