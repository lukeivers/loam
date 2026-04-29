# Architecture

The framework is one Python package (`self_upgrade`) organised around
a single control flow: the external `pos upgrade <tag>` CLI that
drives a sequence of side effects against the sealed components and
their substrates.

## Module layout

```
self_upgrade/
├── cli.py                 # pos upgrade / pos rollback / pos status
├── upgrade.py             # execute_upgrade() — the full sequence
├── rollback.py            # whole-upgrade atomic rollback
├── manifest.py            # pos-release.yml schema (D1)
├── conflict_report.py     # <tag>-conflicts.yaml schema (D7)
├── conflict_detection.py  # pre-install sha-diff → conflict report
├── snapshot.py            # substrate file-copy snapshots (D3)
├── probes.py              # adapters to each sealed component (D4)
├── aggregator_probes.py   # framework-owned aggregator probe set
├── clause_checks.py       # seven named (a)-(g) check functions (D6)
├── orchestrator_control.py# pause/drain/SIGTERM/swap/kickstart (D5)
├── notification.py        # primary-persona one-on-one channel
├── observability.py       # OTel span emission (v1.1 R11)
├── config.py              # UpgradeConfig / auto_update_mode
└── paths.py               # ~/.loam/* resolution
```

## System diagram

```
       +---------------------+       +-----------------------+
       |  pos upgrade <tag>  | <---- | ~/.loam/upgrade-config |
       |   (external CLI)    |       | (auto_update_mode...) |
       +---------+-----------+       +-----------------------+
                 |
                 v
   +-------------+-------------+
   |  execute_upgrade()        |
   |  ───────────────────────  |
   |  1. pre-snapshot (D3)     |---> ~/.loam/framework/history/<tag>-pre/
   |  2. pre-probe   (D4)      |---> pre-probe.json
   |  3. pause_activation      |---> orchestrator.pause_activation("upgrade:<tag>")
   |  4. drain (bounded)       |
   |  5. SIGTERM + pid wait    |---> orchestrator pid
   |  6. symlink swap (atomic) |---> ~/.loam/framework/current → staging/<tag>
   |  7. launchctl kickstart   |---> launchd user agent
   |  8. wait_for_boot         |
   |  9. post-probe + clauses  |
   | 10. accept or rollback    |
   +---------------------------+
         |                |
         v                v
   +----------+    +----------------+
   | accept   |    | rollback (D8)  |
   | (D9)     |    |  - symlink     |
   |  - OTel  |    |    revert      |
   |  - .json |    |  - substrate   |
   |  - notify|    |    restore     |
   |  - resume|    |  - restart     |
   +----------+    +----------------+
```

## Trust boundaries

- **Live orchestrator** — sealed. Framework only sends SIGTERM and
  reads its PID. No in-process calls; the framework is an external
  process by construction.
- **Sealed components' substrates** — written only by the component;
  the framework never modifies `orchestrator.sqlite` directly. The
  snapshot is a byte-copy; the restore is a byte-copy. No schema
  knowledge here.
- **Manifest + conflict report** — Pydantic-validated on every load.
  `skipped` is structurally impossible.
- **User channel** — the primary persona's one-on-one channel. The
  framework does not speak directly to the user; it sends messages
  through the persona layer.

## Failure modes and responses

| Failure | Response |
|---------|----------|
| Drain timeout | No swap attempted. Halt with `drain_timeout`. `resume_activation` called. User notified. |
| SIGTERM timeout | Rollback. No swap committed (symlink still at prior). `resume_activation`. |
| Symlink swap fails | Halt; framework is in prior state. Report to user. |
| Orchestrator boot timeout | Rollback; revert symlink; restart on prior tree. |
| Clause a-g fail | Rollback. `<tag>-rolled-back.json` written; `pos.upgrade.rolled_back` span emitted. |
| Rollback fails | `RollbackFailed` raised; `<tag>-rollback-failed.json` written; Tier 1 notification. Manual recovery. |
| Conflict pending | Upgrade blocks until YAML resolved. `resolution: skipped` is parse-rejected. |
| Silent schema bump | Clause (e) fails; rollback. |

## Tunables

Every timeout is configurable via `~/.loam/upgrade-config.yaml`:

```yaml
auto_update_mode: require_confirmation
drain_timeout_seconds: 30
sigterm_timeout_seconds: 30
orchestrator_boot_timeout_seconds: 60
cancel_window_seconds: 60
confirmation_timeout_hours: 24
launchd_label: com.pos.orchestrator
```
