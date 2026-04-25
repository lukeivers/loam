# Orphan launchd plist cleanup tool — build plan

Dev-discipline tooling, NOT a sealed-component amendment cycle. Lives
under `tools/` per the convention established by `tools/pos-amend/`.
No `pos-amend` manifest. No seal commit. No SEAL_COMMIT sidecar bumps.
Standard `git commit` for the tool itself.

## Why this exists

Amendment #6 (`namespaced-labels-and-bootout`) introduced workspace-
slug-namespaced launchd labels for pos-v2 services, e.g.
`com.pos-v2.<slug>.<kind>`. Hosts that ran pos-v2 *before* #6 may
still carry the older plists with single-segment label shape — e.g.
`com.pos-v2.memory-graphiti.plist` or `com.pos.orchestrator.plist`.
Those orphans are real:

- Observed 2026-04-23 in the pos3 first-run session: an orphan
  `~/Library/LaunchAgents/com.pos-v2.memory-graphiti.plist` was loaded
  and bound port 8765, satisfying the new workspace's health probe
  falsely. Documented in `docs/rebuild/POST_FIRST_RUN_REVIEW.md`
  entry #4.
- The amendment #6 seal narrative also names the pre-#6 hard-coded
  shapes `com.pos.orchestrator` and `com.pos-v2.memory-graphiti`.

This tool detects those orphans and remediates them reversibly.

## Objective

A CLI tool exists under `tools/orphan-plist-cleanup/` that, on a macOS
host, identifies pre-amendment-#6 orphan pos-v2 launchd plists in
`~/Library/LaunchAgents/`, lists them in dry-run mode, and in apply
mode booted-out and renames them aside to `*.orphan-disabled.bak`
(reversible). Idempotent. Refuses to act on plists carrying a
workspace-slug-namespaced label.

## Constraints

- **Reversibility class:** fully reversible. Plists are *renamed*,
  never deleted. The user can restore by renaming `.orphan-disabled.bak`
  back to `.plist` and `launchctl bootstrap` it.
- **Dependency fence:** no sealed-component source touches. No
  imports from any sealed component. Stdlib + `PyYAML` only if
  needed (likely not — plists are XML, label discovery is via filename
  pattern; we don't have to parse plist contents to determine
  orphan-ness).
- **Authority bound:** macOS-only. Other platforms refused with a
  clear error. The builder may decline to support `~/Library/
  LaunchDaemons/` (system-scope) — orphans there require root, are
  out of scope for this dev-discipline tool, and pos-v2 services
  install to the user-scope `~/Library/LaunchAgents/` per amendment
  #6.
- **Fail-closed direction:** when uncertain (e.g. label shape doesn't
  match either expected form), leave the plist alone and report it
  as "skipped — unrecognised shape." Never act on doubt.
- **Forbidden surfaces:** no `rm`, no `unlink` on plists; no edits
  to plists matching `com.pos-v2.<slug>.<kind>.plist` (3-segment-
  after-prefix shape — these belong to live workspaces).
- **Budget:** one commit (or small ordered series). Single
  background-agent dispatch worth of work.

## File layout

```
tools/orphan-plist-cleanup/
  pyproject.toml              # package metadata + console_scripts entry
  README.md                   # one-page usage overview
  src/orphan_plist_cleanup/
    __init__.py               # package marker + __version__
    __main__.py               # `python -m orphan_plist_cleanup`
    cli.py                    # argparse + dispatch
    detector.py               # filesystem scan + label classification
    remediator.py             # bootout + rename-aside (apply mode)
    launchctl.py              # subprocess wrapper for launchctl bootout
  tests/
    __init__.py
    conftest.py               # fixture LaunchAgents dirs in tmp_path
    test_detector.py          # AC1, AC5
    test_dry_run.py           # AC2
    test_apply.py             # AC3
    test_idempotent.py        # AC4
    test_platform_refusal.py  # AC6
```

## Acceptance criteria (outcome-shaped)

Each AC is paired with the test file that verifies it.

**AC1 — Orphan detection by label-pattern.**

Given an `~/Library/LaunchAgents/`-shaped directory containing plist
files whose filenames follow either of the pre-#6 shapes
(`com.pos-v2.<single-segment>.plist` or `com.pos.<single-segment>.plist`,
where `<single-segment>` contains no embedded dots), the detector
returns those filenames as orphans. Plist files whose filenames are
`com.pos-v2.<slug>.<kind>.plist` (workspace-slug-namespaced, two
segments after the `com.pos-v2.` prefix) are not returned. Files
that do not match either pos-v2 shape (e.g. `com.apple.*.plist`,
unrelated user plists) are not returned.

→ verified by `tests/test_detector.py`.

**AC2 — Dry-run lists, does not mutate.**

