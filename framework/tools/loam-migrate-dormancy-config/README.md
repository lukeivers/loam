# loam-migrate-dormancy-config

One-shot per-host migration helper relocating dormancy's
config-files inside `~/.loam/` after the M1f
graceful-degradation → dormancy rename:

- `~/.loam/degradation.sqlite` → `~/.loam/dormancy.sqlite`
  (with WAL + SHM siblings).
- `~/.loam/degradation-config.yaml` → `~/.loam/dormancy-config.yaml`.

## Usage

```bash
.venv/bin/python -m loam_migrate_dormancy_config
# or, after editable install:
.venv/bin/loam-migrate-dormancy-config
```

## Contract

Per-file four-case logic (sqlite + yaml independently):

1. **OLD_EXISTS_NEW_ABSENT** — rename. Single `os.rename()` per file
   pair. For the SQLite case, WAL/SHM siblings (`*-wal`, `*-shm`)
   rename concurrently if present; missing siblings are tolerated.
2. **NEW_EXISTS_OLD_ABSENT** — already migrated; no-op.
3. **NEITHER** — nothing to migrate; no-op (fresh machine).
4. **BOTH** — conflict; halt without modification per file; surface
   guidance.

The helper is idempotent: case-1 followed by re-run hits case 2.
Running it after a case-4 halt produces case 4 again on the same
file pair until the user resolves the conflict manually.

## Exit codes

- 0 on cases 1, 2, 3 (clean exit) for both files.
- 2 if either file pair hits case 4 (conflict).

## See also

- `framework/tools/loam-migrate-host-config/` — the M1b precedent
  (directory rename `~/.pos/` → `~/.loam/`).
- `framework/tools/loam-migrate-launchd-labels/` — the M1c precedent
  (launchd-label rebrand).
- `docs/rebuild/plans/oss-v0-1-0-publish-rename-1f.md` — M1f sub-plan
  AC.RNM-1f.5.
