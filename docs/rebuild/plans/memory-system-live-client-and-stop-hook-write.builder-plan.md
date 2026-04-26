# Builder plan — memory-system live MCP client + Stop-hook turn-close write

**Amendment number:** #48 (next after #47).
**BASELINE (HEAD~1 of amendment commit):** `de5fe11`.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Operates against locked plan:**
`docs/rebuild/plans/memory-system-live-client-and-stop-hook-write.md`
(D1–D12 LOCKED, AC.M.1–AC.M.S frozen).

This builder plan operationalises the locked D-decisions. It does not
re-rule them.

---

## 1. Files touched

### Net-new — primary-persona

- `primary-persona/src/mcp_memory_client.py` (new) — D1.
- `primary-persona/src/stop_emitter.py` (new) — D2.

### Edits — primary-persona

- `primary-persona/src/session_start_emitter.py` — replace
  `_default_memory_client_factory` body so it returns
  `build_live_mcp_memory_client(workspace_root)`. No other change.
- `primary-persona/src/cli.py` — add `stop` subparser (routes to
  `cli_stop` from `stop_emitter`) and a `memory-write` subparser
  (routes to `cli_memory_write` from `stop_emitter`; the detached
  child entry point per D3).
- `primary-persona/src/__init__.py` — re-export `cli_stop`,
  `cli_memory_write`, `build_live_mcp_memory_client` for module-level
  introspection (mirrors #46's re-export pattern).
- `primary-persona/pyproject.toml` — add `mcp` runtime dep, version
  pinned per D5.

### Net-new — primary-persona tests (one-file-per-AC convention)

- `primary-persona/tests/test_AC_M_1_live_client_protocol_shape.py`
  — protocol-shape conformance against an in-process FastMCP server
  (so the test is deterministic without networking against the
  real workspace service).
- `primary-persona/tests/test_AC_M_2_per_turn_retrieval_reaches_additional_context.py`
  — uses the existing `FakeMemoryClient` substrate to drive the
  retrieval contributor through the registered factory path.
- `primary-persona/tests/test_AC_M_3_memory_unreachable_graceful_empty.py`
  — factory returning a client whose `search` raises
  `ConnectionRefusedError`; CLI exits 0 with empty payload.
- `primary-persona/tests/test_AC_M_4_stop_hook_exits_zero_every_path.py`
  — empty stdin / non-JSON stdin / missing transcript_path / unreadable
  transcript / internal exception → all exit 0.
- `primary-persona/tests/test_AC_M_5_stop_hook_recovers_turn_content.py`
  — well-formed JSONL transcript → handler invokes the spawn-detach
  shim with the recovered user message + assistant reply.
- `primary-persona/tests/test_AC_M_6_one_episode_per_turn.py`
  — `cli_memory_write` (the detached entry point) drives `add_episode`
  exactly once and the body contains both the user message and the
  assistant reply; group_id equals workspace slug.
- `primary-persona/tests/test_AC_M_7_stop_returns_fast_write_async.py`
  — Stop subprocess returns within 200ms while a synthetic
  `add_episode` blocks on an `asyncio.Event`. Implemented with
  monkeypatched `subprocess.Popen` recording the call site (the actual
  detach is verified via Popen invocation + start_new_session=True;
  the latency assertion uses a mocked Popen).
- `primary-persona/tests/test_AC_M_8_no_double_write_on_repeat_stop.py`
  — second Stop firing on same (session_id, last user message) skips
  detach by reading `<workspace>/.pos/last-turn-id`; only one Popen
  call is observed across two firings.
- `primary-persona/tests/test_AC_M_9_transcript_unreadable_no_op.py`
  — missing file / malformed JSONL / no user message / no assistant
  reply → zero Popen calls, exit 0.
- `primary-persona/tests/test_AC_M_10_live_client_failure_during_write.py`
  — `cli_memory_write` against an unreachable service: exits cleanly
  (rc 0), structured diagnostic line appended to
  `<workspace>/.pos/memory-writes.log`, no exception bubbles.
- `primary-persona/tests/test_AC_M_S_seal_diff_window.py` — companion
  to the existing `test_no_sealed_amendments.py`; cross-cuts to verify
  the §5 seal-diff fence (added under primary-persona because the
  AC.M.S allowed-paths set is more specific than the existing test's;
  scoped narrow assertion).

### Edits — hands-off-lifecycle

- `hands-off-lifecycle/hooks/first_run_settings.py` — add:
  - `_POS_V2_STOP_COMMAND_MARKERS` tuple (`primary_persona.cli stop`,
    `-m primary_persona`).
  - `_is_pos_v2_owned_stop(stanza_entries)` — predicate mirroring
    `_is_pos_v2_owned_user_prompt_submit`.
  - `merge_stop(*, settings_path, new_entry, now_iso=None)` — mirrors
    `merge_user_prompt_submit` shape exactly; operates on
    `hooks.Stop`.
- `hands-off-lifecycle/hooks/first_run_helper.py` — add:
  - `_persona_stop_stanza(pos_v2_root)` — lazy import of
    `primary_persona.session_start_emitter.build_persona_stop_inner_hook`
    (new helper added in #48 — see below); returns envelope or None
    on import error.
  - `_maybe_merge_stop(*, pos_v2_root, settings_path)` — mirrors
    `_maybe_merge_user_prompt_submit`; fail-soft.
  - Three call sites get a `_maybe_merge_stop(...)` invocation
    immediately after each existing `_maybe_merge_user_prompt_submit`
    call (Phase 3d ~L1640, Phase 4c re-merge ~L1839, Phase 6
    `_self_retire` ~L1222).
- Add `build_persona_stop_inner_hook(pos_v2_root) -> dict` to
  `primary-persona/src/session_start_emitter.py` (mirrors the existing
  `build_persona_session_start_inner_hook` /
  `build_persona_user_prompt_submit_inner_hook` shape; D6 timeout=5).

### Net-new — hands-off-lifecycle tests

- `hands-off-lifecycle/tests/test_AC_M_11_merge_stop_first_write.py`
- `hands-off-lifecycle/tests/test_AC_M_11_merge_stop_re_merge_pos_v2_owned.py`
- `hands-off-lifecycle/tests/test_AC_M_11_merge_stop_re_merge_user_authored.py`
- `hands-off-lifecycle/tests/test_AC_M_11_three_call_sites_invoke_merge_stop.py`
  (mirrors `test_AC46_5_first_run_stanza_carries_persona_session_start_hook`
  pattern — uses `_maybe_merge_stop` + sniffs which call paths reach
  it.)
- `hands-off-lifecycle/tests/test_AC_M_S_seal_diff_window.py` — same
  scope as the cross-cutting H19 / SEAL_COMMIT pair; asserts the
  amendment's diff stays inside §5 fence.

### Edits — sealed-component sidecars (post-amendment, via `pos-amend seal`)

- `primary-persona/tests/test_no_sealed_amendments.py` — BASELINE
  literal advances to `de5fe11` (HEAD~1 of amendment commit) per
  the BASELINE-as-HEAD~1 pattern.
- `primary-persona/tests/SEAL_COMMIT` — bumped by `pos-amend seal`.
- `hands-off-lifecycle/tests/SEAL_COMMIT` — bumped by `pos-amend seal`.
- `hands-off-lifecycle/seals/SEAL_COMMIT.true-first-run` — narrative
  appended by `pos-amend seal --plan-doc <path>`.

### Universal admissions

- `docs/rebuild/plans/memory-system-live-client-and-stop-hook-write.builder-plan.md`
  (this file, new).
- `docs/rebuild/plans/memory-system-live-client-and-stop-hook-write.manifest.yaml`
  (new — manifest authored below).
- The locked plan + research doc are already present in tree (untracked
  at HEAD `de5fe11`) and will be tracked in this commit.

---

## 2. Module shape — `primary-persona/src/mcp_memory_client.py` (D1, D5, D9)

Public symbols:

```python
async def _open_session(workspace_root: Path) -> tuple[ClientSession, AsyncExitStack]
class LiveMCPMemoryClient:                  # MemoryClient Protocol shape
    workspace_root: Path
    async def search(...) -> dict[str, Any]
    async def add_episode(...) -> dict[str, Any]
def build_live_mcp_memory_client(workspace_root: Path) -> MemoryClient | None
```

Internals:

- Read `<workspace>/.mcp.json`. If absent / malformed / missing
  `mcpServers["memory-graphiti"]["url"]`, return `None`.
- The `LiveMCPMemoryClient` object is a thin Protocol-conforming
  wrapper. It does NOT hold a long-lived session; per-call it opens
  `streamablehttp_client(url) -> ClientSession.initialize() ->
  call_tool(name, arguments) -> structured_content` and closes. Per
  the plan §9 explicit out-of-scope item (no connection pooling).
- `call_tool` returns a `CallToolResult`; we read its
  `structuredContent` field (FastMCP encodes `_impl_*` returns as
  structured content) and return the dict directly. If
  `structuredContent` is absent, fall back to parsing the textual
  content as JSON. If both fail, raise — the caller (the contributor
  or `cli_memory_write`) is the fail-soft layer.
- `add_episode` accepts `reference_time: datetime` and serialises
  via `.isoformat()` (matches the FastMCP wrapper's
  `datetime.fromisoformat(reference_time)` parse path).

D5 mcp pin: read by inspecting `memory-system/.venv/lib/python3.13/site-packages/mcp-1.27.0.dist-info/METADATA` → version is `1.27.0`. Pin to `mcp==1.27.0` in pyproject.toml.

---

## 3. Module shape — `primary-persona/src/stop_emitter.py` (D2, D3, D4, D7, D8, D11)

Public symbols:

```python
@dataclass
class StopEnvelope:
    session_id: str
    transcript_path: str
    cwd: str | None
    stop_hook_active: bool

@dataclass
class TurnContent:
    user_message: str
    assistant_reply: str
    turn_id: str

def parse_stop_envelope(raw: str) -> StopEnvelope | None
def recover_turn_content(envelope: StopEnvelope) -> TurnContent | None
def cli_stop(workspace_root: Path | None = None) -> int          # AC.M.4 / .7
def handle_stop_envelope(envelope, workspace_root) -> None       # AC.M.5 / .8
def cli_memory_write(workspace_root: Path | None = None) -> int  # AC.M.6 / .10 / D3
```

Behaviour map:

- `cli_stop`: read stdin → parse → `handle_stop_envelope`. Always
  returns 0; every internal exception caught and swallowed (AC.M.4).
- `handle_stop_envelope`: recover content; if either user_message
  or assistant_reply empty → log "skipped: <reason>" and return
  (AC.M.9, D11); compute `turn_id = f"{session_id}:{sha256(user_message)[:12]}"`;
  read `<workspace>/.pos/last-turn-id` — if equal, log "skipped:
  duplicate" and return (AC.M.8); write the new turn_id atomically;
  spawn the detached child via
  `subprocess.Popen([python, "-m", "primary_persona.cli",
  "memory-write", "--workspace", str(workspace_root),
  "--turn-id", turn_id, "--user-message", user_message,
  "--assistant-reply", assistant_reply, "--session-id", session_id],
  start_new_session=True, stdin=DEVNULL, stdout=DEVNULL,
  stderr=DEVNULL)` (D3) and return.
- `cli_memory_write`: synchronous-from-asyncio entry point. Loads
  the live MCP client; if None, log diag + return 0; build a
  `TurnAggregator(memory_client=client, workspace_slug=resolve_workspace_slug(root))`;
  call `aggregator.close_turn(...)` synchronously by driving the
  task to completion via a fresh event loop (the detached process
  has no other work). Catch every exception, log a structured
  diagnostic to `<workspace>/.pos/memory-writes.log`, return 0
  (AC.M.10).
- Diag log shape (D8): newline-delimited JSON, one entry per write
  attempt; fields `{ts, kind, turn_id, ok, error?}`.

The arguments-via-CLI shape avoids exposing user/assistant content on
the kernel-visible argv beyond what is strictly necessary; but the
turn content IS argv-visible. ODD §1.1 method-call. Acceptable per
the plan's threat model — this is a single-user laptop process.

D10 caveat: a quick empirical-verification fixture during build —
captured as `personas/...` is out of scope; instead, the build adds
a unit test (`test_AC_M_8_no_double_write_on_repeat_stop`) that
exercises the dedupe surface with a simulated re-firing envelope.
The envelope shape is documented in
`/Users/lukeivers/ivers-corp-pos-v2/docs/rebuild/plans/research/memory-system-live-client-and-stop-hook-write-research.md`
§ on Stop-hook contract (research §3-§5). If empirical verification
in pos3 reveals divergence later, AC.M.9 graceful-no-op absorbs it.

---

## 4. `cli.py` extension

Two new subparsers:

```python
p_stop = sub.add_parser("stop", help="...")
p_stop.add_argument("--workspace", type=Path, default=None)
p_stop.set_defaults(func=_cmd_stop)

p_mw = sub.add_parser("memory-write", help="...")
p_mw.add_argument("--workspace", type=Path, default=None)
p_mw.add_argument("--turn-id", type=str, required=True)
p_mw.add_argument("--user-message", type=str, required=True)
p_mw.add_argument("--assistant-reply", type=str, required=True)
p_mw.add_argument("--session-id", type=str, required=True)
p_mw.set_defaults(func=_cmd_memory_write)
```

`_cmd_stop` routes to `cli_stop`. `_cmd_memory_write` routes to
`cli_memory_write` (which receives args via the `args.workspace`,
`args.turn_id`, etc.). Both return 0 unconditionally.

---

## 5. Manifest (`docs/rebuild/plans/memory-system-live-client-and-stop-hook-write.manifest.yaml`)

```yaml
schema_version: 1
amendment:
  number: 48
  slug: memory-system-live-client-and-stop-hook-write
  title: "primary-persona live MCP memory client + Stop-hook turn-close write"

baseline: de5fe11e48d848332db339273cabe6ca0c3faa69

plan: docs/rebuild/plans/memory-system-live-client-and-stop-hook-write.md

seal_description: "primary-persona live MCP client + Stop-hook turn-close"

components:
  - name: primary-persona
    seal_test: primary-persona/tests/test_no_sealed_amendments.py
    sidecar: primary-persona/tests/SEAL_COMMIT
    frozen_baseline: false
  - name: hands-off-lifecycle
    seal_test: hands-off-lifecycle/tests/test_cross_cutting.py
    sidecar: hands-off-lifecycle/tests/SEAL_COMMIT
    frozen_baseline: true

universal_paths:
  prefixes:
    - docs/rebuild/plans/
  files:
    - CLAUDE.md
    - docs/odd-in-pos.md
    - docs/odd-methodology.md
    - docs/rebuild/FUTURE_IDEAS.md

narrative:
  target: hands-off-lifecycle/seals/SEAL_COMMIT.true-first-run
  body: |
    # Amendment #48 — primary-persona live MCP memory client +
    #                  Stop-hook turn-close write
    (filled at seal time per locked plan §6/§10)
```

---

## 6. Order of operations

1. Add `mcp==1.27.0` to `primary-persona/pyproject.toml`; pip-install it
   into `.venv` so imports resolve at test time.
2. Author `primary-persona/src/mcp_memory_client.py` + tests for
   `build_live_mcp_memory_client` (Protocol-shape conformance).
3. Author `primary-persona/src/stop_emitter.py` + cli wiring + tests.
4. Add `build_persona_stop_inner_hook` to `session_start_emitter.py`.
5. Edit `_default_memory_client_factory` to return live client.
6. `hands-off-lifecycle/hooks/first_run_settings.py` adds `merge_stop`.
7. `hands-off-lifecycle/hooks/first_run_helper.py` adds
   `_persona_stop_stanza` + `_maybe_merge_stop` + 3 call sites.
8. Author `hands-off-lifecycle/tests/` Stop-related tests.
9. Run `primary-persona/tests/` and `hands-off-lifecycle/tests/`
   separately. Iterate to green.
10. Author the manifest YAML.
11. `pos-amend apply --dry-run <manifest>` — must exit 0.
12. Amendment commit: `feat(primary-persona, hands-off-lifecycle):
    wire live MCP memory client + Stop-hook turn-close write
    (amendment #48, AC.M.1–AC.M.S)`.
13. `pos-amend apply <manifest>` (advances BASELINE if needed; the
    plan's universal-paths admissions are already in the literal).
14. `pos-amend seal --plan-doc <abs-plan-path> <manifest>` —
    advances sidecars, runs tests, creates seal commit + the
    method-decision-register follow-up commit.

---

## 7. ODD §2.5 reverse-trace audit (pre-seal)

Every behaviour in the diff must trace back to AC.M.1–AC.M.S.
Audit checklist:

- `mcp_memory_client.py` → AC.M.1 + AC.M.3 (every fail-soft branch).
- `stop_emitter.py.cli_stop` → AC.M.4.
- `stop_emitter.py.handle_stop_envelope` recovery branch → AC.M.5.
- `stop_emitter.py.handle_stop_envelope` empty/malformed branches → AC.M.9.
- `stop_emitter.py.handle_stop_envelope` dedupe branch → AC.M.8.
- `stop_emitter.py.cli_stop` Popen detach → AC.M.7.
- `stop_emitter.py.cli_memory_write` → AC.M.6 + AC.M.10.
- `cli.py` subparsers → infrastructure for AC.M.4 / AC.M.6.
- `_default_memory_client_factory` body → AC.M.1, AC.M.2.
- `merge_stop` + `_is_pos_v2_owned_stop` → AC.M.11.
- `_persona_stop_stanza` + `_maybe_merge_stop` + 3 call sites →
  AC.M.11.
- All test files → corresponding AC names in their filename.
- pyproject.toml `mcp` dep → AC.M.1 (the live client needs to import).
- AC.M.12 verified by re-running pre-amendment test names.
- AC.M.13 IS this audit.
- AC.M.S verified by `test_no_sealed_amendments.py` plus the new
  `test_AC_M_S_seal_diff_window.py`.

No defensive `if`s without AC backing.

---

## 8. Halt conditions monitored

Plan §8 (1–9) + the dispatcher's additions:

- ODD violation in surrounding code I would inherit → halt.
- Required source edit outside fence → halt.
- AC cannot be outcome-shaped → halt.
- Test fixture cannot be deterministic → halt.
- Stop-hook empirical shape diverges materially from research §
  → halt (D10 caveat).
- Live MCP client construction fails for unanticipated reason → halt.
- `pos-amend apply --dry-run` red → halt.

No `git commit --amend`. Corrective NEW commits if any file misses.
