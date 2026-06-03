"""STATE-OF-LOAM operative-reality record + substrate-audit comparator.

The N2 slice (R-1 + R-3): a single mechanism, two parts.

  * The **record** (R-1) is the terse, always-derivable answer to "what
    does loam currently RUN" — which components are built/sealed/merged,
    which hooks are wired-live vs dark, which backends are live vs
    design-aspirational. It is GENERATED FRESH from ground truth on every
    read (D1 = generate-fresh): git ref graph + per-component seal
    sidecars + live runtime config + a cheap REAL probe for backend-class
    components. There is NO persisted prose source — a persisted record
    is exactly the drift surface this slice exists to kill.

  * The **comparator** (R-3) compares a CLAIMED status (a doc's
    front-matter / status field, a stored memory claim) against the
    derived record and surfaces a DIVERGENCE — the specific claim plus
    the ground-truth contradiction. ONE comparator, two entry points:
    the doc-status drift caller (the `loam audit` verb / the release
    gate) and the FBM stored-claim-vs-truth caller
    (:func:`reconcile.reconcile_stored_claim`).

Public surface re-exported here:

  * :class:`record.ComponentState` / :class:`record.StateOfLoam` —
    the derived record.
  * :func:`record.generate_record` — the generate-fresh entry point.
  * :class:`probe.Liveness` — the wired/dark/built/sealed/merged classes.
  * :func:`comparator.compare_claim` / :class:`comparator.Divergence` —
    the R-3 comparator.
  * :func:`reconcile.reconcile_stored_claim` — the FBM second caller.
"""

from __future__ import annotations

from loam_cli.audit.comparator import (
    ClaimedStatus,
    Divergence,
    compare_claim,
    extract_claims_from_doc,
)
from loam_cli.audit.probe import (
    Liveness,
    classify_backend_liveness,
    classify_build_status,
    classify_hook_wired,
)
from loam_cli.audit.reconcile import (
    StoredClaim,
    reconcile_stored_claim,
)
from loam_cli.audit.record import (
    ComponentState,
    StateOfLoam,
    generate_record,
    render_record,
)
from loam_cli.audit.cairn_state import (
    ModuleProbeSpec,
    cairn_state_record,
    classify_module_build_status,
)
from loam_cli.audit.registry import (
    PROJECT_REGISTRY,
    ProjectStateSpec,
    derive_project_state,
    registered_project_names,
    resolve_project,
)

__all__ = [
    "ClaimedStatus",
    "ComponentState",
    "Divergence",
    "Liveness",
    "ModuleProbeSpec",
    "PROJECT_REGISTRY",
    "ProjectStateSpec",
    "StateOfLoam",
    "StoredClaim",
    "cairn_state_record",
    "classify_backend_liveness",
    "classify_build_status",
    "classify_hook_wired",
    "classify_module_build_status",
    "compare_claim",
    "derive_project_state",
    "extract_claims_from_doc",
    "generate_record",
    "reconcile_stored_claim",
    "registered_project_names",
    "render_record",
    "resolve_project",
]
