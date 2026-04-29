# Retirement — user-facing reference

## When a persona is retired

Four reasons are valid:

- **`user_initiated`** — the user said to retire this persona
  (e.g. "retire sip"). This is the most common case.
- **`never_acknowledged`** — a pending-introduction persona was
  introduced and never acknowledged over a long window. This
  reason exists for housekeeping — by default the retire-window
  is indefinite (Luke's decision) and this reason is used only
  when workspace policy explicitly schedules a housekeeping
  sweep.
- **`workspace_policy`** — a workspace-level rule retired the
  persona (e.g. "retire all personas not addressed in 180 days").
  Workspaces that want this policy implement it outside this
  layer; the layer provides the machinery and the audit event.
- **`superseded`** — the persona has been replaced by a better-
  authored one.

## What happens to a retired persona

1. The directory `personas/<handle>/` moves to
   `personas/_retired/<handle>-<timestamp>/`. Contents are byte-
   identical.
2. The active loader ignores `_retired/*` — retired personas never
   appear in `loader.load()` results.
3. An OTel event `loam.persona.retired` fires with the handle and
   the reason.
4. Memory and scope-of-work references to the retired handle
   continue to resolve via the preserved directory — a historical
   scope owned by `sip` still has a resolvable context even after
   sip is retired.

## Un-retiring a persona

Un-retirement is deliberately manual. A retired persona cannot
reload itself without an explicit `mv`:

```bash
mv workspace/personas/_retired/sip-20260417T143000Z \
   workspace/personas/sip
```

After this move, `loader.load_one("sip")` succeeds again. The
contract's `is_addressable` flag is preserved from before
retirement — if the persona was fully addressable pre-retirement,
they are so again after un-retirement. (This is an intentional
choice: retirement does not re-introduce; un-retirement is a
user-directed restore.)

## Retire instructions in introductions

Every introduction dispatched through `IntroductionDispatcher`
includes a retire instruction by default:

> If that doesn't sound right, reply "retire `<handle>`" and I will
> move them out of the active roster.

Workspaces can override the phrasing by passing
`retire_instruction=` to `dispatcher.introduce(...)`.

## Guarantees

- A retired persona cannot send any message (the introduction
  guard catches this on the send path; the loader catches it on
  the load path).
- Retirement is idempotent: a second `retire_persona` call on the
  same handle raises `FileNotFoundError` because the source
  directory is already gone.
- Retirement timestamps are UTC, formatted `YYYYMMDDThhmmssZ` so
  sorting by directory name sorts chronologically.
