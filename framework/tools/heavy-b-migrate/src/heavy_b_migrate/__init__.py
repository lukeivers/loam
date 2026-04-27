"""heavy-b-migrate — Heavy-B Phase α / β / γ data-migration tooling.

Plan: ``docs/rebuild/plans/heavy-b-phase-alpha-beta-gamma-migration.md``.
Builder plan:
``docs/rebuild/plans/heavy-b-phase-alpha-beta-gamma-migration.builder-plan.md``.

Dev-discipline; no SEAL_COMMIT bump, no pos-amend manifest, no seal
commit. Composes against amendments #38 (objective-tracker schema
widening — ``lifted_from``, ``query_projection_view``), #39
(workspace-bootstrap tracker seed — value-prop root + spec
descendants), #40 (primary-persona tracker-context contributor — the
consumer that surfaces the migrated content), pos-amend tracker-
integration (#16 — ``objectives`` manifest block + apply registration),
and sub-plan A (`dev_intent` field on PersonaContract — the lazy-
projection trigger reads this signal).

Public entry points:

- :func:`trigger.run_if_dev_intent` — fail-soft side-effect entry the
  loam-mode session-start emitter calls; reads dev_intent, dispatches
  the phase runner if the workspace is dev-intent and the tree is not
  yet projected. Idempotent via ``lifted_from`` (every phase queries
  the tracker for already-projected records and skips them).
- :func:`runner.run_phases` — the synchronous phase runner; enforces
  α before β before γ ordering structurally.
- :mod:`components` / :mod:`component_acs` / :mod:`amendment_acs` —
  the three phases' extractor surfaces.
"""

from heavy_b_migrate.runner import run_phases  # noqa: F401
from heavy_b_migrate.trigger import run_if_dev_intent  # noqa: F401

__all__ = ["run_phases", "run_if_dev_intent"]
