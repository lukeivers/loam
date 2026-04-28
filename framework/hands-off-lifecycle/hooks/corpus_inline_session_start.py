"""SessionStart inner hook — inlines the always-load corpus content
into Claude Code's ``additionalContext`` channel.

Added by the corpus-inlining SessionStart hook amendment (number 73,
slug ``corpus-inlining-session-start-hook``). Per ODD §5.1.1 this
amendment ELIMINATES the "always read corpus at session-start"
failure class: the model has the bytes in context the moment the
session opens. The advisory rule in MEMORY.md prose
(``feedback_session_start_discipline``) becomes a substrate
property — bypass requires the substrate to fail.

## Composition with A1 substrate

Composes on the A1 substrate (``corpus_load_sentinel`` module) as a
consumer + extender:

  - Reads ``workspace_mode`` to gate DEV-MODE-only emission per
    AC.CI.3 (D-CI.8 / D-build.8).
  - Updates A1's per-(workspace, session) sentinel via
    ``write_corpus_load_sentinel(..., corpus_paths_loaded=...)`` to
    record the actually-inlined paths per AC.CI.4 (D-CI.5 /
    D-build.5).

Path resolution duplicates the 3-line ``_resolve_corpus_path`` helper
from ``framework/primary-persona/src/session_start_gate.py`` per
D-CI.4.(b) / D-build.2 (matches A1's ``WORKSPACE_STATE_SUBDIR``
duplicate-rather-than-cross-component-boundary precedent).

## Always-load tier (D-build.1; consumes owner D-CI.1.(a) lean)

Static set of three workspace-relative paths:

  - ``CLAUDE.md``
  - ``docs/rebuild/VALUE_PROPOSITION.md``
  - ``docs/rebuild/STATE.md``

Lean tier per the locked owner ruling. ~6.8k tokens / 27k chars per
session-start emission. The static set avoids the manifest-
tightening dependency (the manifest's ``always_loaded`` set today
includes whole component-source globs which are not corpus-shaped);
manifest tightening is an explicit out-of-scope follow-on per plan
§7.

## On-demand tier (D-build.5; D-CI.2.(a) path-pointer only)

Static set of three workspace-relative paths emitted as a pointer
block; persona reads on-demand via the Read tool when a turn
requires methodology / pos-v2-specific ODD / strategic-future
context:

  - ``docs/odd-methodology.md``
  - ``docs/odd-in-pos.md``
  - ``docs/rebuild/FUTURE_IDEAS.md``

Section-anchor extraction (research §5.4 hybrid) is an explicit
out-of-scope follow-on per plan §7.

## Output shape (D-build.6)

Raw text on stdout (matches loam-mode + persona emitter precedent —
both write to stdout; Claude Code captures stdout as
``additionalContext`` automatically). No ``hookSpecificOutput`` JSON
envelope authored by this hook.

Format:

    === pos-v2 always-loaded corpus (DEV MODE) ===

    --- CLAUDE.md ---
    <content>

    --- docs/rebuild/VALUE_PROPOSITION.md ---
    <content>

    --- docs/rebuild/STATE.md ---
    <content>

    === pos-v2 on-demand corpus (read via Read tool when relevant) ===
    - docs/odd-methodology.md
    - docs/odd-in-pos.md
    - docs/rebuild/FUTURE_IDEAS.md

Missing always-load files emit a structured ``[missing]`` marker
slot (AC.CI.1); missing on-demand files are silently omitted from
the pointer block (AC.CI.2 — that's the always-load tier's
contract).

## Per-file ceiling (AC.CI.6 / D-build.3 / D-CI.7)

50_000 chars per file. Files exceeding the ceiling are truncated at
the boundary with a structured marker:

    [truncated at 50000 chars; full file at <workspace-relative-path>]

Other files in the same fire are unaffected.

## Fail-soft contract (AC.CI.7)

Exit 0 on every path. Mirrors A1's ``corpus_load_session_start.py``
fail-soft pattern. The hook never raises into Claude Code's
SessionStart fan-out.

Stdlib only.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure sibling modules (corpus_load_sentinel) are importable when
# invoked as a script under the workspace's venv Python.
_HOOKS_DIR = Path(__file__).resolve().parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

from corpus_load_sentinel import (  # noqa: E402
    workspace_mode,
    write_corpus_load_sentinel,
)


# ---------------------------------------------------------------------
# Static tier definitions (D-build.1 + D-build.5)
# ---------------------------------------------------------------------


_ALWAYS_LOAD: tuple[str, ...] = (
    "CLAUDE.md",
    "docs/rebuild/VALUE_PROPOSITION.md",
    "docs/rebuild/STATE.md",
)

_ON_DEMAND: tuple[str, ...] = (
    "docs/odd-methodology.md",
    "docs/odd-in-pos.md",
    "docs/rebuild/FUTURE_IDEAS.md",
)


# Per-file ceiling (AC.CI.6 / D-build.3).
_PER_FILE_CEILING = 50_000


# ---------------------------------------------------------------------
# Path resolver (D-build.2; duplicates #67's _resolve_corpus_path)
# ---------------------------------------------------------------------


def _resolve_corpus_path(workspace_root: Path, rel: str) -> Path:
    """Return the resolved on-disk path for a workspace-relative
    corpus reference.

    AC.CI.5 binding: probes ``<workspace_root>/<rel>`` first; falls
    through to ``<workspace_root>/framework/<rel>`` when the
    workspace-root copy is absent. Returns the workspace-root path
    when neither exists (caller's existence check then surfaces the
    absence in the standard way, e.g. via the ``[missing]`` marker
    in the always-load tier or omission from the on-demand tier).

    Duplicated from ``framework/primary-persona/src/
    session_start_gate.py`` per D-CI.4.(b) / D-build.2 — matches A1's
    ``WORKSPACE_STATE_SUBDIR`` precedent (duplicate rather than
    cross-component-boundary lift).
    """
    workspace_root_path = workspace_root / rel
    if workspace_root_path.exists():
        return workspace_root_path
    framework_path = workspace_root / "framework" / rel
    if framework_path.exists():
        return framework_path
    return workspace_root_path


# ---------------------------------------------------------------------
# Content rendering (AC.CI.1 + AC.CI.2 + AC.CI.6)
# ---------------------------------------------------------------------


def _read_file_with_ceiling(path: Path, rel: str) -> tuple[str, bool]:
    """Read ``path`` and return (content, truncated_flag).

    AC.CI.6: when the on-disk file exceeds ``_PER_FILE_CEILING`` chars,
    the returned content is truncated at the boundary and a structured
    truncation marker is appended. The flag signals to the caller that
    the file was truncated (used for diagnostics / future micro-
    amendments; current emission paths do not branch on it beyond
    appending the marker text inside this helper).

    Fail-soft: any read error returns ``("", False)`` — the caller
    surfaces the absence via the ``[missing]`` slot.
    """
    try:
        content = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return "", False
    if len(content) <= _PER_FILE_CEILING:
        return content, False
    truncated = content[:_PER_FILE_CEILING]
    marker = (
        f"\n[truncated at {_PER_FILE_CEILING} chars; "
        f"full file at {rel}]\n"
    )
    return truncated + marker, True


def _render_always_load_block(
    workspace_root: Path,
) -> tuple[str, list[str]]:
    """Render the always-load tier and return (text, loaded_paths).

    AC.CI.1: emits per-file delimited content blocks. Files absent
    from disk emit a structured ``[missing]`` marker slot; their
    ``rel`` path is NOT added to ``loaded_paths`` (so A1's sentinel
    reflects only what actually entered context).
    """
    lines: list[str] = []
    lines.append("=== pos-v2 always-loaded corpus (DEV MODE) ===")
    lines.append("")
    loaded_paths: list[str] = []
    for rel in _ALWAYS_LOAD:
        resolved = _resolve_corpus_path(workspace_root, rel)
        lines.append(f"--- {rel} ---")
        if not resolved.exists():
            lines.append(
                f"[missing] file not found at workspace-root or "
                f"framework subdir"
            )
            lines.append("")
            continue
        content, _truncated = _read_file_with_ceiling(resolved, rel)
        if not content:
            # Read failure (permission denied, decode error, etc.).
            lines.append(
                f"[missing] file present but unreadable"
            )
            lines.append("")
            continue
        # Strip leading/trailing whitespace on the file content so the
        # delimiter blocks stay tidy; the inner content's structure is
        # preserved.
        lines.append(content.rstrip("\n"))
        lines.append("")
        loaded_paths.append(rel)
    return "\n".join(lines), loaded_paths


def _render_on_demand_block(workspace_root: Path) -> str:
    """Render the on-demand tier as a path-pointer block.

    AC.CI.2: workspace-relative paths only (no section-anchor
    extraction — out-of-scope per plan §7). Missing on-demand files
    are silently omitted from the pointer block (no ``[missing]``
    marker — that's the always-load tier's contract).
    """
    lines: list[str] = []
    lines.append(
        "=== pos-v2 on-demand corpus (read via Read tool when relevant) ==="
    )
    any_present = False
    for rel in _ON_DEMAND:
        resolved = _resolve_corpus_path(workspace_root, rel)
        if not resolved.exists():
            continue
        any_present = True
        lines.append(f"- {rel}")
    if not any_present:
        # Edge case: no on-demand files exist on disk at all. Emit a
        # placeholder so the block is observable / documented even
        # when the workspace shape is degenerate; do NOT inflate with
        # `[missing]` markers per AC.CI.2.
        lines.append("(no on-demand corpus files present)")
    return "\n".join(lines)


# ---------------------------------------------------------------------
# Main entry — SessionStart CLI
# ---------------------------------------------------------------------


def _emit(text: str) -> None:
    """Write the rendered text to stdout (Claude Code captures stdout
    as ``additionalContext`` per the established loam-mode + persona
    emitter convention)."""
    if not text:
        return
    sys.stdout.write(text)
    if not text.endswith("\n"):
        sys.stdout.write("\n")


def main(argv: list[str] | None = None) -> int:
    """Read SessionStart envelope; emit corpus content; update A1
    sentinel; exit 0.

    AC.CI.7: every error path returns 0. The hook never raises into
    Claude Code's SessionStart fan-out.
    """
    try:
        raw = sys.stdin.read()
    except Exception:  # noqa: BLE001 — fail-soft per AC.CI.7
        return 0
    if not raw.strip():
        return 0
    try:
        envelope = json.loads(raw)
    except json.JSONDecodeError:
        return 0
    if not isinstance(envelope, dict):
        return 0

    workspace = envelope.get("workspace")
    if not isinstance(workspace, dict):
        return 0
    workspace_root_str = workspace.get("project_dir")
    if not isinstance(workspace_root_str, str) or not workspace_root_str:
        return 0
    workspace_root = Path(workspace_root_str)

    session_id = envelope.get("session_id")
    if not isinstance(session_id, str) or not session_id:
        # Continue WITHOUT sentinel update — the corpus emit is the
        # primary AC. (AC.CI.4 names sentinel update; AC.CI.1+2 name
        # emission. The two are independently fail-soft per AC.CI.7.)
        session_id = ""

    # AC.CI.3 mode-partition: NORMAL USE workspaces no-op.
    try:
        mode = workspace_mode(workspace_root)
    except Exception:  # noqa: BLE001 — fail-soft per AC.CI.7
        return 0
    if mode != "dev-mode":
        return 0

    # Render content.
    try:
        always_text, loaded_paths = _render_always_load_block(workspace_root)
        on_demand_text = _render_on_demand_block(workspace_root)
    except Exception:  # noqa: BLE001 — fail-soft per AC.CI.7
        return 0

    output = always_text + "\n" + on_demand_text
    _emit(output)

    # Update A1's sentinel `corpus_paths_loaded` (AC.CI.4).
    if session_id:
        try:
            write_corpus_load_sentinel(
                workspace_root,
                session_id=session_id,
                mode=mode,
                corpus_paths_loaded=loaded_paths,
            )
        except Exception:  # noqa: BLE001 — fail-soft per AC.CI.7
            pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
