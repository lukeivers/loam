# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
  ``~/.loam/canonical-cache/<repo-id>/`` per β.1 cache-clone shape).

Outcome (success path)::

    <new-ws-path>/
      framework/                # git clone of <canonical-source>
      workspace/                # scaffolded by run_first_run_scaffold
        .pos/
          sync-config.yaml      # canonical_source recorded
          legacy-user-config/   # user-config defaults (~/.loam/-shaped)
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


class FrameworkVenvProvisionError(NewWorkspaceError):
    """Building ``<ws>/framework/.venv`` (the interpreter the scaffolded
    SessionStart hooks resolve to) failed.

    loam-init-framework-venv-or-robust-interpreter (AC.LIVI.1):
    bootstrap-time provisioning of the per-workspace framework venv is
    LOAD-BEARING, not fail-soft. The scaffolded SessionStart hooks
    (``build_supervisor_stanza`` / ``build_persona_session_start_inner_hook``)
    invoke ``<ws>/framework/.venv/bin/python``; if that venv is absent
    or its install failed, both hooks exit 127 on every fresh-init
    session (the exact silent defect this amendment closes). Per the
    plan's quality bar (structural over advisory) a provisioning
    failure surfaces LOUDLY here rather than silently degrading into a
    workspace whose persona/orchestrator session-start enrichment is
    dead — a quietly-broken workspace is strictly worse than a refused
    bootstrap the operator can retry.
    """


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


# OSS dev-architecture migration (2026-05-04). The bootstrap clones
# canonical's default branch ``main`` (post-migration). Canonical
# carries ``framework/<comp>/`` paths + top-level docs at root; the
# clone-into ``<new-ws>/framework/`` produces ``<new-ws>/framework/
# framework/<comp>/`` (the doubled-component shape; FBE.2c.5 binding)
# plus ``<new-ws>/framework/CLAUDE.md`` etc. at one level under
# ``framework/`` (the corpus-discovery readers fall through to
# ``<workspace>/framework/`` per AC.SFR.3).
#
# Pre-migration (synthesis era) the bootstrap targeted the now-
# deprecated ``framework-only`` synthetic branch produced by the
# pos-publish-framework-only tool (archived at
# ``docs/archive/synthesis-tool-2026-05-04/``).
CANONICAL_BRANCH = "main"


