# Proposal — telegram-interface-framework-integration amendment (#9)

**Status:** DRAFT — awaiting owner ruling on §5 inferences.
**Authored by:** assistant (this session, 2026-04-22).
**Target components (multi-component amendment):**
`workspace-bootstrap` + `telegram-interface` + `hands-off-lifecycle`.
**Precedent:** orchestrator-bootstrap-unification amendment (multi-component
seal at `9aeabd4`), namespaced-labels-and-bootout amendment (multi-component
seal at `a5dbf8f`).

---

## 1. Objective

The workspace-bootstrap framework composes `telegram-interface` into
every pos-v2 boot alongside the other twelve foundational adapters.
After the amendment, `~/.pos/bootstrap.yaml` lists a thirteenth
contribution (`telegram_interface`); the first-run scaffold writes a
`~/.pos/telegram.yaml` starter; the new `TelegramInterfaceContribution`
constructs a `TelegramAdapter`, exposes its `OneOnOneChannel` on the
host, and registers it as a pos-v2 channel surface — all without
amending the sealed `telegram-interface` public API and without
requiring Telegram credentials to exist at boot.

Three behaviours in one objective — §4 below counts criteria against it.

## 2. Constraints

- **Budget.** New adapter file + one `_BOOTSTRAP_YAML` line + one new
  scaffold YAML constant + seal-diff discipline. No new framework
  phase, no new `Phase` enum value, no change to `ContributionMetadata`
  schema. If implementation would require new core machinery, halt
  and signal — scope creep.
- **Reversibility.** Fully reversible. Removing the adapter file and
  reverting the `_BOOTSTRAP_YAML` constant restores prior behaviour.
  `~/.pos/telegram.yaml` is an owner-editable starter; deleting it is
  harmless.
- **Dependency fence.** Amends `workspace-bootstrap/` (new adapter +
  scaffold constant), `telegram-interface/` (docs only — see §5 #7),
  and `hands-off-lifecycle/` (BASELINE bump + allowed-prefix
  addition). Every other sealed component is off-limits: orchestrator,
  memory-system, safety-layer, reversibility-primitive, cost-governance,
  self-correction, graceful-degradation, scope-of-work,
  objective-tracker, primary-persona, observability-aggregator,
  self-upgrade.
- **Sealed-API invariant.** The adapter consumes only
  `TelegramAdapter.build_channel()`, `AccessFile.load()`,
  `AvailabilityProbe(...)`, and `BotApiClient(...)` — every symbol
  already exported by `telegram-interface`'s public surface at
  `cdfb3f3`. Zero `telegram-interface/src/` edits.
- **Authority bound.** Owner approves acceptance criteria (this doc)
  + the flagged inferences in §5 + the seal-plan SHA bump. Builder
  chooses file layout, diagnostic wording, log-line shape.
- **Fail-closed direction.** When telegram-interface is listed in
  `bootstrap.yaml` but the config file / token / allowlist are
  absent, the adapter composes into a **degraded-but-alive** channel
  — `is_active=False`, `send` routes to fallback, no exception
  surfaces. The component's own availability probe is the loud-
  escalation path; boot does not fail. (Owner rules on #3 confirms
  the `required=False` shape.)
- **Error codes.** Reuse the component's reserved range
  `-32100..-32109`. No new top-level codes. If the adapter wraps a
  `BotApiError` at boot (e.g. unreachable token validation), it
  raises `AdapterRaisedError` with the component's own error code in
  the `data` payload — same pattern as `workspace_bootstrap_py`.
- **Out of scope.** Richer per-domain authority taxonomy, Telegram-
  originated add flow, group-chat support, MCP stdio-transport
  wiring from the orchestrator's side (the adapter ships
  `mcp_client=None` at boot; only the primary persona's in-session
  path supplies one). Each remains owned by its own future amendment.

## 3. Acceptance criteria

Each criterion maps 1:1 to a test function in the build.

### AC1 — Adapter class exists with correct metadata

