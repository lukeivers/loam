"""``loam amend seal`` — advance sidecars + finalise the amendment cycle.

Pre-extension behaviour (still available via ``--no-finalize``):
advance sidecars to HEAD + append narrative.

Post-extension default (per AC.D-sa.1): also stage the changes, run
the touched component(s)' full pytest suite, run the cross-component
sweep (every sealed component's seal-diff test by default; per
AC.D-sa.3), create a deterministic seal commit (per AC.D-sa.2), and
verify ``loam amend apply --dry-run`` exits 0 against the post-seal
HEAD (the amendment-#22 hard prereq, preserved at the seal step).

Failure-mode (per AC.D-sa.5): on any failure class, halt before the
commit (or for the post-commit dry-run failure case, leave the seal
commit in place per D-4 ruling); emit a structured diagnostic; leave
the working tree at a recoverable checkpoint.

Plan-doc projection (per AC.D-sa.7): when ``--plan-doc <path>`` is
supplied, append a ``### Commit SHAs`` subsection under the plan
doc's ``## 14.`` OR ``## §14`` heading (per AC.LAS14R.{1,2}, the
canonical plan-doc convention uses ``## §14 — Method-decision
register``; the legacy ``## 14.`` shape is also accepted for
backwards compatibility) and create a follow-up
``docs(plans): record amendment #N commit SHAs ...`` commit.

Per AC.LAE.2 (v0.1.2 item 6 — loam-amend ergonomics sweep):
``--allow-untracked-globs <pattern>`` (repeatable) admits paths
matching the named glob pattern when computing dirty-tree status.
Common case: dirty ``docs/FUTURE_IDEAS_DRAFT.md`` from
in-flight capture. Patterns are NOT staged or committed by the seal
step — admission is dirty-check-only.
"""

from __future__ import annotations

import fnmatch
import os
import re
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from loam_amend.commands import apply as apply_cmd
from loam_amend.fidraft_cleanup import plan_slug_from_path, scan_fidraft
from loam_amend.manifest import Manifest, ManifestError, load_manifest
from loam_amend.narrative import append_narrative
from loam_amend.paths import find_repo_root
from loam_amend.sidecar import write_sidecar
from loam_amend.tracker_registration import (
    TrackerUnavailableError,
    update_source_commits,
)


# AC.FBMT1.APS.1 — sealed plan-docs land here. Sibling to
# ``docs/plans/`` (NOT per-component) per §14 D-T1.4.DIR ruling:
# plan-docs are universal admissions; per-component placement would
# fragment multi-component plans.
SEALED_PLANS_SUBDIR = Path("docs/plans/sealed")


# Co-Authored-By trailer per D-5: include only when invoked under a
# Claude-Code-attributed environment (env-var detection). Trailer text
# matches the convention from prior seal commits in this repo.
_CO_AUTHORED_BY = (
    "Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
)
_CLAUDE_ENV_VARS = ("CLAUDECODE", "CLAUDE_CODE_SDK", "CLAUDE_AGENT_RUN")


def _claude_environment() -> bool:
    """Return True iff invoked under a Claude-Code-attributed shell.

    Auto-detected via any of the env vars commonly set in dispatched-
    agent shells. None set → human invocation; trailer omitted.
    """
    return any(os.environ.get(name) for name in _CLAUDE_ENV_VARS)


