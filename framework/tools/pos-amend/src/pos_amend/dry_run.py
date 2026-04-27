"""Simulate the seal-diff check for a manifest without mutating the tree.

For each component declared in the manifest, we:
 1. Compute ``git diff --name-only <manifest.baseline>..HEAD``.
 2. Resolve the component's current ``allowed_prefixes`` + ``allowed_files``
    from the seal-test file's literals.
 3. Union those with the manifest's universal + per-component extras.
 4. Report any changed path not admitted.

T9 requires exit-0 when every path is admitted.
T10 requires exit-non-0 with the offending path named when a change is
unadmitted.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from pos_amend.manifest import ComponentEntry, Manifest
from pos_amend.seal_diff import BindingNotFound, read_entries


@dataclass(frozen=True)
class ComponentReport:
    name: str
    missing_admissions: tuple[str, ...]
    would_widen_prefixes: tuple[str, ...]
    would_widen_files: tuple[str, ...]
    skipped_reason: str | None = None

    @property
    def ok(self) -> bool:
        return not self.missing_admissions and self.skipped_reason is None


def _git_diff_names(repo_root: Path, baseline: str, ref: str = "HEAD") -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{baseline}..{ref}"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    return [ln for ln in result.stdout.splitlines() if ln.strip()]


def _diff_with_working_tree(repo_root: Path, baseline: str) -> list[str]:
    """Return paths that would be part of the next commit.

    This is: everything already committed in baseline..HEAD, plus
    currently-staged (tracked) edits, plus tracked-but-unstaged edits.
    Untracked files are NOT included — they would not be part of a
    `git commit` without an explicit `git add`.
    """
    changed = set(_git_diff_names(repo_root, baseline, "HEAD"))
    # status --porcelain with XY status chars. Include tracked files only
    # (any line where neither X nor Y is '?'). Untracked ('??') are skipped.
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    for line in result.stdout.splitlines():
        if not line or len(line) < 3:
            continue
        x, y = line[0], line[1]
        if x == "?" and y == "?":
            # untracked — would need explicit `git add` to land in a commit
            continue
        path = line[3:]
        if " -> " in path:
            # rename: consider the destination
            path = path.split(" -> ", 1)[1]
        changed.add(path.strip())
    return sorted(changed)


def _cross_component_prefixes(manifest: Manifest, self_name: str) -> set[str]:
    """Return the set of partner-component prefixes for *self_name*.

    Multi-component amendments need each component's seal-diff test to
    admit the other components' top-level dirs (the whole-repo diff sees
    partner edits). Per research doc §2.3, this is derivable from the
    manifest's component set. Post-D.1 (directory restructure):
    components live under ``framework/`` so partner prefixes are
    ``framework/<name>/`` (e.g. ``cost-governance`` →
    ``framework/cost-governance/``). The pre-D.1 ``<name>/`` form is
    kept alongside for back-compat with pre-restructure baselines that
    show old-path deletions in the diff window.
    """
    out: set[str] = set()
    for c in manifest.components:
        if c.name == self_name:
            continue
        out.add(f"framework/{c.name}/")
        # Back-compat: include the bare ``<name>/`` prefix so renames
        # showing the deletion side (old path) are admitted across
        # the D.1 amendment window.
        out.add(f"{c.name}/")
    return out


def analyse(manifest: Manifest, repo_root: Path) -> list[ComponentReport]:
    """Run the dry-run analysis and return one report per component."""
    changed = _diff_with_working_tree(repo_root, manifest.baseline)
    reports: list[ComponentReport] = []
    for comp in manifest.components:
        reports.append(_analyse_component(comp, manifest, repo_root, changed))
    return reports


def _analyse_component(
    comp: ComponentEntry,
    manifest: Manifest,
    repo_root: Path,
    changed: list[str],
) -> ComponentReport:
    seal_test_path = repo_root / comp.seal_test
    if not seal_test_path.exists():
        return ComponentReport(
            name=comp.name,
            missing_admissions=(),
            would_widen_prefixes=(),
            would_widen_files=(),
            skipped_reason=f"seal-test file missing: {comp.seal_test}",
        )
    # Resolve the component's current admissions.
    try:
        current_prefixes = read_entries(seal_test_path, "allowed_prefixes")
    except BindingNotFound:
        current_prefixes = []
    try:
        current_files = read_entries(seal_test_path, "allowed_files")
    except BindingNotFound:
        current_files = []

    # Hands-off-lifecycle uses an ``allowed`` set of top-level dirs in
    # test_cross_cutting.py instead of allowed_prefixes; try that fallback.
    if not current_prefixes and not current_files:
        try:
            current_top_level = read_entries(seal_test_path, "allowed")
            # The top-level set admits whole first-segment directories.
            # For dry-run purposes, treat each entry as a prefix of form
            # "<entry>/" OR as an allowed_file for single-file entries.
            prefixes: list[str] = []
            files: list[str] = []
            for entry in current_top_level:
                if "/" in entry or "." in entry:
                    # path-like or file-like (e.g. "README.md",
                    # "first-run-inventory.yaml", ".claude")
                    if entry.endswith("/") or "." not in entry.split("/")[-1]:
                        prefixes.append(entry.rstrip("/") + "/")
                    else:
                        files.append(entry)
                else:
                    prefixes.append(entry + "/")
            current_prefixes = prefixes
            current_files = files
        except BindingNotFound:
            pass

    admitted_prefixes = set(current_prefixes)
    admitted_files = set(current_files)
    admitted_prefixes.update(manifest.universal_paths.prefixes)
    admitted_files.update(manifest.universal_paths.files)
    admitted_prefixes.update(comp.extra_allowed_prefixes)
    admitted_files.update(comp.extra_allowed_files)
    # Cross-component partners: every other manifest-listed component's
    # top-level dir. The seal-diff test sees the whole-repo diff, so
    # partner edits must be admitted on each component.
    admitted_prefixes.update(_cross_component_prefixes(manifest, comp.name))

    missing: list[str] = []
    for path in changed:
        if any(path.startswith(p) for p in admitted_prefixes):
            continue
        if path in admitted_files:
            continue
        missing.append(path)

    would_widen_prefixes = tuple(
        sorted(set(manifest.universal_paths.prefixes) - set(current_prefixes))
    )
    would_widen_files = tuple(
        sorted(set(manifest.universal_paths.files) - set(current_files))
    )

    return ComponentReport(
        name=comp.name,
        missing_admissions=tuple(missing),
        would_widen_prefixes=would_widen_prefixes,
        would_widen_files=would_widen_files,
    )


def format_reports(reports: list[ComponentReport]) -> str:
    lines: list[str] = []
    for r in reports:
        lines.append(f"[{r.name}]")
        if r.skipped_reason:
            lines.append(f"  skipped: {r.skipped_reason}")
            continue
        if r.missing_admissions:
            lines.append("  MISSING_ADMISSION:")
            for p in r.missing_admissions:
                lines.append(f"    - {p}")
        if r.would_widen_prefixes or r.would_widen_files:
            lines.append("  WOULD_WIDEN (info):")
            for p in r.would_widen_prefixes:
                lines.append(f"    + prefix: {p}")
            for f in r.would_widen_files:
                lines.append(f"    + file: {f}")
        if r.ok and not r.would_widen_prefixes and not r.would_widen_files:
            lines.append("  ok")
    return "\n".join(lines)
