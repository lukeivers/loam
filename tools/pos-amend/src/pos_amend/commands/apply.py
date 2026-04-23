"""``pos-amend apply [--dry-run]`` — dry-run or mutate the tree per manifest."""

from __future__ import annotations

from pathlib import Path

from pos_amend.baseline import BaselineNotFound, set_baseline
from pos_amend.dry_run import analyse, format_reports
from pos_amend.manifest import ManifestError, load_manifest
from pos_amend.paths import find_repo_root
from pos_amend.seal_diff import BindingNotFound, widen_binding
from pos_amend.sidecar import write_sidecar


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

    # Real apply: (1) bump BASELINE literal, (2) widen allowed_* bindings,
    # (3) write sidecar to baseline (empty-diff window).
    changes: list[str] = []
    # Cross-component partners: every manifest-listed component's
    # top-level dir. Each component's seal-diff test sees the whole-repo
    # diff, so partner edits need admission on every seal-test.
    partner_prefixes = {f"{c.name}/" for c in manifest.components}
    for comp in manifest.components:
        seal_test_path = repo_root / comp.seal_test
        sidecar_path = repo_root / comp.sidecar
        if not seal_test_path.exists():
            print(f"skip {comp.name}: seal-test missing at {comp.seal_test}")
            continue
        # 1. BASELINE bump (skip for files with no BASELINE, e.g.
        # safety-layer; those shouldn't appear in a manifest but we
        # defend gracefully). When ``frozen_baseline`` is declared on
        # the component, the module-top literal is held fixed for the
        # project lifetime (amendment #23's frozen-H19 pattern) — skip
        # the bump entirely while still advancing the sidecar below.
        if comp.frozen_baseline:
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
        # partners (excluding self).
        partners = sorted(partner_prefixes - {f"{comp.name}/"})
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
        # 3. Sidecar → baseline (empty-diff window).
        if write_sidecar(sidecar_path, manifest.baseline):
            changes.append(f"{comp.name}: SEAL_COMMIT → {manifest.baseline}")

    if not changes:
        print("no changes (idempotent re-run)")
    else:
        print("applied:")
        for c in changes:
            print(f"  - {c}")
    return 0
