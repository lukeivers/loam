"""Shared-doc guard-floor coverage (AC.SDG.* / AC.SDC.* family).

Class C of the 2026-07-08 release-seal near-miss audit: a seal that edits
a doc **shared across components** must not be able to breach that doc's
content-guard unseen. The v1.11.0 failure — a ``primary-persona`` (recall)
seal grew the shared ``plugins/dev-sdlc/docs/odd-methodology.md`` past
``dev-sdlc``'s ``test_AC_KDOC_1`` line-count guard, which is neither a
fence test nor a ``guard-floor.yaml`` member, so no seal gate ran it.

This module supplies the DISCOVERY half of the fix (the registry half is
data in ``docs/plans/guard-floor.yaml``). It answers, from tracked files
only and deterministically:

- **What is the shared-doc surface?** The FILE-level ``universal_paths.files``
  union over current + sealed manifests (``docs/plans/*.manifest.yaml`` +
  ``docs/plans/sealed/*.manifest.yaml``) — the specific docs a manifest
  admits ANY cycle to edit, i.e. the seal-blast-radius admission set the
  failure lives in. PREFIX admissions are excluded (broad working spaces,
  not specific shared docs). The one known dev-mode relocation
  ``docs/<X>`` <-> ``plugins/dev-sdlc/docs/<X>`` (post-M6b.0) is normalized.
  (plan-doc §2 D-SDC.SURFACE / PREFIX-EXCLUDED / SUBST.)

- **Which tests are content guards on a doc?** A test with a module-level
  ``Path`` constant that resolves (repo-root-anchored via ``parents[N]``,
  following intra-module constant refs) EXACTLY to a tracked doc file, whose
  content is read (``.read_text`` / ``.splitlines`` / ``.read_bytes``) via
  that constant. This is the precise per-doc-pin signature of the KDOC-class
  failure; it excludes string-only allow-lists (fence / seal-diff tests),
  ``tmp_path`` fixtures, and ``rglob`` corpus sweeps.
  (plan-doc §2 D-SDC.GUARD-SHAPE.)

- **Is a guard floored?** Resolved against the live floor via
  :func:`loam_amend.guard_floor.discover_guard_floor` — a guard is covered
  when a floor target matches it exactly (file-glob) or contains it
  (directory pattern), never by exact-string registry match.
  (plan-doc §2 D-SDC.MEMBERSHIP.)

:func:`find_uncovered_shared_doc_guards` is the meta-check: it returns a
violation for every surface-doc content-guard that the supplied floor does
NOT cover — so the registry cannot silently rot as new shared-doc guards
appear (plan-doc §2 D-SDC.META-FLOORED; the meta-check test is itself a
registered floor member).
"""

from __future__ import annotations

import ast
import subprocess
from dataclasses import dataclass
from pathlib import Path

import yaml

from .guard_floor import GuardFloor

# Known dev-mode relocation (post-M6b.0): the long-form dev-sdlc discipline
# docs are declared in manifests at their normal-use ``docs/<X>`` path but
# live in the canonical tree at ``plugins/dev-sdlc/docs/<X>``. Surface
# membership is tested against BOTH forms so a guard reading the real path
# matches a declared normal-use surface entry. A future relocation extends
# this map; the meta-check's own coverage surfaces the resulting gap.
_DEVSDLC_DOCS_PREFIX = "plugins/dev-sdlc/docs/"
_NORMAL_USE_DOCS_PREFIX = "docs/"

_CONTENT_READ_MARKERS = (".read_text", ".splitlines", ".read_bytes")
_FENCE_BASENAMES = ("test_no_sealed_amendments.py", "test_cross_cutting.py")
_EXCLUDED_TEST_PREFIXES = ("docs/archive/",)
_DOC_SUFFIXES = (".md", ".txt", ".yaml", ".yml")


