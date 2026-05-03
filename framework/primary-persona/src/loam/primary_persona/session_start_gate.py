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

"""Session-start gate — baseline payload assembly (D8.1, D8.2).

This module owns the session-level payload-field dict the
``ComposedContextPayload.on_session_start`` entry point consumes. It
discovers the baseline corpus, enumerates in-flight amendments, probes
session-level services, reads cost headroom, and computes the
``corpus_gate_state`` sentinel.

Graceful refusal on missing corpus (AC D8.2): missing paths are named
in ``missing_paths``; the sentinel takes ``partial`` (some present) or
``missing`` (none present) values; the composer does NOT raise and does
NOT request ``continue: false``. Per owner ruling D-2, the refusal is a
loud-diagnostic additionalContext — the session proceeds.

Corpus discovery reads ``CLAUDE.md``'s "Session-start discipline"
section dynamically (research §9 flag #5). If the baseline list in
CLAUDE.md grows in the future, the gate picks up the change without a
new amendment. When ``CLAUDE.md`` itself is missing, the gate uses a
hard-coded fallback list matching the current CLAUDE.md contents +
flags CLAUDE.md itself as a missing path.
"""

from __future__ import annotations

import re
import socket
import time
from pathlib import Path
from typing import Any

from .context_composer import CorpusGateState


# Fallback baseline paths used when CLAUDE.md is absent or its
# session-start-discipline section is unparseable. Defence-in-depth
# only; the dynamic CLAUDE.md parse is the authoritative path. Only
# paths shipped in every public workspace are listed here — the
# condensed ODD doc is the canonical floor.
_FALLBACK_BASELINE_PATHS: tuple[str, ...] = (
    "docs/design/odd.md",
)


_SESSION_START_HEADER_RE = re.compile(
    r"^##\s+Session-start discipline\s*$", re.MULTILINE | re.IGNORECASE
)
_NEXT_HEADER_RE = re.compile(r"^(##[^#]|---)\s*", re.MULTILINE)
_BACKTICK_PATH_RE = re.compile(r"`([^`\n]+\.md)`")


# Single-framework restructure (amendment #67). The four corpus-
# discovery readers probe the workspace-root path first (preserving
# behaviour for workspaces that scaffold their own workspace-root
# CLAUDE.md / docs/), and fall through to ``<workspace>/framework/``
# when the workspace-root copy is absent. ``framework-only`` carries
# top-level docs at the synthetic-branch root, so the workspace's
# clone lands them at ``<workspace>/framework/<doc>``.
def _resolve_corpus_path(workspace_root: Path, rel: str) -> Path:
    """Return the resolved on-disk path for a workspace-relative
    corpus reference.

    AC.SFR.3 binding: probes ``<workspace_root>/<rel>`` first; falls
    through to ``<workspace_root>/framework/<rel>`` when the workspace-
    root copy is absent. Returns the workspace-root path when neither
    exists (caller's existence check then surfaces the absence in the
    standard way, e.g. via ``compose_session_fields``'s
    ``missing_paths``).
    """
    workspace_root_path = workspace_root / rel
    if workspace_root_path.exists():
        return workspace_root_path
    framework_path = workspace_root / "framework" / rel
    if framework_path.exists():
        return framework_path
    return workspace_root_path


