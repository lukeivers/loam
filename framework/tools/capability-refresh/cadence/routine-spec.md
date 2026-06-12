# Cadence binding — cloud routine spec (PRIMARY; activation OWNER-GATED)

> **Status: SPEC ONLY — no routine has been created.** Live activation of
> any persistent unattended automation is owner-gated (dispatcher gate
> 2026-06-11; precedent: the refusal-watchdog persistence ruling,
> `2026-06-11-refusal-watchdog-persistent-service-keep.md` — persistent
> unattended automation gets the owner's explicit word before it is
> switched on). Activation is the single documented step below.

## D-CUR.2 — why a cloud routine (verified live 2026-06-11)

Verified against `https://code.claude.com/docs/en/routines` (fetched
2026-06-11) + the in-session `/schedule` skill:

- Routines run on **Anthropic-managed cloud infrastructure** — no local
  machine awake. The failure mode that birthed this slice ("the refresh
  that never ran") is exactly the laptop-asleep failure launchd inherits.
- Available on **Pro/Max plans** with Claude Code on the web enabled —
  the subscription path; **no API key** (constraint corpus).
- Schedule triggers support cron expressions (min interval 1 hour) —
  the locked cadence classes (daily / weekly) fit comfortably.
- Repo write path: the routine selects the `lukeivers/loam` repository
  via the owner's own GitHub connection. Default branch permissions push
  to **`claude/`-prefixed branches only** — refresh commits arrive as a
  reviewable branch/PR rather than direct-to-main. That default is the
  recommended setting (a second protection layer on top of the D-CUR.4
  partition); "Allow unrestricted branch pushes" is NOT required.
- Limits: routines draw down subscription usage like interactive
  sessions; a daily per-account run cap applies (two short runs/day fit).

Fallback: launchd (plists in `launchd/`, proven in this stack). Ruled
out: session-cron (`/loop` / CronCreate) — session-only; an unattended
cadence cannot depend on a live session.

## The two routines (one per locked cadence class)

### 1. `capability-refresh-daily` (high-velocity sources)

- **Schedule:** daily, 06:30 America/Chicago.
- **Repository:** `lukeivers/loam`, default (`claude/`-prefix) branch
  permissions.
- **Prompt:**

  ```
  Run the deterministic capability-corpus refresh for the high-velocity
  cadence class and commit the result.

  Steps:
  1. python3 -m pip install -e framework/tools/capability-refresh/ --quiet
     (or: PYTHONPATH=framework/tools/capability-refresh/src)
  2. capability-refresh --cadence-class high-velocity
     (equivalently: python3 -m capability_refresh --cadence-class high-velocity)
  3. If the run changed files under docs/capability-corpus/, commit them:
     git add docs/capability-corpus/ && git commit -m "chore(corpus): scheduled capability refresh (high-velocity)"
  4. Do NOT edit anything by hand: the refresh tool's output is the whole
     change. Do NOT touch docs/capability-corpus/best-practice/. If the
     tool exits 3 (cross-class-write refusal) stop and report the error.
  ```

### 2. `capability-refresh-weekly` (long-form sources)

- **Schedule:** weekly, Sunday 07:00 America/Chicago.
- Same repository, permissions, and prompt with
  `--cadence-class long-form` and commit message
  `chore(corpus): scheduled capability refresh (long-form)`.

`on-merge` sources (Class A-prime, e.g. `harness/scope-of-work.md`) are
declared as data in `sources.yaml` but are NOT cron-bound — the locked
cadence table binds them to a merge-time trigger (future work; they can
be refreshed manually any time with `--cadence-class on-merge`).

## Activation (the owner-gated single step)

From an interactive Claude Code session in this repo, run `/schedule`
once per routine and paste the corresponding block above:

```
/schedule create the capability-refresh-daily routine exactly as specified in
framework/tools/capability-refresh/cadence/routine-spec.md
```

(then the same for `capability-refresh-weekly`). See `ACTIVATION.md` for
the launchd fallback's one-command activation.