def _materialise_canonical_branch(path: Path) -> None:
    """Materialise ``main`` as a local branch on ``path``.

    Re-points ``refs/heads/main`` at ``refs/remotes/origin/main`` so
    a subsequent ``git clone <path>`` propagates the canonical branch
    as a LOCAL ref (``git clone`` only propagates LOCAL refs from the
    source).

    Two call sites:

    1. ``_resolve_url_to_clone_source`` — runs against the
       ``~/.loam/canonical-cache/<repo-id>/`` clone produced by
       ``ensure_cache_clone``. The cache's ``git clone <url>`` makes
       the remote's default branch available as both
       ``refs/heads/main`` AND ``refs/remotes/origin/main`` — so the
       materialisation step is a no-op idempotency on the typical
       case but stays defensive against any future scenario where
       a non-default branch becomes the canonical clone target.
    2. ``bootstrap_new_workspace``'s local-path branch — runs against
       a stranger's ``git clone <canonical-url>`` of canonical when
       ``--from`` resolves to that local clone (the typical post-FBE.9
       cwd-default-when-git-tree pattern). Same idempotency on the
       typical case (``main`` is already a local branch on the
       stranger-clone because it was the source's default branch).

    Fail-soft: a non-zero exit (e.g. the remote-tracking ref is
    absent because canonical does not publish ``main``) is non-
    fatal here; the downstream ``_clone_canonical`` checkout step
    will diagnose the absence with a structured ``CloneFailedError``
    naming ``main``.
    """
    subprocess.run(  # noqa: S603 — argv constructed
        [
            "git",
            "-C",
            str(path),
            "update-ref",
            f"refs/heads/{CANONICAL_BRANCH}",
            f"refs/remotes/origin/{CANONICAL_BRANCH}",
        ],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        text=True,
    )


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
    ``~/.loam/canonical-cache/<repo-id>/`` and returns the cache path
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
        from loam.workspace_sync.canonical_cache import (  # noqa: PLC0415
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

    # OSS dev-architecture migration (2026-05-04): post-migration
    # canonical's default branch is ``main``, so ``ensure_cache_clone``
    # makes ``main`` available as both ``refs/heads/main`` AND
    # ``refs/remotes/origin/main``. The materialise step is a no-op
    # idempotency on the typical case (``git update-ref`` succeeds
    # silently when the ref already points at the target SHA) but
    # stays defensive — kept for symmetry with the local-path branch
    # in ``bootstrap_new_workspace`` and for any future scenario where
    # a non-default branch becomes the canonical clone target.
    _materialise_canonical_branch(cache_path)
    return str(cache_path)


def _clone_canonical(
    clone_source: str,
    target_framework_dir: Path,
    *,
    branch: str = CANONICAL_BRANCH,
) -> None:
    """Clone canonical and check out ``branch``.

    OSS dev-architecture migration (2026-05-04): clones canonical and
    checks out ``main`` (canonical's default branch). Canonical
    carries ``framework/<comp>/`` paths + top-level docs at root, so
    the clone-into ``<new-ws>/framework/`` produces
    ``<new-ws>/framework/framework/<comp>/`` (the doubled-component
    shape; FBE.2c.5 binding) with ``<new-ws>/framework/CLAUDE.md``
    etc. at one level deeper than the four corpus-discovery readers
    expect — the readers fall through to ``<workspace>/framework/``
    per AC.SFR.3.

    The flow is two-step (``clone`` → ``checkout -B <branch>
    origin/<branch>``) rather than one-step (``clone --branch
    <branch>``) for symmetry with non-default-branch scenarios that
    might be reintroduced later (e.g. a release-branch clone target).
    On the typical case where ``branch`` is canonical's default,
    ``checkout -B main origin/main`` is a defensive no-op that lands
    on the same SHA as the freshly-cloned HEAD.

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
            f"Hint: canonical must publish a {branch!r} branch."
        )


def _provision_framework_venv(framework_dir: Path) -> Path | None:
    """Build ``<framework_dir>/.venv`` so the scaffolded SessionStart
    hooks resolve to a WORKING interpreter on a fresh ``loam init``.

    loam-init-framework-venv-or-robust-interpreter, D-LIVI.2 approach
    (a) (RATIFIED). Closes the verified root cause: the predecessor
    amendment wrote a correct SessionStart envelope whose two hook
    commands invoke ``<ws>/framework/.venv/bin/python``
    (``build_supervisor_stanza`` ``first_run_settings.py:284`` +
    ``build_persona_session_start_inner_hook``
    ``session_start_emitter.py:389``, both composing
    ``loam_root/.venv/bin/python`` with ``loam_root == <ws>/framework/``
    per the ``_scaffold_persona_binding`` call site), but
    ``bootstrap_new_workspace`` never built that venv (the documented
    Quickstart's ``python -m venv .venv`` builds the venv in the
    *disposable install clone*, not in ``<ws>/framework/``). Net: both
    hooks exited 127 on every fresh-init session — persona IDENTITY
    bound but session-start ENRICHMENT dead. This step makes the
    workspace genuinely self-contained (the README §"self-contained
    from that point / install clone is disposable" claim becomes TRUE
    as written) and leaves the SEALED stanza builders UNCHANGED — their
    ``loam_root/.venv/bin/python`` is now correct because the venv
    exists (single-component fence; no sealed-stanza-builder edit).

    Mechanism (method is the builder's call within the ratified
    approach):

    - ``python -m venv`` using ``sys.executable`` (the interpreter
      running the bootstrap — the documented Quickstart's install-clone
      venv python, already a 3.13 with the framework resolvable).
    - ``pip install -r <framework_dir>/install-from-source.txt`` run
      with the new venv's python. The cloned ``<ws>/framework/`` tree
      carries ``install-from-source.txt`` at its root plus every
      ``framework/<comp>`` + ``plugins/`` source tree, so the
      ``-e ./<path>`` editable entries resolve ENTIRELY against the
      clone (no PyPI roundtrip for any loam component — Lens 1: reuse
      the documented dependency set, do not re-implement resolution).
      Third-party transitive deps are served from pip's local
      wheel/HTTP cache, already populated by the documented Quickstart
      step 2 (same machine, same user, same pip cache) — so the common
      path is offline-capable + fast (halt-trigger 3 mitigation: the
      install-clone's already-resolved wheel set is reused, not
      re-fetched). ``--no-input`` keeps it non-interactive for the
      hands-off scaffold.

    Return contract (mirrors ``_scaffold_persona_binding``'s fail-soft-
    on-absent-machinery precedent below):

    - The cloned tree carries no ``install-from-source.txt`` (a
      minimal / stripped / fixture clone — NOT the documented
      Quickstart): there is no documented dependency set to install,
      so there is no venv to build and the persona binding will
      itself fail-soft (no machinery present => no SessionStart
      envelope wired => no dead hooks scaffolded). Return ``None``;
      the workspace is still usable, exactly as before this amendment.
      This is the pre-amendment behaviour, unchanged, for the
      not-the-documented-Quickstart case — AC.LIVI.1's outcome is
      scoped to the documented Quickstart (a real canonical clone,
      which DOES carry install-from-source.txt).
    - The dependency set IS present but the venv build / install
      genuinely fails: raise ``FrameworkVenvProvisionError`` LOUDLY.
      This is the case the quality bar targets — a quietly-dead
      session-start enrichment on the documented Quickstart is the
      precise defect this amendment closes; a refused-and-retryable
      bootstrap is strictly better than a workspace that looks bound
      but whose enrichment exits 127.

    Returns the path to the provisioned venv's python interpreter
    (the exact path the scaffolded hooks resolve to) on success, or
    ``None`` when the clone carries no documented dependency set
    (fail-soft, pre-amendment behaviour preserved).
    """
    venv_dir = framework_dir / ".venv"
    venv_python = venv_dir / "bin" / "python"
    requirements = framework_dir / "install-from-source.txt"

    if not requirements.is_file():
        # No documented dependency set in this clone => not the
        # documented Quickstart. Fail-soft: no venv, no dead hooks
        # (the binding fail-softs for the same reason). Pre-amendment
        # behaviour, unchanged.
        return None

    venv_completed = subprocess.run(  # noqa: S603 — argv constructed
        [sys.executable, "-m", "venv", str(venv_dir)],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        text=True,
    )
    if venv_completed.returncode != 0:
        raise FrameworkVenvProvisionError(
            f"`{sys.executable} -m venv {venv_dir!s}` failed (exit "
            f"{venv_completed.returncode}): "
            f"{(venv_completed.stderr or '').strip()!r}"
        )
    if not venv_python.is_file():
        raise FrameworkVenvProvisionError(
            f"venv build reported success but {venv_python!s} is "
            "absent — the scaffolded hooks would still exit 127."
        )

    install_completed = subprocess.run(  # noqa: S603 — argv constructed
        [
            str(venv_python),
            "-m",
            "pip",
            "install",
            "--no-input",
            "-r",
            str(requirements),
        ],
        cwd=str(framework_dir),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        text=True,
    )
    if install_completed.returncode != 0:
        raise FrameworkVenvProvisionError(
            f"`pip install -r install-from-source.txt` into "
            f"{venv_dir!s} failed (exit "
            f"{install_completed.returncode}). The fresh-init "
            "SessionStart hooks would resolve to an interpreter under "
            "which loam.primary_persona / the orchestrator are not "
            f"importable. stderr: "
            f"{(install_completed.stderr or '').strip()[-2000:]!r}"
        )

    return venv_python


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


# FBE.5b (amendment #110) — minimal `<workspace>/.claude/` scaffold.
#
# AC.FBE.5b.{1,2,3}: bootstrap_new_workspace creates `<workspace>/.claude/`
# (so Claude Code's workspace-discovery primitive resolves to a real
# location) and writes a minimal `settings.json` (empty object — no
# project-level overrides; defer to user-level settings + Claude Code
# defaults). Idempotent: if `settings.json` already exists, the operator
# may have customised it — leave it untouched. Mirrors the
# `_write_workspace_gitignore` "scaffold if absent" pattern in
# `adapters/first_run_scaffold.py`.
#
# Out of scope per AC.FBE.5b.5: hooks pointing at framework code,
# `.claude/agents/` subdir, persona seeds, and any `settings.json`
# key beyond the bare `{}`. Those land in v0.1.x amendments.
_CLAUDE_SETTINGS_JSON_TEMPLATE = "{}\n"


def _scaffold_claude_dir(claude_dir: Path) -> bool:
    """Scaffold ``<workspace>/.claude/`` if absent.

    Idempotent: if ``settings.json`` already exists, leaves it
    untouched (the operator may have customised it after first
    bootstrap; AC.FBE.5b.3). Returns True iff the directory was newly
    created OR the settings.json was newly written.
    """
    created = False
    if not claude_dir.exists():
        claude_dir.mkdir(parents=True, exist_ok=True)
        created = True
    settings = claude_dir / "settings.json"
    if not settings.exists():
        settings.write_text(
            _CLAUDE_SETTINGS_JSON_TEMPLATE, encoding="utf-8"
        )
        settings.chmod(0o644)
        created = True
    return created


# loam-init persona-wiring (AC.LIPW.1 / AC.LIPW.2 / AC.LIPW.3) —
# forward extension of the FBE.5b scaffold surface.
#
# AC.FBE.5b.5 deliberately out-scoped persona-binding from the `{}`
# settings.json ("Those land in v0.1.x amendments" — new_workspace.py
# :434-436). The deferral is now due: a non-tech user's documented
# quickstart (clone -> loam init -> cd -> claude) was landing them in
# a bare-LLM workspace with a dead persona (AC.PO.1 — the maximal
# translation-burden failure). LOCKED-DESIGN-NOT-LICENSE: "by design"
# is not a reason to keep that outcome. This forward extension writes
# the persona-binding surface a fresh `loam init` was missing, by
# COMPOSING on existing sealed primitives (Lens 1 — no new hook
# machinery):
#
#   - `to_agent_md(contract, prompt_text=...)` (amendment #35/#50) —
#     the deterministic contract -> `.claude/agents/<handle>.md`
#     subagent-file projector. UNCHANGED; imported, not edited.
#   - `_render_prompt_md(...)` (amendment #50 onboarding) — the
#     existing `{user_preferred_name}`/`{persona_given_name}`
#     str.format token substitution. UNCHANGED; imported, not edited.
#   - `merge_session_start(..., agent_handle=<handle>)` +
#     `build_supervisor_stanza(..., extra_inner_hooks=[...])`
#     (amendment #37/#45/#46 hands-off-lifecycle) — writes the
#     SessionStart envelope into `<ws>/.claude/settings.json` AND
#     sets top-level `"agent": <handle>` so a fresh Claude Code
#     session selects the workspace persona as its default subagent
#     (the main-thread-turn-one binding the canonical-dev template
#     proves works). UNCHANGED; imported, not edited.
#   - `build_persona_session_start_inner_hook(loam_root)` (amendment
#     #46 primary-persona) — the persona's `session-start` emit
#     inner-hook. UNCHANGED; imported, not edited.
#
# The build cycle decided BOTH binding surfaces are written (the
# `.claude/agents/<handle>.md` subagent file AND the settings.json
# `"agent"` key + SessionStart emit) because `.claude/agents/` alone
# makes the persona a DISPATCHABLE subagent, while the settings.json
# `"agent"` key is what binds it as the session's default agent on
# turn one. AC.LIPW.1 is outcome-shape ("persona active turn one");
# this two-surface method satisfies it without method-in-AC.
#
# Placeholder-safe identity (AC.LIPW.2): the bound prompt is rendered
# through `_render_prompt_md` with a brace-free placeholder identity
# so NO literal `{user_preferred_name}`/`{persona_given_name}` token
# ever reaches a bound surface on a fresh init. The existing
# `persist_grounding` (#50) remains the post-onboarding source of
# truth and re-renders identity from captured grounding unchanged
# (AC.LIPW.3 — no regression to the onboarding write-back contract).


# Placeholder-safe identity for the from-turn-zero binding. Brace-free
# (AC.LIPW.2) and intentionally non-personal: the real identity is
# captured by `persist_grounding` on the first onboarding turn. The
# persona-template's starter contract carries `given_name: Example`;
# the starter prompt's playbook drives a rename in the second turn.
_PLACEHOLDER_USER_NAME = "you"
_PLACEHOLDER_PERSONA_NAME = "your workspace persona"


def _persona_binding_already_bound(
    settings_path: Path, agents_file: Path, handle: str
) -> bool:
    """Idempotency probe (AC36.3 discipline, halt-trigger 5).

    Returns True iff the persona binding is already present and
    consistent — the agents file exists non-empty AND settings.json
    already carries ``"agent": <handle>``. On a re-``loam init`` of an
    already-bound workspace this returns True and the binding write is
    a no-op (no clobber of operator-customised settings keys; the
    underlying ``merge_session_start`` already preserves user keys but
    the early-return keeps the re-run a strict no-op for the binding).
    """
    if not agents_file.exists() or agents_file.stat().st_size == 0:
        return False
    if not settings_path.exists():
        return False
    try:
        import json  # noqa: PLC0415 — local, stdlib

        data = json.loads(settings_path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001 — malformed settings -> rebind
        return False
    return isinstance(data, dict) and data.get("agent") == handle


def _scaffold_persona_binding(
    *, workspace_root: Path, handle: str, loam_root: Path
) -> bool:
    """Write the primary-persona binding surface for a fresh workspace.

    Returns True iff this invocation wrote (or rewrote) the binding.
    Idempotent (AC36.3): a re-``loam init`` on an already-bound
    workspace is a no-op. Fail-soft: any failure to locate the
    just-installed persona contract / template surfaces as a return
    of False (the workspace is still usable; the binding can be
    re-attempted by a later re-scaffold) rather than aborting the
    whole bootstrap — mirrors the scaffold's other fail-soft writes.

    Composes on sealed primitives only (Lens 1). No primary-persona
    or hands-off-lifecycle source is edited; both are imported.
    """
    from .workspace_paths import claude_dir as _claude_dir
    from .workspace_paths import personas_dir as _personas_dir

    workspace_root = Path(workspace_root).resolve()
    persona_dir = _personas_dir(workspace_root) / handle
    contract_path = persona_dir / "contract.yaml"
    claude_dir = _claude_dir(workspace_root)
    agents_dir = claude_dir / "agents"
    agents_file = agents_dir / f"{handle}.md"
    settings_path = claude_dir / "settings.json"

    if not contract_path.exists() or contract_path.stat().st_size == 0:
        # The persona dir was not installed (or is half-written). The
        # scaffold's _install_persona_directory already surfaces the
        # malformed case as a structured diagnostic; here we simply
        # decline to bind rather than raise (fail-soft).
        return False

    if _persona_binding_already_bound(settings_path, agents_file, handle):
        return False

    # ---- compose on the sealed primitives ----------------------------
    # Fail-soft envelope (AC36.3 discipline + this function's docstring
    # contract): a workspace whose `framework/` clone does not carry
    # the persona-binding machinery (e.g. a minimal fixture clone, a
    # stranger clone of a stripped subtree, or a partial-recovery
    # state) is still a usable workspace — the binding simply does not
    # happen and `bootstrap_new_workspace` does NOT abort. The imports
    # are therefore inside the fail-soft try (a missing
    # primary_persona / hands-off-lifecycle surface returns False, not
    # a ModuleNotFoundError escaping the whole bootstrap).
    try:
        from loam.primary_persona.agent_md import (  # noqa: PLC0415
            to_agent_md,
        )
        from loam.primary_persona.contract import (  # noqa: PLC0415
            load_contract,
        )
        from loam.primary_persona.onboarding import (  # noqa: PLC0415
            _render_prompt_md,
        )
        from loam.primary_persona.session_start_emitter import (  # noqa: PLC0415,E501
            build_persona_session_start_inner_hook,
        )

        # hands-off-lifecycle's settings-merge builders live under a
        # hooks/ dir (not a src/ package). Resolve `first_run_settings`
        # from THIS WORKSPACE's own clone via an isolated importlib
        # spec — NOT a global `sys.path.insert`. A leaked sys.path
        # entry would make the binding's success depend on ambient
        # process state (e.g. an earlier caller having inserted a
        # different clone's hooks dir), which is non-deterministic and
        # cross-contaminating. Per-workspace spec resolution makes the
        # binding deterministic: it succeeds iff THIS workspace's
        # clone actually carries the machinery (fail-soft otherwise),
        # regardless of any other sys.path state in the process.
        import importlib.util as _ilu  # noqa: PLC0415

        first_run_settings_py = (
            loam_root
            / "framework"
            / "hands-off-lifecycle"
            / "hooks"
            / "first_run_settings.py"
        )
        if not first_run_settings_py.is_file():
            return False
        _mod_name = "_subloam_first_run_settings"
        _spec = _ilu.spec_from_file_location(
            _mod_name, first_run_settings_py
        )
        if _spec is None or _spec.loader is None:
            return False
        _frs = _ilu.module_from_spec(_spec)
        # first_run_settings.py defines @dataclass types; the stdlib
        # dataclasses machinery resolves a class's module via
        # ``sys.modules.get(cls.__module__)`` at exec time, so the
        # module MUST be registered in sys.modules under its spec name
        # before exec_module (the documented importlib pattern for
        # spec-loaded modules containing dataclasses). The synthetic
        # name is unique + removed in `finally`, so this does NOT leak
        # cross-test/process state (unlike a global sys.path.insert) —
        # the per-workspace determinism property is preserved.
        prior_mod = sys.modules.get(_mod_name)
        sys.modules[_mod_name] = _frs
        try:
            _spec.loader.exec_module(_frs)
        finally:
            if prior_mod is not None:
                sys.modules[_mod_name] = prior_mod
            else:
                sys.modules.pop(_mod_name, None)
        build_supervisor_stanza = _frs.build_supervisor_stanza
        merge_session_start = _frs.merge_session_start
    except Exception:  # noqa: BLE001 — binding machinery absent ->
        # fail-soft: workspace usable, binding skipped (the clone
        # lacks the primary-persona / hands-off-lifecycle surface).
        return False

    try:
        contract = load_contract(contract_path)
    except Exception:  # noqa: BLE001 — malformed contract -> fail-soft
        return False

    # Render the persona prompt through the EXISTING substitution path
    # with a brace-free placeholder identity (AC.LIPW.2). Read the
    # just-installed workspace prompt.md (it is the framework template
    # copy with literal tokens); substitute so zero `{...}` reaches
    # the bound surface.
    prompt_md_path = persona_dir / "prompt.md"
    rendered_prompt: str | None = None
    if prompt_md_path.exists() and prompt_md_path.stat().st_size > 0:
        try:
            rendered_prompt = _render_prompt_md(
                prompt_md_path.read_text(encoding="utf-8"),
                user_preferred_name=_PLACEHOLDER_USER_NAME,
                persona_given_name=_PLACEHOLDER_PERSONA_NAME,
            )
        except Exception:  # noqa: BLE001 — fall back to contract-only
            rendered_prompt = None

    try:
        agent_md_text = to_agent_md(contract, prompt_text=rendered_prompt)
    except Exception:  # noqa: BLE001 — projector refused -> fail-soft
        return False

    agents_dir.mkdir(parents=True, exist_ok=True)
    agents_file.write_text(agent_md_text, encoding="utf-8")
    agents_file.chmod(0o644)

    # Wire the SessionStart envelope + the top-level "agent" key. The
    # supervisor stanza is the post-first-run shape (a fresh non-tech
    # init is past the heavy first-run installer's concern — the
    # persona emit is the binding that matters turn one). The
    # `agent_handle` arg is the amendment #37 surface that makes a
    # fresh Claude Code session select the persona as default agent.
    persona_inner_hook = build_persona_session_start_inner_hook(loam_root)
    new_entry = build_supervisor_stanza(
        loam_root, extra_inner_hooks=[persona_inner_hook]
    )
    merge_session_start(
        settings_path=settings_path,
        new_entry=new_entry,
        agent_handle=handle,
    )
    return True


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
    3. URL form: populate cache clone in ``~/.loam/canonical-cache/``;
       local form: use the path directly. Either way, end up with a
       ``clone_source`` string passable to ``git clone``.
    4. ``git clone <clone_source> <new_ws_path>/framework/``
       (skipped when ``init_existing=True``).
    5. Write ``<new_ws_path>/workspace/.pos/sync-config.yaml`` with the
       (original) ``canonical_source`` recorded.
    6. Invoke ``run_first_run_scaffold`` against ``workspace_root=
       <new_ws_path>`` with ``pos_root=<new_ws_path>/workspace/.pos/
       legacy-user-config/`` (workspace-scoped; never touches
       operator's actual ``~/.loam/``).

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
            # OSS dev-architecture migration (2026-05-04): mirror the
            # URL-form materialisation step at the local-path branch.
            # On the typical case (``local_path`` is a stranger's
            # ``git clone <canonical-url>`` of canonical, the post-
            # FBE.9 cwd-default-when-git-tree pattern), ``main`` is
            # already ``local_path``'s local default branch (it was
            # the source's default), so the materialise step is a
            # no-op idempotency. Kept for symmetry with the URL-form
            # cache-clone path + defensive against any future
            # scenario where ``CANONICAL_BRANCH`` is a non-default
            # branch on the source.
            _materialise_canonical_branch(local_path)
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
    # workspace (legacy-user-config) so the operator's actual ~/.loam/
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

    # FBE.5b (amendment #110) — AC.FBE.5b.{1,2}: scaffold
    # `<workspace>/.claude/` + minimal `settings.json` so the CLI's
    # ".claude/    ← scaffolded" success-summary message is truthful
    # at runtime (closes FBE.5 Surface #7). Runs AFTER the scaffold
    # block so workspace state is fully populated first.
    _scaffold_claude_dir(claude_dir)

    # loam-init-framework-venv-or-robust-interpreter (AC.LIVI.1),
    # D-LIVI.2 approach (a) RATIFIED: build `<ws>/framework/.venv`
    # BEFORE the persona binding wires the SessionStart hooks against
    # it. This is the load-bearing fix: the predecessor amendment's
    # scaffolded hook commands invoke `<ws>/framework/.venv/bin/python`
    # (the stanza builders compose `loam_root/.venv/bin/python` with
    # `loam_root == framework_dir`), but nothing built that venv — both
    # hooks exited 127 on every fresh-init session (persona IDENTITY
    # bound, session-start ENRICHMENT dead). Provisioning it here makes
    # the workspace genuinely self-contained (the README's documented
    # "self-contained from that point / install clone disposable" claim
    # becomes TRUE as written) and keeps the SEALED stanza builders
    # UNCHANGED — their interpreter path is now correct because the
    # venv exists. LOUD when the documented dependency set IS present
    # but provisioning genuinely fails (a quietly-dead enrichment is
    # the exact defect this amendment closes); fail-soft (returns None,
    # pre-amendment behaviour) when the clone carries no
    # install-from-source.txt — a minimal / stripped / fixture clone is
    # NOT the documented Quickstart and the persona binding fail-softs
    # for the same absent-machinery reason, so no dead hooks are
    # scaffolded — see `_provision_framework_venv`. Runs for both the
    # fresh-clone and `--init-existing` paths (both produce a
    # `<ws>/framework/` whose hooks depend on this venv); idempotent
    # re-provision on a re-`loam init` is acceptable (venv rebuild +
    # pip re-resolve against the unchanged install set is a no-op-shaped
    # reinstall).
    _provision_framework_venv(framework_dir)

    # loam-init persona-wiring (AC.LIPW.1/.2/.3): forward extension of
    # the FBE.5b scaffold — write the primary-persona binding surface
    # the `{}` settings.json deliberately out-scoped, so a bare
    # `claude` in this fresh workspace has the persona ACTIVE on turn
    # one (no manual hook install, no canonical-dev template copy, no
    # unsubstituted prompt tokens). Composes on sealed primitives
    # (Lens 1); idempotent (AC36.3); fail-soft (a binding failure does
    # not abort the bootstrap — the workspace is still usable and the
    # binding is re-attempted on a re-scaffold). `loam_root` is the
    # CLONE ROOT (`<ws>/framework/`): `bootstrap_new_workspace` does
    # `git clone <canonical> <ws>/framework/`, and canonical loam
    # itself carries a top-level `framework/` subdir, so the cloned
    # layout is `<ws>/framework/framework/<component>/...`. The
    # `<ws>/framework/.venv/` the settings-stanza builders compose
    # against (`loam_root/.venv/bin/python`) is built by the
    # `_provision_framework_venv` step IMMEDIATELY ABOVE (it is NOT a
    # passive `git clone` artefact — canonical carries no committed
    # `.venv`; the predecessor's in-code comment asserting it as a
    # clone-layout artefact was the load-bearing inconsistency this
    # amendment corrects, plan §10.1). The settings-stanza builders
    # compose `loam_root/.venv/bin/python` + `loam_root/framework/
    # orchestrator/...` and `_scaffold_persona_binding` resolves the
    # hooks at `loam_root/framework/hands-off-lifecycle/hooks` — all
    # of which resolve correctly ONLY when `loam_root == <ws>/
    # framework/` (the clone root), NOT the workspace root.
    _scaffold_persona_binding(
        workspace_root=new_ws_path,
        handle=persona_handle,
        loam_root=framework_dir,
    )

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
            "https://github.com/lukeivers/loam\n"
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
            "clones to ~/.loam/canonical-cache/<repo-id>/ first; the "
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
        "  .claude/    ← scaffolded (Claude Code expects this here)",
        file=sys.stderr,
    )
    print(
        "  sync-config.yaml ← canonical_source recorded; "
        "`pos-sync` from inside the workspace works no-args.",
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
