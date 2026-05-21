"""One-shot retroactive sweep of sealed plan-docs (AC.FBMT1.APS.3 +
AC.T1RS.HEURISTIC.* extensions).

Walks ``docs/plans/*.md`` in a repo, identifies plan-docs that have
a corresponding seal commit in the git log, and ``git mv``s them
(plus their sibling manifest) into ``docs/plans/sealed/``.

Per plan-doc ``amendment-134-fbm-tier1-foundations.md`` §4
AC.FBMT1.APS family + §6 step 8 (Q3 owner-ratified retroactive
seed). Heuristic widened by amendment #143 §3 Scope A + §14
D-T1RS.HEURISTIC: three-strategy fallback chain to recover
pre-#134-style attribution where the seal commit subject names a
different slug than the plan-doc filename.

Heuristic chain (first non-empty result wins, then single-vs-multi
match determines move-vs-ambiguous):

  Strategy 1 (original narrow):
      git log --grep=^chore(seals): --grep=<full-slug> --all-match
  Strategy 2 (body-slug, new at #143):
      For plan-docs matching ``amendment-NN-<body>``, retry with
      ``--grep=<body>`` instead of the full slug. Recovers seals
      like ``chore(seals): pos-amend-cli-and-universal-paths seal —``
      attributed to ``amendment-22-pos-amend-cli.md``.
  Strategy 3 (amendment-NN, new at #143):
      For plan-docs matching ``amendment-NN-...``, search for
      commits whose message contains ``amendment #NN`` (with
      space), filtered to ``chore(seals):`` subjects.

Ambiguous plan-docs (multi-match in ANY strategy) are LEFT IN PLACE
per the §134 halt-trigger #5 contract — preserved verbatim by #143.
The operator manually triages those.

``.builder-plan.md`` companion plan-docs are filtered out (authoring
scratch, not the canonical plan-doc — D-T1RS.HEURISTIC.4).
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path


# Match ``amendment-NN-<body>``; group 1 is the number, group 2 is the
# body-slug (everything after ``amendment-NN-``). Mirrors the regex in
# ``heavy_b_migrate/amendment_acs.py`` but expressed locally to avoid a
# cross-tree import.
_AMENDMENT_SLUG_RE = re.compile(r"^amendment-(\d+)-(.+)$")


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
    # AC.T1RS.SWEEP.2: per-strategy move attribution for the
    # ``loam amend sweep-archive`` CLI commit body. Maps
    # strategy name (``narrow`` / ``body`` / ``amendment-n``) to a
    # list of plan-doc filenames moved via that strategy. Sibling
    # manifests are NOT enumerated separately; they ride with their
    # plan-doc.
    moved_by_strategy: dict[str, list[str]] = field(default_factory=dict)


def _git_log_seal_grep(repo_root: Path, *grep_args: str) -> list[str]:
    """Run ``git log --all --grep=^chore(seals): --grep=<...> ... --all-match``
    and return matching SHAs. Helper for Strategies 1 + 2."""
    cmd = [
        "git",
        "log",
        "--all",
        "--grep=^chore(seals):",
        *(f"--grep={g}" for g in grep_args),
        "--all-match",
        "--format=%H",
    ]
    try:
        result = subprocess.run(
            cmd,
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError:
        return []
    return [ln.strip() for ln in result.stdout.splitlines() if ln.strip()]


def _git_log_amendment_n_seal(repo_root: Path, n: int) -> list[str]:
    """Strategy 3: find ``chore(seals): ...`` commits whose message
    contains ``amendment #NN`` for the given N.

    Uses ``--all-match`` to AND the two greps; default BRE (no
    ``--extended-regexp``) keeps ``(`` literal in the
    ``^chore(seals):`` anchor. ``#`` is not a regex metacharacter
    so the raw pattern is safe.

    Note on word-boundary disambiguation: a commit message
    referencing ``amendment #5`` would otherwise match a query for
    N=50 under naive substring matching. Filter post-grep by
    re-checking each candidate's full message via a tighter Python
    regex (``\\bamendment #N\\b``).
    """
    import re as _re

    cmd = [
        "git",
        "log",
        "--all",
        "--grep=^chore(seals):",
        f"--grep=amendment #{n}",
        "--all-match",
        "--format=%H %s%n%b%x00",
    ]
    try:
        result = subprocess.run(
            cmd,
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError:
        return []
    # Split on the NUL we emit between records (handles multi-line
    # commit bodies; ``--format=%H %s%n%b%x00`` is the canonical
    # record terminator).
    boundary_re = _re.compile(rf"\bamendment #{n}\b")
    shas: list[str] = []
    for record in result.stdout.split("\x00"):
        record = record.strip()
        if not record:
            continue
        sha, _, rest = record.partition(" ")
        if not sha:
            continue
        if boundary_re.search(rest):
            shas.append(sha)
    return shas


def _find_seal_commit_for_slug(
    repo_root: Path,
    slug: str,
) -> tuple[list[str], str | None]:
    """Three-strategy fallback chain (AC.T1RS.HEURISTIC.{1,2}).

    Returns ``(shas, strategy_name)``. ``shas`` is the SHAs from
    the first non-empty strategy; ``strategy_name`` is
    ``"narrow"`` / ``"body"`` / ``"amendment-n"`` / ``None`` (no
    strategy returned a match). The caller decides move vs ambiguous
    vs in-flight based on ``len(shas)``.

    Strategy 1 (narrow): always tried first; the post-#134 convention.
    Strategy 2 (body): only tried for ``amendment-NN-<body>`` slugs.
    Strategy 3 (amendment-n): only tried for ``amendment-NN-...`` slugs
        AND only when Strategy 2 returns empty.
    """
    # Strategy 1 — original narrow heuristic
    shas = _git_log_seal_grep(repo_root, slug)
    if shas:
        return shas, "narrow"

    # Strategies 2 + 3 require the slug to be amendment-NN-shaped
    m = _AMENDMENT_SLUG_RE.match(slug)
    if not m:
        return [], None

    n = int(m.group(1))
    body_slug = m.group(2)

    # Strategy 2 — body-slug second-pass
    shas = _git_log_seal_grep(repo_root, body_slug)
    if shas:
        return shas, "body"

    # Strategy 3 — amendment-NN third-pass
    shas = _git_log_amendment_n_seal(repo_root, n)
    if shas:
        return shas, "amendment-n"

    return [], None


def _seal_commits_mentioning_slug(repo_root: Path, slug: str) -> list[str]:
    """Back-compat shim: original Strategy 1 only.

    Preserved so existing callers + tests of the narrow heuristic
    keep working unchanged (AC.FBMT1.APS.3 test fixture exercises
    Strategy 1 only).
    """
    return _git_log_seal_grep(repo_root, slug)


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
    # NOT into sub-dirs like research/). Filter out ``.builder-plan.md``
    # companions (authoring scratch, not canonical) per
    # D-T1RS.HEURISTIC.4.
    plan_docs = sorted(
        p
        for p in plans_dir.iterdir()
        if p.is_file() and p.suffix == ".md" and ".builder-plan." not in p.name
    )
    for plan_doc in plan_docs:
        slug = plan_doc.stem
        # Three-strategy fallback chain (amendment #143 Scope A).
        seal_shas, strategy = _find_seal_commit_for_slug(repo_root, slug)
        if not seal_shas:
            result.in_flight.append(plan_doc)
            continue
        if len(seal_shas) > 1:
            # Multiple matches in the winning strategy: ambiguous;
            # leave for manual triage (§134 halt-trigger #5 contract
            # preserved verbatim by #143).
            result.ambiguous.append(plan_doc)
            continue
        # Exactly one seal commit attributes this plan-doc. Move
        # plan-doc + sibling manifest (if present).
        new_plan_doc = sealed_dir / plan_doc.name
        result.moved.append((plan_doc, new_plan_doc))
        # Strategy attribution for CLI commit-body grouping.
        if strategy is not None:
            result.moved_by_strategy.setdefault(strategy, []).append(plan_doc.name)
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