def discover_baseline_corpus(workspace_root: Path) -> list[str]:
    """Return the baseline corpus paths (workspace-relative).

    Reads ``workspace_root/CLAUDE.md``'s session-start-discipline
    section; extracts every backtick-wrapped ``*.md`` reference.
    Falls back to ``_FALLBACK_BASELINE_PATHS`` on any parse failure.
    The CLAUDE.md path itself is prepended because the discipline
    reads CLAUDE.md as the entry point — its own presence is also
    part of the gate.

    Single-framework restructure (amendment #67, AC.SFR.3): when
    ``<workspace>/CLAUDE.md`` is absent, falls through to
    ``<workspace>/framework/CLAUDE.md`` (the framework-only branch's
    root copy of CLAUDE.md, cloned in by ``pos-new-workspace``).
    """
    paths: list[str] = ["CLAUDE.md"]
    claude_md = _resolve_corpus_path(workspace_root, "CLAUDE.md")
    if not claude_md.exists():
        paths.extend(_FALLBACK_BASELINE_PATHS)
        return paths
    try:
        text = claude_md.read_text(encoding="utf-8")
    except OSError:
        paths.extend(_FALLBACK_BASELINE_PATHS)
        return paths
    section_match = _SESSION_START_HEADER_RE.search(text)
    if not section_match:
        paths.extend(_FALLBACK_BASELINE_PATHS)
        return paths
    section_start = section_match.end()
    tail = text[section_start:]
    next_header = _NEXT_HEADER_RE.search(tail)
    section_end = next_header.start() if next_header else len(tail)
    section = tail[:section_end]
    extracted = _BACKTICK_PATH_RE.findall(section)
    # Filter: only take paths that look workspace-relative + are .md.
    # A few backtick quotes in the section reference amendment-*.md
    # globs — those are enumerated separately in amendments_in_flight.
    for raw in extracted:
        raw = raw.strip()
        if not raw.endswith(".md"):
            continue
        if "amendment-*" in raw or raw.startswith("/"):
            continue
        if raw.startswith("./"):
            raw = raw[2:]
        if raw == "CLAUDE.md":
            continue
        if raw in paths:
            continue
        paths.append(raw)
    if len(paths) == 1:
        # Only CLAUDE.md parsed — fall back.
        paths.extend(_FALLBACK_BASELINE_PATHS)
    return paths


def enumerate_amendments_in_flight(workspace_root: Path) -> list[str]:
    """Return sorted ``amendment-*.md`` paths under the workspace's
    plan directory. Empty list when the directory is absent or holds
    no matching files.

    Probes the workspace-root plan directory first; falls through to
    the framework-clone copy when the workspace-root copy is absent.
    The returned paths remain workspace-relative; when the framework
    copy is the source, the returned strings carry the ``framework/``
    prefix so the caller can read them at the right location.
    """
    plans_dir = workspace_root / "docs" / "rebuild" / "plans"
    base_root = workspace_root
    if not plans_dir.is_dir():
        framework_plans_dir = (
            workspace_root / "framework" / "docs" / "rebuild" / "plans"
        )
        if not framework_plans_dir.is_dir():
            return []
        plans_dir = framework_plans_dir
        base_root = workspace_root  # paths are still rooted at workspace
    matches = sorted(
        p.relative_to(base_root).as_posix()
        for p in plans_dir.glob("amendment-*.md")
    )
    return matches


def probe_service_state(workspace_root: Path) -> dict[str, str]:
    """Quick, cheap probe of session-level services.

    Probes:
      - memory-system: HTTP health port as recorded on
        ``<workspace>/.pos/memory-port``, else default 8765. 250 ms
        timeout per research §7.3's 1.5 s worst-case envelope; D8
        uses the cheaper setting since the session-start budget
        aggregates multiple probes.
      - orchestrator: UNIX-socket reachability on the recorded path.
    Returns a dict with string values: "up" / "down" / "unknown".
    """
    state: dict[str, str] = {}
    state["memory"] = _probe_memory(workspace_root)
    state["orchestrator"] = _probe_orchestrator(workspace_root)
    return state


def _probe_memory(workspace_root: Path) -> str:
    from loam.workspace_bootstrap.workspace_paths import pos_subdir

    port = 8765
    port_file = pos_subdir(workspace_root) / "memory-port"
    if port_file.exists():
        try:
            port = int(port_file.read_text(encoding="utf-8").strip() or "8765")
        except (ValueError, OSError):
            port = 8765
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.25)
    try:
        sock.connect(("127.0.0.1", port))
        return "up"
    except (socket.timeout, OSError):
        return "down"
    finally:
        try:
            sock.close()
        except OSError:
            pass


