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

"""SubagentStart auto-context bundle composition (loam-realignment 1a).

Composes the three-tier ``additionalContext`` bundle injected into every
dispatched subagent's context:

  1. MICROKERNEL (AC.SACH.1 / AC.SACH.2) — the always-on Trusted
     Computing Base, read VERBATIM from ``kernel/loam-microkernel.md``
     (D-SACH.2: content lives in the file, never hardcoded here, so
     editing the kernel needs no code change — mirrors
     ``corpus_inline_session_start.py``'s file-read pattern).
  2. WORKSTREAM CONTEXT (AC.SACH.3) — the active workstream. The
     resolver is STUBBED to the current workstream for slice 1a
     (D-SACH.3); project-keying is the deferred P-layer (plan §7-2).
     The tier's PRESENCE is asserted now so the bundle shape is frozen
     for downstream slices.
  3. MEMORY (AC.SACH.3) — workspace-scoped relevant memory, REUSING the
     persona's existing retrieval path unchanged (D-SACH.4 / Lens 1):
     ``build_live_mcp_memory_client`` -> ``search(query=<task text>,
     group_ids=[workspace_slug])`` -> ``_render_retrieval``. NOT a new
     retrieval mechanism.

Output envelope (AC.SACH.5 wiring / D-SACH.5): the hook emits
``{"hookSpecificOutput": {"hookEventName": "SubagentStart",
"additionalContext": <bundle>}}`` — the documented subagent-targeting
shape ``principle_reminder.py`` already proves at UserPromptSubmit.

Fail-soft contract (AC.SACH.4): every tier degrades to a structured
``[...]`` marker rather than raising. The hook NEVER aborts a subagent
dispatch — mirrors ``corpus_inline_session_start.py``'s exit-0 contract.

Per ODD §2.5 every branch below traces to a named AC: tier rendering ->
AC.SACH.1/2/3; the ``[missing]`` / ``[unavailable]`` markers ->
AC.SACH.4.

Stdlib + the sealed ``loam.primary_persona.memory_consumer`` /
``mcp_memory_client`` retrieval surface only.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Strips HTML-comment blocks (the Apache license header + authoring
# notes) from the microkernel render so only governing content reaches
# the subagent's context — the file is still read VERBATIM (D-SACH.2:
# content lives in the file, not hardcoded); this drops license
# boilerplate that carries zero governance value + would tax every
# subagent's context window. The governing content (prime marker, three
# roles, if-then triggers) is untouched.
_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)

# Reuse the persona's sealed memory surface (D-SACH.4 / Lens 1). The
# import is wrapped at call sites so a packaging gap never aborts a
# dispatch (AC.SACH.4) — see ``_render_memory_tier``.


# ---------------------------------------------------------------------
# Markers + delimiters (AC.SACH.1 prime marker; AC.SACH.4 fail markers)
# ---------------------------------------------------------------------

# The microkernel-tier delimiter header. The first token a probe looks
# for to confirm the microkernel reached the subagent (AC.SACH.1 /
# AC.SACH.S). Stable string — downstream slices + the AC.SACH.S probe
# key off it.
MICROKERNEL_PRIME_MARKER = "=== loam microkernel (always-on core) ==="

_WORKSTREAM_MARKER = "=== active workstream context ==="
_MEMORY_MARKER = "=== relevant memory ==="

# Fail-soft markers (AC.SACH.4). Each tier emits its own so a degraded
# bundle is observable + diagnosable, never silently empty + never
# raised.
MISSING_KERNEL_MARKER = "[microkernel unavailable — kernel file not found or unreadable]"
_WORKSTREAM_NONE_MARKER = "[no active workstream]"
_MEMORY_UNAVAILABLE_MARKER = "[memory unavailable — no live store or query]"
_MEMORY_EMPTY_MARKER = "[no relevant memory for this dispatch]"

SUBAGENT_START_EVENT = "SubagentStart"


# ---------------------------------------------------------------------
# Envelope parsing (D-SACH.4 task-text seed; AC.SACH.4 malformed input)
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class DispatchContext:
    """The fields the bundle composer reads off a SubagentStart envelope.

    ``workspace_root`` seeds the kernel-path resolution + the memory
    workspace-slug. ``task_text`` seeds the memory query (D-SACH.4).
    ``workstream`` is the resolved active-workstream label (D-SACH.3
    stub). Any field may be empty — the composer degrades each tier
    independently (AC.SACH.4).
    """

    workspace_root: Path | None
    task_text: str
    workstream: str


def parse_envelope(envelope: Any) -> DispatchContext:
    """Extract the dispatch context from a SubagentStart envelope.

    Fail-soft (AC.SACH.4): a malformed / empty / non-dict envelope
    yields an all-empty :class:`DispatchContext` rather than raising.
    The caller still composes a bundle (degraded microkernel-only).

    Task-text seed (D-SACH.4): the subagent's brief/task text is read
    from the envelope's ``prompt`` field (the SubagentStart dispatch
    text), falling back to ``task`` / ``description``. When none is
    present the memory tier degrades to a workspace-scoped marker
    rather than inventing a query (plan §8 halt-trigger #2's named
    fallback).
    """
    if not isinstance(envelope, dict):
        return DispatchContext(workspace_root=None, task_text="", workstream="")

    workspace = envelope.get("workspace")
    workspace_root: Path | None = None
    if isinstance(workspace, dict):
        root_str = workspace.get("project_dir")
        if isinstance(root_str, str) and root_str.strip():
            workspace_root = Path(root_str)

    # Task-text seed for the memory query (D-SACH.4). Accept the
    # documented dispatch-text fields in priority order; the first
    # non-empty string wins.
    task_text = ""
    for key in ("prompt", "task", "description"):
        value = envelope.get(key)
        if isinstance(value, str) and value.strip():
            task_text = value.strip()
            break

    workstream = _resolve_workstream(workspace_root)
    return DispatchContext(
        workspace_root=workspace_root,
        task_text=task_text,
        workstream=workstream,
    )


# ---------------------------------------------------------------------
# Tier 1 — microkernel (AC.SACH.1 / AC.SACH.2; D-SACH.2 file-read)
# ---------------------------------------------------------------------


def _resolve_kernel_path(workspace_root: Path | None) -> Path | None:
    """Return the on-disk microkernel path for *workspace_root*.

    The TCB lives at ``<workspace_root>/kernel/loam-microkernel.md``
    (integrated-design §2-K). When ``workspace_root`` is unknown
    (degenerate envelope), returns ``None`` so the caller emits the
    missing-marker (AC.SACH.4).
    """
    if workspace_root is None:
        return None
    return workspace_root / "kernel" / "loam-microkernel.md"


def _read_microkernel(workspace_root: Path | None) -> str:
    """Read the microkernel file VERBATIM (D-SACH.2).

    Fail-soft (AC.SACH.4): an absent / unreadable kernel file yields
    :data:`MISSING_KERNEL_MARKER` rather than raising. The content is
    emitted unmodified (the if-then form lives in the file; the hook
    does not author or reshape it — AC.SACH.2 asserts the FILE's shape).
    """
    path = _resolve_kernel_path(workspace_root)
    if path is None or not path.exists():
        return MISSING_KERNEL_MARKER
    try:
        raw = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return MISSING_KERNEL_MARKER
    # Drop HTML-comment blocks (license header + authoring notes) so the
    # injected microkernel is governing content only — never the license
    # boilerplate. Governing content is unmodified.
    stripped = _HTML_COMMENT_RE.sub("", raw)
    # Collapse the blank-line runs the removed comments leave behind.
    stripped = re.sub(r"\n{3,}", "\n\n", stripped)
    return stripped.strip("\n")


# ---------------------------------------------------------------------
# Tier 2 — workstream context (AC.SACH.3; D-SACH.3 STUB)
# ---------------------------------------------------------------------


def _resolve_workstream(workspace_root: Path | None) -> str:
    """Resolve the active-workstream label (D-SACH.3 STUB for 1a).

    Slice 1a resolves to the CURRENT workstream only. Project-keyed
    selective loading (the P-layer) is the deferred project-summary
    build (plan §7-2). The resolver reads the live work-streams STATE
    file (#70/#84) when present; otherwise it reports the stub
    sentinel. Either way the tier is PRESENT so the bundle shape is
    frozen for downstream slices (RF-2).

    Fail-soft (AC.SACH.4): any read error returns an empty string and
    the caller emits :data:`_WORKSTREAM_NONE_MARKER`.
    """
    if workspace_root is None:
        return ""
    # The work-streams register's current-workstream pointer. Probed
    # best-effort; absence is not an error (AC.SACH.4) — the tier is
    # still present, carrying the none-marker. The workspace-state
    # location routes through the workspace_paths helper (AC.D.2.5 —
    # path-helper centralisation); the import + construction are
    # guarded so a missing helper or a refused workspace_root degrades
    # to the docs/ fallback rather than aborting the bundle (AC.SACH.4).
    try:
        from loam.workspace_bootstrap.workspace_paths import pos_subdir

        candidates: tuple[Path, ...] = (
            pos_subdir(workspace_root) / "active-workstream",
            workspace_root / "docs" / "active-workstream.txt",
        )
    except Exception:
        candidates = (workspace_root / "docs" / "active-workstream.txt",)
    for candidate in candidates:
        try:
            if candidate.exists():
                text = candidate.read_text(encoding="utf-8").strip()
                if text:
                    return text.splitlines()[0].strip()
        except (OSError, UnicodeDecodeError):
            continue
    return ""


# ---------------------------------------------------------------------
# Tier 3 — memory (AC.SACH.3; D-SACH.4 REUSE persona retrieval path)
# ---------------------------------------------------------------------


def _render_memory_tier(ctx: DispatchContext) -> str:
    """Render the workspace-scoped memory tier, REUSING the persona's
    existing retrieval path unchanged (D-SACH.4 / Lens 1).

    Path: ``build_live_mcp_memory_client(workspace_root)`` ->
    ``build_memory_retrieval_contributor`` (the SAME callable the live
    UserPromptSubmit contributor registers) seeded with the dispatch
    task text as ``prompt`` and ``group_ids=[workspace_slug]``.

    Fail-soft (AC.SACH.4): a missing workspace, a missing task-text
    seed, an absent live store, or any boundary error degrades to a
    structured marker — never raises, never aborts the dispatch. The
    reused contributor is itself fail-closed (returns ""); an empty
    return renders the empty-marker so the tier is always present.
    """
    if ctx.workspace_root is None:
        return _MEMORY_UNAVAILABLE_MARKER
    if not ctx.task_text:
        # Plan §8 halt-trigger #2's named fallback: no task-text seed ->
        # do not invent a query; report unavailable rather than
        # fabricate (AC.SACH.4).
        return _MEMORY_UNAVAILABLE_MARKER

    try:
        from loam.primary_persona.mcp_memory_client import (
            build_live_mcp_memory_client,
        )
        from loam.primary_persona.memory_consumer import (
            MemoryRetrievalConfig,
            build_memory_retrieval_contributor,
            resolve_workspace_slug,
        )
    except Exception:  # noqa: BLE001 — packaging gap is fail-soft per AC.SACH.4
        return _MEMORY_UNAVAILABLE_MARKER

    try:
        client = build_live_mcp_memory_client(ctx.workspace_root)
    except Exception:  # noqa: BLE001 — substrate read is fail-soft
        return _MEMORY_UNAVAILABLE_MARKER
    if client is None:
        # No live memory-graphiti substrate (the PRODUCTION file-based
        # world post-M-FBM) — run the persona's GATED keep-pace
        # retrieval instead (AC.DMP.1, memory recall cycle Slice 4):
        # corpus rules + junk-gated episodes + DECISION RECORDS, with
        # rulings relevant to the task text injected WHOLE per the
        # AC.SRF.3 contract, within the retrieval surface's named
        # budget. Same Lens-1 posture as the MCP branch: the sealed
        # persona surface is reused, never re-implemented. Pre-cycle
        # this branch returned the empty marker — dispatched agents
        # were memory-blind by construction (the third leg of the
        # 2026-06-09 $750k failure).
        return _render_file_memory_tier(ctx)

    try:
        slug = resolve_workspace_slug(ctx.workspace_root)
    except Exception:  # noqa: BLE001 — unrepresentable slug is fail-soft
        return _MEMORY_UNAVAILABLE_MARKER

    config = MemoryRetrievalConfig(memory_client=client, workspace_slug=slug)
    contributor = build_memory_retrieval_contributor(
        config, workspace_root=ctx.workspace_root
    )
    try:
        rendered = contributor({"prompt": ctx.task_text})
    except Exception:  # noqa: BLE001 — defence-in-depth; contributor is fail-closed
        return _MEMORY_UNAVAILABLE_MARKER
    if not rendered.strip():
        return _MEMORY_EMPTY_MARKER
    return rendered.rstrip("\n")


def _render_file_memory_tier(ctx: DispatchContext) -> str:
    """The file-based-store memory tier (AC.DMP.1 — memory recall
    cycle, Slice 4): the persona's GATED keep-pace ``retrieve`` run
    with the dispatch task text as the prompt, against the SAME live
    config resolution the per-turn contributor uses.

    What the dispatched agent inherits by construction: matched +
    ``status: open`` decision records WHOLE (question / ruling /
    reasoning / source pointer — the AC.SRF.3 contract), path-bearing
    corpus + episode pointers, all junk-gated, within the retrieval
    surface's named ~5KB-class budget (the tier's budget IS that named
    constant — no second budget to drift).

    Fail-soft (AC.SACH.4, byte-preserved in outcome): any import /
    resolution / retrieval error degrades to a structured marker;
    never raises, never blocks the dispatch.
    """
    try:
        from loam.primary_persona.keep_pace.retrieval import (
            resolve_live_retrieval_config,
            retrieve,
        )
        from loam.primary_persona.memory_consumer import (
            resolve_workspace_slug,
        )
    except Exception:  # noqa: BLE001 — packaging gap is fail-soft per AC.SACH.4
        return _MEMORY_UNAVAILABLE_MARKER
    try:
        slug = resolve_workspace_slug(ctx.workspace_root)
        config = resolve_live_retrieval_config(ctx.workspace_root, slug)
        rendered = retrieve(prompt=ctx.task_text, config=config)
    except Exception:  # noqa: BLE001 — degraded tier never aborts a dispatch
        return _MEMORY_UNAVAILABLE_MARKER
    if not rendered.strip():
        return _MEMORY_EMPTY_MARKER
    return rendered.rstrip("\n")


# ---------------------------------------------------------------------
# Bundle assembly + envelope (AC.SACH.1/2/3/4; D-SACH.5)
# ---------------------------------------------------------------------


def compose_bundle(envelope: Any) -> str:
    """Compose the three-tier ``additionalContext`` bundle from a
    SubagentStart *envelope*.

    Tiers, in order, each under a delimiter header (mirrors
    ``corpus_inline_session_start.py``'s ``--- <name> ---`` block
    format):

      1. :data:`MICROKERNEL_PRIME_MARKER` + the verbatim microkernel.
      2. :data:`_WORKSTREAM_MARKER` + the active-workstream label.
      3. :data:`_MEMORY_MARKER` + the workspace-scoped memory render.

    Fail-soft (AC.SACH.4): each tier degrades independently to a
    structured marker; this function never raises.
    """
    ctx = parse_envelope(envelope)

    microkernel = _read_microkernel(ctx.workspace_root)
    workstream = ctx.workstream or _WORKSTREAM_NONE_MARKER
    memory = _render_memory_tier(ctx)

    blocks = [
        MICROKERNEL_PRIME_MARKER,
        "",
        microkernel,
        "",
        _WORKSTREAM_MARKER,
        "",
        workstream,
        "",
        _MEMORY_MARKER,
        "",
        memory,
    ]
    return "\n".join(blocks)


def render_envelope(bundle: str) -> str:
    """Wrap *bundle* in the SubagentStart additionalContext JSON
    envelope (D-SACH.5).

    Shape mirrors ``principle_reminder.py`` — the documented
    subagent-targeting contract:
    ``{"hookSpecificOutput": {"hookEventName": "SubagentStart",
    "additionalContext": <bundle>}}``.
    """
    return json.dumps(
        {
            "hookSpecificOutput": {
                "hookEventName": SUBAGENT_START_EVENT,
                "additionalContext": bundle,
            }
        }
    )