`workspace-bootstrap/src/workspace_bootstrap/adapters/telegram_interface.py`
defines `TelegramInterfaceContribution(BaseContribution)` with
`metadata = ContributionMetadata(name="telegram_interface",
phase=Phase.after_orchestrator_ready,
after=("primary_persona", "safety_layer"), required=False)`. Test:
import the class, assert metadata fields match byte-for-byte.

### AC2 — Adapter is the thirteenth entry in `_BOOTSTRAP_YAML`

`_BOOTSTRAP_YAML` in `first_run_scaffold.py` lists thirteen
contributions; the trailing entry is `telegram_interface` mapped to
`workspace_bootstrap.adapters.telegram_interface.TelegramInterfaceContribution`.
Header comment reads "thirteen-foundational-adapter bundle". Test:
parse the YAML, assert `len(contributions) == 13` and the last
entry's `name == "telegram_interface"`.

### AC3 — Framework composes telegram_interface end-to-end at default config

Invoke the framework on a tmp workspace with the new
`_BOOTSTRAP_YAML`, no `~/.pos/telegram.yaml`, no
`~/.claude/channels/telegram/access.json`, no `TELEGRAM_BOT_TOKEN`
env var. Assert composition succeeds, `host.telegram_adapter` is a
`TelegramAdapter`, `host.telegram_channel` is a `OneOnOneChannel`
with `kind=ChannelKind.personal_telegram` and `is_active=False`.
No exception reaches the caller. This is the "missing credentials =
degraded-alive, not failed-closed" shape (owner ruling on §5 #3).

### AC4 — First-run scaffold writes `~/.pos/telegram.yaml`

After `run_first_run_scaffold(pos_root=tmp_path, ...)` on a fresh
tmp_path, `(tmp_path / "telegram.yaml").exists() is True`. The file
content matches a new `_TELEGRAM_YAML` constant with the starter
shape from §5 #4. Assumes owner ruling lands on the "scaffold writes
starter" path.

### AC5 — Adapter publishes the Telegram channel on the host

