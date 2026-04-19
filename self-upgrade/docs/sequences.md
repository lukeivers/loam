# Sequence Diagrams

ASCII sequences for the three canonical flows.

## Happy path (require_confirmation mode)

```
User       CLI           Orchestrator    Substrates    Persona Channel
 |          |                 |              |              |
 |          |                 |              |              |
 |          |-- read cfg ---->|              |              |
 |          |   (auto_update_mode=require)   |              |
 |          |                 |              |              |
 |          |-- notify "upgrade <tag> available" -->  [Eve → Luke]
 |                                                          |
 |                                             reply("yes") |
 |          |<---------------- wait_for_confirmation -------|
 |          |                 |              |              |
 |          |-- pre_snapshot -|------------->|              |
 |          |   (all substrates byte-copied to -pre/)       |
 |          |                 |              |              |
 |          |-- pre_probe ----|-- probe ---->|              |
 |          |                 |   (each sealed surface)     |
 |          |                 |              |              |
 |          |-- pause_activation("upgrade:<tag>") --------->|
 |          |                 |                             |
 |          |-- wait_for_drain() -- bounded 30s             |
 |          |                 |                             |
 |          |-- SIGTERM pid ->|                             |
 |          |   (orchestrator exits gracefully)             |
 |          |<--- pid exits ---                             |
 |          |                                               |
 |          |-- os.replace(current → staging/<tag>)         |
 |          |   (atomic symlink swap)                       |
 |          |                                               |
 |          |-- launchctl kickstart gui/$UID/com.pos.orchestrator
 |          |                                               |
 |          |-- wait_for_boot (is_orchestrator_up polling)  |
 |          |<------- orchestrator booted -------           |
 |          |                                               |
 |          |-- no_op_rpc()  -------------> orchestrator    | (clause a)
 |          |-- build_survival_payload ---> primary-persona | (clause b)
 |          |-- memory.upgrade.compare() -> memory-system   | (clause c)
 |          |-- assert_no_drift         --> scope + objective| (clause d)
 |          |-- manifest.silent_schema_bumps()              | (clause e)
 |          |-- pre-snapshot exists                         | (clause f)
 |          |-- sha_verify manifest.files                   | (clause g)
 |          |                                               |
 |          |   all clauses pass                            |
 |          |-- write <tag>-accepted.json                   |
 |          |-- emit pos.upgrade.accepted span              |
 |          |-- resume_activation()         --> orchestrator|
 |          |-- notify "upgrade <tag> accepted in 38.4s" -->[Eve → Luke]
 |          |                                               |
 |<- exit 0 |                                               |
```

## Clean-failure rollback (e.g. memory drift)

```
User       CLI           Orchestrator    Substrates    Persona Channel
 |          |                 |              |              |
 ... pre-snapshot, pre-probe, swap, orchestrator restart OK ...
 |          |                                               |
 |          |-- memory.compare() -> DriftReport(passed=False)|
 |          |                                               |
 |          |   clause c FAILED                             |
 |          |-- rollback:                                   |
 |          |    1. os.replace(current → prior release dir) |
 |          |    2. restore every substrate from -pre/      |
 |          |    3. launchctl kickstart (prior tree)        |
 |          |-- emit pos.upgrade.rolled_back span           |
 |          |-- write <tag>-rolled-back.json                |
 |          |-- notify "rolled back: clauses [c]" -------->[Eve → Luke]
 |          |-- resume_activation()                         |
 |          |                                               |
 |<- exit 1 |                                               |
```

## Conflict reporting flow (clause g structural)

```
User       CLI           Disk
 |          |              |
 |--pos upgrade <tag>----->|
 |          |              |
 |          |-- detect_conflicts(manifest, live_root)
 |          |   user has locally edited framework/memory/upgrade.py
 |          |   live_sha != expected_pre_sha AND != expected_post_sha
 |          |              |
 |          |-- write <tag>-conflicts.yaml (summary: 1 pending)
 |          |              |
 |<-- exit 3, print path ---
 |                         |
 |   (user opens YAML; tries resolution: skipped)
 |                         |
 |--pos upgrade <tag>----->|
 |          |-- load_conflict_report(path) -> ValidationError:
 |          |   "resolution 'skipped' is structurally forbidden"
 |                         |
 |   (user sets resolution: accept-upstream)
 |                         |
 |--pos upgrade <tag>----->|
 |          |-- load_conflict_report: schema valid
 |          |-- no pending → proceed with upgrade
 |          |              |
 |          ... (normal upgrade sequence) ...
```

## Rollback-failed path (prototype-only runbook)

```
... rollback step fails (e.g. snapshot missing, disk full) ...
 |          |                                               |
 |          |-- RollbackFailed raised                       |
 |          |-- write <tag>-rollback-failed.json            |
 |          |-- emit pos.upgrade.rollback_failed span       |
 |          |-- notify "UPGRADE FAILED AND ROLLBACK FAILED" |
 |          |   (Tier 1, one-on-one channel)                |
 |<- exit 4 |                                               |
 |                                                          |
 (Manual: user inspects the history json, runs
  scripts/destructive_test_runbook.sh's recovery section.
  No auto-retry. No auto-recovery. The framework never
  claims success it has not verified.)
```
