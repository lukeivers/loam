# telegram-interface

## What it does

`telegram-interface` is the channel adapter that lets the primary
persona reach you on Telegram instead of (or in addition to) the
terminal. It composes against the Claude MCP Telegram plugin
where one is configured, falls back to direct Bot API calls
where the plugin is not available, and enforces an allowlist of
who is permitted to talk to the persona on the channel.

The component exists because:

- **The terminal is not always where the user is.** Long-running
  background work that finishes mid-meeting needs to surface
  somewhere portable.
- **Telegram is a low-ceremony surface.** No app to install,
  no dashboard to log into; a notification on the user's
  existing device.
- **Multi-identity needs are real.** A user may want a personal
  channel and a project-team channel reachable on the same bot,
  with policies that differ by chat.

## How to invoke

The user-facing flow has three parts:

1. **Set up the bot.** The `/telegram:configure` skill walks
   through bot token capture and channel review. Run it from
   inside Claude Code in the workspace.
2. **Manage access.** The `/telegram:access` skill approves
   pairings, edits the allowlist, sets DM-vs-group policy.
3. **Talk.** Once paired, you message the bot from Telegram;
   the persona replies through the same channel. The terminal
   continues to receive diagnostic output but is not the
   user-visible reply surface when Telegram is configured.

There is no `loam telegram` CLI in v0.1.0; the channel is
configured through the skill flow.

## Observable surface

What you can `tail` / `cat` / `grep` to see the component working:

- **OTel spans.** `loam.telegram_interface.*` namespace.
  Reply attempts emit `reply` spans; access checks emit
  `access` spans; pairing flows emit `pair` spans.
- **Allowlist file.** Per-workspace allowlist under the
  component's data area; the access skill reads/writes it.
- **Outage behaviour.** If a reply fails (network, MCP server
  down, auth expired), the persona pauses new dispatches and
  surfaces the outage in the terminal once. Visible in
  `loam.telegram_interface.outage.*` spans.
- **Bot API fallback log.** When the MCP plugin is unavailable,
  the component falls back to direct Bot API calls; the
  fallback path emits its own `bot_api.*` span series.

## Stable surfaces (for plugin authors)

The component publishes a `Channel` adapter contract; alternative
channel implementations (Slack, IRC, email) plug in by
contributing the same shape. The persona's reply surface routes
through whichever channel the workspace declares as primary.

For internal implementation detail see the component source under
`framework/telegram-interface/`.
