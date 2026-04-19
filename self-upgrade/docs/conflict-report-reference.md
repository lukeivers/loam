# Conflict report — `<tag>-conflicts.yaml` (D7)

Emitted at `~/.pos/framework/history/<tag>-conflicts.yaml` when
pre-install sha-diff finds any file whose local sha disagrees with
both the prior-release sha and the new-release sha.

## Structural rule

**`resolution: skipped` is not a valid value.** The `Resolution` enum
in `self_upgrade/conflict_report.py` explicitly omits `skipped`. A
YAML document that tries to use it fails Pydantic validation at
parse time:

```
ValidationError: resolution 'skipped' is structurally forbidden
(clause g: no silent skip). Choose one of:
pending, accept-upstream, keep-local, three-way-merge, abort.
```

This is clause (g)'s operational guarantee: there is no code path
that silently drops a change.

## Permitted resolutions

| Value | Meaning |
|-------|---------|
| `pending` | User has not decided. Upgrade blocks until resolved. |
| `auto-accept-local-matches-upstream` | Deterministic: local sha == new-release sha. Auto-set by `detect_conflicts`; user does not author this. |
| `accept-upstream` | Overwrite the local edit with the new release's version. Local content preserved at `~/.pos/framework/overrides/<tag>/<path>` for audit. |
| `keep-local` | Preserve the local edit; record a workspace override at this path so future releases know to reapply. |
| `three-way-merge` | User supplies a merged file (path in `resolved_content_path`). |
| `abort` | Cancel the upgrade. No state change. |

## Example

```yaml
upgrade_tag: pos-v2-v0.3.0
prior_tag: pos-v2-v0.2.0
detected_at: 2026-04-19T14:23:11Z
conflicts:
  - path: framework/memory_system/src/upgrade.py
    prior_release_sha256: a1b2c3...
    installed_sha256: d4e5f6...
    new_release_sha256: 789abc...
    change_kind: upstream_modified_and_local_modified
    three_way_diff_path: ~/.pos/framework/history/<tag>-conflicts/memory_upgrade.diff
    resolution: pending
  - path: framework/orchestrator/src/orchestrator.py
    prior_release_sha256: aaa111...
    installed_sha256: bbb222...
    new_release_sha256: bbb222...
    change_kind: local_modified_equals_upstream
    resolution: auto-accept-local-matches-upstream
summary:
  total_framework_files: 412
  unchanged: 398
  will_update_cleanly: 9
  conflicts_requiring_resolution: 1
  auto_resolved: 4
```

## Resolving a conflict

1. CLI exits with code 3 and prints the report path.
2. User opens `<tag>-conflicts.yaml`.
3. For each entry with `resolution: pending`:
   - Choose one of the permitted values.
   - For `three-way-merge`, write the merged content to a file and
     set `resolved_content_path` to that path.
4. User re-runs `pos upgrade <tag> --conflicts-from <path>`.
5. CLI loads the resolved YAML; schema re-validates; upgrade proceeds.

## Change-kind taxonomy

| Value | Meaning |
|-------|---------|
| `local_modified_only` | Local edit; no upstream change in this file. |
| `upstream_modified_and_local_modified` | Local edit collides with upstream change. |
| `local_modified_equals_upstream` | Local edit happens to match the new release. Deterministically auto-resolved. |
