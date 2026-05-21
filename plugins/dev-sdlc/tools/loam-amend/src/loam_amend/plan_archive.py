"""One-shot retroactive sweep of sealed plan-docs (AC.FBMT1.APS.3).

Walks ``docs/plans/*.md`` in a repo, identifies plan-docs that have
a corresponding seal commit in the git log, and ``git mv``s them
(plus their sibling manifest) into ``docs/plans/sealed/``.

Per plan-doc ``amendment-134-fbm-tier1-foundations.md`` §4
AC.FBMT1.APS family + §6 step 8 (Q3 owner-ratified retroactive
seed).

The seal-commit attribution heuristic is narrow: a plan-doc is
"clearly sealed" when AT LEAST ONE commit in the git log carries a
subject matching ``chore(seals): ...`` AND mentions the plan-doc's
slug verbatim (in the subject line OR in the commit body). Ambiguous
plan-docs (no attributable seal commit) are LEFT IN PLACE per the
§8 halt trigger #5 contract — the operator manually triages those.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class SweepResult:
    """Outcome of one retroactive sweep call.

    ``moved`` is the list of (old_path, new_path) pairs for plan-
    docs (and sibling manifests) the sweep moved. ``in_flight``
    is the list of plan-docs left in ``docs/plans/`` (no clear
    seal-commit attribution found). ``ambiguous`` is the list of
    plan-docs that matched MULTIPLE seal commits — also left in
    place for manual triage per the §8 halt trigger contract.
    """

    moved: list[tuple[Path, Path]] = field(default_factory=list)
    in_flight: list[Path] = field(default_factory=list)
    ambiguous: list[Path] = field(default_factory=list)


def _seal_commits_mentioning_slug(repo_root: Path, slug: str) -> list[str]:
    """Return SHAs of every seal commit (``chore(seals): ...``)
    whose subject or body mentions ``slug``.

    Uses ``git log -G`` (regex on diff) which would over-match; we
    instead use ``--grep`` against subject + body so only commits
    that name the slug in their MESSAGE qualify. This rules out
    seal commits that happened to touch a file mentioning the slug
    in unrelated context.
    """
    try:
        result = subprocess.run(
            [
                "git",
                "log",
                "--all",
                "--grep=^chore(seals):",
                f"--grep={slug}",
                "--all-match",
                "--format=%H",
            ],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError:
        return []
    return [ln.strip() for ln in result.stdout.splitlines() if ln.strip()]


def sweep_sealed_plan_docs(
    repo_root: Path,
    *,
    dry_run: bool = False,
) -> SweepResult:
    """Move every clearly-sealed plan-doc into ``docs/plans/sealed/``.

    AC.FBMT1.APS.3:
      - Plan-docs with EXACTLY ONE attributable seal commit are
        moved (plus sibling manifest if present).
      - In-flight plan-docs (no seal commit found) stay in
        ``docs/plans/``.
      - Ambiguous plan-docs (multiple seal commits match) are
        left in place for manual triage.

    ``dry_run`` returns the would-be moves without executing them.
    """
    plans_dir = repo_root / "docs" / "plans"
    sealed_dir = plans_dir / "sealed"
    result = SweepResult()
    if not plans_dir.exists():
        return result
    if not dry_run:
        sealed_dir.mkdir(parents=True, exist_ok=True)

    # Only consider direct-children .md files under docs/plans/
    # (NOT recursive into sealed/ — those are already archived;
    # NOT into sub-dirs like research/).
    plan_docs = sorted(
        p
        for p in plans_dir.iterdir()
        if p.is_file() and p.suffix == ".md"
    )
    for plan_doc in plan_docs:
        slug = plan_doc.stem
        seal_shas = _seal_commits_mentioning_slug(repo_root, slug)
        if not seal_shas:
            result.in_flight.append(plan_doc)
            continue
        if len(seal_shas) > 1:
            # Multiple matches: ambiguous; leave for manual triage.
            result.ambiguous.append(plan_doc)
            continue
        # Exactly one seal commit attributes this plan-doc. Move
        # plan-doc + sibling manifest (if present).
        new_plan_doc = sealed_dir / plan_doc.name
        result.moved.append((plan_doc, new_plan_doc))
        manifest_path = plans_dir / f"{slug}.manifest.yaml"
        if manifest_path.exists():
            new_manifest = sealed_dir / manifest_path.name
            result.moved.append((manifest_path, new_manifest))

    if dry_run:
        return result

    for old, new in result.moved:
        rel_old = old.relative_to(repo_root)
        rel_new = new.relative_to(repo_root)
        subprocess.run(
            ["git", "mv", str(rel_old), str(rel_new)],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
    return result
