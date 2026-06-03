"""The per-project STATE probe spec for the Cairn repo (Slice C, P4-1).

Cairn is a SEPARATE repo (``/Users/lukeivers/cairn``) that does NOT use
loam's seal-sidecar markers. Its durable, Tier-0 ground-truth build
markers are:

  1. the ``src/cairn/<module>/`` directory is present with at least one
     non-``__init__`` implementation file, AND
  2. the git commit that FIRST added that module is an ancestor of HEAD
     (the module landed on the mainline via its merged feature PR).

Both are facts that cannot drift: a directory on disk and a
``merge-base --is-ancestor`` git verdict. This is the direct analogue of
loam's seal-sidecar ancestry classifier (:func:`probe.classify_build_status`),
re-keyed to Cairn's real markers — proving the STATE engine generalizes
to a separate repo, not merely a second loam-shaped hardcode.

The diagnosis (loam-fbm-project-status-accuracy-diagnosis-and-fix.md)
named BUILD-PLAN presence + ``pytest --collect-only`` as candidate
markers. At build time the BUILD-PLANs had been removed by Cairn's
professionalism scrub (commit ``c0e750a``) and ``pytest --collect-only``
on a single cairn module returns "no tests collected" (rootdir/conftest
fragility) — neither is a durable ground-truth signal. The present-module
+ merged-introducing-commit markers ARE durable, which is why they are
the classifier here.

This module REUSES the repo-agnostic engine: the :class:`Liveness`
classes, the :class:`ComponentState` row shape, the :class:`StateOfLoam`
record, and the ``merge-base --is-ancestor`` git probe. The ONLY new
logic is the module-presence + introducing-commit build classifier.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from loam_cli.audit.probe import Liveness, _git_is_ancestor
from loam_cli.audit.record import ComponentState, StateOfLoam, _head_sha

#: The live Cairn repo root (per the diagnosis + owner mandate). Tests
#: override this with a fixture repo; production reads the live repo.
DEFAULT_CAIRN_REPO_ROOT = Path("/Users/lukeivers/cairn")

#: Where Cairn's modules live, relative to the repo root.
_CAIRN_SRC = "src/cairn"


@dataclass(frozen=True)
class ModuleProbeSpec:
    """A Cairn build-class probe spec: a name + the module directory
    (relative to repo root) whose presence + introducing-commit ancestry
    is the ground-truth build marker.
    """

    name: str
    module_relpath: str


def _module_impl_files(module_dir: Path) -> list[Path]:
    """Non-``__init__``, non-test ``.py`` implementation files in a
    module dir. A directory with only ``__init__.py`` (or nothing) is a
    stub, not a built module.
    """
    if not module_dir.is_dir():
        return []
    out: list[Path] = []
    for p in module_dir.glob("*.py"):
        if p.name == "__init__.py":
            continue
        if p.name.startswith("test_"):
            continue
        out.append(p)
    return out


def _first_add_commit(repo_root: Path, module_relpath: str) -> str | None:
    """The git SHA that FIRST added the module directory (the merged
    feature-PR commit that introduced it), or ``None`` when git cannot
    resolve one.

    Uses ``git log --reverse --diff-filter=A`` over the module path and
    takes the earliest add — the introduction point. This is Cairn's
    equivalent of loam's pinned seal SHA, derived from the ref graph
    rather than a sidecar.
    """
    proc = subprocess.run(
        [
            "git",
            "log",
            "--reverse",
            "--diff-filter=A",
            "--format=%H",
            "--",
            module_relpath,
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return None
    lines = [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]
    return lines[0] if lines else None


def classify_module_build_status(
    repo_root: Path,
    module_relpath: str,
) -> tuple[Liveness, str]:
    """Classify a Cairn module's build state from Cairn's REAL markers.

    Resolution (ground-truth only — no seal sidecar, no prose):

      * module dir ABSENT or has no impl file → :attr:`Liveness.UNBUILT`
        (never built — nothing on disk).
      * module PRESENT (≥1 impl file) AND its introducing commit is an
        ancestor of HEAD → :attr:`Liveness.MERGED` (built and on the
        mainline — the fully-shipped state, mirroring loam's
        seal-ancestor MERGED).
      * module PRESENT but its introducing commit is a real commit NOT
        reachable from HEAD → :attr:`Liveness.SEALED` (present on a side
        branch, not merged into the current line).
      * module PRESENT but git cannot resolve / verify the introducing
        commit → :attr:`Liveness.UNKNOWN` (fail-safe: never a false
        green).

    Returns (liveness, evidence) — evidence is the human-readable trail
    that produced the class, matching the engine's evidence convention.
    """
    module_dir = repo_root / module_relpath
    impl_files = _module_impl_files(module_dir)
    if not impl_files:
        return (
            Liveness.UNBUILT,
            f"no module at {module_relpath} (absent or only a stub __init__)",
        )

    intro = _first_add_commit(repo_root, module_relpath)
    n_impl = len(impl_files)
    if intro is None:
        return (
            Liveness.UNKNOWN,
            f"{module_relpath} present ({n_impl} impl files) but git could "
            f"not resolve its introducing commit (indeterminate — fail-safe)",
        )

    ancestry = _git_is_ancestor(repo_root, intro)
    if ancestry is True:
        return (
            Liveness.MERGED,
            f"{module_relpath} present ({n_impl} impl files); introducing "
            f"commit {intro[:9]} is an ancestor of HEAD (merged on mainline)",
        )
    if ancestry is False:
        return (
            Liveness.SEALED,
            f"{module_relpath} present ({n_impl} impl files); introducing "
            f"commit {intro[:9]} not reachable from HEAD (side branch)",
        )
    return (
        Liveness.UNKNOWN,
        f"{module_relpath} present ({n_impl} impl files); introducing "
        f"commit {intro[:9]} not a known git object (indeterminate — fail-safe)",
    )


def default_cairn_module_specs() -> tuple[ModuleProbeSpec, ...]:
    """Cairn's built Layer-A engine modules — the markers whose build
    status the persona got WRONG ("the engine isn't usable,
    verify/execute/ledger remain") and that this slice reproduces as
    BUILT from ground truth.
    """
    return (
        ModuleProbeSpec(name="verify", module_relpath=f"{_CAIRN_SRC}/verify"),
        ModuleProbeSpec(name="ledger", module_relpath=f"{_CAIRN_SRC}/ledger"),
        ModuleProbeSpec(name="execute", module_relpath=f"{_CAIRN_SRC}/execute"),
        ModuleProbeSpec(name="pilot", module_relpath=f"{_CAIRN_SRC}/pilot"),
        ModuleProbeSpec(name="cause", module_relpath=f"{_CAIRN_SRC}/cause"),
    )


def cairn_state_record(
    repo_root: Path | None = None,
    *,
    module_specs: tuple[ModuleProbeSpec, ...] | None = None,
) -> StateOfLoam:
    """Generate Cairn's per-project STATE record FRESH from ground truth.

    Reuses the engine's :class:`StateOfLoam` / :class:`ComponentState`
    record types; the only Cairn-specific logic is the module build
    classifier. Nothing is persisted — the record regenerates from disk
    + the git ref graph on every call, so it cannot have drifted (the
    same generate-fresh invariant as loam's ``default_state_record``).

    *repo_root* defaults to the live Cairn repo
    (:data:`DEFAULT_CAIRN_REPO_ROOT`); tests pass a fixture repo.
    """
    root = (repo_root or DEFAULT_CAIRN_REPO_ROOT).resolve()
    specs = module_specs if module_specs is not None else default_cairn_module_specs()

    rows: list[ComponentState] = []
    for spec in specs:
        liveness, evidence = classify_module_build_status(root, spec.module_relpath)
        rows.append(
            ComponentState(
                name=spec.name,
                liveness=liveness,
                kind="component",
                evidence=evidence,
            )
        )

    return StateOfLoam(head_sha=_head_sha(root), components=tuple(rows))
