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
doc's ``## 14.`` heading and create a follow-up
``docs(plans): record amendment #N commit SHAs ...`` commit.
"""

from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from loam_amend.commands import apply as apply_cmd
from loam_amend.manifest import Manifest, ManifestError, load_manifest
from loam_amend.narrative import append_narrative
from loam_amend.paths import find_repo_root
from loam_amend.sidecar import write_sidecar
from loam_amend.tracker_registration import (
    TrackerUnavailableError,
    update_source_commits,
)


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


def _working_tree_dirty(repo_root: Path, ignore_paths: set[Path]) -> list[str]:
    """Return list of dirty paths NOT in *ignore_paths*.

    *ignore_paths* are repo-relative paths the seal step is itself
    expected to have written (sidecars + narrative target + plan doc).
    Anything else dirty at invocation time is unrelated dirt and the
    seal step refuses to proceed (AC.D-sa.5 case (c)).
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
        if rel not in ignore_paths:
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
    # `docs/rebuild/plans/pos-amend-halt-visibility.md`.
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

    # Locate the "## 14." heading. Accept "## 14. " or "## 14 " as
    # the canonical shape per AC.D-sa.7 wording.
    section_header_re = re.compile(r"^## 14[.\s]", re.MULTILINE)
    m = section_header_re.search(text)
    if m is None:
        return _FailureCheckpoint(
            code=3,
            klass="plan-doc-missing-section-14",
            detail=(
                f"plan doc has no '## 14.' heading: {plan_doc}\n"
                "AC.D-sa.7 requires the designated plan doc to "
                "carry the §14 method-decision-record heading. The "
                "seal commit has been left in place. Operator may "
                "author the §14 prose + SHA subsection by hand."
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


def _legacy_seal(manifest: Manifest, repo_root: Path) -> int:
    """Pre-extension behaviour: advance sidecars + append narrative.

    Used when ``--no-finalize`` is set. Output and exit-code semantics
    are byte-identical to pre-extension ``loam amend seal``.
    """
    sha = _head_sha(repo_root)
    changes: list[str] = []
    for comp in manifest.components:
        sidecar_path = repo_root / comp.sidecar
        if write_sidecar(sidecar_path, sha):
            changes.append(f"{comp.name}: SEAL_COMMIT → {sha}")
    if manifest.narrative is not None:
        target = repo_root / manifest.narrative.target
        if append_narrative(target, manifest.narrative.body):
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


def _finalize(
    manifest: Manifest,
    manifest_path: Path,
    repo_root: Path,
    *,
    scoped_sweep: bool,
    plan_doc: Path | None,
) -> int:
    """Full finalisation per AC.D-sa.1 + AC.D-sa.5 + AC.D-sa.7."""

    # ------------------------------------------------------------------
    # (a) Resolve the amendment SHA (current HEAD).
    # ------------------------------------------------------------------
    amendment_sha = _head_sha(repo_root)
    amendment_subject = _commit_subject(repo_root, amendment_sha)

    # Compute the set of paths the seal step is itself expected to
    # write (so `git status` dirt-checking can ignore them).
    expected_writes: set[Path] = set()
    for comp in manifest.components:
        expected_writes.add(Path(comp.sidecar))
    if manifest.narrative is not None:
        expected_writes.add(Path(manifest.narrative.target))

    # ------------------------------------------------------------------
    # (b) Pre-flight: refuse to proceed on unrelated dirty state
    # (case (c) of AC.D-sa.5).
    # ------------------------------------------------------------------
    dirty = _working_tree_dirty(repo_root, expected_writes)
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
        if append_narrative(target, manifest.narrative.body):
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
    # ------------------------------------------------------------------
    for comp in manifest.components:
        # Post-D.1: components live under framework/<name>/.
        comp_tests = repo_root / "framework" / comp.name / "tests"
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
    # emit operator-actionable diagnostic.
    # ------------------------------------------------------------------
    dry_rc = _apply_dry_run_post_seal(manifest_path)
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
                    "author a corrective commit (do not --amend)."
                ),
            )
        )
        return dry_rc

    # ------------------------------------------------------------------
    # (h) Optional: plan-doc §14 SHA backfill (AC.D-sa.7).
    # ------------------------------------------------------------------
    if plan_doc is not None:
        ck = _backfill_plan_doc_shas(
            plan_doc=plan_doc,
            amendment_sha=amendment_sha,
            amendment_subject=amendment_subject,
            seal_sha=seal_sha,
            seal_subject=seal_subject,
        )
        if ck is not None:
            _emit_diagnostic(ck)
            return ck.code

        # Stage + commit the plan-doc edit.
        rel_plan_doc = plan_doc.relative_to(repo_root)
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
        diff_check = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            cwd=repo_root,
        )
        if diff_check.returncode == 0:
            # Nothing staged — backfill was a no-op. That's fine.
            print(f"plan-doc {rel_plan_doc}: §14 SHAs already current.")
            return 0

        backfill_subject = (
            f"docs(plans): record amendment #{manifest.number} "
            "commit SHAs in method-decision register"
        )
        backfill_body_lines = [
            backfill_subject,
            "",
            (
                f"Backfills the §14 commit-SHAs subsection of the "
                f"amendment #{manifest.number} plan with the actual "
                f"amendment commit ({_short_sha(amendment_sha)}) and "
                f"seal commit ({_short_sha(seal_sha)}) SHAs."
            ),
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

    return 0


def run(
    manifest_path: Path,
    *,
    no_finalize: bool = False,
    scoped_sweep: bool = False,
    plan_doc: Path | None = None,
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
        return _legacy_seal(manifest, repo_root)

    return _finalize(
        manifest,
        manifest_path,
        repo_root,
        scoped_sweep=scoped_sweep,
        plan_doc=plan_doc,
    )