def _probe_orchestrator(workspace_root: Path) -> str:
    from loam.workspace_bootstrap.workspace_paths import pos_subdir

    candidates: list[Path] = [
        pos_subdir(workspace_root) / "orchestrator.sock",
        Path.home() / ".loam" / "orchestrator.sock",
    ]
    for candidate in candidates:
        if candidate.exists():
            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            sock.settimeout(0.25)
            try:
                sock.connect(str(candidate))
                return "up"
            except (socket.timeout, OSError):
                return "down"
            finally:
                try:
                    sock.close()
                except OSError:
                    pass
    return "unknown"


def read_cost_headroom(workspace_root: Path) -> dict[str, Any]:
    """Read cost-governance month-to-date spend + ceiling headroom.

    Reads from ``<workspace>/.pos/cost-headroom.json`` if present (a
    cost-governance sidecar future work may populate). Returns empty
    dict when absent — D8 surfaces whatever is available without
    requiring cost-governance source changes.
    """
    import json

    from loam.workspace_bootstrap.workspace_paths import pos_subdir

    path = pos_subdir(workspace_root) / "cost-headroom.json"
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            # Defensive-copy with str values so the SessionPayload
            # model accepts them in ``cost_headroom: dict[str, Any]``.
            return {str(k): v for k, v in data.items()}
    except (OSError, ValueError):
        pass
    return {}


def read_first_run_completion(workspace_root: Path) -> str | None:
    """Read the recent first-run completion timestamp if recorded.

    Per amendment #28 first-run routing: the first-run state lives at
    ``<workspace>/workspace/.pos/first-run.state`` post-D.2 (was
    ``<workspace>/.pos/first-run.state`` pre-D.2). Returns the
    ``completed_at`` field value if present, else None.
    """
    import json

    from loam.workspace_bootstrap.workspace_paths import pos_subdir

    path = pos_subdir(workspace_root) / "first-run.state"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            value = data.get("completed_at")
            if isinstance(value, str) and value:
                return value
    except (OSError, ValueError):
        pass
    return None


# ---- top-level builder ----------------------------------------------


_GENERATION_MARKER = "session-start/1"


def compose_session_fields(workspace_root: Path) -> dict[str, Any]:
    """Produce the session-level field dict consumed by
    ``ComposedContextPayload.on_session_start``.

    The dict is Pydantic-compatible input for ``SessionPayload`` (minus
    the ``additional_context_text`` and ``contributor_outputs`` fields
    which the composer fills in at construction).

    Discovers baseline corpus, probes services, reads cost headroom,
    computes the ``corpus_gate_state`` sentinel + ``missing_paths``.
    All I/O is best-effort: probe failures degrade to ``down`` /
    ``unknown`` values; missing files degrade to absence + sentinel
    transitions.
    """
    _start = time.time()
    baseline_paths = discover_baseline_corpus(workspace_root)
    corpus_pairs: list[tuple[str, bool]] = []
    missing: list[str] = []
    # Single-framework restructure (amendment #67, AC.SFR.3): each
    # corpus reference probes the workspace-root path first, then
    # falls through to <workspace>/framework/<rel>.
    for rel in baseline_paths:
        resolved = _resolve_corpus_path(workspace_root, rel)
        present = resolved.is_file()
        corpus_pairs.append((rel, present))
        if not present:
            missing.append(rel)
    if not missing:
        sentinel = CorpusGateState.loaded
    elif len(missing) == len(baseline_paths):
        sentinel = CorpusGateState.missing
    else:
        sentinel = CorpusGateState.partial

    amendments = enumerate_amendments_in_flight(workspace_root)
    service_state = probe_service_state(workspace_root)
    cost_headroom = read_cost_headroom(workspace_root)
    first_run = read_first_run_completion(workspace_root)

    # Record wall-time for D8.4 diagnostics (not part of the payload).
    _elapsed_ms = int((time.time() - _start) * 1000)

    return {
        "corpus_paths": tuple(corpus_pairs),
        "amendments_in_flight": tuple(amendments),
        "service_state": service_state,
        "cost_headroom": cost_headroom,
        "corpus_gate_state": sentinel,
        "first_run_completion": first_run,
        "generation_marker": _GENERATION_MARKER,
        "missing_paths": tuple(missing),
    }
