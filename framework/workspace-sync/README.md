# workspace-sync

**Role.** Pull canonical changes into a downstream loam workspace
clone (e.g. pos3) under Architecture B (per-workspace embedded
framework, locked 2026-04-26). Companion to `self-upgrade/` which is
the canonical-only A-mode mechanism.

**Operator-visible verbs.**

```
pos-sync --canonical <path> [--ref <commit-or-tag>] \
         [--workspace <path>] [--dry-run] [--auto-accept]

pos-workspace-sync ...   # alias
```

**Three-class workspace-data envelope.** Each path under the
workspace is classified by `<workspace>/.pos/sync-protected.yaml`:

- **Class A — workspace state.** Never overwritten. Examples:
  `personas/<handle>/contract.yaml`, `.pos/objective_tracker.sqlite`,
  `.pos/**`, `.scratch/**`, `.mcp.json`. The framework floor is
  Pydantic-validated; a workspace cannot remove floor entries.
- **Class B — operator preference.** Workspace-modified wins;
  canonical wins on untouched paths. Example: `memory.yaml`.
- **Class C — framework code.** When both sides changed, the LLM
  resolver (via `claude -p`) decides; verdict + rationale +
  confidence land in the audit.

**Audit + state.** Each sync run writes:

- `<workspace>/.pos/sync/<ref>/audit.yaml` — every conflict's
  resolution + rationale + confidence (sortable low-confidence-first).
- `<workspace>/.pos/sync/state.yaml` — convergent-idempotency
  record; re-runs no-op when the same ref is already applied.

**Salvage attribution.** ~70% of workspace-sync's primitives lift
from `self-upgrade/src/self_upgrade/` (clause-(h) salvage). All
lifts are by file-copy (Hard Constraint #1: NO edits to
`self-upgrade/`). Vendoring under `workspace_sync._resolver_client`
mirrors `tools/upgrade-merge-resolver/` for the `claude -p`
subprocess wrap without runtime dependency on self-upgrade.

**See also.**

- Component-level design notes: `docs/components/workspace-sync.md`