@dataclass(frozen=True)
class SharedDocGuardViolation:
    """One shared-doc content-guard that the floor does not cover.

    ``doc`` is the surface doc's repo-relative path; ``guard_test`` is the
    repo-relative path of the content-guard test not resolvable to a floor
    member; ``suggested_pattern`` is a ``guard-floor.yaml`` pattern that
    would register it (the exact test path — a valid fnmatch pattern that
    resolves to itself).
    """

    doc: str
    guard_test: str
    suggested_pattern: str


def _tracked_files(repo_root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    return [ln for ln in result.stdout.splitlines() if ln.strip()]


# ---------------------------------------------------------------------------
# Surface derivation (D-SDC.SURFACE / PREFIX-EXCLUDED / SUBST)
# ---------------------------------------------------------------------------
def _manifest_paths(tracked: list[str]) -> list[str]:
    """Tracked current + sealed manifest files (schema-agnostic yaml read).

    Deliberately a lightweight yaml read rather than the strict manifest
    validator: sealed manifests span schema versions, and only
    ``universal_paths.files`` is consumed here — a strict load would reject
    older shapes and shrink the surface (surface-rot).
    """
    out = []
    for t in tracked:
        if not t.endswith(".manifest.yaml"):
            continue
        if t.startswith("docs/plans/") and (
            t.count("/") == 2  # docs/plans/<x>.manifest.yaml
            or t.startswith("docs/plans/sealed/")
        ):
            out.append(t)
    return out


def shared_doc_surface(repo_root: Path) -> set[str]:
    """Repo-relative doc paths on the file-level universal-admitted surface.

    Union of ``universal_paths.files`` over current + sealed manifests,
    threshold-free (any manifest granting universal edit creates the
    cross-component-edit path), with the dev-mode relocation normalized so
    membership can be tested against either the normal-use or the real path.
    """
    tracked = _tracked_files(repo_root)
    declared: set[str] = set()
    for rel in _manifest_paths(tracked):
        try:
            data = yaml.safe_load((repo_root / rel).read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        up = data.get("universal_paths") or {}
        if not isinstance(up, dict):
            continue
        for f in up.get("files") or []:
            if isinstance(f, str) and f.strip():
                declared.add(f.strip())
    # Expand the known dev-mode relocation in BOTH directions so a guard
    # reading the real path matches a normal-use declaration and vice versa.
    surface = set(declared)
    for p in declared:
        if p.startswith(_NORMAL_USE_DOCS_PREFIX) and not p.startswith(
            _DEVSDLC_DOCS_PREFIX
        ):
            surface.add(_DEVSDLC_DOCS_PREFIX + p[len(_NORMAL_USE_DOCS_PREFIX):])
        if p.startswith(_DEVSDLC_DOCS_PREFIX):
            surface.add(
                _NORMAL_USE_DOCS_PREFIX + p[len(_DEVSDLC_DOCS_PREFIX):]
            )
    return surface


# ---------------------------------------------------------------------------
# Content-guard detection (D-SDC.GUARD-SHAPE)
# ---------------------------------------------------------------------------
def _is_root_anchor(node: ast.AST) -> bool:
    """``Path(__file__).resolve().parents[N]`` — treated as repo root.

    Any ``parents[N]`` is treated as the repo root: an over-/under-shot N
    yields a joined path that is not tracked, hence no match — the
    exact-tracked-existence check below keeps detection false-positive-free.
    """
    return (
        isinstance(node, ast.Subscript)
        and isinstance(node.value, ast.Attribute)
        and node.value.attr == "parents"
    )


def _resolve_path_expr(node: ast.AST, consts: dict[str, str]) -> str | None:
    """Repo-relative path if *node* is an exact repo-root-anchored ``Path``
    div-chain of string literals (following intra-module const refs); else
    ``None``. ``consts`` maps a resolved module constant name to its
    repo-relative prefix (``""`` == repo root)."""
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        left = _resolve_path_expr(node.left, consts)
        if left is None:
            return None
        right = node.right
        if isinstance(right, ast.Constant) and isinstance(right.value, str):
            return (left + "/" + right.value).lstrip("/")
        return None
    if isinstance(node, ast.Name):
        return consts.get(node.id)
    if _is_root_anchor(node):
        return ""
    return None


def _module_doc_constants(tree: ast.Module) -> dict[str, str]:
    """Map module-level ``Path`` constants to their resolved repo-rel path."""
    consts: dict[str, str] = {}
    # Seed repo-root anchors.
    for node in tree.body:
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and _is_root_anchor(node.value)
        ):
            consts[node.targets[0].id] = ""
    # Fixed-point over chained directory / file constants.
    for _ in range(6):
        changed = False
        for node in tree.body:
            if not (
                isinstance(node, ast.Assign)
                and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
            ):
                continue
            name = node.targets[0].id
            if name in consts:
                continue
            resolved = _resolve_path_expr(node.value, consts)
            if resolved is not None:
                consts[name] = resolved
                changed = True
        if not changed:
            break
    return consts


def _guarded_docs_in_test(test_rel: str, repo_root: Path, tracked: set[str]) -> set[str]:
    """Tracked doc paths whose content this test guards via a Path constant."""
    if test_rel.startswith(_EXCLUDED_TEST_PREFIXES):
        return set()
    if Path(test_rel).name in _FENCE_BASENAMES:
        return set()
    try:
        src = (repo_root / test_rel).read_text(encoding="utf-8")
        tree = ast.parse(src)
    except (OSError, SyntaxError):
        return set()
    consts = _module_doc_constants(tree)
    hits: set[str] = set()
    for name, path in consts.items():
        if not path.endswith(_DOC_SUFFIXES):
            continue
        if path not in tracked:
            continue
        if any(f"{name}{marker}" in src for marker in _CONTENT_READ_MARKERS):
            hits.add(path)
    return hits


def content_guards(repo_root: Path) -> dict[str, set[str]]:
    """Map every tracked doc -> the set of tests that content-guard it."""
    tracked_list = _tracked_files(repo_root)
    tracked = set(tracked_list)
    out: dict[str, set[str]] = {}
    for t in tracked_list:
        if not (t.endswith(".py") and "/tests/" in t and Path(t).name.startswith("test_")):
            continue
        for doc in _guarded_docs_in_test(t, repo_root, tracked):
            out.setdefault(doc, set()).add(t)
    return out


def shared_doc_guards(repo_root: Path) -> dict[str, set[str]]:
    """Content guards restricted to docs on the shared-doc surface."""
    surface = shared_doc_surface(repo_root)
    return {
        doc: tests
        for doc, tests in content_guards(repo_root).items()
        if doc in surface
    }


# ---------------------------------------------------------------------------
# The meta-check (D-SDC.MEMBERSHIP / META-FLOORED)
# ---------------------------------------------------------------------------
def _is_floored(guard_test: str, floor: GuardFloor) -> bool:
    """True iff a floor target matches (file-glob) or contains (directory)
    *guard_test*. Reuses the resolved floor targets — never exact-string
    registry matching, so a guard covered by a directory pattern counts."""
    for target in floor.targets:
        t = str(target)
        if guard_test == t or guard_test.startswith(t + "/"):
            return True
    return False


def find_uncovered_shared_doc_guards(
    repo_root: Path, floor: GuardFloor
) -> list[SharedDocGuardViolation]:
    """Every shared-doc content-guard the *floor* does not cover.

    The meta-check. An empty list means the floor covers every content guard
    on every file-level universal-admitted doc (registry complete). A
    non-empty list is registry rot: each violation names the doc, the
    uncovered guard test, and a corrective ``guard-floor.yaml`` pattern.
    """
    violations: list[SharedDocGuardViolation] = []
    for doc, tests in shared_doc_guards(repo_root).items():
        for guard_test in sorted(tests):
            if not _is_floored(guard_test, floor):
                violations.append(
                    SharedDocGuardViolation(
                        doc=doc,
                        guard_test=guard_test,
                        suggested_pattern=guard_test,
                    )
                )
    return sorted(violations, key=lambda v: (v.doc, v.guard_test))
