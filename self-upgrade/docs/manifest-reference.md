# `pos-release.yml` — manifest reference (D1)

Every release ships a `pos-release.yml` declaring every file with
sha256, per-component schema versions, breaking changes, and ordered
migrations. Pydantic-validated at load; a malformed manifest refuses
to load with a clear error.

## Minimal example

```yaml
release_tag: pos-v2-v0.3.0
commit_sha: 7f3c1e4
files:
  - path: framework/self_upgrade/cli.py
    expected_pre_sha: a1b2c3...  # 64-hex
    expected_post_sha: d4e5f6...
    change_kind: modified
  - path: framework/self_upgrade/new_module.py
    expected_pre_sha: null
    expected_post_sha: 789abc...
    change_kind: new
  - path: framework/legacy/old.py
    expected_pre_sha: aaa111...
    expected_post_sha: null
    change_kind: deleted
component_schemas:
  - component: memory
    version_pre: 3
    version_post: 3
  - component: scope_of_work
    version_pre: 5
    version_post: 5
breaking_changes: []
migrations: []
generated_at: 2026-04-19T12:00:00Z
```

## Schema

### Top level (`Manifest`)

| Field | Type | Notes |
|-------|------|-------|
| `release_tag` | string | must start with `pos-v2-v` |
| `commit_sha` | string | 7+ hex chars |
| `files` | list\[FileEntry\] | every file tracked across the upgrade |
| `component_schemas` | list\[ComponentSchema\] | per-component pre/post versions |
| `breaking_changes` | list\[BreakingChange\] | may be empty |
| `migrations` | list\[Migration\] | ordered; orders must be unique |
| `generated_at` | string \| null | ISO-8601 UTC |

### `FileEntry`

| Field | Type | Notes |
|-------|------|-------|
| `path` | string | relative to framework root |
| `expected_pre_sha` | string\|null | 64-hex. null iff `change_kind=new` |
| `expected_post_sha` | string\|null | 64-hex. null iff `change_kind=deleted` |
| `change_kind` | enum | one of: `new`, `modified`, `deleted`, `unchanged` |

Validator enforces consistency: `modified` requires both shas and they
must differ; `unchanged` requires both shas and they must match;
`new` forbids pre-sha; `deleted` forbids post-sha.

### `ComponentSchema`

| Field | Type | Notes |
|-------|------|-------|
| `component` | string | identifier used by framework (e.g. `memory`) |
| `version_pre` | int | pre-upgrade schema version |
| `version_post` | int | post-upgrade schema version |

Any component whose `version_post != version_pre` MUST have a matching
entry in `breaking_changes`. Otherwise clause (e) fails and the
upgrade halts.

### `BreakingChange`

| Field | Type | Notes |
|-------|------|-------|
| `id` | string | unique identifier |
| `component` | string | which component |
| `description` | string | human-readable |
| `migration_path` | string | migration file path or procedure |

### `Migration`

| Field | Type | Notes |
|-------|------|-------|
| `id` | string | unique |
| `component` | string | which component owns it |
| `order` | int | evaluated ascending; must be unique |
| `entry` | string | `package.module:callable` reference |
| `description` | string | defaults to empty |

## Authoring workflow

1. Run tests on `pos-v2` branch; tag commit: `git tag pos-v2-v0.3.0`.
2. Generate shas: `find framework -type f -exec sha256sum {} \;`
3. Hand-author (or script) the YAML with those shas.
4. Validate: `python -c "from self_upgrade.manifest import load_manifest; load_manifest('pos-release.yml')"`
5. Attach to the release tarball at `pos-release.yml` (root).
