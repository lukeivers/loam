# plugins/dev-sdlc/odd-extractor

ODD reverse-engineering scaffold for loam — reads a foreign codebase,
emits a confidence-banded ODD contract draft, surfaces ambiguity for
ratification rather than fabricating ACs.

**Status:** v0.1.8 Cycle 1 (sealed-component discipline applies; the
dev-sdlc plugin's seal-test gates the entire `plugins/dev-sdlc/`
sub-tree, including this package). Cycle 1 ships the four-stage
workflow shape + language-adapter registry skeleton; Cycles 2-4 ship
confidence bands, ratification workflow, Ruby/Rails first-class
adapter, Python first-class adapter.

**Plan-docs:**

- v0.1.8 master plan: `docs/rebuild/plans/v0-1-8-master-plan.md`.
- Cycle 1 (this scaffolding): `docs/rebuild/plans/v0-1-8-cycle-1-odd-extractor-scaffolding.md`.

## What this package is

A Python library + `loam odd-extract` CLI subcommand that:

1. **Walks a target repository** (any language).
2. **Plans extractions per language adapter** (zero adapters in
   Cycle 1; Ruby in Cycle 3; Python in Cycle 4).
3. **Generates raw ACs** by dispatching adapters per slice.
4. **Verifies + post-processes** into a contract draft + sidecar
   YAML at `<workspace>/.loam/extractions/<repo-id>/`.

Every invocation runs in **dry-run mode by default** (Decision D —
Eric synthesis). Live extraction requires `--live`. Live extraction
respects a **foreign-codebase budget envelope** (Decision E) that
refuses runaway runs above a configurable money ceiling.

## Public API surface

```python
from loam_odd_extractor import (
    # Stage functions (pure — input → output, no global state).
    init_extraction,
    analyze_repo,
    generate_raw_acs,
    verify_contract,
    # Pydantic models.
    ExtractionConfig,
    AnalysisPlan,
    Slice,
    RawACs,
    ContractDraft,
    # Registry.
    LanguageAdapter,
    register_adapter,
    discover_adapters,
    # Budget.
    estimate_for_extraction,
    enforce_budget,
    # Errors.
    OddExtractorError,
    BudgetExceededError,
    RegistryError,
    StageError,
)
```

## CLI surface

```
loam odd-extract <repo-path> [--live] [--budget-cents N]
                             [--budget-override] [--workspace-root P]
                             [--stage init|analyze|generate|verify]
                             [--resume] [--status] [--repo-id X]
```

Default behaviour: dry-run; produces an `EstimateResult` block on
stdout; writes per-stage artefacts to
`<workspace>/.loam/extractions/<repo-id>/`.

## Workspace layout

```
<workspace>/.loam/extractions/<repo-id>/
    config.yaml          # Stage 1 output (ExtractionConfig)
    plan.yaml            # Stage 2 output (AnalysisPlan)
    raw-acs.yaml         # Stage 3 output (RawACs)
    contract-draft.md    # Stage 4 output (markdown)
    contract-draft.yaml  # Stage 4 output (sidecar)
    state.yaml           # cross-run state (D5 cross-session)
    audit-log/           # per-stage + per-run audit entries
        0001.yaml        # extraction_start
        0002.yaml        # stage_complete (init)
        ...
```

`<repo-id>` is derived deterministically from the repo's absolute
path: `<basename>-<8-char-sha256-hex>`.

## Language-adapter contract (for cycles 3+4)

```python
from typing import Protocol
from pathlib import Path
from loam_odd_extractor import AnalysisPlan, RawACs

class LanguageAdapter(Protocol):
    name: str
    def supports(self, repo: Path) -> bool: ...
    def extract(self, repo: Path, plan: AnalysisPlan) -> RawACs: ...
```

Adapters register via the `loam.odd_extractor.language_adapters`
entry-point group on their own pyproject.

## Out of scope (Cycle 1)

- Confidence bands → Cycle 2.
- Ratification workflow → Cycle 2.
- Ruby/Rails adapter → Cycle 3.
- Python adapter → Cycle 4.
- 6 dev-sdlc SKILLs → Cycle 5.
- Continuous codebase-watch → v0.2.0.

See the master plan for full scope and sequencing.
