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

"""Shared helper library for hands-off-lifecycle PreToolUse gate
scripts (structural-enforcement A2 + A3 + future).

Extracted by structural-enforcement A3 (D-A3.7 of the locked plan).
A2's ``objective_binding_gate.py`` was the first gate; helpers were
inlined there per A2's D-build.2 (premature-extraction rationale).
A3 is the second gate; the rationale flips, and the shared helpers
move here. A4 (Bash/Agent-context guards) inherits this library.

The helpers carry:

  - workspace-state path constants (``WORKSPACE_STATE_SUBDIR``,
    ``POS_SUBDIR``);
  - dev-discipline carve-out tuples (``_CARVE_OUT_PREFIXES``,
    ``_CARVE_OUT_FILES``);
  - carve-out predicate (``is_carve_out_path``);
  - workspace-relative path canonicaliser (``workspace_relative``);
  - workspace-mode reader with fail-closed-to-permissive default
    (``read_workspace_mode_or_normal_use``);
  - active-scope sentinel reader with fail-closed-to-permissive
    default (``read_active_scope_sentinel_or_none``);
  - ObjectiveTracker opener with venv path-fix
    (``open_tracker_or_none``);
  - audit-log path resolver + atomic-append writer
    (``audit_log_path``, ``append_audit_line``).

Stdlib only (json, fnmatch, pathlib, os, sys, time). The
``read_active_scope_sentinel_or_none`` and
``read_workspace_mode_or_normal_use`` helpers do lazy imports of
``active_scope_sentinel`` and ``corpus_load_sentinel`` (sibling
modules under hooks/) to keep cold-start cost minimal and to allow
tests to monkeypatch ``sys.modules`` for those names. The
``open_tracker_or_none`` helper does a lazy import of
``objective_tracker`` + ``workspace_bootstrap`` after the venv path-
fix runs.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# Ensure sibling modules (active_scope_sentinel, corpus_load_sentinel)
# are importable when an importing script is invoked directly via
# ``python <hooks-dir>/<gate>.py``. Add this module's directory once
# at import time.
_HOOKS_DIR = Path(__file__).resolve().parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))


# ---------------------------------------------------------------------
# Workspace-state path constants (D-migration D.2 — amendment #63)
# ---------------------------------------------------------------------
#
# Workspace state lives under ``<workspace>/workspace/`` post-D.2.
# Hook scripts duplicate the constant per stdlib-only contract
# (canonical source: ``framework/workspace-bootstrap/src/
# workspace_bootstrap/workspace_paths.py`` ``WORKSPACE_STATE_SUBDIR``).

WORKSPACE_STATE_SUBDIR = "workspace"
POS_SUBDIR = ".pos"


# ---------------------------------------------------------------------
# Carve-out path list (D-A2.6 — D1 dev-discipline)
# ---------------------------------------------------------------------
#
# Workspace-relative path PREFIXES that admit edits regardless of
# sentinel state. Per AC.OBG.5: paths under any of these admit allow
# in DEV MODE. The list is union of pre-D-migration + post-D-migration
# shapes per locked plan §D-A2.6 (the migration window admits both).
#
# A3 inherits this list verbatim — the carve-out is shared structural
# infrastructure across all gates. A3 adds an additional "test-tree"
# short-circuit at its own decision-chain layer (NOT in the carve-out
# list — A3's tests/ short-circuit fires before the new-AC check
# specifically; it's a chicken-and-egg avoidance, not a dev-discipline
# admission).

_CARVE_OUT_PREFIXES: tuple[str, ...] = (
    "docs/",
    "tools/",
    ".scratch/",
    "personas/",
    "framework/docs/",
    "framework/tools/",
    "framework/personas/",
)

_CARVE_OUT_FILES: frozenset[str] = frozenset(
    {
        "CLAUDE.md",
        "CLAUDE.dev.md",
        "framework/CLAUDE.md",
        "framework/CLAUDE.dev.md",
        ".gitignore",
        "framework/.gitignore",
        # Long-form ODD docs — exact-file admission so the gate
        # remains permissive on the discipline corpus regardless
        # of the parent prefix carve-out membership.
        "docs/odd-methodology.md",
        "docs/odd-in-loam.md",
        # FUTURE_IDEAS{,_DRAFT}.md exact-admission entries STRIPPED
        # per C2-prime amendment §11 D-Q.ABC-prime.2: those files
        # have no public counterpart so substitution is not
        # available; the parent ``docs/`` prefix carve-out (in
        # ``_CARVE_OUT_PREFIXES``) admits them in dev-mode use,
        # so removing the exact-file entries is fail-soft.
    }
)


def is_carve_out_path(workspace_relative_path: str) -> bool:
    """True iff ``workspace_relative_path`` is a dev-discipline carve-
    out admitted regardless of sentinel state.

    Method per ODD §7.4: prefix-match for tree carve-outs + exact-
    match for file admissions. Path is workspace-relative, forward-
    slash separated.
    """
    if workspace_relative_path in _CARVE_OUT_FILES:
        return True
    for prefix in _CARVE_OUT_PREFIXES:
        if workspace_relative_path.startswith(prefix):
            return True
    return False


# ---------------------------------------------------------------------
# Path canonicalisation (R8 mitigation)
# ---------------------------------------------------------------------


def workspace_relative(
    file_path: str, workspace_root: Path
) -> str | None:
    """Canonicalise ``file_path`` to a workspace-relative POSIX-style
    string, OR return None when the path is not under workspace_root.

    Per R8: tool_input.file_path may be absolute or relative. Resolve
    both via ``Path.resolve()`` then compute the relative path. Returns
    None when the path lies outside the workspace (the gate's scope is
    workspace-relative; foreign paths are not gated — they fall through
    to allow because no manifest row can match a non-workspace path).
    """
    try:
        p = Path(file_path)
        if not p.is_absolute():
            p = workspace_root / p
        p_resolved = p.resolve()
        ws_resolved = workspace_root.resolve()
        rel = p_resolved.relative_to(ws_resolved)
    except (ValueError, OSError):
        return None
    return rel.as_posix()


# ---------------------------------------------------------------------
# Lazy-imported substrate readers (fail-closed-to-permissive)
# ---------------------------------------------------------------------


def read_workspace_mode_or_normal_use(workspace_root: Path) -> str:
    """Read the workspace-mode bit, or fall back to ``normal-use``.

    Lazy import of ``corpus_load_sentinel`` so a system-Python invoked
    hook script picks up the sibling module via the ``_HOOKS_DIR``
    insertion above. Failure (corpus-load-sentinel module absent,
    workspace_root unreadable) falls through to ``normal-use``, which
    short-circuits the gate to no-op (fail-closed-to-permissive at
    the import boundary).
    """
    try:
        from corpus_load_sentinel import workspace_mode

        return workspace_mode(workspace_root)
    except Exception:  # noqa: BLE001 — fail-closed-to-permissive
        return "normal-use"


def read_active_scope_sentinel_or_none(workspace_root: Path) -> Any:
    """Read the active-scope sentinel, or return None on failure.

    Lazy import of ``active_scope_sentinel``. Returns None when the
    sentinel is absent OR when the read fails (malformed JSON, IO
    error). Caller decides whether absent-sentinel is a deny or an
    allow per its own gate-specific contract.
    """
    try:
        from active_scope_sentinel import read_active_scope_sentinel

        return read_active_scope_sentinel(workspace_root)
    except Exception:  # noqa: BLE001 — fail-closed-to-permissive
        return None


# ---------------------------------------------------------------------
# Tracker open
# ---------------------------------------------------------------------


def open_tracker_or_none(workspace_root: Path) -> Any | None:
    """Open the workspace's ObjectiveTracker, or return None on failure.

    Lazy import + venv path-fix so a system-Python-invoked hook script
    can still reach the shared venv's installed objective_tracker
    package (matching the existing hands-off-lifecycle convention in
    first_run_helper.py / corpus_load_sentinel.py).
    """
    try:
        venv_lib = workspace_root / ".venv" / "lib"
        if venv_lib.is_dir():
            for site_dir in venv_lib.iterdir():
                site_pkgs = site_dir / "site-packages"
                if site_pkgs.is_dir() and str(site_pkgs) not in sys.path:
                    sys.path.insert(0, str(site_pkgs))
        from loam.objective_tracker import ObjectiveTracker  # type: ignore[import-not-found]
        from loam.workspace_bootstrap.workspace_paths import (  # type: ignore[import-not-found]
            tracker_db_path,
        )

        db_path = tracker_db_path(workspace_root)
        if not db_path.exists():
            return None
        return ObjectiveTracker(db_path)
    except Exception:  # noqa: BLE001 — fail-closed-to-permissive
        return None


# ---------------------------------------------------------------------
# Audit log writer
# ---------------------------------------------------------------------


def audit_log_path(workspace_root: Path, log_filename: str) -> Path:
    """Resolve the audit-log path for a gate.

    Per the D-migration D.2 convention (amendment #63):
    ``<workspace>/workspace/.pos/<log_filename>``.
    """
    return workspace_root / WORKSPACE_STATE_SUBDIR / POS_SUBDIR / log_filename


def append_audit_line(
    workspace_root: Path,
    log_filename: str,
    payload: dict[str, Any],
) -> None:
    """Append one NDJSON line to the gate's audit log. Fail-soft.

    Atomic single-line append via ``os.O_APPEND`` for writes shorter
    than ``PIPE_BUF`` (POSIX guarantees single-write atomicity for
    such payloads; one decision row is well under that).
    """
    target = audit_log_path(workspace_root, log_filename)
    line = json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n"
    encoded = line.encode("utf-8")
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(
            target, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644
        )
        try:
            os.write(fd, encoded)
        finally:
            os.close(fd)
    except OSError:
        # Fail-soft per the surrounding hooks convention; log failure
        # must never block the gate decision.
        return


# ---------------------------------------------------------------------
# Misc utilities used by gates
# ---------------------------------------------------------------------


def now_iso_z() -> str:
    """ISO-8601 UTC timestamp with second resolution + ``Z`` suffix.

    Mirrors A2's ``time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())``
    pattern; centralised here so all gates share the same shape.

    Used by audit-log writers (human-readable log lines, no compare).
    For A1-substrate ``created_at`` fields that participate in
    lex-comparison, use ``now_iso_microsecond_z`` instead — see
    amendment #75 (AC.TFN.1 .. AC.TFN.6).
    """
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


# ---------------------------------------------------------------------
# A1-substrate timestamp helper (amendment #75 — AC.TFN.3)
# ---------------------------------------------------------------------
#
# Single source-of-truth for the A1 substrate's ``created_at`` shape.
# Both sentinel writers (active_scope_sentinel._now_iso,
# corpus_load_sentinel._now_iso) delegate to this helper. The
# objective-tracker manifest insert (objective_tracker.store.
# insert_manifest_row) carries a one-line mirror of this helper's body
# under the ``_now_iso_microsecond_z`` private name in store.py — the
# two-step delegation reflects the cross-component import constraint
# (objective-tracker unit tests must run without the hands-off-lifecycle
# hooks dir on sys.path). AC.TFN.6 verifies the two emitters stay in
# byte-for-byte format agreement.
#
# Format γ (per amendment #75 plan §6 D-TFN.1): microsecond resolution,
# ``Z`` zone-suffix, fixed-width 27 chars. The fixed width matters
# because lexicographic comparison of γ-format strings is structurally
# correct on any same-second pair (no edge case at microsecond=0;
# strftime's ``%f`` always emits 6 digits).


def now_iso_microsecond_z() -> str:
    """ISO-8601 UTC timestamp with microsecond resolution + ``Z``
    suffix (format γ).

    Fixed-width 27 characters: ``YYYY-MM-DDTHH:MM:SS.ffffffZ``.
    The format string is ``%Y-%m-%dT%H:%M:%S.%fZ`` applied to a
    timezone-aware ``datetime.now(tz=timezone.utc)``; ``%f`` always
    emits 6 digits (zero-padded), eliminating the variable-width
    edge case that ``datetime.isoformat()`` exhibits on microsecond=0.

    Used by the two A1 sentinel writers and (via a one-line mirror in
    store.py) by the A1 manifest insert. Future A1-substrate
    ``created_at`` emitters MUST use this helper so lexicographic
    comparison remains structurally correct (per amendment #75
    AC.TFN.1, AC.TFN.2, AC.TFN.3).
    """
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


# ---------------------------------------------------------------------
# Universal-applicable command classifiers (structural-enforcement A4)
# ---------------------------------------------------------------------
#
# Two classifier functions added by structural-enforcement A4 for use
# by ``bash_guard.py``. Both are universal-applicable (no mode-bit
# dependency) so a future amendment auditing Bash history can reuse
# them. AC.BAG.1 (secret-commit) + AC.BAG.2 (blast-radius).
#
# Conservative regex deny-lists: false-positive direction is "deny
# rather than allow"; carve-outs admit the well-known legitimate cases
# (.env-example, .scratch/ deletions, /tmp/ deletions). The lists are
# extensible by future amendments; A4 ships the curated minimal set
# named in the plan-doc §4 + research §1.1 / §4.


# Secret-file path patterns. Each pattern matches a path basename or
# trailing path segment that names a secret-class file. The patterns
# are case-sensitive (sensible-default; .env vs .ENV is not a real
# carve-out direction).

_SECRET_FILE_PATTERNS: tuple[str, ...] = (
    # .env, .env.production, .env.local — but NOT .env-example or
    # .env.example (the example carve-out is handled below).
    r"(?:^|[\s/])\.env(?:\.[A-Za-z0-9_-]+)?(?=$|\s|[^A-Za-z0-9_.-])",
    # credentials.json
    r"(?:^|[\s/])credentials\.json(?=$|\s|[^A-Za-z0-9_.-])",
    # .aws/credentials
    r"(?:^|[\s/])\.aws/credentials(?=$|\s|[^A-Za-z0-9_.-])",
    # *.pem, *.key — matched as suffix only.
    r"(?:^|[\s/])[\S]+\.pem(?=$|\s|[^A-Za-z0-9_.-])",
    r"(?:^|[\s/])[\S]+\.key(?=$|\s|[^A-Za-z0-9_.-])",
    # SSH private key files (id_rsa, id_ed25519, id_ecdsa, id_dsa)
    r"(?:^|[\s/])id_(?:rsa|ed25519|ecdsa|dsa)(?=$|\s|[^A-Za-z0-9_.-])",
    # .npmrc / .pypirc with credentials are common; broad match.
    r"(?:^|[\s/])\.npmrc(?=$|\s|[^A-Za-z0-9_.-])",
    r"(?:^|[\s/])\.pypirc(?=$|\s|[^A-Za-z0-9_.-])",
)

# Carve-out: paths the secret-pattern matched but are explicitly safe.
# .env-example / .env.example / .env.sample are documentation patterns,
# not the credentials themselves. The carve-out is suffix-matched on
# the whole token.
_SECRET_FILE_CARVE_OUT_SUFFIXES: tuple[str, ...] = (
    "-example",
    ".example",
    "-sample",
    ".sample",
    "-template",
    ".template",
)

# Git subcommands that stage / commit / stash files. The classifier
# only fires when the command starts with one of these (after
# whitespace + a leading `git` or env-prefix).
_GIT_STAGING_SUBCOMMANDS: tuple[str, ...] = (
    "add",
    "commit",
    "stash",
)


def is_secret_commit_command(
    command: str,
) -> tuple[bool, list[str]]:
    """Classify ``command`` as a secret-file commit attempt (AC.BAG.1).

    Returns ``(matched, list of detected paths)``. Matches when:

    * the command invokes ``git`` with a staging subcommand
      (``add``, ``commit``, ``stash``); AND
    * at least one token in the command matches a secret-file pattern
      (``.env`` and friends, ``.pem``, ``.key``, ``id_rsa``, etc.); AND
    * the matched token does not end in a carve-out suffix
      (``-example``, ``.example``, ``-sample``, ``.sample``,
      ``-template``, ``.template``).

    The classifier is conservative — false-positive direction is
    "matched" (which yields a deny) rather than "missed" (which would
    admit a leak). The returned ``list of detected paths`` is the set
    of matched tokens for the deny diagnostic.

    Method per ODD §7.4: regex over the command string; no AST parse;
    git commit signing variants (``-S``, ``--gpg-sign``) and message
    flags (``-m``, ``--message``) are tolerated because the classifier
    matches the secret-file token wherever it appears in the command,
    not its position.
    """
    if not isinstance(command, str) or not command:
        return (False, [])

    # Quick filter: must be a git staging subcommand.
    if not _is_git_staging_subcommand(command):
        return (False, [])

    matched: list[str] = []
    seen: set[str] = set()
    for pattern in _SECRET_FILE_PATTERNS:
        for m in re.finditer(pattern, command):
            token = m.group(0).lstrip().lstrip("/")
            # Strip leading whitespace/slash captured by the leading
            # alternation. The classifier reports the trimmed token.
            token = token.strip()
            if not token:
                continue
            # Carve-out: .env-example etc.
            lower = token.lower()
            if any(
                lower.endswith(s) for s in _SECRET_FILE_CARVE_OUT_SUFFIXES
            ):
                continue
            # Carve-out: an interior `.example` between segments
            # (e.g. `.env.example.txt`). Conservative — admit when
            # any segment ends in a carve-out suffix.
            tail = token.rsplit("/", 1)[-1]
            tail_lower = tail.lower()
            if any(
                s in tail_lower
                and tail_lower.find(s) + len(s)
                >= len(tail_lower) - 16  # within trailing 16 chars
                for s in ("-example", ".example", "-sample", ".sample")
            ):
                # If "example" / "sample" appears in the trailing
                # portion of the basename, treat as documentation.
                # Conservative carve-out; intentional false-allow on
                # an obscure ".env.example.bak" pattern is preferable
                # to false-deny on the canonical `.env-example`.
                if any(
                    tail_lower.endswith(s)
                    or s in tail_lower.split(".")[-2:]
                    for s in (
                        "example",
                        "sample",
                        "template",
                    )
                ):
                    continue
            if token in seen:
                continue
            seen.add(token)
            matched.append(token)

    return (bool(matched), matched)


def _is_git_staging_subcommand(command: str) -> bool:
    """True iff ``command`` invokes ``git`` with a staging subcommand.

    Tolerates env-var prefixes (``FOO=bar git add ...``), interpreter
    prefixes (``sudo git add ...``), and pipes (``cat x | git add``).
    The classifier scans every pipeline segment for a `git <subcmd>`
    invocation.
    """
    # Split on shell pipeline separators (|, ;, &&, ||). Conservative —
    # any segment matching `git <staging>` triggers the check.
    segments = re.split(r"[|;]|&&|\|\|", command)
    for seg in segments:
        seg = seg.strip()
        if not seg:
            continue
        # Strip leading env-var assignments (NAME=value).
        tokens = seg.split()
        i = 0
        while i < len(tokens) and re.match(
            r"^[A-Za-z_][A-Za-z0-9_]*=", tokens[i]
        ):
            i += 1
        # Optional sudo / env / nice prefixes.
        while i < len(tokens) and tokens[i] in (
            "sudo",
            "env",
            "nice",
            "ionice",
            "time",
        ):
            i += 1
            # `env` may be followed by NAME=value too.
            while i < len(tokens) and re.match(
                r"^[A-Za-z_][A-Za-z0-9_]*=", tokens[i]
            ):
                i += 1
        if i + 1 >= len(tokens):
            continue
        if tokens[i] != "git":
            continue
        # Skip any -c key=value options between `git` and the subcmd.
        j = i + 1
        while j < len(tokens) and tokens[j] == "-c":
            j += 2  # skip flag and value
        if j >= len(tokens):
            continue
        if tokens[j] in _GIT_STAGING_SUBCOMMANDS:
            return True
    return False


# Blast-radius destructive command patterns. Each entry pairs a regex
# with a reason-class label that the deny diagnostic surfaces.

_BLAST_RADIUS_PATTERNS: tuple[tuple[str, str], ...] = (
    # git push --force / --force-with-lease to a protected branch.
    # Matches `git push ... --force* ... <ref>` where ref names main,
    # master, pos-v2, develop, prod*, release*.
    (
        r"\bgit\s+push\b[^\n]*--force(?:-with-lease)?(?:[^\n]*\b(?:origin|upstream)\b)?[^\n]*\b(?:main|master|pos-v2|develop|production|prod|release)\b",
        "git-push-force-protected",
    ),
    # Plain `git push --force` without a named ref also fires (default
    # ref is the upstream of the current branch — could be protected).
    (
        r"\bgit\s+push\s+(?:[^\n|;&]*\s)?--force(?:-with-lease)?\b",
        "git-push-force",
    ),
    # rm -rf with mass-destructive targets. Caller-side check delegates
    # path-scope verification (.scratch/ + /tmp/ admission) to
    # ``is_blast_radius_command`` proper; this regex is the trigger.
    (
        r"\brm\s+(?:-[rRf]+\s+|-r\s+-f\s+|-f\s+-r\s+)\S+",
        "rm-rf",
    ),
    # chmod -R 777 / 0 / 666 against $HOME or /.
    (
        r"\bchmod\s+(?:-R\s+|--recursive\s+)(?:0+|777|666)\s+(?:~|/|\$HOME)",
        "chmod-recursive-home",
    ),
    # dd if=... of=/dev/<disk> — disk overwrite class.
    (
        r"\bdd\s+[^\n]*\bof=/dev/(?:disk|sd|hd|nvme|mmcblk|xvd)",
        "dd-to-device",
    ),
    # curl/wget piped to bash/sh — remote-code-execution class.
    (
        r"\b(?:curl|wget)\s+[^\n|;&]*\|\s*(?:bash|sh|zsh|fish)\b",
        "curl-pipe-shell",
    ),
    # mkfs against a real device — filesystem creation = data loss.
    (
        r"\bmkfs(?:\.[a-z0-9]+)?\s+/dev/(?:disk|sd|hd|nvme|mmcblk|xvd)",
        "mkfs-on-device",
    ),
)


# Path-scope carve-outs for `rm -rf`. A `rm -rf` is admitted iff every
# target path is under one of these prefixes (workspace-relative or
# absolute). The carve-out is conservative — when path resolution
# fails, the command is flagged.
_RM_RF_ADMITTED_PREFIXES_RELATIVE: tuple[str, ...] = (
    ".scratch/",
    "workspace/.scratch/",
    "framework/.scratch/",
    ".pos/",
    "workspace/.pos/",
    "tmp/",
    "build/",
    "dist/",
    "node_modules/",
    "__pycache__/",
    ".pytest_cache/",
    ".mypy_cache/",
    ".ruff_cache/",
    ".cache/",
    ".venv/",
    "venv/",
    ".tox/",
)

_RM_RF_ADMITTED_PREFIXES_ABSOLUTE: tuple[str, ...] = (
    "/tmp/",
    "/var/tmp/",
    "/private/tmp/",
    "/private/var/tmp/",
    "/var/folders/",
)


def is_blast_radius_command(
    command: str,
    workspace_root: Path,
) -> tuple[bool, str, str]:
    """Classify ``command`` as a blast-radius destructive command
    (AC.BAG.2).

    Returns ``(matched, reason_class, matched_text)``. The
    ``reason_class`` names the failure class for the deny diagnostic
    (``"git-push-force-protected"``, ``"git-push-force"``,
    ``"rm-rf-outside-scratch"``, ``"chmod-recursive-home"``,
    ``"dd-to-device"``, ``"curl-pipe-shell"``, ``"mkfs-on-device"``).
    The ``matched_text`` is the literal substring that triggered the
    classifier — surfaced in the deny diagnostic.

    For ``rm -rf``, the classifier additionally inspects each target
    path: when EVERY target is under an admitted prefix
    (``<ws>/.scratch/``, ``/tmp/``, ``node_modules/``, ``.venv/``,
    ``__pycache__/``, etc.), the command is admitted (no match).

    Method per ODD §7.4: regex over the command string; no AST parse;
    rm-rf path-scope inspection is the only carve-out beyond plain
    pattern match.
    """
    if not isinstance(command, str) or not command:
        return (False, "", "")

    for pattern, reason_class in _BLAST_RADIUS_PATTERNS:
        m = re.search(pattern, command)
        if m is None:
            continue
        if reason_class == "rm-rf":
            # Inspect each rm -rf target — admit when ALL are scratch.
            admitted = _rm_rf_targets_all_admitted(
                command, workspace_root
            )
            if admitted:
                continue
            return (True, "rm-rf-outside-scratch", m.group(0))
        # git-push-force-protected takes precedence over generic
        # git-push-force when both fire.
        if reason_class == "git-push-force":
            # Only flag the plain force if no ref was named at all.
            # If a ref IS named and it's a protected branch, the
            # earlier pattern already matched; if it's an unprotected
            # branch, --force is permitted.
            if re.search(
                r"\bgit\s+push\s+(?:[^\n|;&]*\s)?\S+\s*$",
                m.group(0).rstrip(),
            ):
                # Trailing ref token present — admit (unprotected ref).
                continue
        return (True, reason_class, m.group(0))

    return (False, "", "")


def _rm_rf_targets_all_admitted(
    command: str, workspace_root: Path
) -> bool:
    """True iff every ``rm -rf`` target in ``command`` is under an
    admitted path prefix.

    Walks the command tokens looking for ``rm`` invocations, collects
    the path arguments after ``-rf`` / ``-r -f`` flags, and checks each
    against the relative + absolute admit lists. Conservative — when
    target resolution is ambiguous (variable expansion, etc.), the
    classifier returns False (the command is FLAGGED as blast-radius).
    """
    # Split on pipeline separators; inspect each segment.
    segments = re.split(r"[|;]|&&|\|\|", command)
    any_rm_rf = False
    for seg in segments:
        seg = seg.strip()
        if not seg:
            continue
        # Match `rm -rf <targets>` with various flag orderings.
        m = re.search(
            r"\brm\s+((?:-[rRf]+\s+|-r\s+-f\s+|-f\s+-r\s+)+)(.+?)$",
            seg,
        )
        if m is None:
            continue
        any_rm_rf = True
        targets_text = m.group(2)
        # Strip trailing pipe-tokens / shell control.
        targets = [
            t for t in re.split(r"\s+", targets_text.strip()) if t
        ]
        if not targets:
            return False
        for tgt in targets:
            # Strip leading flags (e.g. `--`).
            if tgt.startswith("-"):
                continue
            # Strip surrounding quotes.
            stripped = tgt.strip("\"'")
            # Reject if target contains shell-expansion patterns —
            # conservative: cannot resolve, so flag.
            if "$" in stripped or "`" in stripped:
                return False
            # Reject the catastrophic targets outright.
            if stripped in ("/", "~", "/*", "~/", "$HOME", "*"):
                return False
            # Absolute path — check the absolute admit list.
            if stripped.startswith("/"):
                if not any(
                    stripped.startswith(p)
                    for p in _RM_RF_ADMITTED_PREFIXES_ABSOLUTE
                ):
                    return False
                continue
            # Workspace-relative path — check the relative admit list.
            # Tolerate leading `./`.
            normalized = stripped[2:] if stripped.startswith("./") else stripped
            if not any(
                normalized.startswith(p)
                or normalized == p.rstrip("/")
                for p in _RM_RF_ADMITTED_PREFIXES_RELATIVE
            ):
                # Resolve against workspace_root and re-check via
                # absolute admit list as a fallback.
                try:
                    resolved = (workspace_root / normalized).resolve()
                    resolved_str = str(resolved) + "/"
                    if any(
                        resolved_str.startswith(p)
                        for p in _RM_RF_ADMITTED_PREFIXES_ABSOLUTE
                    ):
                        continue
                except (OSError, ValueError):
                    pass
                return False
    return any_rm_rf
