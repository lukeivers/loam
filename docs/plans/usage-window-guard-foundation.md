# usage-window-guard — Slice 1 (foundation): real Anthropic rolling-window probe + parse + fail-open — plan

**Slug:** `usage-window-guard-foundation`
**AC prefix:** `AC.USG`
**Component:** `framework/usage-window-guard/` (NEW component — first seal)
**Plan author/builder:** build agent (loam tree, serialized)
**Owner greenlight:** Luke 13512 — non-tech-user USAGE-LIMIT GUARD MINOR, macOS-only v1, foundation slice.
**Design source:** `/Users/lukeivers/pos3/workspace/.scratch/claude-output/loam-nontech-usage-limit-guard-design.md` (Slice 1 = `usage-window-guard-foundation`, AC.USG.{1,5,S}).
**Methodology source (Tier-0 verified):** `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_real_claude_usage_oauth_endpoint.md`.

---

## §1 — Summary / TL;DR

The foundation slice of the non-tech-user usage-limit guard: a NEW loam
component that reads the user's REAL Anthropic-side rolling-window
utilization (the rolling 5-hour window + the 7-day weekly window) directly
from `GET https://api.anthropic.com/api/oauth/usage`, parses the
`{utilization, resets_at}` struct for each window, and **fails open** —
reporting "usage unavailable" rather than fabricating a percentage —
whenever the credential is missing/expired-and-unrefreshed or the endpoint
returns non-200 / is unreachable.

This slice is **probe + parse + fail-open ONLY**. Thresholds, the
plain-language warning copy, de-duplication, and hook wiring are explicitly
deferred to a tighter follow-on slice (design AC.USG.{2,3,4}).

**This is NOT token-counting.** `utilization` is Anthropic's server-side
percentage of the enforced cap. The component never counts a token, never
estimates cost, never reads a session JSONL. loam's `cost-governance`
(token/cost ceilings) is explicitly NOT the foundation and is untouched.

**The single load-bearing risk (Tier-0 measured):** the OAuth access token
rotates ~hourly. The probe therefore re-reads the keychain on **every** call
and treats a transient 401 / unreachable endpoint as fail-open. It never
caches the token across calls; it never persists or logs the token.

---

## §2 — Placement decision

NEW component `framework/usage-window-guard/`. Grep across `framework/` +
`docs/` found NO existing surface that reads `/api/oauth/usage` (the design
STEP 2 already established greenfield; re-confirmed at build time). The real
rolling-window read is a distinct capability that belongs in none of the
existing components:
- `cost-governance` is token/cost-based (the explicitly-rejected approach).
- `claude-p-client` is for LLM calls via `claude -p`, not keychain reads or
  REST probes.
- `observability-aggregator` consumes events; it does not source the cap read.

A new component is the clean boundary (doctrine §"How loam is built — in
layers").

Package: `loam.usage_window_guard` (matches the dashed-component →
underscored-package convention: `cost-governance` → `loam.cost_governance`).

---

## §3 — Halt-and-surface recorded DURING plan authoring

**SAL-1 — data-shape mismatch between the memory note and the live endpoint
(resolved, Tier-0).** The memory note (`feedback_real_claude_usage_oauth_endpoint.md`
line 16) documents a FLAT shape `{"five_hour": 8.0, "seven_day": 9.0,
"seven_day_reset": "..."}`. The LIVE endpoint (probed at build time, HTTP 200)
returns the NESTED shape the design's STEP 1 captured:
`{"five_hour": {"utilization": 18.0, "resets_at": "..."}, "seven_day":
{"utilization": 11.0, "resets_at": "..."}, ...}`. **Resolution:** parse the
NESTED shape (live ground truth Tier-0 beats the note's Tier-2 summary, per
information-trust-ordering). The note's flat example is a simplified earlier
capture; the design's nested capture matches live. AC.USG.1 pins the nested
shape. No owner gate needed — operational reality is unambiguous.

**SAL-2 — beta header is NOT required (design STEP 1, Tier-0).** The design
verified the endpoint works with or without `anthropic-beta:
oauth-2025-04-20`. The reference `usage_cap.sh` sends it. **Resolution:** send
the documented headers (`anthropic-beta` + `User-Agent: claude-cli`) to match
the verified-working recipe exactly — the brief's hard constraint is "do not
invent beyond the documented keychain+curl recipe," so I replicate the recipe
verbatim rather than dropping a header the design proved optional. Lower
divergence risk.

---

## §4 — Spec-objective placement (ladder-up)

Ladders to VALUE_PROPOSITION's two tests (the prime objective, per
`feedback_value_proposition_as_prime_objective`):
- **Primary-persona test:** a non-technical user has no model of "rolling
  5-hour window" or "weekly Max cap" until they're throttled mid-sentence.
  This foundation makes the REAL enforced numbers READABLE so a later slice
  can translate `utilization: 82.0` into plain language. The read is the
  load-bearing substrate of that translation.
