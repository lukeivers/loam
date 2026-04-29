# Notification flow

The framework is persona-less. All user communication goes through
the primary persona's one-on-one channel per **v1.1 R13 + v1.2 R15**
(one-on-one restriction — never group chats).

## `auto_update_mode` modes

### `require_confirmation` (default for v1)

Safest — matches the rebuild's fail-closed posture.

```
[Eve → Luke, one-on-one]
"Upgrade pos-v2-v0.3.0 available. Breaking changes declared: mem-v4.
 Reply 'yes' to proceed or 'no' to skip."

User: yes

[Eve → Luke, post-accept]
"Upgrade pos-v2-v0.3.0 accepted in 42.1s — clauses OK: a, b, c, d, e, f, g."
```

**Timeout:** 24 h default (Eve's inference — tunable in config). On
timeout, the upgrade is marked **deferred** and the framework logs the
deferral. The user can retry by running `pos upgrade <tag>` again.

**Breaking changes surface in the notification.** When the manifest
declares any `breaking_changes`, the notification includes the list.
The user's `yes` is consent to the breaking changes. A non-interactive
invocation (e.g. scheduled cron, should we ever add one) must still
observe this: the CLI supports an explicit
`--i-read-the-breaking-changes` flag that serves the same function.

### `notify_and_apply`

```
[Eve → Luke]
"Upgrading to pos-v2-v0.3.0 in 60 s — reply 'cancel' to abort."

(60 seconds pass)

[Eve → Luke, post-accept]
"Upgrade pos-v2-v0.3.0 accepted in 42.1s — clauses OK: a, b, c, d, e, f, g."
```

**Cancel window:** 60 s default (Eve's inference — tunable). Short
enough not to feel like an interruption, long enough for a "wait, no"
response to land.

## Failure-mode notifications

### Rolled back

```
[Eve → Luke]
"Upgrade pos-v2-v0.3.0 rejected and rolled back.
 Failing clauses: c. Report: ~/.loam/framework/history/<tag>-rolled-back.json"
```

### Rollback failed (Tier 1, manual recovery)

```
[Eve → Luke, Tier 1]
"UPGRADE FAILED AND ROLLBACK FAILED. System in undefined state.
 Details: ~/.loam/framework/history/<tag>-rollback-failed.json.
 Manual recovery required."
```

No auto-retry. The user decides next action.

## Implementation

- `self_upgrade.notification.NotificationChannel` is the one-method
  `send(str)` + `recv(timeout_s)` protocol.
- Production: workspace wires it to the primary persona's IPC
  channel.
- Testing: `InMemoryChannel` lets tests drive it synchronously.

## Channel requirements

- **One-on-one only.** The channel talks to the user alone.
  Group-chat writes are forbidden (v1.1 R13).
- **Primary persona voice.** The channel is the primary persona's
  voice to the user — not Luke's voice to others.
- **Pre-authorised.** The channel is set up during first-run
  orientation; the framework does not authorise it itself.
