# telegram-interface-framework-integration amendment (#9) — build plan

**Status:** plan (written before any edit lands, per plan-before-code CDC).
**Branch:** `pos-v2` at HEAD `b9e1f96`.
**Proposal:** `docs/archive/component-research/telegram-interface-framework-integration/proposal.md`.

---

## 1. Objective (from proposal §1)

Compose `telegram-interface` into every pos-v2 boot alongside the other
twelve foundational adapters. After the amendment,
`~/.pos/bootstrap.yaml` lists a thirteenth contribution
(`telegram_interface`); the first-run scaffold writes a
`~/.pos/telegram.yaml` starter; the new
`TelegramInterfaceContribution` constructs a `TelegramAdapter`, exposes
its `OneOnOneChannel` on the host, and registers it as a pos-v2 channel
surface — all without amending the sealed `telegram-interface` public
API and without requiring Telegram credentials to exist at boot.

## 2. Owner rulings applied (from the dispatch, per proposal §5)

1. Default shape = degraded-alive (matches §5 #3).
2. `required=False` metadata (matches §5 #3).
3. `~/.pos/telegram.yaml` starter written (matches §5 #4).
4. `after=("primary_persona","safety_layer")` deps (matches §5 #2).
5. `after_orchestrator_ready` phase (matches §5 #1).

## 3. Scope math — BASELINE advance

Dispatch states: current tip `b9e1f96`; all BASELINE advances in
sealed-component tests land at this SHA. The proposal's seal-plan §6
names `a5dbf8f → 9aeabd4`; that delta pre-dates amendments #10/#11,
so the actual advance is `<prior-baseline> → b9e1f96` for each of the
three sealed-component tests:

| Test | Prior BASELINE | New BASELINE |
|------|----------------|--------------|
| `workspace-bootstrap/tests/test_no_sealed_amendments.py` | `7d462e3` | `b9e1f96` |
| `hands-off-lifecycle/tests/test_cross_cutting.py` | `77389ce` | `b9e1f96` |
| `telegram-interface/tests/test_no_sealed_amendments.py` | `e1686e1` | `b9e1f96` |

## 4. File-level plan

### 4.1 Files to CREATE

1. `workspace-bootstrap/src/workspace_bootstrap/adapters/telegram_interface.py`
   — new adapter module exporting `TelegramInterfaceContribution`
   (BaseContribution subclass). Phase
   `after_orchestrator_ready`, `after=("primary_persona","safety_layer")`,
   `required=False`. `contribute(host)` constructs an
   `AvailabilityProbe` with a degraded-alive default probe, an
   `AccessFile.load()` from the configured path, and a `TelegramAdapter`;
   builds the `OneOnOneChannel` via `adapter.build_channel()`; attaches
   both to the host (`host.telegram_adapter`, `host.telegram_channel`,
   `host.channel_registry["telegram"]`). Reads `~/.pos/telegram.yaml`
   (if present) for the `required: bool` key + path overrides. When
   `required: true` and the file/token/allowlist is absent, raises
   `AdapterRaisedError` wrapping an `IPC_TELEGRAM_*` code.
2. `workspace-bootstrap/tests/test_telegram_interface_adapter.py` — one
   test function per AC1, AC3, AC5, AC6, AC8 (the adapter-side ACs).
3. `docs/plans/telegram-interface-framework-integration-build-plan.md`
   — this file.

### 4.2 Files to MODIFY

1. `workspace-bootstrap/src/workspace_bootstrap/adapters/first_run_scaffold.py`
   — three edits:
   - `_BOOTSTRAP_YAML` header comment `twelve-foundational-adapter
     bundle` → `thirteen-foundational-adapter bundle`; append one
     contribution stanza for `telegram_interface` referencing
     `workspace_bootstrap.adapters.telegram_interface.TelegramInterfaceContribution`.
   - `CONFIRMATION_SENTENCE` `twelve foundational components` →
     `thirteen foundational components`.
   - Add new `_TELEGRAM_YAML` constant (owner-approved starter shape
     from proposal §5 #4) and add `"telegram.yaml": _TELEGRAM_YAML`
     entry to `_SCAFFOLD_FILES`.
2. `workspace-bootstrap/tests/test_first_run_scaffold.py` — update
   `test_H5_confirmation_sentence_is_Q7_approved_wording` expected
   string to say `thirteen foundational`; update
   `test_H1_fresh_first_run_writes_all_yamls` to also assert
   `telegram.yaml` present (AC4).
3. `workspace-bootstrap/pyproject.toml` — add
   `pos_telegram_interface` to `[project].dependencies` + register
   `telegram_interface` entry-point under
   `[project.entry-points."pos.bootstrap.contributions"]`.
4. `workspace-bootstrap/tests/test_no_sealed_amendments.py` — advance
   `BASELINE` to `b9e1f96`; append history comment block; add
   `"telegram-interface/"` and
   `"docs/archive/component-research/telegram-interface-framework-integration/"`
   to `allowed_prefixes`.
5. `hands-off-lifecycle/tests/test_cross_cutting.py` — advance
   `BASELINE` to `b9e1f96`; append history comment block; `telegram-
   interface` top-level dir is already captured via top-level-name
   allowed set extension (`telegram-interface`) +
   `docs/archive/component-research/telegram-interface-framework-integration/`
   routes through the existing `docs` top-level allowance.
6. `telegram-interface/tests/test_no_sealed_amendments.py` — advance
   `BASELINE` to `b9e1f96`; extend `allowed_prefixes` with
   `"workspace-bootstrap/"`, `"hands-off-lifecycle/"`,
   `"docs/archive/component-research/telegram-interface-framework-integration/"`,
   and `"docs/plans/"`.

### 4.3 Files NOT to touch

- Any `telegram-interface/src/` file (per proposal AC7 sealed-API
  invariant). The adapter imports `TelegramAdapter`, `AccessFile`,
  `AvailabilityProbe`, `BotApiClient`, and error-code constants from
  the unmodified public surface.
- Any other sealed component.

## 5. BASELINE advance one-line diffs (exact)

- `workspace-bootstrap/tests/test_no_sealed_amendments.py:75`:
  `BASELINE = "7d462e3"` → `BASELINE = "b9e1f96"`.
- `hands-off-lifecycle/tests/test_cross_cutting.py:85`:
  `BASELINE = "77389ce"` → `BASELINE = "b9e1f96"`.
- `telegram-interface/tests/test_no_sealed_amendments.py:19`:
  `BASELINE = "e1686e1"` → `BASELINE = "b9e1f96"`.

Each advance is accompanied by a historical comment block explaining
the amendment (numbered #9, naming the tip immediately before the
amendment's code commit).

## 6. Test plan (ODD AC → test mapping)

| AC  | Test function (file) |
|-----|----------------------|
| AC1 | `test_AC1_adapter_metadata_matches_proposal` (workspace-bootstrap/tests/test_telegram_interface_adapter.py) |
| AC2 | `test_AC2_bootstrap_yaml_lists_thirteen_contributions` (workspace-bootstrap/tests/test_telegram_interface_adapter.py) |
| AC3 | `test_AC3_default_degraded_alive_composition_succeeds` (workspace-bootstrap/tests/test_telegram_interface_adapter.py) |
| AC4 | `test_AC4_scaffold_writes_telegram_yaml_starter` + updated `test_H1_fresh_first_run_writes_all_yamls` |
| AC5 | `test_AC5_channel_published_on_host_and_fallback_routes` |
| AC6 | `test_AC6_required_true_missing_creds_raises_adapter_error` |
| AC7 | Enforced at seal-commit by `test_tg23_only_telegram_interface_changed` — no test new function needed (AC7 is structural). |
| AC8 | `test_AC8_ordering_places_telegram_after_primary_persona_and_safety_layer` |
| AC9 | Enforced at seal-commit by `test_B20_only_workspace_bootstrap_changed` + `test_H19_diff_scope_covers_only_approved_surfaces` + `test_tg23_only_telegram_interface_changed`. |

## 7. Seal-plan step ordering

1. Write plan doc (this file).
2. Edit `first_run_scaffold.py` (YAML bundle + scaffold constant +
   confirmation sentence).
3. Create `adapters/telegram_interface.py`.
4. Update `workspace-bootstrap/pyproject.toml`.
5. Create `test_telegram_interface_adapter.py` and update
   `test_first_run_scaffold.py`.
6. Advance BASELINEs + allowed_prefixes in the three seal tests.
7. Run the four named test suites green (+ memory-system sanity).
8. Commit amendment: `fix(workspace-bootstrap, telegram-interface,
   hands-off-lifecycle): telegram-interface-framework-integration
   amendment (#9)` — code + tests + BASELINE bumps + plan doc in one
   commit.
9. Bump `seals/SEAL_COMMIT.*` sidecars + `tests/SEAL_COMMIT` sidecars
   to the amendment code-commit SHA; append amendment-cycle notes to
   each component's seal narrative.
10. Commit seal: `chore(seals): telegram-interface-framework-integration
    seal — workspace-bootstrap + telegram-interface + hands-off-
    lifecycle at <amendment-sha>`.
11. Re-run the four suites green at seal tip.

## 8. Halt-trigger checks (from proposal §7)

Before committing, confirm none of the following occurred:

1. Any file under `telegram-interface/src/` was modified.
2. Any new `Phase` enum value was added.
3. AC3 test required real Telegram credentials.
4. AC6 test required network I/O to pass.
5. Any AC test was written non-deterministically.
6. The `hands-off-lifecycle` supervisor was extended to supervise a
   new telegram service (the adapter runs inside the orchestrator
   process).

If any trigger fires, HALT and report.

## 9. Credentials safety

No real bot token, chat ID, or session secret is written to any test,
fixture, or YAML file. Tests pass fakes (class-level stub `AvailabilityProbe`
subclasses, in-memory `AccessFile` with no identities). The starter
`_TELEGRAM_YAML` contains paths only — no secret material.