- **Harness test:** adds a `usage_window.read()` capability the primary
  persona can invoke before launching heavy work. New toolkit entry.

Prime-directive tie (`feedback_loam_prime_directive_user_tuned_translation`):
the guard productizes the existing personal usage-monitor for non-tech users
— the WHAT ("don't surprise-throttle me") translated into the HOW (the real
endpoint read), customized per-user by a later adaptive slice (#34).

---

## §5 — Module shape (builder's contract; exact layout is builder's call per ODD §1.1)

```
framework/usage-window-guard/
  pyproject.toml                                  # loam-usage-window-guard; deps: (none beyond stdlib — keychain via subprocess, HTTP via urllib)
  src/loam/usage_window_guard/__init__.py         # public surface: read() + the result types
  src/loam/usage_window_guard/credential.py       # transient keychain read (AC.USG.1 token source; AC.USG.5 missing-credential fail-open)
  src/loam/usage_window_guard/probe.py            # the production entry-point: read() → HTTP GET → parse → UsageWindows | Unavailable
  src/loam/usage_window_guard/model.py            # Window / UsageWindows / UsageUnavailable result types (parse-only; no thresholds)
  tests/
    conftest.py                                   # (if needed) path/fixture wiring
    test_AC_USG_1_real_window_read.py             # AC.USG.1 — fixture HTTP 200 → parsed nested struct (source-identity)
    test_AC_USG_5_fail_open.py                    # AC.USG.5 — 401 / non-200 / unreachable / missing-credential → Unavailable, no number, no crash
    test_AC_USG_S_outcome_altitude_live_or_failopen.py  # ★ AC.USG.S — production read() entry-point, NO pre-arranged state, real endpoint OR real fail-open path
    test_no_secret_persistence.py                 # token never returned in result / never logged / never written (no-secrets discipline)
    test_no_token_counting.py                     # source-identity guard: value comes from the endpoint field, not any token sum
    test_no_sealed_amendments.py                  # NEW-component seal fence
    SEAL_COMMIT                                    # sidecar (created at seal)
  seals/SEAL_COMMIT.usage-window-guard-foundation # narrative target
```

**Method-level choices (builder's call per ODD §1.1):**

- **D-build.1 — token read = direct `security find-generic-password`
  subprocess** (mirrors the verified `usage_cap.sh` recipe; design D-USG.2
  preliminary). Read transiently inside the probe; never returned, never
  stored on `self`, never logged.
- **D-build.2 — HTTP via stdlib `urllib.request`** (no `requests`/`httpx`
  dependency — keeps the component dependency-light; the call is a single GET
  with three headers). A short timeout (≈10s) → timeout is treated as
  unreachable → fail-open.
- **D-build.3 — result is a sum type** (`UsageWindows` on success,
  `UsageUnavailable` on any failure) rather than raising. The caller can never
  accidentally read a fabricated number off an exception; the failure is a
  first-class, number-free value carrying a `reason` string for diagnostics.
- **D-build.4 — fail-open reasons are categorical** (`missing_credential`,
  `auth_rejected` (401/403), `endpoint_error` (other non-200),
  `unreachable` (network/timeout), `malformed_response`). None carries a
  fabricated utilization. The reason is for the later surfacing slice to say
  "usage unavailable" honestly.

---

## §6 — Acceptance criteria (outcome-shape; method-in-AC test passed on each)

### AC.USG.1 — real-window read (source-identity)
`read()` against a fixture HTTP 200 body (the live nested shape) returns a
`UsageWindows` carrying BOTH windows' `utilization` (float %) AND `resets_at`
(parsed timestamp): `five_hour` and `seven_day`. The value for each window is
sourced from that window's `utilization` field in the endpoint response — NOT
from any token count, cost estimate, or tally. Test: feed the recorded 200
body; assert both windows parsed with the exact field values; assert the
parse reads the `.utilization` / `.resets_at` keys of the named window object.

*Method-in-AC test:* can this be satisfied another way? Yes — any parser that
reads the named endpoint fields satisfies it; the AC does not pin urllib vs
requests vs the parse internals. Scope is tight (good).

### AC.USG.5 — fail-open on unreadable usage
For each of: (a) missing/empty keychain credential, (b) HTTP 401/403,
(c) other non-200 (e.g. 500), (d) unreachable endpoint / timeout,
(e) malformed/non-JSON 200 body — `read()` returns a `UsageUnavailable` value
that (1) carries NO utilization number, (2) does not raise, (3) does not block
or sleep indefinitely, (4) names a categorical reason. Test: drive each
failure mode via injected transports/credential sources; assert
`UsageUnavailable` with no numeric field and a reason; assert no exception
escapes.

*This is the information-trust-ordering AC: never confabulate a usage number.*

### ★ AC.USG.S — outcome-altitude (real probe, no pre-arranged state)
Invoke the PRODUCTION entry-point `read()` with NO pre-arranged in-test state
— no injected transport, no fixture credential, no monkeypatch of the
keychain or HTTP layer. The call reads the real keychain and hits the real
`https://api.anthropic.com/api/oauth/usage`. Assert the outcome is one of
exactly two real-code-path results: (1) a `UsageWindows` whose `five_hour` and
`seven_day` utilizations are real floats in `[0, 100]` with parsed
`resets_at`; OR (2) a `UsageUnavailable` with a categorical reason and NO
number (the genuine fail-open path, exercised through the real code, never a
stub of it). Either outcome PASSES; a fabricated number or an uncaught
exception FAILS. A STUB-class test (pre-seeded response) does NOT satisfy this
AC (`feedback_test_outcome_altitude_required`).

*Build-env note:* the live endpoint IS reachable in the build env (probed
HTTP 200 at plan time), so this test exercises the success branch live; if a
future run hits a rotated-out token, it exercises the fail-open branch through
the SAME real code path. Both are real; neither is a stub.

---

## §7 — Out of scope (deferred + when)

- **AC.USG.2** (threshold ladder + de-dup) — follow-on slice.
- **AC.USG.3** (plain-language surfacing contract) — follow-on slice.
- **AC.USG.4** (hook wiring — UserPromptSubmit / PreToolUse trip-point) — follow-on slice.
- **D-USG.4** (Linux `~/.claude/.credentials.json` file path) — owner set
  macOS-only for v1 (Luke 13512). Darwin keychain only this slice.
- The per-model weekly buckets (`seven_day_sonnet`, `seven_day_opus`) and the
  `extra_usage` overage block — present in the response, NOT parsed this slice
  (foundation needs only the two top-level windows). Parsing them is a
  natural follow-on addition, not dropped silently — recorded here.
- Pushing to origin — LOCAL seal only (owner-gated release later).

---

## §8 — Halt triggers (in-flight; abort the build + surface)

- The live endpoint requires anything beyond the documented keychain+curl
  recipe (a new header, a refresh dance, a different keychain service) →
  HALT, do not invent.
- The nested data shape differs from §6 AC.USG.1 at build time → HALT,
  surface the actual shape (information-trust-ordering).
- The seal fence shows any sealed-component path outside the declared fence →
  HALT (halt-signal condition).

---

## §9 — Bookkeeping (backfill at seal)

- NEW-component first seal → `framework/usage-window-guard/tests/SEAL_COMMIT`
  created at seal (no prior sidecar to advance).
- Narrative appended to
  `framework/usage-window-guard/seals/SEAL_COMMIT.usage-window-guard-foundation`.
- `loam amend apply` then `loam amend seal` (named per
  `feedback_dispatch_explicit_loam_amend_apply`).
- NEW commits only; never `--amend` (`feedback_no_amend_in_agent_dispatches`).
- LOCAL seal only; no push.

---

## §10 — F2 Ruthless Feedback (honest doubts + named risks)

1. **Token rotation is the real production risk (named, mitigated).** Measured
   ~1.1h expiry at design time. Mitigation: re-read keychain per call + fail
   open on 401. The component piggybacks on Claude Code's own refresh; it does
   NOT implement the OAuth refresh dance. If Claude Code hasn't refreshed and
   the token is expired → 401 → honest "unavailable." This is correct
   behavior, not a bug.
2. **Note-vs-live shape divergence (SAL-1) surfaced, not silently resolved.**
   The memory note's flat shape is stale relative to live; I parse live and
   record the divergence so the note can be corrected.
3. **macOS-only is an owner-set v1 constraint, not a capability ceiling.** The
   Linux file-path read is a known follow-on (D-USG.4), recorded so it isn't
   lost.

---

## §11 — Provenance trail

- `feedback_real_claude_usage_oauth_endpoint.md` — the endpoint + keychain recipe (Tier-0).
- `loam-nontech-usage-limit-guard-design.md` — the slice spec + ACs (owner-greenlit design).
- `usage_cap.sh` — the verified-working reference curl recipe.
- Live probe at build time — HTTP 200, nested shape, `five_hour: 18.0` / `seven_day: 11.0` (Tier-0).
- `framework/protection-matrix/` — the NEW-component manifest + seal-fence reference pattern.

---

## §12 — Summary of named decisions (owner-readable)

1. Parse the LIVE nested shape, not the note's flat shape (live Tier-0 wins).
2. Send the documented headers verbatim (replicate the verified recipe; don't drop the optional beta header).
3. Result is a number-free sum type (`UsageWindows` | `UsageUnavailable`) — fail-open is structurally impossible to misread as a number.
4. stdlib-only (urllib + subprocess) — dependency-light.
5. macOS keychain only this slice (owner-set v1).

---

## §13 — Forks for the dispatcher (none requiring a ruling)

No open forks. The design + owner greenlight + live verification resolve every
decision; the residual choices are method-level (builder's call). macOS-only,
thresholds-deferred, and shape-parsing are all settled.

---

## §14 — Method-decision record (builder, post-build)

(Backfilled at seal.)