After composition (AC3 fixtures), `host.telegram_channel` is the
same object returned by `adapter.build_channel()`; calling
`host.telegram_channel.send("hi")` under `is_active=False`
routes through the adapter's fallback (writes one line to
`~/.pos/attention.md` under the tmp root). Confirms the channel
surface is wired the same way terminal/safety/cost channels are
(via `host.channel_registry["telegram"] = host.telegram_channel`
convention — see §5 #6).

### AC6 — Adapter fails loud when required=True and credentials missing

Same fixtures as AC3 plus a `~/.pos/telegram.yaml` containing
`required: true`. Assert the framework raises `AdapterRaisedError`
wrapping a telegram-interface diagnostic whose `code` is
`IPC_TELEGRAM_TOKEN_INVALID` (`-32102`) or
`IPC_TELEGRAM_SETUP_FAILED` (`-32108`). Confirms the opt-in fail-
closed path for workspaces that require Telegram present at boot.

### AC7 — Sealed-API invariant: no telegram-interface source touched

`git diff --name-only BASELINE..SEAL_COMMIT -- telegram-interface/src/`
is empty. The amendment consumes `telegram-interface`'s public
surface exclusively; if any source file under `src/` is modified,
halt — the amendment scope has outgrown "single adapter addition".
Docs-only additions under `telegram-interface/` (e.g. a
README section noting the framework-integration path) remain
allowed.

### AC8 — Adapter ordering: runs after primary_persona and safety_layer

With all thirteen adapters listed in bootstrap.yaml, the framework's
topological sort places `telegram_interface` strictly after
`primary_persona` (provides `ChannelKind` enum + channel dataclass)
and `safety_layer` (establishes the gate chain; telegram's
Tier-A/B confirmation gate consults safety). Test: drive the
framework's composition-order introspection hook and assert the
ordering.

### AC9 — Seal diff discipline

`git diff --name-only BASELINE..SEAL_COMMIT` after the amendment
shows only paths under `workspace-bootstrap/`, `telegram-interface/`
(docs subset only, per AC7), `hands-off-lifecycle/`,
`docs/rebuild/components/telegram-interface-framework-integration/`,
and `data/`. Any path outside this set is a halt condition for
the seal commit.

## 4. Behaviour-count check

| Behaviour | Criteria |
|-----------|----------|
| Adapter exists and is ordered correctly | AC1, AC8 |
| Framework composes telegram_interface as the 13th foundational bundle | AC2, AC3, AC5 |
| Degraded-alive at default; loud-fail on explicit required=True | AC3 (default), AC6 (opt-in-strict) |
| Scaffold + sealed-API discipline | AC4 (scaffold writes starter), AC7 (no sealed src touched) |
| Seal discipline | AC9 |

Five distinct behaviours → nine criteria → every behaviour covered
by at least one test.

## 5. Flagged inferences (owner rules)

1. **Phase placement = `after_orchestrator_ready`.** Justification:
   telegram-interface needs `host.orchestrator`-adjacent state
   (ipc_server for tier-A/B confirmation plumbing if wired later,
   the scope runtime's event emitter for background-failure
   escalation) but does NOT wrap `activate_scope`. Mirrors
   `self_correction` and `workspace_bootstrap_py`. Alternative
   considered: `before_orchestrator_start` (like
   `observability_aggregator`). Rejected because the adapter's
   `after=("safety_layer",)` dependency can only be expressed in
   `after_orchestrator_ready` — safety_layer is wrap-phase.

2. **`after:` dependencies = `("primary_persona", "safety_layer")`.**
   `primary_persona` is the owner of `OneOnOneChannel` /
   `ChannelKind.personal_telegram` — the sealed primitive the
   adapter consumes. `safety_layer` is included because telegram's
   Tier-A/B confirmation gate is the user-visible counterpart to
   safety's always-ask floor; ordering after safety ensures
   `host.safety_controller` is populated if the adapter (in a
   future enhancement) wants to cross-check approval state.
   **Challenge note:** `safety_layer` dependency could be dropped
   if the adapter does not currently consult
   `host.safety_controller`. Builder call: read the adapter body
   this amendment lands and keep the dependency only if used.

3. **`required = False` at the metadata level.** Telegram is a
   "user-adds-later" channel — most workspaces boot without a bot
   token and never configure one. First-run must succeed with zero
   Telegram state. The `required` knob on `ContributionMetadata`
   governs import-time availability, not runtime credentials; the
   adapter is always importable, so this is technically a no-op,
   but setting `required=False` documents the intent. Runtime-
   credential strictness is controlled by
   `~/.pos/telegram.yaml`'s own `required: bool` key (AC6), mirroring
   the `workspace_bootstrap_py` pattern.

4. **`~/.pos/telegram.yaml` starter shape.** Proposed:
   ```yaml
   # ~/.pos/telegram.yaml — per-workspace Telegram channel config.
   # Most fields are optional. Leaving this whole file out is fine;
   # the adapter boots in degraded-alive mode and the setup
   # walkthrough runs on session two.
   required: false                       # set true to fail-close boot if creds absent
   env_path: ~/.claude/channels/telegram/.env
   access_path: ~/.claude/channels/telegram/access.json
   default_tier: 2                       # degradation-config default
   probe_interval_s: 60                  # overrides telegram-interface default
   ```
   **Challenge note:** bot token is NOT stored here (§5 #5). If
   owner prefers no starter YAML at all (adapter reads built-in
   defaults, user creates the file only to override), strike
   `_TELEGRAM_YAML` and rewrite AC4 as a "file absent is fine" assertion.

5. **Credentials (bot token) remain in `~/.claude/channels/telegram/.env`.**
   This is where `bot_api.load_token()` already reads from, and where
   the setup walkthrough (`setup_walkthrough.step2_confirm`) writes.
   The framework adapter does NOT relocate the token into `~/.pos/` —
   that would fork the source of truth with the Claude MCP plugin,
   which owns the `.env` shape. `TELEGRAM_BOT_TOKEN` env var is the
   secondary override, as it is today. No Keychain integration in
   this amendment.

6. **Host attribute names.** Proposed:
   - `host.telegram_adapter: TelegramAdapter`
   - `host.telegram_channel: OneOnOneChannel` (duplicate ref for
     callers who want the channel without reaching through the
     adapter)
   - `host.channel_registry["telegram"] = host.telegram_channel`
     (same registration pattern as safety/cost/reversibility).
   Builder picks final names; tests key off these.

7. **`telegram-interface/` edits.** Probably docs-only. A brief
   README section pointing at the framework integration path is
   helpful for the next reader; if the adapter can be written
   against `telegram-interface`'s current exports without any src
   change, no src touch at all. Builder confirms by writing AC3
   against the unmodified `telegram-interface/` source; only amend
   `telegram-interface/` if a test cannot pass.

## 6. Seal plan

1. Create the new adapter at
   `workspace-bootstrap/src/workspace_bootstrap/adapters/telegram_interface.py`.
   Update `_BOOTSTRAP_YAML` in `first_run_scaffold.py` to list
   thirteen contributions; update the header comment from
   "twelve-foundational-adapter bundle" to "thirteen-foundational-
   adapter bundle". Update `CONFIRMATION_SENTENCE` from "twelve
   foundational components" to "thirteen foundational components"
   (one-word change — verify nothing grep-pins the old string).
2. Add `_TELEGRAM_YAML` constant + `"telegram.yaml"` entry in
   `_SCAFFOLD_FILES` (conditional on §5 #4 landing).
3. Advance `BASELINE` in
   `workspace-bootstrap/tests/test_no_sealed_amendments.py` from
   `a5dbf8f` → `9aeabd4` (current tip).
4. Advance `BASELINE` in
   `hands-off-lifecycle/tests/test_cross_cutting.py` from `a5dbf8f`
   → `9aeabd4`.
5. Advance `BASELINE` in
   `telegram-interface/tests/test_no_sealed_amendments.py` from
   `e1686e1` → `9aeabd4` and add `"workspace-bootstrap/"`,
   `"hands-off-lifecycle/"`,
   `"docs/rebuild/components/telegram-interface-framework-integration/"`
   to its allowed-prefixes tuple.
6. Amendment commit:
   `fix(workspace-bootstrap, telegram-interface, hands-off-lifecycle):
   telegram-interface-framework-integration amendment (#9)`.
7. Tests committed together with the fix.
8. Seal commit (separate):
   `chore(seals): telegram-interface-framework-integration seal —
   workspace-bootstrap + telegram-interface + hands-off-lifecycle
   at <sha>`. Advances the three `SEAL_COMMIT` sidecars to the
   amendment code-commit SHA and appends amendment-cycle notes.
9. Allowed-prefix additions:
   - `workspace-bootstrap/` test gains
     `"telegram-interface/"`,
     `"docs/rebuild/components/telegram-interface-framework-integration/"`.
   - `hands-off-lifecycle/` test gains
     `"docs/rebuild/components/telegram-interface-framework-integration/"`.
   - `telegram-interface/` test gains the three prefixes listed in
     step 5.

## 7. Halt triggers

- The adapter cannot construct a `TelegramAdapter` without
  amending `telegram-interface/src/` — signals the public API
  needs a new constructor or factory, which is out of scope.
- Composition order requires a new `Phase` value (the current
  four-phase enum cannot express
  `after=("primary_persona","safety_layer")` within
  `after_orchestrator_ready`) — signals framework-core scope creep.
- AC3 requires real Telegram credentials to pass deterministically
  — signals the degraded-alive path isn't actually credential-
  independent and needs a design revisit.
- AC6 requires the adapter to block on network I/O at boot to
  validate the token — signals the `required: true` path is
  incompatible with fast-boot; owner rules on whether to keep the
  behaviour or relax it to a post-boot probe failure.
- Any AC test cannot be written deterministically (would require
  model inference, network access, or real human interaction with
  Telegram).
- The `hands-off-lifecycle` first-run worker's health poll (the
  AC7 equivalent from amendment #6) assumes exactly the
  orchestrator + memory-graphiti service pair; adding Telegram as
  a supervised service is out of scope for this amendment (the
  adapter runs inside the orchestrator process, not as a separate
  launchd/systemd service).

Any of the above: halt, signal to owner, re-scope before continuing.
