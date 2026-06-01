# v1.0.0 HARD smoke writeup — the 1.0 release cut

**Date:** 2026-06-01. **Release:** v1.0.0 — owner-declared MAJOR over v0.14.0
(Luke, Telegram 13414: "calling this 1.0").
**Tree:** `/Users/lukeivers/loam` (main). **HEAD at smoke:** `3e007845`
(post-migration-declaration commit).
**Last published (Tier-0, git ref):** `v0.14.0` (tag on `origin/main`).
**Window:** `v0.14.0..HEAD`.
**`claude --version`:** `2.1.156 (Claude Code)`. **Subscription mode** — no
`ANTHROPIC_API_KEY`; no `anthropic` SDK (per `feedback_no_anthropic_api_key`).

**Aggregate verdict: GREEN.**

---

## §1 — Probe design (per `feedback_hard_smoke_per_minor_before_publish`)

**HARD bar:** a REAL cold-clone + a REAL editable install with no API key + a
REAL spawn-isolated `claude -p` (per
`feedback_spawned_claude_must_isolate_telegram_plugin` — `--strict-mcp-config`
+ empty `--mcp-config`, `ANTHROPIC_API_KEY` + `TELEGRAM_BOT_TOKEN` scrubbed) +
a real outcome-altitude exercise of the release's user-visible delta + the
touched-component test sweep.

The v1.0.0 cut is release-readiness, not new features. Its user-visible delta
over v0.14.0 is (1) the two newly-documented runtime verbs `loam guards`
(protection-matrix) and `loam migrate` (state-migration-engine) reaching their
1.0 component pages, and (2) the lockstep version bump producing 1.0.0
component metadata. Both are exercised from the cold install below at
outcome-altitude.

## §2 — F1 — Cold-clone + spawn-isolated `claude -p` subscription probe

**Probe invocation:**
```bash
rm -rf /tmp/v1-0-0-cold-clone
git clone -q /Users/lukeivers/loam /tmp/v1-0-0-cold-clone
cd /tmp/v1-0-0-cold-clone
env -u ANTHROPIC_API_KEY -u TELEGRAM_BOT_TOKEN bash -c \
  'echo "What is 2+2? Answer in one short sentence." | timeout 120 \
   claude -p --strict-mcp-config --mcp-config "{\"mcpServers\":{}}" \
   --output-format text'
```

**Verdict: GREEN.** Clone HEAD = `3e007845`. Output: `4.` Exit 0. Single short
sentence. Spawn-isolated via `--strict-mcp-config` + empty `--mcp-config` (no
Telegram bot-slot steal — the live MCP connection was not killed); env scrubbed
of both `ANTHROPIC_API_KEY` and `TELEGRAM_BOT_TOKEN` (subscription-only).

## §3 — F2 — Cold editable install + outcome-altitude verb exercise

The real cold install — the exact failure the HARD smoke exists to catch (a
fresh clone that doesn't actually install / doesn't produce working verbs).

**Probe:**
```bash
cd /tmp/v1-0-0-cold-clone
python3.13 -m venv .venv
.venv/bin/python -m pip install -q -r install-from-source.txt
.venv/bin/loam guards
.venv/bin/loam migrate --dry-run
.venv/bin/python -m pip show loam-protection-matrix loam-state-migration-engine loam-init
```

**Verdict: GREEN.** Install exit 0 (full editable graph from
`install-from-source.txt`, including the `protection-matrix` +
`state-migration-engine` install-graph lines the health-check added).

- **`loam guards` (protection-matrix verb):** produced a real
  protection-pillar coverage report — `rows: 18 (16 floor-class)`, per-failure-
  mode `[ok]`/`[GAP]` status against the live tree. Exit 0. The newly-page-
  documented verb works from a cold install at outcome-altitude (no
  pre-arranged state).
- **`loam migrate --dry-run` (state-migration-engine verb):** registered + reached
  the replay engine. It raised `MigrationOrderError` naming 10 **pre-existing**
  unstamped migration files (see §6 finding) — this is the engine correctly
  refusing to order release-version-less migrations, NOT a v1.0.0 regression
  (my `v1-0-0-release-cut.migration.yaml` is the FIRST stamped file). The verb
  itself installs + dispatches correctly.