When invoked as `orphan-plist-cleanup --dry-run`, the tool prints the
list of detected orphan plists to stdout (one per line, with the
absolute path) and exits 0. No `launchctl bootout` is invoked, no
files are renamed, no files are deleted. Running dry-run twice on
the same host produces identical output.

→ verified by `tests/test_dry_run.py`.

**AC3 — Apply mode boots out and renames aside.**

When invoked as `orphan-plist-cleanup --apply` (or whatever the
builder chooses as the apply flag), for each detected orphan plist:

1. The tool invokes `launchctl bootout gui/<uid>/<label>` for the
   orphan's label.
2. The tool renames the orphan plist file to a sibling with suffix
   `.orphan-disabled.bak` (the original `.plist` extension is
   replaced wholesale, not appended-after).
3. The tool reports the action to stdout.

The plist file is never `rm`'d. The renamed file remains on disk.
A failed `launchctl bootout` is non-fatal *only* on the
"service-not-loaded" stderr variant (consistent with amendment #6's
ServiceManagerRunner.bootstrap policy); other failures abort the
remediation for that plist and the file is not renamed.

→ verified by `tests/test_apply.py` (mocking the launchctl
subprocess boundary).

**AC4 — Idempotent on re-run.**

Running `--apply` a second time on the same host (after the first
apply succeeded) detects no orphans (because they have been renamed
to `.orphan-disabled.bak` and no longer match the orphan filename
pattern), takes no action, and exits 0. No errors. No double-
action. Same outcome for `--dry-run` after apply.

→ verified by `tests/test_idempotent.py`.

**AC5 — Workspace-slug-namespaced plists are not touched.**

A plist named `com.pos-v2.alpha.orchestrator.plist` (workspace-slug-
namespaced — three segments after `com.pos-v2.`, where the third
segment is the kind) is never returned as an orphan, never booted-
out, never renamed, never produces a warning that suggests it might
be stale. Positive guard.

→ verified inside `tests/test_detector.py` (the negative-case half
of AC1).

**AC6 — macOS-only; other platforms refuse loudly.**

When invoked on a non-Darwin platform, the tool exits with a non-
zero status and a single line on stderr naming the platform and the
fact that this tool is macOS-only. No filesystem reads of `~/Library/
LaunchAgents/` are performed (which would be a no-op anyway on Linux
but would mask the platform-mismatch signal).

→ verified by `tests/test_platform_refusal.py`.

## Method (advisory; the builder refines)

Suggested shape, not prescriptive:

- `detector.classify_filename(name: str)` returns one of
  `OrphanV2 | OrphanV1 | NamespacedV2 | NotPosV2`. Pure function on
  the filename. Test-shaped.
- `detector.scan(launch_agents_dir: Path)` walks the directory and
  yields the `OrphanV2 | OrphanV1` filenames it finds.
- `remediator.bootout_and_rename(path: Path)` performs the apply-mode
  side-effect for one plist; depends on `launchctl.bootout(label)`.
- `launchctl.bootout(label)` is a thin subprocess wrapper that the
  tests mock. Stderr-pattern recognition for "service not loaded"
  lives here.
- The CLI plumbs detect → (dry-run print | apply loop), with
  `--dry-run` as the default safe-mode and an explicit `--apply` to
  perform mutation.

## Halt triggers

1. ODD break — the work cannot be completed within the ACs above
   without prescribing method in the contract or smuggling code that
   no AC names.
2. Tool requires sealed-component code edits. (Should not happen —
   this tool is wholly outside sealed-component territory.)
3. Discovery of orphan classes beyond launchd plists — orphan
   `~/.pos/` residuals, orphan kuzu DBs, deprecated config keys, etc.
   File a finding in `docs/rebuild/POST_FIRST_RUN_REVIEW.md` (or a
   new entry there) and halt rather than expanding scope.
4. A test cannot be written deterministically (e.g. requires a real
   keychain, a real loaded launchd service, a real workspace bind).
   Halt and signal — that's a sign the AC needs re-shaping.

## Validation

- `pytest tools/orphan-plist-cleanup/tests/ -q` passes (each AC's
  test file green).
- `tools/orphan-plist-cleanup/` is `pip install -e`-able and the
  console script `orphan-plist-cleanup` is registered.
- Manual smoke (the builder's call): on the dev host, `--dry-run`
  reports the same kind of orphan that pos3 saw 2026-04-23, with
  zero false-positives against the live workspace's slug-namespaced
  labels.

## Commit shape

Single `git commit` (or small ordered series) under `tools/orphan-
plist-cleanup/`. NOT an amendment commit. NOT a seal commit. No
`pos-amend` manifest. No SEAL_COMMIT sidecar bumps. Conventional
commit prose describing the new tool.

## Outcome match check (run at completion)

- Plan exists at this path. ✓ (this file).
- Each AC has a backing test file as listed above.
- Each test file's tests reference the AC by ID in a docstring or
  comment.
- No code path in the tool exists without an AC backing — reverse
  §2.5 check passes by inspection.
