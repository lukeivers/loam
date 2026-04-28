"""``pos-new-workspace`` — fresh-workspace bootstrap primitive.

D-migration D.4 (amendment #65). The β.2 absorption: this is the
operator-facing one-verb surface for creating a new pos-v2 workspace
at the D-shape (framework/ + workspace/ + .claude/).

Invocation::

    pos-new-workspace <new-ws-path> --from <canonical-source>

where ``<canonical-source>`` is either:

- An absolute POSIX path to a local git working tree
  (``/Users/.../ivers-corp-pos-v2``).
- An ``http(s)://`` URL or a ``git@``-style SSH spec (cloned to
  ``~/.pos/canonical-cache/<repo-id>/`` per β.1 cache-clone shape).

Outcome (success path)::

    <new-ws-path>/
      framework/                # git clone of <canonical-source>
      workspace/                # scaffolded by run_first_run_scaffold
        .pos/
          sync-config.yaml      # canonical_source recorded
          legacy-user-config/   # user-config defaults (~/.pos/-shaped)
        personas/<handle>/
        .mcp.json
        objective_tracker.sqlite
        ...
      .claude/                  # scaffolded by run_first_run_scaffold
                                # (Claude Code expects at workspace root)
      .gitignore                # framework/ + .claude/ are the only tracked
                                # subtrees by default

Subsequent ``pos-sync`` invocations from inside the workspace work no-
args (β.1 path): the workspace's ``workspace/.pos/sync-config.yaml``
carries ``canonical_source:`` so the resolver short-circuits.

The composition is structural: this module owns no scaffolding logic
of its own. It clones with ``git clone`` + invokes the existing
``run_first_run_scaffold`` API + writes one extra file
(``sync-config.yaml``). All scaffolding behaviour comes from the
sealed ``adapters/first_run_scaffold.py`` surface.

HC#1 fence: this module is internal to ``workspace-bootstrap``;
the cross-component import (``workspace_sync.canonical_cache``) is
lazy + read-only.

HC#6 structural promise: post-bootstrap, every workspace-state file
lives under ``<new-ws-path>/workspace/<...>`` (apart from ``.claude/``
per D-Q.A4 lock). The bootstrap never writes inside ``framework/``
beyond what ``git clone`` produces.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .adapters.first_run_scaffold import (
    DEFAULT_PERSONA_HANDLE,
    ScaffoldResult,
    run_first_run_scaffold,
)
from .workspace_paths import pos_subdir


# ---- error hierarchy -------------------------------------------------


class NewWorkspaceError(Exception):
    """Base exception raised by ``pos-new-workspace``.

    Concrete subclasses surface the failure class so the CLI can map
    them onto exit codes + structured stderr messages.
    """


class TargetNotEmptyError(NewWorkspaceError):
    """The target ``<new-ws-path>`` exists and is non-empty.

    Fail-closed semantic per β.2 HC #9 (workspace-sync-ergonomics.md):
    operators don't accidentally clobber an existing workspace. Raised
    BEFORE any side effects (no partial-bootstrap residue).
    """


class CanonicalSourceInvalidError(NewWorkspaceError):
    """The ``--from`` value is neither a recognised URL form nor an
    absolute path to an accessible git working tree.
    """


class CloneFailedError(NewWorkspaceError):
    """``git clone`` produced a non-zero exit code."""


class ScaffoldFailedError(NewWorkspaceError):
    """The scaffold step raised; bootstrap halted."""


# ---- public API -----------------------------------------------------


@dataclass(frozen=True)
class BootstrapResult:
    """Structured outcome of a successful bootstrap.

    Returned by ``bootstrap_new_workspace`` so callers (tests, future
    Telegram-bot wrappers, persona invocations) can inspect what
    landed without re-reading the disk surface.
    """

    new_ws_path: Path
    framework_dir: Path
    workspace_state_dir: Path
    claude_dir: Path
    sync_config_path: Path
    canonical_source: str
    canonical_source_kind: str  # "local" | "url"
    scaffold_result: ScaffoldResult
    init_existing: bool  # True iff --init-existing skipped the clone


# ---- canonical-source kind discriminator ----------------------------
#
# Mirror of `workspace_sync.sync_config.canonical_source_kind`. Inlined
# here so D.4 does not introduce a hard runtime dep on workspace-sync
# at import-time (the lazy URL-form import is below). The discriminator
# logic is the same locked shape.


def _canonical_source_kind(source: str) -> str:
    """Discriminate URL vs absolute-local-path forms (mirrors β.1).

    Returns ``"url"`` for ``http://`` / ``https://`` / ``git@`` forms.
    Returns ``"local"`` for absolute POSIX paths (``/...``).
    Raises ``CanonicalSourceInvalidError`` for anything else.
    """
    if source.startswith(("http://", "https://", "git@")):
        return "url"
    if source.startswith("/"):
        return "local"
    raise CanonicalSourceInvalidError(
        f"--from {source!r} must be one of: an http(s) URL "
        "(e.g. 'https://github.com/owner/repo'), a git@-style SSH spec "
        "(e.g. 'git@github.com:owner/repo.git'), or an absolute POSIX "
        "path (e.g. '/Users/.../pos-v2'). Relative paths and file:// "
        "URLs without an authority are not accepted."
    )


# ---- helpers --------------------------------------------------------


# Single-framework restructure (amendment #67). The bootstrap clones
# canonical's ``framework-only`` synthetic branch (rather than the
# default ``pos-v2`` branch) so the resulting workspace has shape
# ``<workspace>/framework/<comp>/`` (single level) plus
# ``<workspace>/framework/CLAUDE.md`` etc. — no
# ``framework/framework/<comp>/`` doubling. The corpus-discovery
# readers fall through to ``<workspace>/framework/`` when the
# workspace-root copy is absent (AC.SFR.3).
FRAMEWORK_ONLY_BRANCH = "framework-only"


def _target_is_empty(path: Path) -> bool:
    """Return True if ``path`` is a viable bootstrap target.

    Empty cases (all return True):

    - Path does not exist (the most common case — operator names a
      fresh location).
    - Path exists, is a directory, and contains no entries.

    All other cases (regular file, non-empty directory, broken
    symlink) return False — the bootstrap refuses to proceed.
    """
    if not path.exists():
        return True
    if not path.is_dir():
        return False
    try:
        next(path.iterdir())
    except StopIteration:
        return True
    return False


def _resolve_url_to_clone_source(url: str) -> str:
    """Resolve a URL-form canonical source to a local clone source.

    Composes on β.1's ``ensure_cache_clone`` to populate
    ``~/.pos/canonical-cache/<repo-id>/`` and returns the cache path
    as a string. The caller passes this string to ``git clone``;
    the resulting ``<new-ws>/framework/.git/config`` carries the
    cache path as ``origin``. Subsequent ``pos-sync`` invocations
    re-resolve the URL via the workspace's ``sync-config.yaml`` —
    which records the ORIGINAL URL, not the cache path — so the
    cache layer stays opaque to the operator.

    Lazy import: D.4 does not introduce a hard runtime dep on
    workspace-sync. Importing here means the dep is resolved at
    bootstrap time, not at module-load time. In the canonical
    pos-v2 install both packages are editable-installed alongside.
    """
    try:
        from workspace_sync.canonical_cache import (  # noqa: PLC0415
            CanonicalCacheError,
            ensure_cache_clone,
        )
    except ImportError as exc:
        raise CanonicalSourceInvalidError(
            f"URL-form canonical source {url!r} requires the "
            "workspace-sync package to be importable (provides the "
            "cache-clone substrate). Install workspace-sync in the "
            "same environment as workspace-bootstrap, or pass an "
            "absolute local path instead."
        ) from exc

    try:
        cache_path = ensure_cache_clone(url, ref="HEAD")
    except CanonicalCacheError as exc:
        raise CloneFailedError(
            f"canonical cache failed for {url!r}: {exc}"
        ) from exc

    # Single-framework restructure (amendment #67, AC.SFR.1):
    # ``ensure_cache_clone`` runs ``git clone <url>`` which makes the
    # remote's branches available as remote-tracking refs
    # (``refs/remotes/origin/framework-only``) but only checks out
    # the default branch as a local branch (``refs/heads/pos-v2``).
    # Subsequent ``git clone <cache-path>`` in ``_clone_canonical``
    # only propagates LOCAL branches, so ``framework-only`` would be
    # missing in the workspace's clone.
    #
    # Materialise ``framework-only`` as a local branch on the cache by
    # re-pointing ``refs/heads/framework-only`` at the remote-tracking
    # ref. Fail-soft: if the remote-tracking ref is absent (e.g. the
    # canonical does not yet publish ``framework-only``), the
    # downstream ``_clone_canonical`` checkout step surfaces the
    # absence with a structured CloneFailedError naming
    # ``framework-only``.
    completed = subprocess.run(  # noqa: S603
        [
            "git",
            "-C",
            str(cache_path),
            "update-ref",
            f"refs/heads/{FRAMEWORK_ONLY_BRANCH}",
            f"refs/remotes/origin/{FRAMEWORK_ONLY_BRANCH}",
        ],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        text=True,
    )
    # Non-zero exit (e.g. remote-tracking ref absent) is non-fatal
    # here; the downstream checkout step will diagnose precisely.
    return str(cache_path)


def _clone_canonical(
    clone_source: str,
    target_framework_dir: Path,
    *,
    branch: str = FRAMEWORK_ONLY_BRANCH,
) -> None:
    """Clone canonical and check out ``branch``.

    Single-framework restructure (amendment #67, AC.SFR.1): clones
    canonical and checks out the ``framework-only`` synthetic branch.
    The synthetic branch's tree promotes canonical's
    ``framework/<entry>`` to root + carries top-level docs verbatim,
    so the resulting workspace has shape
    ``<workspace>/framework/<comp>/`` (single level, no doubling) with
    ``<workspace>/framework/CLAUDE.md`` etc. at one level deeper than
    the four corpus-discovery readers expect — the readers fall
    through to ``<workspace>/framework/`` per AC.SFR.3.

    The flow is two-step (``clone`` → ``checkout -B <branch>
    origin/<branch>``) rather than one-step (``clone --branch
    <branch>``) because the URL-form path routes through the cache
    layer, which materialises non-default branches as remote-tracking
    refs (``refs/remotes/origin/<branch>``) rather than as local
    branches. ``git clone --branch <branch>`` against the cache then
    fails with ``Remote branch <branch> not found in upstream
    origin``. The two-step flow accepts both shapes (local branch on
    the source OR remote-tracking ref) by issuing the explicit
    ``checkout -B`` after the clone.

    Raises ``CloneFailedError`` on non-zero exit at either step. The
    target directory is created by ``git clone``; the caller MUST
    have ensured the parent (``<new-ws-path>/``) exists.
    """
    target_framework_dir.parent.mkdir(parents=True, exist_ok=True)
    clone_completed = subprocess.run(  # noqa: S603 — argv constructed
        ["git", "clone", clone_source, str(target_framework_dir)],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        text=True,
    )
    if clone_completed.returncode != 0:
        raise CloneFailedError(
            f"git clone {clone_source!r} → "
            f"{target_framework_dir!s} failed (exit "
            f"{clone_completed.returncode}): "
            f"{(clone_completed.stderr or '').strip()!r}"
        )

    checkout_completed = subprocess.run(  # noqa: S603
        [
            "git",
            "-C",
            str(target_framework_dir),
            "checkout",
            "-B",
            branch,
            f"origin/{branch}",
        ],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        text=True,
    )
    if checkout_completed.returncode != 0:
        raise CloneFailedError(
            f"git checkout -B {branch} origin/{branch} in "
            f"{target_framework_dir!s} failed (exit "
            f"{checkout_completed.returncode}): "
            f"{(checkout_completed.stderr or '').strip()!r}. "
            f"Hint: canonical must publish a {branch!r} branch "
            f"(synthesise with `pos-publish-framework-only`)."
        )


# Sync-config.yaml content. Single field (canonical_source) per β.1's
# locked schema; future amendments may add operator-tunable fields.
# The YAML is hand-authored rather than pyyaml-emitted so the comment
# preamble survives unaltered (PyYAML drops comments).
_SYNC_CONFIG_TEMPLATE = """\
# <workspace>/workspace/.pos/sync-config.yaml
# Auto-scaffolded by `pos-new-workspace` (D-migration D.4). Carries
# the canonical source the workspace was bootstrapped from. Subsequent
# `pos-sync` invocations from inside the workspace read this field
# and operate no-args (β.1 path). Edit freely to retarget; subsequent
# `pos-sync` runs re-resolve the URL/path against the new value.
canonical_source: {canonical_source}
"""


def _write_sync_config_yaml(
    workspace_root: Path, canonical_source: str
) -> Path:
    """Write ``<workspace>/workspace/.pos/sync-config.yaml``.

    Uses the post-D.2 path-helper (``pos_subdir``) so the location
    matches what β.1's ``load_sync_config`` reads back. Idempotent:
    on second invocation (init-existing path), the file is rewritten
    only if its content differs.
    """
    target = pos_subdir(workspace_root) / "sync-config.yaml"
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = _SYNC_CONFIG_TEMPLATE.format(canonical_source=canonical_source)
    if target.exists():
        existing = target.read_text(encoding="utf-8")
        if existing == payload:
            return target
    target.write_text(payload, encoding="utf-8")
    target.chmod(0o644)
    return target


def _stub_tracker_seed_runner_default() -> Any:
    """Return a no-op tracker-seed runner.

    Used when callers (specifically tests) want to skip the tracker
    seed step. Production CLI invocation passes ``None`` and lets
    the scaffold drive the real seed; tests pass the stub to keep
    test runtime fast + isolated from the objective-tracker
    subsystem.
    """
    from .adapters import tracker_seed  # noqa: PLC0415 — lazy + circular-safe

    def _runner(**_kwargs: Any) -> Any:
        return tracker_seed.TrackerSeedResult(
            seeded=False,
            reason="skipped_test_stub",
            classification="user",
            root_id=None,
            descendants_seeded=(),
            value_prop_source=None,
        )

    return _runner


def bootstrap_new_workspace(
    *,
    new_ws_path: Path,
    canonical_source: str,
    init_existing: bool = False,
    persona_handle: str = DEFAULT_PERSONA_HANDLE,
    service_bootstrap: bool = False,
    service_manager_dir_override: Path | None = None,
    persona_template_override: Path | None = None,
    value_prop_path_override: Path | None = None,
    tracker_seed_runner: Any | None = None,
) -> BootstrapResult:
    """Programmatic API: bootstrap a fresh workspace at ``new_ws_path``.

    Composition order (per D.4-build.C):

    1. Validate canonical-source kind (URL vs local path).
    2. Refuse-on-non-empty target (unless ``init_existing=True``).
    3. URL form: populate cache clone in ``~/.pos/canonical-cache/``;
       local form: use the path directly. Either way, end up with a
       ``clone_source`` string passable to ``git clone``.
    4. ``git clone <clone_source> <new_ws_path>/framework/``
       (skipped when ``init_existing=True``).
    5. Write ``<new_ws_path>/workspace/.pos/sync-config.yaml`` with the
       (original) ``canonical_source`` recorded.
    6. Invoke ``run_first_run_scaffold`` against ``workspace_root=
       <new_ws_path>`` with ``pos_root=<new_ws_path>/workspace/.pos/
       legacy-user-config/`` (workspace-scoped; never touches
       operator's actual ``~/.pos/``).

    Returns a ``BootstrapResult`` carrying the structured outcome.
    Raises ``NewWorkspaceError`` (or a subclass) on any halt path.

    Parameters
    ----------
    new_ws_path:
        Absolute path where the new workspace lands. Parent dirs are
        created if absent.
    canonical_source:
        URL or absolute local path to canonical pos-v2.
    init_existing:
        When True, ``new_ws_path`` is expected to already exist with a
        valid ``framework/`` subtree; the clone step is skipped and
        only the scaffold + sync-config write run. Idempotency contract
        per AC.D.4.2: re-invocation produces no further changes when
        the workspace is already complete.
    persona_handle:
        Workspace persona handle (default ``"primary"``); passed
        through to the scaffold.
    service_bootstrap:
        When False (default), the scaffold writes plist files but does
        NOT run ``launchctl bootstrap``. Production bootstrap defers
        the launchctl invocation to a later step (operator runs
        ``pos-bootstrap`` from inside the workspace, which triggers
        the launchd path on the workspace's installed deps).
    service_manager_dir_override:
        Test-only override for the ``LaunchAgents`` plist destination.
    persona_template_override / value_prop_path_override /
    tracker_seed_runner:
        Test-only overrides forwarded to ``run_first_run_scaffold``.
    """
    new_ws_path = Path(new_ws_path).expanduser().resolve()

    # Step 1: validate canonical source.
    kind = _canonical_source_kind(canonical_source)
    if kind == "local":
        local_path = Path(canonical_source).expanduser().resolve()
        if not local_path.exists():
            raise CanonicalSourceInvalidError(
                f"--from {canonical_source!r}: path does not exist."
            )
        if not (local_path / ".git").exists():
            raise CanonicalSourceInvalidError(
                f"--from {canonical_source!r}: path exists but is not "
                "a git working tree (missing .git/). Pass an absolute "
                "path to a real git clone of canonical, or a remote URL."
            )

    # Step 2: refusal-on-non-empty (unless init-existing).
    if not init_existing and not _target_is_empty(new_ws_path):
        raise TargetNotEmptyError(
            f"--target {new_ws_path!s} is not empty. Refusing to clobber "
            "an existing workspace. Pass --init-existing to re-scaffold "
            "an already-bootstrapped workspace, or remove the target."
        )

    framework_dir = new_ws_path / "framework"
    workspace_state_dir = new_ws_path / "workspace"
    claude_dir = new_ws_path / ".claude"

    if init_existing:
        # init-existing path: validate framework/ already exists; do NOT
        # clone (preserving any local commits on framework/'s tree).
        if not framework_dir.exists():
            raise NewWorkspaceError(
                f"--init-existing: {framework_dir!s} does not exist. "
                "An existing workspace must already carry a framework/ "
                "subtree (e.g. cloned by hand or by a prior "
                "pos-new-workspace run). Drop --init-existing to clone "
                "afresh."
            )
        if not (framework_dir / ".git").exists():
            raise NewWorkspaceError(
                f"--init-existing: {framework_dir!s} exists but is not "
                "a git working tree (missing .git/). Re-clone canonical "
                "into framework/ before running --init-existing."
            )
    else:
        # Fresh bootstrap: ensure the new-ws-path parent exists, then clone.
        new_ws_path.mkdir(parents=True, exist_ok=True)
        if kind == "url":
            clone_source = _resolve_url_to_clone_source(canonical_source)
        else:
            clone_source = str(local_path)
        try:
            _clone_canonical(clone_source, framework_dir)
        except CloneFailedError:
            # Clean up partial-bootstrap state so the user can retry.
            # Only remove framework/ if WE created the parent — never
            # remove a pre-existing target subtree.
            if framework_dir.exists():
                shutil.rmtree(framework_dir, ignore_errors=True)
            raise

    # Step 5: write sync-config.yaml. Done BEFORE the scaffold so the
    # workspace-state directory is bootstrapped with the canonical-
    # source field present from first contact.
    sync_config_path = _write_sync_config_yaml(
        workspace_root=new_ws_path,
        canonical_source=canonical_source,
    )

    # Step 6: scaffold workspace-state. pos_root scoped INSIDE the
    # workspace (legacy-user-config) so the operator's actual ~/.pos/
    # is never touched by D.4.
    legacy_user_config_dir = (
        workspace_state_dir / ".pos" / "legacy-user-config"
    )
    try:
        scaffold_result = run_first_run_scaffold(
            pos_root=legacy_user_config_dir,
            platform_override="macos",
            service_bootstrap=service_bootstrap,
            service_manager_dir_override=service_manager_dir_override,
            workspace_root=new_ws_path,
            persona_handle=persona_handle,
            persona_template_override=persona_template_override,
            value_prop_path_override=value_prop_path_override,
            tracker_seed_runner=tracker_seed_runner,
        )
    except Exception as exc:  # noqa: BLE001 — wrap into structured error
        raise ScaffoldFailedError(
            f"first-run scaffold failed for {new_ws_path!s}: "
            f"{type(exc).__name__}: {exc}"
        ) from exc

    return BootstrapResult(
        new_ws_path=new_ws_path,
        framework_dir=framework_dir,
        workspace_state_dir=workspace_state_dir,
        claude_dir=claude_dir,
        sync_config_path=sync_config_path,
        canonical_source=canonical_source,
        canonical_source_kind=kind,
        scaffold_result=scaffold_result,
        init_existing=init_existing,
    )


# ---- argparse + cli entry point --------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build the ``pos-new-workspace`` argparse.

    AC.D.4.3 binding: the parser's ``description`` + per-argument help
    strings name ``--from``, the ``<new-ws-path>`` positional, and
    describe the resulting directory shape.
    """
    parser = argparse.ArgumentParser(
        prog="pos-new-workspace",
        description=(
            "Bootstrap a fresh pos-v2 workspace from a canonical "
            "source. Creates <new-ws-path>/framework/ (cloned from "
            "<canonical-source>), <new-ws-path>/workspace/ "
            "(scaffolded with .pos/, personas/, .mcp.json, tracker "
            "DB), and <new-ws-path>/.claude/ (Claude Code's "
            "expected location at workspace root). Subsequent "
            "`pos-sync` invocations from inside the workspace work "
            "no-args."
        ),
        epilog=(
            "Examples:\n"
            "  pos-new-workspace ~/my-ws --from /Users/.../pos-v2\n"
            "  pos-new-workspace ~/my-ws --from "
            "https://github.com/lukeivers/pos-v2\n"
            "  pos-new-workspace ~/existing-ws --from /Users/.../pos-v2 "
            "--init-existing\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "new_ws_path",
        type=Path,
        help=(
            "Target path for the new workspace. Must be empty or "
            "non-existent (use --init-existing to re-scaffold an "
            "already-bootstrapped workspace)."
        ),
    )
    parser.add_argument(
        "--from",
        dest="canonical_source",
        required=True,
        type=str,
        help=(
            "Canonical pos-v2 source: an absolute POSIX path to a "
            "local git working tree, or an http(s)/git@ URL. URL form "
            "clones to ~/.pos/canonical-cache/<repo-id>/ first; the "
            "original URL is recorded in the new workspace's "
            "sync-config.yaml so subsequent pos-sync runs resolve it "
            "the same way."
        ),
    )
    parser.add_argument(
        "--init-existing",
        action="store_true",
        help=(
            "Skip the clone step; assume <new-ws-path>/framework/ "
            "already exists as a git working tree. Runs only the "
            "scaffold + sync-config write. Idempotent: re-invocation "
            "on a complete workspace produces no further changes."
        ),
    )
    parser.add_argument(
        "--persona-handle",
        default=DEFAULT_PERSONA_HANDLE,
        help=(
            f"Workspace primary-persona handle (default: "
            f"{DEFAULT_PERSONA_HANDLE!r}). Passed through to the "
            "first-run scaffold."
        ),
    )
    return parser


def cli_main(argv: list[str] | None = None) -> int:
    """``pos-new-workspace`` console-script entry point.

    Returns the CLI exit code. Maps:

    - 0 — bootstrap succeeded.
    - 1 — target not empty (recoverable; user removes target or
      passes --init-existing).
    - 2 — canonical source invalid (recoverable; user fixes the path
      or URL).
    - 3 — clone failed (network / permissions; user retries).
    - 4 — scaffold failed (structural; user reads the diagnostic).
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        result = bootstrap_new_workspace(
            new_ws_path=args.new_ws_path,
            canonical_source=args.canonical_source,
            init_existing=args.init_existing,
            persona_handle=args.persona_handle,
        )
    except TargetNotEmptyError as exc:
        print(f"[pos-new-workspace] {exc}", file=sys.stderr)
        return 1
    except CanonicalSourceInvalidError as exc:
        print(f"[pos-new-workspace] {exc}", file=sys.stderr)
        return 2
    except CloneFailedError as exc:
        print(f"[pos-new-workspace] {exc}", file=sys.stderr)
        return 3
    except ScaffoldFailedError as exc:
        print(f"[pos-new-workspace] {exc}", file=sys.stderr)
        return 4
    except NewWorkspaceError as exc:
        # Catch-all for the few halt conditions outside the named subclasses
        # (e.g. --init-existing with no framework/).
        print(f"[pos-new-workspace] {exc}", file=sys.stderr)
        return 5

    # Success summary — operator-actionable next-step guidance.
    print(
        f"[pos-new-workspace] bootstrapped {result.new_ws_path!s}",
        file=sys.stderr,
    )
    print(
        f"  framework/  ← clone of {result.canonical_source} "
        f"({result.canonical_source_kind})",
        file=sys.stderr,
    )
    print(
        f"  workspace/  ← scaffolded "
        f"(persona={args.persona_handle}, "
        f"reason={result.scaffold_result.reason})",
        file=sys.stderr,
    )
    print(
        f"  .claude/    ← scaffolded (Claude Code expects this here)",
        file=sys.stderr,
    )
    print(
        f"  sync-config.yaml ← canonical_source recorded; "
        f"`pos-sync` from inside the workspace works no-args.",
        file=sys.stderr,
    )
    if not result.init_existing:
        print(
            "\nNext steps:\n"
            f"  cd {result.new_ws_path}\n"
            "  # install per-component editable installs (see "
            "framework/Makefile or your install method)\n"
            "  pos-bootstrap            # triggers launchd plist "
            "bootstrap on first run\n"
            "  claude                   # Claude Code session-load",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    sys.exit(cli_main())