- **Installed component versions:** `loam-protection-matrix` 1.0.0,
  `loam-state-migration-engine` 1.0.0, `loam-init` 1.0.0 — the lockstep bump
  produced honest 1.0.0 metadata at install time.

## §4 — F3 — Touched-component test suites

Run from the canonical tree (separate `pytest` invocations per component to
avoid the pre-existing shared-`conftest.py` `ImportPathMismatchError`).

| Component | Result | Notes |
|---|---|---|
| `framework/protection-matrix/tests/` | **33 passed, 0 failed** | `loam guards` engine + catalogue |
| `framework/state-migration-engine/tests/` | **13 passed, 0 failed** | `loam migrate` schema + replay + cursor |
| `framework/hands-off-lifecycle/tests/` | **726 passed, 7 skipped, 0 failed** | includes D.1 byte-content 16/16 post-rebaseline |
| `framework/primary-persona/tests/` | **green, 0 failed** | D.1-sampled pyproject component |
| `plugins/dev-sdlc/tests/` | **274 passed, 7 skipped, 0 failed** | lockstep 5/5 + the sealed doc-accuracy amendment's seal-test |

**Verdict: GREEN.** No failures in any touched-component suite. The 7 skips in
dev-sdlc are pre-existing (Python-version-gated).

## §5 — F4 — Spawn-isolation + no-API-key invariants

- **Spawn-isolation:** every `claude -p` in this smoke ran with
  `--strict-mcp-config` + empty `mcpServers` (F1). No un-isolated `claude -p`
  spawn introduced in the window.
- **No-API-key:** `ANTHROPIC_API_KEY` unset throughout; the cold-clone probe
  explicitly scrubbed it (`env -u`). Subscription-only path proven.
- **Boundary:** the cold install wrote only into `/tmp/v1-0-0-cold-clone/.venv`
  (an admitted carve-out); no framework write to user-state outside a home
  (release gate 9 verifies this structurally).

**Verdict: GREEN.**

## §6 — Surfaced findings (F2 ruthless feedback — NOT smoke blockers)

1. **`loam migrate` cannot replay the unstamped historical migration corpus
   (PRE-EXISTING).** 10 of the 11 `docs/state-migrations/*.migration.yaml`
   files carry no `version:` stamp (they are scope-descriptive-slug-keyed per
   `feedback_version_numbers_at_release_time`). `loam migrate` refuses to order
   them (`MigrationOrderError` — "an unstamped pending migration is a
   release-time gap"). v1.0.0's own declaration IS stamped; this is the
   accumulated gap from 10 prior slices that shipped without a release-time
   version stamp. Release gate 7 only checks declaration PRESENCE (GREEN), so
   this does not block v1.0.0 — but the `loam migrate` verb is not usable
   end-to-end against the real corpus until the historical files are stamped.
   Recommend a follow-on stamping pass (back-fill each slice's release-version
   stamp from STATE/roadmap). Owner-gated; not 1.0-blocking.

2. **5 pre-existing `loam-amend` test failures (PRE-EXISTING, unrelated).**
   `plugins/dev-sdlc/tools/loam-amend/tests/` carries 5 failures, all rooted in
   one pre-existing committed manifest
   (`docs/plans/session-clear-safety-tracker-register-and-first-run-update-parity.manifest.yaml`,
   committed `26fd2e5a`) whose `smoke_outcome` field is 575 chars (cap 200).
   The schema-corpus-sweep meta-tests catch it. Unrelated to v1.0.0; not in any
   release gate's path. Recommend a one-line manifest trim follow-on.

3. **D.1 pyproject-byte pin recurrence (FOURTH).** The lockstep bump again
   invalidated the primary-persona + scope-of-work pyproject SHAs pinned in
   `test_d1_byte_content_match.py`. Rebaselined in-band (16/16 GREEN). The
   root-cause structural fix (exclude pyproject.toml from the byte-content
   sample — they MUST mutate every MINOR/cut by design) remains OWED.
