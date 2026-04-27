"""``pos-amend apply [--dry-run]`` — dry-run or mutate the tree per manifest.

Schema-v2 manifests carrying an ``objectives`` block additionally
register ObjectiveSpec records into the workspace's tracker DB at
the start of the (non-dry-run) apply step. See
``pos-amend-tracker-integration.md`` AC.D-pa.1 / AC.D-pa.2 / AC.D-pa.5.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from pos_amend.baseline import BaselineNotFound, read_baseline, set_baseline
from pos_amend.dry_run import analyse, format_reports
from pos_amend.manifest import ManifestError, load_manifest
from pos_amend.paths import find_repo_root
from pos_amend.rename_detection import is_rename_only
from pos_amend.seal_diff import BindingNotFound, widen_binding
from pos_amend.sidecar import read_sidecar, write_sidecar
from pos_amend.tracker_registration import (
    TrackerUnavailableError,
    register_objectives,
)


def _git_head_sha(repo_root: Path) -> str:
    """Return the resolved HEAD SHA at *repo_root*."""
    proc = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout.strip()


def run(manifest_path: Path, *, dry_run: bool) -> int:
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

    if dry_run:
        reports = analyse(manifest, repo_root)
        print(format_reports(reports))
        if any(r.missing_admissions or r.skipped_reason for r in reports):
            return 1
        return 0

    # AC.D-pa.1 + AC.D-pa.2 + AC.D-pa.5: register the manifest's
    # ``objectives`` block (if any) BEFORE the BASELINE / sidecar /
    # widening edits. Putting the registration first means a tracker-
    # unavailable failure leaves the tree absolutely untouched (no
    # partial-state rollback needed). v1 manifests have an empty
    # ``manifest.objectives`` tuple and the helper is a no-op.
    if manifest.objectives:
        try:
            result = register_objectives(manifest, repo_root)
        except TrackerUnavailableError as exc:
            print(f"halt: {exc.klass}")
            print(exc.detail)
            return 3
        if result.created:
            print(f"registered {len(result.created)} objective(s):")
            for ac in result.created:
                print(f"  + {ac}")
        if result.skipped:
            print(
                f"skipped {len(result.skipped)} already-registered "
                "objective(s):"
            )
            for ac in result.skipped:
                print(f"  = {ac}")

    # Real apply: (1) bump BASELINE literal, (2) widen allowed_* bindings,
    # (3) write sidecar to baseline (empty-diff window).
    changes: list[str] = []
    # Cross-component partners: every manifest-listed component's
    # top-level dir. Each component's seal-diff test sees the whole-repo
    # diff, so partner edits need admission on every seal-test.
    # Post-D.1: components live under framework/<name>/ so partner
    # prefixes carry both the new framework/ form and the bare-<name>
    # form (for back-compat with pre-D.1 baselines whose diffs show
    # the deletion side of the rename pair).
    partner_prefixes: set[str] = set()
    for _c in manifest.components:
        partner_prefixes.add(f"framework/{_c.name}/")
        partner_prefixes.add(f"{_c.name}/")
    # AC.D.1.5.1 / AC.D.1.5.2 (amendment #62): per-component
    # rename-only verdict. Computed once per component up-front so the
    # diagnostic line carries the prior-state SHAs from the same read
    # the conditional bump branches on.
    head_sha = _git_head_sha(repo_root)
    # AC.D.1.5.5 (amendment #62): components named in
    # ``cleanup_directives:`` are bypassed by the standard component
    # loop. The cleanup-pass below writes their pre-bump values
    # explicitly; bumping then reverting in one apply is wasteful and
    # produces noise in the diagnostic output.
    cleanup_protected = {d.comp_name for d in manifest.cleanup_directives}
    for comp in manifest.components:
        seal_test_path = repo_root / comp.seal_test
        sidecar_path = repo_root / comp.sidecar
        if not seal_test_path.exists():
            print(f"skip {comp.name}: seal-test missing at {comp.seal_test}")
            continue

        # If a cleanup_directive applies to this component, the cleanup
        # pass below handles BASELINE + SEAL_COMMIT. Standard loop
        # widens admissions only.
        if comp.name in cleanup_protected:
            # Still run the widening pass so prefix admissions advance
            # for downstream amendments. Skip bumps + sidecar advance.
            partners = sorted(
                partner_prefixes - {f"{comp.name}/", f"framework/{comp.name}/"}
            )
            prefixes = (
                list(manifest.universal_paths.prefixes)
                + list(comp.extra_allowed_prefixes)
                + partners
            )
            files = (
                list(manifest.universal_paths.files)
                + list(comp.extra_allowed_files)
            )
            if prefixes:
                try:
                    did, _new, added = widen_binding(
                        seal_test_path,
                        "allowed_prefixes",
                        prefixes,
                        mode="tuple",
                    )
                    if did:
                        changes.append(
                            f"{comp.name}: allowed_prefixes += {added!r}"
                        )
                except BindingNotFound:
                    pass
            if files:
                try:
                    did, _new, added = widen_binding(
                        seal_test_path,
                        "allowed_files",
                        files,
                        mode="set",
                        create_if_missing_after="allowed_prefixes",
                    )
                    if did:
                        changes.append(
                            f"{comp.name}: allowed_files += {added!r}"
                        )
                except BindingNotFound:
                    pass
            continue

        # Rename-only verdict for the component's BASELINE..HEAD window.
        # When True: skip BASELINE + sidecar bumps; widening still runs.
        # See `pos_amend.rename_detection.is_rename_only` + plan-doc
        # AC.D.1.5.1.
        rename_only = is_rename_only(
            repo_root,
            baseline=manifest.baseline,
            head=head_sha,
            old_path=f"{comp.name}/",
            new_path=f"framework/{comp.name}/",
        )
        if rename_only:
            # Read the prior-state SHAs for the diagnostic line. Use
            # defensive defaults if the sidecar/BASELINE is missing.
            try:
                prior_baseline = read_baseline(seal_test_path)
            except BaselineNotFound:
                prior_baseline = "(no BASELINE literal)"
            prior_seal_commit = read_sidecar(sidecar_path) or "(empty)"
            print(
                f"note {comp.name}: rename-only — "
                f"BASELINE preserved at {prior_baseline}; "
                f"SEAL_COMMIT preserved at {prior_seal_commit}; "
                f"allowed_prefixes widened."
            )
            changes.append(
                f"{comp.name}: rename-only (BASELINE + SEAL_COMMIT preserved)"
            )
        # 1. BASELINE bump (skip for files with no BASELINE, e.g.
        # safety-layer; those shouldn't appear in a manifest but we
        # defend gracefully). When ``frozen_baseline`` is declared on
        # the component, the module-top literal is held fixed for the
        # project lifetime (amendment #23's frozen-H19 pattern) — skip
        # the bump entirely while still advancing the sidecar below.
        # When the component is rename-only (D.1.5), skip the literal
        # bump — the fence didn't conceptually move.
        if rename_only:
            pass  # explicit no-op
        elif comp.frozen_baseline:
            print(
                f"note {comp.name}: BASELINE frozen — skipping literal bump"
            )
        else:
            try:
                changed = set_baseline(seal_test_path, manifest.baseline)
                if changed:
                    changes.append(f"{comp.name}: BASELINE → {manifest.baseline}")
            except BaselineNotFound:
                print(f"note {comp.name}: no BASELINE literal (structural test?)")
        # 2. Widen bindings with universal + extras + cross-component
        # partners (excluding self — both pre- and post-D.1 self forms).
        partners = sorted(
            partner_prefixes - {f"{comp.name}/", f"framework/{comp.name}/"}
        )
        prefixes = (
            list(manifest.universal_paths.prefixes)
            + list(comp.extra_allowed_prefixes)
            + partners
        )
        files = list(manifest.universal_paths.files) + list(comp.extra_allowed_files)
        if prefixes:
            try:
                did, _new, added = widen_binding(
                    seal_test_path, "allowed_prefixes", prefixes, mode="tuple"
                )
                if did:
                    changes.append(
                        f"{comp.name}: allowed_prefixes += {added!r}"
                    )
            except BindingNotFound:
                # Fallback: hands-off-lifecycle's test_cross_cutting.py
                # checks first-path-segments against an ``allowed`` set.
                # Translate each prefix to its first segment.
                try:
                    first_segs = sorted(
                        {p.rstrip("/").split("/", 1)[0] for p in prefixes}
                    )
                    did, _new, added = widen_binding(
                        seal_test_path, "allowed", first_segs, mode="set"
                    )
                    if did:
                        changes.append(
                            f"{comp.name}: allowed (top-level) += {added!r}"
                        )
                except BindingNotFound:
                    print(
                        f"note {comp.name}: neither allowed_prefixes nor "
                        f"allowed binding found; skipping prefix widening"
                    )
        if files:
            # Prefer a conventional `allowed_files` binding. If absent,
            # synthesize it after `allowed_prefixes` as an empty set
            # stub and then widen. Hands-off-lifecycle uses a different
            # `allowed` top-level-dir set — fall back to widening that
            # with first-segments when no conventional form is present.
            try:
                did, _new, added = widen_binding(
                    seal_test_path,
                    "allowed_files",
                    files,
                    mode="set",
                    create_if_missing_after="allowed_prefixes",
                )
                if did:
                    changes.append(f"{comp.name}: allowed_files += {added!r}")
            except BindingNotFound:
                try:
                    first_segs = sorted({f.split("/", 1)[0] for f in files})
                    did, _new, added = widen_binding(
                        seal_test_path, "allowed", first_segs, mode="set"
                    )
                    if did:
                        changes.append(
                            f"{comp.name}: allowed (top-level) += {added!r}"
                        )
                except BindingNotFound:
                    print(
                        f"note {comp.name}: neither allowed_files nor "
                        f"allowed binding found; skipping file widening"
                    )
        # 3. Sidecar → baseline (empty-diff window). Skipped on
        # rename-only components (D.1.5) — the fence's prior sidecar
        # value is preserved.
        if not rename_only:
            if write_sidecar(sidecar_path, manifest.baseline):
                changes.append(f"{comp.name}: SEAL_COMMIT → {manifest.baseline}")

    # AC.D.1.5.5 (amendment #62): retroactive cleanup directives.
    # After the standard component loop, walk any cleanup_directives
    # the manifest declared and write the pre-bump BASELINE +
    # SEAL_COMMIT values back into each named component's seal-test +
    # sidecar. Each directive's ``comp_name`` must resolve to a
    # corresponding entry in the manifest's ``components:`` list (the
    # seal step also consults the cleanup_directives set and skips
    # its standard sidecar bump for those components — see
    # ``commands/seal.py`` _finalize). Idempotent.
    if manifest.cleanup_directives:
        comp_by_name = {c.name: c for c in manifest.components}
        for directive in manifest.cleanup_directives:
            comp = comp_by_name.get(directive.comp_name)
            if comp is None:
                print(
                    f"halt: cleanup_directive references unknown "
                    f"comp_name {directive.comp_name!r}; declare it "
                    f"under 'components:' or remove the directive"
                )
                return 4
            seal_test_path = repo_root / comp.seal_test
            sidecar_path = repo_root / comp.sidecar
            if not seal_test_path.exists():
                print(
                    f"skip cleanup {directive.comp_name}: seal-test missing"
                )
                continue
            try:
                changed = set_baseline(seal_test_path, directive.pre_baseline)
                if changed:
                    changes.append(
                        f"{directive.comp_name}: BASELINE reverted to "
                        f"{directive.pre_baseline}"
                    )
            except BaselineNotFound:
                print(
                    f"note cleanup {directive.comp_name}: no BASELINE literal"
                )
            if write_sidecar(sidecar_path, directive.pre_seal_commit):
                changes.append(
                    f"{directive.comp_name}: SEAL_COMMIT reverted to "
                    f"{directive.pre_seal_commit}"
                )

    if not changes:
        print("no changes (idempotent re-run)")
    else:
        print("applied:")
        for c in changes:
            print(f"  - {c}")
    return 0