def _head_sha(repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def _short_sha(sha: str) -> str:
    return sha[:7]


def _commit_subject(repo_root: Path, sha: str) -> str:
    """Return the subject line of the commit at *sha*."""
    result = subprocess.run(
        ["git", "log", "-1", "--format=%s", sha],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def _working_tree_dirty(
    repo_root: Path,
    ignore_paths: set[Path],
    *,
    allow_untracked_globs: Sequence[str] = (),
) -> list[str]:
    """Return list of dirty paths NOT in *ignore_paths* / glob-admitted.

    *ignore_paths* are repo-relative paths the seal step is itself
    expected to have written (sidecars + narrative target + plan doc).
    Anything else dirty at invocation time is unrelated dirt and the
    seal step refuses to proceed (AC.D-sa.5 case (c)).

    *allow_untracked_globs* (per AC.LAE.2) is a sequence of shell-style
    glob patterns; any dirty path matching one of these via
    ``fnmatch.fnmatchcase`` is admitted into the ignore set. Patterns
    are NOT staged or committed — admission is dirty-check-only.
    Patterns are anchored at the repo root (no implicit trailing ``*``):
    ``docs/FUTURE_IDEAS_DRAFT.md`` matches the literal file;
    ``docs/plans/*`` matches direct children only; ``docs/**/*`` is
    the recursive form.
    """
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    dirty: list[str] = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        # porcelain v1 format: "XY <path>" (path may include rename)
        path_part = line[3:].strip()
        # Handle renames "old -> new"
        if " -> " in path_part:
            path_part = path_part.split(" -> ", 1)[1]
        rel = Path(path_part)
        if rel in ignore_paths:
            continue
        if any(
            fnmatch.fnmatchcase(path_part, pattern)
            for pattern in allow_untracked_globs
        ):
            continue
        dirty.append(line)
    return dirty


def _discover_sealed_components(repo_root: Path) -> list[str]:
    """Return the list of sealed-component names in the workspace.

    Discovery: every directory under ``framework/`` that carries a
    ``tests/SEAL_COMMIT`` sidecar is a sealed component. This matches
    the convention every seal-diff test in the workspace already
    relies on (post-D.1 directory restructure: framework code lives
    under ``framework/``). Returned sorted for determinism.
    """
    components: list[str] = []
    for sidecar in repo_root.glob("framework/*/tests/SEAL_COMMIT"):
        comp_dir = sidecar.parent.parent
        if comp_dir.is_dir():
            components.append(comp_dir.name)
    return sorted(components)


def _seal_diff_test_path(repo_root: Path, component: str) -> Path | None:
    """Return the seal-diff test path for *component*, or None.

    Convention (post-D.1): ``framework/<comp>/tests/test_no_sealed_amendments.py``
    for most sealed components, ``framework/<comp>/tests/test_cross_cutting.py``
    for hands-off-lifecycle (per amendment #22 ruling on the lifecycle's
    different seal-diff test name).
    """
    comp_dir = repo_root / "framework" / component
    candidates = (
        comp_dir / "tests" / "test_no_sealed_amendments.py",
        comp_dir / "tests" / "test_cross_cutting.py",
    )
    for c in candidates:
        if c.exists():
            return c
    return None


@dataclass
class _FailureCheckpoint:
    """A recoverable failure during finalisation."""

    code: int  # exit code (1 / 2 / 3 per existing taxonomy)
    klass: str  # short failure-class name for diagnostics
    detail: str  # operator-readable message (multi-line ok)


def _emit_diagnostic(checkpoint: _FailureCheckpoint) -> None:
    # Emit on stdout with an uppercase HALT prefix so the line is
    # scannable across all loam amend subcommands and survives
    # contexts where stderr is dropped (e.g. some Bash-tool eval-
    # wrapper invocations). Per AC.PA-hv.1 / AC.PA-hv.2 of
    # `docs/plans/pos-amend-halt-visibility.md`.
    print(f"HALT: {checkpoint.klass}")
    print(checkpoint.detail)


def _build_commit_message(
    *,
    manifest: Manifest,
    amendment_sha: str,
    bumped_sidecars: list[str],
    narrative_target: str | None,
    sweep_summary: str,
    include_co_authored_by: bool,
) -> str:
    """Assemble the deterministic seal-commit message (AC.D-sa.2).

    Subject:
        chore(seals): <description> — <comp1>[+<comp2>...] at <sha-short>

    Body sections (each with a leading blank line):
        1. Amendment-number reference
        2. Bumped sidecar paths
        3. Narrative target (if any)
        4. Baseline-to-amendment-SHA window
        5. Cross-component sweep result
        Optional: Co-Authored-By trailer
    """
    description = manifest.seal_description or manifest.slug
    components_part = "+".join(c.name for c in manifest.components)
    short = _short_sha(amendment_sha)
    subject = (
        f"chore(seals): {description} — {components_part} at {short}"
    )

    body_lines = [subject, ""]
    # AC.DPS1.11: schema v3 manifests may omit ``amendment.number``.
    # Drop the ``#N`` prefix when ``manifest.number is None``;
    # identify by slug only via the existing subject line.
    if manifest.number is None:
        body_lines.append(f"Amendment {manifest.slug} seal commit.")
    else:
        body_lines.append(f"Amendment #{manifest.number} seal commit.")
    body_lines.append("")
    body_lines.append("Bumped sidecars:")
    if bumped_sidecars:
        for s in bumped_sidecars:
            body_lines.append(f"  - {s}")
    else:
        body_lines.append("  (none — idempotent re-seal)")
    body_lines.append("")
    if narrative_target is not None:
        body_lines.append(f"Narrative appended to: {narrative_target}")
    else:
        body_lines.append("Narrative: (none)")
    # AC.DPS2.6: schema v3 manifests carrying ``plan_doc_ref`` get a
    # ``Plan doc:`` body line so readers of ``git log`` see the
    # pointer to the full reasoning without opening the
    # ``SEAL_COMMIT.<slug>`` file. Schema v1 / v2 (and v3 manifests
    # without ``plan_doc_ref``) keep today's body byte-identical.
    if (
        manifest.schema_version == 3
        and manifest.plan_doc_ref is not None
    ):
        body_lines.append(f"Plan doc: {manifest.plan_doc_ref}")
    body_lines.append("")
    body_lines.append(
        f"Diff window: {manifest.baseline} .. {amendment_sha}"
    )
    body_lines.append("")
    body_lines.append(f"Cross-component sweep: {sweep_summary}")
    if include_co_authored_by:
        body_lines.append("")
        body_lines.append(_CO_AUTHORED_BY)
    return "\n".join(body_lines) + "\n"


def _run_pytest(
    repo_root: Path, target: Path | str, *, env: dict[str, str] | None = None
) -> tuple[int, str]:
    """Run pytest against *target* in *repo_root*.

    Method choice per ODD §3.4: invoked via the workspace venv's
    Python (``.venv/bin/python -m pytest``) when present, else
    ``python -m pytest`` (the ambient interpreter the test harness
    is running under). Returns (returncode, combined stdout+stderr).
    """
    venv_python = repo_root / ".venv" / "bin" / "python"
    py_cmd = (
        [str(venv_python)]
        if venv_python.exists()
        else ["python"]
    )
    cmd = py_cmd + ["-m", "pytest", str(target), "-q"]
    proc = subprocess.run(
        cmd,
        cwd=repo_root,
        capture_output=True,
        text=True,
        env=env,
    )
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def _backfill_plan_doc_shas(
    *,
    plan_doc: Path,
    amendment_sha: str,
    amendment_subject: str,
    seal_sha: str,
    seal_subject: str,
) -> _FailureCheckpoint | None:
    """Append the deterministic ``### Commit SHAs`` subsection to §14.

    Returns None on success; a checkpoint when the plan doc is
    missing or has no §14 heading. Idempotent: if a
    ``### Commit SHAs`` subsection already lives under §14, it is
    REPLACED (not duplicated) — this keeps re-invocation safe.
    """
    if not plan_doc.exists():
        return _FailureCheckpoint(
            code=3,
            klass="plan-doc-missing",
            detail=(
                f"plan doc not found: {plan_doc}\n"
                "AC.D-sa.7 requires the designated plan doc to exist; "
                "the seal commit has been left in place. Operator may "
                "author a corrective commit by hand."
            ),
        )
    text = plan_doc.read_text(encoding="utf-8")

    # Locate the §14 heading. Accept BOTH the canonical
    # plan-doc-convention ``## §14<sep>`` shape AND the legacy
    # ``## 14<sep>`` shape, where <sep> is one of ``.``, whitespace,
    # or em-dash (U+2014). Per AC.LAS14R.{1,2}; the optional ``§``
    # and the widened separator class make the widening additive +
    # backwards-compatible.
    section_header_re = re.compile(r"^## §?14[.\s—]", re.MULTILINE)
    m = section_header_re.search(text)
    if m is None:
        return _FailureCheckpoint(
            code=3,
            klass="plan-doc-missing-section-14",
            detail=(
                f"plan doc has no '## 14.' or '## §14' heading: "
                f"{plan_doc}\n"
                "AC.D-sa.7 (widened by AC.LAS14R.{1,2}) requires "
                "the designated plan doc to carry the §14 "
                "method-decision-record heading in either the "
                "canonical ``## §14<sep>`` shape or the legacy "
                "``## 14<sep>`` shape, where <sep> is ``.``, "
                "whitespace, or em-dash. The seal commit has been "
                "left in place. Operator may author the §14 prose + "
                "SHA subsection by hand."
            ),
        )

    subsection = (
        "### Commit SHAs\n\n"
        f"- Amendment commit: `{amendment_sha}` —\n"
        f"  `{amendment_subject}`\n"
        f"- Seal commit: `{seal_sha}` —\n"
        f"  `{seal_subject}`\n"
    )

    # Find the bounds of §14: from the heading to the next "^## " or EOF.
    section_start = m.start()
    next_section_re = re.compile(r"^## ", re.MULTILINE)
    nxt = next_section_re.search(text, m.end())
    section_end = nxt.start() if nxt else len(text)

    section_text = text[section_start:section_end]

    # Idempotency: if a "### Commit SHAs" subsection already exists
    # in §14, replace it; otherwise append.
    sub_re = re.compile(r"^### Commit SHAs\b", re.MULTILINE)
    sub_m = sub_re.search(section_text)
    if sub_m is not None:
        # Replace from "### Commit SHAs" to the next "^### " or end of section.
        next_sub_re = re.compile(r"^### ", re.MULTILINE)
        nxt_sub = next_sub_re.search(section_text, sub_m.end())
        sub_end = nxt_sub.start() if nxt_sub else len(section_text)
        new_section = (
            section_text[: sub_m.start()]
            + subsection
            + ("\n" if not section_text[sub_end - 1: sub_end] == "\n" else "")
            + section_text[sub_end:]
        )
    else:
        # Append to the end of §14 (trim trailing whitespace; keep one blank line)
        trimmed = section_text.rstrip() + "\n\n"
        new_section = trimmed + subsection

    new_text = text[:section_start] + new_section + text[section_end:]
    if new_text == text:
        # No-op (already up to date)
        return None
    plan_doc.write_text(new_text, encoding="utf-8")
    return None


def _apply_dry_run_post_seal(manifest_path: Path) -> int:
    """Run ``loam amend apply --dry-run`` against the post-seal HEAD."""
    return apply_cmd.run(manifest_path, dry_run=True)


# AC.FBMT1.APS.1 — compute the archive-target paths for a plan-doc
# and its sibling manifest. The manifest filename convention is
# ``<slug>.manifest.yaml`` adjacent to ``<slug>.md``; both move
# together. Returns ``(plan_target, manifest_target)`` resolved
# relative to ``repo_root``.
def _archive_targets(
    plan_doc: Path, manifest_path: Path, repo_root: Path
) -> tuple[Path, Path]:
    """Resolve where a plan-doc + manifest pair archive to.

    Per §14 D-T1.4.DIR: ``docs/plans/sealed/<slug>.md`` and
    ``docs/plans/sealed/<slug>.manifest.yaml`` (siblings under
    ``docs/plans/sealed/``).
    """
    sealed_dir = repo_root / SEALED_PLANS_SUBDIR
    plan_target = sealed_dir / plan_doc.name
    manifest_target = sealed_dir / manifest_path.name
    return plan_target, manifest_target


def _plan_doc_already_sealed(plan_doc: Path, repo_root: Path) -> bool:
    """Return ``True`` when ``plan_doc`` is already under
    ``docs/plans/sealed/``.

    Used to make T1.4's archive step idempotent: a re-seal that
    points at an already-archived plan-doc skips the move (the
    file is where it should be). Also guards the bootstrap case
    where this very amendment's plan-doc has already been moved
    by an earlier dry-run.
    """
    try:
        rel = plan_doc.resolve().relative_to(repo_root.resolve())
    except ValueError:
        return False
    return str(rel).startswith(str(SEALED_PLANS_SUBDIR) + "/") or (
        str(rel).startswith(str(SEALED_PLANS_SUBDIR) + os.sep)
    )


def _stage_plan_doc_archive(
    *,
    plan_doc: Path,
    manifest_path: Path,
    repo_root: Path,
) -> tuple[Path, Path] | None:
    """Move plan-doc + manifest into ``docs/plans/sealed/`` (T1.4).

    AC.FBMT1.APS.1: the moves are performed BEFORE the seal commit
    so the rename lands IN the seal commit (the deterministic-
    content invariant accommodates the rename via git's standard
    rename detection — the seal commit's tree carries the new
    paths, the old paths are deleted, and ``git log -- <new>``
    threads back through the rename).

    AC.FBMT1.APS.2: ``git mv`` preserves byte-identical content;
    the move is rename-only.

    Returns ``(new_plan_doc, new_manifest_path)`` on success; raises
    on git failure (caller emits the failure-checkpoint diagnostic).
    Returns ``None`` when the plan-doc is already at the sealed
    location (idempotent re-seal).
    """
    if _plan_doc_already_sealed(plan_doc, repo_root):
        return None
    plan_target, manifest_target = _archive_targets(
        plan_doc, manifest_path, repo_root
    )
    # Ensure the sealed/ directory exists (git mv won't create it).
    plan_target.parent.mkdir(parents=True, exist_ok=True)
    # Plan-doc move.
    plan_rel_src = plan_doc.resolve().relative_to(repo_root.resolve())
    plan_rel_dst = plan_target.relative_to(repo_root)
    subprocess.run(
        ["git", "mv", str(plan_rel_src), str(plan_rel_dst)],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    # Manifest move (sibling). The manifest_path may have been
    # passed as a relative arg; resolve before computing the
    # relative-to-repo path.
    manifest_rel_src = manifest_path.resolve().relative_to(repo_root.resolve())
    manifest_rel_dst = manifest_target.relative_to(repo_root)
    subprocess.run(
        ["git", "mv", str(manifest_rel_src), str(manifest_rel_dst)],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    return plan_target, manifest_target


def _emit_fidraft_cleanup_surface(
    *,
    plan_doc: Path,
    repo_root: Path,
) -> None:
    """Emit the FIDRAFT cleanup surface (T1.3 / AC.FBMT1.FCS family).

    AC.FBMT1.FCS.1: post-seal hook reads the just-sealed plan-doc's
    slug, scans ``docs/FUTURE_IDEAS_DRAFT.md`` for entries above
    the slug-overlap threshold, prints a structured surface to
    stdout. AC.FBMT1.FCS.2: never writes to FIDRAFT (the
    ``scan_fidraft`` helper is read-only). AC.FBMT1.FCS.3: no-
    false-positive shape — an unmatched scan prints "no matching
    entries; nothing to clean up".
    """
    fidraft_path = repo_root / "docs" / "FUTURE_IDEAS_DRAFT.md"
    slug = plan_slug_from_path(plan_doc)
    surface = scan_fidraft(plan_slug=slug, fidraft_path=fidraft_path)
    # Always print the surface (even on no-match — the operator
    # knows the hook fired and decided not-to-clean rather than
    # silently skipping).
    print(surface.render())


def _legacy_seal(manifest: Manifest, repo_root: Path) -> int:
    """Pre-extension behaviour: advance sidecars + append narrative.

    Used when ``--no-finalize`` is set. Output and exit-code semantics
    are byte-identical to pre-extension ``loam amend seal``.

    Per AC.DPS1.4: schema v3 manifests with ``plan_doc_ref`` and no
    ``narrative.body`` get a synthesized 5-15 line seal-narrative
    body composed from ``<title> + plan_doc_ref + amendment-SHA``.
    Schema v1 / v2 unchanged (the ``narrative.body`` field is required
    + carries the full text).
    """
    sha = _head_sha(repo_root)
    changes: list[str] = []
    for comp in manifest.components:
        sidecar_path = repo_root / comp.sidecar
        if write_sidecar(sidecar_path, sha):
            changes.append(f"{comp.name}: SEAL_COMMIT → {sha}")
    if manifest.narrative is not None:
        target = repo_root / manifest.narrative.target
        body = _resolve_narrative_body(manifest, sha)
        if append_narrative(target, body):
            changes.append(
                f"narrative appended to {manifest.narrative.target}"
            )
    if not changes:
        print("no changes (idempotent re-seal)")
    else:
        print("sealed:")
        for c in changes:
            print(f"  - {c}")
    return 0


def _resolve_narrative_body(manifest: Manifest, amendment_sha: str) -> str:
    """Return the seal-narrative body to append to ``narrative.target``.

    - Schema v1 / v2 (and any v3 manifest that explicitly sets
      ``narrative.body``): return the manifest-supplied body
      verbatim.
    - Schema v3 with ``plan_doc_ref`` and no ``narrative.body``
      (the new collapsed shape per cost-audit Recommendation A +
      Recommendation B): synthesize a 5-15 line summary citing the
      plan-doc, the amendment SHA, plus optional ACs-satisfied count
      and smoke outcome from the manifest's ``ac_count`` /
      ``smoke_outcome`` fields. The full plan-doc content is NOT
      inlined — readers follow the ``plan_doc_ref`` pointer for
      detail.

    Per plan ``dev-pattern-simplifications-1.md`` AC.DPS1.4 +
    ``dev-pattern-simplifications-2.md`` AC.DPS2.{1,2,3,4,5}.
    """
    assert manifest.narrative is not None  # caller-checked
    if manifest.narrative.body is not None:
        # AC.DPS2.5: explicit body returned verbatim. Preserves
        # AC.DPS1.4 invariant for v3 manifests authored with body.
        return manifest.narrative.body
    # v3 collapsed shape: synthesize from plan_doc_ref + optional
    # ac_count / smoke_outcome.
    if manifest.plan_doc_ref is None:  # defensive — load_manifest forbids
        raise AssertionError(
            "v3 manifest reached _resolve_narrative_body with neither "
            "narrative.body nor plan_doc_ref — load_manifest should have "
            "rejected this earlier"
        )
    if manifest.number is None:
        ident_line = f"# {manifest.title}"
    else:
        ident_line = f"# Amendment #{manifest.number} — {manifest.title}"
    components_part = "+".join(c.name for c in manifest.components)
    # AC.DPS2.1 + AC.DPS2.4: body covers what-shipped (title, slug,
    # components), ACs-satisfied count + smoke outcome (when set), and
    # the plan-doc reference. Optional fields produce optional lines —
    # the body fits in 5-15 lines across the full input matrix.
    body_lines = [
        ident_line,
        "",
        f"slug: {manifest.slug}",
        f"components: {components_part}",
        f"baseline: {manifest.baseline}",
        f"amendment-commit: {amendment_sha}",
        f"plan-doc: {manifest.plan_doc_ref}",
    ]
    if manifest.ac_count is not None:
        body_lines.append(f"acs-satisfied: {manifest.ac_count}")
    if manifest.smoke_outcome is not None:
        body_lines.append(f"smoke: {manifest.smoke_outcome}")
    body_lines.append("")
    body_lines.append(
        "Narrative body collapsed per cost-audit 2026-05-04 "
        "Recommendations A + B (manifest narrative collapse + seal-"
        "narrative compression) — see the plan-doc above for full "
        "rationale, AC family, and smoke results."
    )
    return "\n".join(body_lines)


def _finalize(
    manifest: Manifest,
    manifest_path: Path,
    repo_root: Path,
    *,
    scoped_sweep: bool,
    plan_doc: Path | None,
    allow_untracked_globs: Sequence[str] = (),
    skip_fidraft_cleanup: bool = False,
) -> int:
    """Full finalisation per AC.D-sa.1 + AC.D-sa.5 + AC.D-sa.7.

    T1.4 (AC.FBMT1.APS.*): when ``plan_doc`` is supplied, move the
    plan-doc + manifest into ``docs/plans/sealed/`` BEFORE the seal
    commit so the rename lands inside the seal commit.

    T1.3 (AC.FBMT1.FCS.*): after the seal commit lands, emit the
    FIDRAFT cleanup-surface unless ``skip_fidraft_cleanup`` is True
    (AC.FBMT1.FCS.4 emergency-bypass flag).
    """

    # ------------------------------------------------------------------
    # (a) Resolve the amendment SHA (current HEAD).
    # ------------------------------------------------------------------
    amendment_sha = _head_sha(repo_root)
    amendment_subject = _commit_subject(repo_root, amendment_sha)

    # Compute the set of paths the seal step is itself expected to
    # write (so `git status` dirt-checking can ignore them).
    # Amendment #138 Scope B (AC.DTCO.*): the dirty-tree gate now
    # runs BEFORE the plan-doc/manifest archive, so the rename pair
    # has NOT happened at gate time — no rename-in-expected_writes
    # filtering needed. Earlier the rename was staged by `git mv`
    # before the gate fired and the staged paths had to be admitted
    # explicitly; the reorder makes that filter unnecessary and
    # also leaves the working tree pristine when the gate halts
    # (operator no longer needs to manually `git mv` plan-doc +
    # manifest back from `sealed/`).
    expected_writes: set[Path] = set()
    for comp in manifest.components:
        expected_writes.add(Path(comp.sidecar))
    if manifest.narrative is not None:
        expected_writes.add(Path(manifest.narrative.target))

    # ------------------------------------------------------------------
    # (b) Pre-flight: refuse to proceed on unrelated dirty state
    # (case (c) of AC.D-sa.5). Amendment #138 Scope B (AC.DTCO.1):
    # this gate fires BEFORE any file move so halt leaves the working
    # tree pristine — operator does not need to manually `git mv`
    # archived files back from `docs/plans/sealed/`.
    # ------------------------------------------------------------------
    dirty = _working_tree_dirty(
        repo_root,
        expected_writes,
        allow_untracked_globs=allow_untracked_globs,
    )
    if dirty:
        _emit_diagnostic(
            _FailureCheckpoint(
                code=3,
                klass="dirty-working-tree",
                detail=(
                    "working tree carries unrelated dirty paths:\n"
                    + "\n".join(f"  {d}" for d in dirty)
                    + "\nRefusing to seal. Stash, commit, or revert "
                    "the unrelated paths and re-invoke."
                ),
            )
        )
        return 3

    # T1.4 (AC.FBMT1.APS.1) — archive plan-doc + manifest into
    # `docs/plans/sealed/` AFTER the dirty-tree gate has passed
    # (amendment #138 Scope B reorder; previously this ran before
    # the gate, which left the rename half-applied on every halt).
    # Tracks the post-archive paths for use downstream (the §14
    # backfill must target the new plan-doc location; the post-seal
    # dry-run must use the new manifest location).
    effective_plan_doc = plan_doc
    effective_manifest_path = manifest_path
    if plan_doc is not None and plan_doc.exists():
        archive_result = _stage_plan_doc_archive(
            plan_doc=plan_doc,
            manifest_path=manifest_path,
            repo_root=repo_root,
        )
        if archive_result is not None:
            new_plan_doc, new_manifest_path = archive_result
            effective_plan_doc = new_plan_doc
            effective_manifest_path = new_manifest_path

    # ------------------------------------------------------------------
    # (c) Advance sidecars + append narrative (today's behaviour).
    # AC.D.1.5.5 (amendment #62): components named in the manifest's
    # ``cleanup_directives:`` block have their sidecars preserved at
    # the cleanup-target value (set by ``apply``); the seal step does
    # NOT advance their sidecars to the amendment SHA. Otherwise the
    # retroactive revert would be clobbered.
    # ------------------------------------------------------------------
    cleanup_protected = {d.comp_name for d in manifest.cleanup_directives}
    bumped_sidecars: list[str] = []
    for comp in manifest.components:
        if comp.name in cleanup_protected:
            print(
                f"note {comp.name}: cleanup_directive — SEAL_COMMIT "
                f"preserved at cleanup-target (sidecar bump skipped)"
            )
            continue
        sidecar_path = repo_root / comp.sidecar
        if write_sidecar(sidecar_path, amendment_sha):
            bumped_sidecars.append(f"{comp.sidecar} → {amendment_sha}")
    narrative_target_str: str | None = None
    if manifest.narrative is not None:
        target = repo_root / manifest.narrative.target
        # Per AC.DPS1.4: schema v3 manifests with ``plan_doc_ref`` and
        # no ``narrative.body`` get a synthesized 5-15 line summary;
        # v1 / v2 keep the explicit ``body`` verbatim.
        body = _resolve_narrative_body(manifest, amendment_sha)
        if append_narrative(target, body):
            narrative_target_str = manifest.narrative.target
        else:
            # Idempotent — narrative already present.
            narrative_target_str = manifest.narrative.target

    # ------------------------------------------------------------------
    # (c.5) AC.D-pa.3: rewrite each registered objective's
    # ``lifted_from.source_commit`` to point at the amendment SHA.
    # No-op for v1 manifests (manifest.objectives is empty). Runs
    # before tests so a tracker-unavailable failure halts before
    # any commit is created.
    # ------------------------------------------------------------------
    if manifest.objectives:
        try:
            updated_n = update_source_commits(
                manifest, repo_root, amendment_sha
            )
        except TrackerUnavailableError as exc:
            _emit_diagnostic(
                _FailureCheckpoint(
                    code=3,
                    klass=exc.klass,
                    detail=(
                        exc.detail
                        + "\nSidecar + narrative changes left "
                        "uncommitted. Restore the tracker DB and "
                        "re-invoke."
                    ),
                )
            )
            return 3
        if updated_n:
            print(
                f"tracker: source_commit pinned on {updated_n} "
                "registered objective(s)"
            )

    # ------------------------------------------------------------------
    # (d) Run touched components' full pytest suites.
    # AC.D-sa.1 step (c) — touched components only here; the
    # cross-component sweep at step (e) handles every other component
    # via the seal-diff test only (per dispatch-speedups CDC).
    #
    # Amendment #138 Scope A (AC.STSP.*): derive the tests directory
    # from the manifest's `seal_test:` field (the mandatory schema
    # field already consumed by `apply.py` + `dry_run.py`) instead of
    # hardcoding `framework/<comp>/tests/`. Both framework/-tree and
    # plugins/-tree components now have their tests run by the seal
    # step (previously plugins/-tree components silently skipped).
    # No fallback to legacy `framework/<comp>/tests/`: `seal_test:`
    # is mandatory per manifest.py line 58 + `_require_str` at line
    # 423 — `load_manifest` rejects any manifest lacking it.
    # ------------------------------------------------------------------
    for comp in manifest.components:
        comp_tests = (repo_root / Path(comp.seal_test)).parent
        if not comp_tests.exists():
            continue
        rc, output = _run_pytest(repo_root, comp_tests)
        if rc != 0:
            _emit_diagnostic(
                _FailureCheckpoint(
                    code=3,
                    klass="component-tests-failed",
                    detail=(
                        f"component '{comp.name}' tests failed (exit {rc}).\n"
                        f"  test target: {comp_tests}\n\n"
                        + output
                        + "\nSidecar + narrative changes left "
                        "uncommitted. Fix the failing test and re-invoke."
                    ),
                )
            )
            return 3

    # ------------------------------------------------------------------
    # (e) Cross-component sweep — every sealed component's seal-diff
    # test by default; manifest-listed only when --scoped-sweep.
    # ------------------------------------------------------------------
    if scoped_sweep:
        sweep_components = [c.name for c in manifest.components]
    else:
        sweep_components = _discover_sealed_components(repo_root)
        if not sweep_components:
            _emit_diagnostic(
                _FailureCheckpoint(
                    code=3,
                    klass="sweep-discovery-empty",
                    detail=(
                        "cross-component sweep discovery found no "
                        "sealed components (no */tests/SEAL_COMMIT "
                        "marker files). Verify workspace layout and "
                        "re-invoke; or use --scoped-sweep to bypass."
                    ),
                )
            )
            return 3

    sweep_run: list[str] = []
    sweep_skipped: list[str] = []
    for comp_name in sweep_components:
        seal_diff = _seal_diff_test_path(repo_root, comp_name)
        if seal_diff is None:
            # No seal-diff test convention recognised for this
            # component — skip with a note (defensive).
            sweep_skipped.append(comp_name)
            continue
        rc, output = _run_pytest(repo_root, seal_diff)
        if rc != 0:
            _emit_diagnostic(
                _FailureCheckpoint(
                    code=3,
                    klass="cross-component-sweep-failed",
                    detail=(
                        f"sweep regression in '{comp_name}'\n"
                        f"  seal-diff test: {seal_diff.relative_to(repo_root)}\n\n"
                        + output
                        + "\nSidecar + narrative changes left "
                        "uncommitted. Fix the regression and re-invoke."
                    ),
                )
            )
            return 3
        sweep_run.append(comp_name)
    sweep_summary = (
        f"{len(sweep_run)} components green"
        + (
            f" ({len(sweep_skipped)} skipped — no seal-diff test recognised: "
            f"{', '.join(sweep_skipped)})"
            if sweep_skipped
            else ""
        )
    )

    # ------------------------------------------------------------------
    # (f) Stage + commit (AC.D-sa.1 steps (e) + (f), AC.D-sa.2).
    # T1.4 (AC.FBMT1.APS.1): the plan-doc + manifest rename pair (if
    # the archive step ran) is already staged by ``git mv``; ``git
    # add`` here covers sidecars + narrative target.
    # ------------------------------------------------------------------
    paths_to_stage: list[str] = []
    for comp in manifest.components:
        paths_to_stage.append(comp.sidecar)
    if manifest.narrative is not None:
        paths_to_stage.append(manifest.narrative.target)
    add_proc = subprocess.run(
        ["git", "add", "--"] + paths_to_stage,
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    if add_proc.returncode != 0:
        _emit_diagnostic(
            _FailureCheckpoint(
                code=3,
                klass="git-add-failed",
                detail=(
                    "git add failed:\n"
                    + (add_proc.stdout or "")
                    + (add_proc.stderr or "")
                ),
            )
        )
        return 3

    commit_message = _build_commit_message(
        manifest=manifest,
        amendment_sha=amendment_sha,
        bumped_sidecars=bumped_sidecars,
        narrative_target=narrative_target_str,
        sweep_summary=sweep_summary,
        include_co_authored_by=_claude_environment(),
    )
    commit_proc = subprocess.run(
        ["git", "commit", "-m", commit_message],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    if commit_proc.returncode != 0:
        _emit_diagnostic(
            _FailureCheckpoint(
                code=3,
                klass="git-commit-failed",
                detail=(
                    "git commit failed:\n"
                    + (commit_proc.stdout or "")
                    + (commit_proc.stderr or "")
                ),
            )
        )
        return 3

    seal_sha = _head_sha(repo_root)
    seal_subject = _commit_subject(repo_root, seal_sha)
    print(f"sealed: {seal_subject}")
    print(f"  amendment: {amendment_sha}")
    print(f"  seal:      {seal_sha}")

    # ------------------------------------------------------------------
    # (g) Post-seal apply --dry-run verification (AC.D-sa.1 step (g)).
    # On non-zero, leave the seal commit in place per D-4 ruling and
    # emit operator-actionable diagnostic. Per amendment #141
    # (AC.SCT.* family): the dry-run result is CAPTURED here and the
    # diagnostic emits at the failure point, but the early-return is
    # DEFERRED until after step (h) §14 backfill so the operator's
    # plan-doc method-decision register lands deterministically
    # regardless of dry-run outcome. The seal command's final return
    # code STILL equals ``dry_rc`` (AC.SCT.2); only step-(h)
    # reachability changes (AC.SCT.1).
    # T1.4: the manifest may have moved into ``docs/plans/sealed/``
    # as part of the seal commit; dry-run uses the post-archive path.
    # ------------------------------------------------------------------
    dry_rc = _apply_dry_run_post_seal(effective_manifest_path)
    if dry_rc != 0:
        _emit_diagnostic(
            _FailureCheckpoint(
                code=dry_rc,
                klass="post-seal-dry-run-failed",
                detail=(
                    f"post-seal `loam amend apply --dry-run` exited "
                    f"{dry_rc}. The seal commit at {seal_sha} HAS BEEN "
                    "LEFT IN PLACE per the no-amend CDC. Operator must "
                    "inspect the dry-run report above, identify the "
                    "missing admission or invariant violation, and "
                    "author a corrective commit (do not --amend). "
                    "Per amendment #141 AC.SCT.1, the §14 SHA backfill "
                    "(step (h) below) STILL fires when a --plan-doc was "
                    "supplied, so the plan-doc's method-decision "
                    "register lands as a separate follow-up commit "
                    "regardless of this dry-run failure."
                ),
            )
        )
        # NOTE: do NOT early-return here. The dry-run exit code is
        # captured in ``dry_rc`` and surfaces as the final return
        # value at the end of ``_finalize`` (AC.SCT.2). Falling
        # through allows step (h) to run unconditionally (AC.SCT.1).

    # ------------------------------------------------------------------
    # (h) Optional: plan-doc §14 SHA backfill (AC.D-sa.7).
    # Per amendment #141 AC.SCT.1: this step is reached
    # UNCONDITIONALLY on plan-doc presence after a seal commit lands,
    # regardless of the dry-run exit code captured in step (g). The
    # §14 register documents the seal commit SHA (not HEAD); the SHA
    # is computed at ``seal_sha`` above and is independent of any
    # corrective fixups the operator may author after a dry-run halt.
    # T1.4: when the archive step ran, ``effective_plan_doc`` points
    # at the new ``docs/plans/sealed/<slug>.md`` location; backfill
    # targets that path so the moved file is the one carrying the
    # SHA register.
    # ------------------------------------------------------------------
    if effective_plan_doc is not None:
        ck = _backfill_plan_doc_shas(
            plan_doc=effective_plan_doc,
            amendment_sha=amendment_sha,
            amendment_subject=amendment_subject,
            seal_sha=seal_sha,
            seal_subject=seal_subject,
        )
        if ck is not None:
            _emit_diagnostic(ck)
            return ck.code

        # Stage + commit the plan-doc edit.
        rel_plan_doc = effective_plan_doc.relative_to(repo_root)
        backfill_add = subprocess.run(
            ["git", "add", "--", str(rel_plan_doc)],
            cwd=repo_root,
            capture_output=True,
            text=True,
        )
        if backfill_add.returncode != 0:
            _emit_diagnostic(
                _FailureCheckpoint(
                    code=3,
                    klass="plan-doc-git-add-failed",
                    detail=(
                        "plan-doc git add failed:\n"
                        + (backfill_add.stdout or "")
                        + (backfill_add.stderr or "")
                        + "\nSeal commit is in place; plan-doc backfill "
                        "did not commit. Operator may author the "
                        "follow-up commit by hand."
                    ),
                )
            )
            return 3

        # If `git add` produced no staged change (idempotent re-run),
        # skip the commit instead of erroring on empty.
        # Per amendment #141 AC.SCT.3: the idempotent-no-op path no
        # longer early-returns; it falls through to step (i) FIDRAFT
        # cleanup-surface + the final ``return dry_rc`` so the FIDRAFT
        # cleanup surface fires + the dry-run exit code surfaces
        # unconditionally (preserving AC.SCT.2's exit-code contract).
        diff_check = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            cwd=repo_root,
        )
        backfill_committed = diff_check.returncode != 0
        if not backfill_committed:
            # Nothing staged — backfill was a no-op. That's fine.
            print(f"plan-doc {rel_plan_doc}: §14 SHAs already current.")

        # AC.DPS1.11: schema v3 manifests may omit ``amendment.number``;
        # the backfill subject + body identify by slug instead. The
        # commit-SHAs subsection itself is still keyed by the amendment
        # commit SHA, so it remains addressable.
        if backfill_committed:
            if manifest.number is None:
                backfill_subject = (
                    f"docs(plans): record {manifest.slug} commit SHAs "
                    "in method-decision register"
                )
                backfill_intro = (
                    f"Backfills the §14 commit-SHAs subsection of the "
                    f"{manifest.slug} plan with the actual amendment "
                    f"commit ({_short_sha(amendment_sha)}) and seal "
                    f"commit ({_short_sha(seal_sha)}) SHAs."
                )
            else:
                backfill_subject = (
                    f"docs(plans): record amendment #{manifest.number} "
                    "commit SHAs in method-decision register"
                )
                backfill_intro = (
                    f"Backfills the §14 commit-SHAs subsection of the "
                    f"amendment #{manifest.number} plan with the actual "
                    f"amendment commit ({_short_sha(amendment_sha)}) and "
                    f"seal commit ({_short_sha(seal_sha)}) SHAs."
                )
            backfill_body_lines = [
                backfill_subject,
                "",
                backfill_intro,
                "",
                "Mechanised by `loam amend seal --plan-doc` per AC.D-sa.7.",
            ]
            if _claude_environment():
                backfill_body_lines.extend(["", _CO_AUTHORED_BY])
            backfill_message = "\n".join(backfill_body_lines) + "\n"

            backfill_commit = subprocess.run(
                ["git", "commit", "-m", backfill_message],
                cwd=repo_root,
                capture_output=True,
                text=True,
            )
            if backfill_commit.returncode != 0:
                _emit_diagnostic(
                    _FailureCheckpoint(
                        code=3,
                        klass="plan-doc-commit-failed",
                        detail=(
                            "plan-doc git commit failed:\n"
                            + (backfill_commit.stdout or "")
                            + (backfill_commit.stderr or "")
                        ),
                    )
                )
                return 3
            backfill_sha = _head_sha(repo_root)
            print(
                f"plan-doc {rel_plan_doc}: §14 SHAs backfilled at "
                f"{_short_sha(backfill_sha)}"
            )

    # ------------------------------------------------------------------
    # (i) T1.3 (AC.FBMT1.FCS family) — FIDRAFT cleanup-on-seal hook.
    # Fires AFTER the seal commit + §14 backfill so the surface
    # appears as the final line of seal output. AC.FBMT1.FCS.4: the
    # ``skip_fidraft_cleanup`` flag bypasses the hook for emergency
    # seals where the operator wants to skip the surface.
    # ------------------------------------------------------------------
    if effective_plan_doc is not None and not skip_fidraft_cleanup:
        _emit_fidraft_cleanup_surface(
            plan_doc=effective_plan_doc, repo_root=repo_root
        )

    # Per amendment #141 AC.SCT.2: the seal command's final return
    # code equals the post-seal dry-run exit code (captured in step
    # (g) above). When dry-run passed cleanly, ``dry_rc`` is 0 and
    # this matches the pre-fix behaviour byte-for-byte. When dry-run
    # failed but step (h) §14 backfill landed (the AC.SCT.1 case),
    # the operator sees BOTH the dry-run failure diagnostic + the
    # §14 backfill commit + a non-zero exit code.
    return dry_rc


def run(
    manifest_path: Path,
    *,
    no_finalize: bool = False,
    scoped_sweep: bool = False,
    plan_doc: Path | None = None,
    allow_untracked_globs: Sequence[str] = (),
    skip_fidraft_cleanup: bool = False,
) -> int:
    try:
        manifest = load_manifest(manifest_path)
    except ManifestError as exc:
        print(f"invalid manifest: {exc}")
        return 2
    try:
        repo_root = find_repo_root(manifest_path.parent)
    except RuntimeError as exc:
        print(f"repo error: {exc}")
        return 3

    if no_finalize:
        # Pre-extension behaviour preserved byte-identically.
        # ``--allow-untracked-globs`` is a finalisation-pre-flight flag;
        # the legacy path doesn't dirty-check, so the flag has no effect.
        return _legacy_seal(manifest, repo_root)

    return _finalize(
        manifest,
        manifest_path,
        repo_root,
        scoped_sweep=scoped_sweep,
        plan_doc=plan_doc,
        allow_untracked_globs=allow_untracked_globs,
        skip_fidraft_cleanup=skip_fidraft_cleanup,
    )
