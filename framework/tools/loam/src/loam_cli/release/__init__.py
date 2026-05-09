"""``loam release`` — concrete release process for the loam framework.

Per ``docs/plans/v0-6-0-release-process.md`` (AC.V060.{1-7,S}).

The ``loam release <version>`` subcommand structurally enforces the
publish ritual that until v0.6.0 was figured-out-as-I-went on every
publish: HARD smoke GREEN, ACs verified, STATE.md updated, no
uncommitted changes, branch == main, seal commit reachable from HEAD;
then annotated tag + ``git push`` to the ``origin`` remote; optional
GitHub Release via ``gh release create``; followed by an autonomous
post-ship review block naming the next scope.

Public surface:

    loam release <version> [--dry-run] [--release]

Behaviour summary:

- ``--dry-run`` runs every pre-publish gate + reports verdicts; no
  side effect on the working tree or remote.
- Without flags, runs gates → if all GREEN, creates the annotated tag
  at the seal commit + pushes branch + tag to ``origin``.
- ``--release`` adds ``gh release create <tag>`` with auto-generated
  notes (plan-doc §1 outcome shape + §status verdicts + commit log).
- Post-publish, the runner emits a "Next-scope proposal" block
  reading the roadmap §4 priority queue + recent FUTURE_IDEAS_DRAFT
  captures + halt-and-surface findings.

Entry-point registration follows the M6a builder contract — the
``loam.cli.subcommands`` entry-point group hosts the ``release``
adapter exported from :mod:`loam_cli.release.cli`.
"""

from __future__ import annotations
