"""``pos-publish-framework-only`` — synthesise the ``framework-only``
branch on canonical pos-v2.

Single-framework restructure (amendment #67). Canonical maintains a
synthetic ``framework-only`` branch in lockstep with its primary
``pos-v2`` branch. Each ``framework-only`` commit's tree is::

    framework-only/<root>:
      <every entry under canonical's framework/>   # promoted to root
      CLAUDE.md                                    # carried verbatim
      CLAUDE.dev.md
      README.md
      docs/...

The branch is consumed by ``pos-new-workspace --from <canonical>``
(``git clone --branch framework-only ...``) so workspaces produced by
the bootstrap have shape ``<workspace>/framework/<comp>/`` (single
level), eliminating the ``framework/framework/<comp>/`` doubling
failure class structurally.

The public API is :func:`synthesise_framework_only` (programmatic) and
the ``pos-publish-framework-only`` console script (operator-facing).
The synthesis composes existing git plumbing (``read-tree``, ``write-
tree``, ``commit-tree``, ``update-ref``) — no working-tree mutation,
no third-party deps.
"""

from pos_publish_framework_only.synth import (
    SynthesisError,
    SynthesisResult,
    synthesise_framework_only,
)


__all__ = [
    "SynthesisError",
    "SynthesisResult",
    "synthesise_framework_only",
]
