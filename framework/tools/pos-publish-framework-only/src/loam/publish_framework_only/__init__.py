"""``pos-publish-framework-only`` — synthesise the ``framework-only``
branch on canonical pos-v2.

Single-framework restructure (amendment #67). Canonical maintains a
synthetic ``framework-only`` branch in lockstep with its primary
``pos-v2`` branch. Each ``framework-only`` commit's tree contains
the entries that classify as ``public_only`` or ``dev_and_public``
under the publish-mode partition manifest at
``framework/tools/pos-publish-framework-only/publish-mode-manifest.yaml``
(amendment #83 — M2). Framework component dirs promote to the
synthetic-branch root; top-level public docs overlay verbatim.

The branch is consumed by ``pos-new-workspace --from <canonical>``
(``git clone --branch framework-only ...``) so workspaces produced
by the bootstrap have shape ``<workspace>/framework/<comp>/``
(single level), eliminating the ``framework/framework/<comp>/``
doubling failure class structurally.

The public API is :func:`synthesise_framework_only` (programmatic)
and the ``pos-publish-framework-only`` console script (operator-
facing). The synthesis composes existing git plumbing
(``ls-tree``, ``mktree``, ``commit-tree``, ``update-ref``) — no
working-tree mutation, no third-party deps beyond ``pyyaml`` for
the manifest read.

Partition surface (amendment #83 — M2):

  - :class:`PartitionClass`     — StrEnum of the four classes.
  - :class:`PartitionManifest`  — parsed manifest dataclass.
  - :class:`ManifestEntry`      — single classification entry.
  - :class:`ManifestError`      — schema-shape exception.
  - :func:`load_manifest`       — parse YAML → manifest.
  - :func:`classify_path`       — classify a workspace-relative path.
  - :func:`is_publishable`      — True iff class is a ship class.
  - :func:`is_audit_excluded`   — True iff path is audit-excluded.
"""

from loam.publish_framework_only.partition import (
    ManifestEntry,
    ManifestError,
    PartitionClass,
    PartitionManifest,
    classify_path,
    is_audit_excluded,
    is_publishable,
    load_manifest,
)
from loam.publish_framework_only.synth import (
    SynthesisError,
    SynthesisResult,
    synthesise_framework_only,
)


__all__ = [
    # Synthesis surface.
    "SynthesisError",
    "SynthesisResult",
    "synthesise_framework_only",
    # Partition surface (amendment #83 — M2).
    "PartitionClass",
    "PartitionManifest",
    "ManifestEntry",
    "ManifestError",
    "load_manifest",
    "classify_path",
    "is_publishable",
    "is_audit_excluded",
]
